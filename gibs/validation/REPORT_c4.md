# C4: removing event-context edges (Milestone 2, pilot scale)

**Question.** Does removing our extra event-context edges improve valid-step consensus while keeping C3's
rejection of incorrect tool actions?

**Short answer:**
- **Tool actions: yes.** Valid-step consensus rose to the paper-style baseline (A) level on every labelled tool
  step. No incorrect step reached ≥ 0.5. No mapped tool pair has a structured conflict, and there are no cross-tool
  or cross-kind mappings.
- **Overall: C4 fails the pre-registered criterion F5.** The review of newly matched **agent messages** found
  false matches: 4 of 30 sampled pairs perform a different communicative act.
- **C4 also removes a protection C3 had.** The confirmation message that relays the incorrect T25 booking now
  gets 0.789 on *both* targets (C3: `m_ctx` = 0).

By the plan's own rule, **C4 is reported as unsafe as a whole and is not recommended as-is** (§8). The gains and
the failures are confined to different step types, and that points to a narrow follow-up.

Scope:
- Three-task pilot only: T48, T9, T25.
- No GCN training, no full-corpus scoring, no threshold change, no label change.
- No existing output was modified.

**Evidence tags:**
- **[OBS]**: observed in stored outputs.
- **[VER]**: an independent label from `step_verification.py`.
- **[HYP]**: an untested explanation.
- **[POST-HOC]**: an analysis not in `c4_plan.md`.

## Files

| File | Content |
|---|---|
| `c4_plan.md` | pre-registration (code inspection, the C3 → C4 difference, H1–H8, F1–F5, metrics, AUROC rule). Written before computing |
| `run_c4.py` | `compute` / `analyze`. Defines C4 as C3 with `topology="paper_literal"`. Writes only to `results_c4/` and reads A/C0/C3 from `results_pilot/` read-only |
| `results_c4/task{48,9,25}_C4.json` | per-reference MCS results: node and edge maps, indicators, rejections, cost |
| `results_c4/per_step_masks_c4.csv` | 595 agent steps × label × `m_node` / `m_ctx` for A, C0, C3, C4 |
| `results_c4/c4_summary.json`, `results_c4/tables_c4.md` | distributions (6 bins), unexpected cases, C4 − C3, AUROC, mapping audit, positional drift, T48 lookup groups, reference-count curves, review sets |
| `gibs/tests/test_c4.py` | 11 unit tests (§2, §6b) |

Reproduce:

```
.venv/bin/python -B gibs/validation/run_c4.py compute
.venv/bin/python -B gibs/validation/run_c4.py analyze
```

Compute is resumable and never overwrites existing files. Cost [OBS]: T48 0.7 s, T9 2.0 s, T25 9.4 s, with
**0 uncached NLI forward passes**. Every NLI score came from the existing cache.

## 1. What C4 changes (verified in code and on all 66 pilot runs)

**What the code does:**
- The step graph has `temporal` and `data_dependency` edges.
- A tool's response is **not an edge**: the observation is the result node of its own call, and the call text is
  the edge text. So "tool-response relationships" are retained by construction.
- `event_context` (C0/C3) adds a `context` edge from the preceding event and merges it with a data edge where both
  connect the same pair.
- `paper_literal` (A, C4) keeps only `data` edges and attaches dependency-free events to ROOT.

**Checked before running** [OBS]:
- The set of data-dependency edges is identical in the step graph and in both projections, for every run.
- C4 removes 205 / 221 / 358 context-only edges (T48 / T9 / T25) and strips the context role from 24 / 24 / 43
  merged edges.
- **No data dependency is lost.**

**Edges that remain in C4:**
1. `data` edges: the source event's visible text contains a value used in the call's arguments.
2. `root` edges: `ROOT → event` for every event without a data dependency. That is every agent message, every user
   turn, and 1 / 0 / 20 tool calls in T48 / T9 / T25.

**Unchanged from C3:**
- DeBERTa-large-MNLI with the max of both directions;
- τe = τv = 0.7, top-K 10, source-node threshold;
- `require_same_kind`;
- structured-field rejection;
- symmetric truncation;
- globally consistent multi-component matching;
- the same queries, references and labels. The analysis asserts identical query and reference order for all four
  variants.

**Consequence.** Messages and user turns are now matched **without any positional context**. Their only edge comes
from ROOT, and edge text = node text = the utterance. This is the mechanism behind §5.

**Code change.** No library code changed. C4 is a 3-line variant definition in `run_c4.py`.

## 2. Tests [OBS]

`gibs/tests/test_c4.py` (11 tests; the ROOT test is described in §6b). Synthetic graphs are used only in unit tests.

| Test | Checks |
|---|---|
| C4 = C3 except topology | config identity |
| Real T48, T25 (two runs) | the C4 data-edge set equals the step graph's dependencies; no context edges; each event hangs from its data sources or from ROOT only |
| Tool response folded into the call | result node = observation text; incoming edge text = call text |
| Messages and user turns hang from ROOT | — |
| **Real T25 `6f12b024 s30` vs gold booking `0f0f7358`** with a stub NLI that accepts every pair (0.99) | the wrong booking is still not mapped; the rejection reasons include `args.flights` |
| Synthetic booking with a conflicting date, with and without a prior lookup | rejected; the identical booking is matched on both targets |
| Synthetic ROOT-hanging conflicting bookings | rejected on the target check |

Results:
- full GIBS suite `pytest gibs/tests`: **76 passed** (65 existing + 11 new, including the ROOT test in §6b);
- `nibs/tests`: **52 passed, 1 skipped**;
- no failures.

## 3. Labels (unchanged) [VER]

| Task | Successful / failed runs | Valid (successful runs) | Valid (failed runs) | Incorrect | Unverified |
|---|---|---|---|---|---|
| 48 | 10 / 13 | 20 (10 gold lookups, 10 transfer messages) | 13 gold lookups | 13 cancellations | 93 |
| 9 | 17 / 4 | 23 (9 gold searches, 14 transfer messages) | 4 gold searches | 8 writes | 144 |
| 25 | 19 / 3 | 19 gold bookings | 1 transfer message | 2 (wrong booking, cancellation) | 255 |

## 4. Results: labelled steps [OBS]

### 4.1 Means (`m_node` / `m_ctx`)

| Task | Group | A | C0 | C3 | **C4** |
|---|---|---|---|---|---|
| 48 | valid, successful runs (20) | 0.967 / 0.967 | 0.545 / 0.545 | 0.778 / 0.778 | **0.967 / 0.967** |
| 48 | valid, failed runs (13) | 0.969 / 0.969 | 0.508 / 0.508 | 0.577 / 0.577 | **0.969 / 0.969** |
| 48 | incorrect (13) | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 0** |
| 9 | valid, successful runs (23) | 0.802 / 0.802 | 0.372 / 0.326 | 0.802 / 0.723 | **0.802 / 0.802** |
| 9 | valid, failed runs (4) | 0.514 / 0.514 | 0.514 / 0.397 | 0.529 / 0.397 | **0.529 / 0.529** |
| 9 | incorrect (8) | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 0** |
| 25 | valid, successful runs (19) | 1.000 / 0.854 | 1.000 / 0.269 | 1.000 / 0.269 | **1.000 / 0.854** |
| 25 | valid, failed runs (1) | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 0** |
| 25 | incorrect (2) | **0.473** / 0 | 0 / 0 | 0 / 0 | **0 / 0** |

### 4.2 C4 distributions of labelled steps (bins `[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`)

| Task | Group | C4 `m_node` | C4 `m_ctx` | C3 `m_ctx` for comparison |
|---|---|---|---|---|
| 48 | valid, successful runs | 0 0 0 1 3 16 | 0 0 0 1 3 16 | 0 2 1 6 1 10 |
| 48 | valid, failed runs | 0 0 0 0 4 9 | 0 0 0 0 4 9 | 0 0 4 9 0 0 |
| 9 | valid, successful runs | 0 0 0 9 1 13 | 0 0 0 9 1 13 | 2 0 0 7 14 0 |
| 9 | valid, failed runs | 0 0 0 4 0 0 | 0 0 0 4 0 0 | 1 0 0 3 0 0 |
| 25 | valid, successful runs | 0 0 0 0 0 19 | 0 0 0 3 10 6 | 3 6 7 3 0 0 |
| all | incorrect (23) | 23 0 0 0 0 0 | 23 0 0 0 0 0 | 23 0 0 0 0 0 |

Full distributions, including unverified steps by successful/failed run, are in `tables_c4.md`.

### 4.3 Pre-registered unexpected cases (valid < 0.5, incorrect ≥ 0.5), node / ctx

| Task | A | C0 | C3 | **C4** |
|---|---|---|---|---|
| 48 | 0 / 0 | 10 / 10 | 7 / 7 | **0 / 0** |
| 9 | 1 / 1 | 12 / 14 | 0 / 3 | **0 / 0** |
| 25 | 2 / 1 (one is the incorrect booking at 0.947) | 1 / 17 | 1 / 17 | **1 / 1** |

The only C4 case is T25 `51d355a9 s22`, a valid transfer message in a failed run. It cannot be matched, because
no successful T25 run transfers (REPORT_pilot §9.2).

### 4.4 AUROC (valid vs incorrect; ties ½)

Computed only where there are ≥ 5 labelled positives and ≥ 5 labelled negatives.

| Task (positives / negatives) | A node / ctx | C0 | C3 | C4 |
|---|---|---|---|---|
| 48 (33 / 13) | 1.000 / 1.000 | 0.985 / 0.985 | 1.000 / 1.000 | 1.000 / 1.000 |
| 9 (27 / 8) | 1.000 / 1.000 | 0.981 / 0.926 | 1.000 / 0.944 | 1.000 / 1.000 |
| 25 (20 / 2) | not computed | — | — | — |

**These AUROCs carry almost no information about discrimination.** All 21 negatives in T48 and T9 are writes that
no successful run performs. Any matcher that does not confuse tools gives them 0, so AUROC < 1 only measures valid
steps scoring 0. The single discriminative negative (T25 `6f12b024 s30`) is reported on its own in §6.1. AUROC was
not pooled across tasks.

### 4.5 C4 − C3 per step

| Task | Target | Increased | Decreased | Valid steps | Incorrect steps | Unverified steps |
|---|---|---|---|---|---|---|
| 48 | node | 26 | 10 | +22 / −0 (mean +0.269) | 0 / 0 | +4 / −10 |
| 48 | ctx | 30 | 0 | +22 / −0 | 0 / 0 | +8 / −0 |
| 9 | node | 4 | 26 | 0 / 0 | 0 / 0 | +4 / −26 |
| 9 | ctx | 87 | 0 | +16 / −0 (mean +0.086) | 0 / 0 | +71 / −0 |
| 25 | node | 33 | 4 | 0 / 0 | 0 / 0 | +33 / −4 |
| 25 | ctx | 130 | 1 | +19 / −0 (mean +0.555) | 0 / 0 | +111 / −1 |

**No valid step decreased on either target.**

All 40 `m_node` decreases are unverified steps:
- 27 transfer *calls* (T48 10: 1.00 → 0.00–0.11; T9 17: 0.82–0.94 → 0.00–0.50);
- 8 T9 user/reservation lookups (−1 reference each);
- 1 T9 message, 3 T25 messages and 1 T25 errored booking.

[OBS] In C3, a transfer call's node was supported through its **successor** context edge (transfer → message;
REPORT_pilot §8). C4 has no such edge, so a transfer call is supported only when its own free-text summary is
entailed. As a result:
- **C4 has 0 node-high / ctx-low steps** (C3: 98; A: 9).
- `m_node` ≠ `m_ctx` for only 41 steps (C3: 225).

### 4.6 Reference-count stability (C4, mean absolute deviation from the full pool)

| Task | k=1 | 2 | 3 | 5 | 8 |
|---|---|---|---|---|---|
| 48 node | 0.105 | 0.066 | 0.054 | 0.034 | 0.015 |
| 9 node | 0.223 | 0.145 | 0.112 | 0.083 | 0.056 |
| 25 node | 0.175 | 0.119 | 0.091 | 0.069 | 0.049 |
| 25 ctx | 0.195 | 0.133 | 0.107 | 0.077 | 0.053 |

- The values fall monotonically with k.
- They are within ±0.01 of A and C3 for the same task (REPORT_pilot §10).
- The same caveats apply: T48 k = 8 is close to the full pool, and the unexpected rate is discrete at small k.

## 5. Safety audit [OBS]

| Pre-registered criterion | Result |
|---|---|
| **F1** incorrect step ≥ 0.5 (node or ctx) | **pass**: all 23 incorrect steps are 0 on both targets |
| **F2** mapped tool pair with a structured conflict or a different tool, audited over **all** mapped tool pairs (2,896: T48 219, T9 869, T25 1,808) | **pass**: 0 conflicts, 0 cross-tool. A for comparison: **76 structured conflicts** in T25 |
| **F3** cross-kind mapping | **pass**: 0. A: 56 / 21 / 60 (T48 / T9 / T25) |
| **F4** T9 gold search above its pool cap | **pass**: 0.500 / 0.529, exactly at the cap |
| **F5** false match among newly matched or re-mapped steps | **fail** (details below) |

**F5, labelled steps.** All 85 newly matched labelled (query, reference) pairs are T48 gold lookups mapped to the
reference's identical gold lookup, with compatible structured fields. These are correct recoveries.

**F5, tool calls.** All newly matched or re-mapped tool calls are covered by the F2 audit: same tool, no
structured conflict. [HYP] They are not false matches under F-b. Their semantic agreement beyond structured fields
(for example, transfer summaries) was not reviewed.

**F5, messages:** 123 newly matched or re-mapped (query message, reference) pairs. The pre-registered random sample
of 30 (seed 0) was judged against `variants_criteria.md` F-b:

| Judgement | n / 30 | Examples (query → reference) |
|---|---|---|
| Same communicative act | 18 | plan table ↔ plan table; fare discrepancy ↔ fare discrepancy; closing ↔ closing |
| Borderline: one text entails a short part of the other | 5 | "Your certificate balance is still $500.00." ↔ a table that includes the balance and asks to confirm a booking |
| Same act, **conflicting facts** | 3 | `6f12b024 s32` "Booking confirmed … May 21 … HAT267" (the incorrect booking) ↔ three references' confirmations of the gold booking (May 17, HAT251) |
| **Different act (F-b false match)** | **4** | see below |

The four F-b false matches:
- **#8 and #25** (same pair, in both directions): `bb73aded s12` / `1e01a088 s10`. One presents a full plan and
  asks for "yes"; the other asks for the passenger's date of birth.
- **#18**: `bb73aded s10` asks for the date of birth ↔ `1e01a088 s14` presents the plan.
- **#30**: `2aca18ff s26` "Your certificate balance is still $500.00." ↔ `bb73aded s20` "✅ Your new reservation has
  been created! …". The reference ends with "Your certificate balance remains $500 (unchanged)", so maximum
  bidirectional entailment passes on a sub-sentence.

[OBS] All 30 judgements, with both texts, can be regenerated from
`c4_summary.json → review.message_sample_seed0`.

**[POST-HOC] base rate in C3.** To see whether this failure is new to C4, the same F-b judgement was applied to a
random sample of 30 (seed 0) of the 870 C3 mappings whose message texts differ. The result:
- 3 different act (for example, a plan with a confirmation request ↔ a request for a date of birth);
- 3 borderline;
- 1 conflicting facts: the same wrong-booking confirmation `6f12b024 s32`, which C3 already maps at the node level;
- 23 same act.

Matching non-identical messages by NLI produces some act-level false matches in **both** variants: 4 of 30 in C4's
new mappings, 3 of 30 in C3. The two samples come from different populations, so the rates are indicative only.
This post-hoc comparison does **not** change the pre-registered F5 outcome.

**The specific new risk: `m_ctx` no longer screens messages that relay an incorrect action** [OBS]:

| Step | A | C0 | C3 | C4 |
|---|---|---|---|---|
| T25 `6f12b024 s32`: confirmation of the incorrect booking s30 (unverified) | 0.789 / 0.789 | 0 / 0 | 0.368 / **0** | **0.789 / 0.789** |
| T25 `d7a124a4 s42`: confirmation of the prohibited cancellation | 0.053 / 0.053 | 0 / 0 | 0.053 / 0 | 0.053 / 0.053 |
| 18 other messages right after an incorrect T48 or T9 write | 0 (one at 0.059) | 0 | 0 | 0 (one at 0.059) |

- In C3, the message's context edge came from the rejected booking, which kept `m_ctx` at 0.
- In C4, the message hangs from ROOT, and NLI cannot tell "May 21 / HAT267" from "May 17 / HAT251" (probe findings
  P07 and P08).
- The T48 and T9 zeros are structural: no reference contains a confirmation of a cancellation.

**Positional drift** of mapped agent-step pairs (|relative position difference|), mean / share > 0.25:

| Task | C3 | C4 |
|---|---|---|
| 48 | 0.029 / 0.005 | 0.029 / 0.005 |
| 9 | 0.086 / 0.108 | 0.084 / 0.110 |
| 25 | 0.064 / 0.021 | 0.070 / 0.034 |

Drift rises slightly in T25, which is consistent with position-free message matching.

## 6. Requested cases

### 6.1 T25 `6f12b024 s30`: the incorrect booking [VER incorrect]

It books 2024-05-21 with HAT097 + HAT267 and pays 171 by card; the gold booking is 2024-05-17 with HAT097 +
HAT251 and 247.

| Variant | `m_node` | `m_ctx` | Notes |
|---|---|---|---|
| A | 0.947 | 0 | mapped to the gold booking in 18 of 19 references |
| C3 | 0 | 0 | — |
| **C4** | **0** | **0** | every candidate pairing it with a reference booking is rejected with reasons such as `args.flights: (hat097, 2024-05-21), (hat267, 2024-05-21) != (hat097, 2024-05-17), (hat251, 2024-05-17)` and `args.payment_methods …` |

The unit test reproduces the C4 rejection with an NLI stub that accepts everything, so the protection does not
depend on NLI. **H1 holds.**

### 6.2 T25 valid bookings that C3's context edges penalised

| Run · step | C3 node / ctx | C4 node / ctx |
|---|---|---|
| `1e01a088 s18` | 1.00 / 0.00 | 1.00 / **1.00** |
| `2aca18ff s22` | 1.00 / 0.00 | 1.00 / 0.83 |
| `d3366062 s20` | 1.00 / 0.00 | 1.00 / 0.56 |
| `a92c9234 s20`, `c801d833 s26` | 1.00 / 0.06 | 1.00 / 0.83 |
| `16aac895 s24` | 1.00 / 0.11 | 1.00 / 0.56 |
| `bb73aded s18`, `d2135fe7 s18` | 1.00 / 0.17 | 1.00 / 1.00 |
| all 19 | mean 1.00 / 0.269 | mean 1.00 / **0.854** (min 0.556) |

- **H2 holds** (prediction: `m_ctx` ≥ 0.70).
- The three runs at 0.556 (16aac895, cc2b26ea, d3366062) lose references on the data edge from the opening user
  turn, which maps in 0.56 of references in C3 as well. [HYP] As in T48, a paraphrased opening turn fails NLI
  against some references.

### 6.3 T48 `5b5eaa71 s2`: valid lookup

**C3 0.667 → C4 0.667, exactly as predicted (H3).**
- The 6 references where the ID arrives in a later turn match.
- The 3 references where the ID is in the opening turn are still blocked by the source-node threshold. The opening
  turns score 0.072 / 0.191, as in REPORT_pilot §6.

The **other** opening-turn runs rise from 0.22–0.33 to 0.889 (successful runs) and 0.900 (failed runs). **H4
holds.** The lookup-group matrix for C4 equals A's:

| Pairs | C4 rate |
|---|---|
| O×L (48) | 1.000 |
| L×O (60) | 1.000 |
| L×L (84) | 1.000 |
| O×O (28) | 0.643 |

All O×O misses involve 5b5eaa71. The remaining loss is the R3 source check (our reading of the PDF), not the
topology.

### 6.4 T9 gold searches with limited reference support

| | C3 node / ctx | C4 node / ctx |
|---|---|---|
| 9 successful runs | 0.500 / 0.389 | 0.500 / **0.500** |
| 4 failed runs | 0.529 / 0.397 | 0.529 / **0.529** |
| `7cd3469e s12`, `49f89baf s16`, `71270d8b s10` | ctx 0 | ctx 0.50 / 0.50 / 0.53 |

- Node consensus stays at the pool cap: 8 of 16 or 9 of 17 references perform the gold search. It never goes above
  the cap (**H5 holds; F4 passes**).
- The low values come from **path frequency**, a property of the paper's mask definition, and no matcher change
  should raise them.

### Hypothesis summary

| | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 |
|---|---|---|---|---|---|---|---|---|
| Result | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

H6: transfer messages stay ≥ 0.9 (T48 1.00, T9 0.996).

## 6b. ROOT and data-dependency audit (`run_c4.py audit` → `results_c4/c4_audit.json`)

This audit runs over the stored C4 mappings, with no re-matching. It was requested after the plan was written, so
it is **[POST-HOC]**, but its checks are mechanical.

**ROOT does not create cross-structure matches** [OBS]:

| Task | ROOT ↦ ROOT | ROOT ↔ non-ROOT | root-edge ↔ root-edge | data-edge ↔ data-edge | mixed root ↔ data |
|---|---|---|---|---|---|
| 48 | 220 | **0** | 810 | 219 | **0** |
| 9 | 340 | **0** | 1,426 | 968 | **0** |
| 25 | 399 | **0** | 2,753 | 3,904 | **0** |

This is guaranteed by the rules:
- ROOT↔ROOT = 1 and ROOT↔other = 0 without NLI;
- the source-node threshold makes a ROOT-sourced edge unable to pair with a dependency edge.

A new unit test confirms both properties on a real T25 pair with an NLI stub that accepts everything, giving
11 tests in `test_c4.py`.

The cost of ROOT is the position-free message matching in §5. ROOT is the shared source of every message edge, so
any two sufficiently entailing messages can be paired. ROOT does not cause any tool-level mismatch.

**Which tool calls hang from ROOT** (no data dependency):

| Task | Calls | Assessment |
|---|---|---|
| 25 | 15 runs call `get_user_details(user_id="?")` before the user has given an ID; 2 call `"user123"`; 2 call `"sara_doe_496"` | placeholder or hallucinated IDs, so ROOT is the correct attachment |
| 48 | 1 transfer | its summary contains no tracked value |
| 25 | 1 transfer | same |

For the placeholder calls:
- [OBS] Their `m_node` is identical in A, C0, C3 and C4 (0.667 for the "?" call, which most successful runs share).
- C4 only raises their `m_ctx` to equal `m_node`.
- These steps are unverified. Their consensus reflects a common but probably useless action, so "consensus ≠
  correctness" applies.

**Dependencies are not altered:** the C4 data-edge set equals the step graph's for all 66 runs (§1).

**High node scores not supported by the step's data dependencies.** Unit: (query tool step, reference) pairs where
the node is mapped.

| Task · label | Pairs with node mapped | …but some data edge unmapped | Mapped data edges: source kind differs | Mapped data edges: dependency values differ |
|---|---|---|---|---|
| 48 · valid | 210 | 0 | 0 | 0 |
| 48 · unverified | 9 | 1 | 0 | 0 |
| 9 · valid | 108 | 0 | 0 | **9** |
| 9 · unverified | 761 | 1 | 0 | 27 |
| 25 · valid | 342 | **50** | 0 | 0 |
| 25 · unverified | 1,280 | 68 | 0 | 16 |

- **T25 valid bookings, 50 pairs.** The node maps but one data edge does not. In 48 of the 50, the unmapped edge
  is the one from the **opening user turn** (u1). [HYP] A paraphrased opening request fails NLI against some
  references. The booking itself is field-checked equal to the reference booking, so the node match is correct.
  `m_ctx` (0.854) is the score that reflects the missing support, and `m_node` (1.0) overstates it.
  - This is the remaining "node-high, dependency-partial" pattern in C4.
  - It is small, and no step crosses the 0.5 boundary (0 node-high / ctx-low steps in C4).
- **T9 valid, 9 mapped data edges with different dependency values.** All have the failed run `71270d8b` as the
  query.
  - Its search consumes `[2024-05-22, JFK, MCO]` from one source.
  - The references take `[2024-05-22, JFK]` from that source and MCO from another.
  - The search calls are identical and field-compatible. Only the partition of values across source events
    differs. Benign.
- **Unverified differences:** 26 transfer-summary edges in T9 (free-text tokens) and 16 errored T25 booking
  attempts. Both are matched to their own kind and are field-compatible.

## 7. C4 vs A

**On labelled steps, C4 equals A in T48 and T9.** In T25 it differs only on the incorrect booking (A 0.947, C4 0).

`m_node` differs between C4 and A on 50 of 595 steps:
- in T25, A is higher on 12 unverified bookings. All 12 are errored payment attempts; A also maps them to
  successful bookings (part of A's 76 structured conflicts), while C4 matches them only to other errored attempts.
  A is also higher on 28 messages (T25 20, T9 6, T48 2);
- A's cross-kind mappings disappear.

So C4 ≈ A plus C3's safeguards. The safeguards removed every tool-level false match A made, but they do not cover
messages.

## 8. Recommendation

**Do not adopt C4 as-is.** By the pre-registered rule it fails F5:
- 4 of 30 sampled new message matches perform a different act;
- it gives 0.789 on both targets to a message that relays an incorrect booking, where C3's `m_ctx` gave 0.

Everything C4 was designed to fix, it fixed **for tool calls**, with no detected tool-level false match. The
failures are confined to **agent messages**, which C4 matches without position. The post-hoc C3 sample shows
message matching was already imperfect in C3.

**Proposed next step** (needs your approval; a new pre-registration; no threshold changes):
1. **C5 = hybrid topology.**
   - Tool-call events use C4's construction (data edges only; ROOT if none).
   - Agent messages keep their incoming context edge from the preceding event. That keeps the C3 protection for
     messages that relay an incorrect result, as in `6f12b024 s32`.
   - This is a small projection option. It should be compared with C3 and C4 on the same pilot, using the same F5
     message review.
2. **Alternatively**, restrict consensus targets to tool-call steps and report message masks separately as
   unvalidated. That needs no matcher change, but it narrows what GIBS scores.
3. In either case, the **independent label set needs negatives that have same-tool counterparts** (wrong-argument
   writes) beyond the single T25 case. Discrimination evidence currently rests on n = 1. The R3 sensitivity (§6.3)
   remains open.

**GCN suitability:** still not established. 83% of steps are unverified, and the message false-match rate is
non-zero in every variant.

## 9. Limitations

- Three tasks and one agent regime.
- 103 labelled steps; only 1 discriminative incorrect step.
- **Message judgements:**
  - one reviewer;
  - a 30-pair sample from 123 new or re-mapped pairs;
  - not blind: the reviewer knew the variant;
  - the C3 baseline is post-hoc and drawn from a different population.
- **No messages are labelled.** Their false-match rate is a review estimate, not a verified label.
- The tool-call F-b judgement relies on the structured-field audit, not on reading transfer summaries.

## 10. Integrity [OBS]

- `results_pilot/` is unchanged (all 15 files keep their earlier timestamps; no file was written there).
- Unchanged:
  - `run_pilot.py`, `step_verification.py`, the library code under `gibs/graph` and `gibs/mcs`;
  - `pairs.json` (sha256 `c075979c…d738`);
  - the v0.1 example files.
- No labels were changed.
- New files: `c4_plan.md`, `run_c4.py`, `results_c4/`, `tests/test_c4.py`, this report.
- Nothing was committed.

Stopped here for your review: no GCN, no full-corpus scoring, no threshold tuning, and no C5 implementation.
