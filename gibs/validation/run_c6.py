"""
C6 experiment (plan: gibs/validation/c6_plan.md): C5 + stage-3 outcome route. OUR adaptation, not the paper's GIBS.
Outcome agreement does not establish that a tool action was correct under the user's request or policy.

    .venv/bin/python -B gibs/validation/run_c6.py compute   # resumable; reads results_c4/ only
    .venv/bin/python -B gibs/validation/run_c6.py analyze   # vs C3/C4/C5 (read-only)

Writes only to gibs/validation/results_c6/.
"""
from __future__ import annotations

import csv
import json
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
from gibs.mcs.structured_fields import CALL_FIELDS, StructuredFieldValidator, _compare  # noqa: E402
from gibs.mcs.two_stage import extend_messages, freeze_tool_part, outcome_key, project_c5  # noqa: E402
from gibs.validation.run_c4 import C4, OUT as C4_OUT, dist  # noqa: E402
from gibs.validation.run_c5 import load_variant as load_v5  # noqa: E402
from gibs.validation.run_pilot import TASKS, THRESH, load_runs  # noqa: E402
from gibs.validation.step_verification import classify_steps  # noqa: E402

OUT = REPO / "gibs/validation/results_c6"
ALL = ["A", "C0", "C3", "C4", "C5", "C6"]
H6_PAIRS = [("25", "16aac895", "s10", "1e01a088", "s10"), ("25", "16aac895", "s10", "cd5be315", "s8"),
            ("25", "51d355a9", "s10", "bb73aded", "s10"), ("25", "bb73aded", "s10", "291cfe67", "s10"),
            ("25", "d2135fe7", "s10", "1e01a088", "s10"), ("25", "1e01a088", "s10", "8c8332b6", "s10"),
            ("25", "2e0c25a6", "s10", "1e01a088", "s10")]


def load_variant(t, v):
    return json.loads((OUT / f"task{t}_C6.json").read_text()) if v == "C6" else load_v5(t, v)


# --------------------------------------------------------------------------------------------- compute
def compute():
    from gibs.mcs.nli import DebertaEntailment
    OUT.mkdir(parents=True, exist_ok=True)
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate").with_overlength(C4["overlength"])
    sim = Similarity(model, direction="max_bidirectional")
    (OUT / "model.json").write_text(json.dumps(model.describe(), indent=2) + "\n")
    for t in TASKS:
        path = OUT / f"task{t}_C6.json"
        if path.exists():
            print(f"T{t} C6: exists, skipping", flush=True)
            continue
        runs, skipped = load_runs(t)
        by_id = {r["id"]: r for r in runs}
        c4 = json.loads((C4_OUT / f"task{t}_C4.json").read_text())
        p4 = {r["id"]: project(r["steps"], C4["topology"]) for r in runs}
        p5 = {r["id"]: project_c5(r["steps"]) for r in runs}
        t0, f0, n0 = time.time(), model.n_forward, model.n_requested
        queries = []
        for q in c4["queries"]:
            qid = q["query"]
            per_ref = []
            for pr in q["per_reference"]:
                rid = pr["reference"]
                fv, fe = freeze_tool_part(p4[qid], pr["node_map"], pr["edge_map"])
                res = extend_messages(p5[qid], p5[rid], sim, fv, fe, C4["mcs"],
                                      field_check=StructuredFieldValidator(by_id[qid]["steps"], by_id[rid]["steps"]),
                                      outcome_route=True, query_steps=by_id[qid]["steps"],
                                      reference_steps=by_id[rid]["steps"])
                ind = pair_indicators(p5[qid], res)
                per_ref.append({"reference": rid,
                                "node": {e: x["node_level"] for e, x in ind.items()},
                                "ctx": {e: x["context_step_level"] for e, x in ind.items()},
                                "node_map": res.node_map, "edge_map": res.edge_map,
                                "outcome_route_edges": res.outcome_route_edges,
                                "outcome_alignments": res.outcome_alignments,
                                "n_components": len(res.components), "n_rejected": len(res.rejected),
                                "stage2": res.stage2_stats})
            queries.append({"query": qid, "success": q["success"], "per_reference": per_ref})
        cost = {"seconds": round(time.time() - t0, 1), "nli_forward_passes_uncached": model.n_forward - f0,
                "nli_directional_pairs_requested": model.n_requested - n0,
                "n_mcs_runs": sum(len(q["per_reference"]) for q in queries)}
        path.write_text(json.dumps({"task": t, "variant": "C6", "skipped_runs": skipped, "cost": cost,
                                    "status": "OUR adaptation: C5 + outcome route (not the paper's GIBS)",
                                    "queries": queries}) + "\n")
        print(f"T{t} C6: done {cost}", flush=True)


# --------------------------------------------------------------------------------------------- analyze
def r3(x):
    return None if x is None else round(x, 3)


def analyze():
    S = {"plan": "gibs/validation/c6_plan.md", "checks": Counter(), "tasks": {}, "outcome_pairs": [], "h6": [],
         "valid_transfer_messages": [], "t25_6f12b024_s32": {}}
    rows_all = []
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
        p5 = {r["id"]: project_c5(r["steps"]) for r in runs}

        def pred(rid, ev):
            k = order[rid].index(ev)
            return nodes[rid][order[rid][k - 1]] if k else None

        rows = []
        for qid in qv["C4"]:
            prs4 = qv["C4"][qid]["per_reference"]
            if not prs4:
                continue
            for ev in prs4[0]["node"]:
                n, p = nodes[qid][ev], pred(qid, ev)
                row = {"task": t, "run": qid[:8], "success": by_id[qid]["success"], "step": ev, "kind": n["kind"],
                       "what": n["tool_call"]["name"] if n["kind"] == "tool_call" else "message",
                       "predecessor": "none" if p is None else ("user_turn" if p["type"] == "UserTurn" else
                                                                (f"tool:{p['tool_call']['name']}" if p["kind"] == "tool_call" else "message")),
                       "text": (n["op_text"] or "")[:100], "label": labels[qid][ev]["label"]}
                for v in ALL:
                    prs = qv[v][qid]["per_reference"]
                    row[f"m_node_{v}"] = r3(sum(x["node"][ev] for x in prs) / len(prs))
                    row[f"m_ctx_{v}"] = r3(sum(x["ctx"][ev] for x in prs) / len(prs))
                if n["kind"] == "message":
                    prs6 = qv["C6"][qid]["per_reference"]
                    via = sum(("N:" + ev) in {e.split("->")[1] for e in x["outcome_route_edges"]} for x in prs6)
                    row["m_ctx_C6_outcome_route"] = r3(via / len(prs6))
                    row["m_ctx_C6_action_route"] = r3(row["m_ctx_C6"] - via / len(prs6))
                else:
                    row["m_ctx_C6_outcome_route"] = row["m_ctx_C6_action_route"] = None
                rows.append(row)
        rows_all += rows
        ck = S["checks"]
        # ---- F1 tool invariance
        for r in rows:
            if r["kind"] == "tool_call":
                ck["F1_tool_steps"] += 1
                ck["F1_tool_score_differs"] += (r["m_node_C4"], r["m_ctx_C4"]) != (r["m_node_C6"], r["m_ctx_C6"])
        tstats = Counter()
        adm_by_tool = Counter()
        for qid, q6 in qv["C6"].items():
            g1 = p5[qid]
            tools = {n for n, d in g1.nodes.items() if d["kind"] == "tool_result"}
            tool_edges = {e["id"] for e in g1.edges if e["dst"] in tools}
            for p4, p5r, p6 in zip(qv["C4"][qid]["per_reference"], qv["C5"][qid]["per_reference"], q6["per_reference"]):
                ck["pairs"] += 1
                tstats.update(p6["stage2"])
                fv, _ = freeze_tool_part(project(by_id[qid]["steps"], "paper_literal"), p4["node_map"], p4["edge_map"])
                if {n: m for n, m in p4["node_map"].items() if n in tools} != \
                   {n: m for n, m in p6["node_map"].items() if n in tools} or \
                   {e: m for e, m in p4["edge_map"].items() if e in tool_edges} != \
                   {e: m for e, m in p6["edge_map"].items() if e in tool_edges}:
                    ck["F1_tool_map_differs"] += 1
                ck["F1_non_frozen_tool_node_in_map"] += sum(n in tools and n not in fv for n in p6["node_map"])
                # ---- F2 C5 retention
                ck["F2_c5_node_mapping_changed"] += sum(p6["node_map"].get(k) != v for k, v in p5r["node_map"].items())
                ck["F2_c5_edge_mapping_changed"] += sum(p6["edge_map"].get(k) != v for k, v in p5r["edge_map"].items())
                ck["F2_c5_indicator_lost"] += sum((p5r[key][ev] and not p6[key][ev]) for key in ("node", "ctx")
                                                  for ev in p5r["node"])
                # ---- F4 injectivity
                vals = list(p6["node_map"].values()) + list(p6["outcome_alignments"].values())
                ck["F4_not_injective"] += len(vals) != len(set(vals)) or \
                    len(set(p6["edge_map"].values())) != len(p6["edge_map"])
                # ---- F3 re-check every outcome-route edge
                g2 = p5[p5r["reference"]]
                for e1 in p6["outcome_route_edges"]:
                    ck["outcome_route_edges"] += 1
                    e2 = p6["edge_map"][e1]
                    s1, d1 = e1.split("->")
                    s2 = next(e for e in g2.edges if e["id"] == e2)["src"]
                    a, b = nodes[qid][s1[2:]], nodes[p6["reference"]][s2[2:]]
                    bad = (a["tool_call"]["name"] != b["tool_call"]["name"] or
                           _compare("a", a["tool_call"]["arguments"] or {}, b["tool_call"]["arguments"] or {},
                                    CALL_FIELDS.get(a["tool_call"]["name"], [])) or outcome_key(a) != outcome_key(b) or
                           p6["outcome_alignments"].get(s1) != s2)
                    ck["F3_violation"] += bool(bad)
                    adm_by_tool[a["tool_call"]["name"] + (" (error)" if a["observation"]["error"] else "")] += 1
                    qm, rm = nodes[qid][d1[2:]], nodes[p6["reference"]][e2.split("->")[1][2:]]
                    S["outcome_pairs"].append({
                        "task": t, "query": qid[:8], "q_msg": d1[2:], "q_tool": s1[2:], "reference": p6["reference"][:8],
                        "r_msg": qm and e2.split("->")[1][2:], "r_tool": s2[2:], "tool": a["tool_call"]["name"],
                        "tool_error": a["observation"]["error"], "outcome": outcome_key(a)[1][:120],
                        "q_label": labels[qid][d1[2:]]["label"], "q_success": by_id[qid]["success"],
                        "identical_text": (qm["content"] or "").strip() == (rm["content"] or "").strip(),
                        "q_text": qm["content"], "r_text": rm["content"],
                        "q_call_args": a["tool_call"]["arguments"], "r_call_args": b["tool_call"]["arguments"]})
        # ---- F5
        if t == "25":
            for v in ("C3", "C4", "C5", "C6"):
                q = next(x for x in data[v]["queries"] if x["query"].startswith("6f12b024"))
                S["t25_6f12b024_s32"][v] = {"node_refs": sum(p["node"]["s32"] for p in q["per_reference"]),
                                            "ctx_refs": sum(p["ctx"]["s32"] for p in q["per_reference"]),
                                            "n_refs": len(q["per_reference"])}
            ck["F5_6f12b024_s32_supported_refs"] = S["t25_6f12b024_s32"]["C6"]["node_refs"] + \
                S["t25_6f12b024_s32"]["C6"]["ctx_refs"]
        # ---- H6
        for (pt, qs, st, rs, rst) in H6_PAIRS:
            if pt != t:
                continue
            item = {"pair": f"{qs} {st} -> {rs} {rst}"}
            for v in ("C3", "C4", "C5", "C6"):
                q = next(x for x in data[v]["queries"] if x["query"].startswith(qs))
                p = next(x for x in q["per_reference"] if x["reference"].startswith(rs))
                item[v] = {"mapped_to_that_step": p["node_map"].get("N:" + st) == "N:" + rst, "ctx": p["ctx"][st],
                           "via_outcome_route": any(e.endswith("->N:" + st) for e in p.get("outcome_route_edges", []))}
            S["h6"].append(item)
        # ---- valid transfer messages
        for r in rows:
            if r["label"] == "valid" and r["kind"] == "message":
                S["valid_transfer_messages"].append({k: r[k] for k in ("task", "run", "step", "success", "m_ctx_C3",
                                                                       "m_ctx_C4", "m_ctx_C5", "m_ctx_C6",
                                                                       "m_ctx_C6_action_route", "m_ctx_C6_outcome_route")})
        # ---- coverage and distributions
        cov = {}
        for v in ("C3", "C4", "C5", "C6"):
            c = Counter()
            for q in data[v]["queries"]:
                for p in q["per_reference"]:
                    oroute = {e.split("->")[1][2:] for e in p.get("outcome_route_edges", [])}
                    for ev in p["node"]:
                        if nodes[q["query"]][ev]["kind"] != "message":
                            continue
                        c["indicators"] += 1
                        c["node"] += p["node"][ev]
                        c["ctx"] += p["ctx"][ev]
                        c["node_only"] += p["node"][ev] and not p["ctx"][ev]
                        c["ctx_outcome_route"] += p["ctx"][ev] and ev in oroute
            cov[v] = dict(c)
        D = {}
        for v in ("C3", "C4", "C5", "C6"):
            for key in ("node", "ctx"):
                groups = defaultdict(list)
                for r in rows:
                    g = "success" if r["success"] else "failed"
                    if r["kind"] == "message":
                        groups[f"message:{r['label']}|{g}"].append(r[f"m_{key}_{v}"])
                        pk = r["predecessor"] if not r["predecessor"].startswith("tool:") else (
                            "tool:transfer" if r["predecessor"] == "tool:transfer_to_human_agents" else "tool:other")
                        groups[f"message|pred={pk}|{g}"].append(r[f"m_{key}_{v}"])
                    else:
                        groups[f"tool:{r['label']}|{g}"].append(r[f"m_{key}_{v}"])
                for k, xs in groups.items():
                    D[f"{v}|{key}|{k}"] = dist(xs)
        unexpected = Counter()
        for r in rows:
            for v in ALL:
                for key in ("node", "ctx"):
                    m = r[f"m_{key}_{v}"]
                    unexpected[f"{v}|{key}"] += (r["label"] == "valid" and m < THRESH) or \
                                                (r["label"] == "incorrect" and m >= THRESH)
        S["tasks"][t] = {"cost_C6": data["C6"]["cost"], "stage_stats": dict(tstats),
                         "outcome_admissions_by_tool": dict(adm_by_tool), "coverage": cov, "distributions": D,
                         "unexpected": dict(unexpected)}
    S["checks"] = dict(S["checks"])
    distinct = {}
    for x in S["outcome_pairs"]:
        distinct.setdefault((x["task"], x["query"], x["q_msg"], x["reference"], x["r_msg"]), x)
    S["n_outcome_route_indicators"] = len(S["outcome_pairs"])
    S["n_distinct_outcome_pairs"] = len(distinct)
    S["outcome_pairs_identical_text"] = sum(x["identical_text"] for x in distinct.values())
    (OUT / "c6_summary.json").write_text(json.dumps(S, indent=1, ensure_ascii=False, default=str) + "\n")
    with open(OUT / "per_step_masks_c6.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_all[0].keys()))
        w.writeheader()
        w.writerows(rows_all)
    print(json.dumps(S["checks"], indent=1))
    print("outcome-route indicators:", S["n_outcome_route_indicators"], "distinct pairs:", S["n_distinct_outcome_pairs"],
          "identical text:", S["outcome_pairs_identical_text"])
    print(f"wrote {OUT}/c6_summary.json, per_step_masks_c6.csv")


if __name__ == "__main__":
    {"compute": compute, "analyze": analyze}[sys.argv[1]]()
