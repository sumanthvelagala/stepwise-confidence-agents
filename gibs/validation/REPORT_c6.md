# C6: C5 + outcome-aligned message matching

Plan: `c6_plan.md` (pre-registered before implementation). Background: `INSPECTION_outcome_support.md`.

**C6 is our adaptation, not the paper's GIBS method.**

**Outcome agreement does not establish policy correctness.** An outcome-supported message means:

> "In this fraction of correct runs, a message of the same content followed the same observable tool outcome."

It does not mean the tool call was appropriate, the two runs took the same action, or the message is accurate about
anything beyond that outcome.

Scope:
- the same 66 pilot trajectories, references and labels;
- no threshold change, no GCN, no new data.

**Evidence tags:**
- **[OBS]**: observed in stored outputs.
- **[VER]**: an independent label.
- **[JUDGED]**: a manual judgement (one reviewer, not blind).

## Bottom line

| Question | Answer |
|---|---|
| Tool scores identical to C4? | **Yes, bit-for-bit.** 315 tool steps and 959 pairs: 0 score, node-map or tool-edge-map differences. 0 outcome-aligned tool nodes in any final node map |
| C5 message matching retained? | **Yes.** 0 C5 node or edge mappings changed; 0 C5 indicators lost |
| T48 / T9 valid transfer messages | **Recovered:** T48 0.089 → **1.000**; T9 0.232 → **0.938** (every run) |
| T25 wrong-booking confirmation `6f12b024 s32` | **Still unsupported:** 0 / 0 |
| Date-of-birth/plan false pairs | **Persist** (7 of 7, unchanged from C5). Outcome alignment does not touch them |
| Empty-search and error-text matches | **None admitted.** The route fired only after `transfer_to_human_agents` |
| Newly introduced false matches (relative to C5) | **Yes, 1 distinct message** (14 reference indicators). Failed-run T9 `7e3e8b73 s20` reports a **prohibited cancellation** and then the transfer. It goes from 0 (C5) to **0.824** (C6), entirely through the outcome route. **M2 fails** |
| Net effect | **C6 message context scores = C3's for all 280 message steps.** Tool scores = C4's. Unlike C3, there is no node-only message support |

## Files

| File | Content |
|---|---|
| `c6_plan.md` | definition, outcome normalization, meaning of the scores, H1–H8, F1–F5, M1–M3 |
| `gibs/mcs/two_stage.py` | `outcome_key`, the shared component loop `_grow_components`, and the opt-in `outcome_route` stage 3 in `extend_messages` |
| `run_c6.py` | `compute` (reads `results_c4/`) and `analyze` (reads `results_pilot/`, `results_c4/`, `results_c5/`) |
| `results_c6/task{48,9,25}_C6.json` | per-reference maps, indicators, `outcome_route_edges`, `outcome_alignments`, stage counters |
| `results_c6/per_step_masks_c6.csv` | 595 steps × A / C0 / C3 / C4 / C5 / C6, with C6 message `m_ctx` split into action route and outcome route |
| `results_c6/c6_summary.json` | checks, coverage, distributions, every outcome-route pair with texts, H6 panel, transfer table |
| `gibs/tests/test_c6.py` | 7 tests (§2) |

Reproduce:

```
.venv/bin/python -B gibs/validation/run_c6.py compute
.venv/bin/python -B gibs/validation/run_c6.py analyze
```

Cost [OBS]: 0.7 s, 1.9 s and 9.5 s, with **0 uncached NLI forward passes**.

**C5 is unchanged.** The default `outcome_route=False` keeps C5's code path. Recomputing C5 with the refactored code
into a scratch directory gives output identical to the stored `results_c5/` in all three tasks (every field except
cost). `results_c5/` itself was not rewritten.

## 1. What C6 adds

**Stages 1 and 2** are exactly C5: the frozen C4 tool part, then message context matching that requires the
predecessor tool call to be stage-1-matched.

**Stage 3 (new)** runs only after stage 2 has finished. Its candidates are the message-edge candidates that C5
dropped because the query predecessor tool call is unmatched in stage 1. A candidate is admitted only if:
- **(a) it already passed the unchanged candidate stage:**
  - NLI ≥ 0.7 for the message edge, the message node and the tool-result node;
  - same kind;
  - **structured-field check on the predecessor tool pair:** same tool, compatible `CALL_FIELDS` arguments, equal
    error status, compatible record fields;
- **(b) the two tool results are exactly equal** after normalization (`outcome_key`):
  - JSON parsed if possible, keys sorted, strings whitespace-collapsed (case kept), numbers as floats;
  - the error flag and the error text are kept;
  - no similarity model is used;
- **(c) it is one-to-one** with everything already mapped or aligned;
- **(d) it grows** with the unchanged component loop.

Outcome-aligned tool nodes are then **removed from the node map** and stored as `outcome_alignments`, so no tool
match is introduced.

Not used, as instructed:
- error-flag-only matching;
- outcome similarity;
- within-run message/result consistency.

## 2. Tests [OBS]

`gibs/tests/test_c6.py`, 7 tests:

| Test | Shows |
|---|---|
| `outcome_key` | key order, whitespace and int/float are normalized; `[]` = `[]`; error texts `User ? not found` ≠ `User user123 not found`; error ≠ non-error; a price difference ≠ |
| Real T48 transfer pair (`59810305` vs `c890f90b`; summaries differ) | the transfer message is supported only in C6; `outcome_alignments == {N:s4: N:s8}`; tool indicators equal across C4, C5 and C6; the aligned tool node is not in the node map; every C5 mapping retained |
| Empty search with conflicting dates, permissive NLI | not outcome-supported (call-field check) |
| Semantically similar but unequal results (`Transfer successful` vs `Transfer completed`, NLI stub 0.99) | rejected |
| Error outcomes with different error texts | rejected |
| Two query transfers vs one reference transfer | a single alignment; one message supported; maps injective |
| T25 `6f12b024 s32` vs `0f0f7358`, permissive NLI | unsupported; tool indicators equal C4 |

Results: **93 GIBS tests passed** (86 earlier + 7 new) and **52 NIBS passed, 1 skipped**, with no failures.

## 3. Pre-registered checks [OBS]

| Check | Result |
|---|---|
| **F1** tool invariance (315 steps; 959 pairs: tool node map, tool-edge map; non-frozen tool nodes in final maps) | **0 / 0 / 0** |
| **F2** C5 retention (changed node mappings, changed edge mappings, lost indicators) | **0 / 0 / 0** |
| **F3** outcome-route edges re-checked (same tool, compatible call fields, equal `outcome_key`, consistent alignment) | 276 edges, **0 violations** |
| **F4** injectivity (node map ∪ alignments, edge map) | 0 violations |
| **F5** `6f12b024 s32` supported | **0** references |
| H1 tools = C4 | ✓ |
| H2 C5 retained | ✓ |
| H3 T48 valid transfer messages = 1.000 | ✓ all 10 |
| H4 T9 valid transfer messages = 0.938 | ✓ all 14 |
| H5 `6f12b024 s32` 0 / 0 | ✓ |
| H6 the 7 date-of-birth/plan pairs persist | ✓ all 7 still context-supported (as in C5) |
| H7 empty-search outcome matches | none admitted |
| H8 error-text outcome matches | none admitted. One T25 errored-booking candidate with identical error text was blocked by injectivity, not admitted |
| **M1** every outcome-route pair inspected | ✓ 276 indicators = 276 distinct (query message, reference message) pairs; all reviewed (§5) |
| **M2** 0 outcome-route pairs judged different act or conflicting facts | **✗**: 14 pairs from one query message (§5) |
| **M3** H6 pairs | persist; C6 does not address this error class |

## 4. Results [OBS]

### 4.1 Outcome-route admissions

| Task | Stage-3 candidates | Rejected: outcome differs | Admitted | Predecessor tool |
|---|---|---|---|---|
| T48 | 82 | 0 | 82 | `transfer_to_human_agents` (all) |
| T9 | 194 | 0 | 194 | `transfer_to_human_agents` (all) |
| T25 | 1 | 0 | 0 (injectivity) | an errored `book_reservation` |

Every admission follows a transfer whose free-text summary failed NLI. The result is always the identical string
`Transfer successful`.

### 4.2 Valid transfer messages ([VER] valid), `m_ctx`

| Task | C3 | C4 | C5 | **C6** | C6 action route / outcome route |
|---|---|---|---|---|---|
| T48 (10) | 1.000 | 1.000 | 0.089 | **1.000** | 0.089 / 0.911 (mean) |
| T9 (14) | 0.938 | 0.996 | 0.232 | **0.938** | 0.232 / 0.706 (mean) |
| T25 (1, failed run) | 0 | 0 | 0 | 0 | — (no successful run transfers) |

In T9 the missing reference is `7cd3469e`, which announces a transfer but never calls the tool (REPORT_pilot §9.3).

Pre-registered unexpected cases (valid < 0.5 / incorrect ≥ 0.5), node and ctx:

| Variant | T48 | T9 | T25 |
|---|---|---|---|
| C5 | 10 / 10 | 12 / 12 | 1 / 1 |
| **C6** | **0 / 0** | **0 / 0** | 1 / 1 (`51d355a9 s22`, unmatchable) |

### 4.3 Message coverage: context-supported (message, reference) indicators

| Task | C3 (`ctx` / node-only) | C4 | C5 | **C6** (of which outcome route) |
|---|---|---|---|---|
| 48 | 419 / 0 | 423 | 337 | **419** (82) |
| 9 | 693 / 29 | 725 | 499 | **693** (194) |
| 25 | 969 / 180 | 1,220 | 969 | **969** (0) |

**C6 message `m_ctx` equals C3 `m_ctx` for all 280 message steps** [OBS]. C6 message `m_node` differs from C3 for 60
steps, because C6 never gives node-only message support and C3 did. Equivalently:
- C6 recovers exactly the context support that C5 removed after transfer calls;
- it adds no message support beyond C3's context-supported set.

### 4.4 Message `m_ctx` distributions

Bins: `[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`. These are messages after a transfer, from successful runs.

| Task | C3 | C4 | C5 | C6 |
|---|---|---|---|---|
| 48 (10) | 0 0 0 0 0 10 | 0 0 0 0 0 10 | 2 8 0 0 0 0 | 0 0 0 0 0 10 |
| 9 (16) | 0 0 0 0 16 0 | 0 0 0 0 3 13 | 3 4 7 2 0 0 | 0 0 0 0 16 0 |

All other message groups (predecessor: none, user turn, other tool) are identical in C5 and C6, and identical to C3
in `m_ctx`. Full tables are in `c6_summary.json → tasks.*.distributions`.

### 4.5 Specific cases

| Case | C3 | C4 | C5 | **C6** |
|---|---|---|---|---|
| T25 `6f12b024 s32` (node / ctx references of 19) | 7 / 0 | 15 / 15 | 0 / 0 | **0 / 0** |
| T25 valid bookings (`m_node` / `m_ctx`) | 1.00 / 0.269 | 1.00 / 0.854 | 1.00 / 0.854 | **1.00 / 0.854** |
| T9 `7e3e8b73 s20` (failed run; reports the prohibited IFOYYZ cancellation) | 0.824 | 0.824 | 0 | **0.824** (all through the outcome route) |
| H6 date-of-birth/plan pairs, context-supported | 7 / 7 | 6 / 7 mapped to that step | 7 / 7 | **7 / 7** |

## 5. Every outcome-route match, inspected [JUDGED]

- **276 indicators** (T48 82, T9 194), each a distinct (query message, reference message) pair.
- **218** have identical message text: the policy transfer message on both sides, after `Transfer successful`.
  Judged "same act".
- **58** have non-identical text. They fall into 5 distinct text pairs, each reviewed:

| # | Indicators | Query → reference | Judgement |
|---|---|---|---|
| 1 | 14 | **`7e3e8b73 s20`** (failed run): "Your reservation **IFOYYZ has been cancelled**. I'm transferring you … YOU ARE BEING TRANSFERRED…" → the bare policy transfer message, in 14 references | **same act with conflicting facts.** The query also reports an incorrect earlier action ([VER] `7e3e8b73 s16` cancel IFOYYZ is incorrect) that no reference performs. Support comes from the shared transfer outcome. This is the false positive predicted in INSPECTION §6 ("messages that also narrate earlier actions") |
| 2 | 12 | the policy message (valid; 12 successful runs) → `2f77c770 s8`: "I'm sorry, but I'm unable to process those cancellations directly. I've forwarded your request … YOU ARE BEING TRANSFERRED…" | borderline subset: same primary act (transfer announcement) plus a refusal |
| 3 | 12 | `2f77c770 s8` → the policy message | borderline subset (reverse of #2) |
| 4 | 10 | the policy message (valid; 10 runs) → `ed3e4cc7 s10`: "I'm sorry, but I'm unable to process the cancellations … I'll transfer you … YOU ARE BEING TRANSFERRED…" | borderline subset |
| 5 | 10 | `ed3e4cc7 s10` → the policy message | borderline subset |

Summary:
- **Different act:** 0.
- **Conflicting facts:** 1 distinct message, 14 indicators.
- **Borderline subset:** 44 indicators.
- **Same act:** 218 indicators.

The judgement of #2–#5 matches the identical case in the C3 baseline sample (REPORT_c4 §5, C3 #22).

**Why #1 happens.** The outcome route checks only the **immediately preceding** tool outcome. The message reports
two things:
- the transfer, which matches the outcome;
- an earlier prohibited cancellation, which the outcome cannot reflect.

Message-level NLI passes because the reference text (the policy message) is entailed by the query text. C3 and C4
supported the same message to the same degree (0.824); C5 alone suppressed it, as a side effect of its strictness.

## 6. Interpretation

1. **Tool calls.** C6 = C5 = C4. The invariance requirement holds exactly.
2. **Messages.** The outcome route recovers the valid transfer messages completely, and does so only through the
   exact `Transfer successful` outcome. In the pilot it never fired for searches, errors or bookings, so the
   guards against empty-search and error-text matches were not exercised on real data. They are unit-tested only.
3. **C6 message context support ends up exactly equal to C3's.** The strictness C5 added was concentrated entirely
   on messages after transfers. C6 removes it, so C6 also re-admits C3's one context-supported message that relays
   an incorrect action (`7e3e8b73 s20`). Against C5, this is a newly introduced false match (M2 ✗). Against C3, it
   is not new.
4. **The wrong-booking confirmation stays unsupported** in C6 for a structural reason: no reference has an equal
   booking outcome. That protection does not extend to messages after outcome-identical tools, i.e. transfers, which
   can narrate anything.
5. **The date-of-birth/plan confusions are untouched.** They follow a stage-1-matched lookup with identical
   outcomes; the difference lies in dialogue state.

## 7. Recommendation

- **C6 vs C5.** C6 trades 1 newly supported message relaying an incorrect action (0 → 0.824) for full recovery of
  24 valid transfer messages (0.089 / 0.232 → 1.000 / 0.938). By the pre-registered rule M2, **C6 is reported as
  adding a false message match**. The trade-off is for you to decide. Under neither variant should message scores
  be treated as validated.
- **If adopted, C6 should be described as** "C4 tool consensus + C3-equivalent message context consensus without
  node-only support", with message scores marked outcome-consistent, not correct.
- **For any message that follows an outcome-identical tool (transfers), the score carries no information about the
  rest of the message's content.** A possible next check, not proposed for implementation here, would restrict the
  outcome route to messages whose text matches the reference message closely, e.g. identical after normalization.
  In the pilot that would keep the 218 identical policy-message indicators and drop all 58 others, including #1.
  That is a stricter message comparator, not an outcome rule, and it would need its own pre-registration.
- **GCN suitability:** unchanged. Messages have no independent labels except the policy transfer message; 83% of
  steps are unverified; the discriminative incorrect-step evidence is one case.

## 8. Limitations

- Three tasks; one reviewer; non-blind judgements.
- The outcome route was exercised only on transfers. Empty-search, error-text and booking-outcome behaviour is
  covered by unit tests on synthetic graphs, not by pilot data.
- `outcome_key` keeps string case and list order. Outcomes that differ only in those would not align. None was
  observed.
- C6 depends on stored C4 results. A change to C4 requires recomputing C5 and C6, which takes seconds from cache.

## 9. Integrity [OBS]

- **REPORT_c5.md:** only the approved erratum was added (§4.2 and §5; original text struck through and marked).
  No result was revised.
- **Unchanged:** `results_pilot/`, `results_c4/`, `results_c5/`, labels and thresholds.
- **New:** `c6_plan.md`, `run_c6.py`, `results_c6/`, `tests/test_c6.py`, this report.
- **Modified library file:** `gibs/mcs/two_stage.py`, with an opt-in stage 3 and a refactored loop. C5 output was
  verified to be identical.
- Nothing was committed.

Stopped for review: no GCN, no threshold change, no corpus expansion.
