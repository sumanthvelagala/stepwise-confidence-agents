"""C4 (OUR adaptation): C3 matching on the paper-literal projection. Edge construction and structured-field safety.

Real-trajectory tests read benchmark files; synthetic tests build small graphs with `make_sim` and a stub NLI that
accepts every pair, so only the structured-field check can prevent a match.
"""
import pytest

from gibs.graph.event_projection import ROOT, project
from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.mcs.consensus import pair_indicators
from gibs.mcs.nli import Similarity, StubEntailment
from gibs.mcs.structured_fields import StructuredFieldValidator
from gibs.tests.helpers import REPO, TASK48_FILE, TASK48_SUCCESS, make_sim
from gibs.validation.run_c4 import C4
from gibs.validation.run_pilot import VARIANTS

T25_FAIL = REPO / "results/probe/new_batch1/results.json"         # 6f12b024: wrong booking (s30)
T25_OK = REPO / "results/pilot/task_25_topup/results.json"        # 0f0f7358: gold booking (s16)


def accept_all():
    return Similarity(StubEntailment(default=0.99), direction="max_bidirectional")


def run_c4(qg, rg, sim):
    q, r = project(qg, C4["topology"]), project(rg, C4["topology"])
    res = C4["matcher"](q, r, sim, C4["mcs"], field_check=StructuredFieldValidator(qg, rg))
    return q, res


# ------------------------------------------------------------------ definition
def test_c4_differs_from_c3_only_in_topology():
    c3 = VARIANTS["C3"]
    assert C4["topology"] == "paper_literal" and c3["topology"] == "event_context"
    for key in ("mcs", "fields", "matcher", "overlength"):
        assert C4[key] == c3[key], key
    assert C4["mcs"].tau_v == C4["mcs"].tau_e == 0.7 and C4["mcs"].require_same_kind


# ------------------------------------------------------------------ edge construction (real trajectories)
@pytest.mark.parametrize("path,prefix", [(TASK48_FILE, TASK48_SUCCESS), (T25_OK, "0f0f7358"), (T25_FAIL, "6f12b024")])
def test_c4_projection_keeps_every_data_dependency_and_no_context_edge(path, prefix):
    sg = build_step_graph(*load_simulation(str(path), prefix))
    g = project(sg, C4["topology"])
    deps = {(f"N:{e['source']}", f"N:{e['target']}") for e in sg["edges"] if e["type"] == "data_dependency"}
    data = {(e["src"], e["dst"]) for e in g.edges if e["roles"] == ["data"]}
    assert data == deps                                                    # nothing dropped, nothing added
    assert all(e["roles"] in (["data"], ["root"]) for e in g.edges)       # no 'context' edges at all
    assert all(e["src"] == ROOT for e in g.edges if e["roles"] == ["root"])
    for nid, n in g.nodes.items():
        if nid == ROOT:
            continue
        ins = g.in_edges(nid)
        has_dep = any(dst == nid for _, dst in deps)
        # an event with dependencies hangs from its sources only; otherwise from ROOT only
        assert (ins and all(e["roles"] == ["data"] for e in ins)) if has_dep else \
               (len(ins) == 1 and ins[0]["roles"] == ["root"])


def test_c4_tool_response_stays_folded_into_the_call():
    sg = build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_SUCCESS))
    g = project(sg, C4["topology"])
    step = next(n for n in sg["nodes"] if n.get("kind") == "tool_call")
    node = g.nodes[f"N:{step['id']}"]
    assert node["kind"] == "tool_result" and node["text"] == step["result_text"]       # observation = result node
    assert all(e["text"] == step["op_text"] for e in g.in_edges(node["id"]))           # call = operation (edge)


def test_c4_messages_and_user_turns_hang_from_root():
    sg = build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_SUCCESS))
    g = project(sg, C4["topology"])
    for n in g.nodes.values():
        if n["kind"] in ("agent_message", "user_turn"):
            assert [e["src"] for e in g.in_edges(n["id"])] == [ROOT]


# ------------------------------------------------------------------ structured-field safety
def test_c4_real_t25_wrong_booking_cannot_match_gold_booking_even_if_nli_accepts_everything():
    qg = build_step_graph(*load_simulation(str(T25_FAIL), "6f12b024"))
    rg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    q, res = run_c4(qg, rg, accept_all())
    assert "N:s30" not in res.node_map                       # wrong dates / flights / amount
    ind = pair_indicators(q, res)["s30"]
    assert not ind["node_level"] and not ind["context_step_level"]
    assert any(r["e1"].endswith("->N:s30") and any("args.flights" in x for x in r["reasons"]) for r in res.rejected)


BOOK = {"user_id": "u_1", "origin": "DTW", "destination": "SEA", "flight_type": "one_way", "cabin": "economy",
        "flights": [{"flight_number": "HAT097", "date": "2024-05-17"}], "passengers": [{"first_name": "I",
        "last_name": "S", "dob": "1986-03-14"}], "payment_methods": [{"payment_id": "gc_1", "amount": 100}],
        "total_baggages": 0, "nonfree_baggages": 0, "insurance": "no"}
USER = {"user_id": "u_1", "name": {"first_name": "I", "last_name": "S"}, "payment_methods": {}}


def booking_sim(flight_date, with_lookup=True, sim_id="s"):
    args = {**BOOK, "flights": [{"flight_number": "HAT097", "date": flight_date}]}
    events = [("agent", "Hi! How can I help you today?"), ("user", "Book for me, user u_1.")]
    if with_lookup:
        events.append(("call", "get_user_details", {"user_id": "u_1"}, USER))
    events.append(("call", "book_reservation", args, {"reservation_id": "NEW001", **args}))
    return build_step_graph(make_sim(events, sim_id))


@pytest.mark.parametrize("with_lookup", [True, False])   # False: the booking's only data source is the user turn
def test_c4_synthetic_conflicting_booking_rejected_identical_booking_matched(with_lookup):
    sim = accept_all()
    ref = booking_sim("2024-05-17", with_lookup, "ref")
    bk = "s4" if with_lookup else "s2"
    bad_q, bad = run_c4(booking_sim("2024-05-21", with_lookup, "bad"), ref, sim)
    assert f"N:{bk}" not in bad.node_map and bad.rejected
    good_q, good = run_c4(booking_sim("2024-05-17", with_lookup, "good"), ref, sim)
    ind = pair_indicators(good_q, good)[bk]
    assert ind["node_level"] and ind["context_step_level"]


def test_c4_root_hanging_conflicting_bookings_rejected_on_target():
    # neither booking has a data dependency (no prior text contains its values): both hang from ROOT
    def sim_of(date, sid):
        args = {**BOOK, "user_id": "zz_9", "flights": [{"flight_number": "HAT097", "date": date}]}
        return build_step_graph(make_sim([("call", "book_reservation", args, {"reservation_id": "N1", **args})], sid))
    q, r = sim_of("2024-05-21", "q"), sim_of("2024-05-17", "r")
    assert [e["roles"] for e in project(q, "paper_literal").edges] == [["root"]]
    _, res = run_c4(q, r, accept_all())
    assert "N:s0" not in res.node_map and res.rejected and "target" in res.rejected[0]["reasons"][0]


def test_c4_root_only_maps_to_root_and_edge_roles_never_mix_even_if_nli_accepts_everything():
    # real T25 pair (wrong-booking failure vs gold success); permissive NLI isolates the structural rules
    qg = build_step_graph(*load_simulation(str(T25_FAIL), "6f12b024"))
    rg = build_step_graph(*load_simulation(str(T25_OK), "0f0f7358"))
    q, res = run_c4(qg, rg, accept_all())
    r = project(rg, C4["topology"])
    assert all((a == ROOT) == (b == ROOT) for a, b in res.node_map.items())
    roles1 = {e["id"]: e["roles"] for e in q.edges}
    roles2 = {e["id"]: e["roles"] for e in r.edges}
    assert res.edge_map and all(roles1[a] == roles2[b] for a, b in res.edge_map.items())
