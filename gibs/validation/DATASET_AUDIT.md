# Dataset audit: existing τ²-bench airline trajectories (independent-validation milestone, Phase 1)

**Audit only.** No NLI was run, no MCS recomputed, no correctness label altered, no trajectory generated, no matching
algorithm changed.

**Reproduce:** `.venv/bin/python -B gibs/validation/dataset_audit.py`, which writes
`results_audit/dataset_audit.json`. Every number below comes from that file or from the read-only checks listed in
§9.

**Evidence tags:**
- **[OBS]**: counted from the trajectory files.
- **[RULE]**: produced by the **existing, unchanged** step rules (`step_verification.py`, written for T48/T9/T25).
  For other tasks these are rule-derived candidates, not verified labels.
- **[HYP]**: a judgement.

## 1. Files and methodology

**Files.** Every `results/**/results.json` is a τ²-bench simulation file: **27 files**.
- `results/gibs_results.json` and `results/nibs_all_tasks.json` are score outputs of earlier work, not
  trajectories. They are excluded.
- No trajectory files exist elsewhere in the repository.

**Counting and deduplication:**
- **Unique trajectory:** a unique simulation UUID. No UUID occurs in more than one file.
- **Valid run:** a run with a reward. 124 runs have no reward; all of them have termination
  `infrastructure_error`.
- **Success:** reward ≥ 0.5. All rewards are exactly 0 or 1.
- **Exact duplicate:** two valid runs whose message sequences are identical, ignoring ids and timestamps. The
  comparison covers roles, message texts, tool-call names and arguments, tool outputs and error flags.
- **Available successful references:** the number of **distinct** successful trajectories of the task, after exact
  deduplication. A successful query under leave-one-out has one fewer.

**Development use.** Taken from the repository's own code and data:
- `run_pilot.py` (T48, T9, T25);
- `pairs.json` (V1–V9: T48, T40, T25, T34, T9, T4, T38);
- `run_nli_probe.py` (T48, T40, T25, T3, T34);
- `gibs/tests` (T48, T25, T40, T4, T9);
- the pilot cost screening (T38, T4).

**Earlier exposure:** T1, T2 and T5 appear in the score files of the earlier NIBS / WL-graph work. They were not
used to develop A or C0–C6.

**Security.** The `info` block of some files holds a credential, flagged earlier: the API key in
`results/probe/task_{2,4,5}`. The audit reads only the agent and user model names and the temperature from `info`,
and writes nothing from it. A search of the audit output for credential markers returned no match.

## 2. Totals [OBS]

| Quantity | Count |
|---|---|
| Trajectory files | 27 |
| Simulation records = unique trajectories (UUIDs) | 470 |
| Tasks (airline task ids 1–49; task 0 absent) | 49 |
| Runs with a reward | 346 |
| Successful | 206 |
| Failed | 140 |
| No reward (infrastructure error) | 124 |
| Other terminations among valid runs | `max_steps` 14, `too_many_errors` 2, `user_stop` 330 |
| Exact duplicates | 21 extra copies of an identical trajectory, all in the T=0 regime (largest: T40 8, T28 5, T48 4) |
| Agent regimes | Groq `gpt-oss-20b`, temperature 0: 406 runs (all tasks). Local `gpt-oss:20b`, temperature 1.0: 64 runs (tasks 2, 4, 5 only) |

Mixed-regime tasks:
- **T2:** temperature 0, 3 runs, all infrastructure errors; temperature 1.0, 3 successes, 16 failures, 1 no-reward.
- **T4:** temperature 0, 1 success, 2 no-reward; temperature 1.0, 18 successes, 6 failures.
- **T5:** temperature 0, 3 runs, all no-reward; temperature 1.0, 14 successes, 2 failures, 4 no-reward.

The pilot (`run_pilot.load_runs`) excluded the temperature-1.0 directories to keep one regime per task.

## 3. Per-task counts and successful references [OBS + RULE]

Columns:
- **"Distinct successful"** = available successful references, after exact deduplication.
- **"Negatives"** = failed-run write steps labelled `incorrect` or `attempted_incorrect` by the existing rules [RULE].
- **"(same-tool)"** = how many of those negatives use a tool that some successful run of the same task executes
  successfully. Only these can test whether a matcher discriminates.

| Task | Regime | Runs (unique) | No reward | Success | Failed | Distinct successful | Exact-dup extra copies | Gold writes | Rule labels: valid / incorrect+attempted / unverified | Negatives (same-tool) | Development use |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | T=0 Groq | 35 | 11 | 22 | 2 | 21 | 1 | — | 62 / 2 / 196 | 2 (0) | prior (earlier NIBS / WL-GIBS scores) |
| 2 | T=0 Groq + T=1 local | 23 | 4 | 3 | 16 | 3 | 0 | — | 64 / 6 / 351 | 6 (0) | prior (earlier NIBS / WL-GIBS scores) |
| 3 | T=0 Groq | 27 | 4 | 12 | 11 | 12 | 0 | — | 41 / 1 / 88 | 1 (0) | **DEV** |
| 4 | T=0 Groq + T=1 local | 27 | 2 | 19 | 6 | 19 | 0 | — | 102 / 7 / 205 | 7 (0) | **DEV** |
| 5 | T=0 Groq + T=1 local | 23 | 7 | 14 | 2 | 14 | 0 | — | 8 / 2 / 118 | 2 (0) | prior (earlier NIBS / WL-GIBS scores) |
| 6 | T=0 Groq | 3 | 3 | 0 | 0 | 0 | 0 | — | 0 / 0 / 0 | 0 (0) |  |
| 7 | T=0 Groq | 3 | 0 | 0 | 3 | 0 | 0 | update_reservation_flights, cancel_reservation×2 | 7 / 3 / 23 | 3 (0) |  |
| 8 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 0 | book_reservation | 4 / 1 / 16 | 1 (0) |  |
| 9 | T=0 Groq | 29 | 8 | 17 | 4 | 17 | 0 | — | 27 / 8 / 144 | 8 (0) | **DEV** |
| 10 | T=0 Groq | 3 | 3 | 0 | 0 | 0 | 0 | — | 0 / 0 / 0 | 0 (0) |  |
| 11 | T=0 Groq | 3 | 0 | 0 | 3 | 0 | 0 | update_reservation_flights | 3 / 0 / 6 | 0 (0) |  |
| 12 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | update_reservation_baggages | 4 / 0 / 7 | 0 (0) |  |
| 13 | T=0 Groq | 3 | 0 | 3 | 0 | 3 | 0 | — | 3 / 0 / 11 | 0 (0) |  |
| 14 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 1 | cancel_reservation, book_reservation | 2 / 0 / 4 | 0 (0) |  |
| 15 | T=0 Groq | 3 | 0 | 3 | 0 | 3 | 0 | update_reservation_flights | 3 / 0 / 31 | 0 (0) |  |
| 16 | T=0 Groq | 3 | 0 | 3 | 0 | 3 | 0 | update_reservation_flights | 3 / 0 / 23 | 0 (0) |  |
| 17 | T=0 Groq | 3 | 2 | 0 | 1 | 0 | 0 | update_reservation_flights, update_reservation_passengers, update_reservation_baggages | 0 / 2 / 8 | 2 (0) |  |
| 18 | T=0 Groq | 3 | 2 | 0 | 1 | 0 | 0 | update_reservation_flights×5 | 1 / 0 / 13 | 0 (0) |  |
| 19 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 0 | cancel_reservation | 2 / 0 / 15 | 0 (0) |  |
| 20 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 0 | book_reservation | 1 / 0 / 15 | 0 (0) |  |
| 21 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 0 | update_reservation_flights, update_reservation_baggages | 0 / 2 / 16 | 2 (0) |  |
| 22 | T=0 Groq | 3 | 2 | 0 | 1 | 0 | 0 | update_reservation_flights, update_reservation_passengers, update_reservation_baggages | 1 / 1 / 10 | 1 (0) |  |
| 23 | T=0 Groq | 3 | 3 | 0 | 0 | 0 | 0 | cancel_reservation, book_reservation×3 | 0 / 0 / 0 | 0 (0) |  |
| 24 | T=0 Groq | 3 | 0 | 0 | 3 | 0 | 0 | book_reservation | 2 / 0 / 18 | 0 (0) |  |
| 25 | T=0 Groq | 26 | 4 | 19 | 3 | 19 | 0 | book_reservation | 20 / 2 / 255 | 2 (1) | **DEV** |
| 26 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | — | 1 / 0 / 4 | 0 (0) |  |
| 27 | T=0 Groq | 3 | 0 | 3 | 0 | 3 | 0 | — | 4 / 0 / 20 | 0 (0) |  |
| 28 | T=0 Groq | 23 | 2 | 21 | 0 | 16 | 5 | — | 21 / 0 / 65 | 0 (0) |  |
| 29 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 0 | cancel_reservation, book_reservation | 3 / 3 / 21 | 3 (0) |  |
| 30 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | update_reservation_flights | 3 / 0 / 5 | 0 (0) |  |
| 31 | T=0 Groq | 3 | 2 | 0 | 1 | 0 | 0 | — | 0 / 1 / 7 | 1 (0) |  |
| 32 | T=0 Groq | 3 | 0 | 0 | 3 | 0 | 0 | update_reservation_flights×2 | 6 / 0 / 10 | 0 (0) |  |
| 33 | T=0 Groq | 3 | 1 | 0 | 2 | 0 | 0 | update_reservation_flights, update_reservation_baggages | 4 / 1 / 25 | 1 (0) |  |
| 34 | T=0 Groq | 28 | 6 | 7 | 15 | 7 | 0 | — | 3 / 20 / 209 | 20 (0) | **DEV** |
| 35 | T=0 Groq | 6 | 5 | 0 | 1 | 0 | 0 | book_reservation | 1 / 1 / 15 | 1 (0) |  |
| 36 | T=0 Groq | 3 | 0 | 3 | 0 | 3 | 0 | — | 7 / 0 / 16 | 0 (0) |  |
| 37 | T=0 Groq | 23 | 1 | 0 | 22 | 0 | 2 | update_reservation_flights | 41 / 6 / 122 | 6 (0) |  |
| 38 | T=0 Groq | 43 | 21 | 17 | 5 | 17 | 0 | — | 49 / 7 / 292 | 7 (0) | **DEV** |
| 39 | T=0 Groq | 3 | 2 | 0 | 1 | 0 | 0 | cancel_reservation×3 | 5 / 0 / 5 | 0 (0) |  |
| 40 | T=0 Groq | 23 | 0 | 20 | 3 | 13 | 8 | update_reservation_passengers | 43 / 1 / 97 | 1 (1) | **DEV** |
| 41 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | — | 7 / 0 / 2 | 0 (0) |  |
| 42 | T=0 Groq | 6 | 3 | 0 | 3 | 0 | 0 | cancel_reservation×2 | 18 / 4 / 14 | 4 (0) |  |
| 43 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | — | 6 / 0 / 3 | 0 (0) |  |
| 44 | T=0 Groq | 3 | 0 | 0 | 3 | 0 | 0 | update_reservation_flights×3 | 28 / 0 / 20 | 0 (0) |  |
| 45 | T=0 Groq | 6 | 6 | 0 | 0 | 0 | 0 | — | 0 / 0 / 0 | 0 (0) |  |
| 46 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | — | 1 / 0 / 3 | 0 (0) |  |
| 47 | T=0 Groq | 3 | 2 | 1 | 0 | 1 | 0 | — | 2 / 0 / 10 | 0 (0) |  |
| 48 | T=0 Groq | 23 | 0 | 10 | 13 | 8 | 4 | — | 33 / 13 / 93 | 13 (0) | **DEV** |
| 49 | T=0 Groq | 3 | 0 | 3 | 0 | 3 | 0 | — | 6 / 0 / 9 | 0 (0) |  |

**Summary of §3:**
- **Tasks with ≥ 5 distinct successful references: 11** (1, 3, 4, 5, 9, 25, 28, 34, 38, 40, 48). **8 of them are
  development tasks.**
- **Tasks with ≥ 5 distinct successful references and ≥ 1 failed run: 10** (all of the above except 28).
- **36 tasks have only 3–6 runs** (the 3-trial probe batches):
  - 23 have **no successful run**, so no references at all; 4 of these (6, 10, 23, 45) have only infrastructure
    errors;
  - 6 have 3 successes and no failures (13, 15, 16, 27, 36, 49);
  - 7 have a single success and no failures (12, 26, 30, 41, 43, 46, 47), which leaves no leave-one-out reference.
- Task 37 (23 runs) has no successful run either.
- **Same-tool negatives in the entire dataset: 2**, both in development tasks:
  - T25 `6f12b024 s30`, the wrong booking;
  - T40 `b4901df6 s10`, a passenger update with the wrong date of birth.

## 4. Tool-call inventory [OBS]

Over valid runs; "ok / error" refers to the tool observation's error flag.

| Tool | Successful runs: ok / error | Failed runs: ok / error | Write |
|---|---|---|---|
| `get_reservation_details` | 320 / 11 | 226 / 0 |  |
| `get_user_details` | 115 / 22 | 108 / 20 |  |
| `search_direct_flight` | 60 / 0 | 138 / 0 |  |
| `transfer_to_human_agents` | 131 / 3 | 54 / 0 |  |
| `get_flight_status` | 43 / 4 | 53 / 3 |  |
| `book_reservation` | 19 / 39 | 5 / 14 | yes |
| `search_onestop_flight` | 14 / 0 | 57 / 2 |  |
| `cancel_reservation` | 0 / 0 | 50 / 0 | yes |
| `update_reservation_passengers` | 20 / 0 | 3 / 1 | yes |
| `update_reservation_flights` | 7 / 0 | 14 / 3 | yes |
| `send_certificate` | 0 / 0 | 15 / 3 | yes |
| `update_reservation_baggages` | 1 / 0 | 9 / 1 | yes |
| `search_direct_flight<|channel|>commentary` | 0 / 0 | 0 / 9 |  |
| `assistant/get_flight_status<|channel|>commentary` | 0 / 0 | 0 / 5 |  |
| `assistant<|channel|>json` | 0 / 0 | 0 / 5 |  |
| `transfer` | 0 / 1 | 0 / 4 |  |
| `send_message` | 0 / 0 | 0 / 5 |  |
| `assistant/get_user_details<|channel|>commentary` | 0 / 0 | 0 / 2 |  |
| `assistant/get_flight_status` | 0 / 0 | 0 / 2 |  |
| `transfer_to_human_agents<|channel|>commentary` | 0 / 1 | 0 / 0 |  |
| `transfer_to_team` | 0 / 1 | 0 / 0 |  |
| `get_flight_number_for_reservation` | 0 / 1 | 0 / 0 |  |
| `assistant/get_user_details` | 0 / 0 | 0 / 1 |  |
| `list` | 0 / 0 | 0 / 1 |  |
| `list_all_airports` | 0 / 0 | 1 / 0 |  |
| `transfer_to_human_agent` | 0 / 0 | 0 / 1 |  |
| `get_user_info<|channel|>commentary` | 0 / 0 | 0 / 1 |  |

**Malformed tool names.** 40 calls use names that include chat-format control tokens, such as
`search_direct_flight<|channel|>commentary` or `assistant<|channel|>json`, or tools that do not exist (`transfer`,
`send_message`, `list`). Almost all of them returned errors, and most are in failed runs. They are agent formatting
failures, not policy errors.

## 5. Failure patterns

**Reward components of the 140 failed runs** [OBS] (`reward_basis` is DB + COMMUNICATE):

| Component that failed | Runs |
|---|---|
| DB | 104 |
| COMMUNICATE | 11 |
| DB + COMMUNICATE | 9 |
| Not recorded (`max_steps` 14, `too_many_errors` 2) | 16 |

**Step-level localisation by the existing rules** [RULE]:
- 75 failed runs contain at least one write labelled `incorrect` or `attempted_incorrect`.
- **65 do not:**
  - **42** are **omissions**: the task requires a write and no successful write was made. There is no wrong step to
    label; the error is a missing step.
  - **23** are tasks without required writes where nothing prohibited was written. The failure lies elsewhere:
    11 `max_steps`, 10 `user_stop` (communication or other), 2 `too_many_errors`.

**Incorrect writes by tool** [RULE]:

| Tool | Development tasks | Other tasks | Has a same-tool successful counterpart |
|---|---|---|---|
| `cancel_reservation` (prohibited) | 34 | 14 | never; no successful run cancels |
| `send_certificate` (prohibited) | 10 + 2 attempted | 5 + 1 attempted | never |
| `update_reservation_baggages` | 3 + 1 attempted | 6 | never |
| `update_reservation_flights` | 5 + 1 attempted | 3 | never |
| `book_reservation` | **1** (T25) | 4 + 1 attempted | **only T25** |
| `update_reservation_passengers` | **1** (T40) + 1 attempted | 1 | **only T40** |

**Wrong-argument writes outside development exist but have no references.** The tool is a gold write of the task,
but the arguments conflict:
- T8, T29 and T35 bookings;
- T17, T21, T22 and T33 baggage or passenger updates;
- T7 and T42 cancellations (see the rule limitation below).

**Every one of these tasks has 0 successful runs**, so no consensus can be computed for them.

**Rule limitation found during the audit (labels not changed).** For a write, `classify_steps` compares the
arguments only with the **first** gold action of the same tool.
- In tasks with several gold writes of one tool (7, 18, 23, 32, 39, 42, 44), a write equal to a later gold action is
  labelled `incorrect`.
- This produces **5 spurious `incorrect` labels**: T42 3, T7 2. Each equals another gold write on the checked call
  fields.
- **No development task is affected**: T48 and T9 have no gold writes, and T25 has one booking.
- The rule must be fixed, with a pre-registered change, before it is used to label any held-out task with repeated
  gold writes.

## 6. Task-level success vs step-level correctness

**Task success is a final-state criterion.** The reward is DB match (+ COMMUNICATE). It says the end state is right,
not that every step was right or necessary. For example:
- the successful T9 run `7cd3469e` announces a transfer it never made;
- 21 exact duplicates inflate apparent agreement.

**Independently verified step labels exist only where gold actions or a policy text pin a step down** [RULE]:

| Label | In successful runs | In failed runs |
|---|---|---|
| valid | 380 | 272 |
| incorrect | 0 | 87 |
| attempted_incorrect | 0 | 7 |
| unverified | 1,403 | 1,237 |

So **78% of steps are unverified** (2,640 of 3,386). Messages are never labelled, except the policy transfer message.

**Consistency checks:**
- 0 successful runs contain a rule-`incorrect` step.
- 65 of 140 failed runs (46%) contain no rule-detectable incorrect step (§5).

Both quantities are needed separately in any evaluation:
- **run reward** answers "did the run end correctly?";
- **step labels** answer "was this step correct?", for a small subset of steps.

Consensus scores should be evaluated against step labels, never against run reward.

## 7. Candidate held-out tasks (not used to develop A or C0–C6)

| Task | Regime | Distinct successful refs | Failed | Rule negatives (same-tool) | Rule-valid steps (successful / failed runs) | Prior exposure | What it can test |
|---|---|---|---|---|---|---|---|
| **28** | T=0 | 16 (21 runs, 5 duplicates) | 0 | 0 | 21 / 0 | none | **valid-step coverage and reference-count stability only** (no failed runs) |
| **1** | T=0 | 21 | 2 | 2 (0): prohibited cancellations | 60 / 2 | earlier NIBS / WL scores | coverage, stability, **structural** negatives only |
| **5** | **T=1.0** | 14 | 2 | 2 (0): `send_certificate` | 6 / 2 | earlier WL scores | coverage under a **different agent regime**; structural negatives |
| 2 | T=1.0 | 3 | 16 | 6 (0) | 5 / 59 | earlier WL scores | low-reference stress test (2 LOO references) |
| 13, 15, 16, 27, 36, 49 | T=0 | 3 each | 0 | 0 | 3–7 each | none | sanity only (2 LOO references; pilot §10: deviation ≈ 0.13 at k = 2) |
| 37 | T=0 | **0** | 22 | 6 (0) | — | none | none for consensus (no references) |

**Not usable for consensus** (no successful run):
- 7, 8, 11, 14, 17–22, 24, 29, 31–33, 35, 37, 39, 42, 44;
- 6, 10, 23, 45 (infrastructure errors only);
- 12, 26, 30, 41, 43, 46, 47 (one success, no failures: no leave-one-out reference).

## 8. Can the existing data support an independent evaluation, and later a GCN?

**Independent evaluation of valid-step coverage and stability: yes, at small scale.**
- T28, T1 and T5 give 51 distinct successful references (16 + 21 + 14), and 87 rule-valid steps in successful
  runs.
- They provide a genuine hold-out for coverage, leave-one-out stability and the reference-count curve.
- T5 adds a regime shift.

**Independent evaluation of discrimination (valid vs incorrect steps): no.**
- Outside the development tasks there are **0 same-tool negatives**.
- The 4 rule negatives in T1 and T5 (10 with T2) are prohibited writes whose tool never appears in a successful run.
  Any matcher that distinguishes tool names scores them 0, so an AUROC on them is uninformative, as in the pilot.
- The only discriminative negatives in the whole dataset (T25, T40) are development cases.
- Wrong-argument negatives exist only in tasks with no successful runs.

**GCN prototype: engineering-feasible, not evaluable.**
- **Training data.** Consensus masks, the training signal of PDF Eq. 6, can be computed for the 11 tasks with ≥ 5
  distinct references: 242 valid runs. 8 of the 11 tasks are development tasks.
- **Not evaluable.** Nothing in the held-out data can show that a trained GCN localises incorrect steps, because
  there are no discriminative negatives and messages are unlabelled.
- **Overfitting risk [HYP].** With fewer than 20 distinct successful runs per task and 3 usable held-out tasks, a GCN
  would mostly memorise task-specific paths.

**What would be needed** (not done; for your decision):
1. Successful references for tasks whose failures include **wrong-argument writes**: T8, T17, T21, T22, T29, T33,
   T35, T7, T42. This needs more trials of the same regime.
2. More trials for the 3-run tasks with successes.
3. A pre-registered fix of the repeated-gold-write rule (§5).
4. Independent labels for a sample of messages.

## 9. Proposed held-out split (for review; nothing has been run on it)

| Split | Tasks | Purpose |
|---|---|---|
| **Development** (frozen; already used) | 3, 4, 9, 25, 34, 38, 40, 48 | method development only; not reported as held-out evidence |
| **Held-out A: coverage and stability** | **28, 1** (T=0) | pre-registered evaluation of valid-step coverage, leave-one-out stability, reference-count curves. Structural negatives in T1 reported separately, not as discrimination evidence |
| **Held-out B: regime shift** | **5** (T=1.0); optionally 2 as a low-reference stress test | do the conclusions transfer to a different agent regime? |
| **Sanity** | 13, 15, 16, 27, 36, 49 | small-reference behaviour only |
| **Reserved for future discrimination tests** | 7, 8, 17, 21, 22, 29, 33, 35, 42 (+37) | require new successful trajectories first; their wrong-argument writes are the missing discriminative negatives |

**Before any held-out computation:**
- pre-register metrics and expectations;
- **freeze the method** (C5 or C6, as you decide);
- do not adjust anything on held-out results.

## 10. Limitations

- **Labels for non-development tasks** are produced by rules written for T48/T9/T25. They are candidates, and one
  defect is already known (§5).
- **Exact deduplication only.** Near-duplicates (paraphrases, identical tool sequences) are not removed, and
  T=0 runs are highly similar.
- **Task 0 is absent.** Most tasks have only 3 runs; regime coverage is uneven.
- **Development and exposure use is reconstructed** from repository code and data. Informal inspection during the
  initial repository audit (which looked at all files) cannot be ruled out, so "held-out" means "not used to design
  or tune A/C0–C6".

## 11. Files

- **New:**
  - `gibs/validation/dataset_audit.py`;
  - `gibs/validation/results_audit/dataset_audit.json`, which holds per-task counts, regimes, the tool inventory,
    rule-label counts and every rule negative with its reason;
  - this report.
- **Nothing else was modified.** Existing results, labels and code are unchanged.

Stopped for review before selecting evaluation tasks.
