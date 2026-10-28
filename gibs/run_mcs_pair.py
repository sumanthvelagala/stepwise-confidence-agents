"""
MCS between one query trajectory and one correct reference trajectory, under the primary configuration and the
approved ablations. Writes step graphs, projections, MCS results and a Mermaid view. No full-task consensus.

Usage:  .venv/bin/python gibs/run_mcs_pair.py [--query 7f5cbcd7] [--reference c890f90b] [--control]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.graph.step_graph import build_step_graph, load_simulation  # noqa: E402
from gibs.mcs.consensus import pair_indicators  # noqa: E402
from gibs.mcs.mcs import MCSConfig, find_mcs  # noqa: E402
from gibs.mcs.nli import DebertaEntailment, Similarity  # noqa: E402

RESULTS = "results/pilot/tasks_25_40_48/results.json"
CONFIGS = {   # name: (direction, topology, MCSConfig)
    "primary":                     ("max_bidirectional", "event_context", MCSConfig()),
    "ablation_one_way":            ("one_way", "event_context", MCSConfig()),
    "ablation_author_pool_top_k":  ("max_bidirectional", "event_context", MCSConfig(expansion_pool="top_k")),
    "ablation_author_source_rule": ("max_bidirectional", "event_context", MCSConfig(check_source_nodes=False)),
    "ablation_paper_literal_topology": ("max_bidirectional", "paper_literal", MCSConfig()),
}


def short(text: str | None, n: int = 70) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def run_pair(model, q_steps, r_steps, name, direction, topology, cfg):
    q, r = project(q_steps, topology), project(r_steps, topology)
    sim = Similarity(model, direction=direction)
    res = find_mcs(q, r, sim, cfg)
    trunc = model.truncated

    def was_truncated(a, b):
        return (a, b) in trunc or (b, a) in trunc

    edges1 = {e["id"]: e for e in q.edges}
    edges2 = {e["id"]: e for e in r.edges}
    mapped_edges = []
    for e1, e2 in res.edge_map.items():
        s = res.edge_scores[e1]
        a, b = edges1[e1], edges2[e2]
        mapped_edges.append({"query_edge": e1, "reference_edge": e2, "query_event": a["event"],
                             "roles": a["roles"], "operation": short(a["text"], 90),
                             "s_edge": round(s["s_edge"], 4), "s_src": round(s["s_src"], 4),
                             "s_tgt": round(s["s_tgt"], 4),
                             "truncated_text_used": was_truncated(a["text"], b["text"]) or any(
                                 was_truncated(q.nodes[x]["text"] or "", r.nodes[y]["text"] or "")
                                 for x, y in ((a["src"], b["src"]), (a["dst"], b["dst"])))})
    steps = []
    for event, ind in pair_indicators(q, res).items():
        node = q.nodes[ind["node"]]
        steps.append({"event": event, "kind": node["kind"], "text": short(node["text"] if node["kind"] != "tool_result"
                                                                          else next(e["text"] for e in q.in_edges(ind["node"])), 90),
                      "node_level": ind["node_level"], "context_step_level": ind["context_step_level"],
                      "incoming_edges": ind["incoming_edges"], "mapped_to": res.node_map.get(ind["node"])})
    out = {"configuration": name, "direction": direction, "topology": topology, "mcs_config": asdict(cfg),
           "query": q.graph_id, "reference": r.graph_id, "size": res.size, "seed": res.seed,
           "n_candidates": len(res.candidates), "n_seeds": len(res.seeds),
           "n_query_edges": len(q.edges), "n_reference_edges": len(r.edges),
           "node_map": res.node_map, "mapped_edges": mapped_edges, "agent_steps": steps,
           "candidates": res.candidates}
    return out, q


def mermaid(q, res_out) -> str:
    mapped_nodes = res_out["node_map"]
    mapped_edges = {m["query_edge"] for m in res_out["mapped_edges"]}
    lines = ["%% Query graph; green = mapped into the reference by MCS, red = unmapped. Edge labels: operation roles.",
             "flowchart TD"]
    for nid, n in q.nodes.items():
        if n["kind"] == "root":
            label = "ROOT"
        elif n["kind"] == "tool_result":   # show the operation too: observations of different calls can look alike
            label = (f"{nid} · tool_result<br/>CALL {short(q.in_edges(nid)[0]['text'][5:], 55)}"
                     f"<br/>OBS {short(n['text'][13:], 45)}")
        else:
            label = f"{nid} · {n['kind']}<br/>{short(n['text'], 60)}"
        label = label.replace('"', "#quot;").replace("#", "#35;").replace("#35;quot;", "#quot;")
        if nid in mapped_nodes:
            label += f"<br/>↦ {mapped_nodes[nid]}"
        safe = nid.replace(":", "_")
        lines.append(f'    {safe}["{label}"]')
    for k, e in enumerate(q.edges):
        arrow = "-->" if "context" in e["roles"] or "root" in e["roles"] else "-.->"
        lines.append(f'    {e["src"].replace(":", "_")} {arrow}|{"+".join(e["roles"])}| {e["dst"].replace(":", "_")}')
    lines.append("    classDef mapped fill:#e6f4ea,stroke:#137333,color:#111;")
    lines.append("    classDef unmapped fill:#fce8e6,stroke:#c5221f,color:#111;")
    lines.append("    class " + ",".join(n.replace(":", "_") for n in q.nodes if n in mapped_nodes) + " mapped;")
    um = [n.replace(":", "_") for n in q.nodes if n not in mapped_nodes]
    if um:
        lines.append("    class " + ",".join(um) + " unmapped;")
    idx = [str(k) for k, e in enumerate(q.edges) if e["id"] in mapped_edges]
    if idx:
        lines.append(f"    linkStyle {','.join(idx)} stroke:#137333,stroke-width:3px;")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="7f5cbcd7")
    ap.add_argument("--reference", default="c890f90b")
    ap.add_argument("--control", action="store_true", help="also run reference vs another passing run (primary only)")
    ap.add_argument("--out-dir", default=str(REPO / "gibs/examples/task48_pair"))
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    q_steps = build_step_graph(*load_simulation(str(REPO / RESULTS), args.query), source_file=RESULTS)
    r_steps = build_step_graph(*load_simulation(str(REPO / RESULTS), args.reference), source_file=RESULTS)
    if r_steps["metadata"]["success"] is not True:
        raise SystemExit("the reference must be a correct (reward 1.0) trajectory")
    for g in (q_steps, r_steps):
        (out_dir / f"step_graph_{g['graph_id']}.json").write_text(json.dumps(g, indent=2, ensure_ascii=False) + "\n")
        for topo in ("event_context", "paper_literal"):
            (out_dir / f"projection_{topo}_{g['graph_id']}.json").write_text(
                json.dumps(project(g, topo).to_dict(), indent=2, ensure_ascii=False) + "\n")

    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate")
    runs = {}
    for name, (direction, topology, cfg) in CONFIGS.items():
        out, q = run_pair(model, q_steps, r_steps, name, direction, topology, cfg)
        runs[name] = out
        if name == "primary":
            (out_dir / "mcs_failure_vs_success_primary.mmd").write_text(mermaid(q, out))

    if args.control:
        data = json.load(open(REPO / RESULTS))
        other = next(s["id"][:8] for s in data["simulations"] if s["task_id"] == r_steps["metadata"]["task_id"]
                     and (s.get("reward_info") or {}).get("reward") == 1.0 and not s["id"].startswith(args.reference))
        c_steps = build_step_graph(*load_simulation(str(REPO / RESULTS), other), source_file=RESULTS)
        (out_dir / f"step_graph_{c_steps['graph_id']}.json").write_text(json.dumps(c_steps, indent=2, ensure_ascii=False) + "\n")
        for name in ("primary", "ablation_paper_literal_topology"):
            out, q = run_pair(model, r_steps, c_steps, f"control_success_vs_success_{name}", *CONFIGS[name])
            runs[f"control_success_vs_success_{name}"] = out
            if name == "primary":
                (out_dir / "mcs_success_vs_success_control.mmd").write_text(mermaid(q, out))

    report = {"model": model.describe(), "n_truncated_text_pairs_scored": len(model.truncated), "runs": runs}
    (out_dir / "mcs_task48_pair.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    for name, out in runs.items():
        print(f"\n=== {name}: {out['query']} vs {out['reference']} | size={out['size']} seed={out['seed']} "
              f"candidates={out['n_candidates']} mapped_edges={len(out['mapped_edges'])}/{out['n_query_edges']}")
        for s in out["agent_steps"]:
            print(f"   {s['event']:<4} {s['kind']:<13} node={int(s['node_level'])} ctx={int(s['context_step_level'])} "
                  f"-> {s['mapped_to'] or '-':<7} | {s['text']}")
        for m in out["mapped_edges"]:
            print(f"      edge {m['query_edge']:<16} -> {m['reference_edge']:<16} e={m['s_edge']:.3f} "
                  f"src={m['s_src']:.3f} tgt={m['s_tgt']:.3f}{' TRUNCATED' if m['truncated_text_used'] else ''}")


if __name__ == "__main__":
    main()
