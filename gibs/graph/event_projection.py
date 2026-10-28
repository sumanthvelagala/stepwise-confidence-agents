"""
Event projection: step graph (v0.2) -> the paper's operation/result graph, on which MCS runs.

PDF §4.3/§4.4(A): a step is (e, v) where e is the operation and v the result it produces; nodes are results,
edges are operations. Author code (src/dataset/tranformed_graph.py) builds one edge per `depends_on` entry,
roots dependency-free steps at `NodeRaw`, and gives every edge of a step the step's description text.

Our projection (adaptation R1, uniform over event kinds):
  * ROOT                        — plays the role of the author code's `NodeRaw`.
  * one result node per event:  tool call      -> its observation      (text = step.result_text)
                                agent message  -> the message itself   (text = step.result_text)
                                user turn      -> the turn itself      (text = step.result_text)
  * edges into an event's node, all carrying the event's operation text (step.op_text):
      - 'context' : from the immediately preceding event's node (ROOT for the first event)   [OUR adaptation]
      - 'data'    : from each data_dependency source of the event                            [analogue of depends_on]
    A context edge and a data edge with the same endpoints are merged into one edge with both roles.
  * `topology='paper_literal'` drops context edges and roots events without data dependencies at ROOT,
    which is the author code's construction applied to our events (ablation).

Only edges/nodes of AgentStep events are scorable; UserTurn events are context only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

ROOT = "ROOT"
TOPOLOGIES = ("event_context", "paper_literal")


@dataclass
class ProjectedGraph:
    graph_id: str
    topology: str
    nodes: dict[str, dict] = field(default_factory=dict)   # node_id -> {id, kind, text, event, scorable}
    edges: list[dict] = field(default_factory=list)        # {id, src, dst, text, event, roles, scorable}

    def out_edges(self, node_id: str) -> list[dict]:
        return [e for e in self.edges if e["src"] == node_id]

    def in_edges(self, node_id: str) -> list[dict]:
        return [e for e in self.edges if e["dst"] == node_id]

    def edge(self, src: str, dst: str) -> dict:
        return next(e for e in self.edges if e["src"] == src and e["dst"] == dst)

    def to_dict(self) -> dict:
        return {"graph_id": self.graph_id, "topology": self.topology,
                "nodes": list(self.nodes.values()), "edges": self.edges}


def node_id_for(event_id: str) -> str:
    return f"N:{event_id}"


def _node_kind(step_node: dict) -> str:
    if step_node["type"] == "UserTurn":
        return "user_turn"
    return "tool_result" if step_node["kind"] == "tool_call" else "agent_message"


def project(step_graph: dict, topology: str = "event_context") -> ProjectedGraph:
    if topology not in TOPOLOGIES:
        raise ValueError(f"topology must be one of {TOPOLOGIES}")
    g = ProjectedGraph(graph_id=step_graph["graph_id"], topology=topology)
    g.nodes[ROOT] = {"id": ROOT, "kind": "root", "text": None, "event": None, "scorable": False}

    deps: dict[str, list[str]] = {}
    for e in step_graph["edges"]:
        if e["type"] == "data_dependency":
            deps.setdefault(e["target"], []).append(e["source"])

    prev = ROOT
    for n in step_graph["nodes"]:
        nid = node_id_for(n["id"])
        scorable = n["type"] == "AgentStep"
        g.nodes[nid] = {"id": nid, "kind": _node_kind(n), "text": n["result_text"], "event": n["id"],
                        "scorable": scorable}
        inputs: dict[str, set[str]] = {}
        if topology == "event_context":
            inputs.setdefault(prev, set()).add("context")
        for src in deps.get(n["id"], []):
            inputs.setdefault(node_id_for(src), set()).add("data")
        if not inputs:  # paper_literal: dependency-free events hang from ROOT, like the author code's NodeRaw
            inputs[ROOT] = {"root"}
        for src, roles in inputs.items():
            g.edges.append({"id": f"{src}->{nid}", "src": src, "dst": nid, "text": n["op_text"],
                            "event": n["id"], "roles": sorted(roles), "scorable": scorable})
        prev = nid
    return g
