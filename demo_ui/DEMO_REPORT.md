# Phase 2 demonstration: reference cap 5 versus cap 17

Same 1,000 tau2 Airline trajectories, all 50 tasks, frozen input, four task-group folds, seeds 7/17/27, graph implementation, architecture and objective. Minimum three references in both experiments. Only the maximum reference cap changes.
Training targets use successful training-only references; NIBS evaluation uses its broader successful same-task reference bank. Actual cap-17 training counts range from 3 to 16. No new trajectories or LLM training were required.
Each experiment has 860 targets per teacher family and 24 GCN checkpoints. All 1,000 trajectories receive held-out learned predictions. The common comparison has 911 queries; tool AUROC uses 26 tasks with both labelled classes and localization uses 173 eligible failed queries.
Independent human review is pending. Unverified steps are not assumed correct. Learned results are three-seed means; differences are descriptive, with no significance test. These are our agent-benchmark results, not values copied from the paper.

## Main findings

- GIBS improves: tool AUROC 0.700 → 0.723 and first-error Top-1 34.1% → 40.7% (+6.6 percentage points).
- C4 declines: tool AUROC 0.719 → 0.706 and Top-1 52.2% → 49.3% (−2.9 percentage points).
- tool_sim has the best tool AUROC; NIBS Mean has the best first-error Top-1. GIBS/C4 still trail last-step-first (66.5%) on localization.
- The reference-access difference, imperfect teacher targets and incomplete automatic labels limit conclusions. Extra references do not guarantee improved error detection.
- A plausible explanation is that extra matches change the supervision targets; why C4 regresses specifically needs further diagnosis. This experiment does not isolate the mechanism.

## Tool Calls

| Method | 3–5 AUROC | 3–17 AUROC | 3–5 Top-1 | 3–17 Top-1 |
|---|---:|---:|---:|---:|
| GIBS | 0.6999 | 0.7233 | 34.1% | 40.7% |
| C4 | 0.7193 | 0.7055 | 52.2% | 49.3% |
| tool_sim | 0.9935 | 0.9944 | 59.0% | 61.5% |
| NIBS Max | 0.9305 | 0.9161 | 57.2% | 54.3% |
| NIBS Mean | 0.7237 | 0.7312 | 71.7% | 72.3% |
| Random expectation | 0.5000 | 0.5000 | 14.3% | 14.3% |
| Last-step-first | 0.7261 | 0.7261 | 66.5% | 66.5% |

## All Agent Steps

| Method | 3–5 AUROC | 3–17 AUROC | 3–5 Top-1 | 3–17 Top-1 |
|---|---:|---:|---:|---:|
| GIBS | 0.7348 | 0.7464 | 31.2% | 38.2% |
| C4 | 0.7051 | 0.6888 | 45.9% | 41.0% |
| tool_sim | 0.9950 | 0.9958 | 59.0% | 61.5% |
| NIBS Max | 0.9133 | 0.8758 | 1.2% | 0.0% |
| NIBS Mean | 0.7283 | 0.7267 | 16.2% | 16.2% |
| Random expectation | 0.5000 | 0.5000 | 6.3% | 6.3% |
| Last-step-first | 0.6010 | 0.6010 | 0.0% | 0.0% |

## Five actual examples

Post-hoc illustrative cases chosen by actual tool-only first-error rankings, with MCS targets available. Not a representative sample or a new aggregate estimate.
Every example below is a failed benchmark run. Success means identifying its first automatically labelled tool error, not solving the airline task. Predictions shown are from held-out seed-7 models. MCS targets are post-hoc diagnostics; they were not supplied to held-out inference.

### 1. GIBS finds the first error

Task 5 · run `53791b7d-4fff-4313-8fb0-5c65607ac2a7` · seed 7.

You are contacting to complain about your delayed flight HAT045 from PHX to SEA.

The agent sends a compensation certificate. The expected action list contains no write action, so the automatic verifier flags this as an extra action.

At seed 7 under cap 17, GIBS assigns the first labelled tool error the unique lowest tool score; NIBS Mean ranks another step lower. A localization success does not mean the underlying booking task succeeded.

First labelled tool error: step 9, `send_certificate`. Verifier reason: gold actions contain no write; send_certificate executed

| Method | 3–5 error score | 3–5 rank | 3–17 error score | 3–17 rank |
|---|---:|---:|---:|---:|
| GIBS | 0.0034 | 1–1 | 0.0042 | 1–1 |
| C4 | 0.0003 | 1–1 | 0.0001 | 1–1 |
| NIBS Mean | 0.8189 | 2–2 | 0.8222 | 2–2 |
| NIBS Max | 0.9605 | 2–2 | 0.9605 | 2–2 |
| tool_sim | 0.0000 | 1–2 | 0.0000 | 1–2 |

Rank 1 is the lowest tool score. Rank ranges show exact score ties; a tie is not counted as a unique hit.

- cap5, GIBS: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap5, C4: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap17, GIBS: error target 0.0000 = 0 / 14 successful-reference support indicators.
- cap17, C4: error target 0.0000 = 0 / 14 successful-reference support indicators.

Local UI: `#explorer?experiment=cap17&run=53791b7d-4fff-4313-8fb0-5c65607ac2a7&example=gibs_success`. Inspect Step scores → Trajectory graph → MCS & targets → Transcript. Switch the active experiment to compare the same execution.

### 2. NIBS catches what GIBS misses

Task 17 · run `1bbd75e4-f4f4-445e-86a6-a27f7a520b87` · seed 7.

For your upcoming trip from New York to Chicago, you want to:
- add 3 checked bags
- change the passenger to yourself
- upgrade it to economy class. 

Mention all three things at once and in this order.

The baggage update specifies one nonfree bag, while the expected call specifies zero. The automatic verifier flags this argument mismatch.

At seed 7 under cap 17, NIBS Mean uniquely identifies the first labelled tool error while GIBS misses it. NIBS has successful same-task references at scoring time; the held-out GCN sees only the query graph.

First labelled tool error: step 12, `update_reservation_baggages`. Verifier reason: conflicts with every gold update_reservation_baggages action: g2: args.nonfree_baggages: 1.0 != 0.0

| Method | 3–5 error score | 3–5 rank | 3–17 error score | 3–17 rank |
|---|---:|---:|---:|---:|
| GIBS | 0.9029 | 3–3 | 0.0119 | 2–2 |
| C4 | 0.9512 | 3–3 | 0.0470 | 2–2 |
| NIBS Mean | 0.8062 | 1–1 | 0.8062 | 1–1 |
| NIBS Max | 0.9997 | 2–2 | 0.9997 | 2–2 |
| tool_sim | 0.7500 | 2–2 | 0.7500 | 2–2 |

Rank 1 is the lowest tool score. Rank ranges show exact score ties; a tie is not counted as a unique hit.

- cap5, GIBS: error target 0.0000 = 0 / 4 successful-reference support indicators.
- cap5, C4: error target 0.0000 = 0 / 4 successful-reference support indicators.
- cap17, GIBS: error target 0.0000 = 0 / 4 successful-reference support indicators.
- cap17, C4: error target 0.0000 = 0 / 4 successful-reference support indicators.

Local UI: `#explorer?experiment=cap17&run=1bbd75e4-f4f4-445e-86a6-a27f7a520b87&example=nibs_beats_gibs`. Inspect Step scores → Trajectory graph → MCS & targets → Transcript. Switch the active experiment to compare the same execution.

### 3. GIBS misses in both settings

Task 23 · run `1b84a141-f1a4-444c-ae3c-a3832e6ba4b7` · seed 7.

You want to know the sum of gift card balances and the sum of certificate balances.

Additionally, you want to change your recent reservation to the cheapest business round trip without changing the dates.

The agent combines three passengers in one booking, while the expected calls list the passengers separately. Payment allocations also differ. The verifier flags these passenger and payment mismatches.

At seed 7, GIBS misses this error in both settings, although the cap-17 MCS teacher gives the erroneous step at least 0.8 support. This shows why agreement with successful structures is not correctness ground truth. Independent human validation is still needed.

First labelled tool error: step 16, `book_reservation`. Verifier reason: conflicts with every gold book_reservation action: g1: args.passengers: (('mohamed', 'silva', '1960-11-26'), ('raj', 'sanchez', '1986-09-12'), ('liam', 'wilson', '1980-03-27')) != (('mohamed', 'silva', '1960-11-26'),); args.payment_methods: (('certificate_3765853', 500.0), ('credit_card_2198526', 1786.0), ('gift_card_6136092', 129.0), ('gift_card_8020792',... != (('certificate_3765853', 500.0), ('credit_card_2198526', 44.0), ('gift_card_6136092', 129.0), ('gift_card_8020792', 1... | g2: args.passengers: (('mohamed', 'silva', '1960-11-26'), ('raj', 'sanchez', '1986-09-12'), ('liam', 'wilson', '1980-03-27')) != (('raj', 'sanchez', '1986-09-12'),); args.payment_methods: (('certificate_3765853', 500.0), ('credit_card_2198526', 1786.0), ('gift_card_6136092', 129.0), ('gift_card_8020792',... != (('certificate_9984806', 250.0), ('credit_card_2198526', 621.0)) | g3: args.passengers: (('mohamed', 'silva', '1960-11-26'), ('raj', 'sanchez', '1986-09-12'), ('liam', 'wilson', '1980-03-27')) != (('liam', 'wilson', '1980-03-27'),); args.payment_methods: (('certificate_3765853', 500.0), ('credit_card_2198526', 1786.0), ('gift_card_6136092', 129.0), ('gift_card_8020792',... != (('certificate_2765295', 250.0), ('credit_card_2198526', 621.0))

| Method | 3–5 error score | 3–5 rank | 3–17 error score | 3–17 rank |
|---|---:|---:|---:|---:|
| GIBS | 0.1713 | 5–5 | 0.0432 | 5–5 |
| C4 | 0.1131 | 4–4 | 0.0837 | 4–4 |
| NIBS Mean | 0.7848 | 2–2 | 0.7828 | 1–1 |
| NIBS Max | 0.9443 | 1–1 | 0.9404 | 1–1 |
| tool_sim | 0.8182 | 3–3 | 0.8182 | 3–3 |

Rank 1 is the lowest tool score. Rank ranges show exact score ties; a tie is not counted as a unique hit.

- cap5, GIBS: error target 1.0000 = 5 / 5 successful-reference support indicators.
- cap5, C4: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap17, GIBS: error target 1.0000 = 10 / 10 successful-reference support indicators.
- cap17, C4: error target 0.0000 = 0 / 10 successful-reference support indicators.

Local UI: `#explorer?experiment=cap17&run=1b84a141-f1a4-444c-ae3c-a3832e6ba4b7&example=gibs_failure`. Inspect Step scores → Trajectory graph → MCS & targets → Transcript. Switch the active experiment to compare the same execution.

### 4. More references help GIBS

Task 15 · run `0857b47b-432c-478f-8ae8-f059ce8da11c` · seed 7.

For your upcoming trip from ATL to PHL, you want to change for the cheapest flight in Economy cabin class (not Basic Economy) and for the day after the original reservation.

The flight update selects HAT227 and HAT139, while the expected call selects HAT110 and HAT172. The automatic verifier flags the different itinerary.

At seed 7, GIBS misses the first labelled tool error with cap 5 and identifies it uniquely with cap 17. The graph and error label are unchanged; targets and learned weights come from the corresponding experiment.

First labelled tool error: step 14, `update_reservation_flights`. Verifier reason: conflicts with every gold update_reservation_flights action: g0: args.flights: (('hat227', '2024-05-24'), ('hat139', '2024-05-24')) != (('hat110', '2024-05-24'), ('hat172', '2024-05-24'))

| Method | 3–5 error score | 3–5 rank | 3–17 error score | 3–17 rank |
|---|---:|---:|---:|---:|
| GIBS | 0.0344 | 4–4 | 0.0011 | 1–1 |
| C4 | 0.0136 | 2–2 | 0.0476 | 2–2 |
| NIBS Mean | 0.8218 | 1–1 | 0.8208 | 1–1 |
| NIBS Max | 0.9996 | 4–4 | 0.9996 | 3–3 |
| tool_sim | 0.7500 | 1–1 | 0.7500 | 1–1 |

Rank 1 is the lowest tool score. Rank ranges show exact score ties; a tie is not counted as a unique hit.

- cap5, GIBS: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap5, C4: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap17, GIBS: error target 0.0000 = 0 / 10 successful-reference support indicators.
- cap17, C4: error target 0.0000 = 0 / 10 successful-reference support indicators.

Local UI: `#explorer?experiment=cap17&run=0857b47b-432c-478f-8ae8-f059ce8da11c&example=more_refs_help`. Inspect Step scores → Trajectory graph → MCS & targets → Transcript. Switch the active experiment to compare the same execution.

### 5. C4 loses the first error

Task 9 · run `8cbb015d-dfb1-4f15-939b-570332b11463` · seed 7.

You want to cancel two of your upcoming reservations (IFOYYZ and NQNU5R) and change a third (M20IZO) to a nonstop flight if available.

The agent cancels a reservation. The expected action list contains no write action, so the automatic verifier flags this cancellation. Inspect the transcript and policy before treating that label as human-verified truth.

At seed 7, C4 identifies the first labelled tool error with cap 5 but ranks another tool step lower with cap 17. This is an example of regression, not proof of a specific optimization cause.

First labelled tool error: step 9, `cancel_reservation`. Verifier reason: gold actions contain no write; cancel_reservation executed

| Method | 3–5 error score | 3–5 rank | 3–17 error score | 3–17 rank |
|---|---:|---:|---:|---:|
| GIBS | 0.2694 | 4–4 | 0.0270 | 2–2 |
| C4 | 0.0015 | 1–1 | 0.0277 | 3–3 |
| NIBS Mean | 0.8385 | 1–1 | 0.8446 | 1–1 |
| NIBS Max | 0.9833 | 1–1 | 0.9833 | 1–1 |
| tool_sim | 0.0000 | 1–3 | 0.0000 | 1–1 |

Rank 1 is the lowest tool score. Rank ranges show exact score ties; a tie is not counted as a unique hit.

- cap5, GIBS: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap5, C4: error target 0.0000 = 0 / 5 successful-reference support indicators.
- cap17, GIBS: error target 0.0000 = 0 / 11 successful-reference support indicators.
- cap17, C4: error target 0.0000 = 0 / 11 successful-reference support indicators.

Local UI: `#explorer?experiment=cap17&run=8cbb015d-dfb1-4f15-939b-570332b11463&example=c4_regresses`. Inspect Step scores → Trajectory graph → MCS & targets → Transcript. Switch the active experiment to compare the same execution.

## What remains

Human review of the proposed 20–30 failed runs, stakeholder feedback, and missing ACC@80%/ECE remain separate. Phase 3 deployment, monitoring and guardrails are not established by this read-only results UI.

Frozen input SHA256: `7712873512d108a99135c334108c4740bac77bd9721a54e876310dc77ad3a09c`
