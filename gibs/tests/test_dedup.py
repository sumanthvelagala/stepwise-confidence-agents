"""Exact-duplicate rules for evaluation (gibs/validation/dedup.py; EVALUATION_PROTOCOL.md §4)."""
import json

from gibs.tests.helpers import REPO
from gibs.validation.dedup import content_hash, duplicate_classes, references_for, representatives

F48 = REPO / "results/pilot/tasks_25_40_48/results.json"
F28 = REPO / "results/pilot/task_28/results.json"


def runs(path, task):
    d = json.load(open(path))
    return [{"id": s["id"], "_sim": s, "success": s["reward_info"]["reward"] >= 0.5} for s in d["simulations"]
            if str(s["task_id"]) == task and (s.get("reward_info") or {}).get("reward") is not None]


def test_known_t48_duplicate_pair_and_self_exclusion():
    rs = runs(F48, "48")
    classes = [sorted(r["id"][:8] for r in m) for m in duplicate_classes(rs).values() if len(m) > 1]
    assert ["c890f90b", "e6daf449"] in classes
    reps = representatives([r for r in rs if r["success"]])
    q = next(r for r in rs if r["id"].startswith("e6daf449"))
    refs = references_for(q, reps)
    assert all(not r["id"].startswith(("c890f90b", "e6daf449")) for r in refs)       # own class excluded
    assert len({r["content_hash"] for r in refs}) == len(refs)                        # one per class


def test_hash_ignores_ids_and_timestamps():
    s = runs(F48, "48")[0]["_sim"]
    t = json.loads(json.dumps(s))
    t["id"] = "x"
    for m in t["messages"]:
        m["timestamp"] = "2000-01-01"
        if m.get("tool_calls"):
            for c in m["tool_calls"]:
                c["id"] = "other"
    assert content_hash(s) == content_hash(t)


def test_t28_duplicate_classes():
    rs = [r for r in runs(F28, "28") if r["success"]]
    sizes = sorted(len(m) for m in duplicate_classes(rs).values() if len(m) > 1)
    assert sizes == [2, 5]
    reps = representatives(rs)
    assert sum(r["multiplicity"] for r in reps) == len(rs)
