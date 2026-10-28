"""
Post-hoc diagnostics for the consensus-mask pilot (REPORT_pilot.md). Reads the stored per-reference MCS results in
results_pilot/; it never re-runs MCS and changes no threshold, graph, matching rule, reference set or label.
NLI scores quoted in the case studies are read back through the existing cache (forward passes are counted and
reported; expected 0).

    .venv/bin/python -B gibs/validation/pilot_diagnostics.py      # -> results_pilot/diagnostics.{json,md}

Everything here is diagnostic and was NOT pre-registered in pilot_plan.md, except the label counts.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.mcs.mcs import _Scorer  # noqa: E402
from gibs.mcs.structured_fields import WRITE_TOOLS, StructuredFieldValidator  # noqa: E402
from gibs.validation.run_pilot import OUT, TASKS, VARIANTS, load_runs  # noqa: E402
from gibs.validation.step_verification import classify_steps  # noqa: E402

LABELS = ("valid", "incorrect", "attempted_incorrect", "unverified")
BINS = [("0", lambda x: x == 0), ("(0,.25)", lambda x: 0 < x < .25), ("[.25,.5)", lambda x: .25 <= x < .5),
        ("[.5,.75)", lambda x: .5 <= x < .75), ("[.75,1)", lambda x: .75 <= x < 1), ("1", lambda x: x == 1)]


def r3(x):
    return round(x, 3)


def step_kind(n: dict) -> str:
    if n["type"] == "UserTurn":
        return "user_turn"
    return "tool:" + n["tool_call"]["name"] if n["kind"] == "tool_call" else "agent_message"


def subtype(n: dict) -> str:
    return n["tool_call"]["name"] if n["kind"] == "tool_call" else "message"


class Ctx:
    def __init__(self):
        self.runs, self.by_id, self.labels, self.data, self.proj = {}, {}, {}, {}, {}
        for t in TASKS:
            runs, _ = load_runs(t)
            self.runs[t] = runs
            for r in runs:
                self.by_id[r["id"]] = r
                self.labels[r["id"]] = classify_steps(r["steps"], r["task"])
                for topo in ("event_context", "paper_literal"):
                    self.proj[(r["id"], topo)] = project(r["steps"], topo)
            for v in VARIANTS:
                self.data[(t, v)] = json.loads((OUT / f"task{t}_{v}.json").read_text())

    def queries(self, t, v):
        return self.data[(t, v)]["queries"]

    def g(self, rid, v):
        return self.proj[(rid, VARIANTS[v]["topology"])]

    def get(self, t, short):
        return next(r for r in self.runs[t] if r["id"].startswith(short))


def masks(prs, ev):
    n = len(prs)
    return sum(p["node"][ev] for p in prs) / n, sum(p["ctx"][ev] for p in prs) / n


# ------------------------------------------------------------------------------------------------ D1-D3
def label_counts(c: Ctx):
    out = {}
    for t in TASKS:
        cnt, sub = Counter(), Counter()
        for r in c.runs[t]:
            nodes = {n["id"]: n for n in r["steps"]["nodes"]}
            for ev, lab in c.labels[r["id"]].items():
                g = "success" if r["success"] else "failed"
                cnt[(g, lab["label"])] += 1
                if lab["label"] != "unverified":
                    sub[(g, lab["label"], subtype(nodes[ev]))] += 1
        out[t] = {"n_success": sum(r["success"] for r in c.runs[t]), "n_failed": sum(not r["success"] for r in c.runs[t]),
                  "counts": {f"{g}|{lab}": cnt[(g, lab)] for g in ("success", "failed") for lab in LABELS},
                  "labelled_subtypes": {"|".join(k): n for k, n in sorted(sub.items())}}
    return out


def distributions(c: Ctx):
    out = {}
    for t in TASKS:
        for v in VARIANTS:
            vals = defaultdict(list)
            for q in c.queries(t, v):
                prs = q["per_reference"]
                if not prs:
                    continue
                r = c.by_id[q["query"]]
                nodes = {n["id"]: n for n in r["steps"]["nodes"]}
                for ev, lab in c.labels[r["id"]].items():
                    mn, mc = masks(prs, ev)
                    g = "success" if r["success"] else "failed"
                    for tgt, m in (("node", mn), ("ctx", mc)):
                        vals[(tgt, lab["label"], g)].append(m)
                        if lab["label"] == "valid":
                            vals[(tgt, "valid:" + subtype(nodes[ev]), g)].append(m)
            for (tgt, lab, g), xs in vals.items():
                out[f"{t}|{v}|{tgt}|{lab}|{g}"] = {
                    "n": len(xs), "mean": r3(statistics.mean(xs)), "median": r3(statistics.median(xs)),
                    "min": r3(min(xs)), "max": r3(max(xs)), "bins": {b: sum(f(x) for x in xs) for b, f in BINS}}
    return out


# ------------------------------------------------------------------------------------------------ D4
def pool_composition(c: Ctx):
    out = {}
    for t in TASKS:
        succ = [r for r in c.runs[t] if r["success"]]
        tools = Counter()
        for r in succ:
            for name in {n["tool_call"]["name"] for n in r["steps"]["nodes"] if n.get("kind") == "tool_call"
                         and not n["observation"]["error"]}:
                tools[name] += 1
        # labelled steps whose tool / message has no successful counterpart in ANY successful run
        unmatchable = []
        for r in c.runs[t]:
            nodes = {n["id"]: n for n in r["steps"]["nodes"]}
            for ev, lab in c.labels[r["id"]].items():
                if lab["label"] == "unverified":
                    continue
                n = nodes[ev]
                key = n["tool_call"]["name"] if n["kind"] == "tool_call" else "transfer_to_human_agents"
                if tools[key] == 0:
                    unmatchable.append({"run": r["id"][:8], "success": r["success"], "step": ev, "label": lab["label"],
                                        "what": subtype(n), "reason": f"no successful run contains a successful {key}"})
        out[t] = {"n_successful_runs_with_tool": dict(tools.most_common()),
                  "write_tools_in_successful_runs": {k: n for k, n in tools.items() if k in WRITE_TOOLS},
                  "structurally_unmatchable_labelled_steps": unmatchable}
    return out


# ------------------------------------------------------------------------------------------------ D5
def cross_kind(c: Ctx):
    out = {}
    for t in TASKS:
        kinds = {r["id"]: {"N:" + n["id"]: step_kind(n) for n in r["steps"]["nodes"]} for r in c.runs[t]}
        for v in VARIANTS:
            cnt, ex = Counter(), Counter()
            for q in c.queries(t, v):
                for p in q["per_reference"]:
                    for n1, n2 in p["node_map"].items():
                        if not n1.startswith("N:s"):
                            continue
                        k1, k2 = kinds[q["query"]][n1], kinds[p["reference"]].get(n2, "root")
                        rel = "same" if k1 == k2 else ("cross_kind" if k1.split(":")[0] != k2.split(":")[0]
                                                       else "cross_tool")
                        lab = c.labels[q["query"]][n1[2:]]["label"]
                        cnt[(lab, rel)] += 1
                        if rel != "same":
                            ex[f"{lab}: {k1} -> {k2}"] += 1
            out[f"{t}|{v}"] = {"counts": {"|".join(k): n for k, n in sorted(cnt.items())}, "examples": dict(ex)}
    return out


# ------------------------------------------------------------------------------------------------ D6
def ctx_decomposition(c: Ctx):
    """m_ctx vs 'data edges only' vs 'pure context edge' mapping, from stored edge maps (no re-matching)."""
    out = {}
    for t in TASKS:
        for v in VARIANTS:
            acc = defaultdict(list)
            srcs = Counter()
            for q in c.queries(t, v):
                prs = q["per_reference"]
                if not prs:
                    continue
                r = c.by_id[q["query"]]
                g = c.g(r["id"], v)
                for ev, lab in c.labels[r["id"]].items():
                    ins = g.in_edges("N:" + ev)
                    data = [e for e in ins if "data" in e["roles"]]
                    pure_ctx = [e for e in ins if e["roles"] == ["context"]]
                    n = len(prs)
                    full = sum(p["ctx"][ev] for p in prs) / n
                    d_only = sum(p["node"][ev] and all(e["id"] in p["edge_map"] for e in data) for p in prs) / n
                    c_rate = (sum(all(e["id"] in p["edge_map"] for e in pure_ctx) for p in prs) / n) if pure_ctx else None
                    acc[(lab["label"], "success" if r["success"] else "failed")].append((full, d_only, c_rate))
                    if lab["label"] == "valid" and pure_ctx:
                        s = g.nodes[pure_ctx[0]["src"]]
                        srcs[f"{s['kind']}: {(s['text'] or '')[:60]}"] += 1
            for (lab, grp), xs in acc.items():
                cr = [x[2] for x in xs if x[2] is not None]
                out[f"{t}|{v}|{lab}|{grp}"] = {
                    "n": len(xs), "m_ctx": r3(statistics.mean(x[0] for x in xs)),
                    "node_and_all_data_edges": r3(statistics.mean(x[1] for x in xs)),
                    "steps_with_pure_context_edge": len(cr),
                    "pure_context_edge_mapped": r3(statistics.mean(cr)) if cr else None}
            out[f"{t}|{v}|valid_pure_context_sources"] = dict(srcs.most_common(10))
    return out


# ------------------------------------------------------------------------------------------------ D7
def node_high_ctx_low(c: Ctx):
    out = {}
    for v in VARIANTS:
        rows, summary = [], Counter()
        for t in TASKS:
            for q in c.queries(t, v):
                prs = q["per_reference"]
                if not prs:
                    continue
                r = c.by_id[q["query"]]
                g = c.g(r["id"], v)
                nodes = {n["id"]: n for n in r["steps"]["nodes"]}
                for ev, lab in c.labels[r["id"]].items():
                    mn, mc = masks(prs, ev)
                    if not (mn >= 0.5 and mc < 0.5):
                        continue
                    summary[f"{t}|{lab['label']}|{subtype(nodes[ev])}"] += 1
                    edges = []
                    for e in g.in_edges("N:" + ev):
                        edges.append({"edge": e["id"], "roles": e["roles"], "src_kind": g.nodes[e["src"]]["kind"],
                                      "mapped_rate": r3(sum(e["id"] in p["edge_map"] for p in prs) / len(prs))})
                    # node mapped although some incoming edge is not: via which mapped edges?
                    via = Counter()
                    for p in prs:
                        if p["node"][ev] and not p["ctx"][ev]:
                            for e1 in p["edge_map"]:
                                s, d = e1.split("->")
                                if "N:" + ev in (s, d):
                                    via["in" if d == "N:" + ev else "out(successor)"] += 1
                    rows.append({"task": t, "run": r["id"][:8], "success": r["success"], "step": ev,
                                 "label": lab["label"], "what": subtype(nodes[ev]), "m_node": r3(mn), "m_ctx": r3(mc),
                                 "incoming_edges": edges, "node_only_support_via": dict(via)})
        out[v] = {"count": len(rows), "by_task_label_kind": dict(summary.most_common()), "steps": rows}
    return out


# ------------------------------------------------------------------------------------------------ D8
def t48_lookup_groups(c: Ctx):
    """Task 48 gold lookup: does the reservation ID come from the opening user turn (O) or a later turn (L)?"""
    def group(r):
        nodes = r["steps"]["nodes"]
        first_user = next(n["id"] for n in nodes if n["type"] == "UserTurn")
        lk = next(n["id"] for n in nodes if n.get("kind") == "tool_call"
                  and n["tool_call"]["name"] == "get_reservation_details")
        srcs = [e["source"] for e in r["steps"]["edges"] if e["type"] == "data_dependency" and e["target"] == lk]
        return ("O" if first_user in srcs else "L"), lk
    grp = {r["id"]: group(r) for r in c.runs["48"]}
    out = {"groups": {r["id"][:8]: {"group": grp[r["id"]][0], "lookup": grp[r["id"]][1], "success": r["success"]}
                      for r in c.runs["48"]}, "matrix": {}}
    for v in VARIANTS:
        acc = defaultdict(list)
        for q in c.queries("48", v):
            qg, lk = grp[q["query"]]
            for p in q["per_reference"]:
                acc[(qg, grp[p["reference"]][0], "node")].append(p["node"][lk])
                acc[(qg, grp[p["reference"]][0], "ctx")].append(p["ctx"][lk])
        out["matrix"][v] = {f"query {a} x ref {b} ({t})": {"pairs": len(xs), "rate": r3(sum(xs) / len(xs))}
                            for (a, b, t), xs in sorted(acc.items())}
    return out


# ------------------------------------------------------------------------------------------------ D9
def case_studies(c: Ctx):
    from gibs.mcs.nli import DebertaEntailment, Similarity
    author = DebertaEntailment(encoding="code_sep_string", overlength="truncate")
    models = {"truncate": author, "symmetric": author.with_overlength("symmetric")}
    sims = {k: Similarity(m, "max_bidirectional") for k, m in models.items()}

    def edge_report(t, qs, rs, v, ev):
        cfg = VARIANTS[v]
        q, r = c.get(t, qs), c.get(t, rs)
        g1, g2 = c.g(q["id"], v), c.g(r["id"], v)
        sc = _Scorer(g1, g2, sims[cfg["overlength"]], cfg["mcs"])
        val = StructuredFieldValidator(q["steps"], r["steps"]) if cfg["fields"] else None
        cands = []
        for e1 in g1.in_edges("N:" + ev):
            for e2 in g2.edges:
                se = sc.sim(e1["text"], e2["text"])
                if se < cfg["mcs"].tau_e:
                    continue
                ss, st = sc.node_sim(e1["src"], e2["src"]), sc.node_sim(e1["dst"], e2["dst"])
                if st < cfg["mcs"].tau_v:
                    continue
                reasons = val(g1, g2, e1, e2) if val else []
                cands.append({"q_edge": e1["id"], "r_edge": e2["id"], "s_edge": r3(se), "s_src": r3(ss), "s_tgt": r3(st),
                              "passes_R3_source": ss >= cfg["mcs"].tau_v, "field_reasons": reasons})
        qrow = next(x for x in c.queries(t, v) if x["query"] == q["id"])
        p = next(x for x in qrow["per_reference"] if x["reference"] == r["id"])
        return {"query": qs, "reference": rs, "variant": v, "step": ev,
                "candidates_for_incoming_edges (s_edge>=0.7, s_tgt>=0.7)": cands,
                "stored": {"node": p["node"][ev], "ctx": p["ctx"][ev], "n_components": p["n_components"],
                           "node_map": p["node_map"], "edge_map": p["edge_map"]}}

    def text(t, s, ev):
        return c.proj[(c.get(t, s)["id"], "event_context")].nodes["N:" + ev]["text"]

    def op(t, s, ev):
        g = c.proj[(c.get(t, s)["id"], "event_context")]
        return next(e["text"] for e in g.edges if e["dst"] == "N:" + ev)

    m = author
    t48_refs = [r["id"][:8] for r in c.runs["48"] if r["success"] and not r["id"].startswith("5b5eaa71")]
    out = {
        "T48_5b5eaa71_s2": {v: [edge_report("48", "5b5eaa71", rs, v, "s2") for rs in t48_refs] for v in VARIANTS},
        "T48_07ec0bf6_s2_vs_c890f90b": {v: edge_report("48", "07ec0bf6", "c890f90b", v, "s2") for v in VARIANTS},
        "T48_opening_turn_nli": {
            "texts": {"5b5eaa71.u1": text("48", "5b5eaa71", "u1"), "07ec0bf6.u1": text("48", "07ec0bf6", "u1"),
                      "c890f90b.u1": text("48", "c890f90b", "u1"), "c890f90b.u3": text("48", "c890f90b", "u3")},
            "directional": {
                "5b5eaa71.u1 => 07ec0bf6.u1": r3(m.entail_batch([(text("48", "5b5eaa71", "u1"), text("48", "07ec0bf6", "u1"))])[0]),
                "07ec0bf6.u1 => 5b5eaa71.u1": r3(m.entail_batch([(text("48", "07ec0bf6", "u1"), text("48", "5b5eaa71", "u1"))])[0]),
                "5b5eaa71.u1 => c890f90b.u3": r3(m.entail_batch([(text("48", "5b5eaa71", "u1"), text("48", "c890f90b", "u3"))])[0]),
                "07ec0bf6.u1 => c890f90b.u3": r3(m.entail_batch([(text("48", "07ec0bf6", "u1"), text("48", "c890f90b", "u3"))])[0]),
                "5b5eaa71.u1 => c890f90b.u1": r3(m.entail_batch([(text("48", "5b5eaa71", "u1"), text("48", "c890f90b", "u1"))])[0]),
                "07ec0bf6.u1 => c890f90b.u1": r3(m.entail_batch([(text("48", "07ec0bf6", "u1"), text("48", "c890f90b", "u1"))])[0]),
            }},
        "T48_transfer_call_c890f90b_s8_vs_07ec0bf6": {
            "op_q": op("48", "c890f90b", "s8"), "op_r": op("48", "07ec0bf6", "s4"),
            "op_similarity": r3(sims["symmetric"](op("48", "c890f90b", "s8"), op("48", "07ec0bf6", "s4"))),
            "C3": edge_report("48", "c890f90b", "07ec0bf6", "C3", "s8")},
        "T25_6f12b024_s30_vs_0f0f7358": {v: edge_report("25", "6f12b024", "0f0f7358", v, "s30") for v in VARIANTS},
    }
    # T25 incorrect booking: what does A map it to across all references?
    q = c.get("25", "6f12b024")
    qa = next(x for x in c.queries("25", "A") if x["query"] == q["id"])
    out["T25_6f12b024_s30_A_targets"] = Counter(
        f"{step_kind({n['id']: n for n in c.by_id[p['reference']]['steps']['nodes']}[p['node_map']['N:s30'][2:]])}"
        f" labelled {c.labels[p['reference']][p['node_map']['N:s30'][2:]]['label']}"
        for p in qa["per_reference"] if "N:s30" in p["node_map"])
    out["nli_forward_passes_uncached"] = sum(x.n_forward for x in models.values())
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    c = Ctx()
    res = {"note": "post-hoc diagnostics; not pre-registered except label counts",
           "label_counts": label_counts(c), "distributions": distributions(c), "pool": pool_composition(c),
           "cross_kind": cross_kind(c), "ctx_decomposition": ctx_decomposition(c),
           "node_high_ctx_low": node_high_ctx_low(c), "t48_lookup_groups": t48_lookup_groups(c)}
    res["case_studies"] = case_studies(c)
    (OUT / "diagnostics.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n")
    (OUT / "diagnostics.md").write_text(render(res))
    print(f"wrote {OUT}/diagnostics.json, diagnostics.md; uncached NLI forward passes: "
          f"{res['case_studies']['nli_forward_passes_uncached']}")


def render(res) -> str:
    L = ["# Pilot diagnostics (generated by pilot_diagnostics.py; post-hoc, not pre-registered)", ""]
    L += ["## Label counts", "", "| Task | Runs (succ/fail) | " + " | ".join(
        f"{g} {lab}" for g in ("success", "failed") for lab in LABELS) + " |", "|---|---|" + "---|" * 8]
    for t, x in res["label_counts"].items():
        L.append(f"| {t} | {x['n_success']}/{x['n_failed']} | " + " | ".join(
            str(x["counts"][f"{g}|{lab}"]) for g in ("success", "failed") for lab in LABELS) + " |")
    L += ["", "## Distributions (bins: " + ", ".join(b for b, _ in BINS) + ")", "",
          "| Task | Variant | Target | Label | Runs | n | mean | median | bins |", "|---|---|---|---|---|---|---|---|---|"]
    for k, s in sorted(res["distributions"].items()):
        t, v, tgt, lab, g = k.split("|")
        L.append(f"| {t} | {v} | {tgt} | {lab} | {g} | {s['n']} | {s['mean']} | {s['median']} | "
                 + " ".join(str(s["bins"][b]) for b, _ in BINS) + " |")
    L += ["", "## m_ctx decomposition", "", "| Task | Variant | Label | Runs | n | m_ctx | node & all data edges | "
          "steps with pure-context edge | pure-context edge mapped |", "|---|---|---|---|---|---|---|---|---|"]
    for k, s in sorted(res["ctx_decomposition"].items()):
        if k.endswith("valid_pure_context_sources"):
            continue
        t, v, lab, g = k.split("|")
        L.append(f"| {t} | {v} | {lab} | {g} | {s['n']} | {s['m_ctx']} | {s['node_and_all_data_edges']} | "
                 f"{s['steps_with_pure_context_edge']} | {s['pure_context_edge_mapped']} |")
    L += ["", "## Cross-kind node mappings of agent steps", ""]
    for k, s in res["cross_kind"].items():
        L.append(f"* {k}: {s['counts']} {s['examples'] or ''}")
    L += ["", "## Node-high / ctx-low steps (m_node ≥ 0.5, m_ctx < 0.5)", ""]
    for v, s in res["node_high_ctx_low"].items():
        L.append(f"* {v}: {s['count']} steps; {s['by_task_label_kind']}")
    L += ["", "## Task 48 lookup: ID from opening turn (O) vs later turn (L)", ""]
    for v, mtx in res["t48_lookup_groups"]["matrix"].items():
        L.append(f"* {v}: " + "; ".join(f"{k}: {x['rate']} ({x['pairs']})" for k, x in mtx.items()))
    L += ["", "## Reference-pool composition", ""]
    for t, p in res["pool"].items():
        L.append(f"* T{t}: write tools in successful runs {p['write_tools_in_successful_runs'] or 'none'}; "
                 f"structurally unmatchable labelled steps: {len(p['structurally_unmatchable_labelled_steps'])}")
    L += ["", "Case studies with NLI scores: see diagnostics.json → case_studies.", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
