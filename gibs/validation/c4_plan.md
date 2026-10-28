# C4: pre-registration (written before any C4 computation)

Milestone 2: reliable step-level similarity and consensus scoring. This plan was written after
`REPORT_pilot.md` and before running C4. Nothing below is revised after seeing C4 results. Any deviation will be
reported as a deviation.

## 1. What the code actually does (verified, not assumed)

**Step graph (`gibs/graph/step_graph.py`, v0.2).** Two edge types:
- `temporal`: consecutive events.
- `data_dependency`: from the earliest earlier event whose raw visible text contains a value used in a tool
  call's arguments.

The tool response is **not an edge**. Each tool call and its observation are folded into one AgentStep. In the
projection, the call is the operation (the edge text, `op_text`) and the observation is the result node
(`result_text`). Only tool calls receive data-dependency edges; messages and user turns never do.

**Projection (`gibs/graph/event_projection.py`):**
- `event_context` (used by C0/C3): a `context` edge from the immediately preceding event, plus one `data` edge per
  dependency source. Where both connect the same pair of events they are merged into one edge with roles
  `[context, data]`.
- `paper_literal` (used by A): only `data` edges. An event with no data dependency gets a single edge
  `ROOT → event` with role `root`, which is the author code's `NodeRaw` construction.
- All edges into an event carry the same operation text. Node and edge texts are identical in both topologies.

**Checked on all 66 pilot runs:**
- The data-edge set (source → target) is **identical** in the step graph, in `event_context` and in
  `paper_literal`, for every run.
- Removing context edges therefore drops no data dependency.

| Task | event_context edges: context-only / context+data / data-only | paper_literal edges: data / root | Events hanging from ROOT in paper_literal: agent messages / user turns / tool calls |
|---|---|---|---|
| 48 | 205 / 24 / 25 | 49 / 181 | 90 / 90 / 1 |
| 9 | 221 / 24 / 114 | 138 / 132 | 66 / 66 / 0 |
| 25 | 358 / 43 / 292 | 335 / 268 | 124 / 124 / 20 |

**Consequences that C4 inherits** (these are what C4 tests):
1. Every agent message and user turn is attached only to ROOT. They are matched **without positional context**:
   edge text = node text = the utterance, and the source is ROOT ↔ ROOT = 1.
2. ROOT is shared, so the whole graph is one connected component through ROOT. Multi-component matching should
   matter less than in C3.
3. `m_ctx` (all incoming edges mapped) becomes:
   - for a tool call: all of its data-dependency edges mapped;
   - for a message, or a dependency-free call: its single ROOT edge mapped (≈ `m_node`).

**Field checks on ROOT-sourced edges (`StructuredFieldValidator.__call__`):**
- The target pair is checked whenever both endpoints are tool results.
- The source pair is checked only when both sources are tool results; ROOT is skipped.

So a conflicting booking is rejected even when it hangs from ROOT. A unit test will cover this.

## 2. C4 definition: the only difference from C3

| Setting | C3 | C4 |
|---|---|---|
| Projection topology | `event_context` | **`paper_literal`** |
| NLI | DeBERTa-large-MNLI `7296194b`, max of both directions, author string encoding | same |
| Overlength | symmetric truncation [OURS] | same |
| τe = τv = 0.7, top-K = 10, source-node threshold (R3), all-candidates pool, size = edges + nodes | — | same |
| `require_same_kind` [OURS] | True | same |
| Structured-field rejection [OURS] | on | same |
| Matcher | `find_mcs_multi` (globally consistent multi-component) [OURS] | same |
| Queries / references | leave-one-out over successful runs (run_pilot.load_runs) | same |
| Labels | `step_verification.classify_steps` | same, unchanged |

**Implementation.** No library change. C4 is a variant definition in a new script `run_c4.py`:
- it copies C3's settings and sets `topology="paper_literal"`;
- outputs go to a new directory `results_c4/`;
- `run_pilot.py`, `results_pilot/` and every other existing file stay untouched;
- A/C0/C3 values are read from `results_pilot/` read-only.

C4 is therefore our adaptation as well. It is A's topology (the author-code construction) combined with C3's
matching safeguards. It is **not** the paper's algorithm.

## 3. Hypotheses (directional, with the C3 value for comparison)

| ID | Case | C3 value | Prediction for C4 |
|---|---|---|---|
| H1 | T25 incorrect booking `6f12b024 s30` | 0 / 0 | stays **0 / 0** (field check on the target) |
| H2 | T25 19 valid bookings, `m_ctx` | mean 0.269 | rises to **≥ 0.70** (the C3 "node & all data edges" rate is 0.854); `m_node` stays 1.0 |
| H3 | T48 `5b5eaa71 s2` | 0.667 | **0.667**: the 3 O references are still blocked by R3 (opening turns 0.191), and the 6 L references match |
| H4 | T48 gold lookups in the other O runs (07ec0bf6, 59810305, 78c107ed; failed 058388c8, 4a280c26, d5456653, fcce7c71) | 0.22–0.33 | rise to **≥ 0.85** (as in A: O×L pairs map once the context edge is gone) |
| H5 | T9 gold searches | node 0.50 / 0.529; ctx 0 for 7cd3469e, 49f89baf, 71270d8b | node stays **at the pool cap** (0.500 successful, 0.529 failed) and **never above it**; ctx of the three rises above 0 |
| H6 | Transfer messages (T48, T9) | node 1.00 | stay ≥ 0.9 |
| H7 | All incorrect steps (23) | all 0 | all < 0.5 on both targets |
| H8 | Cross-kind mappings | 0 | 0 (`require_same_kind`) |

## 4. Failure criteria (any one ⇒ C4 is reported as unsafe and not recommended)

- **F1.** Any `incorrect` step with `m_node` ≥ 0.5 or `m_ctx` ≥ 0.5.
- **F2.** Any final mapped pair of tool steps whose structured fields conflict (`compare_tool_events` hard reasons),
  or that uses different tools. This is audited over **all** mapped tool pairs of all queries and references, not
  only labelled steps.
- **F3.** Any cross-kind mapping of an agent step.
- **F4.** Any valid T9 gold search with `m_node` above its pool cap. Exceeding the cap is only possible by matching
  a reference that does not perform the gold search.
- **F5.** A false match among newly matched steps, judged by the rules of `variants_criteria.md`:
  - **F-a**: incorrect step;
  - **F-b**: different action or communicative act, judged manually from the texts;
  - **F-c**: structured conflict.

  Reviewed set, fixed now:
  - every newly matched (C3 → C4) or re-mapped **labelled** step;
  - every newly matched or re-mapped **tool-call** step that changes in more than 0 references;
  - a random sample of **30** newly matched or re-mapped (query step, reference) **message** pairs (seed 0).

  F-b judgements on unverified messages are reported as a rate with the sample size. They are not treated as
  verified labels.

"Worse" (reported, not a safety failure): the mean valid-step `m_node` in any task drops by more than 0.05
relative to C3.

## 5. Metrics

Per task and variant (A, C0, C3 read from `results_pilot/`; C4 new):
- counts by label;
- for `m_node` and `m_ctx`: mean, median and the six-bin distribution `[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`,
  by label × successful/failed, and for valid steps by type;
- the pre-registered unexpected cases (valid < 0.5; incorrect ≥ 0.5);
- per-step C4 − C3 changes (increased / decreased);
- the T48 O/L lookup matrix;
- the reference-count curve, with the same k and 50 subsets with seed 0 as in `run_pilot.analyze`;
- the positional-drift distribution of mapped agent-step pairs:
  |relative position in query − relative position in reference|, where relative position = step index / number of
  agent steps. This is descriptive, because C4 matches messages without position;
- wall time and uncached NLI forward passes.

**AUROC** (valid = positive, incorrect = negative; score = mask; ties count ½):
- Computed **only** for tasks with ≥ 5 labelled positives **and** ≥ 5 labelled negatives: T48 (33 / 13) and
  T9 (27 / 8).
- Not computed for T25 (20 / 2) or pooled, because task differences would dominate.
- Disclosed with the AUROC: 22 of the 23 negatives have no same-tool counterpart in any successful run
  (REPORT_pilot §9.2). AUROC in T48 and T9 therefore mostly measures whether valid steps get any support, not
  whether a matcher discriminates. The only discriminative negative (T25 `6f12b024 s30`) is reported on its own.

## 6. Cases examined individually

1. T25 `6f12b024 s30`: mapping and rejection reasons against every reference.
2. T25 valid bookings: edge-level mapping rates.
3. T48 `5b5eaa71 s2`: per reference, using the same NLI scores as in REPORT_pilot §6.
4. T9 gold searches: values, pool cap and mapped reference steps.

## 7. Not done

No GCN, no full-corpus scoring, no threshold change, no label change, no synthetic case reported as a benchmark
result (unit tests use synthetic graphs and are labelled as such), and no change to `results_pilot/`.
