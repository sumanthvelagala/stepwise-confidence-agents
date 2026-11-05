# Collection status — October 29, 2026

**Collection completed: 1,000 graded trajectories. Fresh GIBS/C4 comparison is running.**

- Model: ASU-hosted `qwen38-27b`, agent temperature 1, customer temperature 0.
- Corrected pilot: **10 completed**, 8 official benchmark passes, 2 failures,
  zero infrastructure failures. All 10 graphs parse, with zero parallel-call
  turns, reasoning responses or output-limit stops.
- Main collection: **50 Airline tasks × 20 attempts = 1,000 completed trajectories**.
  Official benchmark outcomes: **680 passes, 320 failures (68.0% task pass rate)**.
  All 1,000 trajectories are distinct and graph-compatible; zero unresolved
  infrastructure failures. Thirty reward-success runs have missing-expected-tool
  review flags. These counts do not establish confidence-method accuracy.
  See [collection results](../results/free_asu/main-qwen38-27b-serial-none/COLLECTION_RESULTS.md).
- Main output: `results/free_asu/main-qwen38-27b-serial-none/`.
- Main log: `collection.log` in that directory. Completed data are checkpointed
  to `results.json`; `job_state.json` records the process and terminal status.
  An audit is written automatically when the job finishes or stops.
- No paid model API was used for collection. Fresh DeBERTa/MCS targets now run
  on ASU Sol; GCN training/evaluation follows locally. Sleep prevention runs
  with the follow-up process. Closing the laptop lid or losing the VPN can
  interrupt monitoring/local fitting; it does not cancel the remote GPU job.

From the project root, read actual progress without making model calls:

```bash
python3 run_tau2.py --output results/free_asu/main-qwen38-27b-serial-none --status
```

To resume a stopped main job with the identical configuration:

```bash
python3 -m collection.job --model qwen38-27b --trials 20 --concurrency 4 \
  --output results/free_asu/main-qwen38-27b-serial-none
```

Locks prevent concurrent writers. The collector checkpoints and stops at ten
infrastructure failures; diagnose the error before repeatedly resuming. Native
simulation retries and pre-resume snapshots must be considered when reporting
all attempts, rather than only final graded trajectories.

The corrected pilot is saved separately at
`results/free_asu/pilot-qwen38-27b-serial-none/`, including its audit and final
job status. Earlier engineering runs are retained in other directories and
excluded from the main dataset. See [ASU_RUN_PLAN.md](ASU_RUN_PLAN.md) for the
reasoning-parameter and parallel-call issues discovered and corrected.

One pilot reward-success case (Task 13) lacks the expected escalation tool call.
This remains a review flag, not a relabeled benchmark failure or verified
reference. Official reward does not establish that every step is correct.

**All-task confidence evaluation is in progress.** The current output is
`results/fresh_all_tasks/`; four task-group folds cover all 1,000 trajectories
out of fold (260/260/240/240), with three seeds and 24 total GCN checkpoints.
The expensive target stage runs on Sol; `gibs.fresh.sol_followup` retrieves the
targets and starts local fitting/evaluation. Its live state is
`results/fresh_all_tasks/worker_state.json` and log is `followup.log` there.
The older single-holdout worker is stopped and retained separately under
`results/fresh_comparison/`. The all-task experiment compares against paper
semantic NIBS, tool_sim, random and position baselines.
The prototype reference-bank cap is fixed at five, minimum three distinct
successes, for both methods. There are 860 eligible teacher queries; all 1,000
still receive learned predictions. NIBS reference shortages and undefined
per-task AUROC remain explicit. See [fresh experiment plan](../gibs/fresh/README.md).

On October 29, Sol job `66924222` started on a full A100; CPU/CUDA NLI parity
passed and target creation is executing. The follow-up allows at most eight
four-hour allocations, resuming checkpointed timeouts/preemption. The initial
GPU-slice attempt and aborted migration are recorded separately. The live
worker state, rather than this static note, is authoritative for subsequent jobs.
Baseline-only results are written separately to `baseline_preview/`; they do
not imply fresh trained GIBS/C4 results are complete.

The 905-record checkpoint was preserved after a disk-space error. Resumption
kept 904 graded records, archived the infrastructure-error record, retried it
and completed the missing attempts. The final checkpoint has 1,000 graded records.

The full new-data training and accuracy results are not complete yet. Independent
human validation still needs reviewers; the worker produces the review sheets.
Scenario grouping is automatic and requires review, as do benchmark-successful
reference trajectories. Existing comparison results use historical Groq data.

An already-trained paper-GIBS checkpoint has successfully scored 11 steps of a
new Task 20 trajectory. That is a working inference demonstration, not fresh
retraining or proof of improved accuracy: [executed demo](../results/paper_gibs_working/DEMO.md).
