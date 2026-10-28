# C5: pre-registration (written before implementing or computing C5)

Design chosen by the reviewer: **option 1, two-stage constrained matching**.

C5 is **our adaptation, not the paper's algorithm**. Nothing below is revised after seeing C5 results; any
deviation will be reported as one.

## 1. Facts this plan relies on (checked in code and on the 66 pilot runs; no C5 computation)

- **C4 graph (`paper_literal`):**
  - every tool call has its data edges, or a single ROOT edge if it has none;
  - every message and user turn has a single ROOT edge;
  - all edges into a tool node are data or ROOT edges.
- **C3 graph (`event_context`):** every message has one incoming context edge from the immediately preceding event.
  Messages never receive data edges.
- **No agent message is a data-dependency source** in any pilot run. User turns are: 44 / 86 / 158 data edges in
  T48 / T9 / T25.
- **Agent messages by predecessor:**
  - 149 follow a tool call (T48 40, T9 29, T25 80);
  - 65 follow a user turn (27, 16, 22);
  - 66 are the first event, the greeting (23, 21, 22);
  - **none** follows another agent message.

  As a result, a message can be "node-only" only through a data edge or through the next message's context edge,
  and neither exists in the pilot. So a message's `m_node` should equal its `m_ctx`.
- **Valid transfer messages always follow a transfer call** that C4 rarely matches. C4 `m_node` of the preceding
  transfer call:
  - T48: 0–0.111;
  - T9: 0–0.5;
  - T25: 0.
- The NLI texts of C5's message context edges (operation and source/target nodes) are the same texts C3 already
  scored. The cache should cover them, and uncached forward passes are counted and reported.

## 2. C5 definition

### Graph (`project_c5`, new function; existing projections unchanged)

- **Tool-call events:** exactly C4's edges (data edges, or a ROOT edge if none), with identical edge ids.
- **User turns:** exactly C4's edges (ROOT edge). Not scored.
- **Agent messages:**
  - **one context edge from the immediately preceding event** (tool result, user turn or message), with the same
    id and text as C3's edge;
  - the first event of a run keeps its ROOT edge (in the pilot this is always the greeting `s0`);
  - **no other message has a ROOT edge**, so ROOT-only matching cannot bypass the context constraint.

### Stage 1: frozen tool part (read from `results_c4/task*_C4.json`, never recomputed)

For each (query, reference) pair, using C4's stored `edge_map` and `node_map`:
- **Frozen edges:** every C4 edge mapping whose query edge ends at a tool-call node. That is all tool data and ROOT
  edges, mapped to the same reference edge.
- **Frozen nodes:** the endpoints of the frozen edges, mapped as in C4. These are:
  - tool nodes;
  - user turns that are data sources;
  - ROOT.
- **Check:** the frozen tool-node set must equal the set of tool nodes in C4's `node_map`. Any mismatch is an error.
- **Dropped:** C4's mappings of messages and user turns made only through ROOT edges are **not** carried over.

### Stage 2: message extension (new function `extend_messages`)

1. **Candidates.** Edge pairs on the C5 graphs, computed by the unchanged `find_mcs` candidate stage:
   - NLI edge ≥ 0.7, target node ≥ 0.7, source node ≥ 0.7 (R3);
   - same event kind;
   - structured-field rejection (C validator).
2. **Allowed candidates.** Only candidates whose query edge **ends at an agent message** (message context edges, or
   the first event's ROOT edge). Tool edges and user-turn edges are never added.
3. **Tool-source rule** (requirement 3). If the query edge's source is a tool node, the candidate is allowed **only
   if** that tool node is frozen-mapped to exactly the candidate's reference source.
   - If the tool node is unmatched in C4, the candidate is dropped and counted as `dropped_tool_unmatched`.
   - If it is matched to a different reference node, it is dropped and counted as `dropped_tool_conflict`.
   - Stage 2 therefore never maps a new tool node.
4. **Growth.** Starting from the frozen maps, components are added with the unchanged multi-component rule
   (`_grow`):
   - seeds: the top 10 remaining candidates that are consistent with the global maps;
   - BFS over allowed candidates only;
   - largest gain wins; stop when no consistent candidate remains;
   - node and edge maps stay one-to-one across stages.
5. **Unchanged:** thresholds 0.7, top-K 10, symmetric truncation, model and cache, references (leave-one-out over
   successful runs), labels.

### Handling by predecessor (requirement 4)

| A message's predecessor | Context support from reference k requires |
|---|---|
| a tool call matched in C4 to the tool call right before the reference message | the message edge to pass NLI and kind checks (fields are checked on the source tool pair) |
| a tool call **unmatched** in C4, or matched to another reference call | **impossible**; no context support from that reference |
| a user turn | that user turn mapped to the reference message's predecessor user turn: by NLI ≥ 0.7 as the edge source, consistent with any frozen data-source mapping of that turn, one-to-one |
| another agent message | that message mapped to the reference message's predecessor message, consistent with stage 2 |
| none (first event) | the reference message is also a first event (ROOT ↔ ROOT) |

### Scores

- `m_node` = the node is mapped. For a message this can also happen as the **source** of the next message's context
  edge, with no support for its own context; such cases are reported separately as "node-only".
- `m_ctx` = all incoming edges mapped, i.e. the message's own context edge.
- **Only `m_ctx` is treated as context-supported.** Node-only message support is reported and never counted as
  support in the comparisons.

**Guarantee (by construction).** Tool-node mappings and tool-edge mappings equal C4's, and incoming edges of tool
nodes are identical in C4 and C5. So **every tool-call `m_node` and `m_ctx` equals C4** for every step (failed,
unverified, all labels). This is checked numerically.

## 3. Expected behaviour (directional; checked after computing)

| ID | Case | Prediction |
|---|---|---|
| E1 | all tool-call steps (595-step table, tool rows) | `m_node` and `m_ctx` identical to C4, to the last digit |
| E2 | T25 `6f12b024 s32`: confirmation of the wrong booking s30, which is unmatched in all 19 C4 references | `m_ctx` = 0 (C4: 0.789; C3: 0). `m_node` = 0 unless it is the source of a following message edge (reported) |
| E3 | the C4 false message pairs: `bb73aded s12 ↔ 1e01a088 s10` (both directions), `bb73aded s10 ↔ 1e01a088 s14`, `2aca18ff s26 ↔ bb73aded s20` | not context-supported in C5 (the predecessors differ). Not guaranteed; reported per pair |
| E4 | T25 valid bookings | identical to C4 (1.00 / 0.854) |
| E5 | valid transfer messages (T48 10, T9 14) | **large loss of coverage**: `m_ctx` ≤ the C4 `m_node` of the preceding transfer call, i.e. T48 ≤ 0.111, T9 ≤ 0.5 (C3 and C4: about 1.0). This is the **expected unavoidable conflict** between tool invariance and requirement 3, and it will be documented, not relaxed |
| E6 | sampled message false-match rate (F-b) | lower than C4 |

## 4. Failure criteria

Any of F1–F4 is an implementation failure and is reported as such.

- **F1 (tool invariance).** Any tool-call step with `m_node` or `m_ctx` different from C4, any label. Also: any
  stored pair whose tool-node map or tool-edge map differs from C4's.
- **F2 (injective messages).** A message node mapped to a non-message node, or two query nodes mapped to one
  reference node.
- **F3 (context consistency).** A mapped message context edge whose query source is a tool node not frozen-mapped
  to the reference source. Also: a context-supported message (`ctx` indicator true) whose predecessor tool call is
  unmatched for that reference.
- **F4 (requirement 3, T25).** `6f12b024 s32` with a ctx indicator true for any reference.
- **F5 (inherited safety).** Any incorrect step ≥ 0.5. This is implied by F1, because all incorrect steps are tool
  calls.

**Message outcome criteria** (judged, not implementation failures):
- **M1.** In the known false-pair panel (§5.2), any pair that is **context-supported** in C5 is a C5 false match.
- **M2.** Sampled F-b different-act rate (§5.3): C5 is "better for messages than C4" only if its count is lower
  than C4's on the same sampling rule.
- **M3.** Valid-message coverage: mean valid transfer-message `m_ctx` per task, against C3 and C4. If it falls
  below 0.5 in T48 or T9 (predicted, E5), C5 is reported as **over-restrictive for messages**.

## 5. Metrics

### 5.1 Main tables

Per task and variant (C3, C4, C5; A and C0 for reference), by label × successful/failed, for `m_node` and `m_ctx`:
counts, mean, median and six-bin distributions. Also, C5 − C4 per step (messages only; tool steps must be 0).

### 5.2 Known false-pair panel

For each pair: whether the query step is mapped to that reference step in C3, C4 and C5, and whether it is
context-supported.

- C4 different-act (F-b) pairs: `bb73aded s12 → 1e01a088 s10`; `1e01a088 s10 → bb73aded s12`;
  `bb73aded s10 → 1e01a088 s14`; `2aca18ff s26 → bb73aded s20`.
- C3 different-act pairs (post-hoc sample, REPORT_c4 §5): `16aac895 s10 → 1e01a088 s10`;
  `16aac895 s10 → cd5be315 s8`; `51d355a9 s10 → bb73aded s10`.
- Wrong-booking confirmation `6f12b024 s32` → its mapping in each of the 19 references.

### 5.3 Message false-match sample (same rule for C3, C4 and C5)

- **Population:** (query message, reference) pairs where the query message is unverified, its node is mapped, and
  the two message texts are not identical.
- **Sample:** 30 per variant, `random.Random(0).sample`.
- **Judgement:** the F-b categories of REPORT_c4 §5 (same act / borderline subset / same act with conflicting facts
  / different act).
- **Reuse:** the C3 sample already judged in REPORT_c4 used this exact rule and is reused. C4 and C5 are sampled
  fresh.
- **C5 split:** context-supported vs node-only, reported separately.

### 5.4 Coverage

- Number of mapped message pairs (node and ctx), per variant.
- Valid transfer messages: `m_node` and `m_ctx` per run.
- Counts of `dropped_tool_unmatched` and `dropped_tool_conflict`, i.e. message candidates removed by the tool-source
  rule, per task.

### 5.5 Cost

Wall time and uncached NLI forward passes.

## 6. Tests (added before computing)

1. **Tool invariance.** Real T25 pair and synthetic graphs, NLI stub that accepts everything: C5 tool-node maps,
   tool-edge maps and tool indicators equal the stage-1 input.
2. **Injective message mappings.**
3. **Context consistency.** Every mapped message edge with a tool source matches the frozen tool map. A message
   after an unmatched tool call gets no context support.
4. **T25 `6f12b024 s32`** is not context-supported against `0f0f7358`, even with permissive NLI.
5. **Projection.** Tool and user edges are identical to C4. Messages have exactly one incoming edge, from their
   predecessor (ROOT only for the first event).
6. **Message after a user turn** needs a predecessor user-turn match. **First message** matches only a first
   message.

## 7. Not done

No GCN, no threshold change, no label change, no new tasks, no change to `run_pilot.py`, `run_c4.py`, the library
behaviour of existing variants, `results_pilot/` or `results_c4/`. The semantic "confirmation supported by tool
outcome" check is out of scope; it is only discussed as a possible extension.
