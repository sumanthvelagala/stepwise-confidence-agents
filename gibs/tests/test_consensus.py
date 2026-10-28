"""R6: the paper's node-level target vs our context-aware step-level target under contradictory user instructions."""
import pytest

from gibs.graph.event_projection import project
from gibs.graph.step_graph import build_step_graph
from gibs.mcs.consensus import consensus_masks, pair_indicators
from gibs.mcs.mcs import MCSConfig, find_mcs
from gibs.mcs.nli import Similarity, StubEntailment
from gibs.tests.helpers import make_sim

CANCEL = ("call", "cancel_reservation", {"reservation_id": "ABC123"}, {"reservation_id": "ABC123", "status": "cancelled"})


def trajectory(confirmation, sim_id):
    return project(build_step_graph(make_sim([
        ("agent", "Hi! How can I help?"),
        ("user", "Please look at reservation ABC123."),
        ("agent", "Shall I cancel reservation ABC123?"),
        ("user", confirmation),
        CANCEL,                                            # identical call, identical observation
        ("agent", "The reservation is cancelled."),
    ], sim_id=sim_id)))


YES, NO = "Yes, please cancel it.", "No, do not cancel it."
TABLE = {(YES, NO): 0.02, (NO, YES): 0.02}                 # contradiction: low entailment both ways


def masks(query, refs, **cfg):
    sim = Similarity(StubEntailment(TABLE))
    return consensus_masks(query, [find_mcs(query, r, sim, MCSConfig(**cfg)) for r in refs])


def test_contradictory_instruction_paper_node_level_still_supports_the_cancel():
    q, ref = trajectory(NO, "query"), trajectory(YES, "ref")
    m = masks(q, [ref])
    assert m["s4"]["m_node"] == 1.0          # result node mapped via the data edge from the ID turn


def test_contradictory_instruction_context_step_level_does_not_support_the_cancel():
    q, ref = trajectory(NO, "query"), trajectory(YES, "ref")
    m = masks(q, [ref])
    assert m["s4"]["m_ctx"] == 0.0           # context edge from "No, do not cancel" cannot match
    assert m["s2"]["m_ctx"] == 1.0           # the confirmation request itself is not blamed


def test_consistent_instruction_supports_the_cancel_under_both_targets():
    q, ref = trajectory(YES, "query"), trajectory(YES, "ref")
    m = masks(q, [ref])
    assert m["s4"]["m_node"] == m["s4"]["m_ctx"] == 1.0


def test_author_code_source_rule_cannot_detect_the_contradiction():
    q, ref = trajectory(NO, "query"), trajectory(YES, "ref")
    m = masks(q, [ref], check_source_nodes=False)
    assert m["s4"]["m_ctx"] == 1.0           # documents why R3 (source-node threshold) is needed


def test_masks_average_over_references():
    q = trajectory(NO, "query")
    m = masks(q, [trajectory(YES, "r1"), trajectory(NO, "r2")])
    assert m["s4"]["m_ctx"] == 0.5 and m["s4"]["n_references"] == 2


def test_user_turns_receive_no_targets():
    q = trajectory(NO, "query")
    m = masks(q, [trajectory(YES, "ref")])
    assert set(m) == {"s0", "s2", "s4", "s6"}


def test_results_must_share_the_query():
    q, other = trajectory(NO, "query"), trajectory(YES, "other")
    sim = Similarity(StubEntailment(TABLE))
    with pytest.raises(ValueError):
        consensus_masks(q, [find_mcs(other, q, sim)])
    assert pair_indicators(q, find_mcs(q, other, sim))["s4"]["incoming_edges"]
