"""
Heuristic Maximum Common Subgraph (PDF Appendix C.3, Algorithm 4) between a query graph G1 and a reference G2.

Provenance of each rule ([PDF] = project_paper.pdf, [CODE] = authors' src/GIBS/find_mcs.py, [OURS] = adaptation):
  candidates   [PDF]  edge pairs with NLI entailment >= tau_e; tau_e = tau_v = 0.7 (C.3, D.3)
               [PDF]  "adding only those edges and nodes whose ... scores exceed the thresholds" -> both the
                      target AND source node of a candidate must reach tau_v (R3). [CODE] checks the target only;
                      available as `check_source_nodes=False`.
  seed score   [CODE] edge similarity + target-node similarity (PDF: "combined edge-node similarity", no formula)
  seeds        [PDF]  top-K, K = 10 (C.4)
  pool         [OURS/R4] BFS may use every threshold-passing pair ('all_candidates'); [CODE] only the top-K
                      pairs ('top_k', ablation), which caps an MCS at K edges.
  BFS          [CODE] FIFO over in- and out-edges of both endpoints; an edge is dequeued once; if it has no
                      compatible match at that moment it is not revisited (as in the author code).
  consistency  [PDF]  "compatible with pi_V"; [CODE] injective node map, source->source and target->target.
  size         [CODE] |edges| + |nodes| (R5); a later seed must be strictly larger to replace the best.
  node sim     [OURS] ROOT<->ROOT = 1 and ROOT<->other = 0 without NLI ([CODE] runs NLI on the fallback text
                      "Problem/Initial State" in both graphs). [OURS] nodes of different event kinds
                      (tool_result / agent_message / user_turn) never match (`require_same_kind`).
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field

from gibs.graph.event_projection import ROOT, ProjectedGraph
from gibs.mcs.nli import Similarity


@dataclass(frozen=True)
class MCSConfig:
    tau_v: float = 0.7
    tau_e: float = 0.7
    top_k: int = 10
    check_source_nodes: bool = True
    expansion_pool: str = "all_candidates"   # or "top_k"
    require_same_kind: bool = True

    def __post_init__(self):
        if self.expansion_pool not in ("all_candidates", "top_k"):
            raise ValueError("expansion_pool must be 'all_candidates' or 'top_k'")


@dataclass
class Candidate:
    e1: str
    e2: str
    s_edge: float
    s_src: float
    s_tgt: float

    @property
    def score(self) -> float:          # [CODE] edge_sim + target node_sim
        return self.s_edge + self.s_tgt


@dataclass
class MCSResult:
    query_id: str
    reference_id: str
    config: dict
    direction: str
    node_map: dict[str, str] = field(default_factory=dict)
    edge_map: dict[str, str] = field(default_factory=dict)
    size: int = 0
    seed: tuple[str, str] | None = None
    candidates: list[dict] = field(default_factory=list)
    seeds: list[tuple[str, str]] = field(default_factory=list)
    node_scores: dict[str, float] = field(default_factory=dict)
    edge_scores: dict[str, dict] = field(default_factory=dict)
    rejected: list[dict] = field(default_factory=list)   # config C only: NLI-passing pairs rejected by field checks
    components: list[dict] = field(default_factory=list)  # multi-component variant only (gibs/mcs/multi_component.py)

    def to_dict(self) -> dict:
        return asdict(self)


class _Scorer:
    def __init__(self, g1: ProjectedGraph, g2: ProjectedGraph, sim: Similarity, cfg: MCSConfig):
        self.g1, self.g2, self.sim, self.cfg = g1, g2, sim, cfg

    def node_sim(self, n1: str, n2: str) -> float:
        a, b = self.g1.nodes[n1], self.g2.nodes[n2]
        if a["kind"] == "root" or b["kind"] == "root":
            return 1.0 if a["kind"] == b["kind"] == "root" else 0.0
        if self.cfg.require_same_kind and a["kind"] != b["kind"]:
            return 0.0
        return self.sim(a["text"], b["text"])

    def node_pair_texts(self, n1: str, n2: str):
        a, b = self.g1.nodes[n1], self.g2.nodes[n2]
        if "root" in (a["kind"], b["kind"]) or (self.cfg.require_same_kind and a["kind"] != b["kind"]):
            return None
        return a["text"], b["text"]


def find_mcs(g1: ProjectedGraph, g2: ProjectedGraph, sim: Similarity, cfg: MCSConfig = MCSConfig(),
             field_check=None) -> MCSResult:
    """`field_check` (optional, configuration C, [OURS]): callable (g1, g2, e1, e2) -> list of hard-incompatibility
    reasons. A candidate that passes every NLI threshold is dropped if the list is non-empty, and recorded in
    `result.rejected`. With `field_check=None` the algorithm is exactly the baseline."""
    sc = _Scorer(g1, g2, sim, cfg)
    result = MCSResult(query_id=g1.graph_id, reference_id=g2.graph_id, config=asdict(cfg), direction=sim.direction)

    # Phase 1 [PDF]: edge text entailment for all of E1 x E2 (batched).
    sim.prefetch((e1["text"], e2["text"]) for e1 in g1.edges for e2 in g2.edges)
    passing = [(e1, e2, sim(e1["text"], e2["text"])) for e1 in g1.edges for e2 in g2.edges]
    passing = [(e1, e2, s) for e1, e2, s in passing if s >= cfg.tau_e]

    # Phase 2: endpoint node entailment only for edge pairs that passed (batched).
    sim.prefetch(t for e1, e2, _ in passing for t in (sc.node_pair_texts(e1["src"], e2["src"]),
                                                       sc.node_pair_texts(e1["dst"], e2["dst"])) if t)
    cands: list[Candidate] = []
    for e1, e2, s_e in passing:
        s_t = sc.node_sim(e1["dst"], e2["dst"])
        s_s = sc.node_sim(e1["src"], e2["src"])
        if s_t < cfg.tau_v or (cfg.check_source_nodes and s_s < cfg.tau_v):
            continue
        if field_check is not None:
            reasons = field_check(g1, g2, e1, e2)
            if reasons:
                result.rejected.append({"e1": e1["id"], "e2": e2["id"], "s_edge": s_e, "s_src": s_s, "s_tgt": s_t,
                                        "reasons": reasons})
                continue
        cands.append(Candidate(e1["id"], e2["id"], s_e, s_s, s_t))

    order1 = {e["id"]: i for i, e in enumerate(g1.edges)}
    order2 = {e["id"]: i for i, e in enumerate(g2.edges)}
    cands.sort(key=lambda c: (-c.score, order1[c.e1], order2[c.e2]))
    seeds = cands[: cfg.top_k]
    pool_list = cands if cfg.expansion_pool == "all_candidates" else seeds
    pool: dict[str, list[Candidate]] = {}
    for c in pool_list:
        pool.setdefault(c.e1, []).append(c)

    result.candidates = [{**asdict(c), "score": c.score} for c in cands]
    result.seeds = [(c.e1, c.e2) for c in seeds]
    e1_by_id = {e["id"]: e for e in g1.edges}
    e2_by_id = {e["id"]: e for e in g2.edges}

    def incident(node: str) -> list[str]:
        return [e["id"] for e in g1.out_edges(node)] + [e["id"] for e in g1.in_edges(node)]

    best: tuple = (0, {}, {}, None, {})   # (size, node_map, edge_map, seed, edge -> Candidate)
    for seed in seeds:
        s1, s2 = e1_by_id[seed.e1], e2_by_id[seed.e2]
        vmap = {s1["src"]: s2["src"], s1["dst"]: s2["dst"]}
        emap = {seed.e1: seed.e2}
        escore = {seed.e1: seed}
        visited = {seed.e1}
        queue: deque[str] = deque()
        # [CODE] initial frontier order: out(u1), out(v1), in(u1), in(v1)
        for eid in ([e["id"] for e in g1.out_edges(s1["src"])] + [e["id"] for e in g1.out_edges(s1["dst"])]
                    + [e["id"] for e in g1.in_edges(s1["src"])] + [e["id"] for e in g1.in_edges(s1["dst"])]):
            if eid not in visited:
                visited.add(eid)
                queue.append(eid)
        while queue:
            eid = queue.popleft()
            if eid not in pool:
                continue
            x1, y1 = e1_by_id[eid]["src"], e1_by_id[eid]["dst"]
            chosen = None
            for c in pool[eid]:                 # pool lists are score-sorted: first compatible max wins
                x2, y2 = e2_by_id[c.e2]["src"], e2_by_id[c.e2]["dst"]
                taken = set(vmap.values())
                ok_x = vmap[x1] == x2 if x1 in vmap else x2 not in taken
                ok_y = vmap[y1] == y2 if y1 in vmap else y2 not in taken
                if ok_x and ok_y and (chosen is None or c.score > chosen.score):
                    chosen = c
            if chosen is None:
                continue
            x2, y2 = e2_by_id[chosen.e2]["src"], e2_by_id[chosen.e2]["dst"]
            emap[eid] = chosen.e2
            escore[eid] = chosen
            vmap.setdefault(x1, x2)
            vmap.setdefault(y1, y2)
            for node in (x1, y1):
                for nxt in incident(node):
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
        size = len(emap) + len(vmap)
        if size > best[0]:
            best = (size, vmap, emap, seed, escore)

    if best[0]:
        size, vmap, emap, seed, escore = best
        result.size, result.node_map, result.edge_map = size, vmap, emap
        result.seed = (seed.e1, seed.e2)
        result.node_scores = {n1: sc.node_sim(n1, n2) for n1, n2 in vmap.items()}
        result.edge_scores = {e: {"to": c.e2, "s_edge": c.s_edge, "s_src": c.s_src, "s_tgt": c.s_tgt}
                              for e, c in escore.items()}
    return result
