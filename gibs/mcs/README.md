# GIBS consensus construction: NLI + heuristic MCS

Status: graph schema, event projection, NLI scoring, MCS and consensus targets are implemented and unit-tested.
**Not implemented: GCN, mask predictor, training.** Full-task consensus scoring has not been run yet.

## References and precedence (decision R0)

| Tag | Source |
|---|---|
| **[PDF]** | `project_paper.pdf` (arXiv 2605.19228; title verified). Primary methodological reference. |
| **[CODE]** | Authors' repository `github.com/Xiao0o0o/stepwise-confidence-attribution` (commit `1ccc8b8`, 2026-06-30): `src/GIBS/find_mcs.py`, `src/GIBS/GIB_MCS_wo_mcs_feature.py`, `src/dataset/tranformed_graph.py`. Used **only** where the PDF is silent. |
| **[OURS]** | Our adaptation for tau2-bench agent trajectories. |

Where [CODE] contradicts [PDF], the PDF is followed and the [CODE] behaviour is kept as an ablation flag.

## Pipeline

```
raw tau2 simulation ──► step graph v0.2 ──► event projection ──► MCS(query, each correct reference) ──► consensus targets
gibs/graph/step_graph.py   gibs/graph/event_projection.py   gibs/mcs/mcs.py + nli.py         gibs/mcs/consensus.py
```

## Rule-by-rule provenance

| Component | [PDF] says | [CODE] does | We do | Where |
|---|---|---|---|---|
| Step representation | step = (e operation, v result); nodes = results, edges = operations (§4.3 p.4, §4.4(A) p.5) | `ReasoningNode` → node; one edge per `depends_on`, all carrying the step description; dependency-free steps from `NodeRaw` | **[OURS] uniform event projection (R1):** one result node per event — tool call → observation, agent message → message, user turn → turn; edges carry the operation text | `event_projection.py` |
| Root | not specified | `NodeRaw` (NLI text falls back to "Problem/Initial State") | `ROOT`; ROOT↔ROOT = 1, ROOT↔other = 0 without NLI [OURS] | `mcs.py` |
| Edges into a step | "logical dependencies or sub-questions" | `depends_on` only | data-dependency edges (value provenance) **+ [OURS] a context edge from the immediately preceding event**; `topology="paper_literal"` = [CODE]-style (dependencies only, dependency-free events from ROOT) | `event_projection.py` |
| Scored events | every reasoning step | every edge | **AgentStep events only**; user turns are context (R1) | `consensus.py` |
| NLI model | DeBERTa-large-MNLI (D.3 p.16–17) | `microsoft/deberta-large-mnli` | same, snapshot `7296194b…` | `nli.py` |
| Score | `NLI(Entail)(R1(e1),R2(e2)) ≥ τe` (Alg. 4 p.15) | softmax, index 2 (ENTAILMENT) | softmax; ENTAILMENT index read from `id2label` (= 2) | `nli.py` |
| Direction | not specified | **max of both directions** | **[CODE] max (primary, R2)**; one-way query⇒reference as ablation | `nli.py` |
| Input format | not specified | single string `a + ' [SEP] ' + b` | [CODE] string (primary); tokenizer pair encoding available | `nli.py` |
| Inputs > 512 tokens | not specified | `truncation=True` (cuts the end of the joined string) | [CODE] truncation, but **every truncated comparison is recorded** and cached under a separate key; `overlength="error"` refuses instead | `nli.py` |
| Thresholds | τv = τe = 0.7 (C.3 p.15, D.3 p.17) | training script 0.7/0.7 (class defaults 0.85/0.8) | 0.7 / 0.7 | `mcs.py` |
| Candidate | edge ≥ τe; "edges **and nodes** … exceed thresholds" (C.3) | edge ≥ τe and **target** node ≥ τv | **[PDF] edge, source node and target node (R3)**; `check_source_nodes=False` = [CODE] | `mcs.py` |
| Seed ranking | "combined edge–node similarity" (no formula) | edge sim + target-node sim | [CODE] | `mcs.py` |
| Seeds | top-K, K = 10 (C.4 p.15) | top 10 | top 10 | `mcs.py` |
| Expansion pool | best match ≥ τe "within the pre-filtered candidate set" | only the top-10 pairs (an MCS can never exceed 10 edges) | **all threshold-passing pairs (R4)**; `expansion_pool="top_k"` = [CODE] | `mcs.py` |
| BFS | "BFS over neighbors of e1" | FIFO over in/out edges of both endpoints; each edge dequeued once | [CODE] | `mcs.py` |
| Consistency | "compatible with πV" | injective; source→source, target→target | [CODE] | `mcs.py` |
| Node kinds | — (homogeneous graphs) | — | **[OURS]** nodes of different event kinds never match (`require_same_kind`) | `mcs.py` |
| "Largest" | not specified | `|edges| + |nodes|`, strict `>` | **[CODE] (R5)** | `mcs.py` |
| Consensus target | `m_ij = (1/|S_correct|) Σ_k 1[v_ij ∈ MCS(G_i,G_k)]` (C.2 p.13) | per-reference edge membership | **`m_node` = [PDF] formula**; **`m_ctx` = [OURS]** step supported only if *all* its incoming edges (incl. context) are in the edge map (R6) | `consensus.py` |
| References | correct trajectories only (App. B p.12–13) | correct graphs of the same problem; masks only for incorrect graphs | correct runs of the same task; leave-one-out for correct queries [OURS] | caller |
| Graphs > 15 nodes | — | MCS skipped (no supervision) | **not replicated** | — |

Neither `m_node` nor `m_ctx` is ground-truth step correctness.

## Optional configuration C: structured-field validation [OURS]

`find_mcs(..., field_check=StructuredFieldValidator(query_steps, reference_steps))`
(`gibs/mcs/structured_fields.py`) adds deterministic *rejections* for tool-event pairs that already pass every NLI
threshold:
- different tool names;
- conflicting decision-critical arguments;
- different error status;
- conflicting reservation or user record fields.

It never creates a match that NLI rejected, and every rejection is recorded with the field values in
`MCSResult.rejected`. With `field_check=None` (default) the algorithm is unchanged. Validation against
configurations A and B is in `gibs/validation/REPORT.md`.

## Experimental variants [OURS] (off by default)

| Variant | Switch | Evaluated in |
|---|---|---|
| Symmetric truncation of pairs longer than 512 tokens (each text gets a fair share of the budget; shorter pairs are unchanged) | `DebertaEntailment(overlength="symmetric")` or `.with_overlength("symmetric")` | `gibs/validation/REPORT_variants.md` (C1, C3) |
| Multi-component MCS (component 0 = unchanged `find_mcs`; further globally consistent, one-to-one components) | `gibs.mcs.multi_component.find_mcs_multi` | same (C2, C3) |

The author-code truncation (`overlength="truncate"`) and single-component `find_mcs` remain the defaults.

## Known limitations measured on real data (see `gibs/examples/task48_pair/README.md`)

* Long structured texts exceed 512 tokens (tool texts up to 3,747 tokens across the dataset).
* DeBERTa-MNLI judges near-identical long JSON observations as entailment even when a decision-relevant field
  differs (`status: cancelled`; a passenger DOB), also without truncation. Observation (node) similarity therefore
  does not distinguish such tool results; the operation (edge) text and the mapping constraints must.
* The single-seed BFS MCS is connected: after the first point where two dialogues diverge, later steps are
  usually unmapped even if they match, under the context topology.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r gibs/requirements-mcs.txt
.venv/bin/python -m pytest gibs/tests -q                          # unit tests, stub NLI, no model
.venv/bin/python gibs/run_nli_probe.py                            # 16 real pairs, pre-registered expectations
.venv/bin/python gibs/run_mcs_pair.py --control                   # Task 48 failure vs success (+ control)
```

The NLI cache lives outside the repository (`~/.cache/stepwise_nli/`, override with `STEPWISE_NLI_CACHE`).
