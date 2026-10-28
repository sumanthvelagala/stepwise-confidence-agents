"""
Two-stage constrained matching, variant C5  [OURS — not the paper's algorithm]. Plan: gibs/validation/c5_plan.md.

Stage 1 (frozen): the tool part of a stored C4 result — every mapped edge that ends at a tool-call node, plus its
endpoints. It is taken as given and never changed.
Stage 2: agent messages are matched through their context edge (from the immediately preceding event), on the
`project_c5` graph, consistent with stage 1:
  * only candidates whose query edge ends at an agent message are used (tool and user-turn edges are never added);
  * a candidate whose query source is a tool node is kept only if stage 1 maps that tool node to exactly the
    candidate's reference source (so stage 2 never maps a new tool node and a message after an unmatched tool call
    cannot be context-supported);
  * growth uses the unchanged multi-component rule (`multi_component._grow`), one-to-one with the frozen maps.
Candidates come from the unchanged `find_mcs` candidate stage (NLI thresholds, source check, kind restriction,
structured-field rejection).

Optional stage 3, variant C6 [OURS; plan: gibs/validation/c6_plan.md], `outcome_route=True`: after stage 2, message
candidates whose query predecessor is a tool call UNMATCHED in stage 1 may be added iff the reference predecessor is the
same tool with compatible call fields (field check on the source pair) and an exactly equal normalized outcome
(`outcome_key`). Outcome agreement does not establish that the tool action was correct. Outcome-aligned tool nodes are
removed from the final node map, so tool scores are unchanged. With the default `outcome_route=False` the behaviour is
exactly C5 (verified by recomputing results_c5/).
"""
from __future__ import annotations

import json

from gibs.graph.event_projection import ROOT, ProjectedGraph, project
from gibs.mcs.mcs import Candidate, MCSConfig, MCSResult, _Scorer, find_mcs
from gibs.mcs.multi_component import _grow
from gibs.mcs.nli import Similarity


def project_c5(step_graph: dict) -> ProjectedGraph:
    """C4 (paper-literal) edges for tool calls and user turns; for every agent message except the first event, its
    C3 (event-context) context edge instead of a ROOT edge."""
    g = project(step_graph, "paper_literal")
    ctx = project(step_graph, "event_context")
    g.topology = "c5_hybrid"
    first = next(iter(n["id"] for n in step_graph["nodes"]))
    edges = []
    for e in g.edges:
        if g.nodes[e["dst"]]["kind"] == "agent_message" and e["dst"] != f"N:{first}":
            continue                                    # replaced below by the context edge
        edges.append(e)
    for e in ctx.edges:
        if ctx.nodes[e["dst"]]["kind"] == "agent_message" and e["dst"] != f"N:{first}":
            assert e["roles"] == ["context"], e        # messages never have data edges
            edges.append(dict(e))
    order = {nid: k for k, nid in enumerate(g.nodes)}
    edges.sort(key=lambda e: (order[e["dst"]], order[e["src"]]))
    g.edges = edges
    return g


def freeze_tool_part(g1: ProjectedGraph, node_map: dict, edge_map: dict) -> tuple[dict, dict]:
    """Stage 1: mapped edges ending at a tool node, and their endpoints, from a stored C4 result."""
    by_id = {e["id"]: e for e in g1.edges}
    femap = {e1: e2 for e1, e2 in edge_map.items() if g1.nodes[by_id[e1]["dst"]]["kind"] == "tool_result"}
    fvmap = {}
    for e1 in femap:
        for n in (by_id[e1]["src"], by_id[e1]["dst"]):
            fvmap[n] = node_map[n]
    tools_c4 = {n for n in node_map if n in g1.nodes and g1.nodes[n]["kind"] == "tool_result"}
    tools_frozen = {n for n in fvmap if g1.nodes[n]["kind"] == "tool_result"}
    if tools_c4 != tools_frozen:
        raise ValueError(f"stage 1 does not cover all C4 tool nodes: {sorted(tools_c4 ^ tools_frozen)}")
    return fvmap, femap


def outcome_key(step: dict) -> tuple[bool, str]:
    """C6 outcome normalization (c6_plan.md §2): exact equality of the full tool result up to whitespace and int/float
    representation. Error results keep their text (never error-flag-only)."""
    obs = step["observation"]

    def norm(v):
        if isinstance(v, dict):
            return {k: norm(x) for k, x in v.items()}
        if isinstance(v, list):
            return [norm(x) for x in v]
        if isinstance(v, str):
            return " ".join(v.split())
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, (int, float)):
            return float(v)
        return v

    body = obs.get("content_parsed")
    if body is None:
        body = obs.get("content_raw") or ""
    return bool(obs["error"]), json.dumps(norm(body), sort_keys=True)


def _grow_components(g1, e1_by_id, e2_by_id, cands, pool, vmap, emap, cfg, min_edges, origin):
    """The unchanged multi-component loop (top-K consistent seeds, `_grow`, largest gain wins)."""
    escore, components = {}, []
    while True:
        used_e2, taken = set(emap.values()), set(vmap.values())

        def eligible(c: Candidate) -> bool:
            if c.e1 in emap or c.e2 in used_e2:
                return False
            x1, y1 = e1_by_id[c.e1]["src"], e1_by_id[c.e1]["dst"]
            x2, y2 = e2_by_id[c.e2]["src"], e2_by_id[c.e2]["dst"]
            ok_x = vmap[x1] == x2 if x1 in vmap else x2 not in taken
            ok_y = vmap[y1] == y2 if y1 in vmap else y2 not in taken
            return ok_x and ok_y

        seeds = [c for c in cands if eligible(c)][: cfg.top_k]
        if not seeds:
            break
        best = None
        for seed in seeds:
            nv, ne, ns = _grow(g1, e1_by_id, e2_by_id, pool, seed, vmap, emap)
            gain = (len(ne) - len(emap)) + (len(nv) - len(vmap))
            if best is None or gain > best[0]:
                best = (gain, nv, ne, ns, seed)
        gain, nv, ne, ns, seed = best
        if len(ne) - len(emap) < min_edges:
            break
        components.append({"index": len(components), "seed": (seed.e1, seed.e2),
                           "edges": sorted(set(ne) - set(emap)), "nodes": sorted(set(nv) - set(vmap)),
                           "origin": origin})
        vmap, emap = nv, ne
        escore.update(ns)
    return vmap, emap, escore, components


def _pool(cands, cfg):
    pool: dict[str, list[Candidate]] = {}
    for c in (cands if cfg.expansion_pool == "all_candidates" else cands[: cfg.top_k]):
        pool.setdefault(c.e1, []).append(c)
    return pool


def extend_messages(g1: ProjectedGraph, g2: ProjectedGraph, sim: Similarity, frozen_v: dict, frozen_e: dict,
                    cfg: MCSConfig = MCSConfig(), field_check=None, min_edges: int = 1,
                    outcome_route: bool = False, query_steps: dict | None = None,
                    reference_steps: dict | None = None) -> MCSResult:
    """C5 (default) or, with `outcome_route=True`, C6 (c6_plan.md): after stage 2, a stage 3 may add message context
    edges whose query predecessor is a tool call unmatched in stage 1, iff the reference predecessor is the same tool
    with compatible call fields (already enforced by `field_check` on the source pair) and an exactly equal outcome
    (`outcome_key`). Outcome-aligned tool nodes are removed from the final node map (no new tool matches)."""
    base = find_mcs(g1, g2, sim, cfg, field_check=field_check)        # used only for its candidate list
    e1_by_id = {e["id"]: e for e in g1.edges}
    e2_by_id = {e["id"]: e for e in g2.edges}
    stats = {"candidates_message_edges": 0, "dropped_tool_unmatched": 0, "dropped_tool_conflict": 0}
    cands, unmatched = [], []
    for c in base.candidates:                                          # already score-sorted
        e1 = e1_by_id[c["e1"]]
        if g1.nodes[e1["dst"]]["kind"] != "agent_message":
            continue
        stats["candidates_message_edges"] += 1
        src1, src2 = e1["src"], e2_by_id[c["e2"]]["src"]
        cand = Candidate(c["e1"], c["e2"], c["s_edge"], c["s_src"], c["s_tgt"])
        if g1.nodes[src1]["kind"] == "tool_result":
            if src1 not in frozen_v:
                stats["dropped_tool_unmatched"] += 1
                unmatched.append(cand)
                continue
            if frozen_v[src1] != src2:
                stats["dropped_tool_conflict"] += 1
                continue
        cands.append(cand)

    vmap, emap, escore, components = _grow_components(
        g1, e1_by_id, e2_by_id, cands, _pool(cands, cfg), dict(frozen_v), dict(frozen_e), cfg, min_edges,
        "stage 2 message component")

    # invariants (also unit-tested): stage 1 untouched, no new tool node, no tool edge added
    assert all(vmap[k] == v for k, v in frozen_v.items()) and all(emap[k] == v for k, v in frozen_e.items())
    assert {n for n in vmap if g1.nodes[n]["kind"] == "tool_result"} == \
           {n for n in frozen_v if g1.nodes[n]["kind"] == "tool_result"}
    assert all(g1.nodes[e1_by_id[e]["dst"]]["kind"] == "agent_message" for e in set(emap) - set(frozen_e))

    outcome_edges, alignments = [], {}
    if outcome_route:
        if query_steps is None or reference_steps is None:
            raise ValueError("outcome_route needs query_steps and reference_steps")
        qs = {n["id"]: n for n in query_steps["nodes"]}
        rs = {n["id"]: n for n in reference_steps["nodes"]}
        stats.update({"outcome_candidates": len(unmatched), "outcome_rejected_outcome_differs": 0})
        ocands = []
        for c in unmatched:
            q_tool = qs[g1.nodes[e1_by_id[c.e1]["src"]]["event"]]
            r_tool = rs[g2.nodes[e2_by_id[c.e2]["src"]]["event"]]
            if outcome_key(q_tool) != outcome_key(r_tool):
                stats["outcome_rejected_outcome_differs"] += 1
                continue
            ocands.append(c)
        stage2_v, stage2_e = dict(vmap), dict(emap)
        vmap, emap, escore3, comps3 = _grow_components(
            g1, e1_by_id, e2_by_id, ocands, _pool(ocands, cfg), vmap, emap, cfg, min_edges,
            "stage 3 outcome-route component")
        escore.update(escore3)
        components += comps3
        assert all(vmap[k] == v for k, v in stage2_v.items()) and all(emap[k] == v for k, v in stage2_e.items())
        outcome_edges = sorted(set(emap) - set(stage2_e))
        assert all(g1.nodes[e1_by_id[e]["dst"]]["kind"] == "agent_message" for e in outcome_edges)
        # outcome-aligned tool nodes are not tool matches: remove them from the node map, record them separately
        alignments = {n: m for n, m in vmap.items() if g1.nodes[n]["kind"] == "tool_result" and n not in frozen_v}
        vmap = {n: m for n, m in vmap.items() if n not in alignments}
        stats["outcome_route_edges"] = len(outcome_edges)
        assert {n for n in vmap if g1.nodes[n]["kind"] == "tool_result"} == \
               {n for n in frozen_v if g1.nodes[n]["kind"] == "tool_result"}

    sc = _Scorer(g1, g2, sim, cfg)
    res = MCSResult(query_id=g1.graph_id, reference_id=g2.graph_id, config=base.config, direction=sim.direction)
    res.node_map, res.edge_map = vmap, emap
    res.size = len(vmap) + len(emap)
    res.rejected = base.rejected
    res.node_scores = {n1: sc.node_sim(n1, n2) for n1, n2 in vmap.items()}
    res.edge_scores = {e: {"to": c.e2, "s_edge": c.s_edge, "s_src": c.s_src, "s_tgt": c.s_tgt}
                       for e, c in escore.items()}
    res.components = [{"index": -1, "origin": "stage 1 (frozen C4 tool part)", "edges": sorted(frozen_e),
                       "nodes": sorted(frozen_v)}] + components
    res.stage2_stats = stats
    res.outcome_route_edges = outcome_edges
    res.outcome_alignments = alignments
    return res


__all__ = ["project_c5", "freeze_tool_part", "extend_messages", "outcome_key", "ROOT"]
