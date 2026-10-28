# C6: pre-registration (written before implementing or computing C6)

Approved scope: the narrow outcome-alignment route proposed in `INSPECTION_outcome_support.md` §6.

C6 is **our adaptation, not the paper's GIBS method**. Nothing below is revised after seeing C6 results; any
deviation will be reported as one.

## 1. Definition

**C6 = C5 plus one additional message-matching route.** Stages 1 and 2 are exactly C5:

1. **Stage 1:** the frozen C4 tool part (`freeze_tool_part` on the stored C4 maps).
2. **Stage 2:** C5 message matching (context edges; a tool predecessor must be stage-1-matched to the reference
   predecessor).
3. **Stage 3 (new, outcome route).** It runs **after** stage 2 has finished. It may only *add* message mappings that
   are consistent with stages 1 and 2, so every C5 mapping is retained. Its candidates are exactly the stage-2
   message-edge candidates that C5 dropped as `dropped_tool_unmatched`: the query message's predecessor is a tool
   call **unmatched in stage 1**.

   Such a candidate is admitted only if **all** of the following hold:
   - **(a) Unchanged candidate checks.** It already passed the unchanged candidate stage, which enforces:
     - message edge NLI ≥ 0.7;
     - message target node NLI ≥ 0.7;
     - source (tool result) node NLI ≥ 0.7;
     - same event kind;
     - structured-field check on the source tool pair: **same tool name, compatible `CALL_FIELDS` arguments**, equal
       error status, compatible record fields.
   - **(b) Exact outcome equality** under the normalization of §2: `outcome_key(query tool) == outcome_key(reference
     tool)`.
   - **(c) Injectivity.** The reference tool node is not mapped by stage 1, and is not outcome-aligned to another
     query tool node. The query tool node is outcome-aligned to at most one reference tool node.
   - **(d) Growth.** Growth uses the unchanged `_grow` / component loop, with a pool restricted to outcome-route
     candidates.

**After stage 3**, every query tool node that was outcome-aligned but is not stage-1-mapped is **removed from the
final node map**. It is recorded separately as `outcome_alignments` and is used only to support the following
message.

As a result:
- **No new tool-call match is introduced.**
- **Tool node and context scores equal C4 bit-for-bit.** The tool node map and the tool-edge map are the stage-1
  maps, and incoming edges of tool nodes are identical in C4 and C6.

Not used, as instructed:
- error-flag-only matching (errors must have identical normalized text);
- semantic similarity of outcomes (outcome equality is exact, not NLI);
- within-run message–result consistency.

## 2. Outcome normalization (`outcome_key`)

For a tool step's observation:

```
error  = bool(observation.error)
body   = content_parsed if the observation parses as JSON, else content_raw
canon  = norm(body), where
         dict   -> {key: norm(value)} serialized with sorted keys
         list   -> [norm(x) ...]            (order kept)
         str    -> whitespace collapsed (" ".join(s.split())); case kept
         int/float -> float
         bool / None -> unchanged
outcome_key = (error, json.dumps(canon, sort_keys=True))
```

This is exact equality of the full result, including fields the structured-field check ignores (e.g. prices), up
to whitespace and int/float representation. Two `Transfer successful` results are equal. `[]` equals `[]`. `Error:
User ? not found` differs from `Error: User user123 not found`.

## 3. Meaning of the message scores

Per (query message, reference), the context indicator is true if **either**:
- **action-supported (C5 route):** the message's context edge is mapped, and its predecessor is matched (stage 1)
  to the reference message's predecessor; or the predecessor is a user turn or ROOT and is matched as in C5;
- **outcome-supported (C6 route):** the message's context edge is mapped to a reference message whose predecessor is
  **the same tool with compatible call fields and an exactly equal result**, but the two tool **calls** were not
  matched. Typically their free-text arguments, such as transfer summaries, fail NLI.

`m_ctx` (C6) = the fraction of references with either route. It is reported **split by route**.

Outcome-supported consensus means:

> "In this fraction of correct runs, a message of the same content followed the same observable tool outcome."

It does **not** mean:
- that the tool call was appropriate or policy-correct;
- that the message is accurate about anything other than the immediate outcome;
- that the two runs performed the same action (their free-text arguments may differ).

## 4. Hypotheses (directional)

| ID | Case | Prediction |
|---|---|---|
| H1 | all tool-call steps | `m_node` and `m_ctx` identical to C4 (bit-for-bit); tool node and tool-edge maps identical to C4 in all 959 pairs |
| H2 | C5 message indicators | every C5 message indicator (node, ctx) that is true stays true in C6. No C6 message mapping that existed in C5 changes its target |
| H3 | T48 valid transfer messages (10) | `m_ctx` 1.000 each (C5: 0.089) |
| H4 | T9 valid transfer messages (14) | `m_ctx` 0.938 each (15 of 16; C5: 0.232) |
| H5 | T25 `6f12b024 s32` | `m_node` = `m_ctx` = 0 (s30 outcome conflicts with every reference booking) |
| H6 | date-of-birth/plan false pairs: `16aac895 s10→1e01a088 s10`, `16aac895 s10→cd5be315 s8`, `51d355a9 s10→bb73aded s10` (C5-supported), and the 4 C5-sample pairs `bb73aded s10→291cfe67 s10`, `d2135fe7 s10→1e01a088 s10`, `1e01a088 s10→8c8332b6 s10`, `2e0c25a6 s10→1e01a088 s10` | **persist unchanged** (their predecessor lookup is stage-1-matched; the outcome route is not involved) |
| H7 | identical empty-search results | any outcome-route match after `search_*` returning `[]` has compatible `origin`/`destination`/`date` (enforced by the call-field check); listed individually |
| H8 | outcome-route matches after errored `get_user_details` | only between identical error texts. Listed and judged individually |

## 5. Failure criteria

Each is an implementation or safety failure and is reported as such.

- **F1.** Any tool-call step whose C6 `m_node` or `m_ctx` differs from C4. Any pair whose tool node map or
  tool-edge map differs from C4. Any tool node in a C6 final node map that is not stage-1-mapped.
- **F2.** Any lost C5 message indicator, or any re-targeted C5 message mapping.
- **F3.** Any outcome-route mapping in which the tool names differ, `CALL_FIELDS` conflict, or `outcome_key`s
  differ (re-checked independently in the analysis).
- **F4.** A non-injective node or edge map, or a reference tool node outcome-aligned to two query tool nodes.
- **F5.** `6f12b024 s32` supported (node or ctx) in any reference.

**Message outcome criteria** (judged; one reviewer, not blind):
- **M1. Every distinct outcome-route (query message, reference message) pair is inspected**, i.e. all of them, not
  a sample. Each is judged with the REPORT_c4 §5 F-b categories:
  - same act;
  - borderline subset;
  - same act with conflicting facts;
  - different act.

  Pairs with identical message text are listed by count and judged "same act" without individual review.
- **M2.** C6 is reported as **not adding false message matches** only if **0** outcome-route pairs are judged
  different act or conflicting facts. Otherwise the count is reported as C6's newly introduced false matches.
- **M3.** Persistence of the H6 pairs is reported. Persistence is expected and is not a C6 failure, but it means C6
  does not address that error class.

## 6. Metrics

- **Valid transfer messages:** per run, `m_ctx` for C3 / C4 / C5 / C6, split by route.
- **Message coverage:** counts of context-supported (message, reference) indicators per task and variant, split for
  C6 into action-supported and outcome-supported.
- **Message `m_node` and `m_ctx` distributions** (six bins), by label, predecessor type and successful/failed run,
  for C3, C4, C5 and C6.
- **Outcome-route admissions by predecessor tool**, and the candidates rejected at stage 3 by reason:
  outcome differs, injectivity, or not grown.
- **Unexpected cases** (valid < 0.5, incorrect ≥ 0.5) for all variants.
- **Cost:** wall time and uncached NLI forward passes (expected 0).

## 7. Implementation constraints

- An opt-in argument on `two_stage.extend_messages` (`outcome_route=False` by default), so **C5 behaviour is
  unchanged**. This is verified by recomputing C5 into a scratch directory and comparing it with the stored
  `results_c5/` (all fields except cost).
- New script `run_c6.py`, writing to `results_c6/`. It reads `results_c4/` and `results_c5/` only.
- Tests:
  - tool invariance;
  - C5 retention;
  - outcome normalization;
  - empty-search arguments;
  - error-text strictness;
  - injectivity;
  - `6f12b024 s32`.

No threshold change, no label change, no GCN, no new data.
