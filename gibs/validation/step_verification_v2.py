"""
Independent step labels, version 2 (corrected verifier; report: gibs/validation/VERIFIER_V2.md).

Version 1 (`step_verification.py`) is kept unchanged; every pilot / C4 / C5 / C6 result was produced with it.

v2 changes ONLY how successful write calls are matched when the task's gold actions contain writes:
  * a write is compared with ALL gold writes of the same tool (v1: only the first one);
  * gold writes are consumed one-to-one (multiset matching): a write is valid if it matches a not-yet-matched gold
    write of its tool; a write that matches only already-matched gold writes is a duplicate (incorrect);
  * the "already matched" state is per gold action (v1: one global flag shared by all tools).
Everything else is identical to v1: reads, the transfer-message rule, writes in tasks without gold writes, and errored
writes in tasks with gold writes ('unverified').

Like v1, labels never read the run's reward. Order and final-DB information are reported only as run-level
DIAGNOSTICS (`verify_run_v2`), never used to assign a step label (see VERIFIER_V2.md §3).
"""
from __future__ import annotations

from gibs.mcs.structured_fields import CALL_FIELDS, WRITE_TOOLS, _compare
from gibs.validation.step_verification import TRANSFER_MESSAGE, _same_call

VERSION = "2.0"


def _conflicts(name: str, args: dict, gold_args: dict) -> list[str]:
    return _compare("args", args or {}, gold_args or {}, CALL_FIELDS.get(name, []))


def classify_steps_v2(step_graph: dict, task: dict) -> dict[str, dict]:
    """{event: {label, reason, gold_index}}; labels as in v1: valid / incorrect / attempted_incorrect / unverified."""
    gold = (task.get("evaluation_criteria") or {}).get("actions") or []
    gold_writes = [(i, g) for i, g in enumerate(gold) if g["name"] in WRITE_TOOLS]
    gold_reads = [g for g in gold if g["name"] not in WRITE_TOOLS]
    consumed: set[int] = set()
    labels: dict[str, dict] = {}
    nodes = step_graph["nodes"]
    for k, n in enumerate(nodes):
        if n["type"] != "AgentStep":
            continue
        label, reason, gidx = "unverified", None, None
        if n["kind"] == "tool_call":
            name, args = n["tool_call"]["name"], n["tool_call"]["arguments"] or {}
            error = bool(n["observation"]["error"])
            if name in WRITE_TOOLS:
                if not gold_writes:                                   # unchanged from v1
                    label = "attempted_incorrect" if error else "incorrect"
                    reason = f"gold actions contain no write; {name} {'attempted (tool error)' if error else 'executed'}"
                elif error:                                           # unchanged from v1
                    label, reason = "unverified", "write attempt returned a tool error (no state change)"
                else:
                    same_tool = [(i, g) for i, g in gold_writes if g["name"] == name]
                    if not same_tool:
                        label, reason = "incorrect", f"successful {name}; the gold actions contain no {name}"
                    else:
                        compatible = [i for i, g in same_tool if not _conflicts(name, args, g["arguments"])]
                        free = [i for i in compatible if i not in consumed]
                        if free:
                            gidx = free[0]
                            consumed.add(gidx)
                            label, reason = "valid", f"DB-critical arguments equal gold action g{gidx}"
                        elif compatible:
                            label, reason = "incorrect", (f"duplicate: equals gold action(s) "
                                                          f"{', '.join(f'g{i}' for i in compatible)}, already matched")
                        else:
                            parts = [f"g{i}: " + "; ".join(_conflicts(name, args, g["arguments"])) for i, g in same_tool]
                            label, reason = "incorrect", "conflicts with every gold " + name + " action: " + " | ".join(parts)
            elif any(_same_call(name, args, g) for g in gold_reads):  # unchanged from v1
                label, reason = "valid", "read call equal to a gold action"
        elif (n.get("content") or "").strip() == TRANSFER_MESSAGE:   # unchanged from v1
            prev = next((p for p in reversed(nodes[:k]) if p["type"] == "AgentStep"), None)
            if prev and prev.get("kind") == "tool_call" and prev["tool_call"]["name"] == "transfer_to_human_agents" \
                    and not prev["observation"]["error"]:
                label, reason = "valid", "policy-mandated message after a successful transfer"
        labels[n["id"]] = {"label": label, "reason": reason, "gold_index": gidx}
    return labels


def verify_run_v2(step_graph: dict, task: dict, db_match: bool | None = None) -> dict:
    """Run-level diagnostics (NOT step labels):
      * missing_gold_writes: gold writes no successful write matched (errors of omission; no step to label);
      * order_inversions: matched gold writes executed in a different relative order than listed in the gold actions
        (the benchmark scores the final DB, so order is reported, not judged);
      * db_consistency: whether the step labels agree with the benchmark's final-DB check, if `db_match` is supplied.
        'expected_ok' = all gold writes matched and no successful incorrect write. Disagreements are flagged for
        manual review; db_match never changes a label."""
    labels = classify_steps_v2(step_graph, task)
    gold = (task.get("evaluation_criteria") or {}).get("actions") or []
    gold_write_idx = [i for i, g in enumerate(gold) if g["name"] in WRITE_TOOLS]
    matched = [v["gold_index"] for v in labels.values() if v["gold_index"] is not None]   # in execution order
    inversions = sum(1 for a in range(len(matched)) for b in range(a + 1, len(matched)) if matched[a] > matched[b])
    incorrect_ok_writes = [e for e, v in labels.items() if v["label"] == "incorrect"]
    expected_ok = not (set(gold_write_idx) - set(matched)) and not incorrect_ok_writes
    out = {"version": VERSION, "missing_gold_writes": sorted(set(gold_write_idx) - set(matched)),
           "matched_gold_writes": matched, "order_inversions": inversions,
           "incorrect_writes": incorrect_ok_writes, "expected_db_ok": expected_ok}
    if db_match is not None:
        out["db_match"] = bool(db_match)
        out["db_consistency"] = "consistent" if expected_ok == bool(db_match) else "inconsistent (manual review)"
    return out
