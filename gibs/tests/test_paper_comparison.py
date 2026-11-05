"""Paper semantic NIBS, released control, new graph and partition checks."""
import copy

import numpy as np
import pytest
import torch

from gibs.comparison.graphs import projection
from gibs.comparison.released_model import ReleasedPredictor, released_loss
from gibs.comparison.run import external_split, load_data
from gibs.comparison.semantic_nibs import cosine_matrix, reference_scores


def test_paper_nibs_equal_weight_per_reference_not_per_step():
    query = np.array([[1., 0.]])
    refs = [np.array([[1., 0.]]), np.array([[0., 1.], [0., 1.], [1., 0.]])]
    maximum, average = reference_scores(query, refs)
    assert maximum == [1.]
    assert average[0] == pytest.approx((1 + 1 / 3) / 2)


def test_pdf_cosine_and_released_distance_are_distinct():
    q, r = np.array([[1., 0.]]), np.array([[0., 1.]])
    assert reference_scores(q, [r])[0] == [0.]
    assert reference_scores(q, [r], released=True)[0] == [.5]
    opposite = np.array([[-1., 0.]])
    assert reference_scores(q, [opposite])[0] == [-1.]
    assert reference_scores(q, [opposite], released=True)[0][0] == pytest.approx(1 / 3)
    np.testing.assert_allclose(cosine_matrix(np.array([[2., 0.]]), np.array([[3., 0.]])), [[1.]])


def test_semantic_nibs_rejects_empty_references():
    with pytest.raises(ValueError):
        reference_scores(np.ones((1, 2)), [])


def trajectory(with_error=False):
    messages = [{"role": "user", "content": "Please update reservation ABC123."}]
    def call(name, args, observation, error=False):
        cid = f"c{len(messages)}"
        messages.append({"role": "assistant", "content": None,
                         "tool_calls": [{"id": cid, "name": name, "arguments": args}]})
        messages.append({"role": "tool", "id": cid, "content": observation, "error": error})
    call("get_reservation_details", {"reservation_id": "ABC123"}, '{"reservation_id":"ABC123","status":"old"}')
    call("get_reservation_details", {"reservation_id": "ABC123"}, '{"reservation_id":"ABC123","status":"refreshed"}')
    if with_error:
        call("get_reservation_details", {"reservation_id": "ABC123"}, 'Error fetching ABC123', True)
    call("update_reservation_passengers", {"reservation_id": "ABC123", "passengers": []}, '{"reservation_id":"ABC123","status":"updated"}')
    messages.append({"role": "assistant", "content": "Your reservation is updated."})
    return {"id": "test", "task_id": "40", "messages": messages}


@pytest.mark.parametrize("with_error", [False, True])
def test_state_graph_uses_latest_non_error_observation_and_message_context(with_error):
    sim = trajectory(with_error)
    original, revised = projection(sim), projection(sim, "state_aware")
    assert original.nodes == revised.nodes
    target = next(nid for nid in revised.nodes if any(e["text"].startswith("Call update_reservation_passengers") for e in revised.in_edges(nid)))
    refreshed = next(nid for nid, node in revised.nodes.items() if 'refreshed' in (node["text"] or ''))
    assert refreshed in {e["src"] for e in revised.in_edges(target)}
    assert refreshed not in {e["src"] for e in original.in_edges(target)}
    message = next(nid for nid, node in revised.nodes.items() if node["kind"] == "agent_message")
    assert {role for e in revised.in_edges(message) for role in e["roles"]} == {"message_user_context", "message_observation"}
    order = {nid: i for i, nid in enumerate(revised.nodes)}
    assert all(order[e["src"]] < order[e["dst"]] for e in revised.edges)
    poison = {**sim, "reward_info": {"reward": 0}, "evaluation_criteria": {"actions": "ignore"}}
    assert projection(poison, "state_aware").to_dict() == revised.to_dict()


def test_original_graph_remains_unchanged_across_ablation():
    sim = trajectory()
    before = copy.deepcopy(projection(sim).to_dict())
    projection(sim, "state_aware")
    assert projection(sim).to_dict() == before


def test_additional_tasks_never_enter_training_or_validation():
    runs, rows, _ = load_data()
    split = external_split(runs)
    assert len(runs) == 100 and len(rows) == 796
    assert {r["task_id"] for r in split["test"]} == {"3", "40"}
    assert {r["task_id"] for r in split["train"] + split["validation"]} == {"9", "25", "48"}
    assert not {r["content_hash"] for r in split["test"]} & {r["content_hash"] for r in split["train"] + split["validation"]}


def test_released_balanced_loss_and_empty_mapping_behavior():
    logits = torch.tensor([-.3, .5, 1.2], requires_grad=True)
    masks = [torch.tensor([1., 0., 0.]), torch.zeros(3)]
    actual = released_loss(logits, masks)
    p = logits.sigmoid()
    entropy = -(p * p.log() + (1 - p) * (1 - p).log()).mean()
    reference = entropy - (p[0] + 1e-8).log() - (1 - p[1:] + 1e-8).log().mean()
    torch.testing.assert_close(actual, reference)
    actual.backward()
    assert torch.isfinite(logits.grad).all()
    torch.testing.assert_close(released_loss(logits, [torch.zeros(3)]), entropy)


def test_released_forward_repeats_identical_operation_masks():
    torch.manual_seed(7)
    model = ReleasedPredictor(embedding_dim=6, hidden_dim=8).eval()
    operation = torch.randn(1, 6)
    graph = {"results": torch.randn(3, 6), "edge_operations": operation.repeat(2, 1),
             "agent_edge_indices": [torch.tensor([0, 1])]}
    edges = model.forward_edges(graph)
    torch.testing.assert_close(edges[0], edges[1], rtol=0, atol=0)
    assert len(model(graph)) == 1
