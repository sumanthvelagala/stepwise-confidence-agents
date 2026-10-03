"""Tests for parsing/parser.py — no API calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsing.parser import (
    normalize_args,
    normalize_value,
    parse_simulation,
    parse_results_file,
)
from tests.fixtures import RAW_SIMULATION, RAW_INFO


# ---------------------------------------------------------------------------
# normalize_value
# ---------------------------------------------------------------------------

def test_normalize_value_strips_and_lowercases_string():
    assert normalize_value("  ALICE ") == "alice"


def test_normalize_value_int_ifies_whole_float():
    assert normalize_value(3.0) == 3
    assert isinstance(normalize_value(3.0), int)


def test_normalize_value_keeps_non_whole_float():
    assert normalize_value(3.14) == 3.14


def test_normalize_value_passthrough_int():
    assert normalize_value(5) == 5


# ---------------------------------------------------------------------------
# normalize_args
# ---------------------------------------------------------------------------

def test_normalize_args_sorts_keys():
    result = normalize_args({"z": "val", "a": "other"})
    assert list(result.keys()) == ["a", "z"]


def test_normalize_args_lowercases_values():
    result = normalize_args({"User_ID": " ALICE "})
    assert result["User_ID"] == "alice"


def test_normalize_args_empty():
    assert normalize_args({}) == {}


# ---------------------------------------------------------------------------
# parse_simulation — step extraction
# ---------------------------------------------------------------------------

def test_parse_simulation_returns_correct_structure():
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    assert traj["task_id"] == "42"
    assert traj["domain"] == "airline"
    assert traj["trial"] == 0
    assert traj["success"] is True
    assert traj["reward"] == 1.0
    assert traj["agent_model"] == "test/model"
    assert traj["meta"]["tau2_version"] == "abc123"


def test_parse_simulation_step_count():
    # 3 assistant messages → 3 steps (greeting, tool call, second tool call)
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    assert len(traj["steps"]) == 3


def test_parse_simulation_first_step_is_greeting():
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    step0 = traj["steps"][0]
    assert step0["idx"] == 0
    assert step0["tool"] is None
    assert step0["thought"] == "Hello, how can I help?"
    assert step0["obs"] is None
    assert step0["scored"] is True


def test_parse_simulation_tool_call_step():
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    step1 = traj["steps"][1]
    assert step1["tool"] == "get_user_details"
    assert step1["args"] == {"user_id": "bob_42"}   # normalized
    assert step1["obs"] is not None
    assert "Bob" in step1["obs"]


def test_parse_simulation_second_tool_call_has_obs():
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    step2 = traj["steps"][2]
    assert step2["tool"] == "cancel_reservation"
    assert step2["args"] == {"reservation_id": "res99"}   # normalized
    assert step2["obs"] == "cancelled"


def test_parse_simulation_all_steps_scored():
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    assert all(s["scored"] for s in traj["steps"])


def test_parse_simulation_depends_on_populated():
    traj = parse_simulation(RAW_SIMULATION, RAW_INFO)
    # step2 uses reservation_id="res99" which appeared in step1's obs
    # (step1 obs: '{"name": "Bob", "reservations": ["RES99"]}')
    step2 = traj["steps"][2]
    assert 1 in step2["depends_on"]


def test_parse_simulation_failed_run():
    import copy
    sim = copy.deepcopy(RAW_SIMULATION)
    sim["reward_info"]["reward"] = 0.0
    traj = parse_simulation(sim, RAW_INFO)
    assert traj["success"] is False
    assert traj["reward"] == 0.0


def test_parse_simulation_none_reward():
    import copy
    sim = copy.deepcopy(RAW_SIMULATION)
    sim["reward_info"] = {}
    traj = parse_simulation(sim, RAW_INFO)
    assert traj["success"] is False
    assert traj["reward"] is None


# ---------------------------------------------------------------------------
# parse_results_file — integration test against real smoke data
# ---------------------------------------------------------------------------

SMOKE_PATH = (
    Path(__file__).parent.parent.parent
    / "tau2-bench/data/simulations/smoke_task0/results.json"
)


def test_parse_results_file_smoke():
    if not SMOKE_PATH.exists():
        import pytest
        pytest.skip("smoke_task0 results not present")

    trajs = parse_results_file(SMOKE_PATH)
    assert len(trajs) == 5                          # 5 trials
    for t in trajs:
        assert t["task_id"] == "0"
        assert t["domain"] == "airline"
        assert isinstance(t["steps"], list)
        assert len(t["steps"]) > 0
        assert all(isinstance(s["idx"], int) for s in t["steps"])
