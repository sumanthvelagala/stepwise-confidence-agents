"""
Graph similarity for GIBS using MiniLM node embeddings + WL kernel.

Two components:
  1. Node embedding cosine similarity (semantic, per-step)
  2. WL kernel (structural, run-level)

Hybrid: run_score = alpha * mean(step_cosine_scores) + (1-alpha) * wl_score

Embedding is handled separately via batch_embed_graphs() to avoid
re-loading the MiniLM model for each graph pair.
"""
from __future__ import annotations

import numpy as np

from .wl_kernel import wl_similarity

_model = None


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _model = SentenceTransformer(model_name)
    return _model


def batch_embed_graphs(graphs: list, model_name: str = "all-MiniLM-L6-v2") -> None:
    """
    Embed all nodes from all graphs in a single batched call.
    Sets graph.embeddings (np.ndarray of shape [n_nodes, dim]) in place.
    Graphs with no nodes get embeddings=None.
    """
    model = _get_model(model_name)

    all_texts: list[str] = []
    graph_slices: list[tuple[int, int]] = []  # (start, end) index into all_texts

    for g in graphs:
        start = len(all_texts)
        all_texts.extend(n["text"] for n in g.nodes)
        graph_slices.append((start, len(all_texts)))

    if not all_texts:
        for g in graphs:
            g.embeddings = None
        return

    all_embs = model.encode(all_texts, convert_to_numpy=True, show_progress_bar=False)

    for g, (start, end) in zip(graphs, graph_slices):
        if start == end:
            g.embeddings = None
        else:
            g.embeddings = all_embs[start:end]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(max(0.0, np.dot(a, b) / (na * nb)))


def _representative_node_id(g, step_idx: int) -> int | None:
    """ToolCall node id for the step, falling back to AgentMsg. ToolResult is skipped."""
    sn = g.step_nodes.get(step_idx, {})
    return sn.get("call") or sn.get("msg")


def _representative_emb(g, step_idx: int) -> np.ndarray | None:
    nid = _representative_node_id(g, step_idx)
    if nid is None or g.embeddings is None:
        return None
    return g.embeddings[nid]


def step_cosine_vs_ref(query_g, ref_g, step_idx: int) -> float:
    """
    Best cosine similarity between the query step's representative node
    and any representative node in the reference graph (best-match, like NIBS).
    """
    q_emb = _representative_emb(query_g, step_idx)
    if q_emb is None:
        return 0.0

    best = 0.0
    for s_idx in ref_g.step_nodes:
        r_emb = _representative_emb(ref_g, s_idx)
        if r_emb is not None:
            best = max(best, _cosine(q_emb, r_emb))
    return best
