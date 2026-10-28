"""
Step graph (schema v0.2) built from one raw tau2-bench simulation.

Nodes:  AgentStep  — every assistant turn; kind 'message' or 'tool_call' (observation folded in). Scorable.
        UserTurn   — every user-simulator turn. Context only, never scored.
Edges:  temporal        — consecutive nodes in raw message order.
        data_dependency — earliest node whose visible text contains a value consumed by a later tool call's arguments.

v0.2 adds to the hand-built v0.1 example (gibs/examples/task48_success/):
  * a reusable, automatic data-dependency rule (reproduces the hand-verified v0.1 edges),
  * `alternative_sources` on dependency edges (later nodes that also contain the value),
  * `response_node` on AgentSteps (the event that responds to the step),
  * `op_text` / `result_text`: the exact strings given to the NLI model (see `verbalize_*`).

The matcher must only read `nodes` and `edges`; `metadata` holds gold actions and must never be used for matching.
"""
from __future__ import annotations

import json
import re
from typing import Any

SCHEMA_VERSION = "0.2"

# Values that are categorical enums rather than identifiers; never treated as dependency values.
ENUM_VALUES = {"yes", "no", "true", "false", "economy", "business", "basic_economy", "one_way", "round_trip"}
# Value-shaped tokens extracted from free-text arguments (e.g. a transfer summary).
VALUE_TOKEN = re.compile(
    r"\d{4}-\d{2}-\d{2}"                                        # ISO dates
    r"|\b[A-Z0-9]{6}\b"                                         # reservation IDs
    r"|\b[a-z]+_[a-z]+_\d+\b"                                   # user IDs
    r"|\b(?:gift_card|credit_card|certificate)_\d+\b"           # payment IDs
    r"|\bHAT\d{3}\b"                                            # flight numbers
)
FREE_TEXT_MIN_LEN = 40
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONTROL_TOKEN = re.compile(r"^###([A-Z_\-]+)###$")
CONTROL_TEXT = {
    "STOP": "The user ended the conversation.",
    "TRANSFER": "The user was transferred to a human agent.",
    "OUT-OF-SCOPE": "The user said the request is out of scope.",
}
UNICODE_FIXES = {"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
                 " ": " ", " ": " ", "‘": "'", "’": "'", "“": '"', "”": '"'}


# ----------------------------------------------------------------------------------------------- text
def normalize_text(text: str) -> str:
    """Strip markdown emphasis, map typographic Unicode to ASCII, collapse whitespace."""
    for k, v in UNICODE_FIXES.items():
        text = text.replace(k, v)
    text = text.replace("**", "").replace("__", "")
    return re.sub(r"\s+", " ", text).strip()


def _flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            out += _flatten(v, f"{prefix}.{k}" if prefix else str(k))
        return out
    if isinstance(value, list):
        if not value:
            return [(prefix, "[]")]
        out = []
        for i, v in enumerate(value):
            out += _flatten(v, f"{prefix}[{i}]")
        return out
    return [(prefix, value)]


def _scalar(v: Any) -> str:
    return "null" if v is None else (str(v).lower() if isinstance(v, bool) else str(v))


def verbalize_tool_call(name: str, arguments: dict) -> str:
    pairs = _flatten(arguments or {})
    if not pairs:
        return f"Call {name} with no arguments."
    return f"Call {name} with " + "; ".join(f"{k} = {normalize_text(_scalar(v))}" for k, v in pairs) + "."


def verbalize_observation(content: str, error: bool) -> str:
    if error:
        return "Tool error: " + normalize_text(content)
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return "Tool result: " + normalize_text(str(content))
    if isinstance(parsed, (dict, list)):
        return "Tool result: " + "; ".join(f"{k}: {normalize_text(_scalar(v))}" for k, v in _flatten(parsed)) + "."
    return "Tool result: " + normalize_text(_scalar(parsed))


def verbalize_utterance(content: str | None) -> str:
    text = (content or "").strip()
    m = CONTROL_TOKEN.match(text)
    if m:
        return CONTROL_TEXT.get(m.group(1), f"The user sent the control signal {m.group(1)}.")
    return normalize_text(text)


# ------------------------------------------------------------------------------------------- helpers
def _reasoning(msg: dict) -> str | None:
    try:
        m = msg["raw_data"]["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return None
    return m.get("reasoning") or m.get("reasoning_content") or None


def _leaves(v: Any):
    if isinstance(v, dict):
        for x in v.values():
            yield from _leaves(x)
    elif isinstance(v, list):
        for x in v:
            yield from _leaves(x)
    else:
        yield v


def dependency_values(arguments: dict) -> list[str]:
    """Values of a tool call's arguments that are eligible as data dependencies (deduplicated, in order)."""
    out: list[str] = []
    for v in _leaves(arguments or {}):
        if not isinstance(v, str):
            continue  # numbers/bools are not tracked: amounts are usually computed, not copied
        if len(v) >= FREE_TEXT_MIN_LEN:
            cands = VALUE_TOKEN.findall(v)
        elif len(v) < 3 or v.lower() in ENUM_VALUES:
            cands = []
        else:
            cands = [v]
        for c in cands:
            if c not in out:
                out.append(c)
    return out


def value_occurs(value: str, text: str) -> bool:
    """Case-sensitive occurrence with alphanumeric boundaries; an ISO date may be followed by 'T' (timestamp)."""
    left = r"(?<![A-Za-z0-9])"
    right = r"(?![A-Za-z0-9])" if not ISO_DATE.match(value) else r"(?![A-SU-Za-z0-9])"
    return re.search(left + re.escape(value) + right, text) is not None


def _visible_text(node: dict) -> str:
    """Raw (unnormalized) text a later step could have copied a value from."""
    if node["type"] == "UserTurn":
        return node.get("content") or ""
    if node.get("kind") == "tool_call":
        return node["observation"]["content_raw"] or ""
    return node.get("content") or ""


# --------------------------------------------------------------------------------------------- build
def build_step_graph(sim: dict, info: dict | None = None, task: dict | None = None,
                     source_file: str | None = None) -> dict:
    msgs = sim.get("messages") or []
    nodes: list[dict] = []
    step_index = 0
    i = 0
    while i < len(msgs):
        m = msgs[i]
        role = m["role"]
        if role == "user":
            nodes.append({
                "id": f"u{i}", "type": "UserTurn", "scorable": False,
                "raw_message_indices": [i], "turn_idx": m.get("turn_idx"), "timestamp": m.get("timestamp"),
                "content": m.get("content"),
                "op_text": verbalize_utterance(m.get("content")),
                "result_text": verbalize_utterance(m.get("content")),
            })
        elif role == "assistant":
            node = {
                "id": f"s{i}", "type": "AgentStep", "scorable": True, "step_index": step_index,
                "raw_message_indices": [i], "turn_idx": m.get("turn_idx"), "timestamp": m.get("timestamp"),
                "reasoning": _reasoning(m), "content": m.get("content"),
            }
            calls = m.get("tool_calls") or []
            if len(calls) > 1:
                raise ValueError(f"message {i}: parallel tool calls are not supported")
            if calls:
                tc = calls[0]
                if i + 1 >= len(msgs) or msgs[i + 1]["role"] != "tool" or msgs[i + 1].get("id") != tc["id"]:
                    raise ValueError(f"message {i}: tool call {tc['id']} has no immediately following observation")
                obs = msgs[i + 1]
                try:
                    parsed = json.loads(obs["content"])
                except (json.JSONDecodeError, TypeError):
                    parsed = None
                node.update({
                    "kind": "tool_call",
                    "tool_call": {"id": tc["id"], "name": tc["name"], "arguments": tc.get("arguments") or {}},
                    "observation": {"tool_call_id": obs["id"], "error": bool(obs.get("error")),
                                    "raw_message_index": i + 1, "timestamp": obs.get("timestamp"),
                                    "content_raw": obs["content"], "content_parsed": parsed},
                    "op_text": verbalize_tool_call(tc["name"], tc.get("arguments") or {}),
                    "result_text": verbalize_observation(obs["content"], bool(obs.get("error"))),
                })
                node["raw_message_indices"].append(i + 1)
                i += 1
            else:
                node.update({"kind": "message",
                             "op_text": verbalize_utterance(m.get("content")),
                             "result_text": verbalize_utterance(m.get("content"))})
            nodes.append(node)
            step_index += 1
        else:
            raise ValueError(f"message {i}: unpaired role {role!r}")
        i += 1

    # response links: tool call -> its own observation; message -> the next node if it is a UserTurn
    for k, n in enumerate(nodes):
        if n["type"] != "AgentStep":
            continue
        if n["kind"] == "tool_call":
            n["response_node"] = n["id"]
        else:
            nxt = nodes[k + 1] if k + 1 < len(nodes) else None
            n["response_node"] = nxt["id"] if nxt and nxt["type"] == "UserTurn" else None

    edges: list[dict] = [{"id": f"t{k}", "type": "temporal", "source": a["id"], "target": b["id"]}
                         for k, (a, b) in enumerate(zip(nodes, nodes[1:]))]
    dep_count = 0
    for k, n in enumerate(nodes):
        if n.get("kind") != "tool_call":
            continue
        grouped: dict[str, dict] = {}
        for value in dependency_values(n["tool_call"]["arguments"]):
            hits = [p["id"] for p in nodes[:k] if value_occurs(value, _visible_text(p))]
            if not hits:
                continue
            src = hits[0]
            g = grouped.setdefault(src, {"values": [], "alternative_sources": {}})
            g["values"].append(value)
            if hits[1:]:
                g["alternative_sources"][value] = hits[1:]
        for src, g in grouped.items():
            edges.append({"id": f"d{dep_count}", "type": "data_dependency", "source": src, "target": n["id"],
                          "values": g["values"], "alternative_sources": g["alternative_sources"],
                          "rule": "earliest prior node whose raw visible text contains the value"})
            dep_count += 1

    info = info or {}
    ri = sim.get("reward_info") or {}
    reward = ri.get("reward")
    metadata = {
        "source_file": source_file,
        "simulation_id": sim.get("id"),
        "task_id": str(sim.get("task_id")),
        "trial": sim.get("trial"),
        "reward": reward,
        "success": None if reward is None else reward >= 0.5,
        "termination_reason": sim.get("termination_reason"),
        "db_match": (ri.get("db_check") or {}).get("db_match"),
        "agent_llm": (info.get("agent_info") or {}).get("llm"),
        "agent_temperature": ((info.get("agent_info") or {}).get("llm_args") or {}).get("temperature"),
        "user_llm": (info.get("user_info") or {}).get("llm"),
        "tau2_git_commit": info.get("git_commit"),
        "NOTE": "Gold task information below is for humans only; matchers must not read metadata.",
        "task_purpose": ((task or {}).get("description") or {}).get("purpose"),
        "task_gold_actions": ((task or {}).get("evaluation_criteria") or {}).get("actions"),
    }
    return {"schema_version": SCHEMA_VERSION, "graph_id": f"task{metadata['task_id']}_{str(sim.get('id'))[:8]}",
            "metadata": metadata, "nodes": nodes, "edges": edges}


def load_simulation(results_path: str, sim_id_prefix: str) -> tuple[dict, dict, dict | None]:
    """Return (simulation, info, task) for the simulation whose UUID starts with `sim_id_prefix`."""
    with open(results_path) as f:
        data = json.load(f)
    matches = [s for s in data["simulations"] if s["id"].startswith(sim_id_prefix)]
    if len(matches) != 1:
        raise ValueError(f"{len(matches)} simulations match prefix {sim_id_prefix!r} in {results_path}")
    sim = matches[0]
    task = next((t for t in data.get("tasks", []) if str(t["id"]) == str(sim["task_id"])), None)
    return sim, data.get("info") or {}, task
