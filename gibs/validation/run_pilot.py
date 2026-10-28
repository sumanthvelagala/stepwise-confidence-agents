"""
Consensus-mask pilot (plan: gibs/validation/pilot_plan.md). Three tasks, leave-one-out masks, variants A / C0 / C3.

    .venv/bin/python gibs/validation/run_pilot.py compute     # MCS for every (query, reference) pair; resumable
    .venv/bin/python gibs/validation/run_pilot.py analyze     # masks, tables, reference-count curves (no model)

C3 = C0 + symmetric truncation + multi-component MCS: OUR adaptation, not the paper's algorithm.
"""
from __future__ import annotations

import csv
import glob
import json
import random
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.graph.step_graph import build_step_graph  # noqa: E402
from gibs.mcs.consensus import pair_indicators  # noqa: E402
from gibs.mcs.mcs import MCSConfig, find_mcs  # noqa: E402
from gibs.mcs.multi_component import find_mcs_multi  # noqa: E402
from gibs.mcs.nli import Similarity  # noqa: E402
from gibs.mcs.structured_fields import StructuredFieldValidator  # noqa: E402
from gibs.validation.step_verification import classify_steps  # noqa: E402

OUT = REPO / "gibs/validation/results_pilot"
TASKS = ["48", "9", "25"]
GPU_DIRS = {"task_2", "task_4", "task_5"}          # agent T=1.0 regime; excluded (one regime per task)
VARIANTS = {
    "C0": {"topology": "event_context", "mcs": MCSConfig(), "fields": True, "matcher": find_mcs, "overlength": "truncate",
           "status": "our adaptation (configuration C)"},
    "A": {"topology": "paper_literal", "mcs": MCSConfig(require_same_kind=False), "fields": False, "matcher": find_mcs,
          "overlength": "truncate", "status": "paper-style baseline"},
    "C3": {"topology": "event_context", "mcs": MCSConfig(), "fields": True, "matcher": find_mcs_multi,
           "overlength": "symmetric", "status": "OUR adaptation: symmetric truncation + multi-component MCS"},
}
K_VALUES = [1, 2, 3, 5, 8]
N_SUBSETS = 50
THRESH = 0.5


def load_runs(task_id: str) -> list[dict]:
    runs, seen, skipped = [], set(), []
    for f in sorted(glob.glob(str(REPO / "results/**/results.json"), recursive=True)):
        if Path(f).parent.name in GPU_DIRS:
            continue
        data = json.load(open(f))
        task = next((t for t in data.get("tasks", []) if str(t["id"]) == task_id), None)
        for s in data["simulations"]:
            if str(s["task_id"]) != task_id or (s.get("reward_info") or {}).get("reward") is None or s["id"] in seen:
                continue
            seen.add(s["id"])
            try:
                g = build_step_graph(s, data["info"], task, source_file=str(Path(f).relative_to(REPO)))
            except ValueError as e:
                skipped.append({"sim": s["id"], "reason": str(e)})
                continue
            runs.append({"id": s["id"], "short": s["id"][:8], "success": s["reward_info"]["reward"] >= 0.5,
                         "reward": s["reward_info"]["reward"], "file": str(Path(f).relative_to(REPO)),
                         "steps": g, "task": task})
    runs.sort(key=lambda r: (not r["success"], r["id"]))
    return runs, skipped


# --------------------------------------------------------------------------------------------- compute
def compute():
    from gibs.mcs.nli import DebertaEntailment
    OUT.mkdir(parents=True, exist_ok=True)
    author = DebertaEntailment(encoding="code_sep_string", overlength="truncate")
    models = {"truncate": author, "symmetric": author.with_overlength("symmetric")}
    (OUT / "model.json").write_text(json.dumps(author.describe(), indent=2) + "\n")
    for task_id in TASKS:
        runs, skipped = load_runs(task_id)
        succ = [r for r in runs if r["success"]]
        for vname, v in VARIANTS.items():
            path = OUT / f"task{task_id}_{vname}.json"
            if path.exists():
                print(f"T{task_id} {vname}: exists, skipping", flush=True)
                continue
            model = models[v["overlength"]]
            sim = Similarity(model, direction="max_bidirectional")
            proj = {r["id"]: project(r["steps"], v["topology"]) for r in runs}
            t0, f0, n0 = time.time(), sum(m.n_forward for m in models.values()), model.n_requested
            queries = []
            for qi, q in enumerate(runs):
                refs = [r for r in succ if r["id"] != q["id"]]          # never its own reference
                per_ref = []
                for r in refs:
                    validator = StructuredFieldValidator(q["steps"], r["steps"]) if v["fields"] else None
                    res = v["matcher"](proj[q["id"]], proj[r["id"]], sim, v["mcs"], field_check=validator)
                    ind = pair_indicators(proj[q["id"]], res)
                    per_ref.append({"reference": r["id"],
                                    "node": {e: x["node_level"] for e, x in ind.items()},
                                    "ctx": {e: x["context_step_level"] for e, x in ind.items()},
                                    "node_map": res.node_map, "edge_map": res.edge_map,
                                    "n_components": len(res.components) or (1 if res.edge_map else 0),
                                    "n_rejected": len(res.rejected)})
                queries.append({"query": q["id"], "success": q["success"], "per_reference": per_ref})
                print(f"T{task_id} {vname}: query {qi + 1}/{len(runs)} ({q['short']}, refs={len(refs)}) "
                      f"elapsed={time.time() - t0:.0f}s forward={sum(m.n_forward for m in models.values()) - f0}",
                      flush=True)
            cost = {"seconds": round(time.time() - t0, 1),
                    "nli_forward_passes_uncached": sum(m.n_forward for m in models.values()) - f0,
                    "nli_directional_pairs_requested": model.n_requested - n0,
                    "n_mcs_runs": sum(len(q["per_reference"]) for q in queries)}
            path.write_text(json.dumps({"task": task_id, "variant": vname, "status": v["status"],
                                        "skipped_runs": skipped, "cost": cost, "queries": queries}) + "\n")
            print(f"T{task_id} {vname}: done {cost}", flush=True)


# --------------------------------------------------------------------------------------------- analyze
def _mask(per_ref, event, key, subset=None):
    rows = per_ref if subset is None else [per_ref[i] for i in subset]
    return sum(r[key][event] for r in rows) / len(rows)


def analyze():
    rng = random.Random(0)
    report = {"tasks": {}}
    csv_rows = []
    for task_id in TASKS:
        runs, skipped = load_runs(task_id)
        by_id = {r["id"]: r for r in runs}
        data = {v: json.loads((OUT / f"task{task_id}_{v}.json").read_text()) for v in VARIANTS}
        labels = {r["id"]: classify_steps(r["steps"], r["task"]) for r in runs}
        tinfo = {"n_success": sum(r["success"] for r in runs), "n_failed": sum(not r["success"] for r in runs),
                 "skipped": skipped, "cost": {v: data[v]["cost"] for v in VARIANTS}, "runs": [], "unexpected": [],
                 "by_label": {}, "curve": {}, "c0_vs_c3": {}}
        for q in data["C0"]["queries"]:
            run = by_id[q["query"]]
            node_by_id = {n["id"]: n for n in run["steps"]["nodes"]}
            qv = {v: next(x for x in data[v]["queries"] if x["query"] == q["query"]) for v in VARIANTS}
            steps = []
            for event in q["per_reference"][0]["node"] if q["per_reference"] else []:
                n = node_by_id[event]
                row = {"task": task_id, "run": run["short"], "success": run["success"], "step": event,
                       "kind": n.get("kind"), "text": (n["op_text"] or "")[:100],
                       "label": labels[run["id"]][event]["label"], "label_reason": labels[run["id"]][event]["reason"]}
                for v in VARIANTS:
                    pr = qv[v]["per_reference"]
                    row[f"m_node_{v}"] = round(_mask(pr, event, "node"), 3)
                    row[f"m_ctx_{v}"] = round(_mask(pr, event, "ctx"), 3)
                steps.append(row)
                csv_rows.append(row)
                for v in VARIANTS:
                    for key in ("node", "ctx"):
                        m = row[f"m_{key}_{v}"]
                        if (row["label"] == "valid" and m < THRESH) or (row["label"] == "incorrect" and m >= THRESH):
                            tinfo["unexpected"].append({"variant": v, "target": key, "run": run["short"],
                                                        "success": run["success"], "step": event, "label": row["label"],
                                                        "value": m, "text": row["text"]})
            tinfo["runs"].append({"run": run["short"], "success": run["success"], "n_refs": len(q["per_reference"]),
                                  "steps": steps})
        # label-level summaries
        for v in VARIANTS:
            for key in ("node", "ctx"):
                for lab in ("valid", "incorrect", "attempted_incorrect", "unverified"):
                    for succ in (True, False):
                        vals = [s[f"m_{key}_{v}"] for r in tinfo["runs"] for s in r["steps"]
                                if s["label"] == lab and r["success"] == succ]
                        if vals:
                            tinfo["by_label"][f"{v}|{key}|{lab}|{'success' if succ else 'failed'}"] = {
                                "n": len(vals), "mean": round(statistics.mean(vals), 3),
                                "min": min(vals), "max": max(vals)}
        # C0 vs C3
        for key in ("node", "ctx"):
            diffs = [s[f"m_{key}_C3"] - s[f"m_{key}_C0"] for r in tinfo["runs"] for s in r["steps"]]
            tinfo["c0_vs_c3"][key] = {"steps": len(diffs), "changed": sum(abs(d) > 1e-9 for d in diffs),
                                      "increased": sum(d > 1e-9 for d in diffs), "decreased": sum(d < -1e-9 for d in diffs),
                                      "mean_change": round(statistics.mean(diffs), 4) if diffs else 0}
        # reference-count curves
        for v in VARIANTS:
            for key in ("node", "ctx"):
                curve = {}
                for k in K_VALUES + ["all"]:
                    dev, val_m, inc_m, unexpected = [], [], [], 0
                    for q in data[v]["queries"]:
                        pr = q["per_reference"]
                        if not pr:
                            continue
                        lab = labels[q["query"]]
                        kk = len(pr) if k == "all" else k
                        if kk > len(pr):
                            continue
                        subsets = [list(range(len(pr)))] if k == "all" else \
                            [rng.sample(range(len(pr)), kk) for _ in range(N_SUBSETS)]
                        for event in pr[0][key]:
                            full = _mask(pr, event, key)
                            for sub in subsets:
                                m = _mask(pr, event, key, sub)
                                dev.append(abs(m - full))
                                if lab[event]["label"] == "valid":
                                    val_m.append(m)
                                    unexpected += m < THRESH
                                elif lab[event]["label"] == "incorrect":
                                    inc_m.append(m)
                                    unexpected += m >= THRESH
                    if dev:
                        curve[str(k)] = {"mean_abs_dev_from_full": round(statistics.mean(dev), 4),
                                         "mean_valid": round(statistics.mean(val_m), 3) if val_m else None,
                                         "mean_incorrect": round(statistics.mean(inc_m), 3) if inc_m else None,
                                         "unexpected_rate": round(unexpected / max(1, len(val_m) + len(inc_m)), 3)}
                tinfo["curve"][f"{v}|{key}"] = curve
        report["tasks"][task_id] = tinfo
    (OUT / "pilot_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with open(OUT / "per_step_masks.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)
    (OUT / "tables.md").write_text(tables(report))
    print(f"wrote {OUT}/pilot_summary.json, per_step_masks.csv, tables.md")


def tables(report) -> str:
    L = ["# Consensus-mask pilot: generated tables (run_pilot.py analyze)", "",
         "C3 = our adaptation (symmetric truncation + multi-component MCS). A = paper-style baseline. "
         "Values are consensus fractions, not correctness.", ""]
    for t, info in report["tasks"].items():
        L += [f"## Task {t} ({info['n_success']} successful, {info['n_failed']} failed)", "",
              "### Mean consensus by independent step label", "",
              "| Variant | Target | Label | Runs | n | mean | min | max |", "|---|---|---|---|---|---|---|---|"]
        for key, s in sorted(info["by_label"].items()):
            v, tgt, lab, succ = key.split("|")
            L.append(f"| {v} | {tgt} | {lab} | {succ} | {s['n']} | {s['mean']} | {s['min']} | {s['max']} |")
        L += ["", "### Unexpected cases (valid < 0.5, incorrect ≥ 0.5)", "",
              "| Variant | Target | Run | Successful run | Step | Label | Value | Step text |", "|---|---|---|---|---|---|---|---|"]
        for u in info["unexpected"]:
            L.append(f"| {u['variant']} | {u['target']} | {u['run']} | {u['success']} | {u['step']} | {u['label']} | "
                     f"{u['value']} | {u['text'].replace('|', '/')} |")
        L += ["", "### Consensus vs number of references (50 random subsets per k)", "",
              "| Variant | Target | k | mean abs dev from full pool | mean (valid) | mean (incorrect) | unexpected rate |",
              "|---|---|---|---|---|---|---|"]
        for key, curve in info["curve"].items():
            v, tgt = key.split("|")
            for k, c in curve.items():
                L.append(f"| {v} | {tgt} | {k} | {c['mean_abs_dev_from_full']} | {c['mean_valid']} | "
                         f"{c['mean_incorrect']} | {c['unexpected_rate']} |")
        L += ["", "### Per-step masks (m_node / m_ctx)", "",
              "| Run | Successful run | Step | Label | Step text | A | C0 | C3 |", "|---|---|---|---|---|---|---|---|"]
        for r in info["runs"]:
            for s in r["steps"]:
                L.append(f"| {r['run']} | {r['success']} | {s['step']} | {s['label']} | {s['text'].replace('|', '/')[:70]} | "
                         f"{s['m_node_A']:.2f}/{s['m_ctx_A']:.2f} | {s['m_node_C0']:.2f}/{s['m_ctx_C0']:.2f} | "
                         f"{s['m_node_C3']:.2f}/{s['m_ctx_C3']:.2f} |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    {"compute": compute, "analyze": analyze}[sys.argv[1]]()
