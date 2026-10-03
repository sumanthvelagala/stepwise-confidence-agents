from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def normalize_value(v: Any) -> Any:
    """Lowercase strings, int-ify whole floats."""
    if isinstance(v, str):
        return v.strip().lower()
    if isinstance(v, float) and v == int(v):
        return int(v)
    return v


def normalize_args(args: dict) -> dict:
    """Normalize all values and sort keys."""
    return {k: normalize_value(v) for k, v in sorted(args.items())}


def _compute_dependencies(steps: list[dict]) -> None:
    """Fill depends_on for each step: step j depends on step i if an arg value first appears in step i's observation."""
    obs_history: list[tuple[int, str]] = []
    for step in steps:
        if step["args"]:
            for val in step["args"].values():
                if isinstance(val, str) and len(val) > 4:
                    for prev_idx, obs in obs_history:
                        if obs and val in obs.lower():
                            if prev_idx not in step["depends_on"]:
                                step["depends_on"].append(prev_idx)
                            break
        if step["obs"] is not None:
            obs_history.append((step["idx"], step["obs"].lower()))


def _extract_steps(messages: list[dict]) -> list[dict]:
    """One step per assistant turn. Tool-call turns get tool/args/obs; text turns get tool=None."""
    steps = []
    idx = 0
    for i, msg in enumerate(messages):
        if msg.get("role") != "assistant":
            continue

        tool_calls = msg.get("tool_calls")
        thought = msg.get("content")

        if tool_calls:
            tc = tool_calls[0]
            tool = tc.get("name")
            args = normalize_args(tc.get("arguments") or {})
            obs = None
            if i + 1 < len(messages) and messages[i + 1].get("role") == "tool":
                raw_obs = messages[i + 1].get("content")
                obs = str(raw_obs) if raw_obs is not None else None
        else:
            tool, args, obs = None, None, None

        steps.append({"idx": idx, "thought": thought, "tool": tool, "args": args, "obs": obs, "depends_on": [], "scored": True})
        idx += 1

    _compute_dependencies(steps)
    return steps


def parse_simulation(sim: dict, info: dict) -> dict:
    """Convert one raw simulation record into a normalized trajectory dict."""
    reward_info = sim.get("reward_info") or {}
    reward = reward_info.get("reward")
    agent_info = info.get("agent_info") or {}
    agent_usage = sim.get("agent_usage") or {}

    return {
        "task_id": str(sim["task_id"]),
        "domain": (info.get("environment_info") or {}).get("domain_name", "unknown"),
        "trial": sim["trial"],
        "agent_model": agent_info.get("llm", ""),
        "success": bool(reward is not None and reward >= 0.5),
        "reward": reward,
        "steps": _extract_steps(sim.get("messages") or []),
        "meta": {"tau2_version": info.get("git_commit", "")},
    }


def parse_results_file(path: str | Path) -> list[dict]:
    """Parse a tau2-bench results.json into a list of trajectory dicts."""
    with open(path) as f:
        data = json.load(f)
    info = data.get("info") or {}
    return [parse_simulation(sim, info) for sim in data.get("simulations", [])]
