"""
Independent step labels for the consensus pilot (rules fixed in gibs/validation/pilot_plan.md).

Uses ONLY the task's gold actions / NL-assertion-backed rules and the airline policy's mandated transfer message.
It never reads the trajectory's reward. Labels: 'valid', 'incorrect', 'attempted_incorrect', 'unverified'.
"""
from __future__ import annotations

from gibs.mcs.structured_fields import CALL_FIELDS, WRITE_TOOLS, _compare, _norm

TRANSFER_MESSAGE = "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."


def _same_call(name: str, args: dict, gold: dict) -> bool:
    if name != gold["name"]:
        return False
    a = {k: _norm(v) for k, v in (args or {}).items()}
    b = {k: _norm(v) for k, v in (gold.get("arguments") or {}).items()}
    return a == b


def classify_steps(step_graph: dict, task: dict) -> dict[str, dict]:
    gold = (task.get("evaluation_criteria") or {}).get("actions") or []
    gold_writes = [g for g in gold if g["name"] in WRITE_TOOLS]
    gold_reads = [g for g in gold if g["name"] not in WRITE_TOOLS]
    labels: dict[str, dict] = {}
    gold_booking_done = False
    nodes = step_graph["nodes"]
    for k, n in enumerate(nodes):
        if n["type"] != "AgentStep":
            continue
        label, reason = "unverified", None
        if n["kind"] == "tool_call":
            name, args = n["tool_call"]["name"], n["tool_call"]["arguments"] or {}
            error = bool(n["observation"]["error"])
            if name in WRITE_TOOLS:
                if not gold_writes:
                    label = "attempted_incorrect" if error else "incorrect"
                    reason = f"gold actions contain no write; {name} {'attempted (tool error)' if error else 'executed'}"
                elif error:
                    label, reason = "unverified", "write attempt returned a tool error (no state change)"
                else:
                    gold_same_tool = [g for g in gold_writes if g["name"] == name]
                    if not gold_same_tool:
                        label, reason = "incorrect", f"successful {name}; the gold actions contain no {name}"
                    elif gold_booking_done:
                        label, reason = "incorrect", f"duplicate successful {name} after the gold-matching one"
                    else:
                        conflicts = _compare("args", args, gold_same_tool[0]["arguments"], CALL_FIELDS.get(name, []))
                        if conflicts:
                            label, reason = "incorrect", "conflicts with gold action: " + "; ".join(conflicts)
                        else:
                            label, reason, gold_booking_done = "valid", "DB-critical arguments equal the gold action", True
            elif any(_same_call(name, args, g) for g in gold_reads):
                label, reason = "valid", "read call equal to a gold action"
        elif (n.get("content") or "").strip() == TRANSFER_MESSAGE:
            prev = next((p for p in reversed(nodes[:k]) if p["type"] == "AgentStep"), None)
            if prev and prev.get("kind") == "tool_call" and prev["tool_call"]["name"] == "transfer_to_human_agents" \
                    and not prev["observation"]["error"]:
                label, reason = "valid", "policy-mandated message after a successful transfer"
        labels[n["id"]] = {"label": label, "reason": reason}
    return labels
