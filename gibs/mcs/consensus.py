"""
Consensus targets for AgentStep events from MCS results against correct reference graphs.

Two targets are reported separately (R6). Neither is ground-truth step correctness.

  m_node  [PDF C.2]  m_ij = (1/|S_correct|) * sum_k 1[v_ij in MCS(G_i, G_k)]
                     v_ij is the step's result node. It counts as "in the MCS" whenever it is mapped, which can
                     happen through ANY of its incoming edges, or as the source of a later matched edge.

  m_ctx   [OURS]     context-aware step-level target:
                     m_ij = (1/|S_correct|) * sum_k 1[every incoming edge of v_ij is in the MCS edge map]
                     A step is supported only if its operation matched under all of its inputs, including the
                     context edge from the preceding event. If a user instruction (or observation) that the step
                     responds to contradicts the reference, the context edge cannot match, so the step is not
                     supported even when an identical call with an identical result appears in the reference.

The caller is responsible for choosing references: correct trajectories of the same task only (PDF App. B),
excluding the query itself when the query is correct (leave-one-out, our choice; the PDF is silent).
"""
from __future__ import annotations

from gibs.graph.event_projection import ProjectedGraph
from gibs.mcs.mcs import MCSResult


def pair_indicators(query: ProjectedGraph, result: MCSResult) -> dict[str, dict]:
    """Per scorable event of `query`: whether it is supported by this one reference, under both definitions."""
    out = {}
    for nid, node in query.nodes.items():
        if not node["scorable"]:
            continue
        incoming = [e["id"] for e in query.in_edges(nid)]
        out[node["event"]] = {
            "node": nid,
            "node_level": nid in result.node_map,
            "context_step_level": bool(incoming) and all(e in result.edge_map for e in incoming),
            "incoming_edges": {e: result.edge_map.get(e) for e in incoming},
        }
    return out


def consensus_masks(query: ProjectedGraph, results: list[MCSResult]) -> dict[str, dict]:
    if any(r.query_id != query.graph_id for r in results):
        raise ValueError("all MCS results must use `query` as G1")
    if not results:
        raise ValueError("at least one correct reference is required")
    per_ref = [pair_indicators(query, r) for r in results]
    masks = {}
    for event in per_ref[0]:
        masks[event] = {
            "m_node": sum(p[event]["node_level"] for p in per_ref) / len(per_ref),
            "m_ctx": sum(p[event]["context_step_level"] for p in per_ref) / len(per_ref),
            "n_references": len(per_ref),
        }
    return masks
