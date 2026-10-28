import pytest

from gibs.graph.event_projection import ROOT, project
from gibs.graph.step_graph import build_step_graph, load_simulation
from gibs.tests.helpers import TASK48_FAILURE, TASK48_FILE, TASK48_SUCCESS


@pytest.fixture(scope="module")
def failure_steps():
    return build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_FAILURE))


def test_one_result_node_per_event_plus_root(failure_steps):
    g = project(failure_steps)
    assert len(g.nodes) == len(failure_steps["nodes"]) + 1 and ROOT in g.nodes
    kinds = {n["event"]: n["kind"] for n in g.nodes.values() if n["event"]}
    assert kinds["s4"] == kinds["s6"] == "tool_result"
    assert kinds["s8"] == "agent_message" and kinds["u9"] == "user_turn"


def test_only_agent_events_are_scorable(failure_steps):
    g = project(failure_steps)
    for n in g.nodes.values():
        assert n["scorable"] == (n["kind"] in ("tool_result", "agent_message"))
    for e in g.edges:
        assert e["scorable"] == g.nodes[e["dst"]]["scorable"]


def test_context_and_data_edges_for_the_cancel_call(failure_steps):
    g = project(failure_steps)
    into_cancel = {e["src"]: e["roles"] for e in g.in_edges("N:s6")}
    assert into_cancel == {"N:s4": ["context"], "N:u3": ["data"]}
    assert all(e["text"] == "Call cancel_reservation with reservation_id = 3RK2T9." for e in g.in_edges("N:s6"))
    assert {e["src"]: e["roles"] for e in g.in_edges("N:s4")} == {"N:u3": ["context", "data"]}  # merged


def test_every_event_has_a_context_edge_from_its_predecessor(failure_steps):
    g = project(failure_steps)
    order = [ROOT] + [f"N:{n['id']}" for n in failure_steps["nodes"]]
    for prev, cur in zip(order, order[1:]):
        assert "context" in g.edge(prev, cur)["roles"]


def test_paper_literal_topology_roots_dependency_free_events(failure_steps):
    g = project(failure_steps, topology="paper_literal")
    assert not any("context" in e["roles"] for e in g.edges)
    assert {e["src"] for e in g.in_edges("N:s8")} == {ROOT}
    assert {e["src"] for e in g.in_edges("N:s6")} == {"N:u3"}


def test_success_graph_projection_counts():
    g = project(build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_SUCCESS)))
    assert len(g.nodes) == 11
    # 10 context edges; data edge u3->s4 merges with its context edge; s4->s8 is an extra data edge
    assert len(g.edges) == 11
