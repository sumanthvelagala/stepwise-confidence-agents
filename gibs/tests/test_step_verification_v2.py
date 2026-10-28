"""Verifier v2 regression tests (gibs/validation/VERIFIER_V2.md). v1 stays unchanged; pilot labels must not change."""
import pytest

from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.tests.helpers import REPO, make_sim
from gibs.validation.step_verification import classify_steps
from gibs.validation.step_verification_v2 import classify_steps_v2, verify_run_v2

T7 = REPO / "results/probe/task_7/results.json"
T42 = REPO / "results/probe/ratelimit_tasks/results.json"
T25F = REPO / "results/probe/new_batch1/results.json"
T25P = REPO / "results/pilot/task_25_topup/results.json"


def both(path, prefix):
    sim, info, task = load_simulation(str(path), prefix)
    g = build_step_graph(sim, info, task)
    return classify_steps(g, task), classify_steps_v2(g, task), g, task


# ------------------------------------------------------------------ the five false v1 labels (real data)
@pytest.mark.parametrize("path,prefix,step,gold", [
    (T42, "ec3d7c00", "s14", 9), (T42, "cdd54c3d", "s18", 9), (T42, "69591e6d", "s26", 9),
    (T7, "39faed8b", "s8", 4), (T7, "c0be2f86", "s18", 4)])
def test_v1_false_incorrect_labels_are_valid_in_v2(path, prefix, step, gold):
    v1, v2, _, _ = both(path, prefix)
    assert v1[step]["label"] == "incorrect"           # documented v1 defect (compared with the first gold write only)
    assert v2[step]["label"] == "valid" and v2[step]["gold_index"] == gold


def test_real_true_negatives_unchanged():
    v1, v2, _, _ = both(T7, "c0be2f86")
    assert v1["s16"]["label"] == v2["s16"]["label"] == "incorrect"          # update on the wrong reservation
    v1, v2, _, _ = both(T42, "69591e6d")
    assert v1["s22"]["label"] == v2["s22"]["label"] == "incorrect"          # cancels SE9KEL (not in gold)
    assert v2["s24"]["label"] == "valid" and v2["s24"]["gold_index"] == 8
    v1, v2, _, _ = both(T25F, "6f12b024")
    assert v1["s30"]["label"] == v2["s30"]["label"] == "incorrect"          # wrong booking
    v1, v2, _, _ = both(T25P, "ab3d173b")
    assert v1["s16"]["label"] == v2["s16"]["label"] == "valid"


def test_pilot_labels_identical_under_v2():
    from gibs.validation.run_pilot import load_runs
    for t in ("48", "9", "25"):
        for r in load_runs(t)[0]:
            a, b = classify_steps(r["steps"], r["task"]), classify_steps_v2(r["steps"], r["task"])
            assert {k: v["label"] for k, v in a.items()} == {k: v["label"] for k, v in b.items()}, (t, r["short"])


# ------------------------------------------------------------------ synthetic ambiguous cases
def task(*actions):
    return {"evaluation_criteria": {"actions": [{"name": n, "arguments": a} for n, a in actions]}}


def labels(events, tk):
    g = build_step_graph(make_sim(events))
    return classify_steps(g, tk), classify_steps_v2(g, tk), g


C = lambda rid: ("call", "cancel_reservation", {"reservation_id": rid}, {"reservation_id": rid, "status": "cancelled"})


def test_duplicate_beyond_gold_count_is_incorrect():
    _, v2, _ = labels([C("A"), C("A")], task(("cancel_reservation", {"reservation_id": "A"})))
    assert v2["s0"]["label"] == "valid" and v2["s2"]["label"] == "incorrect" and "duplicate" in v2["s2"]["reason"]


def test_repeated_identical_gold_writes_consumed_one_to_one():
    tk = task(("cancel_reservation", {"reservation_id": "A"}), ("cancel_reservation", {"reservation_id": "A"}))
    _, v2, _ = labels([C("A"), C("A"), C("A")], tk)
    assert [v2[s]["label"] for s in ("s0", "s2", "s4")] == ["valid", "valid", "incorrect"]


def test_order_is_not_judged_but_reported():
    tk = task(("cancel_reservation", {"reservation_id": "A"}), ("cancel_reservation", {"reservation_id": "B"}))
    v1, v2, g = labels([C("B"), C("A")], tk)
    assert v1["s0"]["label"] == "incorrect"                       # v1 defect: compared with gold A only
    assert v2["s0"]["label"] == v2["s2"]["label"] == "valid"
    run = verify_run_v2(g, tk)
    assert run["order_inversions"] == 1 and run["missing_gold_writes"] == [] and run["expected_db_ok"]


def test_v1_global_flag_defect_fixed_for_different_tools():
    bag = {"reservation_id": "A", "total_baggages": 1, "nonfree_baggages": 0, "payment_id": "gc_1"}
    tk = task(("cancel_reservation", {"reservation_id": "B"}), ("update_reservation_baggages", bag))
    v1, v2, _ = labels([C("B"), ("call", "update_reservation_baggages", bag, {"reservation_id": "A"})], tk)
    assert v1["s2"]["label"] == "incorrect" and "duplicate" in v1["s2"]["reason"]   # v1: one global 'done' flag
    assert v2["s0"]["label"] == v2["s2"]["label"] == "valid"


def test_conflict_with_every_gold_write_lists_all():
    tk = task(("cancel_reservation", {"reservation_id": "A"}), ("cancel_reservation", {"reservation_id": "B"}))
    _, v2, _ = labels([C("Z")], tk)
    assert v2["s0"]["label"] == "incorrect" and "g0:" in v2["s0"]["reason"] and "g1:" in v2["s0"]["reason"]


def test_unchanged_rules_no_gold_writes_and_errored_writes():
    _, v2, _ = labels([C("A"), ("call", "cancel_reservation", {"reservation_id": "B"}, "Error: x", True)], task())
    assert v2["s0"]["label"] == "incorrect" and v2["s2"]["label"] == "attempted_incorrect"
    _, v2, _ = labels([("call", "cancel_reservation", {"reservation_id": "A"}, "Error: x", True)],
                      task(("cancel_reservation", {"reservation_id": "A"})))
    assert v2["s0"]["label"] == "unverified"


def test_omission_and_db_consistency_diagnostics_do_not_change_labels():
    tk = task(("cancel_reservation", {"reservation_id": "A"}), ("cancel_reservation", {"reservation_id": "B"}))
    events = [C("A")]
    _, v2, g = labels(events, tk)
    run = verify_run_v2(g, tk, db_match=True)                     # deliberately contradictory DB flag
    assert run["missing_gold_writes"] == [1] and not run["expected_db_ok"]
    assert run["db_consistency"].startswith("inconsistent")
    assert classify_steps_v2(g, tk) == v2                         # labels independent of db_match
