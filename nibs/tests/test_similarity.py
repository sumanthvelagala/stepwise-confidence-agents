"""Tests for similarity/similarity.py — no API or model downloads."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from similarity.similarity import tool_sim, text_sim, hybrid_sim


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def step(tool=None, args=None, thought=None):
    return {"tool": tool, "args": args or {}, "thought": thought, "scored": True}


def exact_match(a: str, b: str) -> float:
    """Mock text backend: 1.0 if equal, 0.0 otherwise."""
    return 1.0 if a == b else 0.0


def always_half(_a: str, _b: str) -> float:
    return 0.5


# ---------------------------------------------------------------------------
# tool_sim
# ---------------------------------------------------------------------------

def test_tool_sim_same_tool_same_args():
    a = step("cancel_reservation", {"reservation_id": "r1"})
    b = step("cancel_reservation", {"reservation_id": "r1"})
    assert tool_sim(a, b) == 1.0


def test_tool_sim_same_tool_different_args():
    a = step("cancel_reservation", {"reservation_id": "r1"})
    b = step("cancel_reservation", {"reservation_id": "r2"})
    assert tool_sim(a, b) == 0.0


def test_tool_sim_same_tool_partial_args():
    # 2 keys total, 1 matches
    a = step("book_flight", {"origin": "jfk", "destination": "lax"})
    b = step("book_flight", {"origin": "jfk", "destination": "sfo"})
    assert tool_sim(a, b) == 0.5


def test_tool_sim_different_tools():
    a = step("cancel_reservation", {"reservation_id": "r1"})
    b = step("get_user_details",   {"user_id": "alice"})
    assert tool_sim(a, b) == 0.0


def test_tool_sim_both_no_tool():
    a = step(None, {}, "Hello!")
    b = step(None, {}, "Hi there!")
    assert tool_sim(a, b) == 1.0


def test_tool_sim_one_no_tool():
    a = step(None, {})
    b = step("cancel_reservation", {"reservation_id": "r1"})
    assert tool_sim(a, b) == 0.0


def test_tool_sim_same_tool_no_args():
    a = step("ping", {})
    b = step("ping", {})
    assert tool_sim(a, b) == 1.0


def test_tool_sim_extra_key_in_one():
    # union = 2 keys, 1 matches (shared key), other key only in one
    a = step("f", {"x": "1", "y": "2"})
    b = step("f", {"x": "1"})
    assert tool_sim(a, b) == 0.5


# ---------------------------------------------------------------------------
# text_sim with mock backend
# ---------------------------------------------------------------------------

def test_text_sim_callable_backend_match():
    assert text_sim("hello", "hello", backend=exact_match) == 1.0


def test_text_sim_callable_backend_no_match():
    assert text_sim("hello", "world", backend=exact_match) == 0.0


def test_text_sim_empty_string_a():
    assert text_sim("", "hello", backend=exact_match) == 0.0


def test_text_sim_none_a():
    assert text_sim(None, "hello", backend=exact_match) == 0.0


def test_text_sim_both_empty():
    assert text_sim("", "", backend=exact_match) == 0.0


def test_text_sim_unknown_backend_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown text_sim backend"):
        text_sim("a", "b", backend="unknown")


# ---------------------------------------------------------------------------
# hybrid_sim
# ---------------------------------------------------------------------------

def test_hybrid_sim_alpha_1_equals_tool_sim():
    a = step("cancel_reservation", {"reservation_id": "r1"}, thought="please cancel")
    b = step("cancel_reservation", {"reservation_id": "r1"}, thought="different text")
    assert hybrid_sim(a, b, alpha=1.0, text_backend=exact_match) == tool_sim(a, b)


def test_hybrid_sim_alpha_0_equals_text_sim():
    a = step(None, {}, thought="same text")
    b = step(None, {}, thought="same text")
    result = hybrid_sim(a, b, alpha=0.0, text_backend=exact_match)
    assert result == 1.0


def test_hybrid_sim_blends_correctly():
    # tool_sim = 1.0 (same tool + args), text_sim = 0.5 (mock always_half)
    # alpha=0.7 → 0.7*1.0 + 0.3*0.5 = 0.85
    a = step("cancel_reservation", {"reservation_id": "r1"}, thought="text a")
    b = step("cancel_reservation", {"reservation_id": "r1"}, thought="text b")
    result = hybrid_sim(a, b, alpha=0.7, text_backend=always_half)
    assert abs(result - 0.85) < 1e-9


def test_hybrid_sim_no_thought_falls_back_to_tool_sim():
    a = step("cancel_reservation", {"reservation_id": "r1"})
    b = step("cancel_reservation", {"reservation_id": "r1"})
    result = hybrid_sim(a, b, alpha=0.7, text_backend=exact_match)
    assert result == tool_sim(a, b)


def test_hybrid_sim_different_tools_no_thought():
    a = step("cancel_reservation", {"reservation_id": "r1"})
    b = step("get_user_details",   {"user_id": "alice"})
    result = hybrid_sim(a, b, alpha=0.7, text_backend=always_half)
    # tool_sim=0.0, no thought → returns 0.0
    assert result == 0.0
