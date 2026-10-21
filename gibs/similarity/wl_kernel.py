"""
Weisfeiler-Leman (WL) graph kernel for structural similarity.

Algorithm:
  1. Assign initial label per node = "{node_type}:{first_word_of_text}"
     (captures tool name for ToolCall nodes, e.g. "tool_call:get_reservation_details")
  2. For k iterations: new_label[v] = hash(label[v], sorted(labels of neighbors))
  3. Build a feature vector = count of each label across iterations
  4. Similarity = cosine similarity of the two feature vectors (normalized to [0,1])
"""
from __future__ import annotations

import hashlib
from collections import Counter


def _initial_label(node: dict) -> str:
    first_word = node["text"].split()[0] if node["text"].strip() else ""
    return f"{node['type']}:{first_word}"


def _wl_feature_vector(nodes: list, edges: list, k: int = 2) -> Counter:
    """Compute WL feature vector (multi-set of labels over k iterations)."""
    if not nodes:
        return Counter()

    labels = {n["id"]: _initial_label(n) for n in nodes}

    # Undirected adjacency for WL neighborhood aggregation
    adj: dict[int, list[int]] = {n["id"]: [] for n in nodes}
    for src, dst, _ in edges:
        if src in adj:
            adj[src].append(dst)
        if dst in adj:
            adj[dst].append(src)

    features = Counter(labels.values())

    for _ in range(k):
        new_labels: dict[int, str] = {}
        for n in nodes:
            nid = n["id"]
            neighbor_labels = sorted(labels.get(nb, "") for nb in adj.get(nid, []))
            label_str = labels[nid] + "|" + ",".join(neighbor_labels)
            new_labels[nid] = hashlib.md5(label_str.encode()).hexdigest()[:8]
        labels = new_labels
        features.update(labels.values())

    return features


def wl_similarity(g1, g2, k: int = 2) -> float:
    """
    WL kernel similarity in [0, 1] between two TrajGraph objects.
    Returns 1.0 if both graphs are empty.
    """
    h1 = _wl_feature_vector(g1.nodes, g1.edges, k)
    h2 = _wl_feature_vector(g2.nodes, g2.edges, k)

    if not h1 and not h2:
        return 1.0
    if not h1 or not h2:
        return 0.0

    all_keys = set(h1) | set(h2)
    dot = sum(h1[key] * h2[key] for key in all_keys)
    norm1 = sum(v * v for v in h1.values()) ** 0.5
    norm2 = sum(v * v for v in h2.values()) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))
