# Phase 3A: difficult-negative dataset plan (planning only)

**Status: a plan.**
- No trajectory was generated, no NLI or MCS was run, and no method, verifier, threshold or earlier result was
  changed.
- All figures come from the existing 66+ trajectories, the task specifications in the results files, and
  `DATASET_AUDIT.md`.
- Where a number is a forecast, it is marked **[EST]**.

**Goal.** Obtain **independently verifiable difficult negatives**: successful write calls labelled `incorrect` by the
verifier (v2) whose **tool** is also executed and labelled `valid` in successful reference runs of the same task.
This is the definition in EVALUATION_PROTOCOL §7.6. The target is about 20 such steps from at least 4 tasks, each
task with at least 5 distinct successful references, so that C4's ability to separate correct from incorrect tool
actions can be tested.

## 1. Candidate review (Tasks 7, 8, 17, 21, 22, 29, 33, 35, 37, 42)

**Sources:**
- gold actions, NL assertions and user instructions from the task specifications;
- the existing runs, labelled by verifier v2.

"Natural negatives observed" means existing failed-run write steps that v2 labels `incorrect` **and** that use a
tool in the task's gold writes. These are difficult once successful references exist.

| Task | Expected correct writes (gold) | Natural same-tool incorrect writes already observed | Realistic incorrect substitutions (pattern) | Verifiable by gold args + DB? | Existing runs (valid / infra) | Why 0 successes so far |
|---|---|---|---|---|---|---|
| **42** | `cancel_reservation(FDZ0T5)`, `cancel_reservation(HSR97W)` | `cancel(SE9KEL)` in `69591e6d` (wrong reservation) | cancelling another of the user's same-day reservations; cancelling one but not the other (omission) | **yes**: gold IDs and DB status | 3 / 3 | all 3 cancel HSR97W correctly; 2 omit FDZ0T5, 1 adds SE9KEL. Partial competence; infrastructure 50% |
| **17** | update FQ8APE: flights to economy (gift card), passenger → Omar Rossi, baggages 3 (0 non-free) | baggages and passengers updated on **UM3OG5** (wrong reservation), non-free 3 vs 0 | wrong reservation (the user has another NY→Chicago trip); wrong free/non-free bag split; wrong payment method | **yes** | 1 / 2 | the single valid run picked the wrong reservation; infrastructure 67% |
| **22** | same three writes as T17 (same scenario, different user behaviour) | baggages total 5, non-free 3, credit card (should be 3 / 0 / gift card) | wrong bag counts or fees; wrong payment method | **yes** | 1 / 2 | passenger update correct, baggages wrong, flights omitted; infrastructure 67% |
| **21** | update OBUT9V return flights (fastest same-day), baggages 2 (0 non-free, smallest gift card) | baggages on **AQLBTL** (wrong reservation), ×2 runs | wrong reservation; wrong flight selection (not fastest); wrong gift card | **yes** for reservation and bags; flight choice via gold flights | 2 / 1 | requires itinerary optimisation; both runs updated the wrong reservation |
| **7** | upgrade XEHM4B to business (CC 2135), cancel XEHM4B, cancel 59XX6W; communicate $1,628 | `update_reservation_flights` on **59XX6W** with other flights | wrong reservation upgraded; cancelling before upgrading | **yes**; COMMUNICATE also needed for success | 3 / 0 | mid-conversation intent change; COMMUNICATE failed in all 3 |
| 29 | cancel VA5SGQ, book DTW↔JFK round trip HAT169 / HAT033 with one bag | `book_reservation` with a different payment amount (312 vs 282) | wrong fare or bag fee; wrong flights (not the cheapest early economy) | **yes** | 2 / 1 | multi-constraint search; one run used an update (not allowed) instead of cancel + book |
| 33 | update HXDUBJ flights (HAT072 / HAT278), baggages 2 with 0 non-free | baggages non-free 2 vs 0 | charging for bags that should be free; one-leg business change (policy) | **yes** | 2 / 1 | flights updated correctly in 1 run, bags charged |
| 8 | book ORD→PHL HAT271 May 26, 2 passengers, 0 bags, one certificate | `book_reservation` with total bags 2 vs 0 | wrong bags; wrong passenger set; wrong payment (certificate) | **yes** | 2 / 1 | price-conditional passenger logic; errored attempts |
| 35 | book JFK→SFO second-cheapest economy (HAT069 + HAT258), $290 on a credit card; **no** cancellation | `book_reservation` of **HAT023** (the cheapest, not second cheapest) | cheapest instead of second cheapest; prohibited cancellation under pressure | **yes** | 1 / **5** | infrastructure 83% (special-token tool names) |
| 37 | upgrade M20IZO to business; **no** cancellations | only prohibited `cancel_reservation` (structural; no gold cancel). The update is often **valid** | prohibited cancellation (structural, not difficult) | **yes** | 22 / 1 | 22 / 22 fail: 17 omit the upgrade (one of them also cancels), 6 make a prohibited cancellation (5 of these upgrade correctly). Near-deterministic at T = 0 |

**Policy dimension.** Several incorrect writes are not only "wrong argument" but policy violations:
- T33: bag fees under the free-bag allowance;
- T37: cancellation not allowed;
- T35: cancellation under pressure.

The verifier labels them from gold actions (argument conflicts or a write absent from the gold). It does **not**
interpret policy text, so policy-sensitive cases go to adjudication (§6).

## 2. Why successful references are zero for these tasks

| Cause | Evidence | Tasks most affected |
|---|---|---|
| **Infrastructure** | 0-message runs with no reward. The README documents Groq rejecting tool names containing `<|channel|>` tokens, and the 250k-tokens-per-minute limit (sequential runs required) | T35 5 / 6, T17 2 / 3, T22 2 / 3, T42 3 / 6 |
| **Agent capability / task difficulty** | multi-write tasks with optimisation (fastest or second-cheapest flight), entity disambiguation (which of several reservations), mid-dialogue intent changes; gpt-oss-20b fails at least one required write | all |
| **Deterministic regime** | agent temperature 0. Repeated trials fail the same way: T37 22 / 22, including an exact-duplicate class of 3 runs | T37 strongly; probably all |
| **Tiny samples** | only 3 trials per task in the probe batches (1–3 valid) | all except T37 |
| **Policy constraints** | tasks that reward *not* acting (T35, T37) are failed by agents that comply with user pressure | T35, T37 |

[HYP] More temperature-0 trials are unlikely to produce successes for T37, and probably not for the others either.
Sampling diversity (agent temperature 1.0, as in T2, T4 and T5) is the cheapest lever. T5 showed that temperature-1.0
successes exist but are diverse (Phase 2B §8).

## 3. Natural vs counterfactual failures

| Stream | Definition | Use |
|---|---|---|
| **Natural** (primary) | an incorrect write produced by the agent in a real τ²-bench simulation | the only stream counted toward the ~20 target and the headline metrics |
| **Counterfactual** (optional, separate) | a successful run in which **one** valid write's arguments are replaced by a pre-specified substitution (§5.4), with the observation recomputed by replaying the modified call against the τ²-bench environment at that state | a controlled supplement, **always reported separately and labelled "constructed"**. It is never pooled with natural negatives for headline metrics and never described as agent-generated |

Counterfactuals test only the matcher's sensitivity to the substituted fields. Their dialogue does not reflect what
an agent would say after the wrong action, which is a known validity limit.

## 4. Task-level split (entities and failure patterns)

**Overlap with development tasks** (shared users or reservations; computed from the specifications):
- **T8** shares user `sophia_silva_7557` and reservation **WUNA5K** with T4 (development).
- **T33** shares `yara_garcia_1905` and **HXDUBJ** with T34 (development).
- **T35 and T37** share `aarav_ahmed_6699` with T9 (development), and T37 also IFOYYZ, M20IZO and NQNU5R.
- **T17 and T22** are the same scenario family (FQ8APE).
- T7, T21, T29 and T42 share no entities with development tasks.

**Failure patterns:**

| Code | Pattern | Development examples | Candidates |
|---|---|---|---|
| P1 | entity confusion (write on the wrong reservation) | — | T42, T17, T21, T7 |
| P2 | quantity or fee error (bags, non-free bags) | — | T22, T17, T33, T8 |
| P3 | selection or optimisation error (wrong flight) | **T25** | T35, T29, T21 |
| P4 | payment amount or method error | **T25** | T29, T22 |
| P5 | passenger-data error | **T40** | — |

**Proposed split:**

| Split | Tasks | Rationale |
|---|---|---|
| **Final evaluation (held out)** | **T42, T17 + T22 (one family), T21, T7** | entity-disjoint from development. Patterns **P1 and P2** never appear in development tasks. 4 families / 5 tasks |
| **Phase-3 development** (pipeline, adjudication rehearsal, counterfactual tooling) | T25, T40 (existing difficult negatives), **T29, T35, T8, T33, T37** | development patterns P3 / P4 / P5 (T25, T40, T29, T35), or entity overlap with development tasks (T8, T33, T35, T37) |

**Rules:**
- A task, scenario family or failure pattern in the final split is never used to inspect scores, debug code or
  rehearse adjudication before the frozen final run.
- **Disclosure:** existing T7 and T42 runs were used in the verifier-v2 regression tests. That is label-rule
  exposure, not matcher exposure. Final evaluation uses **newly collected** runs only.

## 5. Collection plan (proposal; requires approval and key hygiene)

### 5.1 Regime

- Agent and user: `groq/openai/gpt-oss-20b`, **agent temperature 1.0**, `--max-concurrency 1`, the same τ²-bench
  version as existing runs.
- One regime per task: all queries and references of a task come from the same new collection.
- Old temperature-0 runs of these tasks are not mixed in; they are kept only as audit context.
- **Fallback, if Groq yields no successes:** the local `gpt-oss:20b` endpoint (temperature 1.0), only after the
  exposed API key in `results/probe/task_{2,4,5}` has been **rotated**.

### 5.2 Stages and estimated run counts

**Stage 0: feasibility probe.** 10 trials per task:
- final split: T42, T17, T22, T21, T7;
- development split (pipeline only): T35, T29.

That is **70 runs**. [EST] At about 10–25 s per valid run plus infrastructure retries, sequentially, roughly 0.5–1
hour.

**Stage 1: targeted collection.** For each final-split task that passes Stage 0, continue in blocks of 10 trials until
both of the following hold, with a **hard cap of 60 trials per task**:
- **≥ 5 distinct successful content classes**;
- **≥ 5 natural difficult negatives**, counted from labels only.

**Stage 1 run counts [EST], depending on the Stage-0 success rate p:**

| p | Runs per task to reach 5 successes | Runs for 4 tasks |
|---|---|---|
| 0.30 | about 17 | about 70 |
| 0.15 | about 35 | about 140 |
| < 0.08 | cap of 60 likely hit | — |

Upper bound: **300 runs** (5 tasks × 60). Generation time [EST]: 1.5–4 hours.

**Natural difficult-negative yield [EST]:** existing failed runs of the final-split tasks produced 0.3–2 same-tool
incorrect writes per valid failed run. Reaching about 20 across 4 families needs roughly 15–40 failed runs in
total, which Stage 1 provides if successes exist.

### 5.3 Successful references and deduplication

- **References:** successful runs (reward = 1) of the same task and collection.
- **Duplicates:** exact-content deduplication (`dedup.py`), smallest UUID as class representative. A query never uses
  its own class.
- **Minimum:** ≥ 5 distinct successful classes per task before the task can enter the final analysis.
- **Diversity check:** near-duplicates (paraphrases) are kept, but reported as the distinct-tool-sequence count and
  the identical-message rate (Phase 2B §6.6).

### 5.4 Counterfactual stream (optional, Phase-3 development first)

**Fixed substitution rules** (written now, before any scores exist), applied to **one** valid write in a successful
run:

| Pattern | Substitution |
|---|---|
| P1 | the reservation ID replaced by another reservation of the same user, in user-details order |
| P2 | `total_baggages` ± 1; or `nonfree_baggages` set to `total_baggages` |
| P3 | a flight replaced by the next listed same-route flight from the run's own search results |
| P4 | `payment_id` replaced by another payment method of the user |

**Procedure:**
- the observation is recomputed by replaying the modified call in the τ²-bench environment at that state;
- the rest of the dialogue is unchanged, and that is flagged as a validity limit;
- substitution choice is deterministic: first eligible write, first eligible alternative.

**Requirements:** a replay tool that has not been written yet (tooling risk). Constructed runs are stored separately,
with a `constructed: true` manifest field.

### 5.5 Cost

| Item | Estimate |
|---|---|
| **Generation** | the recorded `agent_cost` of existing Groq runs is 0 (free tier). The binding constraint is the rate limit and infrastructure errors (§2) |
| **Consensus computation, later Phase 3C** [EST] | Phase 2B took 30 min for T1 (T = 0, 462 pairs) and 85 min for T5 (T = 1.0, 210 pairs, uncached). Final split: about 5 tasks × (≈ 30 classes × ≈ 8 references ≈ 240 pairs) at T5-like speed ≈ **5–8 hours** of NLI on MPS, one process |
| **Labelling and adjudication** | about 2–4 person-hours per 100 incorrect or ambiguous writes |

### 5.6 Safeguards against score-based selection

1. **Freeze before any NLI or MCS.** A dataset manifest (UUIDs, content hashes, source file hashes, v2 labels,
   adjudicated labels, label version) is frozen and hashed.
2. **Label-only rules.** Inclusion, stopping (§5.2) and negative counting use only reward, termination, v2 labels,
   adjudication and deduplication. No C4, C5 or C6 score is computed on any final-split task before the freeze.
3. **No discarding.** Every collected run is kept. Infrastructure-error runs are excluded by rule (no reward).
4. **No regeneration** of a task after its scores have been seen.
5. **Frozen code.** Analysis code is fingerprinted, and metric definitions are fixed (§7) before computation.
6. **Blind review.** Reviewers adjudicate without access to scores.
7. **Fixed counterfactual rules** (§5.4); they are not tuned after any score is seen.

## 6. Independent step-label verification and adjudication

1. **Automatic labels:** verifier v2 (gold-action matching with one-to-one consumption; run-level DB consistency as a
   diagnostic). Errored writes stay `unverified`.
2. **Queued for human adjudication:**
   - every v2-`incorrect` write;
   - every v2-`valid` write in a failed run;
   - every errored write;
   - any write whose arguments match the gold on `CALL_FIELDS` but differ on unchecked fields (e.g. prices, seat
     counts);
   - every run with `db_consistency` = inconsistent.
3. **Two annotators.** Each labels the queue independently as correct / incorrect / ambiguous, using the task
   instruction, the policy text, gold actions and the DB result, blind to consensus scores. Agreement is reported as
   Cohen's κ.
4. **Adjudication.** Disagreements and "ambiguous" go to a third reviewer. Final categories:
   - **verified-correct**;
   - **verified-incorrect** (difficult if the tool appears `valid` in a successful reference);
   - **excluded-ambiguous** (reported, not scored).
5. **Policy-sensitive cases** (free bag allowance, cancellation eligibility, insurance waivers) need the relevant
   policy clause cited in the adjudication note.
6. **Freeze.** The labels are frozen into the manifest before §5.6 step 1.

## 7. Metrics for Phase 3C (defined now)

Unit: content class; per task; then pooled with **task-cluster bootstrap** CIs (1,000 resamples; seed fixed in the
Phase-3C protocol). The decision threshold τ = 0.5 is pre-registered (as in the pilot), and full score distributions
are reported. Primary score: C4 `m_ctx`, with `m_node` secondary.

| Metric | Definition |
|---|---|
| **False negative (missed detection)** | a verified difficult negative with score ≥ 0.5. Reported as the FN rate and as the list of cases, with the reference step each was mapped to |
| **False positive (false alarm)** | a verified-correct write of the same tools with score < 0.5. Split into **ceiling-limited** (`cap` < 0.5, reference frequency) vs **matching failures** (mechanisms b–d, as in Phase 2B §6.3) |
| **Discrimination** | task-stratified AUROC (ties ½) for difficult negatives vs same-tool verified-correct writes. Computed only if ≥ 20 natural difficult negatives from ≥ 4 tasks |
| **Error-localisation rank** | for each failed run with ≥ 1 verified-incorrect write: rank all agent steps (and, separately, tool steps) by ascending score, with ties at expected rank. Report the rank of the **first** verified-incorrect step: top-1 and top-3 accuracy, and mean reciprocal rank |
| **Localisation baselines** | random order; "last write first"; "first write first" |
| **Reference-count dependence** | all of the above for k ∈ {1, 2, 3, 5, 8, all}, using Phase 2B's deterministic subset scheme (`sha256("phase3c|task|query|k")`, all combinations if ≤ 50, else 50) |
| **Stream separation** | natural and counterfactual are reported in separate tables. Final and development splits are never pooled |

## 8. Prioritised shortlist

| Priority | Task | Split | Pattern | Strength | Main risk |
|---|---|---|---|---|---|
| 1 | **42** | final | P1 (wrong-reservation cancel) | partial competence: all valid runs cancel one correct reservation; clean gold; DB-verifiable | infrastructure 50%; success may stay rare |
| 2 | **22** | final (family A) | P2 / P4 | one of three writes already correct; clear fee and payment errors | infrastructure 67% |
| 3 | **17** | final (family A) | P1 / P2 | wrong-reservation and fee errors observed | infrastructure 67%; same family as T22, counted as one unit for the split |
| 4 | **21** | final | P1 (+ P3) | wrong-reservation writes in 2 / 2 runs | success requires flight optimisation; may be very rare |
| 5 | **7** | final | P1 | wrong-reservation update observed; no infrastructure errors | success also requires COMMUNICATE ($1,628) and intent switching |
| — | 29, 35 | development | P3 / P4 | natural difficult-negative types; useful for pipeline rehearsal | pattern overlap with T25 |
| — | 8, 33, 37 | development | P2 / structural | — | entity overlap with T4 / T34 / T9; T37's negatives are structural |

## 9. Feasibility risks

- **No successes at temperature 1.0 either.** This would end the natural-negative route for that task. Mitigation:
  the counterfactual stream (development first), or the local model fallback after key rotation.
- **Regime shift:** temperature-1.0 diversity lowers exact agreement (T5: 9% of tool steps had an exact
  counterpart). Valid writes may then fail to match for diversity reasons. This must be separated as ceiling- or
  diversity-limited false positives.
- **Infrastructure errors:** high in several candidates. Budget for the excess trials.
- **Gold-action ambiguity:**
  - T21 ("next fastest if unavailable") and T29 ("cheapest within constraints") may admit several defensible
    answers;
  - v2 compares only `CALL_FIELDS` (e.g. not prices).
  - Both go to adjudication.
- **Small number of task families (4).** Task-cluster bootstrap CIs will be wide; claims must stay per-task and
  descriptive if CIs span chance.
- **Pattern concentration:** most final-split negatives are expected to be P1 (wrong reservation). Results may not
  generalise to other error types.
- **Security:** the exposed key must be rotated before any use of the local endpoint. Groq credentials live in
  `tau2-bench/.env`, outside this repository, and must not be committed.

## 10. Go / no-go criteria

| Gate | Go if | Otherwise |
|---|---|---|
| **G0: start Stage 0** | plan approved; τ²-bench version recorded; key hygiene confirmed | wait |
| **G1: per task after Stage 0** (10 trials) | ≥ 2 successful runs **and** ≥ 1 natural same-tool incorrect write (label-based) **and** ≥ 5 valid runs (infrastructure ≤ 50%) | drop the task from the final split (no retries with altered settings for that task) |
| **G2: proceed to Stage 1** | ≥ 4 final-split tasks (≥ 3 families) pass G1 | report infeasibility; decide between the counterfactual stream, the fallback model, or stopping |
| **G3: freeze the dataset** | per task: ≥ 5 distinct successful classes. In total: **≥ 20 natural difficult negatives from ≥ 4 tasks**, adjudicated, with κ reported | 10–19: Phase 3C is **descriptive only** (per-case FN analysis and localisation ranks, no AUROC). Below 10: no discrimination evaluation |
| **G4: run Phase 3C** | manifest hash and code fingerprints recorded; Phase-3C protocol pre-registered | — |

## 11. Not done (by instruction)

No trajectories generated, no NLI or MCS, no change to C4, C5, C6, the verifier, thresholds or earlier results, and
no GCN.

Stopped for review.
