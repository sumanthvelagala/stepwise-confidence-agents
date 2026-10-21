"""
Graph construction for GIBS.

Each trajectory becomes a directed graph:
  Nodes:  ToolCall, ToolResult, AgentMessage
  Edges:  Temporal (sequential flow)
          ToolResponse (call → result, same step)
          DataDependency (result_i → call_j, arg value from prior obs)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

# Node types
NODE_TOOL_CALL = "tool_call"
NODE_TOOL_RESULT = "tool_result"
NODE_AGENT_MSG = "agent_msg"

# Edge types
EDGE_TEMPORAL = "temporal"
EDGE_TOOL_RESPONSE = "tool_response"
EDGE_DATA_DEP = "data_dep"


@dataclass
class TrajGraph:
    task_id: str
    trial: int
    success: bool
    reward: Optional[float]
    # nodes: list of {id, type, text, step_idx}
    nodes: list = field(default_factory=list)
    # edges: list of (src_id, dst_id, edge_type)
    edges: list = field(default_factory=list)
    # step_nodes: step_idx -> {"call": id|None, "result": id|None, "msg": id|None}
    step_nodes: dict = field(default_factory=dict)
    # embeddings: (n_nodes, dim) numpy array, set by batch_embed_graphs()
    embeddings: Optional[np.ndarray] = field(default=None, repr=False)


def _call_text(step: dict) -> str:
    args_str = " ".join(f"{k}={v}" for k, v in (step.get("args") or {}).items())
    return f"{step['tool']} {args_str}".strip()


def _result_text(step: dict) -> str:
    return (step.get("obs") or "")[:300]


def _msg_text(step: dict) -> str:
    return (step.get("thought") or "")[:300]


def build_graph(trajectory: dict) -> TrajGraph:
    """
    Convert a parsed trajectory dict (from nibs/parsing/parser.py) into a TrajGraph.

    Expected trajectory keys: task_id, trial, success, reward, steps
    Each step: {idx, tool, args, obs, thought, depends_on, scored}
    """
    g = TrajGraph(
        task_id=str(trajectory["task_id"]),
        trial=trajectory.get("trial", 0),
        success=trajectory.get("success", False),
        reward=trajectory.get("reward"),
    )

    node_id = 0
    last_node_id: Optional[int] = None

    for step in trajectory.get("steps", []):
        if not step.get("scored", True):
            continue

        idx = step["idx"]
        g.step_nodes[idx] = {"call": None, "result": None, "msg": None}

        if step.get("tool"):
            # --- ToolCall node ---
            call_id = node_id
            g.nodes.append({
                "id": call_id,
                "type": NODE_TOOL_CALL,
                "text": _call_text(step),
                "step_idx": idx,
            })
            g.step_nodes[idx]["call"] = call_id
            node_id += 1

            # --- ToolResult node ---
            result_id = node_id
            g.nodes.append({
                "id": result_id,
                "type": NODE_TOOL_RESULT,
                "text": _result_text(step),
                "step_idx": idx,
            })
            g.step_nodes[idx]["result"] = result_id
            node_id += 1

            # ToolResponse edge: call → result
            g.edges.append((call_id, result_id, EDGE_TOOL_RESPONSE))

            # Temporal edge from previous last node to this call
            if last_node_id is not None:
                g.edges.append((last_node_id, call_id, EDGE_TEMPORAL))

            last_node_id = result_id

        else:
            # --- AgentMessage node ---
            msg_id = node_id
            g.nodes.append({
                "id": msg_id,
                "type": NODE_AGENT_MSG,
                "text": _msg_text(step),
                "step_idx": idx,
            })
            g.step_nodes[idx]["msg"] = msg_id
            node_id += 1

            if last_node_id is not None:
                g.edges.append((last_node_id, msg_id, EDGE_TEMPORAL))

            last_node_id = msg_id

    # Data dependency edges: result_i → call_j  (arg value came from obs of step i)
    for step in trajectory.get("steps", []):
        if not step.get("scored", True):
            continue
        idx = step["idx"]
        call_id = g.step_nodes.get(idx, {}).get("call")
        if call_id is None:
            continue
        for dep_idx in step.get("depends_on", []):
            result_id = g.step_nodes.get(dep_idx, {}).get("result")
            if result_id is not None:
                g.edges.append((result_id, call_id, EDGE_DATA_DEP))

    return g
