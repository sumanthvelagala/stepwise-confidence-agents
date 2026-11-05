"""Numerical parity checks against selected functions at a pinned author commit.

Fetch/hash primary sources, then compile ONLY the listed class methods into a
minimal namespace. Do not import/run the full upstream modules or training code.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request

import networkx as nx
import numpy as np
import torch
from torch import nn

from gibs.comparison.released_model import ReleasedPredictor, released_loss
from gibs.comparison.semantic_nibs import reference_scores

BASE = "https://raw.githubusercontent.com/Xiao0o0o/stepwise-confidence-attribution/1ccc8b8/"
SOURCES = {
    "src/NIBS/similarity_based_baseline.py": "91b53617e3accdc65e05d4b748f4a999fc6ea713cb3766086dce0b6bfff79e53",
    "src/GIBS/GIB_MCS_wo_mcs_feature.py": "86d12c9cbff319a14bf79981e755b0abc444641898b775e26d0720a67b07a372",
    "src/GIBS/find_mcs.py": "6a1c972424f7419adf7e130b1f2fe66938a6fe73453f8c5c342ff02c40610be0",
    "src/dataset/bert_graph.py": "2eed9ff3217e71f47164b7c9bf9797ecabbdf3125f950d2e5a04f640135b4f35"}


def source(relative):
    cache = Path.home() / ".cache/stepwise_gibs/author_1ccc8b8" / relative
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(BASE + relative, timeout=30) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != SOURCES[relative]:
            raise ValueError("pinned author source hash mismatch")
        cache.write_bytes(data)
    data = cache.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCES[relative]:
        raise ValueError("cached author source hash mismatch")
    return data.decode()


def selected_class(tree, name, methods):
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    return ast.ClassDef(name=name, bases=original.bases, keywords=[], decorator_list=[],
                        body=[m for m in original.body if isinstance(m, ast.FunctionDef) and m.name in methods], type_params=[])


def verify():
    texts = {relative: source(relative) for relative in SOURCES}
    namespace = {"np": np, "torch": torch, "nn": nn, "nx": nx, "Dict": Dict,
                 "List": List, "Tuple": Tuple, "Optional": Optional,
                 "MaximumCommonSubgraph": lambda **kwargs: object(), "MCSCache": lambda: object(),
                 "GCN2Layer": lambda **kwargs: nn.Identity()}
    # Upstream graph parsing helper is side-effect-free and only needs regex/nx.
    import re
    namespace["re"] = re
    gib_tree = ast.parse(texts["src/GIBS/GIB_MCS_wo_mcs_feature.py"])
    build = next(n for n in gib_tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_graph")
    cls = selected_class(gib_tree, "GIBErrorDetectionModel", {"__init__", "extract_graph_features", "forward", "compute_losses", "compute_mcs_consistency_loss"})
    module = ast.fix_missing_locations(ast.Module(body=[build, cls], type_ignores=[]))
    exec(compile(module, "pinned_author_selected_gibs", "exec"), namespace)
    torch.manual_seed(7)
    ours = ReleasedPredictor(embedding_dim=6, hidden_dim=8).eval()
    theirs = namespace["GIBErrorDetectionModel"](embedding_dim=6, hidden_dim=8).eval()
    for name in ("node_encoder", "edge_encoder", "graph_encoder", "mask_predictor"):
        getattr(theirs, name).load_state_dict(getattr(ours, name).state_dict())
    nodes = np.arange(18, dtype=np.float32).reshape(3, 6) / 10
    operations = np.arange(12, dtype=np.float32).reshape(2, 6) / 8
    graph = {"results": torch.tensor(nodes), "edge_operations": torch.tensor(operations),
             "agent_edge_indices": [torch.tensor([0]), torch.tensor([1])]}
    upstream = {"structure_str": "[NodeRaw, Node0, Edge0];[Node0, Node1, Edge1]",
                "embeddings": {**{n: nodes[i] for i, n in enumerate(["NodeRaw", "Node0", "Node1"])},
                               **{n: operations[i] for i, n in enumerate(["Edge0", "Edge1"])}}}
    with torch.no_grad():
        predicted = theirs(upstream, [])
        logits = ours.forward_edges(graph)
        torch.testing.assert_close(logits.sigmoid(), predicted["edge_masks"], rtol=0, atol=1e-7)
        mappings = [{("NodeRaw", "Node0"): ("a", "b")}, {}, {("Node0", "Node1"): ("b", "c")}]
        upstream_losses = theirs.compute_losses(upstream, [], predicted["edge_masks"], None, None, predicted["edge_ids"], mappings)
        ours_loss = released_loss(logits, [torch.tensor([1., 0.]), torch.tensor([0., 0.]), torch.tensor([0., 1.])])
        torch.testing.assert_close(ours_loss, sum(upstream_losses.values()), rtol=0, atol=1e-7)
    # Only cosine functions are selected; no upstream model loading occurs.
    nibs_tree = ast.parse(texts["src/NIBS/similarity_based_baseline.py"])
    namespace["cosine"] = lambda a, b: 1 - float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    module = ast.fix_missing_locations(ast.Module(body=[
        selected_class(nibs_tree, "SimilarityCalculator", {"cosine_distance", "cosine_similarity"}),
        selected_class(nibs_tree, "GraphSimilarityAnalyzer", {"cosine_mean", "cosine_max"})], type_ignores=[]))
    exec(compile(module, "pinned_author_selected_nibs", "exec"), namespace)
    analyzer = namespace["GraphSimilarityAnalyzer"]()
    analyzer.sim_calculator = namespace["SimilarityCalculator"]()
    reference_graphs = {}
    references = [np.array([[1., 0.], [0., 1.]]), np.array([[.8, .6]])]
    for i, values in enumerate(references):
        g = nx.DiGraph()
        for j, vector in enumerate(values):
            g.add_edge(j, j + 1, embedding=vector)
        reference_graphs[i] = g
    query = np.array([[1., 0.], [.6, .8]])
    maxima, means = reference_scores(query, references, released=True)
    np.testing.assert_allclose(maxima, [analyzer.cosine_max(q, reference_graphs) for q in query], atol=1e-12)
    np.testing.assert_allclose(means, [analyzer.cosine_mean(q, reference_graphs) for q in query], atol=1e-12)
    return {"author_commit": "1ccc8b8", "sources_sha256": SOURCES,
            "checks": {"released_forward_probabilities_match": True, "released_entropy_and_balanced_loss_match": True,
                       "released_cosine_max_matches": True, "released_cosine_mean_matches": True},
            "scope": "Selected active functions only; not original dataset/training-procedure replication."}


if __name__ == "__main__":
    from nibs.run_evaluation import write_json
    output = Path("results/paper_comparison/source_verification.json")
    write_json(output, verify())
    print(f"Pinned author forward, loss and cosine formulas match: {output}")
