"""
GIBS scoring — graph-aware leave-one-out scoring.

Two signals combined:
  Step-level (DataDep):
    - tool_match:  does this tool call appear in the reference graph?
    - dep_match:   does the reference also have a DataDep edge for this tool call?
                   catches hardcoded args / skipped lookups — what NIBS misses
    step_score = 0.5 * tool_match + 0.5 * dep_match

  Run-level (WL kernel):
    - wl_score: WL kernel similarity between full graphs (catches wrong order/structure)

  Final run_score = beta * mean(step_scores) + (1-beta) * mean(wl_vs_refs)
  Default beta = 0.5
"""
from __future__ import annotations

import numpy as np

from gibs.graph.builder import EDGE_DATA_DEP, NODE_TOOL_CALL
from gibs.similarity.wl_kernel import wl_similarity


def _tools_in_graph(g) -> set[str]:
    """Set of tool names present as ToolCall nodes in this graph."""
    return {n["text"].split()[0] for n in g.nodes if n["type"] == "tool_call"}


def _tools_with_dep(g) -> set[str]:
    """Set of tool names whose ToolCall node has at least one incoming DataDep edge."""
    call_ids_with_dep = {dst for src, dst, etype in g.edges if etype == EDGE_DATA_DEP}
    result = set()
    for n in g.nodes:
        if n["type"] == "tool_call" and n["id"] in call_ids_with_dep:
            result.add(n["text"].split()[0])
    return result


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(max(0.0, np.dot(a, b) / (na * nb)))


def _best_cosine_vs_ref(node_emb: np.ndarray, ref_g) -> float:
    """Best cosine similarity between node_emb and any ToolCall node in ref_g."""
    if ref_g.embeddings is None:
        return 0.0
    best = 0.0
    for n in ref_g.nodes:
        if n["type"] == NODE_TOOL_CALL:
            best = max(best, _cosine(node_emb, ref_g.embeddings[n["id"]]))
    return best


def step_score_vs_ref(step_tool: str, step_emb, step_has_dep: bool, ref_g, alpha: float = 0.5) -> float:
    """
    Score one step against one reference graph.
      semantic   = MiniLM cosine (if embeddings available) else binary tool_match
      dep_match  = 1.0 if ref's DataDep pattern matches, skipped if step has no dep
    final = alpha * semantic + (1-alpha) * dep_match
    """
    if step_emb is not None:
        semantic = _best_cosine_vs_ref(step_emb, ref_g)
    else:
        ref_tools = _tools_in_graph(ref_g)
        semantic = 1.0 if step_tool in ref_tools else 0.0

    if not step_has_dep:
        dep_match = 1.0
    else:
        ref_dep_tools = _tools_with_dep(ref_g)
        dep_match = 1.0 if step_tool in ref_dep_tools else 0.0

    return alpha * semantic + (1 - alpha) * dep_match


def score_graph(query_g, ref_graphs: list, alpha: float = 0.5, beta: float = 0.5) -> dict:
    """
    Score query_g against ref_graphs.
      Step-level: alpha * MiniLM_cosine + (1-alpha) * dep_match
      Run-level:  beta  * mean(step_scores) + (1-beta) * WL_kernel
    Returns {"step_scores": [...], "wl_score": float, "run_score": float}
    """
    dep_tools = _tools_with_dep(query_g)
    step_scores = []

    for n in query_g.nodes:
        if n["type"] != NODE_TOOL_CALL:
            continue
        tool = n["text"].split()[0]
        step_idx = n["step_idx"]
        has_dep = tool in dep_tools
        node_emb = query_g.embeddings[n["id"]] if query_g.embeddings is not None else None

        if not ref_graphs:
            score = 0.0
        else:
            per_ref = [step_score_vs_ref(tool, node_emb, has_dep, ref, alpha) for ref in ref_graphs]
            score = sum(per_ref) / len(per_ref)

        step_scores.append({"idx": step_idx, "tool": tool, "score": score})

    # WL kernel: run-level structural similarity vs each reference
    if ref_graphs:
        wl_scores = [wl_similarity(query_g, ref) for ref in ref_graphs]
        wl_score = sum(wl_scores) / len(wl_scores)
    else:
        wl_score = 0.0

    step_mean = sum(s["score"] for s in step_scores) / len(step_scores) if step_scores else 0.0
    run_score = beta * step_mean + (1 - beta) * wl_score

    return {"step_scores": step_scores, "wl_score": wl_score, "run_score": run_score}


def score_task(graphs: list, k_min: int = 3, alpha: float = 0.5, beta: float = 0.5) -> dict:
    """
    Leave-one-out GIBS scoring for all graphs of one task.
    Skips if fewer than k_min passing graphs exist.
    """
    passing = [g for g in graphs if g.success]

    if len(passing) < k_min:
        return {
            "skipped": True,
            "reason": f"only {len(passing)} passing run(s), need at least {k_min}",
            "success_count": len(passing),
        }

    results = []
    for g in graphs:
        refs = [r for r in passing if r is not g]
        scored = score_graph(g, refs, alpha=alpha, beta=beta)
        results.append({
            "task_id": g.task_id,
            "trial": g.trial,
            "success": g.success,
            "step_scores": scored["step_scores"],
            "wl_score": scored["wl_score"],
            "run_score": scored["run_score"],
        })

    return {"skipped": False, "success_count": len(passing), "results": results}
