# Phase 2B: frozen evaluation of Tasks 28, 1 and 5

**Protocol:** `EVALUATION_PROTOCOL.md` (2B-final), frozen before computation. **Deviations:** none.

**Methods:**
- C4 is the primary tool-call matcher; C5 and C6 are exploratory message scoring.
- All are our adaptations, not the paper's GIBS method.

**Exposure:**
- **T28 is an untouched hold-out.**
- **T1 and T5 were previously exposed:** they were scored in earlier NIBS / WL-graph work, but not used to design A
  or C0–C6.

**No discrimination claim.** These tasks contain no difficult negatives, and nothing below measures whether incorrect
steps are separated from correct ones.

**Evidence tags:**
- **[OBS]**: computed from `results_eval/`.
- **[HYP]**: an untested explanation.

## Headline

| Question | T28 (untouched) | T1 (exposed) | T5 (exposed; T = 1.0) |
|---|---|---|---|
| Labelled valid tool steps (v2) | **0** (gold actions empty) | **39** | 1 (failed run) |
| C4 valid tool-step coverage@0.5 (`m_ctx`) | — | **39 / 39 = 1.00**. Mean 0.897 = mean ceiling 0.897; ceiling-normalised 1.00 | 0 / 1 (ceiling 0: no successful run makes that call) |
| C4 exact-step recall (node / context-supported), over exact pairs | **0.991 / 0.991** (210 / 212) | **1.000 / 1.000** (2,424 / 2,424) | 1.000 / 1.000 (only 2 pairs) |
| Valid transfer messages, `m_ctx` (C4 / C5 / C6) vs ceiling | 1.00 / **0.63** / 1.00 (cap 1.00) | 0.95 / **0.25** / 0.95 (cap 0.95) | 0.39 / **0.04** / 0.39 (cap 0.39) |
| Incorrect steps (structural only) | — | 2 cancellations: 0 / 0 | 2 `send_certificate`: 0 / 0 |

Wherever a step occurs in the references, **C4 tool-call consensus reached the reference ceiling** for every labelled
valid tool step.
- The only exact-agreement misses (2 of 2,638 pairs) come from the source-node threshold on paraphrased opening user
  turns (§4).
- All low scores among labelled steps are explained by **reference frequency**, or by **C5's design**, which requires
  the preceding transfer call to be matched (§5).

## 1. Execution [OBS]

| Task | Runs (success / failed) | Content classes (successful) | Duplicate classes | Query × reference pairs | Wall time | Uncached NLI passes |
|---|---|---|---|---|---|---|
| 28 | 21 / 0 | 16 (16) | {5, 2} | 240 | 86 s | 1,025 |
| 1 | 22 / 2 | 23 (21) | {2} | 462 | 1,778 s | 16,962 |
| 5 | 14 / 2 | 16 (14) | none | 210 | 5,093 s | 32,901 |

- **Overall:** one process (lock file), about 2 h 3 min in total, plus self-matches for duplicate classes.
- **Analysis:** 0 uncached passes.
- **Reproduce:** `run_eval.py compute 28 1 5`, then `run_eval.py analyze`.

**Checks:**

| Check | Result |
|---|---|
| S1 C5 / C6 tool scores and maps = C4 | **0 differences** over 912 pairs |
| S2 cross-kind mappings; tool pairs with structured conflicts | **0 / 0** |
| S3 references from the query's own class | **0** |
| S4 run and class counts as pre-registered | ✓ |
| S5 code fingerprints | ✓; computed immediately before launch, and recorded in the protocol |
| S6 uncached passes reported | ✓ |

## 2. Pre-registered expectations

| ID | Expectation | Result |
|---|---|---|
| E1 | C4 = C5 = C6 on tool steps | **met** |
| E2 | No incorrect step ≥ 0.5 (structural negatives) | **met**: all 4 are 0 / 0, not discrimination evidence |
| E3 | T1 `get_user_details` mean `m_ctx` ≥ 0.75; `get_reservation_details` `m_ctx / cap` ≥ 0.75 | **met**: 1.00 (n = 23); 0.75 / 0.75 = 1.00 (n = 16) |
| E4 | No valid step with `m_node` > `cap` + 1/n | **met**: 0 violations (C4, C5 and C6) |
| E5 | Transfer messages: C6 `m_ctx / cap` ≥ 0.8, C5 lower | **met**: C6 1.00 in all three tasks; C5 0.63 / 0.26 / 0.11 |
| E6 | k = 5: C4 mean absolute deviation (all tool steps) ≤ 0.10 in T1 and T28; T5 > T28 | **not met.** T1 0.029 ✓; **T28 0.114**; T5 0.022 < T28 |
| E7 | Exact context-supported recall ≥ 0.8 in T1 and T28; lower in T5 | **partly met.** T1 1.00, T28 0.991 ✓. T5 1.00, but on 2 pairs only, so uninformative |

## 3. Valid-step coverage [OBS]

Bins: `[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`.

| Task | Valid step | n | C4 `m_ctx`: mean, bins | Mean ceiling | Coverage@0.5 |
|---|---|---|---|---|---|
| 1 | `get_user_details(raj_sanchez_7340)`, successful | 21 | 1.00 · 0 0 0 0 0 21 | 1.00 | 1.00 |
| 1 | `get_user_details`, failed | 2 | 1.00 · 0 0 0 0 0 2 | 1.00 | 1.00 |
| 1 | `get_reservation_details(Q69X3R)`, successful | 16 | **0.75** · 0 0 0 0 16 0 | **0.75** | 1.00 |
| 5 | `get_user_details(mei_brown_7075)`, failed | 1 | 0 · 1 0 0 0 0 0 | **0** | 0 |

- **T1:** every labelled tool step equals its ceiling. The `get_reservation_details` value of 0.75 means 15 of 20
  references contain that lookup: 5 successful T1 classes never perform it. That is **reference frequency**.
- **T5:** the only labelled tool step (failed run `c0810635 s8`) is a gold read that **no successful T5 run
  performs**. Its 14 references are all classified (a), "reference lacks the step".

## 4. Unmatched valid steps and exact-step recall [OBS]

**Labelled valid tool steps with C4 `m_ctx` < 0.5:** **1** (T5 `c0810635 s8`). Mechanism: (a) reference frequency in
14 of 14 references.

**Exact-step recall** (C4; label-free; tool calls):

| Task | Tool steps | With any exact counterpart | Exact pairs | Node recall | Context recall | Non-exact supported pairs |
|---|---|---|---|---|---|---|
| 28 | 31 | 17 (55%) | 212 | 0.991 | 0.991 | 150 (all transfer calls) |
| 1 | 153 | 125 (82%) | 2,424 | 1.000 | 1.000 | 100 (all transfer calls) |
| 5 | 22 | **2 (9%)** | 2 | 1.000 | 1.000 | 4 (all transfer calls) |

**The 2 misses** (T28, a mutual pair). `65fe6fb0 s2` and `b6b8a2fb s4` are the identical
`get_reservation_details(SI5UKW)` with an identical result:
- edge NLI 0.978 and target 0.988 both pass;
- **the source-node score between the two opening user turns is 0.486**, below τ = 0.7. One turn includes the user
  ID, the other does not.
- The candidate is therefore rejected by the R3 source check. This is a **matching failure**, mechanism (c), the same
  as T48 `5b5eaa71` in the pilot.

**Non-exact supported pairs** (254) are all `transfer_to_human_agents` calls whose free-text summaries differ, so they
are not exact. They were matched through NLI on the summaries and the identical `Transfer successful` result.
- T28 has 73 distinct summary pairs, T1 89, T5 4.
- Inspected samples describe the same situation in other words. Examples: "wants to cancel reservation SI5UKW … basic
  economy" ↔ "requests cancellation of reservation SI5UKW …"; "compensation for delayed flight … not allowed per
  policy" ↔ "… not possible under policy".
- These are unverified steps. Transfer calls have no structured fields, so the summaries' content is checked only by
  NLI.

## 5. Messages (exploratory) [OBS]

**Valid transfer messages** (the only labelled messages):

| Task | n | Ceiling | C4 | C5 | C6 | C6 outcome-route matches |
|---|---|---|---|---|---|---|
| 28 | 16 | 1.00 | 1.00 | 0.63 (5 below 0.5) | 1.00 | 88 |
| 1 | 20 | 0.95 | 0.95 | 0.25 (19 below 0.5) | 0.95 | 280 |
| 5 | 7 | 0.39 | 0.39 | 0.04 | 0.39 | 32 |

**Why C5 is low.** C5 supports a message after a transfer only if C4 matched the transfer **call**. The free-text
summaries rarely entail each other: mean C4 `m_ctx` of transfer calls is T1 0.20, T28 0.52, T5 0.04. That is a
property of C5's design, as found in REPORT_c5, not a new failure.

**C6 recovers the ceiling exactly** in all three tasks.

**All C6 outcome-route matches were inspected (400):**
- **every one** pairs the identical policy text "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."
  after an identical `Transfer successful`;
- 0 have non-identical text;
- 6 (T5) have a query message from the failed run `c0810635`. That message is the policy text itself, labelled
  `valid`, after a successful transfer. The run's earlier prohibited `send_certificate` steps stay at 0.
- **No newly supported potentially incorrect message was found.** The C6 false match seen in the pilot (a message
  narrating an earlier prohibited action) does not occur here.

**C4's message scores are not a recommendation.** C4 matches every message position-free through ROOT (REPORT_c4
§5). In these tasks they coincide with C6 for transfer messages. Mean `m_ctx` of all messages:

| Variant | T1 | T28 | T5 |
|---|---|---|---|
| C5 | 0.37 | 0.75 | 0.31 |
| C6 | 0.52 | 0.92 | 0.33 |

Unverified messages carry no correctness interpretation.

## 6. Reference-count sensitivity (deterministic subsets; §6.4) [OBS]

**C4, all tool steps:**

| Task | k = 1 | 2 | 3 | 5 | 8 | Notes |
|---|---|---|---|---|---|---|
| 1 (refs 20–21) | 0.072 | — | — | **0.029** | 0.019 | at k = 5: p90 0.15; valid unexpected rate 0.034 |
| 28 (refs 15) | 0.296 | — | — | **0.114** | 0.079 | at k = 5: p90 0.20 |
| 5 (refs 13–14) | 0.036 | — | — | 0.022 | 0.014 | most tool steps are 0 everywhere |

The values in the table are mean absolute deviations from the full-pool value. The full grid (k = 1, 2, 3, 5, 8,
all; mean, median and p90 deviation; mean valid; unexpected rate; observation and subset counts) is in
`eval_summary.json → tasks.*.sensitivity`.

Valid messages at k = 5:

| Variant | T1 | T28 | T5 |
|---|---|---|---|
| C6 | 0.077 | 0 | 0.128 |
| C5 | 0.116 | 0.136 | 0.041 |

[HYP] **T28 is less stable than T1** because its tool steps are mostly transfer calls with intermediate support (mean
0.52, from summary-dependent NLI), and it has fewer references (15). Steps near 0 or 1 have small deviations
regardless of k, which is why T5 has the lowest deviations: its scores are mostly 0.

## 7. Deduplication effect [OBS]

Per run: deduplicated references vs duplicates retained, pilot-style.

| Task | Variant | Mean valid `m_ctx` | Coverage@0.5 |
|---|---|---|---|
| 28 | C5 (messages) | 0.683 → **0.733** | 0.714 → **0.952** |
| 28 | C6 | 1.00 → 1.00 | 1.00 → 1.00 |
| 1 | C4 (tools) | 0.896 → 0.901 | 1.00 → 1.00 |
| 1 | C5 | 0.264 → 0.281 | 0.095 → 0.095 |
| 5 | all | no duplicates; unchanged | — |

**Retaining duplicates inflates scores** where a run's own copies serve as its references: up to +0.24 coverage
(T28, C5). The class-level view in §3 and §5 is the primary result.

## 8. Agent-setup shift (descriptive) [OBS]

| Descriptor | T28 (T = 0) | T1 (T = 0) | **T5 (T = 1.0)** |
|---|---|---|---|
| Distinct tool sequences / classes | 2 / 16 | 7 / 23 | 5 / 16 |
| Successful classes without any tool call | 0 | 0 | **8 / 14** |
| Tool steps with any exact counterpart | 55% | 82% | **9%** |
| Mean C4 `m_ctx`, all tool steps | 0.71 | 0.82 | **0.02** |
| Valid transfer-message ceiling | 1.00 | 0.95 | **0.39** |

T5's low values come from the **behaviour of the temperature-1.0 runs**, not from a matching failure:
- most successful runs resolve the task in conversation without tools;
- the agent transfers in only 6 of 14;
- tool calls rarely recur identically.

**Where a counterpart exists, C4 and C6 reach the ceiling** (transfer messages: `m_ctx / cap` = 1.00; exact recall
2 / 2).

The regime shift is confounded with task differences: one task per regime.

## 9. Separation of causes

| Observed low value | Cause | Evidence |
|---|---|---|
| T1 `get_reservation_details` 0.75 | **reference frequency** (5 of 21 successful classes skip the lookup) | equals ceiling 0.75 |
| T5 failed-run `get_user_details` 0 | **reference frequency** (ceiling 0) | (a) in 14 / 14 references |
| T5 transfer messages 0.39 | **reference frequency** (ceiling 0.39) plus **agent setup** (few transfers) | C4 / C6 = ceiling |
| T28 2 exact misses | **matching failure**: R3 source threshold on paraphrased opening turns (0.486) | §4 |
| C5 message losses (T1 19 / 20 below 0.5) | **matching rule (C5 design)**: transfer call unmatched because summaries differ | transfer-call `m_ctx` 0.20 / 0.52 / 0.04 |
| Up to +0.24 coverage when duplicates are retained | **deduplication** | §7 |
| T5 tool-step scores near 0 | **agent setup / task**: no recurring tool calls | §8 |

## 10. Limitations

- **Labelled evidence is narrow:**
  - 40 labelled valid tool steps, 39 of them in T1, a previously exposed task;
  - 43 labelled valid messages, all the same policy text;
  - **T28, the only untouched hold-out, has no labelled tool steps.** Its tool-call evidence is the label-free
    exact-step recall.
- **No discrimination evidence:** the 4 incorrect steps are structural (tools absent from every successful run).
  Their 0 values would be produced by any tool-distinguishing matcher.
- **Exact-step recall** measures agreement with identical steps, not correctness. Non-exact transfer-call matches
  rely on NLI over free-text summaries.
- **One task per regime.** The T5 contrast is descriptive only.
- **Message judgements** (outcome-route inspection) are by one reviewer, and trivial here: all texts were
  identical.
- **E6 failed** as written, because T28's deviation exceeded 0.10. The threshold was set before the data; it is not
  revised.

## 11. Files

- **New:**
  - `gibs/validation/run_eval.py`;
  - `gibs/validation/results_eval/`: `partial/` (per query, per reference: C4, C5 and C6 maps and indicators),
    `eval_summary.json`, `per_step_eval.csv`, cost files, `model.json`;
  - this report.
- **Updated before computation:** `EVALUATION_PROTOCOL.md` (2B-final).
- **Unchanged:**
  - every pilot and variant result directory;
  - matching code;
  - labels;
  - thresholds.

Stopped for review: no GCN, no new trajectories, no threshold or matching change.
