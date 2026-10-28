"""
Exact-duplicate handling for evaluation (EVALUATION_PROTOCOL.md §4).

Two runs are exact duplicates if `content_hash` is equal: identical message sequence (roles, texts, tool-call names and
arguments, tool outputs, error flags), ignoring ids and timestamps. The hash is the one used by dataset_audit.py.

Rules:
  * representative of a duplicate class = the run with the lexicographically smallest simulation UUID;
  * successful references for a query = one representative per DISTINCT successful content class, excluding the
    query's own class (a run is never supported by a copy of itself);
  * evaluation unit = distinct content class (each class scored once, with its multiplicity recorded).
"""
from __future__ import annotations

from collections import defaultdict

from gibs.validation.dataset_audit import canon as content_hash  # noqa: F401  (single definition)


def duplicate_classes(runs: list[dict]) -> dict[str, list[dict]]:
    """runs: dicts with 'id' and '_sim' (raw simulation) -> {hash: [runs sorted by id]}"""
    classes = defaultdict(list)
    for r in runs:
        classes[content_hash(r["_sim"])].append(r)
    return {h: sorted(v, key=lambda r: r["id"]) for h, v in classes.items()}


def representatives(runs: list[dict]) -> list[dict]:
    """One run per content class (smallest UUID), each annotated with its class multiplicity."""
    out = []
    for h, members in duplicate_classes(runs).items():
        rep = dict(members[0])
        rep["content_hash"], rep["multiplicity"], rep["duplicates"] = h, len(members), [m["id"] for m in members[1:]]
        out.append(rep)
    return sorted(out, key=lambda r: r["id"])


def references_for(query: dict, successful_reps: list[dict]) -> list[dict]:
    """Distinct successful references for `query` (never its own content class)."""
    qh = content_hash(query["_sim"])
    return [r for r in successful_reps if r["content_hash"] != qh]
