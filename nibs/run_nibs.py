"""
Run NIBS scoring on one or more tau2-bench results.json files.

Usage:
    python run_nibs.py <results.json> [<results2.json> ...] [--aggregation max|mean] [--k-min 3] [--output out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parsing.parser import parse_results_file
from scoring.nibs import score_task
from similarity.similarity import tool_sim


def avg_score(r):
    ss = r["step_scores"]
    return sum(s["score"] for s in ss) / len(ss) if ss else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, nargs="+")
    parser.add_argument("--aggregation", default="max", choices=["max", "mean"])
    parser.add_argument("--k-min", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    # Load and merge all files, exclude infra errors (reward=None)
    trajs = [t for path in args.results for t in parse_results_file(path) if t["reward"] is not None]

    by_task: dict[str, list[dict]] = defaultdict(list)
    for t in trajs:
        by_task[t["task_id"]].append(t)

    print(f"Tasks: {sorted(by_task.keys(), key=int)}\n")

    all_results = {}
    for task_id in sorted(by_task.keys(), key=int):
        out = score_task(by_task[task_id], tool_sim, aggregation=args.aggregation, k_min=args.k_min)
        all_results[task_id] = out

        if out["skipped"]:
            print(f"Task {task_id}: SKIPPED — {out['reason']}")
            continue

        success_r = [r for r in out["results"] if r["success"]]
        fail_r    = [r for r in out["results"] if not r["success"]]
        avg_s = sum(avg_score(r) for r in success_r) / len(success_r) if success_r else 0.0
        avg_f = sum(avg_score(r) for r in fail_r)    / len(fail_r)    if fail_r    else 0.0

        print(f"Task {task_id}: successes={len(success_r)}  fails={len(fail_r)}")
        print(f"  avg score — success: {avg_s:.3f}  fail: {avg_f:.3f}  gap: {avg_s - avg_f:+.3f}\n")

    if args.output:
        args.output.write_text(json.dumps(all_results, indent=2))
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
