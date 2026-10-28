"""C6 (OUR adaptation): C5 + stage-3 outcome route (gibs/validation/c6_plan.md). Outcome agreement is NOT evidence that
the tool action was correct. Real-trajectory tests read benchmark files; synthetic tests use `make_sim`; stub NLI only."""
import json

from gibs.graph.event_projection import project
from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.mcs.consensus import pair_indicators
from gibs.mcs.nli import Similarity, StubEntailment
from gibs.mcs.structured_fields import StructuredFieldValidator
from gibs.mcs.two_stage import extend_messages, freeze_tool_part, outcome_key, project_c5
from gibs.tests.helpers import REPO, TASK48_FILE, make_sim
from gibs.validation.run_c4 import C4

T25_FAIL = REPO / "results/probe/new_batch1/results.json"
T25_OK = REPO / "results/pilot/task_25_topup/results.json"
MSG = "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."


def sim(default=0.0, table=None):
    return Similarity(StubEntailment(table=table, default=default), direction="max_bidirectional")


def run(qg, rg, s):
    """Stage 1 from a C4 match computed here; returns C4, C5 and C6 results on their projections."""
    q4, r4 = project(qg, C4["topology"]), project(rg, C4["topology"])
    res4 = C4["matcher"](q4, r4, s, C4["mcs"], field_check=StructuredFieldValidator(qg, rg))
    fv, fe = freeze_tool_part(q4, res4.node_map, res4.edge_map)
    q5, r5 = project_c5(qg), project_c5(rg)
    kw = dict(cfg=C4["mcs"], field_check=StructuredFieldValidator(qg, rg))
    res5 = extend_messages(q5, r5, s, fv, fe, **kw)
    res6 = extend_messages(q5, r5, s, fv, fe, outcome_route=True, query_steps=qg, reference_steps=rg, **kw)
    return q4, res4, q5, res5, res6


def ind(g, res, kind=None):
    return {ev: (x["node_level"], x["context_step_level"]) for ev, x in pair_indicators(g, res).items()
            if kind is None or g.nodes[x["node"]]["kind"] == kind}


def _sg(events, sid):
    return build_step_graph(make_sim(events, sid))


# ------------------------------------------------------------------ normalization
def test_outcome_key_normalization_and_strictness():
    step = lambda obs, err=False: _sg([("call", "t", {}, obs, err)], "x")["nodes"][0]
    assert outcome_key(step({"a": 1, "b": " x  y "})) == outcome_key(step('{"b": "x y", "a": 1.0}'))   # order/ws/num
    assert outcome_key(step([])) == outcome_key(step("[]"))
    assert outcome_key(step("Transfer successful")) == outcome_key(step("Transfer  successful "))
    assert outcome_key(step("Error: User ? not found", True)) != outcome_key(step("Error: User user123 not found", True))
    assert outcome_key(step("x", True)) != outcome_key(step("x", False))                          # error status kept
    assert outcome_key(step({"price": 1})) != outcome_key(step({"price": 2}))                      # full result


# ------------------------------------------------------------------ real T48 transfer (summaries differ)
def test_c6_recovers_transfer_message_without_new_tool_match_and_keeps_c5():
    qg = build_step_graph(*load_simulation(str(TASK48_FILE), "59810305"))
    rg = build_step_graph(*load_simulation(str(TASK48_FILE), "c890f90b"))
    q4, res4, q5, res5, res6 = run(qg, rg, sim())          # only identical strings entail
    assert "N:s4" not in res4.node_map                       # transfer call unmatched (different summaries)
    assert not ind(q5, res5)["s6"][1] and ind(q5, res6)["s6"][1]
    assert res6.outcome_route_edges == ["N:s4->N:s6"] and res6.outcome_alignments == {"N:s4": "N:s8"}
    # tool scores and maps identical to C4; outcome-aligned tool node is not a tool match
    assert ind(q4, res4, "tool_result") == ind(q5, res5, "tool_result") == ind(q5, res6, "tool_result")
    assert "N:s4" not in res6.node_map
    # every C5 mapping retained unchanged
    assert all(res6.node_map[k] == v for k, v in res5.node_map.items())
    assert all(res6.edge_map[k] == v for k, v in res5.edge_map.items())


# ------------------------------------------------------------------ guards
def test_c6_empty_search_with_conflicting_arguments_is_not_outcome_supported():
    s = lambda d, sid: _sg([("agent", "Hi!"), ("call", "search_direct_flight",
                                               {"origin": "JFK", "destination": "MCO", "date": d}, []),
                            ("agent", "No direct flights are available.")], sid)
    _, _, q5, _, res6 = run(s("2024-05-22", "q"), s("2024-05-23", "r"), sim(default=0.99))   # permissive NLI
    assert not ind(q5, res6)["s3"][1] and not res6.outcome_route_edges


def test_c6_semantically_similar_but_unequal_outcomes_are_rejected():
    # results entail each other (stub 0.99) but differ textually -> outcome route must reject
    q = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "a"}, "Transfer successful"),
             ("agent", MSG)], "q")
    r = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "b"}, "Transfer completed"),
             ("agent", MSG)], "r")
    table = {("Tool result: Transfer successful.", "Tool result: Transfer completed."): 0.99}
    _, _, q5, _, res6 = run(q, r, sim(table=table))
    assert not ind(q5, res6)["s3"][1]
    assert res6.stage2_stats["outcome_rejected_outcome_differs"] >= 1 or res6.stage2_stats["outcome_candidates"] == 0


def test_c6_error_outcomes_need_identical_error_text():
    mk = lambda uid, err_txt, sid: _sg([("agent", "Hi!"), ("call", "get_user_details", {"user_id": uid}, err_txt, True),
                                        ("agent", "Could you share your user ID?")], sid)
    _, _, q5, _, res6 = run(mk("?", "Error: User ? not found", "q"), mk("?", "Error: lookup failed", "r"),
                            sim(default=0.99))
    assert not res6.outcome_route_edges


def test_c6_outcome_alignment_is_injective():
    q = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "a"}, "Transfer successful"),
             ("agent", MSG), ("user", "ok"),
             ("call", "transfer_to_human_agents", {"summary": "b"}, "Transfer successful"), ("agent", MSG)], "q")
    r = _sg([("agent", "Hi!"), ("call", "transfer_to_human_agents", {"summary": "z"}, "Transfer successful"),
             ("agent", MSG)], "r")
    _, _, q5, _, res6 = run(q, r, sim())
    assert len(res6.outcome_alignments) == 1 and len(set(res6.outcome_alignments.values())) == 1
    assert sum(ind(q5, res6)[m][1] for m in ("s3", "s7")) == 1   # messages s3, s7 (each call spans 2 indices)
    vals = list(res6.node_map.values())
    assert len(vals) == len(set(vals)) and len(set(res6.edge_map.values())) == len(res6.edge_map)


def test_c6_t25_wrong_booking_confirmation_stays_unsupported_with_permissive_nli():
    qg = build_step_graph(*load_simulation(str(T25_FAIL), "6f12b024"))
    rg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    q4, res4, q5, res5, res6 = run(qg, rg, sim(default=0.99))
    assert ind(q5, res6)["s32"] == (False, False)
    assert ind(q4, res4, "tool_result") == ind(q5, res6, "tool_result")
    assert all(not e.endswith("->N:s32") for e in res6.outcome_route_edges)
    json.dumps(res6.outcome_alignments)                     # serializable
