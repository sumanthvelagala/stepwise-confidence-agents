"""Builders for small synthetic tau2-style simulations used by the GIBS tests (no model, no API)."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TASK48_FILE = REPO / "results/pilot/tasks_25_40_48/results.json"
TASK48_SUCCESS = "c890f90b"
TASK48_FAILURE = "7f5cbcd7"


def make_sim(events: list[tuple], sim_id: str = "sim-0", reward: float = 1.0) -> dict:
    """events: ("agent", text) | ("user", text) | ("call", tool_name, arguments, observation_dict_or_str[, error])"""
    msgs = []
    for k, ev in enumerate(events):
        if ev[0] == "agent":
            msgs.append({"role": "assistant", "content": ev[1], "tool_calls": None})
        elif ev[0] == "user":
            msgs.append({"role": "user", "content": ev[1]})
        elif ev[0] == "call":
            call_id = f"call_{k}"
            obs = ev[3] if isinstance(ev[3], str) else json.dumps(ev[3])
            msgs.append({"role": "assistant", "content": None,
                         "tool_calls": [{"id": call_id, "name": ev[1], "arguments": ev[2]}]})
            msgs.append({"role": "tool", "id": call_id, "content": obs, "error": len(ev) > 4 and ev[4]})
        else:
            raise ValueError(ev)
    return {"id": sim_id, "task_id": "T", "trial": 0, "messages": msgs,
            "reward_info": {"reward": reward}, "termination_reason": "user_stop"}
