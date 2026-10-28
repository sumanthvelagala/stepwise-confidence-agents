"""Configuration C (structured-field validation, OUR adaptation): unit tests on real and synthetic tool events."""
import pytest

from gibs.graph.event_projection import project
from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.mcs.consensus import consensus_masks
from gibs.mcs.mcs import MCSConfig, find_mcs
from gibs.mcs.nli import Similarity, StubEntailment
from gibs.mcs.structured_fields import StructuredFieldValidator, compare_tool_events
from gibs.tests.helpers import REPO, TASK48_FAILURE, TASK48_FILE, TASK48_SUCCESS, make_sim

T40 = REPO / "results/probe/new_batch2/results.json"
T4 = REPO / "results/probe/task_4/results.json"


def step(g, sid):
    return next(n for n in g["nodes"] if n["id"] == sid)


def tool_step(name, args, obs, error=False):
    g = build_step_graph(make_sim([("call", name, args, obs, error)]))
    return g["nodes"][0]


RES = {"reservation_id": "ABC123", "user_id": "u_1", "origin": "JFK", "destination": "SFO", "flight_type": "one_way",
       "cabin": "economy", "flights": [{"flight_number": "HAT001", "date": "2024-05-20", "price": 100}],
       "passengers": [{"first_name": "A", "last_name": "B", "dob": "1990-01-01"}],
       "payment_history": [{"payment_id": "gift_card_1", "amount": 100}], "created_at": "2024-05-01T10:00:00",
       "total_baggages": 0, "nonfree_baggages": 0, "insurance": "no", "status": None}


# ------------------------------------------------------------------ real trajectories
def test_t40_update_with_conflicting_dob_is_hard_incompatible():
    q = build_step_graph(*load_simulation(str(T40), "b4901df6"))
    r = build_step_graph(*load_simulation(str(T40), "f6000fbe"))
    chk = compare_tool_events(step(q, "s10"), step(r, "s8"))
    assert not chk.compatible
    assert any(h.startswith("args.passengers:") and "1992-07-15" in h and "1989-12-13" in h for h in chk.hard)
    assert any(h.startswith("result.passengers:") for h in chk.hard)


def test_t40_identical_lookups_are_compatible():
    q = build_step_graph(*load_simulation(str(T40), "b4901df6"))
    r = build_step_graph(*load_simulation(str(T40), "f6000fbe"))
    assert compare_tool_events(step(q, "s8"), step(r, "s6")).compatible


def test_t48_cancel_vs_lookup_rejected_on_tool_name():
    q = build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_FAILURE))
    r = build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_SUCCESS))
    chk = compare_tool_events(step(q, "s6"), step(r, "s4"))
    assert chk.hard == ["tool_name: 'cancel_reservation' != 'get_reservation_details'"]


def test_t4_user_record_after_certificate_conflicts_on_payment_methods():
    q = build_step_graph(*load_simulation(str(T4), "259d9890"))
    r = build_step_graph(*load_simulation(str(T4), "ce8b1b6b"))
    assert compare_tool_events(step(q, "s4"), step(r, "s2")).compatible          # before the certificate
    late = compare_tool_events(step(q, "s24"), step(r, "s2"))                    # after send_certificate
    assert not late.compatible and any(h.startswith("result.payment_methods") for h in late.hard)


# ------------------------------------------------------------------ ordinary differences are not rejected
def test_free_text_summary_is_an_ordinary_difference():
    a = tool_step("transfer_to_human_agents", {"summary": "User wants a refund."}, "Transfer successful")
    b = tool_step("transfer_to_human_agents", {"summary": "Customer asks to appeal."}, "Transfer successful")
    chk = compare_tool_events(a, b)
    assert chk.compatible and chk.ignored == ["args.summary"]


def test_flight_price_and_payment_key_variants_are_ignored():
    base = {"user_id": "u_1", "origin": "JFK", "destination": "SFO", "flight_type": "one_way", "cabin": "economy",
            "passengers": [{"first_name": "A", "last_name": "B", "dob": "1990-01-01"}], "total_baggages": 0,
            "nonfree_baggages": 0, "insurance": "no"}
    a = tool_step("book_reservation", {**base, "flights": [{"flight_number": "HAT001", "date": "2024-05-20", "price": 99}],
                                       "payment_methods": [{"payment_id": "gift_card_1", "amount": 50},
                                                           {"payment_id": "credit_card_2", "amount": 49}]}, RES)
    b = tool_step("book_reservation", {**base, "flights": [{"flight_number": "HAT001", "date": "2024-05-20"}],
                                       "payment_methods": [{"id": "credit_card_2", "amount": 49},
                                                           {"id": "gift_card_1", "amount": 50}]}, RES)
    assert compare_tool_events(a, b).compatible


def test_different_search_results_are_not_hard_incompatible():
    a = tool_step("search_direct_flight", {"origin": "JFK", "destination": "SFO", "date": "2024-05-20"}, [{"flight_number": "HAT001"}])
    b = tool_step("search_direct_flight", {"origin": "JFK", "destination": "SFO", "date": "2024-05-20"}, [])
    assert compare_tool_events(a, b).compatible


@pytest.mark.parametrize("change,field", [
    ({"status": "cancelled"}, "result.status"),
    ({"flights": [{"flight_number": "HAT002", "date": "2024-05-20"}]}, "result.flights"),
    ({"created_at": "2024-05-14T09:00:00"}, "result.created_at"),
])
def test_reservation_record_critical_fields(change, field):
    a = tool_step("get_reservation_details", {"reservation_id": "ABC123"}, RES)
    b = tool_step("get_reservation_details", {"reservation_id": "ABC123"}, {**RES, **change})
    chk = compare_tool_events(a, b)
    assert not chk.compatible and chk.hard[0].startswith(field)


def test_error_status_and_identifier_conflicts():
    ok = tool_step("get_reservation_details", {"reservation_id": "ABC123"}, RES)
    err = tool_step("get_reservation_details", {"reservation_id": "ABC123"}, "Error: not found", True)
    other = tool_step("get_reservation_details", {"reservation_id": "XYZ999"}, {**RES, "reservation_id": "XYZ999"})
    assert compare_tool_events(ok, err).hard == ["result.error: False != True"]
    assert compare_tool_events(ok, other).hard[0] == "args.reservation_id: 'abc123' != 'xyz999'"


# ------------------------------------------------------------------ integration with MCS
def graph_and_steps(events, sim_id):
    s = build_step_graph(make_sim(events, sim_id=sim_id))
    return s, project(s)


LOOKUP = lambda status: ("call", "get_reservation_details", {"reservation_id": "ABC123"}, {**RES, "status": status})


def test_C_rejects_nli_equivalent_observations_with_conflicting_status_and_records_reason():
    qs, q = graph_and_steps([("agent", "Hi"), ("user", "Check ABC123."), LOOKUP("cancelled")], "q")
    rs, r = graph_and_steps([("agent", "Hi"), ("user", "Check ABC123."), LOOKUP(None)], "r")
    stub = StubEntailment(default=0.95)          # NLI says everything is equivalent (as observed for long JSON)
    base = find_mcs(q, r, Similarity(stub))
    assert "N:s2" in base.node_map
    c = find_mcs(q, r, Similarity(stub), field_check=StructuredFieldValidator(qs, rs))
    assert "N:s2" not in c.node_map
    assert c.rejected and "result.status: 'cancelled' != None" in c.rejected[0]["reasons"][0]


def test_C_without_field_check_is_identical_to_baseline():
    qs, q = graph_and_steps([("agent", "Hi"), ("user", "Check ABC123."), LOOKUP(None)], "q")
    rs, r = graph_and_steps([("agent", "Hi"), ("user", "Check ABC123."), LOOKUP(None)], "r")
    a = find_mcs(q, r, Similarity(StubEntailment()))
    b = find_mcs(q, r, Similarity(StubEntailment()), field_check=StructuredFieldValidator(qs, rs))
    assert (a.node_map, a.edge_map, a.size) == (b.node_map, b.edge_map, b.size) and not b.rejected


def test_C_keeps_the_contradictory_instruction_behaviour():
    cancel = ("call", "cancel_reservation", {"reservation_id": "ABC123"}, {**RES, "status": "cancelled"})
    yes, no = "Yes, please cancel it.", "No, do not cancel it."
    events = lambda conf: [("agent", "Hi"), ("user", "Please look at reservation ABC123."),
                           ("agent", "Shall I cancel reservation ABC123?"), ("user", conf), cancel, ("agent", "Done.")]
    qs, q = graph_and_steps(events(no), "q")
    rs, r = graph_and_steps(events(yes), "r")
    sim = Similarity(StubEntailment({(yes, no): 0.02, (no, yes): 0.02}))
    m = consensus_masks(q, [find_mcs(q, r, sim, MCSConfig(), field_check=StructuredFieldValidator(qs, rs))])
    assert m["s4"]["m_node"] == 1.0 and m["s4"]["m_ctx"] == 0.0     # identical call: fields agree, context does not
