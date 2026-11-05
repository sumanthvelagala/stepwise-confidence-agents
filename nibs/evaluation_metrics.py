"""Offline ranking metrics. Confidence is high for correct steps; errors are positive."""
from __future__ import annotations

import math
from collections import Counter


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else None


def harmonic(n):
    return sum(1 / r for r in range(1, n + 1))


def binary_metrics(rows, score_key="confidence"):
    """Rows have label correct/incorrect (others ignored), plus a confidence score."""
    correct = [r[score_key] for r in rows if r["label"] == "correct"]
    errors = [r[score_key] for r in rows if r["label"] == "incorrect"]
    pairs = len(correct) * len(errors)
    auc = (sum((c > e) + .5 * (c == e) for c in correct for e in errors) / pairs
           if pairs else None)
    # Group equal scores before advancing the PR curve: no arbitrary tie-breaking.
    groups = {}
    for r in rows:
        if r["label"] in ("correct", "incorrect"):
            bucket = groups.setdefault(r[score_key], Counter())
            bucket[r["label"]] += 1
    tp = total = 0
    ap = 0.0
    for score in sorted(groups):
        g = groups[score]
        tp += g["incorrect"]
        total += sum(g.values())
        if errors:
            ap += g["incorrect"] / len(errors) * tp / total
    return {"n_correct": len(correct), "n_incorrect": len(errors), "n_pairs": pairs,
            "auroc_error_positive": auc,
            "average_precision_error_positive": ap if errors else None,
            "error_detection_at_0.5": mean(x < .5 for x in errors),
            "correct_step_false_alarm_at_0.5": mean(x < .5 for x in correct),
            "mean_correct_confidence": mean(correct), "mean_incorrect_confidence": mean(errors)}


def random_binary_metrics(n_correct, n_incorrect):
    n = n_correct + n_incorrect
    # Exact expected AP of an iid continuous random ordering, not a selected seed.
    if not n_incorrect:
        ap = None
    elif n == 1:
        ap = 1.0
    else:
        ap = ((n_incorrect - 1) / (n - 1)
              + (n - n_incorrect) * harmonic(n) / (n * (n - 1)))
    return {"n_correct": n_correct, "n_incorrect": n_incorrect,
            "n_pairs": n_correct * n_incorrect,
            "auroc_error_positive": .5 if n_correct and n_incorrect else None,
            "average_precision_error_positive": ap,
            "error_detection_at_0.5": .5 if n_incorrect else None,
            "correct_step_false_alarm_at_0.5": .5 if n_correct else None}


def target_rank(scores, target):
    """Expected top-k/rank/RR under uniform tie-breaking for one target."""
    if not scores or not 0 <= target < len(scores):
        raise ValueError("target must identify a candidate")
    if any(not math.isfinite(x) for x in scores):
        raise ValueError("scores must be finite")
    value = scores[target]
    lower = sum(s < value for s in scores)
    tied = sum(s == value for s in scores)
    lo, hi = lower + 1, lower + tied
    return {"n_candidates": len(scores), "rank_min": lo, "rank_max": hi,
            "expected_rank": (lo + hi) / 2,
            "top1": max(0, min(tied, 1 - lower)) / tied,
            "top3": max(0, min(tied, 3 - lower)) / tied,
            "reciprocal_rank": sum(1 / r for r in range(lo, hi + 1)) / tied}


def random_target_rank(n):
    return target_rank([0.0] * n, 0)


def localization_summary(rows):
    rows = list(rows)
    return {"n_failed_queries_with_labelled_error": len(rows),
            **{k: mean(r[k] for r in rows)
               for k in ("top1", "top3", "expected_rank", "reciprocal_rank")}}


def agreement(pairs):
    """Unweighted Cohen's kappa, including ambiguous/environment categories."""
    pairs = list(pairs)
    if not pairs:
        return {"n_double_labelled": 0, "agreement": None, "cohens_kappa": None}
    a, b = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    pe = sum(a[k] * b[k] for k in a.keys() | b.keys()) / n ** 2
    return {"n_double_labelled": n, "agreement": po,
            "cohens_kappa": (po - pe) / (1 - pe) if pe < 1 else None}
