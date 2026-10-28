"""
C5 experiment (plan: gibs/validation/c5_plan.md): two-stage constrained matching. Stage 1 = the stored C4 tool
part (results_c4/, read-only); stage 2 = agent messages via their context edge (gibs/mcs/two_stage.py).
OUR adaptation, not the paper's algorithm.

    .venv/bin/python -B gibs/validation/run_c5.py compute   # resumable; skips existing task files
    .venv/bin/python -B gibs/validation/run_c5.py analyze   # A/C0/C3/C4 (read-only) vs C5

Writes only to gibs/validation/results_c5/.
"""
from __future__ import annotations

import csv
import json
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.mcs.consensus import pair_indicators  # noqa: E402
from gibs.mcs.nli import Similarity  # noqa: E402
from gibs.mcs.structured_fields import StructuredFieldValidator  # noqa: E402
from gibs.mcs.two_stage import extend_messages, freeze_tool_part, project_c5  # noqa: E402
from gibs.validation.run_c4 import C4, OUT as C4_OUT, dist, load_variant as load_v4  # noqa: E402
from gibs.validation.run_pilot import TASKS, THRESH, load_runs  # noqa: E402
from gibs.validation.step_verification import classify_steps  # noqa: E402

OUT = REPO / "gibs/validation/results_c5"
ALL = ["A", "C0", "C3", "C4", "C5"]
TRANSFER_MESSAGE = "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."

# known false-pair panel (c5_plan.md §5.2): (task, query, step, reference, reference step, source)
PANEL = [("25", "bb73aded", "s12", "1e01a088", "s10", "C4 F-b #8"),
         ("25", "1e01a088", "s10", "bb73aded", "s12", "C4 F-b #25"),
         ("25", "bb73aded", "s10", "1e01a088", "s14", "C4 F-b #18"),
         ("25", "2aca18ff", "s26", "bb73aded", "s20", "C4 F-b #30"),
         ("25", "16aac895", "s10", "1e01a088", "s10", "C3 F-b (post-hoc #6)"),
         ("25", "16aac895", "s10", "cd5be315", "s8", "C3 F-b (post-hoc #19)"),
         ("25", "51d355a9", "s10", "bb73aded", "s10", "C3 F-b (post-hoc #24)")]


def load_variant(t, v):
    return json.loads((OUT / f"task{t}_C5.json").read_text()) if v == "C5" else load_v4(t, v)


# --------------------------------------------------------------------------------------------- compute
def compute():
    from gibs.mcs.nli import DebertaEntailment
    OUT.mkdir(parents=True, exist_ok=True)
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate").with_overlength(C4["overlength"])
    sim = Similarity(model, direction="max_bidirectional")
    (OUT / "model.json").write_text(json.dumps(model.describe(), indent=2) + "\n")
    for t in TASKS:
        path = OUT / f"task{t}_C5.json"
        if path.exists():
            print(f"T{t} C5: exists, skipping", flush=True)
            continue
        runs, skipped = load_runs(t)
        by_id = {r["id"]: r for r in runs}
        c4 = json.loads((C4_OUT / f"task{t}_C4.json").read_text())
        p4 = {r["id"]: project(r["steps"], C4["topology"]) for r in runs}
        p5 = {r["id"]: project_c5(r["steps"]) for r in runs}
        t0, f0, n0 = time.time(), model.n_forward, model.n_requested
        queries = []
        for qi, q in enumerate(c4["queries"]):
            qid = q["query"]
            per_ref = []
            for pr in q["per_reference"]:
                rid = pr["reference"]
                fv, fe = freeze_tool_part(p4[qid], pr["node_map"], pr["edge_map"])
                res = extend_messages(p5[qid], p5[rid], sim, fv, fe, C4["mcs"],
                                      field_check=StructuredFieldValidator(by_id[qid]["steps"], by_id[rid]["steps"]))
                ind = pair_indicators(p5[qid], res)
                per_ref.append({"reference": rid,
                                "node": {e: x["node_level"] for e, x in ind.items()},
                                "ctx": {e: x["context_step_level"] for e, x in ind.items()},
                                "node_map": res.node_map, "edge_map": res.edge_map,
                                "n_components": len(res.components), "n_rejected": len(res.rejected),
                                "stage2": res.stage2_stats})
            queries.append({"query": qid, "success": q["success"], "per_reference": per_ref})
            print(f"T{t} C5: query {qi + 1}/{len(c4['queries'])} ({qid[:8]}) elapsed={time.time() - t0:.0f}s "
                  f"forward={model.n_forward - f0}", flush=True)
        cost = {"seconds": round(time.time() - t0, 1), "nli_forward_passes_uncached": model.n_forward - f0,
                "nli_directional_pairs_requested": model.n_requested - n0,
                "n_mcs_runs": sum(len(q["per_reference"]) for q in queries)}
        path.write_text(json.dumps({"task": t, "variant": "C5", "skipped_runs": skipped, "cost": cost,
                                    "status": "OUR adaptation: two-stage (frozen C4 tool part + message context)",
                                    "queries": queries}) + "\n")
        print(f"T{t} C5: done {cost}", flush=True)


# --------------------------------------------------------------------------------------------- analyze
def r3(x):
    return None if x is None else round(x, 3)


def message_pairs(t, data, runs_nodes, labels, require_ctx=None):
    """(query message, reference) pairs: unverified query message, node mapped, texts not identical."""
    out = []
    for q in data["queries"]:
        for p in q["per_reference"]:
            for a, b in p["node_map"].items():
                if not a.startswith("N:s"):
                    continue
                qa = runs_nodes[q["query"]][a[2:]]
                if qa["kind"] != "message" or labels[q["query"]][a[2:]]["label"] != "unverified":
                    continue
                rb = runs_nodes[p["reference"]].get(b[2:])
                if rb is None or (qa["content"] or "").strip() == (rb.get("content") or "").strip():
                    continue
                ctx = p["ctx"][a[2:]]
                if require_ctx is not None and ctx != require_ctx:
                    continue
                out.append({"task": t, "query": q["query"][:8], "step": a[2:], "reference": p["reference"][:8],
                            "ref_step": b[2:], "ctx": ctx, "query_text": qa["content"], "ref_text": rb.get("content")})
    return out


def analyze():
    summary = {"plan": "gibs/validation/c5_plan.md", "tasks": {}, "checks": {}, "panel": [], "samples": {}}
    rows_all, pairs = [], {v: [] for v in ("C3", "C4", "C5")}
    checks = Counter()
    check_examples = defaultdict(list)
    for t in TASKS:
        runs, _ = load_runs(t)
        by_id = {r["id"]: r for r in runs}
        nodes = {r["id"]: {n["id"]: n for n in r["steps"]["nodes"]} for r in runs}
        order = {r["id"]: [n["id"] for n in r["steps"]["nodes"]] for r in runs}
        labels = {r["id"]: classify_steps(r["steps"], r["task"]) for r in runs}
        data = {v: load_variant(t, v) for v in ALL}
        for v in ALL:
            assert [(q["query"], [p["reference"] for p in q["per_reference"]]) for q in data[v]["queries"]] == \
                   [(q["query"], [p["reference"] for p in q["per_reference"]]) for q in data["C4"]["queries"]], v
        qv = {v: {q["query"]: q for q in data[v]["queries"]} for v in ALL}
        p4 = {r["id"]: project(r["steps"], "paper_literal") for r in runs}
        p5 = {r["id"]: project_c5(r["steps"]) for r in runs}
        # ---- per-step table
        rows = []
        for q in data["C4"]["queries"]:
            qid = q["query"]
            if not q["per_reference"]:
                continue
            for ev in q["per_reference"][0]["node"]:
                n = nodes[qid][ev]
                k = order[qid].index(ev)
                pred = nodes[qid][order[qid][k - 1]] if k else None
                row = {"task": t, "run": qid[:8], "success": by_id[qid]["success"], "step": ev, "kind": n["kind"],
                       "what": n["tool_call"]["name"] if n["kind"] == "tool_call" else "message",
                       "predecessor": "none" if pred is None else ("user_turn" if pred["type"] == "UserTurn" else
                                                                    ("tool_call" if pred["kind"] == "tool_call" else "message")),
                       "text": (n["op_text"] or "")[:100], "label": labels[qid][ev]["label"]}
                for v in ALL:
                    prs = qv[v][qid]["per_reference"]
                    row[f"m_node_{v}"] = r3(sum(p["node"][ev] for p in prs) / len(prs))
                    row[f"m_ctx_{v}"] = r3(sum(p["ctx"][ev] for p in prs) / len(prs))
                rows.append(row)
        rows_all += rows
        # ---- F1 tool invariance (scores and stored maps)
        for r in rows:
            if r["kind"] == "tool_call":
                checks["F1_tool_steps_checked"] += 1
                if (r["m_node_C4"], r["m_ctx_C4"]) != (r["m_node_C5"], r["m_ctx_C5"]):
                    checks["F1_tool_score_differs"] += 1
                    check_examples["F1"].append(r)
        stage2 = Counter()
        for qid, q5 in qv["C5"].items():
            g1 = p5[qid]
            tools = {n for n, d in g1.nodes.items() if d["kind"] == "tool_result"}
            tool_edges = {e["id"] for e in g1.edges if e["dst"] in tools}
            for p4r, p5r in zip(qv["C4"][qid]["per_reference"], q5["per_reference"]):
                checks["pairs"] += 1
                stage2.update(p5r["stage2"])
                if {n: m for n, m in p4r["node_map"].items() if n in tools} != \
                   {n: m for n, m in p5r["node_map"].items() if n in tools} or \
                   {e: m for e, m in p4r["edge_map"].items() if e in tool_edges} != \
                   {e: m for e, m in p5r["edge_map"].items() if e in tool_edges}:
                    checks["F1_tool_map_differs"] += 1
                # F2 injective, kind-preserving message maps
                vals = list(p5r["node_map"].values())
                if len(vals) != len(set(vals)) or len(p5r["edge_map"].values()) != len(set(p5r["edge_map"].values())):
                    checks["F2_not_injective"] += 1
                g2 = p5[p5r["reference"]]
                for a, b in p5r["node_map"].items():
                    if g1.nodes[a]["kind"] == "agent_message" and g2.nodes[b]["kind"] != "agent_message":
                        checks["F2_message_to_non_message"] += 1
                # F3 context consistency
                for ev, ok in p5r["ctx"].items():
                    nid = "N:" + ev
                    if g1.nodes[nid]["kind"] != "agent_message" or not ok:
                        continue
                    (e1,) = g1.in_edges(nid)
                    if g1.nodes[e1["src"]]["kind"] == "tool_result":
                        e2 = next(e for e in g2.edges if e["id"] == p5r["edge_map"][e1["id"]])
                        checks["F3_ctx_messages_after_tool"] += 1
                        if p4r["node_map"].get(e1["src"]) != e2["src"]:
                            checks["F3_violation"] += 1
                            check_examples["F3"].append((qid[:8], ev, p5r["reference"][:8]))
        # ---- F4
        if t == "25":
            q = next(x for x in data["C5"]["queries"] if x["query"].startswith("6f12b024"))
            checks["F4_6f12b024_s32_ctx_refs"] = sum(p["ctx"]["s32"] for p in q["per_reference"])
            checks["F4_6f12b024_s32_node_refs"] = sum(p["node"]["s32"] for p in q["per_reference"])
        # ---- distributions
        tinfo = {"cost_C5": data["C5"]["cost"], "stage2": dict(stage2), "distributions": {}, "unexpected": [],
                 "message_coverage": {}, "c5_minus_c4_messages": {}}
        for v in ALL:
            for key in ("node", "ctx"):
                groups = defaultdict(list)
                for r in rows:
                    g = "success" if r["success"] else "failed"
                    groups[f"{r['label']}|{g}"].append(r[f"m_{key}_{v}"])
                    groups[f"{r['label']}:{r['what']}|{g}"].append(r[f"m_{key}_{v}"])
                    if r["kind"] == "message":
                        groups[f"message|pred={r['predecessor']}|{g}"].append(r[f"m_{key}_{v}"])
                for k, xs in groups.items():
                    tinfo["distributions"][f"{v}|{key}|{k}"] = dist(xs)
                for r in rows:
                    m = r[f"m_{key}_{v}"]
                    if (r["label"] == "valid" and m < THRESH) or (r["label"] == "incorrect" and m >= THRESH):
                        tinfo["unexpected"].append({"variant": v, "target": key, "run": r["run"], "step": r["step"],
                                                    "label": r["label"], "value": m, "text": r["text"]})
        for v in ("C3", "C4", "C5"):
            cnt = Counter()
            for q in data[v]["queries"]:
                for p in q["per_reference"]:
                    for ev in p["node"]:
                        if nodes[q["query"]][ev]["kind"] != "message":
                            continue
                        cnt["node"] += p["node"][ev]
                        cnt["ctx"] += p["ctx"][ev]
                        cnt["node_only"] += p["node"][ev] and not p["ctx"][ev]
                        cnt["indicators"] += 1
            tinfo["message_coverage"][v] = dict(cnt)
        d = Counter()
        for r in rows:
            if r["kind"] == "message":
                for key in ("node", "ctx"):
                    x = r[f"m_{key}_C5"] - r[f"m_{key}_C4"]
                    d[f"{key}|{'up' if x > 1e-9 else 'down' if x < -1e-9 else 'same'}|{r['label']}"] += 1
        tinfo["c5_minus_c4_messages"] = dict(d)
        summary["tasks"][t] = tinfo
        # ---- panel
        for (pt, qs, st, rs, rst, src) in PANEL:
            if pt != t:
                continue
            item = {"pair": f"{qs} {st} -> {rs} {rst}", "source": src}
            for v in ("C3", "C4", "C5"):
                q = next(x for x in data[v]["queries"] if x["query"].startswith(qs))
                p = next(x for x in q["per_reference"] if x["reference"].startswith(rs))
                item[v] = {"mapped_to_that_step": p["node_map"].get("N:" + st) == "N:" + rst,
                           "node": p["node"][st], "ctx": p["ctx"][st], "mapped_to": p["node_map"].get("N:" + st)}
            summary["panel"].append(item)
        if t == "25":
            for v in ("C3", "C4", "C5"):
                q = next(x for x in data[v]["queries"] if x["query"].startswith("6f12b024"))
                summary.setdefault("t25_6f12b024_s32", {})[v] = {
                    "node_refs": sum(p["node"]["s32"] for p in q["per_reference"]),
                    "ctx_refs": sum(p["ctx"]["s32"] for p in q["per_reference"]),
                    "n_refs": len(q["per_reference"]),
                    "mapped_to": [(p["reference"][:8], p["node_map"].get("N:s32")) for p in q["per_reference"]
                                  if "N:s32" in p["node_map"]]}
        for v in ("C3", "C4", "C5"):
            pairs[v] += message_pairs(t, data[v], nodes, labels)
    summary["checks"] = dict(checks)
    summary["check_examples"] = {k: v[:10] for k, v in check_examples.items()}
    for v in ("C3", "C4", "C5"):
        summary["samples"][v] = {"population": len(pairs[v]),
                                 "sample_seed0": random.Random(0).sample(pairs[v], min(30, len(pairs[v])))}
        if v == "C5":
            for flag in (True, False):
                sub = [x for x in pairs[v] if x["ctx"] == flag]
                summary["samples"][f"C5_ctx={flag}"] = {"population": len(sub)}
    (OUT / "c5_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    with open(OUT / "per_step_masks_c5.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_all[0].keys()))
        w.writeheader()
        w.writerows(rows_all)
    (OUT / "tables_c5.md").write_text(tables(summary, rows_all))
    print(json.dumps(summary["checks"], indent=1))
    print(f"wrote {OUT}/c5_summary.json, per_step_masks_c5.csv, tables_c5.md")


def tables(s, rows) -> str:
    L = ["# C5 vs A / C0 / C3 / C4: generated tables (run_c5.py analyze)", "",
         "C5 = two-stage constrained matching (OUR adaptation). Values are consensus fractions, not correctness.", "",
         f"Checks: {json.dumps(s['checks'])}", ""]
    for t, x in s["tasks"].items():
        L += [f"## Task {t}", "", f"C5 cost: {x['cost_C5']}; stage-2 counters: {x['stage2']}", "",
              f"Message coverage (indicator counts): {json.dumps(x['message_coverage'])}", "",
              f"C5 − C4 on message steps: {json.dumps(x['c5_minus_c4_messages'])}", "",
              "| Variant | Target | Group | Runs | n | mean | median | bins 0 / (0,.25) / [.25,.5) / [.5,.75) / [.75,1) / 1 |",
              "|---|---|---|---|---|---|---|---|"]
        for k, d in sorted(x["distributions"].items(), key=lambda kv: (kv[0].split("|", 2)[2], kv[0])):
            v, tgt, rest = k.split("|", 2)
            grp, g = rest.rsplit("|", 1)
            L.append(f"| {v} | {tgt} | {grp} | {g} | {d['n']} | {d['mean']} | {d['median']} | "
                     + " ".join(str(b) for b in d["bins"].values()) + " |")
        c = Counter((u["variant"], u["target"]) for u in x["unexpected"])
        L += ["", "Unexpected (valid < 0.5 / incorrect ≥ 0.5): " +
              ", ".join(f"{v} {tg}: {c[(v, tg)]}" for v in ALL for tg in ("node", "ctx")), "",
              "### Per-step masks (m_node / m_ctx)", "",
              "| Run | Succ | Step | Pred | Label | Text | C3 | C4 | C5 |", "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["task"] == t:
                L.append(f"| {r['run']} | {r['success']} | {r['step']} | {r['predecessor']} | {r['label']} | "
                         f"{r['text'][:55].replace('|', '/')} | "
                         + " | ".join(f"{r[f'm_node_{v}']:.2f}/{r[f'm_ctx_{v}']:.2f}" for v in ("C3", "C4", "C5")) + " |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    {"compute": compute, "analyze": analyze}[sys.argv[1]]()
