"""Unchanged baseline graph and a separately named state/context graph ablation."""
from __future__ import annotations

from copy import deepcopy

import torch

from gibs.graph.event_projection import ROOT, project
from gibs.graph.step_graph import build_step_graph, dependency_values, value_occurs, _visible_text
from gibs.learned.data import tensor_graph


def projection(sim, structure="original"):
    clean = {"id": sim.get("id"), "task_id": sim.get("task_id"), "messages": sim.get("messages") or []}
    sg = build_step_graph(clean)
    graph = project(sg, "paper_literal")
    if structure == "original":
        return graph
    if structure != "state_aware":
        raise ValueError("unknown graph structure")
    graph = deepcopy(graph)
    graph.topology = structure
    graph.edges = []
    for index, node in enumerate(sg["nodes"]):
        prior = sg["nodes"][:index]
        inputs = {}
        if node.get("kind") == "tool_call":
            for value in dependency_values(node["tool_call"]["arguments"]):
                observations = [n for n in prior if n.get("kind") == "tool_call"
                                and not n["observation"]["error"] and value_occurs(value, _visible_text(n))]
                fallback = [n for n in prior if value_occurs(value, _visible_text(n))]
                if observations or fallback:
                    source = observations[-1] if observations else fallback[0]
                    inputs.setdefault("N:" + source["id"], set()).add("latest_observation" if observations else "original_provenance")
        elif node["type"] == "AgentStep":
            user = next((n for n in reversed(prior) if n["type"] == "UserTurn"), None)
            observation = next((n for n in reversed(prior) if n.get("kind") == "tool_call"), None)
            for source, role in ((user, "message_user_context"), (observation, "message_observation")):
                if source:
                    inputs.setdefault("N:" + source["id"], set()).add(role)
        if not inputs:
            inputs[ROOT] = {"root"}
        target = "N:" + node["id"]
        for source, roles in inputs.items():
            graph.edges.append({"id": f"{source}->{target}", "src": source, "dst": target,
                                "text": node["op_text"], "event": node["id"], "roles": sorted(roles),
                                "scorable": node["type"] == "AgentStep"})
    order = {nid: i for i, nid in enumerate(graph.nodes)}
    if any(order[e["src"]] >= order[e["dst"]] for e in graph.edges):
        raise ValueError("future information entered a dependency edge")
    return graph


def spec(graph):
    ids = list(graph.nodes)
    index = {nid: i for i, nid in enumerate(ids)}
    operations = {e["dst"]: e["text"] for e in graph.edges}
    agents = [i for i, nid in enumerate(ids) if graph.nodes[nid]["scorable"]]
    return {"node_ids": ids, "result_texts": [graph.nodes[nid]["text"] or "Problem/Initial State" for nid in ids],
            "operation_texts": [operations.get(nid, "Problem/Initial State") for nid in ids],
            "edges": [(index[e["src"]], index[e["dst"]]) for e in graph.edges],
            "edge_ids": [e["id"] for e in graph.edges], "agent_indices": agents,
            "agent_events": [graph.nodes[ids[i]]["event"] for i in agents],
            "agent_edge_indices": [[j for j, e in enumerate(graph.edges) if e["dst"] == ids[i]] for i in agents]}


def tensors(specification, embeddings):
    result = tensor_graph(specification, embeddings)
    result["edge_operations"] = result["operations"][[target for _, target in specification["edges"]]]
    result["agent_edge_indices"] = [torch.tensor(indices, dtype=torch.long) for indices in specification["agent_edge_indices"]]
    return result


def export_diagram(graph, title):
    ids = {nid: f"v{i}" for i, nid in enumerate(graph.nodes)}
    lines = [f"## {title}", "", "```mermaid", "flowchart TD"]
    for nid, node in graph.nodes.items():
        text = node["text"] or "ROOT"
        if node["kind"] == "tool_result":
            incoming = graph.in_edges(nid)
            text = incoming[0]["text"].split(" with ")[0] if incoming else "tool result"
        else:
            text = text[:70]
        text = text.replace('"', "'").replace("\n", " ").replace("[", "(").replace("]", ")")
        lines.append(f'  {ids[nid]}["{node["event"] or "ROOT"}: {text}"]')
    for edge in graph.edges:
        label = ", ".join(edge["roles"])
        lines.append(f'  {ids[edge["src"]]} -->|"{label}"| {ids[edge["dst"]]}')
    return "\n".join(lines + ["```", ""])
