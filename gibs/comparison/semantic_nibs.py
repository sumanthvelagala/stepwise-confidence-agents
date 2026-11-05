"""PDF equation-2 NIBS and separately labelled released cosine transformations."""
from __future__ import annotations

import numpy as np


def cosine_matrix(query, reference):
    query, reference = np.asarray(query, dtype=np.float64), np.asarray(reference, dtype=np.float64)
    q = query / np.maximum(np.linalg.norm(query, axis=1, keepdims=True), 1e-12)
    r = reference / np.maximum(np.linalg.norm(reference, axis=1, keepdims=True), 1e-12)
    return np.clip(q @ r.T, -1, 1)


def reference_scores(query, references, released=False):
    """Equal weight per reference run, regardless of its number of steps."""
    if not references or any(len(r) == 0 for r in references):
        raise ValueError("nonempty reference runs required")
    maxima, means = [], []
    for reference in references:
        cosine = cosine_matrix(query, reference)
        if released:
            # Authors' cosine_max/mean: inverse distance after within-run reduction.
            maxima.append(1 / (2 - cosine.max(axis=1)))
            means.append(1 / (2 - cosine.mean(axis=1)))
        else:
            maxima.append(cosine.max(axis=1))
            means.append(cosine.mean(axis=1))
    return np.mean(maxima, axis=0).tolist(), np.mean(means, axis=0).tolist()


def score_dataset(runs, features):
    operations = {r["id"]: features[r["id"]]["operations"][features[r["id"]]["agent_indices"]].numpy() for r in runs}
    edge_operations = {r["id"]: features[r["id"]]["edge_operations"].numpy() for r in runs}
    results = {name: {} for name in ("paper_nibs_cos_max", "paper_nibs_cos_mean", "released_nibs_cos_max", "released_nibs_cos_mean")}
    references = {}
    for q in runs:
        refs = [r for r in runs if r["task_id"] == q["task_id"] and r["success"] and r["content_hash"] != q["content_hash"]]
        if len(refs) < 3:
            raise ValueError("fewer than 3 leave-class-out semantic NIBS references")
        references[q["id"]] = [r["id"] for r in refs]
        maximum, average = reference_scores(operations[q["id"]], [operations[r["id"]] for r in refs])
        released_max, released_mean = reference_scores(operations[q["id"]], [edge_operations[r["id"]] for r in refs], released=True)
        for name, value in zip(results, (maximum, average, released_max, released_mean)):
            results[name][q["id"]] = value
    return results, references
