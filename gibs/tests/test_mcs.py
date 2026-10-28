from gibs.graph.event_projection import project
from gibs.graph.step_graph import build_step_graph
from gibs.mcs.mcs import MCSConfig, find_mcs
from gibs.mcs.nli import Similarity, StubEntailment
from gibs.tests.helpers import make_sim

LOOKUP = ("call", "get_reservation_details", {"reservation_id": "ABC123"}, {"reservation_id": "ABC123", "status": None})


def graph(events, sim_id):
    return project(build_step_graph(make_sim(events, sim_id=sim_id)))


def run(g1, g2, table=None, direction="max_bidirectional", **cfg):
    sim = Similarity(StubEntailment(table or {}), direction=direction)
    return find_mcs(g1, g2, sim, MCSConfig(**cfg))


BASE = [("agent", "Hi"), ("user", "Cancel ABC123 please."), LOOKUP, ("agent", "Done.")]


def test_identical_graphs_map_completely_and_size_is_edges_plus_nodes():
    g1, g2 = graph(BASE, "q"), graph(BASE, "r")
    r = run(g1, g2)
    assert len(r.edge_map) == len(g1.edges) and len(r.node_map) == len(g1.nodes)
    assert r.size == len(g1.edges) + len(g1.nodes)
    assert all(r.node_map[n] == n for n in g1.nodes)          # same event ids -> same node ids


def test_edge_threshold_is_inclusive_at_0_7():
    q = graph([("agent", "Hello there")], "q")
    ref = graph([("agent", "Hi")], "r")
    for p, expect in ((0.69, 0), (0.70, 1)):
        table = {("Hello there", "Hi"): p}
        assert len(run(q, ref, table).edge_map) == expect


def test_one_way_direction_uses_only_query_to_reference():
    q, ref = graph([("agent", "A")], "q"), graph([("agent", "B")], "r")
    table = {("B", "A"): 0.9}                                 # only reference => query entails
    assert len(run(q, ref, table, direction="max_bidirectional").edge_map) == 1
    assert len(run(q, ref, table, direction="one_way").edge_map) == 0


def test_source_node_threshold_R3_and_author_code_ablation():
    q = graph([("agent", "Hi"), ("user", "Please go ahead."), ("agent", "Okay.")], "q")
    ref = graph([("agent", "Hi"), ("user", "Do not do it."), ("agent", "Okay.")], "r")
    pair = ("N:u1->N:s2", "N:u1->N:s2")
    strict = run(q, ref)
    assert pair not in {(c["e1"], c["e2"]) for c in strict.candidates}   # source turns contradict
    lenient = run(q, ref, check_source_nodes=False)                      # author code checks the target only
    assert pair in {(c["e1"], c["e2"]) for c in lenient.candidates}


def test_mcs_is_one_connected_piece_grown_from_a_single_seed():
    # Same graphs as above with the author-code source rule: u1->s2 is a candidate, but the user turns between
    # it and the ROOT->s0 match do not match, so BFS from either seed cannot join them (PDF Alg. 4 / author code).
    q = graph([("agent", "Hi"), ("user", "Please go ahead."), ("agent", "Okay.")], "q")
    ref = graph([("agent", "Hi"), ("user", "Do not do it."), ("agent", "Okay.")], "r")
    r = run(q, ref, check_source_nodes=False)
    assert len(r.edge_map) == 1 and r.seed == ("ROOT->N:s0", "ROOT->N:s0")   # tie -> earlier seed kept


def test_expansion_pool_all_candidates_vs_author_top_k():
    events = [("agent", f"step {i}") for i in range(6)]
    g1, g2 = graph(events, "q"), graph(events, "r")
    ours = run(g1, g2, top_k=2, expansion_pool="all_candidates")
    code = run(g1, g2, top_k=2, expansion_pool="top_k")
    assert len(ours.edge_map) == 6
    assert len(code.edge_map) == 2                           # MCS capped at K edges


def test_identical_calls_map_injectively():
    q = graph([("agent", "Hi"), ("user", "id ABC123"), LOOKUP, LOOKUP], "q")
    ref = graph([("agent", "Hi"), ("user", "id ABC123"), LOOKUP], "r")
    r = run(q, ref)
    lookup_nodes = [n for n in ("N:s2", "N:s4") if n in r.node_map]
    assert len(lookup_nodes) == 1                            # the reference has only one lookup
    assert len(set(r.node_map.values())) == len(r.node_map)


def test_different_event_kinds_never_match():
    q = graph([("agent", "Yes."), ("user", "Yes.")], "q")
    ref = graph([("user", "Yes."), ("agent", "Yes.")], "r")
    r = run(q, ref)
    for n1, n2 in r.node_map.items():
        assert q.nodes[n1]["kind"] == ref.nodes[n2]["kind"]


def test_no_candidates_gives_empty_mcs():
    r = run(graph([("agent", "A")], "q"), graph([("agent", "B")], "r"))
    assert r.size == 0 and r.edge_map == {} and r.seed is None
