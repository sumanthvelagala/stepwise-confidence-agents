from __future__ import annotations

from typing import Callable


def tool_sim(step_a: dict, step_b: dict) -> float:
    """
    0.0 if tool names differ.
    1.0 if both steps have no tool (plain text turns).
    Otherwise: fraction of arg keys whose normalized values match (union of keys).
    """
    tool_a = step_a.get("tool")
    tool_b = step_b.get("tool")

    if tool_a != tool_b:
        return 0.0
    if tool_a is None:
        return 1.0

    args_a = step_a.get("args") or {}
    args_b = step_b.get("args") or {}
    all_keys = set(args_a) | set(args_b)
    if not all_keys:
        return 1.0

    matches = sum(1 for k in all_keys if args_a.get(k) is not None and args_a.get(k) == args_b.get(k))
    return matches / len(all_keys)


def text_sim(text_a: str | None, text_b: str | None, backend: Callable | str = "cosine") -> float:
    """
    Similarity between two thought strings.
    backend: callable (str,str)->float | 'cosine' (sentence-BERT) | 'nli' (DeBERTa entailment).
    Not used in pilot — tool_sim alone is sufficient for structured tool calls.
    """
    if not text_a or not text_b:
        return 0.0
    if callable(backend):
        return float(backend(text_a, text_b))
    if backend == "cosine":
        from sentence_transformers import SentenceTransformer, util  # type: ignore
        model = SentenceTransformer("all-MiniLM-L6-v2")
        emb_a, emb_b = model.encode([text_a, text_b], convert_to_tensor=True)
        return float(max(0.0, min(1.0, util.cos_sim(emb_a, emb_b).item())))
    if backend == "nli":
        from transformers import pipeline  # type: ignore
        clf = pipeline("text-classification", model="cross-encoder/nli-deberta-v3-small")
        result = clf(f"{text_a} [SEP] {text_b}", truncation=True)[0]
        return result["score"] if result["label"] == "ENTAILMENT" else 0.0
    raise ValueError(f"Unknown text_sim backend: {backend!r}")


def hybrid_sim(step_a: dict, step_b: dict, alpha: float = 0.7, text_backend: Callable | str = "cosine") -> float:
    """alpha * tool_sim + (1 - alpha) * text_sim. At alpha=1.0 ignores text entirely."""
    t_sim = tool_sim(step_a, step_b)
    if alpha == 1.0:
        return t_sim
    thought_a = step_a.get("thought") or ""
    thought_b = step_b.get("thought") or ""
    if not thought_a and not thought_b:
        return t_sim
    return alpha * t_sim + (1.0 - alpha) * text_sim(thought_a, thought_b, text_backend)
