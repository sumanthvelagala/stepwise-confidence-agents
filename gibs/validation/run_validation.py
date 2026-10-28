"""
Validation of graph-matching configurations A / B / C on the pre-registered pairs in gibs/validation/pairs.json.

  A  paper-style baseline: paper-literal projection, DeBERTa max-bidirectional, tau 0.7, heuristic MCS,
     no structured fields, no context edges, no event-kind restriction.
  B  current event-context implementation (primary configuration of gibs/examples/task48_pair).
  C  B + structured-field validation (gibs/mcs/structured_fields.py) — OUR adaptation.

Usage:  .venv/bin/python gibs/validation/run_validation.py
Writes: gibs/validation/results/runs.json and gibs/validation/results/tables.md
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.graph.step_graph import build_step_graph, load_simulation  # noqa: E402
from gibs.mcs.consensus import pair_indicators  # noqa: E402
from gibs.mcs.mcs import MCSConfig, _Scorer, find_mcs  # noqa: E402
from gibs.mcs.nli import DebertaEntailment, Similarity  # noqa: E402
from gibs.mcs.structured_fields import StructuredFieldValidator, compare_tool_events  # noqa: E402

PAIRS = REPO / "gibs/validation/pairs.json"
OUT = REPO / "gibs/validation/results"
TAU = 0.7
CONFIGS = {
    "A": {"label": "paper-style baseline", "topology": "paper_literal", "direction": "max_bidirectional",
          "mcs": MCSConfig(require_same_kind=False), "fields": False},
    "B": {"label": "event-context", "topology": "event_context", "direction": "max_bidirectional",
          "mcs": MCSConfig(), "fields": False},
    "C": {"label": "event-context + structured fields", "topology": "event_context",
          "direction": "max_bidirectional", "mcs": MCSConfig(), "fields": True},
}


def short(t, n=80):
    t = (t or "").replace("\n", " ")
    return t if len(t) <= n else t[: n - 1] + "…"


def analyse(model, alt_model, q_steps, r_steps, cfg_name, cfg=None, return_nli_pairs=False):
    """`cfg` (optional) overrides CONFIGS[cfg_name]; it may carry a "matcher" (default find_mcs)."""
    cfg = cfg or CONFIGS[cfg_name]
    matcher = cfg.get("matcher", find_mcs)
    q, r = project(q_steps, cfg["topology"]), project(r_steps, cfg["topology"])
    sim = Similarity(model, direction=cfg["direction"])
    validator = StructuredFieldValidator(q_steps, r_steps) if cfg["fields"] else None
    f0, n0, t0 = model.n_forward, model.n_requested, time.time()
    res = matcher(q, r, sim, cfg["mcs"], field_check=validator)
    seconds = time.time() - t0
    scorer = _Scorer(q, r, sim, cfg["mcs"])
    cand_e1 = {c["e1"] for c in res.candidates}
    rejected_by_e1: dict[str, list] = {}
    for rj in res.rejected:
        rejected_by_e1.setdefault(rj["e1"], []).append(rj)
    q_steps_by_id = {n["id"]: n for n in q_steps["nodes"]}
    r_steps_by_id = {n["id"]: n for n in r_steps["nodes"]}

    def edge_status(e1):
        """Why is this query edge mapped / unmapped?"""
        if e1["id"] in res.edge_map:
            return "mapped", None
        best = max(((sim(e1["text"], e2["text"]), e2) for e2 in r.edges), key=lambda x: x[0])
        if best[0] < cfg["mcs"].tau_e:
            return "no_reference_edge_above_tau_e", {"best_edge_sim": round(best[0], 4), "best_ref_edge": best[1]["id"]}
        passing = [e2 for e2 in r.edges if sim(e1["text"], e2["text"]) >= cfg["mcs"].tau_e]
        if e1["id"] in rejected_by_e1 and e1["id"] not in cand_e1:
            return "rejected_by_structured_field_check", {"reasons": rejected_by_e1[e1["id"]][0]["reasons"],
                                                          "ref_edge": rejected_by_e1[e1["id"]][0]["e2"]}
        if e1["id"] not in cand_e1:
            detail = []
            for e2 in passing[:3]:
                detail.append({"ref_edge": e2["id"], "s_edge": round(sim(e1["text"], e2["text"]), 4),
                               "s_src": round(scorer.node_sim(e1["src"], e2["src"]), 4),
                               "s_tgt": round(scorer.node_sim(e1["dst"], e2["dst"]), 4)})
            return "endpoint_below_tau_v", {"passing_edge_pairs": detail}
        if e1["src"] not in res.node_map and e1["dst"] not in res.node_map:
            return "candidate_but_disconnected_from_mcs", None
        return "candidate_but_mapping_conflict_or_bfs_order", None

    steps = []
    indicators = pair_indicators(q, res)
    for event, ind in indicators.items():
        node = q.nodes[ind["node"]]
        sn = q_steps_by_id[event]
        incoming = q.in_edges(ind["node"])
        statuses = {e["id"]: dict(zip(("status", "detail"), edge_status(e))) for e in incoming}
        best = max(((sim(incoming[0]["text"], e2["text"]), e2) for e2 in r.edges), key=lambda x: x[0])
        field_note = None
        if sn.get("kind") == "tool_call":      # structured comparison against the best NLI partner, for reporting
            partner = r.nodes[best[1]["dst"]]
            if partner["kind"] == "tool_result":
                chk = compare_tool_events(sn, r_steps_by_id[partner["event"]])
                field_note = {"partner": partner["event"], "compatible": chk.compatible, "hard": chk.hard,
                              "ignored": chk.ignored}
        steps.append({
            "event": event, "kind": node["kind"],
            "operation": short(sn["op_text"], 110),
            "node_level": ind["node_level"], "context_step_level": ind["context_step_level"],
            "mapped_to": res.node_map.get(ind["node"]),
            "best_reference_edge": {"id": best[1]["id"], "event": best[1]["event"], "s_edge": round(best[0], 4)},
            "incoming_edges": statuses, "field_check_vs_best_partner": field_note,
        })

    def first_unmatched(key):
        return next((s["event"] for s in steps if not s[key]), None)

    # comparisons that used truncated text and fed a decision (candidate, rejection or mapping)
    decided = [(e1, e2) for e1 in q.edges for e2 in r.edges if sim(e1["text"], e2["text"]) >= cfg["mcs"].tau_e]
    trunc_rows = []
    for e1, e2 in decided:
        for what, a, b in (("edge", e1["text"], e2["text"]),
                           ("target", q.nodes[e1["dst"]]["text"], r.nodes[e2["dst"]]["text"]),
                           ("source", q.nodes[e1["src"]]["text"], r.nodes[e2["src"]]["text"])):
            if a is None or b is None:
                continue
            if (a, b) in model.truncated or (b, a) in model.truncated:
                s_main = sim(a, b)
                alt = max(alt_model.entail_batch([(a, b), (b, a)]))
                fields_cover = (what != "edge" and q.nodes[e1["dst" if what == "target" else "src"]]["kind"] == "tool_result")
                trunc_rows.append({"query_edge": e1["id"], "ref_edge": e2["id"], "comparison": what,
                                   "score_author_truncation": round(s_main, 4),
                                   "score_alternative_truncation": round(alt, 4),
                                   "decision_flips": (s_main >= TAU) != (alt >= TAU),
                                   "covered_by_structured_fields": cfg["fields"] and fields_cover})
    dedup = {(t["query_edge"], t["ref_edge"], t["comparison"]): t for t in trunc_rows}

    excluded = [{"query_edge": e["id"], "event": e["event"], "reason": edge_status(e)[0]}
                for e in q.edges if e["id"] in cand_e1 and e["id"] not in res.edge_map]
    extra = {}
    if res.components:
        extra["components"] = res.components
    if return_nli_pairs:
        extra["_nli_pairs"] = list(sim._memo.keys())
    return {
        **extra,
        "configuration": cfg_name, "label": cfg["label"], "topology": cfg["topology"],
        "mcs_config": asdict(cfg["mcs"]), "structured_fields": cfg["fields"],
        "size": res.size, "seed": res.seed, "n_query_edges": len(q.edges), "n_reference_edges": len(r.edges),
        "n_mapped_edges": len(res.edge_map), "n_candidates": len(res.candidates), "n_rejected": len(res.rejected),
        "node_map": res.node_map, "edge_map": res.edge_map, "edge_scores": res.edge_scores,
        "rejected": res.rejected, "steps": steps,
        "first_unmatched_node_level": first_unmatched("node_level"),
        "first_unmatched_context_step_level": first_unmatched("context_step_level"),
        "unmatched_node_level": [s["event"] for s in steps if not s["node_level"]],
        "unmatched_context_step_level": [s["event"] for s in steps if not s["context_step_level"]],
        "compatible_but_excluded_edges": excluded,
        "truncated_comparisons": list(dedup.values()),
        "cost": {"seconds": round(seconds, 2), "nli_directional_pairs_required": model.n_requested - n0,
                 "nli_forward_passes_uncached": model.n_forward - f0},
    }


def main():
    spec = json.loads(PAIRS.read_text())
    digest = hashlib.sha256(PAIRS.read_bytes()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    t_load = time.time()
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate")
    alt_model = model.with_encoding("pair")          # alternative truncation strategy (longest_first), same weights
    load_s = time.time() - t_load
    runs = []
    for p in spec["pairs"]:
        q_steps = build_step_graph(*load_simulation(str(REPO / p["query"]["file"]), p["query"]["sim"]),
                                   source_file=p["query"]["file"])
        r_steps = build_step_graph(*load_simulation(str(REPO / p["reference"]["file"]), p["reference"]["sim"]),
                                   source_file=p["reference"]["file"])
        assert r_steps["metadata"]["success"] is True, f"{p['id']}: reference must be a correct trajectory"
        assert q_steps["metadata"]["reward"] == p["query"]["reward"], f"{p['id']}: query reward mismatch"
        incorrect = [d["step"] for d in p.get("demonstrably_incorrect", [])]
        for name in CONFIGS:
            out = analyse(model, alt_model, q_steps, r_steps, name)
            fu = out["first_unmatched_node_level"]
            out["expectation_check"] = {
                "expected_first_unmatched": p["expected_first_unmatched"].get(name),
                "first_unmatched_node_level_as_expected": fu == p["expected_first_unmatched"].get(name),
                "demonstrably_incorrect_steps": incorrect,
                "first_unmatched_is_demonstrably_incorrect": bool(incorrect) and fu == incorrect[0],
                "incorrect_steps_unmatched_node_level": {s: s in out["unmatched_node_level"] for s in incorrect},
                "incorrect_steps_unmatched_context_level": {s: s in out["unmatched_context_step_level"] for s in incorrect},
            }
            out.update({"pair": p["id"], "task": p["task"], "category": p["category"],
                        "query": f"{p['query']['sim']} (reward {p['query']['reward']})",
                        "reference": f"{p['reference']['sim']} (reward {p['reference']['reward']})",
                        "n_agent_steps": len(out["steps"])})
            runs.append(out)
            print(f"{p['id']} T{p['task']} {name}: mapped {out['n_mapped_edges']}/{out['n_query_edges']} edges, "
                  f"unmatched(node)={out['unmatched_node_level']} unmatched(ctx)={out['unmatched_context_step_level']} "
                  f"first={fu} rejected={out['n_rejected']} trunc={len(out['truncated_comparisons'])} "
                  f"{out['cost']}", flush=True)
    report = {"pairs_file_sha256": digest, "model": model.describe(), "model_load_seconds": round(load_s, 1),
              "tau": TAU, "configs": {k: {**v, "mcs": asdict(v["mcs"])} for k, v in CONFIGS.items()}, "runs": runs}
    (OUT / "runs.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (OUT / "tables.md").write_text(tables(report, spec))
    print(f"\nwrote {OUT / 'runs.json'} and {OUT / 'tables.md'}")


def tables(report, spec) -> str:
    runs = report["runs"]
    by = {(r["pair"], r["configuration"]): r for r in runs}
    L = ["# Generated tables (run_validation.py)", "",
         f"pairs.json sha256 `{report['pairs_file_sha256']}`; model `{report['model']['model']}` @ "
         f"`{report['model']['revision']}` on {report['model']['device']}", "",
         "## Per pair and configuration", "",
         "| Pair | Task | Cfg | Mapped edges | Unmatched agent steps (node-level) | Unmatched (context step-level) "
         "| First unmatched (node) | Expected | Demonstrably incorrect step(s) unmatched (node/ctx) | Field rejections "
         "| Truncated comparisons (flips) | NLI pairs required / uncached | Seconds |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in spec["pairs"]:
        for c in CONFIGS:
            r = by[(p["id"], c)]
            ec = r["expectation_check"]
            inc = ", ".join(f"{s}: {int(ec['incorrect_steps_unmatched_node_level'][s])}/"
                            f"{int(ec['incorrect_steps_unmatched_context_level'][s])}"
                            for s in ec["demonstrably_incorrect_steps"]) or "n/a"
            flips = sum(t["decision_flips"] for t in r["truncated_comparisons"])
            L.append(f"| {p['id']} | {p['task']} | {c} | {r['n_mapped_edges']}/{r['n_query_edges']} | "
                     f"{', '.join(r['unmatched_node_level']) or '—'} | {', '.join(r['unmatched_context_step_level']) or '—'} | "
                     f"{r['first_unmatched_node_level'] or '—'} | "
                     f"{'no prediction' if ec['expected_first_unmatched'] is None else ec['expected_first_unmatched'] + (' ✓' if ec['first_unmatched_node_level_as_expected'] else ' ✗')}"
                     f" | {inc} | {r['n_rejected']} | "
                     f"{len(r['truncated_comparisons'])} ({flips}) | {r['cost']['nli_directional_pairs_required']} / "
                     f"{r['cost']['nli_forward_passes_uncached']} | {r['cost']['seconds']} |")
    L += ["", "## Per-step detail", ""]
    for p in spec["pairs"]:
        L.append(f"### {p['id']} (task {p['task']}): query {p['query']['sim']} vs reference {p['reference']['sim']}")
        L.append("")
        L.append("| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for k, s in enumerate(by[(p["id"], "C")]["steps"]):
            cells = []
            for c in CONFIGS:
                st = by[(p["id"], c)]["steps"][k]
                cells.append(f"{int(st['node_level'])}/{int(st['context_step_level'])}")
            why = sorted({v["status"] for v in s["incoming_edges"].values() if v["status"] != "mapped"})
            fc = s["field_check_vs_best_partner"]
            fc_txt = "—" if fc is None else ("compatible" if fc["compatible"] else "HARD: " + "; ".join(fc["hard"])[:160])
            L.append(f"| {s['event']} | {s['kind']} | {s['operation'].replace('|', '/')} | " + " | ".join(cells) +
                     f" | {s['best_reference_edge']['id']} ({s['best_reference_edge']['s_edge']:.3f}) | "
                     f"{', '.join(why) or 'mapped'} | {fc_txt.replace('|', '/')} |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    if sys.argv[1:] == ["--tables-only"]:   # regenerate tables.md from an existing runs.json (no model)
        (OUT / "tables.md").write_text(tables(json.loads((OUT / "runs.json").read_text()), json.loads(PAIRS.read_text())))
    else:
        main()
