"""Learned GIBS: real splits, no label leakage, GCN math, training and reload."""
import copy
import tempfile
from pathlib import Path

import pytest
import torch

from gibs.learned.data import (StoredTeachers, TASKS, fold_split, graph_texts, load_dataset)
from gibs.learned.model import GIBSPredictor, gib_loss, normalized_adjacency
from gibs.learned.run_experiment import predict_graph, set_seed, train_model


def graph(dim=6):
    return {"results": torch.arange(18, dtype=torch.float32).reshape(3, dim) / 10,
            "operations": torch.flip(torch.arange(18, dtype=torch.float32).reshape(3, dim), [0]) / 10,
            "adjacency": normalized_adjacency(3, [(0, 1), (1, 2)]),
            "agent_indices": torch.tensor([1, 2])}


def test_directed_normalization_matches_hand_calculation():
    a = normalized_adjacency(3, [(0, 1), (1, 2)])
    expected = torch.tensor([[1, 0, 0], [1 / 2 ** .5, .5, 0], [0, .5, .5]])
    torch.testing.assert_close(a, expected)
    torch.testing.assert_close(normalized_adjacency(2, []), torch.eye(2))


def test_loss_matches_equation6_and_has_finite_gradients():
    logits = torch.tensor([-2., 0., 2.], requires_grad=True)
    target = torch.tensor([0., .5, 1.])
    loss, entropy, ce = gib_loss(logits, target)
    p = logits.sigmoid()
    reference_entropy = -(p * p.log() + (1 - p) * (1 - p).log()).mean()
    reference_ce = -(target * p.log() + (1 - target) * (1 - p).log()).mean()
    torch.testing.assert_close(entropy, reference_entropy)
    torch.testing.assert_close(ce, reference_ce)
    torch.testing.assert_close(loss, reference_entropy + reference_ce)
    loss.backward()
    assert torch.isfinite(logits.grad).all()
    extreme = torch.tensor([-1000., 1000.], requires_grad=True)
    stable = gib_loss(extreme, torch.tensor([1., 0.]))[0]
    stable.backward()
    assert torch.isfinite(stable) and torch.isfinite(extreme.grad).all()


def test_gcn_uses_graph_edges_and_prediction_is_reference_free():
    set_seed(7)
    model = GIBSPredictor(embedding_dim=6, hidden_dim=8, dropout=0).eval()
    original = graph()
    disconnected = {**original, "adjacency": torch.eye(3)}
    assert not torch.allclose(model(original), model(disconnected))
    # Extra labels/rewards cannot influence a forward pass.
    poison = {**original, "reward": "forbidden", "gold_actions": object(), "target": object()}
    torch.testing.assert_close(model(original), model(poison), rtol=0, atol=0)
    assert len(predict_graph(model, original)) == 2


def test_graph_features_ignore_rewards_tasks_and_provider_metadata():
    raw = {"id": "r", "task_id": "25", "messages": [
        {"role": "user", "content": "Please cancel ABC123"},
        {"role": "assistant", "content": "Okay", "tool_calls": [{"id": "t", "name": "cancel_reservation", "arguments": {"reservation_id": "ABC123"}}]},
        {"role": "tool", "id": "t", "content": "Cancelled"}]}
    altered = {**raw, "reward_info": {"reward": 0}, "evaluation_criteria": {"actions": "forbidden"}, "info": {"secret": "forbidden"}}
    assert graph_texts(raw) == graph_texts(altered)


def test_real_task_splits_and_training_references_do_not_leak():
    runs, rows, _ = load_dataset()
    teachers = StoredTeachers(runs)
    assert len(runs) == 62
    assert rows and len({(r['run_id'], r['step_index']) for r in rows}) == len(rows)
    for heldout in TASKS:
        split = fold_split(runs, heldout)
        train = {r["id"] for r in split["train"]}
        validation = {r["id"] for r in split["validation"]}
        test = {r["id"] for r in split["test"]}
        assert not (train & validation or train & test or validation & test)
        assert all(r["task_id"] == heldout for r in split["test"])
        assert all(r["task_id"] != heldout for r in split["train"] + split["validation"])
        for method in ("paper_style", "agent_adapted"):
            for q in split["train"] + split["validation"]:
                target, refs = teachers.target(method, q, split["train"])
                assert set(refs) <= train and q["id"] not in refs
                assert len(refs) >= 3 and len(target) == len(q["nodes"])
                assert ((target >= 0) & (target <= 1)).all()


def test_seeded_training_changes_weights_and_reloads_exactly():
    # Train a small feature-dimension-independent instance using default 768 inputs.
    torch.set_num_threads(2)
    set_seed(11)
    features = {"train": {**graph(), "results": torch.randn(3, 768), "operations": torch.randn(3, 768)},
                "validation": {**graph(), "results": torch.randn(3, 768), "operations": torch.randn(3, 768)}}
    split = {"train": [{"id": "train"}], "validation": [{"id": "validation"}]}
    targets = {"train": torch.tensor([0., 1.]), "validation": torch.tensor([0., 1.])}
    model, stats = train_model(split, features, targets, 7, epochs=5, patience=3, hidden_dim=8)
    assert stats["max_parameter_change"] > 0
    assert stats["epochs_completed"] >= 1
    again, _ = train_model(split, features, targets, 7, epochs=5, patience=3, hidden_dim=8)
    assert predict_graph(model, features["validation"]) == predict_graph(again, features["validation"])
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "weights.pt"
        torch.save(model.state_dict(), path)
        restored = GIBSPredictor(embedding_dim=768, hidden_dim=8)
        restored.load_state_dict(torch.load(path, weights_only=True))
        assert predict_graph(model, features["validation"]) == predict_graph(restored, features["validation"])
