# NIBS retrospective evaluation

**Status: automatic-label diagnostic. Independent human review is pending unless explicitly reported below.**

The original tool-only NIBS implementation was evaluated without training or model/API calls. The selected milestone tasks were already exposed during development; these are not independent test results.

## Main findings

- NIBS macro AUROC: 1.000 on 4 tasks with both automatic labels. This excludes unverified steps.
- 20 incorrect actions use tools absent from every successful reference. These are easier than wrong-argument errors.
- Inspect the same-tool cases below: high scores can miss wrong arguments even when labelled-subset AUROC is perfect.
- Tool-only localization top-1: NIBS 0.803, last-step-first 0.833. Compare both before claiming a benefit over simple baselines.

## Dataset and references

| Task | Runs (success / failed) | Content classes | Successful classes | Scored queries |
|---|---|---|---|---|
| 3 | 23 (12 / 11) | 23 | 12 | 23 |
| 9 | 21 (17 / 4) | 21 | 17 | 21 |
| 25 | 22 (19 / 3) | 22 | 19 | 22 |
| 40 | 23 (20 / 3) | 15 | 13 | 15 |
| 48 | 23 (10 / 13) | 19 | 8 | 19 |

Exclusions before scoring: `{'infrastructure_error': 16}`. Queries excluded for insufficient references: 0.
References are distinct successful trajectories of the same task, with the query's entire content class removed. Each scored query has at least 3 references. Each content class contributes once.

## Rule-label coverage

All scored agent steps: **796**. Label counts: `{'unverified': 630, 'correct': 143, 'attempted_incorrect': 1, 'incorrect': 22}`.

Only `valid` and `incorrect` enter binary metrics. Attempted errors and unverified steps are excluded. Unverified steps still compete in localization rankings. Labels compare selected fields with gold actions, not human reasoning judgments; they share field definitions with the structured matcher and do not prove causality.

## All agent steps

AUROC is error-positive (low confidence = error). AP uses grouped thresholds. Top-k targets the first verifier-labelled executed incorrect action in a failed run.

| Task | Correct / incorrect | NIBS AUROC | Random AUROC | Last-first AUROC | NIBS AP | Eligible failed runs / total | NIBS top-1 / top-3 | Random top-1 / top-3 | Last-first top-1 / top-3 |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 41 / 0 | — | — | — | — | 0 / 11 | — / — | — / — | — / — |
| 9 | 27 / 8 | 1.000 | 0.500 | 0.269 | 1.000 | 4 / 4 | 0.487 / 0.838 | 0.083 / 0.250 | 0.000 / 0.500 |
| 25 | 20 / 2 | 1.000 | 0.500 | 0.950 | 1.000 | 2 / 3 | 0.500 / 1.000 | 0.052 / 0.156 | 0.000 / 1.000 |
| 40 | 28 / 1 | 1.000 | 0.500 | 0.964 | 1.000 | 1 / 2 | 1.000 / 1.000 | 0.143 / 0.429 | 0.000 / 1.000 |
| 48 | 27 / 11 | 1.000 | 0.500 | 0.704 | 1.000 | 11 / 11 | 0.955 / 1.000 | 0.159 / 0.476 | 0.000 / 0.818 |

| Method | Tasks with both labels | Macro AUROC | Within-task pair-weighted AUROC | Localization runs | Top-1 | Top-3 | MRR |
|---|---|---|---|---|---|---|---|
| nibs | 4 | 1.000 | 1.000 | 18 | 0.803 | 0.964 | 0.878 |
| random_expected | 4 | 0.500 | 0.500 | 18 | 0.129 | 0.388 | 0.338 |
| last_step_first | 4 | 0.722 | 0.571 | 18 | 0.000 | 0.778 | 0.409 |

Ties use exact expected rank/top-k under uniform tie-breaking; random is its analytical expectation, not a selected seed. A high AUROC on tools absent from successful references is weak evidence of subtle error detection.

## Tool calls

AUROC is error-positive (low confidence = error). AP uses grouped thresholds. Top-k targets the first verifier-labelled executed incorrect action in a failed run.

| Task | Correct / incorrect | NIBS AUROC | Random AUROC | Last-first AUROC | NIBS AP | Eligible failed runs / total | NIBS top-1 / top-3 | Random top-1 / top-3 | Last-first top-1 / top-3 |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 30 / 0 | — | — | — | — | 0 / 11 | — / — | — / — | — / — |
| 9 | 13 / 8 | 1.000 | 0.500 | 0.558 | 1.000 | 4 / 4 | 0.487 / 0.838 | 0.127 / 0.380 | 0.250 / 0.500 |
| 25 | 19 / 2 | 1.000 | 0.500 | 0.500 | 1.000 | 2 / 3 | 0.500 / 1.000 | 0.110 / 0.330 | 1.000 / 1.000 |
| 40 | 27 / 1 | 1.000 | 0.500 | 0.759 | 1.000 | 1 / 2 | 1.000 / 1.000 | 0.500 / 1.000 | 1.000 / 1.000 |
| 48 | 19 / 11 | 1.000 | 0.500 | 1.000 | 1.000 | 11 / 11 | 0.955 / 1.000 | 0.470 / 1.000 | 1.000 / 1.000 |

| Method | Tasks with both labels | Macro AUROC | Within-task pair-weighted AUROC | Localization runs | Top-1 | Top-3 | MRR |
|---|---|---|---|---|---|---|---|
| nibs | 4 | 1.000 | 1.000 | 18 | 0.803 | 0.964 | 0.878 |
| random_expected | 4 | 0.500 | 0.500 | 18 | 0.355 | 0.788 | 0.593 |
| last_step_first | 4 | 0.704 | 0.811 | 18 | 0.833 | 0.889 | 0.878 |

Ties use exact expected rank/top-k under uniform tie-breaking; random is its analytical expectation, not a selected seed. A high AUROC on tools absent from successful references is weak evidence of subtle error detection.

## Trajectory score gap

These are mean scores per trajectory (all agent steps), then averaged within outcome. They do not measure step correctness. A missing outcome group produces no gap.

| Task | Mean successful | Mean failed | Gap |
|---|---|---|---|
| 3 | 0.868 | 0.888 | -0.020 |
| 9 | 0.707 | 0.622 | 0.084 |
| 25 | 0.915 | 0.812 | 0.103 |
| 40 | 1.000 | 0.864 | 0.136 |
| 48 | 0.787 | 0.821 | -0.034 |

## Difficult errors and milestone checks

Executed incorrect steps using a tool that is valid in a successful reference: **2**. Incorrect steps whose tool is absent from all successful references: **20**. Other incorrect steps: **0**.

The following are the subtle same-tool cases. A score below 0.5 is a flag; exactly 0.5 is not.

| Task | Run | Step (zero-based) / event | Tool | NIBS confidence | Flagged at <0.5? |
|---|---|---|---|---|---|
| 25 | 6f12b024 | 15 / s30 | book_reservation | 0.904 | no |
| 40 | b4901df6 | 5 / s10 | update_reservation_passengers | 0.500 | no |

A threshold failure and a ranking success can coexist: a wrong step can score below every labelled-correct step yet still have high absolute confidence. Unverified steps may rank below it, lowering localization accuracy.

All-agent AUROC >0.6 on 4 tasks; the milestone target of at least three tasks is **met numerically**. This is a descriptive check with sparse rule labels, not statistical validation.

All-agent top-1 exceeds random expectation: **True**. Top-3 exceeds random expectation: **True**.

## Human review

`review/labels.csv` contains every agent step in eligible failed queries. Context files provide task instructions, policy, transcript and step-to-message mapping. Scores and automatic labels are hidden. Give reviewers separate copies, then combine their columns in the master sheet. Enter independent labels in reviewer_1 and reviewer_2; adjudicate disagreements in adjudicated_label. Allowed values: correct, incorrect, ambiguous, tool_or_env_error. Existing entries are preserved on rerun.

After review: `python3 -B nibs/run_evaluation.py --human-labels results/nibs_evaluation/review/labels.csv`.

## Limits and next action

- Task exposure, few difficult negatives, and incomplete labels prevent a general failure-localization claim.
- NIBS tool_sim scores any two plain-text messages as 1, regardless of meaning. High message scores are not evidence of correctness.
- A low score can reflect an uncommon valid path. It is not a calibrated probability of error.
- First labelled incorrect action can differ from the true first error or causal failure. Omitted actions have no step to rank.
- Finish independent review before interpreting these numbers as human-validated results. More diagnostic data may still be necessary.
- Full GIBS training is outside this NIBS evaluation.

## Reproduce

```bash
python3 -B nibs/run_evaluation.py
```

See nibs/EVALUATION_PROTOCOL.md. summary.json records file/code hashes, reference IDs, exclusions and metrics. The original scorer and historical experiment files are unchanged.
