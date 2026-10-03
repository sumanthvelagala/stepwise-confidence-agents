"""
Hand-made trajectory fixtures for unit tests.

Task "T1": customer cancels a reservation.
  Consensus (successful runs): get_user_details → cancel_reservation
  Failed run A: wrong first tool (get_reservation_details instead)
  Failed run B: wrong second tool (book_reservation instead of cancel)
"""

from __future__ import annotations


def _step(idx, tool, args, obs=None, thought=None):
    return {
        "idx": idx,
        "thought": thought,
        "tool": tool,
        "args": args or {},
        "obs": obs,
        "depends_on": [],
        "scored": True,
    }


def _run(task_id, trial, success, steps):
    return {
        "task_id": task_id,
        "domain": "airline",
        "trial": trial,
        "agent_model": "test-model",
        "user_model": "test-user-model",
        "temperature": 1.0,
        "success": success,
        "reward": 1.0 if success else 0.0,
        "steps": steps,
        "meta": {"tokens_in": 0, "tokens_out": 0, "tau2_version": "test"},
    }


# --- Successful runs (consensus: get_user_details → cancel_reservation) ---

SUCCESS_0 = _run("T1", 0, True, [
    _step(0, "get_user_details",   {"user_id": "alice"}, obs='{"name":"Alice"}'),
    _step(1, "cancel_reservation", {"reservation_id": "res1"}, obs="cancelled"),
])

SUCCESS_1 = _run("T1", 1, True, [
    _step(0, "get_user_details",   {"user_id": "alice"}, obs='{"name":"Alice"}'),
    _step(1, "cancel_reservation", {"reservation_id": "res1"}, obs="cancelled"),
])

SUCCESS_2 = _run("T1", 2, True, [
    _step(0, "get_user_details",   {"user_id": "alice"}, obs='{"name":"Alice"}'),
    _step(1, "cancel_reservation", {"reservation_id": "res1"}, obs="cancelled"),
])

# --- Failed run A: wrong first tool ---

FAIL_A = _run("T1", 3, False, [
    _step(0, "get_reservation_details", {"reservation_id": "res1"}, obs="details"),
    _step(1, "cancel_reservation",      {"reservation_id": "res1"}, obs="cancelled"),
])

# --- Failed run B: wrong second tool ---

FAIL_B = _run("T1", 4, False, [
    _step(0, "get_user_details", {"user_id": "alice"}, obs='{"name":"Alice"}'),
    _step(1, "book_reservation", {"user_id": "alice"}, obs="booked"),
])

ALL_RUNS = [SUCCESS_0, SUCCESS_1, SUCCESS_2, FAIL_A, FAIL_B]


# --- Raw simulation fixture (matches tau2-bench results.json schema) ---

RAW_SIMULATION = {
    "id": "sim-001",
    "task_id": "42",
    "trial": 0,
    "timestamp": "2024-01-01T00:00:00",
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2024-01-01T00:00:10",
    "duration": 10.0,
    "termination_reason": "USER_STOP",
    "agent_cost": 0.0,
    "user_cost": 0.0,
    "agent_usage": {"prompt_tokens": 100, "completion_tokens": 50},
    "reward_info": {
        "reward": 1.0,
        "db_check": {"db_match": True, "db_reward": 1.0},
        "reward_breakdown": {"DB": 1.0},
    },
    "messages": [
        # turn 0: agent greeting
        {
            "role": "assistant",
            "content": "Hello, how can I help?",
            "tool_calls": None,
            "turn_idx": 0,
            "timestamp": None,
        },
        # turn 1: user message
        {
            "role": "user",
            "content": "Cancel my flight RES99.",
            "tool_calls": None,
            "turn_idx": 1,
            "timestamp": None,
        },
        # turn 2: agent tool call
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "tc-1",
                    "name": "get_user_details",
                    "arguments": {"user_id": "Bob_42"},
                    "requestor": "assistant",
                }
            ],
            "turn_idx": 2,
            "timestamp": None,
        },
        # turn 3: tool response
        {
            "role": "tool",
            "content": '{"name": "Bob", "reservations": ["RES99"]}',
            "turn_idx": 3,
            "timestamp": None,
        },
        # turn 4: agent second tool call
        {
            "role": "assistant",
            "content": "Let me cancel that for you.",
            "tool_calls": [
                {
                    "id": "tc-2",
                    "name": "cancel_reservation",
                    "arguments": {"reservation_id": "RES99"},
                    "requestor": "assistant",
                }
            ],
            "turn_idx": 4,
            "timestamp": None,
        },
        # turn 5: tool response
        {
            "role": "tool",
            "content": "cancelled",
            "turn_idx": 5,
            "timestamp": None,
        },
    ],
    "ticks": None,
    "trial": 0,
    "seed": 42,
    "mode": "half_duplex",
    "speech_environment": None,
    "review": None,
    "user_only_review": None,
    "info": None,
    "auth_classification": None,
    "hallucination_retries_used": 0,
    "hallucination_check": None,
    "provider_session_id": None,
    "policy": "",
    "effect_timeline": None,
}

RAW_INFO = {
    "git_commit": "abc123",
    "agent_info": {
        "implementation": "llm_agent",
        "llm": "test/model",
        "llm_args": {"temperature": 1.0},
    },
    "user_info": {
        "implementation": "user_simulator",
        "llm": "test/user-model",
        "llm_args": {"temperature": 0.0},
    },
    "environment_info": {
        "domain_name": "airline",
    },
    "num_trials": 5,
    "seed": 42,
}
