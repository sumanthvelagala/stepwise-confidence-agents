"""Pilot step-verification rules on real trajectories (no reward is used by the rules)."""
from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.tests.helpers import REPO
from gibs.validation.step_verification import classify_steps

F48 = REPO / "results/pilot/tasks_25_40_48/results.json"
F9 = REPO / "results/pilot/task_9_topup/results.json"
F25P = REPO / "results/pilot/task_25_topup/results.json"
F25F = REPO / "results/probe/new_batch1/results.json"


def labels(path, prefix):
    sim, info, task = load_simulation(str(path), prefix)
    return {k: v["label"] for k, v in classify_steps(build_step_graph(sim, info), task).items()}


def test_task48_failure_cancel_is_incorrect_and_gold_lookup_valid():
    lab = labels(F48, "7f5cbcd7")
    assert lab["s6"] == "incorrect" and lab["s4"] == "valid"
    assert lab["s8"] == "unverified"                     # messages are not labelled


def test_task48_success_transfer_message_is_policy_valid():
    lab = labels(F48, "c890f90b")
    assert lab["s4"] == "valid" and lab["s10"] == "valid" and lab["s8"] == "unverified"


def test_task9_cancel_incorrect_and_gold_search_valid():
    lab = labels(F9, "68290327")
    assert lab["s12"] == "incorrect" and lab["s8"] == "valid"


def test_task25_booking_labels():
    good = labels(F25P, "ab3d173b")
    assert good["s12"] == good["s14"] == "unverified"   # errored attempts
    assert good["s16"] == "valid"                       # equals the gold booking (prices ignored)
    bad = labels(F25F, "6f12b024")
    assert bad["s30"] == "incorrect"                    # wrong date / flight


def test_task25_cancellation_is_incorrect():
    lab = labels(F48, "d7a124a4")
    assert lab["s40"] == "incorrect"
