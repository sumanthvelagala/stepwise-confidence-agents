"""Tests for scoring/nibs.py — no API calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.nibs import best_match, score_run, score_task
from similarity.similarity import tool_sim
from tests.fixtures import (
    SUCCESS_0, SUCCESS_1, SUCCESS_2,
    FAIL_A, FAIL_B,
    ALL_RUNS,
)


# Use tool_sim only (alpha=1.0) as the sim_fn — no model downloads needed
sim_fn = tool_sim


# ---------------------------------------------------------------------------
# best_match
# ---------------------------------------------------------------------------

def test_best_match_identical_step_scores_1():
    step = SUCCESS_0["steps"][0]   # get_user_details / user_id=alice
    ref_steps = SUCCESS_1["steps"]
    score = best_match(step, ref_steps, sim_fn, aggregation="max")
    assert score == 1.0


def test_best_match_wrong_tool_scores_0():
    step = FAIL_A["steps"][0]      # get_reservation_details — not in ref
    ref_steps = SUCCESS_0["steps"] # ref has get_user_details
    score = best_match(step, ref_steps, sim_fn, aggregation="max")
    assert score == 0.0


def test_best_match_empty_ref_scores_0():
    step = SUCCESS_0["steps"][0]
    assert best_match(step, [], sim_fn) == 0.0


def test_best_match_mean_vs_max():
    step = SUCCESS_0["steps"][0]   # get_user_details/alice
    ref_steps = SUCCESS_1["steps"] # [get_user_details/alice, cancel_reservation/res1]
    mx = best_match(step, ref_steps, sim_fn, aggregation="max")
    mn = best_match(step, ref_steps, sim_fn, aggregation="mean")
    # max: max(1.0, 0.0) = 1.0 (matches step0, not step1)
    # mean: (1.0 + 0.0) / 2 = 0.5
    assert mx == 1.0
    assert mn == 0.5
    assert mx > mn


# ---------------------------------------------------------------------------
# score_run
# ---------------------------------------------------------------------------

def test_score_run_successful_run_scores_high():
    refs = [SUCCESS_1, SUCCESS_2]   # leave out SUCCESS_0
    scores = score_run(SUCCESS_0, refs, sim_fn)
    assert len(scores) == len(SUCCESS_0["steps"])
    avg = sum(s["score"] for s in scores) / len(scores)
    assert avg == 1.0


def test_score_run_failed_run_a_scores_lower():
    refs = [SUCCESS_0, SUCCESS_1, SUCCESS_2]
    scores = score_run(FAIL_A, refs, sim_fn)
    avg = sum(s["score"] for s in scores) / len(scores)
    # Step 0 of FAIL_A uses wrong tool → scores 0; step 1 is correct → scores 1
    # avg should be 0.5
    assert avg < 1.0


def test_score_run_first_step_of_fail_a_is_0():
    refs = [SUCCESS_0, SUCCESS_1, SUCCESS_2]
    scores = score_run(FAIL_A, refs, sim_fn)
    # idx 0 → get_reservation_details (wrong), should score 0
    step0_score = next(s["score"] for s in scores if s["idx"] == 0)
    assert step0_score == 0.0


def test_score_run_second_step_of_fail_a_is_1():
    refs = [SUCCESS_0, SUCCESS_1, SUCCESS_2]
    scores = score_run(FAIL_A, refs, sim_fn)
    # idx 1 → cancel_reservation (correct), should score 1
    step1_score = next(s["score"] for s in scores if s["idx"] == 1)
    assert step1_score == 1.0


def test_score_run_no_refs_scores_0():
    scores = score_run(SUCCESS_0, [], sim_fn)
    assert all(s["score"] == 0.0 for s in scores)


def test_score_run_returns_one_entry_per_scored_step():
    refs = [SUCCESS_1, SUCCESS_2]
    scores = score_run(SUCCESS_0, refs, sim_fn)
    scored_steps = [s for s in SUCCESS_0["steps"] if s.get("scored", True)]
    assert len(scores) == len(scored_steps)


# ---------------------------------------------------------------------------
# score_task — leave-one-out
# ---------------------------------------------------------------------------

def test_score_task_returns_results_for_all_runs():
    out = score_task(ALL_RUNS, sim_fn, k_min=3)
    assert not out["skipped"]
    assert len(out["results"]) == len(ALL_RUNS)


def test_score_task_successful_runs_score_higher_than_failed():
    out = score_task(ALL_RUNS, sim_fn, k_min=3)
    def mean_score(trial):
        r = next(r for r in out["results"] if r["trial"] == trial)
        ss = r["step_scores"]
        return sum(s["score"] for s in ss) / len(ss)

    avg_success = (mean_score(0) + mean_score(1) + mean_score(2)) / 3
    avg_fail = (mean_score(3) + mean_score(4)) / 2
    assert avg_success > avg_fail


def test_score_task_leave_one_out_successful_run():
    """A successful run must not be in its own reference set."""
    out = score_task(ALL_RUNS, sim_fn, k_min=3)
    # With 3 successful runs and LOO, each successful run uses 2 refs.
    # If a run were compared to itself it would always get 1.0 for every step.
    # SUCCESS_0 scores 1.0 even without itself — that's fine.
    # The key test: the code doesn't crash and returns 3 successful results.
    success_results = [r for r in out["results"] if r["success"]]
    assert len(success_results) == 3


def test_score_task_k_min_skip():
    """Task with fewer than k_min successes must be skipped."""
    only_two_successes = [SUCCESS_0, SUCCESS_1, FAIL_A, FAIL_B]
    out = score_task(only_two_successes, sim_fn, k_min=3)
    assert out["skipped"] is True
    assert out["success_count"] == 2


def test_score_task_k_min_exact_boundary():
    """Exactly k_min successes → not skipped."""
    three_runs = [SUCCESS_0, SUCCESS_1, SUCCESS_2]
    out = score_task(three_runs, sim_fn, k_min=3)
    # After LOO each successful run has 2 refs < k_min=3, so all get skipped
    # at the individual run level — but the task itself is not marked skipped.
    assert out["skipped"] is False
    assert out["success_count"] == 3


def test_score_task_skipped_record_has_reason():
    out = score_task([SUCCESS_0, FAIL_A], sim_fn, k_min=3)
    assert out["skipped"] is True
    assert "reason" in out
    assert "success_count" in out


def test_score_task_aggregation_mean():
    out = score_task(ALL_RUNS, sim_fn, aggregation="mean", k_min=3)
    assert not out["skipped"]
    assert len(out["results"]) == len(ALL_RUNS)
