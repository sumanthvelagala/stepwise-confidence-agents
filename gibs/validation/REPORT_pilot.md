# Consensus-mask pilot: A vs C0 vs C3 on Tasks 48, 9 and 25

Stage: methodology validation. **No GCN training, no full-corpus scoring, no threshold tuning, and no new matcher.**
The plan, step-label rules and "unexpected" criteria were fixed in `pilot_plan.md` before computing. None of the
following was changed afterwards: thresholds (τe = τv = 0.7, K = 10), graph construction, matching rules,
reference selection (leave-one-out over successful runs), or step labels.

**Consensus values are agreement with other successful runs. They are not correctness.** A benchmark success
does not mean every step in that run is correct. One successful T9 run, `7cd3469e`, announces a transfer it never
executed (§9.3).

## Files

| File | Content | Status |
|---|---|---|
| `pilot_plan.md` | pre-registration (tasks, variants, labels, "unexpected", reference-count analysis) | unchanged |
| `run_pilot.py` | `compute` (MCS per query × reference; resumable) and `analyze` | unchanged since the T48 preview |
| `step_verification.py` | independent step labels (never reads the reward) | unchanged |
| `results_pilot/task{48,9,25}_{A,C0,C3}.json` | every per-reference MCS result: node/edge maps, indicators, component count, rejections, cost | final |
| `results_pilot/per_step_masks.csv` | 595 agent steps × (label, m_node and m_ctx for A/C0/C3) | final |
| `results_pilot/pilot_summary.json`, `results_pilot/tables.md` | label summaries, unexpected cases, C0-vs-C3, reference-count curves, per-step tables | final |
| `pilot_diagnostics.py` → `results_pilot/diagnostics.{json,md}` | **post-hoc** diagnostics for §5–§9: distributions, m_ctx decomposition, cross-kind mappings, T48 lookup groups, pool composition, case studies with NLI scores | new; not pre-registered; no re-matching; 0 uncached NLI passes |
| `model.json` | DeBERTa-large-MNLI revision `7296194b…`, MPS, fp32 | unchanged |

## How to read this report

Every claim is tagged:
- **[OBS]**: read directly from the stored pilot outputs.
- **[VER]**: an independent step label from `step_verification.py`, which uses gold actions, NL assertions and the
  policy transfer message, never the reward.
- **[HYP]**: an explanation not tested in isolation.

Method provenance uses the earlier convention:
- **[PDF]**: `project_paper.pdf`.
- **[CODE]**: the author code at commit `1ccc8b8`.
- **[OURS]**: our adaptation.

---

## 1. What was run [OBS]

| | A (paper-style baseline) | C0 (configuration C) | C3 (C0 + symmetric truncation + multi-component) |
|---|---|---|---|
| Projection | paper-literal: data-dependency edges only; dependency-free events hang from ROOT ([CODE] construction applied to our events) | event-context: + context edge from the preceding event **[OURS]** | as C0 |
| Kind restriction | none | `require_same_kind` **[OURS]** | as C0 |
| Structured-field rejection | none | **[OURS]** | as C0 |
| MCS | single component ([PDF] Alg. 4) | single component | multi-component **[OURS]** |
| Overlength pairs | author truncation [CODE] | author truncation | symmetric **[OURS]** |

Shared by all three:
- NLI DeBERTa-large-MNLI with the max of both directions [CODE].
- τ = 0.7 and top-10 seeds [PDF].
- Source- and target-node threshold (R3, our reading of the PDF; the author code checks the target only).
- `m_node` [PDF C.2], plus `m_ctx`, our target: all incoming edges of the step mapped.
- Leave-one-out references [OURS]: a successful query uses every other successful run; a failed query uses all
  successful runs.

| Task | Successful | Failed | MCS runs per variant | C0 wall time (uncached NLI passes) | A | C3 |
|---|---|---|---|---|---|---|
| 48 | 10 | 13 | 220 | 3,544 s (3,945) | 3.8 s (10) | 2.1 s (3) |
| 9 | 17 | 4 | 340 | 2,030 s (7,275) | 3.5 s (4) | 75.8 s (123) |
| 25 | 19 | 3 | 399 | 10,907 s (35,152) | 104.5 s (208) | 180.8 s (289) |

Runtime is **not comparable across variants**. C0 ran first and filled the NLI cache; A and C3 mostly hit it. All three
variants request about the same NLI pairs (5.1k, 11.5k and 58.7k directional pairs per task). Caches and all result
files are preserved. No run was skipped.

## 2. Step labels [VER]

| Task | Success: valid | Success: incorrect | Success: attempted_incorrect | Success: unverified | Failed: valid | Failed: incorrect | Failed: attempted_incorrect | Failed: unverified |
|---|---|---|---|---|---|---|---|---|
| 48 | 20 (10 gold lookups, 10 transfer messages) | 0 | 0 | 34 | 13 (gold lookups) | 13 (cancellations) | 0 | 59 |
| 9 | 23 (9 gold searches, 14 transfer messages) | 0 | 0 | 103 | 4 (gold searches) | 8 (6 cancellations, 2 flight updates) | 0 | 41 |
| 25 | 19 (gold-equal bookings) | 0 | 0 | 207 | 1 (transfer message) | 2 (1 wrong booking, 1 cancellation) | 0 | 48 |

- **No `attempted_incorrect` steps occur.** No run in these tasks made a prohibited write that returned a tool error.
- **The unverified share is large: 492 of 595 steps (83%).** Nothing below says anything about their correctness.
  Their means are reported only for completeness.

## 3. Consensus by label (mean / median; full reference pool) [OBS]

| Task | Variant | Valid, successful runs: node | ctx | Valid, failed runs: node | ctx | Incorrect: node | ctx | Unverified, successful: node / ctx | Unverified, failed: node / ctx |
|---|---|---|---|---|---|---|---|---|---|
| 48 | A | 0.97 / 1.00 | 0.97 / 1.00 | 0.97 / 1.00 | 0.97 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.49 / 0.49 | 0.36 / 0.36 |
| 48 | C0 | 0.54 / 0.56 | 0.54 / 0.56 | 0.51 / 0.60 | 0.51 / 0.60 | 0.00 / 0.00 | 0.00 / 0.00 | 0.48 / 0.29 | 0.32 / 0.32 |
| 48 | C3 | 0.78 / 0.89 | 0.78 / 0.89 | 0.58 / 0.70 | 0.58 / 0.70 | 0.00 / 0.00 | 0.00 / 0.00 | 0.75 / 0.47 | 0.32 / 0.32 |
| 9 | A | 0.80 / 1.00 | 0.80 / 1.00 | 0.52 / 0.53 | 0.52 / 0.53 | 0.00 / 0.00 | 0.00 / 0.00 | 0.61 / 0.61 | 0.39 / 0.39 |
| 9 | C0 | 0.37 / 0.50 | 0.33 / 0.38 | 0.52 / 0.53 | 0.40 / 0.53 | 0.00 / 0.00 | 0.00 / 0.00 | 0.58 / 0.40 | 0.36 / 0.25 |
| 9 | C3 | 0.80 / 1.00 | 0.72 / 0.94 | 0.53 / 0.53 | 0.40 / 0.53 | 0.00 / 0.00 | 0.00 / 0.00 | 0.71 / 0.43 | 0.41 / 0.27 |
| 25 | A | 1.00 / 1.00 | 0.85 / 0.83 | 0.00 (n=1) | 0.00 | **0.47** (0.95 and 0.00) | 0.00 / 0.00 | 0.64 / 0.62 | 0.42 / 0.42 |
| 25 | C0 | 1.00 / 1.00 | 0.27 / 0.28 | 0.00 (n=1) | 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.58 / 0.46 | 0.36 / 0.29 |
| 25 | C3 | 1.00 / 1.00 | 0.27 / 0.28 | 0.00 (n=1) | 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.61 / 0.47 | 0.38 / 0.30 |

### Distribution of valid steps by type

Counts per bin: `[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`.

| Task | Valid step | Runs | n | A node | A ctx | C0 node | C0 ctx | C3 node | C3 ctx |
|---|---|---|---|---|---|---|---|---|---|
| 48 | gold lookup | success | 10 | 0.93 [0 0 0 1 3 6] | same | 0.42 [1 2 1 6 0 0] | same | 0.56 [0 2 1 6 1 0] | same |
| 48 | gold lookup | failed | 13 | 0.97 [0 0 0 0 4 9] | same | 0.51 [0 0 4 9 0 0] | same | 0.58 [0 0 4 9 0 0] | same |
| 48 | transfer message | success | 10 | 1.00 [0 0 0 0 0 10] | same | 0.67 [0 0 2 4 3 1] | same | 1.00 [0 0 0 0 0 10] | same |
| 9 | gold search | success | 9 | 0.50 [0 0 0 9 0 0] | same | 0.50 [0 0 0 9 0 0] | 0.39 [2 0 0 7 0 0] | 0.50 [0 0 0 9 0 0] | 0.39 [2 0 0 7 0 0] |
| 9 | gold search | failed | 4 | 0.52 [0 0 1 3 0 0] | same | 0.52 [0 0 1 3 0 0] | 0.40 [1 0 0 3 0 0] | 0.53 [0 0 0 4 0 0] | 0.40 [1 0 0 3 0 0] |
| 9 | transfer message | success | 14 | 1.00 [0 0 0 0 1 13] | same | 0.29 [1 4 6 3 0 0] | same | 1.00 [0 0 0 0 1 13] | 0.94 [0 0 0 0 14 0] |
| 25 | gold booking | success | 19 | 1.00 [0 0 0 0 0 19] | 0.85 [0 0 0 3 10 6] | 1.00 [all 19 at 1] | 0.27 [3 6 7 3 0 0] | 1.00 [all 19 at 1] | 0.27 [3 6 7 3 0 0] |
| 25 | transfer message | failed | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

Full bins for every label, including unverified, are in `results_pilot/diagnostics.md`.

## 4. Unexpected cases at the full reference pool [OBS]

Pre-registered: a valid step is unexpected if its value is < 0.5; an incorrect step is unexpected if its value is
≥ 0.5.

| Task | A: node | A: ctx | C0: node | C0: ctx | C3: node | C3: ctx |
|---|---|---|---|---|---|---|
| 48 (33 valid, 13 incorrect) | 0 | 0 | 10 | 10 | 7 | 7 |
| 9 (27 valid, 8 incorrect) | 1 | 1 | 12 | 14 | 0 | 3 |
| 25 (20 valid, 2 incorrect) | **2, including 1 incorrect step ≥ 0.5** | 1 | 1 | 17 | 1 | 17 |

Every case is listed in `tables.md`. The causes, which §5–§9 establish:

| Cases | Variants | Cause | Evidence |
|---|---|---|---|
| T48 gold lookups `s2` in the 8 runs where the user gives the reservation ID in the opening turn | C0, C3 | structural mismatch with runs where the ID comes in a later turn | §6 |
| T48 / T9 transfer messages | C0 only | single-component selection; C3 recovers all | §5, §8 |
| T9 gold searches: 7cd3469e, 49f89baf, 71270d8b ctx = 0 | C0, C3 | atypical predecessor event | §7.2 |
| T9 71270d8b node = 0.471 | A | 8 of 17 references | §7.2 |
| T25 valid bookings, ctx 0–0.44 | C0, C3 | the context edge | §7.1 |
| T25 51d355a9 transfer message = 0 | all three | no successful T25 run transfers, so it cannot be matched | §9.2 |
| **T25 6f12b024 s30 wrong booking, `m_node` = 0.947** | A | NLI does not separate the bookings; A has no field check | §9.1 |

**No incorrect step reaches ≥ 0.5 under C0 or C3, on either target.**

## 5. A vs C0 vs C3 per step [OBS]

**C0 → C3** (from `pilot_summary.json`):

| Task | m_node: steps changed | Increased / decreased | Mean Δ | m_ctx: steps changed | Increased / decreased | Mean Δ |
|---|---|---|---|---|---|---|
| 48 | 44 of 139 | 44 / 0 | +0.107 | 35 | 35 / 0 | +0.083 |
| 9 | 50 of 179 | 50 / 0 | +0.142 | 29 | 29 / 0 | +0.070 |
| 25 | 42 of 277 | 40 / 2 | +0.023 | 19 | 17 / 2 | +0.011 |

- The two decreases are unverified T25 steps. Each lost one reference: 16aac895 s18 node 0.111 → 0.056 and
  51d355a9 s10 0.368 → 0.316.
- [HYP] Symmetric truncation changes scores of overlength pairs, so component 0 differs. This was not traced.
- **C3 changes no incorrect-step value.**
- C3's large gains are the transfer messages:
  - T48 C0 0.67 → 1.00;
  - T9 C0 0.29 → 1.00 node and 0.94 ctx.
- These are the "small generic component lost by single-component selection" case already seen in the A/B/C
  validation. Here it happens systematically.

**A vs C3:**
- `m_ctx`: A ≥ C3 on every step except 4 T25 steps. A higher on 32 T48, 90 T9 and 140 T25 steps.
- `m_node`: mixed.
  - T48: A higher 28 times, C3 higher 10 times.
  - T9: A higher 8, C3 higher 28.
  - T25: A higher 56, C3 higher 7.

The structural reason is in §6–§7: A has no context edges, so a step needs fewer edges to match.

**Cross-kind mappings, only possible in A** (agent-step nodes mapped to a node of another kind; `diagnostics.json → cross_kind`):
- In all three tasks, the only cross-kind type is an agent message mapped to a **user turn**.
- **T48 valid steps: 36 of 300 mapped indicators.** 36 of the 90 A indicators for the valid transfer message
  "YOU ARE BEING TRANSFERRED…" map it to the reference's user turn "The user was transferred to a human agent."
  - Example: `07ec0bf6` vs `c890f90b` under A maps `N:s6 → N:u11` and `N:u7 → N:s10`, i.e. agent message and user
    turn are swapped.
- Unverified steps: T48 20; T9 21 of 1,282; T25 60 of 2,782.
- C0 and C3: 0 by construction.

## 6. Run 5b5eaa71 (T48, successful): why C0 gives the valid lookup 0.0

Run: s0 greeting; u1 opening request **containing the reservation ID**; s2 `get_reservation_details(3RK2T9)`; s4
transfer; s6 transfer message; u7.

The lookup's single incoming edge is `N:u1 → N:s2`:
- roles context + data;
- operation text "Call get_reservation_details with reservation_id = 3RK2T9.";
- source: the opening user turn.

The nine references split into two groups (`diagnostics.json → t48_lookup_groups`):
- **O** (ID in the opening turn, lookup edge `N:u1 → N:s2`): 07ec0bf6, 59810305, 78c107ed.
- **L** (agent asks for the ID first; lookup edge `N:u3 → N:s4`): 655b2a43, a41818c2, aa08e645, adcf197e,
  c890f90b, e6daf449.

**Per reference: NLI scores of the best candidate for the lookup edge** (`case_studies.T48_5b5eaa71_s2`, read from
the cache) [OBS]:

| Reference group | Reference edge | s_edge | s_src (opening turn vs reference source turn) | s_tgt (lookup results) | Candidate? | C0 | A | C3 |
|---|---|---|---|---|---|---|---|---|
| O (3 refs) | `N:u1→N:s2` | 0.984 | **0.191** | 0.978 | **no**: fails the source-node threshold (R3) | 0 | 0 | 0 |
| L (6 refs) | `N:u3→N:s4` | 0.984 | 0.985 | 0.978 | yes (no field rejection) | **0** | 1 | 1 |

**Mechanism 1: source-node threshold against O references** [OBS]. The opening turns of `5b5eaa71` and `07ec0bf6`
differ only slightly.
- `5b5eaa71`: "…My name is Anya Garcia, my user ID is anya_garcia_5901, and the confirmation number is 3RK2T9."
- `07ec0bf6`: "…My user ID is anya_garcia_5901 and the confirmation number is 3RK2T9. How can we proceed?"

Their directional entailment scores are 0.072 and 0.191, so the maximum of 0.191 is below τv = 0.7 and the
candidate is never created. [HYP] Each text contains something the other lacks (the name; the closing question),
so neither entails the other.

This is the [PDF]-reading source check (R3); the author code checks only the target node [CODE]. So this rejection
is specific to our R3 decision and affects A as well. It accounts for **every** miss in the O×O cell of the matrix
below: 10 of 28 pairs, all involving `5b5eaa71`.

**Mechanism 2: single-component selection against L references** (C0) [OBS]. The candidate
`N:u1→N:s2 ↦ N:u3→N:s4` exists, but in the event-context graph it cannot join a larger component:
- the query's `N:s0→N:u1` would need `u1 ↦ u1` (opening turns; 5b5eaa71 ⇒ c890f90b.u1 = 0.077);
- the lookup's outgoing context edge `N:s2→N:s4` (operation: the transfer) faces the reference's
  `N:s4→N:s6` (lookup → apology message), which has a different operation and a different target kind.

The lookup component is therefore 1 edge + 2 nodes (size 3). The transfer component
`N:s4→N:s6, N:s6→N:u7 ↦ N:s8→N:s10, N:s10→N:u11` has 2 edges + 3 nodes (size 5) and wins. The stored C0 map against
c890f90b is exactly `{N:s4: N:s8, N:s6: N:s10, N:u7: N:u11}`. It is the same pattern for all 6 L references, so the
result is 0/9.

**Why C3 recovers it, and why that recovery is fragile** [OBS]:
- C3 adds the lookup as a further component against all 6 L references, giving 0.667.
- The same recovery fails for the *other* O runs. For `07ec0bf6` vs `c890f90b`:
  - the greeting component maps `N:s0→N:u1 ↦ N:s0→N:u1`, because 07ec0bf6.u1 ⇒ c890f90b.u1 = **0.964**;
  - that fixes `u1 ↦ u1` in the global node map;
  - the lookup candidate needs `u1 ↦ u3`, so global consistency rejects it (stored C3 map:
    `{…, N:s0: N:s0, N:u1: N:u1}` and no `N:s2`).
- For `5b5eaa71`, the same opening-turn comparison is a near-miss (0.077), which leaves `u1` free. **C3 recovers
  5b5eaa71 because of an NLI false negative on its opening turn.** This is not a principled fix.

**T48 lookup mapping rate by query × reference group** (`m_node` = `m_ctx` here; pair counts in parentheses) [OBS]:

| | O×O (28) | O×L (48) | L×O (60) | L×L (84) |
|---|---|---|---|---|
| A | 0.643 | **1.000** | **1.000** | 1.000 |
| C0 | 0.643 | 0.021 | 0.017 | 1.000 |
| C3 | 0.643 | 0.146 | 0.267 | 1.000 |

**Conclusion:**
- The T48 "unexpectedly low" lookups are a cross-group structural mismatch.
- The lookup is the same operation on the same value; only the turn that supplied the ID differs.
- The context edge [OURS] plus one-to-one consistency with the greeting chain causes it.
- A has no context edges and matches across groups. That is the whole of A's T48 lookup advantage.

### Similar mismatches in T9 and T25

**T25 bookings** (§7.1): the same mechanism, at a larger scale.
- 12 of 19 gold bookings are immediately preceded by an errored booking attempt ("Payment amount does not add
  up…").
- The rest are preceded by a user confirmation (6) or a search result (1).
- The context edge only matches a reference with the same kind of predecessor.

**T9 searches** (§7.2): three individual cases.

**Opening-turn ID placement does not recur:**
- T9 and T25 gold tool calls take their data edges mostly from tool results.
- In T25, the opening-turn data edge `u1 →` booking maps in 0.56–1.00 of references (§7.1). [HYP] Opening-turn
  paraphrases sometimes fail NLI, as in T48.

## 7. Where `m_ctx` loses valid steps: decomposition [OBS]

From the stored edge maps, with no re-matching (`diagnostics.json → ctx_decomposition`):
- **"node & all data edges"** = the fraction of references in which the node and all of its data-dependency edges
  are mapped.
- **"pure-context edge mapped"** = the fraction in which its context-only edge (an [OURS] edge) is mapped.

| Task | Variant | Valid, successful runs: m_ctx | Node & all data edges | Pure-context edge mapped (steps that have one) |
|---|---|---|---|---|
| 48 | C0 | 0.544 | 0.544 | 0.667 (10 transfer messages) |
| 48 | C3 | 0.778 | 0.778 | 1.000 (10) |
| 9 | C0 | 0.326 | 0.372 | 0.250 (16) |
| 9 | C3 | 0.723 | 0.802 | 0.820 (16) |
| 25 | C0 | 0.269 | **0.854** | **0.304** (19) |
| 25 | C3 | 0.269 | **0.854** | **0.304** (19) |
| 25 | A (no context edges) | 0.854 | 0.854 | — |

### 7.1 T25 gold bookings: node 1.0, ctx 0.27 (C0 and C3)

Mean mapping rate of each incoming edge of the 16 C3 node-high / ctx-low valid bookings (`node_high_ctx_low`):

| Incoming edge | Mapping rate |
|---|---|
| data from tool results (`get_user_details`, `get_reservation_details`) | 1.00 (32 edges) |
| data from user turns (`u1`, `u5`) | 0.91 (32) |
| **pure context from the preceding tool result** (the errored attempt) | **0.35** (10) |
| **pure context from the preceding user turn** ("Yes, please…") | **0.13** (6) |

Example: `1e01a088 s18`, node 1.00, ctx 0.00.
- Its four data edges (`s8`, `s6`, `u1`, `u5`) map in 100% of references.
- Its context edge `N:s16 → N:s18` comes from the errored booking result `s16`. It maps in 0 of 18 references,
  because no reference contains the same error result followed by a successful booking.

So `m_ctx` here measures whether the run hit the same recoverable payment error first, not whether the booking
was supported. [HYP] Error retries are benign in this task and should not lower support for a gold-equal booking.

### 7.2 T9 gold searches: ctx 0 in three runs

`search_direct_flight(JFK→MCO, 2024-05-22)`. Each run's context edge comes from an event no reference has
immediately before its search:

| Run | Context source |
|---|---|
| `7cd3469e s12` | a user turn |
| `49f89baf s16` | `get_flight_status` → "available" |
| `71270d8b s10` (failed) | a lookup of IFOYYZ |

The data edges map in about half of the references.

**The node values are capped by the reference pool, not by the matcher:**
- Only 10 of 17 successful T9 runs contain a successful `search_direct_flight`, and 9 of them carry the gold one.
- A successful query therefore has at most 8 of 16 matching references, so `m_node` ≤ 0.5.
- A failed query has 9 of 17 (≤ 0.529).
- All three variants reach this cap (0.50 / 0.529). The one exception is A on `71270d8b`, at 0.471 (8 of 17).

The pre-registered 0.5 threshold sits exactly at the cap. [OBS] This is a property of the [PDF] mask definition:
consensus counts how many successful runs share the step. A valid step on one of several valid paths gets low
consensus by design.

## 8. C3 node-high / ctx-low cases (m_node ≥ 0.5, m_ctx < 0.5) [OBS]

| Variant | Count | Composition |
|---|---|---|
| C3 | 98 | T9 `get_reservation_details` (unverified) 21; T25 `book_reservation` unverified 21 and **valid 16**; transfer calls (unverified) T9 17, T48 10; T25 `get_user_details` 4; T9 valid searches 3; messages 6 |
| C0 | 79 | similar |
| A | 9 | T25 bookings: 8 unverified, **1 incorrect** (§9.1) |

**Transfer calls are not labelled valid by the pre-registered rules.** Only the policy message after a successful
transfer is labelled valid, because transfer summaries are free text and there is no gold transfer action. Their
correctness is therefore **unverified**. They are reported here because they are the clearest node-high / ctx-low
mechanism.

Example: `c890f90b s8` (T48, C3), node 1.00, ctx 0.11.

| Reference | Operation similarity | Node map | Edge map | ctx | Mechanism |
|---|---|---|---|---|---|
| `e6daf449` (identical trajectory text) | — | — | both incoming edges `N:u7→N:s8` and `N:s4→N:s8` map with s_edge 0.991 | **1** | — |
| `07ec0bf6` | **0.016** | `N:s8 → N:s4`, `N:s10 → N:s6`, `N:u11 → N:u7` | `N:s8→N:s10 ↦ N:s4→N:s6` (transfer → message), **not** the s8 incoming edges | 0 | the node is in the MCS only as the **source of its successor edge**, the transfer message edge. Its source similarity compares the two transfer results ("Transfer successful"), which are identical |

The two summaries in the `07ec0bf6` row:
- `c890f90b`: "User claims booking was made 10 hours ago but system shows created_at 2024-05-02. User wants to
  appeal…"
- `07ec0bf6`: "User wants to cancel reservation 3RK2T9 but cancellation not eligible…"

Across the 27 C3 node-high / ctx-low transfer calls, node support came:
- only through the successor edge for 12 calls (T48 6, T9 6);
- through a mix of incoming and successor edges for 15 (T48 4, T9 11).

[OBS] `m_node` here says "a transfer happened at this point". `m_ctx` says "the same transfer, with an entailed
summary, from the same inputs". The second is the stricter reading of the step's operation.

The T25 valid bookings (§7.1) and T9 searches (§7.2) are the other node-high / ctx-low valid cases. In both, the
missing edge is the context edge.

## 9. Incorrect steps and reference-pool composition

### 9.1 The only discriminative incorrect step: T25 `6f12b024 s30`

The booking has dates 2024-05-21 and flights HAT097 + HAT267, paying 171 by card. The gold booking has
2024-05-17, HAT097 + HAT251, and 247. [VER] incorrect.

- **A:** maps it to the reference's gold booking in **18 of 19 references** (`m_node` 0.947). Against `0f0f7358`:
  `N:s30 ↦ N:s16` with s_edge 0.831, s_tgt 0.924. Its `m_ctx` is 0, because the data edge from its own search for
  the wrong date `s26` finds no counterpart.
- **C0 and C3:** reject every such candidate with explicit reasons, for example "args.flights: (hat097, 2024-05-21),
  (hat267, 2024-05-21) != (hat097, 2024-05-17), (hat251, 2024-05-17)" and "args.payment_methods …". Result: 0 / 0.
- This confirms the probe findings (P07, P08): DeBERTa does not separate long structured texts that differ in one
  or two fields.

### 9.2 All other incorrect steps get 0 for structural reasons

`diagnostics.json → pool`:
- No successful T48 or T9 run contains any write tool.
- No successful T25 run contains `cancel_reservation`.

So 22 of the 23 incorrect steps (13 T48 cancellations; 6 cancellations and 2 flight updates in T9; 1 T25
cancellation) **cannot** have a counterpart under any matcher that does not map a cancellation onto a different
tool. Their 0 is guaranteed by the reference pool and is **not evidence that a variant discriminates**. Across the
three tasks, the discriminative test of incorrect steps rests on **n = 1** (§9.1).

The same applies in the other direction to `51d355a9 s22` (T25, failed run): it is a valid transfer message, but no
successful T25 run transfers, so it is 0 under every variant.

### 9.3 Benchmark success ≠ step correctness

T9 `7cd3469e` is a successful run. It never calls `transfer_to_human_agents`, yet its final message `s14` ends with
"YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."
- [VER] unverified, because the rule requires a preceding successful transfer call.
- As a reference, this message is where the other runs' transfer message maps (A and C3 node).
- It is why T9 C3 transfer messages have ctx 0.938 (15/16).

Also, T48 has duplicate trajectories: 10 successful runs but 8 distinct agent-step texts (`c890f90b` = `e6daf449`
and `07ec0bf6` = `78c107ed`). Near-duplicates inflate agreement and shrink the effective number of references.

## 10. Stability as the reference count grows [OBS]

Mean absolute deviation of a step's mask from its full-pool value, over 50 random subsets per k:

| Task | Variant | Target | k=1 | 2 | 3 | 5 | 8 |
|---|---|---|---|---|---|---|---|
| 48 (pool 9–10) | A | node | 0.104 | 0.066 | 0.054 | 0.033 | 0.014 |
| 48 | C0 | node | 0.229 | 0.130 | 0.100 | 0.063 | 0.030 |
| 48 | C3 | node | 0.144 | 0.084 | 0.059 | 0.040 | 0.020 |
| 9 (pool 16–17) | A | node | 0.225 | 0.143 | 0.114 | 0.085 | 0.055 |
| 9 | C0 | node | 0.264 | 0.172 | 0.132 | 0.102 | 0.066 |
| 9 | C3 | node | 0.204 | 0.133 | 0.106 | 0.083 | 0.055 |
| 25 (pool 18–19) | A | node | 0.178 | 0.121 | 0.097 | 0.071 | 0.049 |
| 25 | C0 | node | 0.166 | 0.116 | 0.091 | 0.068 | 0.048 |
| 25 | C3 | node | 0.165 | 0.115 | 0.090 | 0.068 | 0.048 |

The ctx curves are similar; all of them are in `tables.md`.
- **Deviation falls monotonically with k for every variant and target.**
- **Mean consensus by label does not drift with k** (for example T48 C3 valid 0.704 → 0.699; T25 C3 valid node 0.95
  at every k). This is expected, because random subsets give unbiased estimates of the full-pool mean.
- **T48 at k = 8 is close to the full pool of 9–10** (finite-population effect). Its small deviation is therefore
  not comparable with T9 and T25, where k = 8 is about half the pool.
- **With about 8 references, single steps still move by about ±0.05 on average** (T9 and T25). Masks from fewer
  than about 5 references deviate by ≥ 0.07–0.10.
- **The pre-registered "unexpected rate" is not monotone in k** (for example T48 C0 node: 0.34, 0.17, 0.32, 0.32,
  0.19). That is a discreteness artifact: at k = 2 a mask is 0, 0.5 or 1, and 0.5 does not count as low. The rate
  is not a stability measure.

## 11. Critical comparison

### Does A's T48 advantage generalise?

**Only partly; the reason is the topology, not the paper's algorithm.**

| | T48 | T9 | T25 |
|---|---|---|---|
| Valid (successful runs), `m_node`: A vs C3 | 0.97 vs 0.78 | 0.80 vs 0.80 | 1.00 vs 1.00 |
| Valid, `m_ctx`: A vs C3 | 0.97 vs 0.78 | 0.80 vs 0.72 | **0.85 vs 0.27** |
| Incorrect ≥ 0.5 | A 0, C3 0 | A 0, C3 0 | **A 1 (0.947)**, C3 0 |

- A's advantage on valid steps comes from having **no context edges**:
  - T48 lookups across the O/L groups (§6);
  - T25 bookings after an error retry (§7.1).
- On `m_node` A gains nothing over C3 in T9 and T25, which is where most transfer messages and bookings are.
- Its advantages carry two costs that C3 does not have:
  1. **It assigns high consensus to the one incorrect step that has a counterpart in the references** (§9.1). This
     is the only discriminative incorrect-step test in the pilot.
  2. **Cross-kind mappings** (§5). In T48, 36 of A's 90 support indicators for the valid transfer message map it to
     a user turn.

### C0

C0 is dominated by C3:
- 0 decreases on valid or incorrect steps;
- 2 unverified steps lose one reference each;
- all transfer-message losses are recovered.

### C3

- C3 keeps every incorrect step at 0 on both targets.
- It recovers transfer messages and the T9 search nodes up to the pool cap.
- Its remaining valid-step losses come from two sources:
  - the **[OURS] context edge**: T48 O/L lookups, T25 error-retry bookings and three T9 searches;
  - **pool composition**: the T9 search cap and 51d355a9.
- Its T48 recovery of 5b5eaa71 is fragile (§6).
- Note: in C3, `m_node` and `m_ctx` diverge mainly through the context edge. They do **not** separate valid from
  incorrect steps here, because incorrect steps are 0 on both.

## 12. Would an information-based dependency matcher be a justified future adaptation? (assessment only; not implemented)

**The idea:** a step's context is supported when it uses the **same information**, i.e. the same argument values
obtained from earlier observations or user turns (`dependency_values`, `values` on data-dependency edges). It would
not depend on which event delivered that information, or on what event happened to precede it.

**Evidence that it addresses a real failure:**
1. In all three tasks, the valid-step failures of `m_ctx` are dominated by **where** an input came from or **what
   preceded** the step, not by **which** input was used. In T25, data edges map 0.85 while the context edge maps
   0.30 (§7).
2. T48 shows the same pattern: the lookup consumes the same value `3RK2T9` from turn u1 vs u3 (§6).
3. A's results show that dropping the context edge already removes most of these failures.

**Risks:**
1. **It departs from the paper.** [PDF] GIBS compares graph structure via an MCS over NLI-scored operations and
   results. A value-set matcher is closer to argument alignment than to subgraph matching. It would need to be
   reported as a separate adaptation with its own ablation, not as "GIBS".
2. **Provenance can matter for correctness.** A value can be right by coincidence, hallucinated, or taken from the
   wrong passenger or reservation (cf. V3: a wrong DOB relayed from the user). Matching on values regardless of
   source would support such steps. Value occurrence is detected by string matching (`value_occurs`), and common
   values (dates, "economy", "no", amounts) give spurious provenance.
3. **Ordering signals would be lost.** Policy checks ("look up eligibility before cancelling") live in *what came
   before*. The context edge is the only place where the current graph sees them. An information-only matcher would
   rate a cancellation made without checking the same as one made after checking, provided the values are equal.
4. **Circularity with the labels.** Our labels compare arguments with gold actions. A value-based matcher would use
   the same signal, so the pilot labels could no longer validate it independently. A different validation (for
   example, manual blind labels) would be needed.
5. **Scope.** A new matcher needs a pre-registration, tests and its own threshold choices (for example, partial value
   overlap), and none of that is in place.

**Assessment:** justified as a *diagnostic* target. A cheaper intermediate step is available that needs **no new
matcher**: the paper-literal topology (data edges only), which the paper's own construction already uses, combined
with our field checks and kind restriction. §13 proposes exactly that.

## 13. Limitations

- **Three tasks and one agent regime.** 595 agent steps, of which **only 103 are labelled**. T25 has 1 failed-run
  valid step and 2 incorrect steps.
- **The incorrect-step evidence is n = 1 discriminative case** (§9.2). The remaining zeros are guaranteed by the
  pool.
- **Labels are rule-based**, cover only gold-equal steps and the policy message, and do not label transfer calls or
  agent explanations. One annotator wrote the rules (before computing).
- **Near-duplicate references** in T48.
- **§5–§9 are post-hoc**, done after seeing the results. No setting was changed in response to them.
- **R3 (source-node check) is our reading of the PDF.** The 5b5eaa71 O×O misses depend on it. Its sensitivity was
  not measured.

## 14. Recommendation

**Do not adopt A or C0. Keep C3 as the provisional configuration, report `m_node` (paper target) and `m_ctx` side by
side, and run one further targeted, pre-registered validation before any GCN training or full-corpus scoring.**

Why:
- **A:** high valid-step consensus, but it fails the only discriminative incorrect-step case (0.947) and produces
  cross-kind mappings.
- **C0:** dominated by C3.
- **C3:** safe on incorrect steps. Its valid-step losses are traceable to the [OURS] context edge and to pool
  composition, not to NLI.

**Proposed targeted validation.** Run it only on approval. It needs no new matcher, no threshold change and the
same reference sets.

1. **Variant "C3-PL":** C3 with the paper-literal topology (data-dependency edges only), keeping the
   structured-field check, `require_same_kind`, symmetric truncation and multi-component matching. Everything except
   the topology is already a flag in `run_pilot.VARIANTS`.
   - Before running, add a unit test that field checks behave correctly on ROOT-sourced edges.
   - The NLI pairs are A's, which are already cached, so the expected cost is minutes.
2. **Optional ablation:** C3-PL with `check_source_nodes=False` (the author code's target-only check), to measure the
   R3 effect seen in §6.
3. **Pre-registered expectations to test:**
   - T48 O/L lookups are recovered;
   - T25 `6f12b024 s30` stays < 0.5 on both targets;
   - zero cross-kind mappings;
   - T25 valid-booking `m_ctx` near its data-edge value (0.85);
   - no incorrect step ≥ 0.5;
   - T9 transfer messages stay ≥ 0.9.
4. **Add at least one task where incorrect steps have same-tool counterparts in successful runs** (wrong-argument
   writes, like T25), chosen before computing, so that discrimination rests on more than one step. Candidates
   should be selected from the existing corpus by the pre-registration rule, not by looking at masks.

**GCN suitability:** not yet. The masks agree with the independent labels where labels exist. However, (i) 83% of
steps are unverified, (ii) the incorrect-step evidence is one case, and (iii) valid-step consensus is partly
determined by path frequency and our context edge. These need to be settled before the masks are used as training
targets.

## 15. Tests and integrity [OBS]

- `.venv/bin/python -m pytest gibs/tests -q -p no:cacheprovider`: **65 passed**.
- `nibs/tests`: **52 passed, 1 skipped** (as before).
- No test failures.
- Unchanged:
  - `pairs.json` sha256 `c075979c…d738`;
  - the v0.1 Task 48 example files (`49ac93e1…`, `5449156a…`, `ab4b6477…`).
- No tracked file was modified (`git diff` empty), nothing was committed, and the generated `__pycache__`
  directories were removed.
- Benchmark trajectories were not modified.

Stopped here: no GCN training, no full-corpus scoring, no threshold tuning, no new matcher.
