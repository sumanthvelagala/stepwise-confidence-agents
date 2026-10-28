# C5: two-stage constrained matching (frozen C4 tool part + message context)

Plan: `c5_plan.md` (pre-registered before implementation). C5 is **our adaptation, not the paper's algorithm**.

Scope:
- the same 66 pilot trajectories (T48, T9, T25);
- the same leave-one-out successful references and the same independent labels;
- no threshold change, no GCN, no new tasks.

**Evidence tags:**
- **[OBS]**: observed in stored outputs.
- **[VER]**: an independent label.
- **[HYP]**: untested.
- **[JUDGED]**: a manual judgement (one reviewer, not blind).

## Bottom line

| Question | Answer |
|---|---|
| Tool calls identical to C4? | **Yes, exactly.** 315 tool steps and 959 (query, reference) pairs: 0 differences in scores, node maps or tool-edge maps (F1) |
| New tool-level false matches or lost valid tool matches? | **None.** Tool scores and maps are C4's, which had 0 structured conflicts, 0 cross-tool and 0 cross-kind mappings |
| T25 wrong-booking confirmation (`6f12b024 s32`) | **0 / 0** in C5, against C4 0.789 / 0.789 and C3 0.368 / 0 |
| The 4 C4 different-act message pairs | **None** is mapped in C5 |
| Message false matches overall | **Not reduced relative to C3.** C5's context-supported message scores **equal C3's** for 253 of 280 message steps, so C3's NLI-level false matches remain (M1 fails). On the same sampling rule: 4 / 30 different-act pairs for C5, 2 / 30 for C4, 3 / 30 for C3 (M2 fails; samples too small to separate) |
| Valid-message coverage | **Lost for transfer messages, as predicted (E5, M3 fails).** T48 1.00 → 0.089, T9 0.996 → 0.232. Cause: C4 rarely matches the preceding transfer call, because the free-text summaries differ |
| Is C5 preferable? | **For tools: same as C4.** **For messages: safer than C4 and stricter than C3**, but not more precise than C3, and over-restrictive for valid transfer messages (§8) |

## Files

| File | Content |
|---|---|
| `c5_plan.md` | design, handling rules, expectations E1–E6, failure criteria F1–F5 / M1–M3, metrics |
| `gibs/mcs/two_stage.py` | `project_c5`, `freeze_tool_part`, `extend_messages` (new module; no existing code changed) |
| `run_c5.py` | `compute` (reads `results_c4/` read-only, resumable) and `analyze` |
| `results_c5/task{48,9,25}_C5.json` | per-reference maps, indicators and stage-2 counters |
| `results_c5/per_step_masks_c5.csv` | 595 steps × A / C0 / C3 / C4 / C5 (`m_node`, `m_ctx`), plus each step's predecessor type |
| `results_c5/c5_summary.json`, `results_c5/tables_c5.md` | checks, distributions, panel, samples, coverage |
| `results_c5/message_review.json` | the manual judgements of the three 30-pair samples |
| `gibs/tests/test_c5.py` | 10 tests (§2) |

Reproduce:

```
.venv/bin/python -B gibs/validation/run_c5.py compute
.venv/bin/python -B gibs/validation/run_c5.py analyze
```

Cost [OBS]: 0.7 s, 1.9 s and 9.3 s (T48 / T9 / T25), with **0 uncached NLI forward passes**.

## 1. What C5 does

**Graph (`project_c5`):**
- Tool calls and user turns have exactly C4's edges, with identical ids: data edges, or a ROOT edge if none.
- Every agent message except the first event has **one** context edge from its immediate predecessor. This is C3's
  edge, same id and text.
- Only the first event (the greeting `s0` in every pilot run) keeps a ROOT edge, so no other message can be matched
  through ROOT.

**Stage 1 (frozen).** From the stored C4 result of each pair: every edge mapping that ends at a tool node, and its
endpoints (tool nodes, user turns that are data sources, ROOT).
- A coverage check confirmed that the frozen tool-node set equals C4's tool-node set in every pair.
- C4's message and user-turn mappings made through ROOT edges are discarded.

**Stage 2:**
1. Candidates come from the unchanged `find_mcs` candidate stage: NLI ≥ 0.7 for edge, target and source; same kind;
   structured-field rejection.
2. Only candidates whose query edge ends at an agent message are kept.
3. A candidate whose source is a tool node is kept only if stage 1 maps that tool node to exactly the reference
   source.
4. Growth uses the unchanged multi-component `_grow`, one-to-one with the frozen maps.
5. Invariants are asserted at runtime and unit-tested.

**Handling by predecessor:**

| Predecessor | Message steps (T48 / T9 / T25) | Context support from a reference requires |
|---|---|---|
| tool call matched by C4 to the reference message's predecessor | 149 in total (40 / 29 / 80) | edge NLI ≥ 0.7 and target ≥ 0.7. The source pair is the frozen tool pair, already field-checked |
| tool call unmatched by C4, or matched elsewhere | (same steps) | impossible (counted as `dropped_tool_unmatched` / `dropped_tool_conflict`) |
| user turn | 65 (27 / 16 / 22) | that user turn ↔ the reference predecessor turn, NLI ≥ 0.7, one-to-one, consistent with frozen data-source mappings |
| another agent message | 0 | (rule defined; not exercised in the pilot) |
| none (first event) | 66 (23 / 21 / 22) | the reference message is also a first event |

**Message scores.** `m_ctx` is the score for messages, because it requires the message's own context edge. In the
pilot **C5 message `m_node` = `m_ctx` for every step**: no message is a data source and no message follows another
message, so there are no node-only messages. C3 had 209 node-only message indicators (T9 29, T25 180). C5 assigns
no support to a message whose context is unmatched.

## 2. Tests [OBS]

`gibs/tests/test_c5.py`, 10 tests. Real trajectories plus synthetic graphs; the permissive NLI stub scores every pair
0.99.

| Test | Shows |
|---|---|
| Projection on 3 real runs | tool and user edges identical to C4; one context edge per message; ROOT only for the first event |
| **Tool-score invariance** (real T25 pair, permissive NLI) | C5 tool indicators, tool-node map and tool-edge map equal C4's |
| **Message constraints do not lower correct tool consensus** (identical runs) | all tool indicators stay True |
| **Injective message mappings and context consistency** | every mapped message edge with a tool source agrees with the frozen tool map |
| **T25 `6f12b024 s32`** vs `0f0f7358`, permissive NLI | the wrong booking is unmatched in stage 1, so the confirmation is neither node- nor context-supported |
| Message after an unmatched (conflicting) booking | no context support; the first message (ROOT ↔ ROOT) still matches |
| Message after a user turn | needs a predecessor match; a first message never maps to a non-first message |
| Tool-source rule in isolation | transfer summaries differ, so the identical policy message is blocked (`dropped_tool_unmatched` = 1, no field rejection). With equal summaries it is supported |

Results:
- full suite: **86 GIBS passed** (76 earlier + 10 new);
- **52 NIBS passed, 1 skipped**;
- no failures.

## 3. Pre-registered checks [OBS]

| Check | Result |
|---|---|
| **F1** tool invariance: 315 tool steps (`m_node` and `m_ctx`) and 959 pairs (tool-node map, tool-edge map) | **0 differences** |
| **F2** injective, kind-preserving message maps | 0 violations |
| **F3** context consistency: 661 context-supported (message, reference) indicators with a tool predecessor | 0 whose predecessor was not C4-matched to the reference predecessor |
| **F4** `6f12b024 s32` context-supported references | **0 of 19** (and node 0 of 19) |
| **F5** incorrect steps ≥ 0.5 | 0 (implied by F1) |
| E1 tool steps equal C4 | ✓ |
| E2 `6f12b024 s32` `m_ctx` = 0 | ✓ |
| E3 the four C4 F-b pairs not context-supported | ✓ (none is mapped at all) |
| E4 T25 valid bookings = C4 | ✓ 1.00 / 0.854 |
| E5 valid transfer-message `m_ctx` ≤ the C4 `m_node` of the preceding transfer call | ✓ equality in all 24 cases (0 violations) |
| E6 sampled false-match rate lower than C4 | **✗** (4 / 30 vs 2 / 30; §5) |
| **M1** no known false-pair panel entry context-supported in C5 | **✗**: the 3 C3-origin pairs remain (§4) |
| **M2** sampled different-act count below C4's | **✗** |
| **M3** valid transfer-message `m_ctx` ≥ 0.5 in T48 and T9 | **✗**: 0.089 and 0.232 (predicted; over-restrictive) |

Stage-2 counters (message-edge candidates that passed NLI and field checks, then were dropped by the tool-source
rule):

| Task | Message-edge candidates | Dropped: tool unmatched | Dropped: tool conflict |
|---|---|---|---|
| T48 | 419 | 82 | 0 |
| T9 | 693 | 194 | 0 |
| T25 | 971 | 1 | 1 |

## 4. Requested cases

### 4.1 T25 wrong-booking confirmation `6f12b024 s32` [VER: s30 incorrect; s32 unverified]

s32 is "✅ Booking confirmed! … May 21, 2024 … HAT267". The references confirm the gold booking: May 17, HAT251.

| | References where s32 is node-mapped | References where it is context-supported | Mapped to |
|---|---|---|---|
| C3 | 7 of 19 | 0 | confirmations in 16aac895, 1e01a088, 2aca18ff, 2e0c25a6, ab3d173b, cd5be315, d2135fe7 |
| C4 | 15 of 19 | 15 | reference confirmations (position-free) |
| **C5** | **0** | **0** | — |

Mechanism:
- s32's context edge comes from s30, the wrong booking. Stage 1 leaves s30 unmatched in all 19 references, because
  the field check rejects it against every gold booking (`args.flights`, `args.payment_methods`).
- The s30 → s32 candidate is also removed by the field check on its source tool pair.
- Unlike C3, C5 has no other route to node support.

### 4.2 The four C4 different-act message pairs [OBS mapping; JUDGED act]

| Pair (query → reference) | Origin | C3 maps it to | C4 | **C5 maps it to** |
|---|---|---|---|---|
| `bb73aded s12` (plan, asks "yes") → `1e01a088 s10` (asks DOB) | C4 #8 | — | that pair | **— (unmapped)** |
| `1e01a088 s10` → `bb73aded s12` | C4 #25 | `bb73aded s10` | that pair | **`bb73aded s10`**: both ask for the date of birth, same act |
| `bb73aded s10` (asks DOB) → `1e01a088 s14` (plan) | C4 #18 | `1e01a088 s10` | that pair | **`1e01a088 s10`**: same act |
| `2aca18ff s26` "balance still $500" → `bb73aded s20` (booking created) | C4 #30 | — | that pair | **— (unmapped)** |

All four C4 false pairs are gone: two messages are now unmapped against those references, and two are re-mapped to
the same-act message, as in C3.

**Three C3-origin different-act pairs remain context-supported in C5** (M1 ✗):
- `16aac895 s10 → 1e01a088 s10`
- `16aac895 s10 → cd5be315 s8`
- `51d355a9 s10 → bb73aded s10`

All are T25 "present the plan and ask for yes" vs "ask for the passenger's date of birth" pairs. ~~Both messages
follow a user turn, the user turns match by NLI, and~~ the two messages entail each other in one direction. Stage 2
cannot correct this: it is a property of the NLI similarity, not of the topology.

> **Erratum** (added after `INSPECTION_outcome_support.md` §5; the results above are unchanged). The struck-through
> clause is wrong. I had not checked it.
>
> - **What actually precedes them.** In all three pairs, and in the four C5 sample pairs of §5, both messages follow
>   the same successful tool call `get_reservation_details(G72NSF)` at `s8`, not a user turn.
> - **Why stage 2 accepts them.** C4 matches that lookup to an identical lookup, so the message context edge is
>   allowed.
> - **What differs.** The tool outcomes are identical. What differs is the dialogue state: whether the passenger's
>   date of birth was already given in an earlier user turn.
>
> The conclusion is unchanged: the confusion is message-level NLI, not topology.

### 4.3 Valid bookings and other tool steps

Identical to C4 by construction and by check:
- T25 valid bookings 1.00 / 0.854;
- T48 lookups 0.967 / 0.969 (successful / failed runs; C3 0.778 / 0.577);
- T9 searches 0.500 / 0.529 at the pool cap;
- the incorrect booking 0 / 0.

## 5. Message false matches and coverage

**The same sampling rule for all three variants:**
- population: unverified query message, node mapped, message texts not identical;
- 30 pairs per variant, `random.Random(0)`;
- judged with REPORT_c4 §5 F-b; all judgements are in `results_c5/message_review.json`.

| Variant | Population | Same act | Borderline subset | Same act, conflicting facts | **Different act** |
|---|---|---|---|---|---|
| C3 | 870 | 23 | 3 | 1 | 3 |
| C4 | 948 | 24 | 2 | 2 | 2 |
| C5 | 638 (all context-supported) | 25 | 1 | 0 | **4** |

[JUDGED] 30-pair samples cannot separate rates of 2, 3 and 4 in 30; 95% intervals overlap widely.

What is robust is the **type** of error:
- **C5:** all four different-act cases are T25 "ask DOB ↔ plan + confirm" pairs ~~after a user turn~~
  **[Erratum: after the same successful `get_reservation_details(G72NSF)` lookup, not a user turn. See the
  erratum in §4.2.]**
- **C4:** its errors include position-free pairs (for example, "share your user ID?" ↔ a full plan table) and both
  conflicting-facts confirmations of the wrong booking.
- **C5 has no conflicting-facts pair**, and the wrong-booking confirmation is unmatched (deterministic, §4.1).

**Coverage: context-supported (query message, reference) indicators** [OBS]:

| Task | C3 (`ctx` / node-only) | C4 | C5 |
|---|---|---|---|
| 48 | 419 / 0 | 423 | **337** |
| 9 | 693 / 29 | 725 | **499** |
| 25 | 969 / 180 | 1,220 | **969** |

**C5 vs C3, message `m_ctx` per step:**
- equal for **253 of 280** message steps: every message after a user turn, after the greeting, or after a non-transfer
  tool call;
- **lower for 27**: the messages that follow transfer calls (T48 10, T9 17).

### Valid transfer messages (the only labelled messages; [VER] valid)

| Task | C3 `m_ctx` | C4 | C5 | C5 per run |
|---|---|---|---|---|
| 48 (10 runs) | 1.000 | 1.000 | **0.089** | 0.111 ×8, 0 ×2 |
| 9 (14 runs) | 0.938 | 0.996 | **0.232** | 0–0.5 |
| 25 (1 failed run) | 0 | 0 | 0 | no successful run transfers |

In every case the C5 value equals the C4 `m_node` of the preceding transfer call.

Why the preceding transfer call is rarely matched:
- the transfer summary is free text that differs between runs (operation entailment 0.016 in the T48 example of
  REPORT_pilot §8);
- the result node "Transfer successful" is identical, but stage 1 requires the full tool-call match.

This is the **unavoidable conflict** between the invariance requirement and requirement 3. It is documented here and
not relaxed.

## 6. Distributions (labelled steps)

Bins: `[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`. Full tables, including every unverified group by
predecessor type, are in `tables_c5.md`.

| Task | Group | C3 `m_ctx` | C4 `m_ctx` | C5 `m_ctx` |
|---|---|---|---|---|
| 48 | valid gold lookups (23) | 0 2 5 15 1 0 | 0 0 0 1 7 15 | same as C4 |
| 48 | valid transfer messages (10) | 0 0 0 0 0 10 | 0 0 0 0 0 10 | **2 8 0 0 0 0** |
| 9 | valid gold searches (13) | 3 0 0 10 0 0 | 0 0 0 13 0 0 | same as C4 |
| 9 | valid transfer messages (14) | 0 0 0 0 14 0 | 0 0 0 0 1 13 | **3 3 6 2 0 0** |
| 25 | valid bookings (19) | 3 6 7 3 0 0 | 0 0 0 3 10 6 | same as C4 |
| all | incorrect (23) | all 0 | all 0 | all 0 |

Unexpected cases (valid < 0.5, incorrect ≥ 0.5), C5 node / ctx:
- **T48:** 10 / 10, all transfer messages (C4: 0 / 0).
- **T9:** 12 / 12, all transfer messages; the other 2 are at exactly 0.5 (C4: 0 / 0).
- **T25:** 1 / 1, `51d355a9 s22`, which cannot be matched.

## 7. Possible extension (not implemented): outcome-supported confirmations

Requirement 3 is currently implemented as "the preceding tool **call** is matched", i.e. operation and result both.
An alternative is to condition a message on the preceding tool **outcome** only:
- the result node matches (NLI ≥ 0.7);
- the result is structured-field-compatible, including `error` status and record fields.

[HYP] From the stored texts (not computed):
- this would restore the policy transfer message, because "Transfer successful" is identical;
- it would still block `6f12b024 s32`, because the s30 result (a reservation with May 21 / HAT267) conflicts with
  every gold result on reservation fields.

It would break strict invariance with C4 only in what supports a message, not in tool scores, if implemented as a
message-side check on the frozen graph. It needs its own pre-registration and tests. Separately, a semantic check
that a confirmation's stated facts match the tool observation (e.g. date and flight in the message vs the reservation
record) is a further option, also untested.

## 8. Recommendation

1. **Tool-call consensus: use the C4/C5 tool scores** (identical). Every pre-registered tool criterion passed in C4
   and holds in C5 by construction.
2. **Message consensus: C5 over C4.** C5 removes C4's position-free message matches and the 0.789 support for a
   confirmation of an incorrect booking.
3. **C5 does not make message matching more precise than C3.** Its context-supported message scores are C3's for
   253 of 280 steps, so C3's NLI-level act confusions in T25 remain (M1, M2 ✗).
4. **C5 is over-restrictive for valid transfer messages** (M3 ✗).
5. **Practical position until the extension in §7 is tested:**
   - treat **message scores as unvalidated auxiliary targets**;
   - report `m_ctx` only, with no node-only support;
   - do **not** use message scores as GCN targets, or as evidence that a message is correct.
6. **C5 vs C3 overall:** C5 is preferable, because its tool scores are better (C4's) and its message scores are never
   higher than C3's support. The one exception is the 27 transfer-preceded messages, where it is lower.

**GCN suitability:** unchanged, not yet.
- 83% of steps are unverified.
- The discriminative incorrect-step evidence is one case.
- Messages have no independent labels except the transfer message.

## 9. Limitations

- Three tasks, one agent regime, 103 labelled steps.
- The only labelled messages are policy transfer messages. Every message false-match estimate is
  **[JUDGED]**: 30-pair samples, one reviewer, not blind, rates not statistically separable.
- In the pilot, no message follows another message and no message is a data source. Those rules are unit-tested
  only on synthetic graphs.
- C5 inherits every C4 tool-level limitation, notably the R3 source check on the opening user turn (T48
  `5b5eaa71`).
- C5 depends on stored C4 results. A change to C4 requires recomputing C5, which is resumable and takes seconds
  from cache.

## 10. Integrity [OBS]

- **Unchanged:** `results_pilot/` and `results_c4/` (timestamps and contents), `run_pilot.py`, `run_c4.py`,
  `step_verification.py`, the existing library modules, labels and thresholds.
- **New:** `gibs/mcs/two_stage.py`, `run_c5.py`, `results_c5/`, `tests/test_c5.py`, `c5_plan.md`, this report.
- Nothing was committed.

Stopped for review: no GCN, no threshold tuning, no new tasks, and no implementation of the §7 extension.
