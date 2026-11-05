"""Train/evaluate the paper-inspired GIBS agent prototype, or score one raw run.

    .venv/bin/python -m gibs.learned.run_experiment
    .venv/bin/python -m gibs.learned.run_experiment predict --checkpoint ... --results ... --run-id ...
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import random
import statistics
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from gibs.learned.data import (BERT_MODEL, BERT_REVISION, MAX_LENGTH, SPLIT_SEED, TASKS,
                               TEACHERS, FrozenBert, StoredTeachers, fold_split, graph_texts,
                               load_dataset, prepare_features, tensor_graph)
from gibs.learned.model import GIBSPredictor, gib_loss
from nibs.run_evaluation import REPO, analyze, file_hash, fmt, write_csv, write_json

DEFAULT_OUT = REPO / "results/gibs_learned"
SEEDS = (7, 17, 27)
SOURCE_FILES = ["gibs/learned/data.py", "gibs/learned/model.py", "gibs/learned/run_experiment.py",
                "gibs/learned/EVALUATION_PLAN.md", "gibs/graph/step_graph.py", "gibs/graph/event_projection.py",
                "gibs/validation/step_verification_v2.py", "gibs/validation/step_verification.py",
                "gibs/mcs/structured_fields.py", "gibs/validation/dedup.py", "gibs/validation/dataset_audit.py",
                "nibs/run_evaluation.py", "nibs/evaluation_metrics.py", "nibs/parsing/parser.py",
                "nibs/scoring/nibs.py", "nibs/similarity/similarity.py"]


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def train_model(split, features, targets, seed, epochs=150, patience=20, hidden_dim=128):
    """Only input graphs and consensus targets enter optimization/early stopping."""
    set_seed(seed)
    model = GIBSPredictor(hidden_dim=hidden_dim)
    initial = {k: v.clone() for k, v in model.state_dict().items()}
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    history, best, best_state, best_epoch, stale = [], math.inf, None, 0, 0
    started = time.perf_counter()
    for epoch in range(1, epochs + 1):
        model.train()
        order = list(split["train"])
        random.Random(seed + epoch).shuffle(order)
        losses = []
        for start in range(0, len(order), 8):
            optimizer.zero_grad()
            batch = order[start:start + 8]
            loss = torch.stack([gib_loss(model(features[r["id"]]), targets[r["id"]])[0] for r in batch]).mean()
            if not torch.isfinite(loss):
                raise ValueError("non-finite training loss")
            loss.backward()
            optimizer.step()
            losses.extend([loss.item()] * len(batch))
        model.eval()
        with torch.no_grad():
            components = [gib_loss(model(features[r["id"]]), targets[r["id"]]) for r in split["validation"]]
            val_loss, entropy, ce = [torch.stack([values[i] for values in components]).mean().item() for i in range(3)]
        if not math.isfinite(val_loss):
            raise ValueError("non-finite validation loss")
        history.append({"epoch": epoch, "train_loss": statistics.mean(losses),
                        "validation_loss": val_loss, "validation_entropy": entropy, "validation_ce": ce})
        if val_loss < best - 1e-5:
            best, best_epoch, best_state, stale = val_loss, epoch, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
        if stale >= patience:
            break
    model.load_state_dict(best_state)
    model.eval()
    max_change = max((best_state[k] - initial[k]).abs().max().item() for k in initial)
    if max_change == 0:
        raise ValueError("model weights did not change")
    return model, {"seed": seed, "best_epoch": best_epoch, "best_validation_loss": best,
                   "epochs_completed": len(history), "seconds": time.perf_counter() - started,
                   "max_parameter_change": max_change, "parameters": sum(p.numel() for p in model.parameters()),
                   "history": history}


def predict_graph(model, graph):
    model.eval()
    with torch.no_grad():
        scores = model(graph).sigmoid().tolist()
    if len(scores) != len(graph["agent_indices"]) or any(not math.isfinite(x) or not 0 <= x <= 1 for x in scores):
        raise ValueError("invalid per-step prediction")
    return scores


def evaluate(rows, key="nibs"):
    metrics, loc = analyze(rows)
    return {scope: {"aggregate": data["aggregate"][key],
                    "tasks": {task: item["methods"][key] for task, item in data["tasks"].items()}}
            for scope, data in metrics.items()}, loc


def number_stats(values):
    values = [x for x in values if x is not None]
    return {"mean": statistics.mean(values) if values else None,
            "std": statistics.pstdev(values) if values else None, "n": len(values)}


def aggregate_seed_metrics(per_seed):
    out = {}
    for scope in ("all_agent_steps", "tool_calls"):
        data = [v[scope]["aggregate"] for v in per_seed.values()]
        out[scope] = {"macro_auroc": number_stats(v["macro_auroc"] for v in data),
                      "within_task_pair_weighted_auroc": number_stats(v["within_task_pair_weighted_auroc"] for v in data),
                      **{k: number_stats(v["localization"][k] for v in data)
                         for k in ("top1", "top3", "reciprocal_rank")}}
    return out


def build_report(summary):
    lines = ["# Learned GIBS prototype on tau2-bench Airline", "",
             "**A trained, paper-inspired agent adaptation; retrospective automatic-label evaluation. Human validation is pending.**", "",
             "## What ran", "",
             f"- {summary['n_queries']} distinct real benchmark trajectories, {summary['n_agent_steps']} agent steps, tasks 9/25/48.",
             f"- Frozen BERT CLS features ({BERT_MODEL}, revision {BERT_REVISION}, {MAX_LENGTH} tokens).",
             "- A two-layer GCN (128 hidden units, dropout 0.1), operation encoder and graph/step fusion MLP.",
             "- Actual Adam training of the predictor with equation 6: entropy + soft cross-entropy to MCS consensus masks.",
             f"- Three leave-one-task-out folds, seeds {summary['seeds']}; validation loss selects checkpoints. BERT is not fine-tuned.",
             "- All test-task graphs excluded from optimization, training pseudo-target references, validation targets and early stopping.",
             "- Saved real DeBERTa+MCS pair mappings reused; NLI/MCS were not recomputed in this experiment.", "",
             "## Is this the same as the paper?", "",
             "**The core framework is the same. The task representation and experiment are adaptations, so this is not an exact reproduction.**", "",
             "| Aspect | Paper | This prototype |", "|---|---|---|",
             "| Data | GSM8K, Math, MoreHopQA reasoning | Recorded multi-turn Airline tool-use trajectories |",
             "| Step | Operation/result reasoning pair | Tool call/result or agent message; user turns supply context |",
             "| Dependencies | Structured reasoning generation | Deterministic value provenance from recorded events |",
             "| Features/network | BERT + two-layer GCN, hidden 128, dropout 0.1 | Same stated components; explicit mean graph context and fusion MLP |",
             "| Primary teacher | MCS consensus node masks | Existing paper-style A, m_node; no structured checks |",
             "| Adapted teacher | Not in paper | C4 m_ctx, structured field checks, symmetric truncation, multiple components |",
             "| Objective | Final Eq. 6 entropy + lambda CE | Eq. 6 with lambda=1; not a sparse-prior KL implementation |",
             "| Training scale | 2,000 graphs | Tens of training graphs per fold |",
             "| Evaluation labels | LLM judge (plus paper human benchmark experiments) | Existing narrow rule-based verifier; human review pending |",
             "| Inference | Trained predictor, query graph | Query-only inference, without gold labels/references |", "",
             "The released author script's active wo_mcs_feature forward path uses MLPs/mean pooling rather than its declared GCN. "
             "We follow the paper's stated GCN architecture, not that script bit-for-bit. The exact fusion, event-level prediction "
             "and lambda are disclosed implementation choices. The paper's Eq. 5 KL and Eq. 6 entropy objectives differ; Eq. 6 is used.", "",
             "## Evaluation against baselines", "",
             "Learned results are mean +/- population standard deviation across seeds, without ensembling. "
             "Each seed's scores are out-of-fold: the model scoring a task never trained on that task. "
             "These tasks were previously inspected during method development, so this is not an untouched test.", ""]
    for scope in ("all_agent_steps", "tool_calls"):
        lines += [f"### {scope.replace('_', ' ')}", "",
                  "| Method | Macro AUROC | First-labelled-error top-1 | Top-3 | MRR |", "|---|---|---|---|---|"]
        for method, values in summary["learned_aggregate"].items():
            d = values[scope]
            f = lambda k: f"{fmt(d[k]['mean'])} +/- {fmt(d[k]['std'])}"
            lines.append(f"| {method} | {f('macro_auroc')} | {f('top1')} | {f('top3')} | {f('reciprocal_rank')} |")
        for method, values in summary["baseline_metrics"].items():
            a = values[scope]["aggregate"]
            l = a["localization"]
            lines.append(f"| {method} | {fmt(a['macro_auroc'])} | {fmt(l['top1'])} | {fmt(l['top3'])} | {fmt(l['reciprocal_rank'])} |")
        lines.append("")
    lines += ["### Per-task learned AUROC (mean +/- std over seeds)", "",
              "| Method | Task 9 | Task 25 | Task 48 |", "|---|---|---|---|"]
    for method, per_seed in summary["learned_metrics_by_seed"].items():
        cells = []
        for task in TASKS:
            stat = number_stats(v["all_agent_steps"]["tasks"][task]["auroc_error_positive"] for v in per_seed.values())
            cells.append(f"{fmt(stat['mean'])} +/- {fmt(stat['std'])}")
        lines.append(f"| {method} | " + " | ".join(cells) + " |")
    lines += ["", "The complete per-seed/per-task average precision, detection/false-alarm rates and localization "
              "denominators are in summary.json. per_step.csv preserves every prediction and seed.", "",
              "## Limits and interpretation", "",
              "- Baselines NIBS/A/C4 have known-successful same-task references at evaluation; learned inference has only its query. This is an explicit difference in inference resources.",
              "- Labels cover selected gold reads/writes and a fixed transfer message. Unknown steps are not assumed correct. Localization targets the first verifier-labelled executed incorrect step, not proven causal failure.",
              f"- Binary labels: {summary['label_counts']}. Most steps lack correctness labels.",
              "- Almost all incorrect steps use a tool absent from successful runs. Only one difficult wrong-booking example exists in this three-task evaluation.",
              "- The available number of graphs is far below the paper's training scale. Three seeds describe training variability, not statistical confidence intervals.",
              "- C4's messages remain exploratory. A good consensus fit does not establish calibrated correctness probabilities.",
              "- Both GCN layers can use the complete recorded trajectory. This prototype is an offline diagnostic, not a causal online monitor.",
              "- Compare with direct consensus as well as NIBS: learning can lose useful reference information or generalize poorly. No improvement is assumed.", "",
              "## Training and acceptance checks", "",
              f"BERT unique texts: {summary['features']['n_unique_texts']}; texts truncated at 256 tokens: {summary['features']['n_texts_truncated']}.",
              f"Trained models: {len(summary['training'])}. Every best checkpoint reloads with identical test predictions, weights change, and scores are finite in [0,1].", "",
              "| Method | Held-out task | Seed | Train / validation / test graphs | Best epoch | Validation loss |", "|---|---|---|---|---|---|"]
    for t in summary["training"]:
        lines.append(f"| {t['method']} | {t['heldout_task']} | {t['seed']} | {t['n_train']} / {t['n_validation']} / {t['n_test']} | {t['best_epoch']} | {fmt(t['best_validation_loss'])} |")
    lines += ["", "Split, target-reference and source-file hashes are in manifest.json. Checkpoints include architecture, "
              "BERT revision, split IDs and learned weights. Training histories are in training_history.json.", "",
              "## Reproduce and use", "", "```bash", "uv venv .venv --python python3.12",
              "uv pip install --python .venv/bin/python -r gibs/requirements-learned.txt",
              ".venv/bin/python -m gibs.learned.run_experiment", "```", "",
              "See gibs/learned/README.md for standalone query-only prediction and the complete paper/adaptation explanation. "
              "The baseline protocol is gibs/learned/EVALUATION_PLAN.md. Independent human review remains the next validity step.", ""]
    return "\n".join(lines)


def run(args):
    torch.set_num_threads(2)
    started = time.perf_counter()
    runs, base_rows, dataset = load_dataset()
    teachers = StoredTeachers(runs)
    bert = FrozenBert(device=args.feature_device)
    features = prepare_features(runs, bert)
    args.output.mkdir(parents=True, exist_ok=True)
    split_manifest, training, histories, predictions, learned = {}, [], {}, [], {}
    for method in TEACHERS:
        method_predictions = defaultdict(list)
        for heldout in TASKS:
            split = fold_split(runs, heldout)
            targets, target_refs = {}, {}
            for part in ("train", "validation"):
                for q in split[part]:
                    targets[q["id"]], target_refs[q["id"]] = teachers.target(method, q, split["train"])
            test_ids = {r["id"] for r in split["test"]}
            train_ids = {r["id"] for r in split["train"]}
            val_ids = {r["id"] for r in split["validation"]}
            assert not test_ids & (train_ids | val_ids | set(targets))
            assert all(set(ids) <= train_ids for ids in target_refs.values())
            fold_key = f"{method}_heldout{heldout}"
            split_manifest[fold_key] = {part: [r["id"] for r in split[part]] for part in split}
            split_manifest[fold_key]["target_references"] = target_refs
            for seed in args.seeds:
                print(f"Training {fold_key} seed {seed} ({len(train_ids)} train, {len(val_ids)} validation)", flush=True)
                model, details = train_model(split, features, targets, seed, args.epochs, args.patience)
                checkpoint = {"state_dict": model.state_dict(), "model_config": model.config,
                              "bert_model": BERT_MODEL, "bert_revision": BERT_REVISION, "max_length": MAX_LENGTH,
                              "method": method, "heldout_task": heldout, "seed": seed,
                              "train_ids": sorted(train_ids), "validation_ids": sorted(val_ids),
                              "best_epoch": details["best_epoch"]}
                ckpt_path = args.output / f"checkpoints/{fold_key}_seed{seed}.pt"
                ckpt_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(checkpoint, ckpt_path)
                reloaded = load_predictor(ckpt_path)[0]
                scores = {}
                for q in split["test"]:
                    original = predict_graph(model, features[q["id"]])
                    restored = predict_graph(reloaded, features[q["id"]])
                    if original != restored:
                        raise ValueError("checkpoint prediction failed exact reload verification")
                    scores[q["id"]] = original
                for row in base_rows:
                    if row["run_id"] in test_ids:
                        method_predictions[str(seed)].append({**row, "method": f"gibs_{method}", "seed": seed,
                                                             "heldout_task": heldout,
                                                             "confidence": scores[row["run_id"]][row["step_index"]]})
                histories[f"{fold_key}_seed{seed}"] = details.pop("history")
                training.append({"method": method, "heldout_task": heldout, **details,
                                 "n_train": len(train_ids), "n_validation": len(val_ids), "n_test": len(test_ids),
                                 "checkpoint": str(ckpt_path.relative_to(args.output))})
                print(f"  best epoch {details['best_epoch']}, validation loss {details['best_validation_loss']:.4f}, {details['seconds']:.1f}s", flush=True)
        learned[f"gibs_{method}"] = {}
        for seed, rows in method_predictions.items():
            if len(rows) != len(base_rows) or len({(r["run_id"], r["step_index"]) for r in rows}) != len(rows):
                raise ValueError("out-of-fold predictions do not cover every query exactly once")
            learned[f"gibs_{method}"][seed] = evaluate(rows)[0]
            predictions.extend(rows)
    baseline_metrics = {}
    for name, teacher in (("nibs", None), ("consensus_A", "paper_style"), ("consensus_C4", "agent_adapted")):
        if teacher is None:
            rows = [dict(r) for r in base_rows]
        else:
            score_map = {q["id"]: teachers.target(teacher, q, runs)[0].tolist() for q in runs}
            rows = [{**r, "confidence": score_map[r["run_id"]][r["step_index"]]} for r in base_rows]
        baseline_metrics[name] = evaluate(rows)[0]
        predictions.extend({**r, "method": name, "seed": "", "heldout_task": ""} for r in rows)
    for method in ("random_expected", "last_step_first"):
        baseline_metrics[method] = evaluate(base_rows, method)[0]
    counts = defaultdict(int)
    for row in base_rows:
        counts[row["verifier_label"]] += 1
    summary = {"evaluation_plan": "gibs/learned/EVALUATION_PLAN.md", "n_queries": len(runs),
               "n_agent_steps": len(base_rows), "label_counts": dict(counts), "features": bert.description,
               "seeds": args.seeds, "epochs_limit": args.epochs, "patience": args.patience,
               "dataset": dataset["tasks"], "training": training,
               "learned_metrics_by_seed": learned,
               "learned_aggregate": {name: aggregate_seed_metrics(values) for name, values in learned.items()},
               "baseline_metrics": baseline_metrics, "total_seconds": time.perf_counter() - started,
               "runtime": {"torch": torch.__version__, "numpy": np.__version__, "gcn_device": "cpu"}}
    write_json(args.output / "summary.json", summary)
    write_json(args.output / "training_history.json", histories)
    write_json(args.output / "manifest.json", {"dataset": dataset, "splits": split_manifest,
                "split_seed": SPLIT_SEED, "stored_teacher_files_sha256": teachers.provenance,
                "source_sha256": {f: file_hash(REPO / f) for f in SOURCE_FILES},
                "checkpoints_sha256": {t["checkpoint"]: file_hash(args.output / t["checkpoint"]) for t in training},
                "bert_model": BERT_MODEL, "bert_revision": BERT_REVISION})
    write_csv(args.output / "per_step.csv", predictions, list(predictions[0]))
    (args.output / "REPORT.md").write_text(build_report(summary))
    for name, metrics in summary["learned_aggregate"].items():
        m = metrics["all_agent_steps"]
        print(f"{name}: mean macro AUROC {fmt(m['macro_auroc']['mean'])}, mean top1 {fmt(m['top1']['mean'])}")
    print(f"Report: {args.output / 'REPORT.md'}", flush=True)


def load_predictor(path):
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if (checkpoint["bert_model"], checkpoint["bert_revision"], checkpoint["max_length"]) != (BERT_MODEL, BERT_REVISION, MAX_LENGTH):
        raise ValueError("checkpoint BERT feature specification is incompatible")
    model = GIBSPredictor(**checkpoint["model_config"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint


def predict(args):
    torch.set_num_threads(2)
    model, checkpoint = load_predictor(args.checkpoint)
    data = json.loads(args.results.read_text())
    matches = [s for s in data.get("simulations", []) if str(s.get("id", "")).startswith(args.run_id)]
    if len(matches) != 1:
        raise ValueError("run ID prefix must identify exactly one trajectory")
    raw = matches[0]
    # Strip all outcomes, gold tasks and provider metadata before feature extraction.
    sim = {"id": raw["id"], "task_id": raw["task_id"], "messages": raw.get("messages") or []}
    spec = graph_texts(sim)
    bert = FrozenBert(device=args.feature_device)
    embeddings = bert.encode(spec["result_texts"] + spec["operation_texts"])
    scores = predict_graph(model, tensor_graph(spec, embeddings))
    write_json(args.output, {"run_id": sim["id"], "task_id": sim["task_id"], "method": checkpoint["method"],
                            "checkpoint": str(args.checkpoint), "checkpoint_sha256": file_hash(args.checkpoint),
                            "requires_references": False, "uses_gold_labels": False,
                            "steps": [{"step_index": i, "event_id": event, "confidence": score}
                                      for i, (event, score) in enumerate(zip(spec["agent_events"], scores))]})
    print(f"Scored {len(scores)} agent steps using the query graph only: {args.output}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    prediction = sub.add_parser("predict")
    prediction.add_argument("--checkpoint", type=Path, required=True)
    prediction.add_argument("--results", type=Path, required=True)
    prediction.add_argument("--run-id", required=True)
    prediction.add_argument("--output", type=Path, default=DEFAULT_OUT / "prediction.json")
    prediction.add_argument("--feature-device", choices=("cpu", "mps"), default="cpu")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--feature-device", choices=("cpu", "mps"), default="mps" if torch.backends.mps.is_available() else "cpu")
    args = parser.parse_args(argv)
    if args.command == "predict":
        predict(args)
    else:
        if args.epochs < 1 or args.patience < 1 or len(set(args.seeds)) != len(args.seeds):
            parser.error("positive epoch/patience counts and distinct seeds required")
        run(args)


if __name__ == "__main__":
    main()
