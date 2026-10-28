"""
Dataset audit (Milestone: independent validation, Phase 1). Read-only over results/**/results.json.

    .venv/bin/python -B gibs/validation/dataset_audit.py     # -> gibs/validation/results_audit/dataset_audit.json

No NLI, no MCS, no label changes. Step labels below are produced by the EXISTING, unchanged rules in
step_verification.py (written for T48/T9/T25); for other tasks they are rule-derived candidates, not verified labels.
Security: the `info` block of results files can contain credentials; only agent/user model names and temperature are
read from it, and nothing from it is written.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.step_graph import build_step_graph  # noqa: E402
from gibs.mcs.structured_fields import WRITE_TOOLS  # noqa: E402
from gibs.validation.step_verification import classify_steps  # noqa: E402

OUT = REPO / "gibs/validation/results_audit"
DEV_TASKS = {  # tasks used while developing A / C0–C6 (see DATASET_AUDIT.md §5)
    "48": "pilot; validation pairs V1,V2; NLI probe; v0.1 example; tests",
    "9": "pilot; validation pair V6; tests",
    "25": "pilot; validation pair V4; NLI probe; tests",
    "40": "validation pair V3; NLI probe; tests",
    "34": "validation pair V5; NLI probe",
    "4": "validation pairs V7,V8; tests",
    "38": "validation pair V9; pilot cost screening",
    "3": "NLI probe",
}
EARLIER_EXPOSURE = {"1": "NIBS / earlier GIBS scores", "2": "earlier GIBS scores", "5": "earlier GIBS scores"}


def canon(sim: dict) -> str:
    """Content of a trajectory without ids/timestamps: roles, texts, tool calls (name + args), tool outputs."""
    out = []
    for m in sim.get("messages") or []:
        calls = [(c.get("name"), json.dumps(c.get("arguments") or {}, sort_keys=True)) for c in (m.get("tool_calls") or [])]
        out.append((m.get("role"), (m.get("content") or "").strip(), calls, bool(m.get("error"))))
    return hashlib.sha256(json.dumps(out, ensure_ascii=False).encode()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files, sims, tasks_def = [], {}, {}
    uuid_seen = Counter()
    for f in sorted(glob.glob(str(REPO / "results/**/results.json"), recursive=True)):
        rel = str(Path(f).relative_to(REPO))
        d = json.load(open(f))
        info = d.get("info") or {}
        ai = info.get("agent_info") or {}
        regime = f"{ai.get('llm')} T={(ai.get('llm_args') or {}).get('temperature')}"
        files.append({"file": rel, "simulations": len(d["simulations"]), "regime": regime,
                      "tasks": sorted({str(s["task_id"]) for s in d["simulations"]}, key=int)})
        for t in d.get("tasks", []):
            tasks_def.setdefault(str(t["id"]), t)
        for s in d["simulations"]:
            uuid_seen[s["id"]] += 1
            if s["id"] in sims:
                continue
            ri = s.get("reward_info") or {}
            sims[s["id"]] = {"id": s["id"], "file": rel, "task": str(s["task_id"]), "regime": regime,
                             "reward": ri.get("reward"), "termination": s.get("termination_reason"),
                             "breakdown": ri.get("reward_breakdown"), "canon": canon(s), "_sim": s}
    # ---- per task
    per_task, tool_inv, labels_all = {}, {}, {}
    for tid in sorted({x["task"] for x in sims.values()}, key=int):
        S = [x for x in sims.values() if x["task"] == tid]
        task = tasks_def.get(tid) or {}
        ev = task.get("evaluation_criteria") or {}
        gold = ev.get("actions") or []
        valid = [x for x in S if x["reward"] is not None]
        succ = [x for x in valid if x["reward"] >= 0.5]
        fail = [x for x in valid if x["reward"] < 0.5]
        groups = defaultdict(list)
        for x in valid:
            groups[x["canon"]].append(x)
        dup_groups = [g for g in groups.values() if len(g) > 1]
        distinct_succ = len({x["canon"] for x in succ})
        fail_reason = Counter("+".join(k for k, v in (x["breakdown"] or {}).items() if v < 1) or "?" for x in fail)
        inv = Counter()
        lab = Counter()
        same_tool_neg, succ_with_incorrect, fail_without_incorrect, unbuildable = [], 0, 0, 0
        succ_valid_tools = Counter()
        per_run_labels = {}
        for x in valid:
            try:
                g = build_step_graph(x["_sim"], None, task)
            except ValueError:
                unbuildable += 1
                continue
            L = classify_steps(g, task) if task else {}
            per_run_labels[x["id"]] = (g, L)
            for n in g["nodes"]:
                if n.get("kind") == "tool_call":
                    name = n["tool_call"]["name"]
                    inv[(name, "success_run" if x["reward"] >= 0.5 else "failed_run",
                         "error" if n["observation"]["error"] else "ok")] += 1
                    if x["reward"] >= 0.5 and not n["observation"]["error"]:
                        succ_valid_tools[name] += 1
            c = Counter(v["label"] for v in L.values())
            for k, v in c.items():
                lab[(k, "success_run" if x["reward"] >= 0.5 else "failed_run")] += v
            if x["reward"] >= 0.5 and c["incorrect"]:
                succ_with_incorrect += 1
            if x["reward"] < 0.5 and not (c["incorrect"] or c["attempted_incorrect"]):
                fail_without_incorrect += 1
        succ_tools_any = {name for name in succ_valid_tools}
        for rid, (g, L) in per_run_labels.items():
            if sims[rid]["reward"] >= 0.5:
                continue
            for n in g["nodes"]:
                if L.get(n["id"], {}).get("label") in ("incorrect", "attempted_incorrect"):
                    name = n["tool_call"]["name"]
                    same_tool_neg.append({"run": rid[:8], "step": n["id"], "tool": name, "label": L[n["id"]]["label"],
                                          "tool_in_successful_runs": name in succ_tools_any,
                                          "reason": L[n["id"]]["reason"]})
        per_task[tid] = {
            "regimes": sorted({x["regime"] for x in S}), "files": sorted({x["file"] for x in S}),
            "unique_sims": len(S), "infrastructure_or_no_reward": len(S) - len(valid),
            "terminations": dict(Counter(x["termination"] for x in S)),
            "success": len(succ), "failed": len(fail), "success_rate": round(len(succ) / len(valid), 3) if valid else None,
            "distinct_successful": distinct_succ, "exact_duplicate_groups": len(dup_groups),
            "exact_duplicate_extra_copies": sum(len(g) - 1 for g in dup_groups),
            "failed_reward_components": dict(fail_reason), "reward_basis": ev.get("reward_basis"),
            "gold_actions": [a["name"] for a in gold], "gold_writes": [a["name"] for a in gold if a["name"] in WRITE_TOOLS],
            "nl_assertions": len(ev.get("nl_assertions") or []), "unbuildable_step_graphs": unbuildable,
            "rule_labels": {f"{k}|{r}": v for (k, r), v in sorted(lab.items())},
            "negatives": same_tool_neg,
            "n_negatives": len(same_tool_neg),
            "n_same_tool_negatives": sum(n["tool_in_successful_runs"] for n in same_tool_neg),
            "successful_runs_with_rule_incorrect_step": succ_with_incorrect,
            "failed_runs_without_rule_incorrect_step": fail_without_incorrect,
            "dev_use": DEV_TASKS.get(tid), "earlier_exposure": EARLIER_EXPOSURE.get(tid),
        }
        tool_inv[tid] = {"|".join(k): v for k, v in sorted(inv.items())}
    summary = {
        "files": files,
        "n_files": len(files),
        "n_simulation_records": sum(f["simulations"] for f in files),
        "n_unique_uuids": len(sims),
        "uuids_in_more_than_one_file": sum(1 for v in uuid_seen.values() if v > 1),
        "n_tasks": len(per_task),
        "regimes": dict(Counter(x["regime"] for x in sims.values())),
        "rewards": dict(Counter(str(x["reward"]) for x in sims.values())),
        "per_task": per_task,
        "tool_inventory": tool_inv,
    }
    (OUT / "dataset_audit.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}/dataset_audit.json")


if __name__ == "__main__":
    main()
