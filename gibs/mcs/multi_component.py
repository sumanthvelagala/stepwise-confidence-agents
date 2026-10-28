"""
Multi-component MCS  [OURS — experimental variant C2/C3, NOT the paper's algorithm].

PDF Alg. 4 / author code grow ONE connected common subgraph from the best of the top-K seeds. Validation showed
that this drops identical steps that are disconnected from that component (e.g. a greeting, a transfer notice).

This variant:
  1. computes the first component with the unchanged `find_mcs` (so component 0 is exactly the baseline result);
  2. repeatedly adds another component that is globally consistent with everything already mapped:
       * seeds: the top-K remaining candidate pairs (same ranking: edge + target similarity) whose endpoints are
         compatible with the global node map and whose edges are both still unmapped;
       * growth: the same BFS and compatibility rules as `find_mcs`, but checked against the *global* maps, so node
         and edge mappings stay one-to-one across all components (no union of independently built results);
       * the seed giving the largest gain in |edges| + |nodes| wins (ties -> earlier seed);
  3. stops when no consistent candidate remains, the gain is below `min_edges`, or `max_components` is reached.
Thresholds (0.7), candidate filtering (incl. structured fields) and the pool rule are inherited unchanged: the
same candidate list as the baseline is used, so no pair that failed a threshold or a field check can be added.
"""
from __future__ import annotations

from collections import deque

from gibs.graph.event_projection import ProjectedGraph
from gibs.mcs.mcs import Candidate, MCSConfig, MCSResult, _Scorer, find_mcs
from gibs.mcs.nli import Similarity


def _grow(g1, e1_by_id, e2_by_id, pool, seed: Candidate, vmap: dict, emap: dict):
    """BFS growth from `seed`, consistent with (and extending copies of) the global maps."""
    vmap, emap = dict(vmap), dict(emap)
    escore = {}
    used_e2 = set(emap.values())

    def compatible(c: Candidate) -> bool:
        if c.e1 in emap or c.e2 in used_e2:
            return False
        x1, y1 = e1_by_id[c.e1]["src"], e1_by_id[c.e1]["dst"]
        x2, y2 = e2_by_id[c.e2]["src"], e2_by_id[c.e2]["dst"]
        taken = set(vmap.values())
        ok_x = vmap[x1] == x2 if x1 in vmap else x2 not in taken
        ok_y = vmap[y1] == y2 if y1 in vmap else y2 not in taken
        return ok_x and ok_y

    def add(c: Candidate):
        emap[c.e1] = c.e2
        used_e2.add(c.e2)
        escore[c.e1] = c
        vmap.setdefault(e1_by_id[c.e1]["src"], e2_by_id[c.e2]["src"])
        vmap.setdefault(e1_by_id[c.e1]["dst"], e2_by_id[c.e2]["dst"])

    def incident(node):
        return [e["id"] for e in g1.out_edges(node)] + [e["id"] for e in g1.in_edges(node)]

    if not compatible(seed):
        return vmap, emap, escore
    add(seed)
    s1 = e1_by_id[seed.e1]
    visited = {seed.e1}
    queue: deque[str] = deque()
    for eid in ([e["id"] for e in g1.out_edges(s1["src"])] + [e["id"] for e in g1.out_edges(s1["dst"])]
                + [e["id"] for e in g1.in_edges(s1["src"])] + [e["id"] for e in g1.in_edges(s1["dst"])]):
        if eid not in visited:
            visited.add(eid)
            queue.append(eid)
    while queue:
        eid = queue.popleft()
        if eid not in pool or eid in emap:
            continue
        chosen = None
        for c in pool[eid]:
            if compatible(c) and (chosen is None or c.score > chosen.score):
                chosen = c
        if chosen is None:
            continue
        add(chosen)
        for node in (e1_by_id[eid]["src"], e1_by_id[eid]["dst"]):
            for nxt in incident(node):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
    return vmap, emap, escore


def find_mcs_multi(g1: ProjectedGraph, g2: ProjectedGraph, sim: Similarity, cfg: MCSConfig = MCSConfig(),
                   field_check=None, min_edges: int = 1, max_components: int | None = None) -> MCSResult:
    first = find_mcs(g1, g2, sim, cfg, field_check=field_check)
    result = first
    cands = [Candidate(c["e1"], c["e2"], c["s_edge"], c["s_src"], c["s_tgt"]) for c in first.candidates]  # sorted
    pool_list = cands if cfg.expansion_pool == "all_candidates" else cands[: cfg.top_k]
    pool: dict[str, list[Candidate]] = {}
    for c in pool_list:
        pool.setdefault(c.e1, []).append(c)
    e1_by_id = {e["id"]: e for e in g1.edges}
    e2_by_id = {e["id"]: e for e in g2.edges}
    vmap, emap = dict(first.node_map), dict(first.edge_map)
    escore = {e: Candidate(e, s["to"], s["s_edge"], s["s_src"], s["s_tgt"]) for e, s in first.edge_scores.items()}
    components = []
    if emap:
        components.append({"index": 0, "seed": first.seed, "edges": sorted(emap), "nodes": sorted(vmap),
                           "origin": "baseline find_mcs"})
    while max_components is None or len(components) < max_components:
        used_e2, taken = set(emap.values()), set(vmap.values())

        def eligible(c: Candidate) -> bool:
            if c.e1 in emap or c.e2 in used_e2:
                return False
            x1, y1 = e1_by_id[c.e1]["src"], e1_by_id[c.e1]["dst"]
            x2, y2 = e2_by_id[c.e2]["src"], e2_by_id[c.e2]["dst"]
            ok_x = vmap[x1] == x2 if x1 in vmap else x2 not in taken
            ok_y = vmap[y1] == y2 if y1 in vmap else y2 not in taken
            return ok_x and ok_y

        seeds = [c for c in cands if eligible(c)][: cfg.top_k]
        if not seeds:
            break
        best = None
        for seed in seeds:
            nv, ne, ns = _grow(g1, e1_by_id, e2_by_id, pool, seed, vmap, emap)
            gain = (len(ne) - len(emap)) + (len(nv) - len(vmap))
            if best is None or gain > best[0]:
                best = (gain, nv, ne, ns, seed)
        gain, nv, ne, ns, seed = best
        if len(ne) - len(emap) < min_edges:
            break
        new_edges = sorted(set(ne) - set(emap))
        new_nodes = sorted(set(nv) - set(vmap))
        components.append({"index": len(components), "seed": (seed.e1, seed.e2), "edges": new_edges,
                           "nodes": new_nodes, "origin": "additional component"})
        vmap, emap = nv, ne
        escore.update(ns)

    sc = _Scorer(g1, g2, sim, cfg)
    result.node_map, result.edge_map = vmap, emap
    result.size = len(emap) + len(vmap)
    result.node_scores = {n1: sc.node_sim(n1, n2) for n1, n2 in vmap.items()}
    result.edge_scores = {e: {"to": c.e2, "s_edge": c.s_edge, "s_src": c.s_src, "s_tgt": c.s_tgt}
                          for e, c in escore.items()}
    result.components = components
    return result
