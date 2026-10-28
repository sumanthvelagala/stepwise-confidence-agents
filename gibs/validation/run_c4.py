"""
C4 experiment (plan: gibs/validation/c4_plan.md). C4 = C3 with the paper-literal projection, i.e. without our
event-context edges. OUR adaptation, not the paper's algorithm.

    .venv/bin/python -B gibs/validation/run_c4.py compute   # MCS for every (query, reference) pair; resumable
    .venv/bin/python -B gibs/validation/run_c4.py analyze   # A/C0/C3 (read-only from results_pilot/) vs C4

Writes only to gibs/validation/results_c4/. Never touches results_pilot/.
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
from gibs.mcs.structured_fields import StructuredFieldValidator, compare_tool_events  # noqa: E402
from gibs.validation.run_pilot import K_VALUES, N_SUBSETS, OUT as PILOT_OUT, TASKS, THRESH, VARIANTS, load_runs  # noqa: E402
from gibs.validation.step_verification import classify_steps  # noqa: E402

OUT = REPO / "gibs/validation/results_c4"
C4 = {**VARIANTS["C3"], "topology": "paper_literal",
      "status": "OUR adaptation: C3 (symmetric truncation + multi-component + structured fields + same kind) "
                "on the paper-literal projection (no event-context edges)"}
ALL = ["A", "C0", "C3", "C4"]
BINS = [("0", lambda x: x == 0), ("(0,.25)", lambda x: 0 < x < .25), ("[.25,.5)", lambda x: .25 <= x < .5),
        ("[.5,.75)", lambda x: .5 <= x < .75), ("[.75,1)", lambda x: .75 <= x < 1), ("1", lambda x: x == 1)]


# --------------------------------------------------------------------------------------------- compute
def compute():
    from gibs.mcs.nli import DebertaEntailment
    OUT.mkdir(parents=True, exist_ok=True)
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate").with_overlength(C4["overlength"])
    sim = Similarity(model, direction="max_bidirectional")
    (OUT / "model.json").write_text(json.dumps(model.describe(), indent=2) + "\n")
    for task_id in TASKS:
        path = OUT / f"task{task_id}_C4.json"
        if path.exists():
            print(f"T{task_id} C4: exists, skipping", flush=True)
            continue
        runs, skipped = load_runs(task_id)
        succ = [r for r in runs if r["success"]]
        proj = {r["id"]: project(r["steps"], C4["topology"]) for r in runs}
        t0, f0, n0 = time.time(), model.n_forward, model.n_requested
        queries = []
        for qi, q in enumerate(runs):
            refs = [r for r in succ if r["id"] != q["id"]]          # never its own reference
            per_ref = []
            for r in refs:
                validator = StructuredFieldValidator(q["steps"], r["steps"])
                res = C4["matcher"](proj[q["id"]], proj[r["id"]], sim, C4["mcs"], field_check=validator)
                ind = pair_indicators(proj[q["id"]], res)
                per_ref.append({"reference": r["id"],
                                "node": {e: x["node_level"] for e, x in ind.items()},
                                "ctx": {e: x["context_step_level"] for e, x in ind.items()},
                                "node_map": res.node_map, "edge_map": res.edge_map,
                                "n_components": len(res.components) or (1 if res.edge_map else 0),
                                "n_rejected": len(res.rejected)})
            queries.append({"query": q["id"], "success": q["success"], "per_reference": per_ref})
            print(f"T{task_id} C4: query {qi + 1}/{len(runs)} ({q['short']}, refs={len(refs)}) "
                  f"elapsed={time.time() - t0:.0f}s forward={model.n_forward - f0}", flush=True)
        cost = {"seconds": round(time.time() - t0, 1), "nli_forward_passes_uncached": model.n_forward - f0,
                "nli_directional_pairs_requested": model.n_requested - n0,
                "n_mcs_runs": sum(len(q["per_reference"]) for q in queries)}
        path.write_text(json.dumps({"task": task_id, "variant": "C4", "status": C4["status"], "skipped_runs": skipped,
                                    "cost": cost, "queries": queries}) + "\n")
        print(f"T{task_id} C4: done {cost}", flush=True)


# --------------------------------------------------------------------------------------------- analyze helpers
def r3(x):
    return None if x is None else round(x, 3)


def load_variant(t, v):
    path = (OUT if v == "C4" else PILOT_OUT) / f"task{t}_{v}.json"
    return json.loads(path.read_text())


def mask(prs, ev, key, subset=None):
    rows = prs if subset is None else [prs[i] for i in subset]
    return sum(p[key][ev] for p in rows) / len(rows)


def dist(xs):
    return {"n": len(xs), "mean": r3(statistics.mean(xs)), "median": r3(statistics.median(xs)),
            "min": r3(min(xs)), "max": r3(max(xs)), "bins": {b: sum(f(x) for x in xs) for b, f in BINS}}


def auroc(pos, neg):
    """Mann-Whitney AUROC, ties count 1/2."""
    if not pos or not neg:
        return None
    s = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return s / (len(pos) * len(neg))


def subtype(n):
    return n["tool_call"]["name"] if n["kind"] == "tool_call" else "message"


def kind(n):
    if n["type"] == "UserTurn":
        return "user_turn"
    return "tool:" + n["tool_call"]["name"] if n["kind"] == "tool_call" else "agent_message"


# --------------------------------------------------------------------------------------------- analyze
def analyze():
    rng = random.Random(0)
    summary = {"plan": "gibs/validation/c4_plan.md", "tasks": {}}
    csv_rows, review_msgs, review_labelled, audit = [], [], [], Counter()
    audit_examples = []
    for t in TASKS:
        runs, _ = load_runs(t)
        by_id = {r["id"]: r for r in runs}
        nodes = {r["id"]: {n["id"]: n for n in r["steps"]["nodes"]} for r in runs}
        agent_order = {r["id"]: [n["id"] for n in r["steps"]["nodes"] if n["type"] == "AgentStep"] for r in runs}
        labels = {r["id"]: classify_steps(r["steps"], r["task"]) for r in runs}
        data = {v: load_variant(t, v) for v in ALL}
        qv = {v: {q["query"]: q for q in data[v]["queries"]} for v in ALL}
        # same queries and the same references in the same order for every variant
        for v in ALL:
            assert [(q["query"], [p["reference"] for p in q["per_reference"]]) for q in data[v]["queries"]] == \
                   [(q["query"], [p["reference"] for p in q["per_reference"]]) for q in data["C3"]["queries"]], v
        tinfo = {"n_success": sum(r["success"] for r in runs), "n_failed": sum(not r["success"] for r in runs),
                 "cost_C4": data["C4"]["cost"], "label_counts": {}, "distributions": {}, "unexpected": [],
                 "c4_vs_c3": {}, "auroc": {}, "curve_C4": {}, "drift": {}, "safety": {}}
        rows = []
        for q in data["C3"]["queries"]:
            rid = q["query"]
            if not q["per_reference"]:
                continue
            for ev in q["per_reference"][0]["node"]:
                n = nodes[rid][ev]
                row = {"task": t, "run": rid[:8], "success": by_id[rid]["success"], "step": ev, "kind": n["kind"],
                       "text": (n["op_text"] or "")[:100], "label": labels[rid][ev]["label"]}
                for v in ALL:
                    prs = qv[v][rid]["per_reference"]
                    row[f"m_node_{v}"] = r3(mask(prs, ev, "node"))
                    row[f"m_ctx_{v}"] = r3(mask(prs, ev, "ctx"))
                row["what"] = subtype(n)
                rows.append(row)
        csv_rows += rows
        tinfo["label_counts"] = dict(Counter(f"{'success' if r['success'] else 'failed'}|{r['label']}" for r in rows))
        for v in ALL:
            for key in ("node", "ctx"):
                groups = defaultdict(list)
                for r in rows:
                    g = "success" if r["success"] else "failed"
                    groups[f"{r['label']}|{g}"].append(r[f"m_{key}_{v}"])
                    if r["label"] == "valid":
                        groups[f"valid:{r['what']}|{g}"].append(r[f"m_{key}_{v}"])
                for k, xs in groups.items():
                    tinfo["distributions"][f"{v}|{key}|{k}"] = dist(xs)
                for r in rows:
                    m = r[f"m_{key}_{v}"]
                    if (r["label"] == "valid" and m < THRESH) or (r["label"] == "incorrect" and m >= THRESH):
                        tinfo["unexpected"].append({"variant": v, "target": key, "run": r["run"], "success": r["success"],
                                                    "step": r["step"], "label": r["label"], "value": m, "text": r["text"]})
                pos = [r[f"m_{key}_{v}"] for r in rows if r["label"] == "valid"]
                neg = [r[f"m_{key}_{v}"] for r in rows if r["label"] == "incorrect"]
                tinfo["auroc"][f"{v}|{key}"] = {"n_pos": len(pos), "n_neg": len(neg),
                                               "auroc": r3(auroc(pos, neg)) if len(pos) >= 5 and len(neg) >= 5 else None}
        for key in ("node", "ctx"):
            d = [r[f"m_{key}_C4"] - r[f"m_{key}_C3"] for r in rows]
            by_lab = {lab: {"increased": sum(x > 1e-9 for x, r in zip(d, rows) if r["label"] == lab),
                            "decreased": sum(x < -1e-9 for x, r in zip(d, rows) if r["label"] == lab),
                            "mean_change": r3(statistics.mean([x for x, r in zip(d, rows) if r["label"] == lab]))}
                      for lab in {r["label"] for r in rows}}
            tinfo["c4_vs_c3"][key] = {"steps": len(d), "increased": sum(x > 1e-9 for x in d),
                                      "decreased": sum(x < -1e-9 for x in d), "mean_change": r3(statistics.mean(d)),
                                      "by_label": by_lab}
        # reference-count curve for C4 (same k values and subset count as run_pilot; seed 0)
        for key in ("node", "ctx"):
            curve = {}
            for k in K_VALUES + ["all"]:
                dev, val_m, inc_m, unexpected = [], [], [], 0
                for q in data["C4"]["queries"]:
                    prs = q["per_reference"]
                    kk = len(prs) if k == "all" else k
                    if not prs or kk > len(prs):
                        continue
                    subsets = [list(range(len(prs)))] if k == "all" else \
                        [rng.sample(range(len(prs)), kk) for _ in range(N_SUBSETS)]
                    for ev in prs[0][key]:
                        full = mask(prs, ev, key)
                        lab = labels[q["query"]][ev]["label"]
                        for sub in subsets:
                            m = mask(prs, ev, key, sub)
                            dev.append(abs(m - full))
                            if lab == "valid":
                                val_m.append(m)
                                unexpected += m < THRESH
                            elif lab == "incorrect":
                                inc_m.append(m)
                                unexpected += m >= THRESH
                curve[str(k)] = {"mean_abs_dev_from_full": round(statistics.mean(dev), 4),
                                 "mean_valid": r3(statistics.mean(val_m)) if val_m else None,
                                 "mean_incorrect": r3(statistics.mean(inc_m)) if inc_m else None,
                                 "unexpected_rate": r3(unexpected / max(1, len(val_m) + len(inc_m)))}
            tinfo["curve_C4"][key] = curve
        # mapping audits: kinds, tools, structured conflicts, positional drift, new matches (C3 -> C4)
        for v in ALL:
            drift, cnt = [], Counter()
            for q in data[v]["queries"]:
                qid = q["query"]
                for p in q["per_reference"]:
                    rid = p["reference"]
                    for n1, n2 in p["node_map"].items():
                        if not n1.startswith("N:s"):
                            continue
                        a = nodes[qid][n1[2:]]
                        b = nodes[rid].get(n2[2:]) if n2.startswith("N:") else None
                        if b is None or kind(a).split(":")[0] != kind(b).split(":")[0]:
                            cnt["cross_kind"] += 1
                            continue
                        if a["kind"] == "tool_call":
                            if a["tool_call"]["name"] != b["tool_call"]["name"]:
                                cnt["cross_tool"] += 1
                            elif not compare_tool_events(a, b).compatible:
                                cnt["structured_conflict"] += 1
                                if v == "C4":
                                    audit_examples.append({"task": t, "query": qid[:8], "step": n1[2:],
                                                           "reference": rid[:8], "ref_step": n2[2:],
                                                           "reasons": compare_tool_events(a, b).hard})
                            else:
                                cnt["same_tool_compatible"] += 1
                        else:
                            cnt["same_kind_message"] += 1
                        qa, ra = agent_order[qid], agent_order[rid]
                        drift.append(abs(qa.index(n1[2:]) / max(1, len(qa) - 1) - ra.index(n2[2:]) / max(1, len(ra) - 1)))
            tinfo["safety"][v] = dict(cnt)
            tinfo["drift"][v] = {"pairs": len(drift), "mean": r3(statistics.mean(drift)) if drift else None,
                                 "share_gt_0.25": r3(sum(x > .25 for x in drift) / len(drift)) if drift else None,
                                 "share_gt_0.5": r3(sum(x > .5 for x in drift) / len(drift)) if drift else None}
            if v == "C4":
                audit.update({f"T{t}|{k}": n for k, n in cnt.items()})
        for q in data["C4"]["queries"]:
            qid = q["query"]
            q3 = qv["C3"][qid]
            for p4, p3 in zip(q["per_reference"], q3["per_reference"]):
                for ev in p4["node"]:
                    nid = "N:" + ev
                    m4, m3 = p4["node_map"].get(nid), p3["node_map"].get(nid)
                    if m4 is None or m4 == m3:
                        continue
                    a, b = nodes[qid][ev], nodes[p4["reference"]].get(m4[2:])
                    item = {"task": t, "query": qid[:8], "query_success": by_id[qid]["success"], "step": ev,
                            "label": labels[qid][ev]["label"], "reference": p4["reference"][:8],
                            "c3_target": m3, "c4_target": m4, "change": "newly matched" if m3 is None else "re-mapped",
                            "query_text": (a["op_text"] or "")[:300], "ref_text": (b["op_text"] or "")[:300] if b else None,
                            "c4_ctx": p4["ctx"][ev]}
                    if labels[qid][ev]["label"] != "unverified":
                        review_labelled.append(item)
                    elif a["kind"] == "message":
                        review_msgs.append(item)
        tinfo["lookup_groups_T48"] = t48_groups(runs, qv) if t == "48" else None
        summary["tasks"][t] = tinfo
    sample = random.Random(0).sample(review_msgs, min(30, len(review_msgs)))
    summary["audit_C4_mapped_agent_nodes"] = dict(audit)
    summary["audit_C4_structured_conflicts"] = audit_examples
    summary["review"] = {"labelled_new_or_remapped": review_labelled, "n_message_new_or_remapped": len(review_msgs),
                         "message_sample_seed0": sample}
    (OUT / "c4_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    with open(OUT / "per_step_masks_c4.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)
    (OUT / "tables_c4.md").write_text(tables(summary, csv_rows))
    print(f"wrote {OUT}/c4_summary.json, per_step_masks_c4.csv, tables_c4.md")


def t48_groups(runs, qv):
    def group(r):
        ns = r["steps"]["nodes"]
        first_user = next(n["id"] for n in ns if n["type"] == "UserTurn")
        lk = next(n["id"] for n in ns if n.get("kind") == "tool_call" and n["tool_call"]["name"] == "get_reservation_details")
        srcs = [e["source"] for e in r["steps"]["edges"] if e["type"] == "data_dependency" and e["target"] == lk]
        return ("O" if first_user in srcs else "L"), lk
    grp = {r["id"]: group(r) for r in runs}
    out = {}
    for v in ALL:
        acc = defaultdict(list)
        for qid, q in qv[v].items():
            g, lk = grp[qid]
            for p in q["per_reference"]:
                acc[f"{g}x{grp[p['reference']][0]}"].append(p["node"][lk])
        out[v] = {k: {"pairs": len(x), "rate": r3(sum(x) / len(x))} for k, x in sorted(acc.items())}
    return out


def tables(s, rows) -> str:
    L = ["# C4 vs A / C0 / C3: generated tables (run_c4.py analyze)", "",
         "C4 = C3 on the paper-literal projection (OUR adaptation). Values are consensus fractions, not correctness.",
         "Bins: " + " | ".join(b for b, _ in BINS), ""]
    for t, x in s["tasks"].items():
        L += [f"## Task {t} ({x['n_success']} successful, {x['n_failed']} failed)", "",
              f"Labels: {x['label_counts']}", f"C4 cost: {x['cost_C4']}", "",
              "| Variant | Target | Label | Runs | n | mean | median | bins |", "|---|---|---|---|---|---|---|---|"]
        for k, d in sorted(x["distributions"].items(), key=lambda kv: (kv[0].split("|")[2], kv[0].split("|")[1], kv[0])):
            v, tgt, lab, g = k.split("|")
            L.append(f"| {v} | {tgt} | {lab} | {g} | {d['n']} | {d['mean']} | {d['median']} | "
                     + " ".join(str(d["bins"][b]) for b, _ in BINS) + " |")
        L += ["", "| Unexpected (variant, target) | count |", "|---|---|"]
        c = Counter((u["variant"], u["target"]) for u in x["unexpected"])
        for v in ALL:
            for tgt in ("node", "ctx"):
                L.append(f"| {v} {tgt} | {c[(v, tgt)]} |")
        L += ["", "| C4 unexpected case | target | value | text |", "|---|---|---|---|"]
        for u in x["unexpected"]:
            if u["variant"] == "C4":
                L.append(f"| {u['run']} {u['step']} ({u['label']}, {'succ' if u['success'] else 'fail'}) | {u['target']} | "
                         f"{u['value']} | {u['text'][:80].replace('|', '/')} |")
        L += ["", f"C4 − C3: {json.dumps(x['c4_vs_c3'])}", "", f"AUROC: {json.dumps(x['auroc'])}", "",
              f"Mapping audit: {json.dumps(x['safety'])}", "", f"Positional drift: {json.dumps(x['drift'])}", ""]
        if x["lookup_groups_T48"]:
            L += [f"T48 lookup groups: {json.dumps(x['lookup_groups_T48'])}", ""]
        L += ["| C4 k | target | mean abs dev | mean valid | mean incorrect | unexpected rate |", "|---|---|---|---|---|---|"]
        for tgt, curve in x["curve_C4"].items():
            for k, cv in curve.items():
                L.append(f"| {k} | {tgt} | {cv['mean_abs_dev_from_full']} | {cv['mean_valid']} | {cv['mean_incorrect']} | "
                         f"{cv['unexpected_rate']} |")
        L += ["", "### Per-step masks (m_node / m_ctx)", "", "| Run | Succ | Step | Label | Text | A | C0 | C3 | C4 |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["task"] != t:
                continue
            L.append(f"| {r['run']} | {r['success']} | {r['step']} | {r['label']} | {r['text'][:60].replace('|', '/')} | "
                     + " | ".join(f"{r[f'm_node_{v}']:.2f}/{r[f'm_ctx_{v}']:.2f}" for v in ALL) + " |")
        L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------------------------- audit
def audit():
    """ROOT and data-dependency audit of the stored C4 mappings (no re-matching). Writes results_c4/c4_audit.json.

    * ROOT: ROOT may only map to ROOT; a ROOT edge may only map to a ROOT edge; which tool calls hang from ROOT.
    * Data support: for every mapped (query tool step, reference) pair, whether each incoming data edge is mapped,
      whether mapped data edges join sources of the same kind, and whether they carry the same dependency values.
    """
    out = {"root": {}, "dependency_support": {}, "root_hanging_tool_calls": []}
    for t in TASKS:
        runs, _ = load_runs(t)
        nodes = {r["id"]: {n["id"]: n for n in r["steps"]["nodes"]} for r in runs}
        labels = {r["id"]: classify_steps(r["steps"], r["task"]) for r in runs}
        proj = {r["id"]: project(r["steps"], C4["topology"]) for r in runs}
        dvals = {r["id"]: {(f"N:{e['source']}", f"N:{e['target']}"): sorted(e["values"])
                           for e in r["steps"]["edges"] if e["type"] == "data_dependency"} for r in runs}
        for r in runs:
            for nid, n in proj[r["id"]].nodes.items():
                if n["kind"] == "tool_result" and [e["roles"] for e in proj[r["id"]].in_edges(nid)] == [["root"]]:
                    tc = nodes[r["id"]][n["event"]]["tool_call"]
                    out["root_hanging_tool_calls"].append({"task": t, "run": r["id"][:8], "step": n["event"],
                                                           "tool": tc["name"], "arguments": tc["arguments"],
                                                           "label": labels[r["id"]][n["event"]]["label"]})
        root, sup = Counter(), Counter()
        examples = []
        for q in load_variant(t, "C4")["queries"]:
            g1 = proj[q["query"]]
            for p in q["per_reference"]:
                g2 = proj[p["reference"]]
                for a, b in p["node_map"].items():
                    root["ROOT->ROOT" if a == b == "ROOT" else
                         ("ROOT<->non-ROOT" if "ROOT" in (a, b) else "non-ROOT")] += 1
                for e1, e2 in p["edge_map"].items():
                    r1 = next(e for e in g1.edges if e["id"] == e1)["roles"]
                    r2 = next(e for e in g2.edges if e["id"] == e2)["roles"]
                    root["edge " + ("root<->root" if r1 == r2 == ["root"] else
                                    "data<->data" if r1 == r2 == ["data"] else "root<->data (mixed)")] += 1
                for ev, node_ok in p["node"].items():
                    nid = "N:" + ev
                    if g1.nodes[nid]["kind"] != "tool_result" or not node_ok:
                        continue
                    data_in = [e for e in g1.in_edges(nid) if e["roles"] == ["data"]]
                    if not data_in:
                        continue
                    lab = labels[q["query"]][ev]["label"]
                    mapped = [e for e in data_in if e["id"] in p["edge_map"]]
                    sup[f"{lab}|pairs_node_mapped"] += 1
                    if len(mapped) < len(data_in):
                        sup[f"{lab}|node_mapped_but_some_data_edge_unmapped"] += 1
                        if len(examples) < 40:
                            examples.append({"task": t, "query": q["query"][:8], "step": ev, "label": lab,
                                             "reference": p["reference"][:8], "ref_step": p["node_map"][nid],
                                             "unmapped_data_edges": [e["id"] for e in data_in if e not in mapped],
                                             "mapped_data_edges": {e["id"]: p["edge_map"][e["id"]] for e in mapped}})
                    for e in mapped:
                        e2 = next(x for x in g2.edges if x["id"] == p["edge_map"][e["id"]])
                        k1, k2 = g1.nodes[e["src"]]["kind"], g2.nodes[e2["src"]]["kind"]
                        v1 = dvals[q["query"]][(e["src"], e["dst"])]
                        v2 = dvals[p["reference"]].get((e2["src"], e2["dst"]))
                        sup[f"{lab}|mapped_data_edges"] += 1
                        sup[f"{lab}|mapped_data_edge_source_kind_differs"] += k1 != k2
                        sup[f"{lab}|mapped_data_edge_values_differ"] += v1 != v2
        out["root"][t] = dict(root)
        out["dependency_support"][t] = {"counts": dict(sup), "examples": examples}
    (OUT / "c4_audit.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({t: out["root"][t] for t in TASKS}, indent=1))
    print(json.dumps({t: out["dependency_support"][t]["counts"] for t in TASKS}, indent=1))
    print(Counter((x["task"], x["tool"], x["label"]) for x in out["root_hanging_tool_calls"]))


if __name__ == "__main__":
    {"compute": compute, "analyze": analyze, "audit": audit}[sys.argv[1]]()
