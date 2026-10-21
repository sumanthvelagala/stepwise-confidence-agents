"""
Run GIBS scoring on one or more tau2-bench results.json files.

Usage:
    python run_gibs.py <results.json> [<results2.json> ...] [--k-min 3] [--output out.json]

Compares GIBS gap vs NIBS gap to show improvement from graph-aware scoring.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nibs.parsing.parser import parse_results_file
from nibs.scoring.nibs import score_task as nibs_score_task
from nibs.similarity.similarity import tool_sim

from gibs.graph.builder import build_graph
from gibs.scoring.gibs import score_task as gibs_score_task
from gibs.similarity.graph_sim import batch_embed_graphs


def avg_score(r: dict, label: str) -> float:
    if label == "GIBS":
        return r.get("run_score", 0.0)
    ss = r["step_scores"]
    return sum(s["score"] for s in ss) / len(ss) if ss else 0.0


def print_task_results(task_id: str, out: dict, label: str) -> tuple[float, float]:
    if out["skipped"]:
        print(f"  [{label}] Task {task_id}: SKIPPED — {out['reason']}")
        return 0.0, 0.0
    success_r = [r for r in out["results"] if r["success"]]
    fail_r    = [r for r in out["results"] if not r["success"]]
    avg_s = sum(avg_score(r, label) for r in success_r) / len(success_r) if success_r else 0.0
    avg_f = sum(avg_score(r, label) for r in fail_r)    / len(fail_r)    if fail_r    else 0.0
    gap   = avg_s - avg_f
    print(f"  [{label}] pass={avg_s:.3f}  fail={avg_f:.3f}  gap={gap:+.3f}  "
          f"(n_pass={len(success_r)} n_fail={len(fail_r)})")
    return avg_s, avg_f


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, nargs="+")
    parser.add_argument("--k-min", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    # Load trajectories, exclude infra errors, deduplicate by (task_id, trial)
    seen: set[tuple] = set()
    trajs = []
    for path in args.results:
        for t in parse_results_file(path):
            if t["reward"] is None:
                continue
            key = (t["task_id"], t["trial"])
            if key in seen:
                continue
            seen.add(key)
            trajs.append(t)

    by_task: dict[str, list] = defaultdict(list)
    for t in trajs:
        by_task[t["task_id"]].append(t)

    print(f"Loaded {len(trajs)} trajectories across tasks: {sorted(by_task.keys(), key=int)}")

    # Build all graphs and batch embed once (single MiniLM forward pass)
    all_graphs_by_task = {tid: [build_graph(t) for t in tlist] for tid, tlist in by_task.items()}
    all_graphs = [g for glist in all_graphs_by_task.values() for g in glist]
    print(f"Embedding {len(all_graphs)} graphs with MiniLM... ", end="", flush=True)
    batch_embed_graphs(all_graphs)
    print("done.\n")

    all_results = {}
    nibs_gaps, gibs_gaps = [], []

    for task_id in sorted(by_task.keys(), key=int):
        task_trajs = by_task[task_id]
        print(f"Task {task_id}:")

        # NIBS
        nibs_out = nibs_score_task(task_trajs, tool_sim, k_min=args.k_min)
        ns, nf = print_task_results(task_id, nibs_out, "NIBS")

        # GIBS — use pre-embedded graphs
        graphs = all_graphs_by_task[task_id]
        gibs_out = gibs_score_task(graphs, k_min=args.k_min)
        gs, gf = print_task_results(task_id, gibs_out, "GIBS")

        if not nibs_out["skipped"] and not gibs_out["skipped"]:
            nibs_gaps.append(ns - nf)
            gibs_gaps.append(gs - gf)

        all_results[task_id] = {"nibs": nibs_out, "gibs": gibs_out}
        print()

    if nibs_gaps and gibs_gaps:
        print("=" * 50)
        print(f"Mean gap — NIBS: {sum(nibs_gaps)/len(nibs_gaps):+.3f}  "
              f"GIBS: {sum(gibs_gaps)/len(gibs_gaps):+.3f}")

    if args.output:
        args.output.write_text(json.dumps(all_results, indent=2))
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
