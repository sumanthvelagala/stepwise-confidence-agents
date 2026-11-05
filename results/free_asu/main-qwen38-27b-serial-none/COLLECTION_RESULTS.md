# Completed ASU trajectory collection

**1,000 graded trajectories: 680 official benchmark passes and 320 failures (68.0% pass rate).**

This is the generating airline agent’s task pass rate. It is not NIBS/GIBS/C4 error-detection accuracy.
Customers and the airline database are simulated benchmark data.

- All 50 Airline tasks have exactly 20 saved task/trial/seed combinations.
- Distinct task/content classes: 1000.
- Graph-parser failures: 0.
- Reward-success runs missing expected tool names: 30; review flags, not relabelled failures.
- Model: `qwen38-27b` through ASU’s no-charge API.
- Agent temperature 1, customer temperature 0; reasoning and parallel calls disabled.
- Failed infrastructure attempts remain in pre-resume snapshots; native internal retries are not a complete API-request ledger.
- Official reward does not verify every step. Reference review and independent labels remain necessary.

| Task | Graded | Pass | Fail | Distinct successful classes |
|---|---|---|---|---|
| 0 | 20 | 20 | 0 | 20 |
| 1 | 20 | 5 | 15 | 5 |
| 2 | 20 | 13 | 7 | 13 |
| 3 | 20 | 20 | 0 | 20 |
| 4 | 20 | 20 | 0 | 20 |
| 5 | 20 | 18 | 2 | 18 |
| 6 | 20 | 20 | 0 | 20 |
| 7 | 20 | 0 | 20 | 0 |
| 8 | 20 | 19 | 1 | 19 |
| 9 | 20 | 14 | 6 | 14 |
| 10 | 20 | 19 | 1 | 19 |
| 11 | 20 | 13 | 7 | 13 |
| 12 | 20 | 13 | 7 | 13 |
| 13 | 20 | 20 | 0 | 20 |
| 14 | 20 | 2 | 18 | 2 |
| 15 | 20 | 13 | 7 | 13 |
| 16 | 20 | 11 | 9 | 11 |
| 17 | 20 | 5 | 15 | 5 |
| 18 | 20 | 16 | 4 | 16 |
| 19 | 20 | 18 | 2 | 18 |
| 20 | 20 | 3 | 17 | 3 |
| 21 | 20 | 3 | 17 | 3 |
| 22 | 20 | 10 | 10 | 10 |
| 23 | 20 | 13 | 7 | 13 |
| 24 | 20 | 8 | 12 | 8 |
| 25 | 20 | 20 | 0 | 20 |
| 26 | 20 | 20 | 0 | 20 |
| 27 | 20 | 19 | 1 | 19 |
| 28 | 20 | 19 | 1 | 19 |
| 29 | 20 | 2 | 18 | 2 |
| 30 | 20 | 19 | 1 | 19 |
| 31 | 20 | 20 | 0 | 20 |
| 32 | 20 | 3 | 17 | 3 |
| 33 | 20 | 12 | 8 | 12 |
| 34 | 20 | 20 | 0 | 20 |
| 35 | 20 | 9 | 11 | 9 |
| 36 | 20 | 20 | 0 | 20 |
| 37 | 20 | 12 | 8 | 12 |
| 38 | 20 | 18 | 2 | 18 |
| 39 | 20 | 5 | 15 | 5 |
| 40 | 20 | 16 | 4 | 16 |
| 41 | 20 | 11 | 9 | 11 |
| 42 | 20 | 11 | 9 | 11 |
| 43 | 20 | 16 | 4 | 16 |
| 44 | 20 | 2 | 18 | 2 |
| 45 | 20 | 20 | 0 | 20 |
| 46 | 20 | 19 | 1 | 19 |
| 47 | 20 | 12 | 8 | 12 |
| 48 | 20 | 19 | 1 | 19 |
| 49 | 20 | 20 | 0 | 20 |

The separate fresh comparison worker computes new paper/C4 MCS targets, trains the graph predictors,
and evaluates them against NIBS and simple baselines. The all-task out-of-fold results belong in `results/fresh_all_tasks/`.
Do not substitute the agent pass rate above for confidence-method accuracy.

Input SHA256: `110767b28c353d0f8ee0c39bade66d116e55347291f66dca1fb18e66343073ec`
