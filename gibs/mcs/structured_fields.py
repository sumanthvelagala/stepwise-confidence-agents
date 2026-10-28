"""
Configuration C — deterministic structured-field validation for tool steps.  [OURS: NOT part of the paper's method]

Motivation (measured, gibs/examples/task48_pair/README.md): DeBERTa-MNLI rates long JSON observations as mutual
entailment even when a decision-critical field differs (cancelled vs active reservation, a different passenger DOB),
and long tool texts must be truncated at 512 tokens. These checks act only as an extra *rejection* rule on MCS
candidates whose two tool events already pass the NLI thresholds; they never create a match that NLI rejected.

A pair of tool events is HARD-INCOMPATIBLE when:
  * the tool names differ;
  * a decision-critical argument of that tool has conflicting values (or is present in only one call);
  * the observations differ in error status;
  * both observations are records of the same type (reservation / user) and a decision-critical record field
    conflicts.
Everything else is an ORDINARY difference and is left to NLI: free-text arguments (e.g. transfer `summary`),
flight prices, error wording, search-result lists, fields not listed below. Ordinary differences in arguments are
reported as `ignored` for transparency.

Field choice: for write tools, the arguments that determine the resulting database state (the benchmark's success
criterion is a DB match); for read tools, the arguments that identify *what* is read.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

WRITE_TOOLS = {"book_reservation", "cancel_reservation", "send_certificate", "update_reservation_flights",
               "update_reservation_passengers", "update_reservation_baggages"}

FLIGHT_KEYS = ("flight_number", "date")
PASSENGER_KEYS = ("first_name", "last_name", "dob")

# field spec: (name, kind, keys)   kind: 'scalar' | 'seq' (ordered list of dicts on `keys`) | 'payments' (multiset)
CALL_FIELDS: dict[str, list[tuple]] = {
    "get_reservation_details": [("reservation_id", "scalar", None)],
    "get_user_details": [("user_id", "scalar", None)],
    "get_flight_status": [("flight_number", "scalar", None), ("date", "scalar", None)],
    "search_direct_flight": [("origin", "scalar", None), ("destination", "scalar", None), ("date", "scalar", None)],
    "search_onestop_flight": [("origin", "scalar", None), ("destination", "scalar", None), ("date", "scalar", None)],
    "cancel_reservation": [("reservation_id", "scalar", None)],
    "send_certificate": [("user_id", "scalar", None), ("amount", "scalar", None)],
    "update_reservation_passengers": [("reservation_id", "scalar", None), ("passengers", "seq", PASSENGER_KEYS)],
    "update_reservation_flights": [("reservation_id", "scalar", None), ("cabin", "scalar", None),
                                   ("flights", "seq", FLIGHT_KEYS), ("payment_id", "scalar", None)],
    "update_reservation_baggages": [("reservation_id", "scalar", None), ("total_baggages", "scalar", None),
                                    ("nonfree_baggages", "scalar", None), ("payment_id", "scalar", None)],
    "book_reservation": [("user_id", "scalar", None), ("origin", "scalar", None), ("destination", "scalar", None),
                         ("flight_type", "scalar", None), ("cabin", "scalar", None), ("flights", "seq", FLIGHT_KEYS),
                         ("passengers", "seq", PASSENGER_KEYS), ("payment_methods", "payments", None),
                         ("total_baggages", "scalar", None), ("nonfree_baggages", "scalar", None),
                         ("insurance", "scalar", None)],
    "calculate": [("expression", "scalar", None)],
    # transfer_to_human_agents (free-text summary), list_all_airports (no arguments), unknown tools: name only
}

RESERVATION_FIELDS = [(k, "scalar", None) for k in ("reservation_id", "user_id", "origin", "destination",
                                                    "flight_type", "cabin", "status", "created_at", "total_baggages",
                                                    "nonfree_baggages", "insurance")] + \
                     [("flights", "seq", FLIGHT_KEYS), ("passengers", "seq", PASSENGER_KEYS),
                      ("payment_history", "payments", None)]
USER_FIELDS = [("user_id", "scalar", None), ("membership", "scalar", None),
               ("payment_methods", "payment_dict", None), ("reservations", "set", None)]

_MISSING = object()


def _norm(v: Any) -> Any:
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return v.strip().lower()
    return json.dumps(v, sort_keys=True)


def _value(obj: dict, name: str, kind: str, keys):
    raw = obj.get(name, _MISSING) if isinstance(obj, dict) else _MISSING
    if raw is _MISSING:
        return _MISSING
    if kind == "scalar":
        return _norm(raw)
    if kind == "seq":
        return tuple(tuple(_norm(item.get(k)) if isinstance(item, dict) else _norm(item) for k in keys)
                     for item in (raw or []))
    if kind == "payments":   # tolerate the 'id' / 'payment_id' key variants seen in agent calls
        return tuple(sorted((_norm(p.get("payment_id", p.get("id"))), _norm(p.get("amount")))
                            for p in (raw or []) if isinstance(p, dict)))
    if kind == "payment_dict":
        return tuple(sorted((_norm(k), _norm((v or {}).get("amount"))) for k, v in (raw or {}).items()))
    if kind == "set":
        return tuple(sorted(_norm(x) for x in (raw or [])))
    raise ValueError(kind)


def _compare(prefix: str, a: dict, b: dict, specs) -> list[str]:
    out = []
    for name, kind, keys in specs:
        va, vb = _value(a, name, kind, keys), _value(b, name, kind, keys)
        if va is _MISSING and vb is _MISSING:
            continue
        if va is _MISSING or vb is _MISSING:
            out.append(f"{prefix}.{name}: present in only one ({'query' if vb is _MISSING else 'reference'})")
        elif va != vb:
            out.append(f"{prefix}.{name}: {_show(va)} != {_show(vb)}")
    return out


def _show(v) -> str:
    s = repr(v)
    return s if len(s) <= 120 else s[:117] + "..."


def _record_type(obs: Any) -> str | None:
    if isinstance(obs, dict) and "reservation_id" in obs and "flights" in obs:
        return "reservation"
    if isinstance(obs, dict) and "user_id" in obs and "payment_methods" in obs:
        return "user"
    return None


@dataclass
class FieldCheck:
    compatible: bool
    hard: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)


def compare_tool_events(a: dict, b: dict) -> FieldCheck:
    """a, b: AgentStep nodes of kind 'tool_call' from step graphs (query, reference)."""
    hard: list[str] = []
    name_a, name_b = a["tool_call"]["name"], b["tool_call"]["name"]
    args_a, args_b = a["tool_call"]["arguments"] or {}, b["tool_call"]["arguments"] or {}
    if name_a != name_b:
        return FieldCheck(False, [f"tool_name: {name_a!r} != {name_b!r}"])
    specs = CALL_FIELDS.get(name_a, [])
    hard += _compare("args", args_a, args_b, specs)
    covered = {s[0] for s in specs}
    ignored = [f"args.{k}" for k in sorted(set(args_a) | set(args_b))
               if k not in covered and _norm(args_a.get(k)) != _norm(args_b.get(k))]

    oa, ob = a["observation"], b["observation"]
    if bool(oa["error"]) != bool(ob["error"]):
        hard.append(f"result.error: {bool(oa['error'])} != {bool(ob['error'])}")
    elif not oa["error"]:
        pa, pb = oa.get("content_parsed"), ob.get("content_parsed")
        ta, tb = _record_type(pa), _record_type(pb)
        if ta and ta == tb:
            hard += _compare("result", pa, pb, RESERVATION_FIELDS if ta == "reservation" else USER_FIELDS)
        elif ta != tb and (ta or tb):
            hard.append(f"result.record_type: {ta} != {tb}")
    return FieldCheck(not hard, hard, ignored)


class StructuredFieldValidator:
    """Callable used by `find_mcs(..., field_check=...)`. Returns the list of hard-incompatibility reasons
    for a candidate edge pair (empty list = compatible). Checks the target node pair and, when both are tool
    results, the source node pair."""

    def __init__(self, query_steps: dict, reference_steps: dict):
        self.q = {n["id"]: n for n in query_steps["nodes"]}
        self.r = {n["id"]: n for n in reference_steps["nodes"]}
        self._memo: dict[tuple[str, str], FieldCheck] = {}

    def event_check(self, ev_q: str, ev_r: str) -> FieldCheck:
        key = (ev_q, ev_r)
        if key not in self._memo:
            self._memo[key] = compare_tool_events(self.q[ev_q], self.r[ev_r])
        return self._memo[key]

    def __call__(self, g1, g2, e1: dict, e2: dict) -> list[str]:
        reasons = []
        for role, n1, n2 in (("target", e1["dst"], e2["dst"]), ("source", e1["src"], e2["src"])):
            a, b = g1.nodes[n1], g2.nodes[n2]
            if a["kind"] == b["kind"] == "tool_result":
                chk = self.event_check(a["event"], b["event"])
                reasons += [f"{role} {a['event']}~{b['event']}: {r}" for r in chk.hard]
        return reasons
