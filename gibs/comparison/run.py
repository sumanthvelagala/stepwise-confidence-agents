"""Unified paper NIBS / PDF-GIBS / C4 prototype and graph ablation.

    .venv/bin/python -m gibs.comparison.run
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import random
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch

from gibs.comparison.graphs import export_diagram, projection, spec, tensors
from gibs.comparison.released_model import ReleasedPredictor, released_loss
from gibs.comparison.semantic_nibs import score_dataset
from gibs.learned.data import (BERT_MODEL, BERT_REVISION, MAX_LENGTH, TASKS, FrozenBert, StoredTeachers, fold_split)
from gibs.learned.model import GIBSPredictor, gib_loss
from gibs.learned.run_experiment import aggregate_seed_metrics, evaluate, predict_graph, set_seed
from nibs.run_evaluation import (REPO, deduplicate, file_hash, fmt, load_runs, score_queries, write_csv, write_json)

ALL_TASKS = ("3", "9", "25", "40", "48")
EXTERNAL_TASKS = ("3", "40")
OUT = REPO / "results/paper_comparison"
METHODS = {"paper_gibs_pdf": ("paper_style", "original"),
           "c4_gibs": ("agent_adapted", "original"),
           "c4_state_graph": ("agent_adapted", "state_aware"),
           "released_gibs_control": ("edge_membership", "original")}
SEEDS = (7, 17, 27)


def load_data():
    loaded, excluded, inputs, identities = load_runs(REPO / "results", ALL_TASKS)
    reps, counts = deduplicate(loaded)
    rows, runs, skipped, references = score_queries(reps, 3)
    if skipped:
        raise ValueError("unexpected reference-count exclusion")
    return runs, rows, {"counts": counts, "excluded": excluded, "input_sha256": inputs,
                        "task_identities": identities, "evaluation_references": references}


def prepare(runs, device):
    specs, graphs = {}, {}
    for structure in ("original", "state_aware"):
        graphs[structure] = {r["id"]: projection(r["_sim"], structure) for r in runs}
        specs[structure] = {sid: spec(graph) for sid, graph in graphs[structure].items()}
        for r in runs:
            if specs[structure][r["id"]]["agent_events"] != [n["id"] for n in r["nodes"]]:
                raise ValueError("graph event alignment mismatch")
    texts = [text for family in specs.values() for s in family.values()
             for field in ("result_texts", "operation_texts") for text in s[field]]
    bert = FrozenBert(device=device)
    embeddings = bert.encode(texts)
    features = {structure: {sid: tensors(s, embeddings) for sid, s in family.items()} for structure, family in specs.items()}
    return features, specs, graphs, bert.description


def external_split(runs):
    # Reuse the fixed task/outcome split rule, reserving both additional tasks.
    training_pool = [r for r in runs if r["task_id"] in TASKS]
    # Use a sentinel to invoke the fixed core-task validation rule, then replace
    # its test partition. Neither additional task enters the fitting pool.
    sentinel = {**training_pool[0], "id": "external_partition_sentinel", "task_id": "external",
                "content_hash": "external_partition_sentinel"}
    split = fold_split(training_pool + [sentinel], "external")
    split["test"] = [r for r in runs if r["task_id"] in EXTERNAL_TASKS]
    return split


class EdgeTeachers:
    def __init__(self):
        self.data = {}
        for task in TASKS:
            path = REPO / f"gibs/validation/results_pilot/task{task}_A.json"
            for q in json.loads(path.read_text())["queries"]:
                self.data[q["query"]] = {p["reference"]: p["edge_map"] for p in q["per_reference"]}

    def target(self, q, pool, edge_ids):
        refs = [r for r in pool if r["success"] and r["task_id"] == q["task_id"] and r["content_hash"] != q["content_hash"]]
        if len(refs) < 3:
            raise ValueError("insufficient training-only edge references")
        masks = [torch.tensor([edge in self.data[q["id"]][r["id"]] for edge in edge_ids], dtype=torch.float32) for r in refs]
        return masks, [r["id"] for r in refs]


def fit(split, features, targets, method, seed, epochs=150):
    set_seed(seed)
    model = ReleasedPredictor() if method == "released_gibs_control" else GIBSPredictor()
    initial = {k: v.clone() for k, v in model.state_dict().items()}
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    best, best_state, best_epoch, stale, history = math.inf, None, 0, 0, []

    def loss(q):
        graph = features[q["id"]]
        if isinstance(model, ReleasedPredictor):
            return released_loss(model.forward_edges(graph), targets[q["id"]])
        return gib_loss(model(graph), targets[q["id"]])[0]

    for epoch in range(1, epochs + 1):
        model.train()
        order = list(split["train"])
        random.Random(seed + epoch).shuffle(order)
        losses = []
        for start in range(0, len(order), 8):
            batch = order[start:start + 8]
            optimizer.zero_grad()
            objective = torch.stack([loss(q) for q in batch]).mean()
            if not torch.isfinite(objective):
                raise ValueError("nonfinite training loss")
            objective.backward()
            optimizer.step()
            losses.extend([objective.item()] * len(batch))
        model.eval()
        with torch.no_grad():
            validation = torch.stack([loss(q) for q in split["validation"]]).mean().item()
        if not math.isfinite(validation):
            raise ValueError("nonfinite validation loss")
        history.append({"epoch": epoch, "train_loss": statistics.mean(losses), "validation_loss": validation})
        if validation < best - 1e-5:
            best, best_state, best_epoch, stale = validation, copy.deepcopy(model.state_dict()), epoch, 0
        else:
            stale += 1
        if stale >= 20:
            break
    model.load_state_dict(best_state)
    model.eval()
    changed = max(float((best_state[k] - initial[k]).abs().max()) for k in initial)
    if changed == 0:
        raise ValueError("predictor did not train")
    return model, {"best_epoch": best_epoch, "validation_loss": best,
                   "max_weight_change": changed, "epochs": len(history), "history": history}


def report(summary):
    lines = ["# Paper NIBS, paper GIBS and C4: real-data prototype", "",
             "**Retrospective benchmark experiment; automatic labels; independent human validation outstanding.**", "",
             "## What is implemented", "",
             "| Method | Implementation | Status relative to paper |", "|---|---|---|",
             "| paper_nibs_cos_max / mean | BERT cosine, within-reference max/mean, average over successful references | PDF Eq. 2 semantic NIBS on agent operations |",
             "| paper_gibs_pdf | BERT + two GCN layers; entropy + soft CE to A m_node | PDF architecture/objective; explicit agent graph/fusion choices |",
             "| c4_gibs | Same GCN; C4 m_ctx targets | Project adaptation, not a paper method |",
             "| c4_state_graph | Same C4 targets, revised predictor graph | Separate graph ablation; original C4 preserved |",
             "| released_gibs_control | Active author MLP/pooling forward and balanced edge-mask loss | Code-equation control; common training mixture/splits differ from release |",
             "| released_nibs_cos_max / mean | Author inverse-cosine-distance formulas, reference edges incl. multiplicity | Code-formula controls |",
             "| tool_sim_nibs | Existing tool names/arguments comparison | Agent baseline, NOT the paper's semantic NIBS |", "",
             "The paper and released script are not identical. The PDF describes a GCN; the release's active forward uses "
             "MLPs/mean pooling. Both are exposed rather than silently substituting one. The release also trains failed graphs "
             "only and skips supervision above 15 nodes; this controlled runner uses mixed graphs and complete stored mappings. "
             "No claim of exact original math/QA benchmark replication is made.", "",
             "## Evaluation populations", "",
             f"All data: {summary['n_runs']} distinct trajectories, {summary['n_steps']} agent steps. "
             "Recorded tau2-bench Airline, Groq agent/user at temperature 0; missing rewards and exact duplicates excluded.", "",
             "- **Core OOF:** tasks 9/25/48, each test task excluded from fitting and validation; 3 seeds.",
             "- **Additional cases:** tasks 3/40, excluded from training and validation in a separate experiment trained on 9/25/48. "
             "These were previously inspected in NIBS work, so they are not untouched holdouts.",
             "- Successful references for training targets come only from the training partition. Reference baselines use known-successful "
             "same-task runs at evaluation; learned inference uses only the query graph.",
             "- Stored real DeBERTa/MCS mappings supply core-task targets; this run does not recompute NLI or invent targets for additional tasks.", ""]
    for population, data in summary["populations"].items():
        lines += [f"## {population}", "", f"Label counts: `{data['label_counts']}`. "
                  "Unknown and attempted errors are excluded from binary metrics; unknown steps still compete in localization.", ""]
        for scope in ("tool_calls", "all_agent_steps"):
            lines += [f"### {scope.replace('_', ' ')}", "",
                      "| Method | Macro AUROC | Top-1 | Top-3 | MRR |", "|---|---|---|---|---|"]
            for method, per_seed in data["learned"].items():
                agg = aggregate_seed_metrics(per_seed)[scope]
                display = lambda k: f"{fmt(agg[k]['mean'])} +/- {fmt(agg[k]['std'])}"
                lines.append(f"| {method} | {display('macro_auroc')} | {display('top1')} | {display('top3')} | {display('reciprocal_rank')} |")
            for method, metrics in data["baselines"].items():
                a = metrics[scope]["aggregate"]
                l = a["localization"]
                lines.append(f"| {method} | {fmt(a['macro_auroc'])} | {fmt(l['top1'])} | {fmt(l['top3'])} | {fmt(l['reciprocal_rank'])} |")
            lines.append("")
        lines += ["All learned results are mean +/- population standard deviation over seeds, not confidence intervals. "
                  "Macro AUROC averages only tasks containing both explicit correctness labels; inspect summary.json denominators. "
                  "Additional task 3 has no labelled executed error, so its AUROC/localization is undefined.", ""]
    lines += ["## Graph experiment", "",
              "Original C4 matcher/targets remain unchanged. The separate state graph uses the latest prior non-error tool "
              "observation containing an argument value, and links messages to the most recent user and tool observation. "
              "All dependency edges point forward. This is a heuristic representation, not causal or policy verification.", "",
              "Compare c4_state_graph against c4_gibs: only predictor adjacency changes, while text features, targets, splits, "
              "seeds and optimization stay fixed. A gain or loss is reported as observed, not selected away.", "",
              "Example diagrams and edge lists are in graphs/. They include failed/successful cases from additional tasks 3/40 "
              "as well as familiar tasks 25/48. These demonstrations are not independent accuracy evidence.", "",
              "## Limits", "",
              "- Small data, previously exposed task scenarios, incomplete rule labels and very few same-tool wrong-argument examples.",
              "- Paper algorithms are applied to an agent graph adapter; the original paper datasets, generated reasoning graphs, "
              "2,000-graph training scale and full evaluation are not reproduced.",
              "- Cosine scores and learned masks are not established calibrated correctness probabilities. Raw cosine can be negative.",
              "- A high AUROC on tools absent from successful references does not establish subtle action-error detection.",
              "- The first verifier-labelled incorrect action is a localization proxy; omissions and policy/message mistakes may remain unlabelled.",
              "- BERT is frozen. Text truncation and representation may lose exact dates/IDs; the learned C4 model does not enforce its teacher's field checks at inference.",
              "- Complete the existing independent human-review sheet before making human-validated claims.", "",
              "## Reproduce", "", "```bash", ".venv/bin/python -m gibs.comparison.run", "```", "",
              "See gibs/comparison/README.md and EVALUATION_PLAN.md. Per-step predictions, metrics, trained checkpoints, "
              "histories and provenance are stored alongside this report. Earlier results are preserved.", ""]
    return "\n".join(lines)


def run(args):
    torch.set_num_threads(2)
    started = time.perf_counter()
    from gibs.comparison.verify_sources import verify
    write_json(args.output / "source_verification.json", verify())
    runs, base_rows, provenance = load_data()
    core = [r for r in runs if r["task_id"] in TASKS]
    teachers, edge_teachers = StoredTeachers(core), EdgeTeachers()
    features, specs, graphs, bert = prepare(runs, args.feature_device)
    semantic, references = score_dataset(runs, features["original"])
    write_json(args.output / "semantic_nibs_scores.json", semantic)
    write_json(args.output / "semantic_references.json", references)
    population_splits = {"core_oof": {task: fold_split(core, task) for task in TASKS},
                         "additional_cases": {"external3_40": external_split(runs)}}
    all_predictions, summaries, manifest, histories = [], {}, {}, {}
    for population, splits in population_splits.items():
        test_ids = {r["id"] for split in splits.values() for r in split["test"]}
        base = [r for r in base_rows if r["run_id"] in test_ids]
        baseline_metrics = {}
        for name, scores in {"tool_sim_nibs": None, **semantic}.items():
            rows = [dict(r) if scores is None else {**r, "confidence": scores[r["run_id"]][r["step_index"]]} for r in base]
            baseline_metrics[name] = evaluate(rows)[0]
            all_predictions.extend({**r, "population": population, "method": name, "seed": ""} for r in rows)
        for name in ("random_expected", "last_step_first"):
            baseline_metrics[name] = evaluate(base, name)[0]
        if population == "core_oof":
            for name, teacher in (("direct_A", "paper_style"), ("direct_C4", "agent_adapted")):
                scores = {q["id"]: teachers.target(teacher, q, core)[0].tolist() for q in core}
                baseline_metrics[name] = evaluate([{**r, "confidence": scores[r["run_id"]][r["step_index"]]} for r in base])[0]
        learned = {}
        for method, (teacher, structure) in METHODS.items():
            seeded = defaultdict(list)
            for fold, split in splits.items():
                train_ids = {r["id"] for r in split["train"]}
                validation_ids = {r["id"] for r in split["validation"]}
                fold_test_ids = {r["id"] for r in split["test"]}
                if train_ids & validation_ids or fold_test_ids & (train_ids | validation_ids):
                    raise ValueError("split leakage")
                targets, target_references = {}, {}
                for q in split["train"] + split["validation"]:
                    if teacher == "edge_membership":
                        targets[q["id"]], target_references[q["id"]] = edge_teachers.target(q, split["train"], specs["original"][q["id"]]["edge_ids"])
                    else:
                        targets[q["id"]], target_references[q["id"]] = teachers.target(teacher, q, split["train"])
                if not all(set(ids) <= train_ids for ids in target_references.values()):
                    raise ValueError("target reference leakage")
                key = f"{population}_{method}_{fold}"
                manifest[key] = {part: [r["id"] for r in split[part]] for part in split}
                manifest[key]["target_references"] = target_references
                for seed in args.seeds:
                    print(f"{key} seed {seed}", flush=True)
                    model, details = fit(split, features[structure], targets, method, seed, args.epochs)
                    path = args.output / f"checkpoints/{key}_seed{seed}.pt"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    checkpoint = {"state_dict": model.state_dict(), "model_config": model.config,
                                  "architecture": "released_control" if isinstance(model, ReleasedPredictor) else "pdf_gcn",
                                  "structure": structure, "method": method, "population": population, "seed": seed,
                                  "bert_model": BERT_MODEL, "bert_revision": BERT_REVISION, "max_length": MAX_LENGTH,
                                  "train_ids": sorted(train_ids), "validation_ids": sorted(validation_ids),
                                  "test_ids": sorted(fold_test_ids)}
                    torch.save(checkpoint, path)
                    loaded = load_checkpoint(path)
                    scores = {q["id"]: predict_graph(model, features[structure][q["id"]]) for q in split["test"]}
                    if any(scores[q["id"]] != predict_graph(loaded[0], features[structure][q["id"]]) for q in split["test"]):
                        raise ValueError("checkpoint reload mismatch")
                    for row in base:
                        if row["run_id"] in fold_test_ids:
                            seeded[str(seed)].append({**row, "confidence": scores[row["run_id"]][row["step_index"]],
                                                      "population": population, "method": method, "seed": seed})
                    histories[f"{key}_seed{seed}"] = details
            learned[method] = {}
            for seed, rows in seeded.items():
                if len(rows) != len(base) or len({(r["run_id"], r["step_index"]) for r in rows}) != len(base):
                    raise ValueError("unequal evaluation populations")
                learned[method][seed] = evaluate(rows)[0]
                all_predictions.extend(rows)
        summaries[population] = {"n_runs": len(test_ids), "n_steps": len(base), "label_counts": dict(Counter(r["verifier_label"] for r in base)),
                                  "baselines": baseline_metrics, "learned": learned}
    # Export cases by task/outcome and UUID only, before inspecting individual scores.
    graph_audit = []
    for task in ("3", "25", "40", "48"):
        for success in (False, True):
            candidates = sorted([r for r in runs if r["task_id"] == task and r["success"] == success], key=lambda r: r["id"])
            if not candidates:
                continue
            q = candidates[0]
            path = args.output / f"graphs/task{task}_{'success' if success else 'failed'}_{q['id'][:8]}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            original, revised = (graphs[g][q["id"]] for g in ("original", "state_aware"))
            path.write_text(f"# Task {task}, {'successful' if success else 'failed'} run {q['id']}\n\n"
                            + export_diagram(original, "Original graph") + "\n" + export_diagram(revised, "State/context graph ablation"))
            write_json(path.with_suffix(".json"), {"original": original.to_dict(), "state_aware": revised.to_dict()})
            graph_audit.append({"task": task, "run_id": q["id"], "success": success,
                                "nodes": len(original.nodes), "original_edges": len(original.edges), "state_edges": len(revised.edges)})
    summary = {"evaluation_plan": "gibs/comparison/EVALUATION_PLAN.md", "n_runs": len(runs), "n_steps": len(base_rows),
               "seeds": args.seeds, "epochs": args.epochs, "bert": bert, "populations": summaries,
               "graph_examples": graph_audit, "seconds": time.perf_counter() - started}
    write_json(args.output / "summary.json", summary)
    write_json(args.output / "training_histories.json", histories)
    sources = [*sorted((REPO / "gibs/comparison").glob("*.py")), REPO / "gibs/comparison/EVALUATION_PLAN.md",
               REPO / "gibs/learned/data.py", REPO / "gibs/learned/model.py", REPO / "gibs/learned/run_experiment.py",
               REPO / "gibs/graph/step_graph.py", REPO / "gibs/graph/event_projection.py",
               REPO / "gibs/validation/step_verification_v2.py", REPO / "gibs/validation/step_verification.py",
               REPO / "gibs/mcs/structured_fields.py", REPO / "nibs/evaluation_metrics.py", REPO / "nibs/run_evaluation.py"]
    write_json(args.output / "manifest.json", {"data": provenance, "splits": manifest, "stored_teachers": teachers.provenance,
                 "source_sha256": {str(p.relative_to(REPO)): file_hash(p) for p in sources},
                 "checkpoint_sha256": {str(p.relative_to(args.output)): file_hash(p) for p in (args.output / "checkpoints").glob("*.pt")}})
    write_csv(args.output / "per_step.csv", all_predictions, list(all_predictions[0]))
    (args.output / "REPORT.md").write_text(report(summary))
    print(f"Finished: {len(histories)} trained models; {len(runs)} distinct runs. {args.output / 'REPORT.md'}", flush=True)


def load_checkpoint(path):
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if (checkpoint["bert_model"], checkpoint["bert_revision"], checkpoint["max_length"]) != (BERT_MODEL, BERT_REVISION, MAX_LENGTH):
        raise ValueError("incompatible BERT features")
    if checkpoint["architecture"] not in ("released_control", "pdf_gcn"):
        raise ValueError("unknown predictor architecture")
    cls = ReleasedPredictor if checkpoint["architecture"] == "released_control" else GIBSPredictor
    model = cls(**checkpoint["model_config"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--feature-device", choices=("cpu", "mps"), default="mps" if torch.backends.mps.is_available() else "cpu")
    args = parser.parse_args()
    if args.epochs < 1 or len(set(args.seeds)) != len(args.seeds):
        parser.error("positive epochs and distinct seeds required")
    run(args)


if __name__ == "__main__":
    main()
