"""C5 (OUR adaptation): two-stage constrained matching. Stage 1 = frozen C4 tool part; stage 2 = agent messages via
their context edge. Real-trajectory tests read benchmark files; synthetic tests use `make_sim`. A permissive NLI stub
(every pair 0.99) isolates the structural rules from the model."""
import pytest

from gibs.graph.event_projection import ROOT, project
from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.mcs.consensus import pair_indicators
from gibs.mcs.nli import Similarity, StubEntailment
from gibs.mcs.structured_fields import StructuredFieldValidator
from gibs.mcs.two_stage import extend_messages, freeze_tool_part, project_c5
from gibs.tests.helpers import REPO, TASK48_FILE, TASK48_SUCCESS, make_sim
from gibs.validation.run_c4 import C4

T25_FAIL = REPO / "results/probe/new_batch1/results.json"         # 6f12b024: wrong booking s30, confirmation s32
T25_OK = REPO / "results/pilot/task_25_topup/results.json"        # 0f0f7358: gold booking


def sim(default=0.99, table=None):
    return Similarity(StubEntailment(table=table, default=default), direction="max_bidirectional")


def run_c5(qg, rg, s):
    """C4 (stage 1, computed here) then C5 stage 2; returns the C4 and C5 projections and results."""
    q4, r4 = project(qg, C4["topology"]), project(rg, C4["topology"])
    res4 = C4["matcher"](q4, r4, s, C4["mcs"], field_check=StructuredFieldValidator(qg, rg))
    fv, fe = freeze_tool_part(q4, res4.node_map, res4.edge_map)
    q5, r5 = project_c5(qg), project_c5(rg)
    res5 = extend_messages(q5, r5, s, fv, fe, C4["mcs"], field_check=StructuredFieldValidator(qg, rg))
    return q4, res4, q5, r5, res5


def tool_indicators(g, res):
    return {ev: (x["node_level"], x["context_step_level"]) for ev, x in pair_indicators(g, res).items()
            if g.nodes[x["node"]]["kind"] == "tool_result"}


# ------------------------------------------------------------------ projection
@pytest.mark.parametrize("path,prefix", [(TASK48_FILE, TASK48_SUCCESS), (T25_FAIL, "6f12b024"), (T25_OK, "0f0f7358")])
def test_c5_projection_tool_and_user_edges_equal_c4_messages_have_one_context_edge(path, prefix):
    sg = build_step_graph(*load_simulation(str(path), prefix))
    g4, g5 = project(sg, "paper_literal"), project_c5(sg)
    kind = {n: d["kind"] for n, d in g5.nodes.items()}
    non_msg = lambda g: sorted((e["id"], tuple(e["roles"]), e["text"]) for e in g.edges
                               if kind[e["dst"]] != "agent_message")
    assert non_msg(g4) == non_msg(g5)
    order = list(g5.nodes)
    for nid, k in kind.items():
        if k != "agent_message":
            continue
        ins = g5.in_edges(nid)
        assert len(ins) == 1
        expected_src = order[order.index(nid) - 1]                    # predecessor, or ROOT for the first event
        assert ins[0]["src"] == expected_src
        assert (ins[0]["src"] == ROOT) == (order.index(nid) == 1)     # ROOT only for the first event


# ------------------------------------------------------------------ tool invariance (real pair, permissive NLI)
def test_c5_tool_maps_and_tool_scores_identical_to_c4_on_real_t25_pair():
    qg = build_step_graph(*load_simulation(str(T25_FAIL), "6f12b024"))
    rg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    q4, res4, q5, r5, res5 = run_c5(qg, rg, sim())
    assert tool_indicators(q4, res4) == tool_indicators(q5, res5)
    tool_nodes = {n for n, d in q4.nodes.items() if d["kind"] == "tool_result"}
    assert {n: m for n, m in res4.node_map.items() if n in tool_nodes} == \
           {n: m for n, m in res5.node_map.items() if n in tool_nodes}
    tool_edges = {e["id"] for e in q4.edges if e["dst"] in tool_nodes}
    assert {e: m for e, m in res4.edge_map.items() if e in tool_edges} == \
           {e: m for e, m in res5.edge_map.items() if e in tool_edges}


def test_c5_message_constraints_do_not_lower_correct_tool_consensus():
    # identical runs: every tool call matches in C4; adding stage 2 must leave all tool indicators True
    sg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    q4, res4, q5, _, res5 = run_c5(sg, sg, sim(default=0.0))      # identical texts only (stub: identical -> 1)
    t4, t5 = tool_indicators(q4, res4), tool_indicators(q5, res5)
    assert t4 == t5 and all(a and b for a, b in t5.values())


# ------------------------------------------------------------------ injectivity and context consistency
def test_c5_message_mappings_injective_and_context_consistent():
    qg = build_step_graph(*load_simulation(str(T25_FAIL), "6f12b024"))
    rg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    _, res4, q5, r5, res5 = run_c5(qg, rg, sim())
    vals = list(res5.node_map.values())
    assert len(vals) == len(set(vals))
    assert len(res5.edge_map.values()) == len(set(res5.edge_map.values()))
    fv, _ = freeze_tool_part(project(qg, "paper_literal"), res4.node_map, res4.edge_map)
    by1, by2 = {e["id"]: e for e in q5.edges}, {e["id"]: e for e in r5.edges}
    for e1, e2 in res5.edge_map.items():
        a, b = by1[e1], by2[e2]
        if q5.nodes[a["dst"]]["kind"] == "agent_message":
            assert r5.nodes[b["dst"]]["kind"] == "agent_message"
            if q5.nodes[a["src"]]["kind"] == "tool_result":
                assert fv.get(a["src"]) == b["src"]


def test_c5_t25_wrong_booking_confirmation_not_context_supported_even_with_permissive_nli():
    qg = build_step_graph(*load_simulation(str(T25_FAIL), "6f12b024"))
    rg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    _, res4, q5, _, res5 = run_c5(qg, rg, sim())
    assert "N:s30" not in res4.node_map                       # the wrong booking is rejected in stage 1
    ind = pair_indicators(q5, res5)["s32"]
    assert not ind["context_step_level"] and not ind["node_level"]
    # the s30 -> s32 candidate is removed either by the field check on the source tool pair or by the tool-source rule
    assert any(r["e1"] == "N:s30->N:s32" for r in res5.rejected) or res5.stage2_stats["dropped_tool_unmatched"] > 0


# ------------------------------------------------------------------ synthetic handling rules
def _sg(events, sid):
    return build_step_graph(make_sim(events, sid))


def test_c5_message_after_unmatched_tool_gets_no_context_support():
    # same call name, conflicting booking args -> tool unmatched in stage 1 -> the following confirmation is unsupported
    book = lambda d: {"user_id": "u_1", "origin": "DTW", "destination": "SEA", "flight_type": "one_way",
                      "cabin": "economy", "flights": [{"flight_number": "HAT097", "date": d}],
                      "passengers": [{"first_name": "I", "last_name": "S", "dob": "1986-03-14"}],
                      "payment_methods": [{"payment_id": "gc_1", "amount": 100}], "total_baggages": 0,
                      "nonfree_baggages": 0, "insurance": "no"}
    q = _sg([("agent", "Hi!"), ("user", "Book it."), ("call", "book_reservation", book("2024-05-21"), {"ok": 1}),
             ("agent", "Booking confirmed!")], "q")
    r = _sg([("agent", "Hi!"), ("user", "Book it."), ("call", "book_reservation", book("2024-05-17"), {"ok": 1}),
             ("agent", "Booking confirmed!")], "r")
    _, res4, q5, _, res5 = run_c5(q, r, sim())
    assert "N:s2" not in res4.node_map
    assert not pair_indicators(q5, res5)["s4"]["context_step_level"]       # s2 = call (+ observation), s4 = message
    assert pair_indicators(q5, res5)["s0"]["context_step_level"]                  # first message: ROOT <-> ROOT


def test_c5_message_after_user_turn_requires_predecessor_match_and_first_message_only_matches_first():
    q = _sg([("agent", "Hi!"), ("user", "Cancel my trip."), ("agent", "Sure.")], "q")
    r = _sg([("agent", "Hello."), ("user", "Change my seat."), ("agent", "Sure.")], "r")
    # only identical strings entail (default 0): predecessor user turns differ -> 'Sure.' unsupported
    _, _, q5, _, res5 = run_c5(q, r, sim(default=0.0))
    assert not pair_indicators(q5, res5)["s2"]["context_step_level"]
    # a first message never maps to a non-first message, even if texts are identical
    q2 = _sg([("agent", "Sure."), ("user", "x")], "q2")
    r2 = _sg([("agent", "Hi!"), ("user", "y"), ("agent", "Sure.")], "r2")
    _, _, qq, _, rr = run_c5(q2, r2, sim(default=0.0))
    assert "N:s0" not in rr.node_map


def test_c5_tool_source_rule_alone_blocks_message_after_unmatched_transfer():
    # transfer summaries differ (NLI 0) -> the transfer call is unmatched in stage 1; the transfer results and the
    # policy message are identical, so only the tool-source rule removes the message candidate
    msg = "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."
    q = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "wants a refund"}, "Transfer successful"),
             ("agent", msg)], "q")
    r = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "appeal decision"}, "Transfer successful"),
             ("agent", msg)], "r")
    _, res4, q5, _, res5 = run_c5(q, r, sim(default=0.0))
    assert "N:s1" not in res4.node_map
    assert res5.stage2_stats["dropped_tool_unmatched"] == 1 and not res5.rejected
    assert not pair_indicators(q5, res5)["s3"]["context_step_level"]
    # with matching summaries the same message is context-supported
    r2 = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "wants a refund"}, "Transfer successful"),
              ("agent", msg)], "r2")
    _, _, q5b, _, res5b = run_c5(q, r2, sim(default=0.0))
    assert pair_indicators(q5b, res5b)["s3"]["context_step_level"]
