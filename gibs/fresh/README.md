# Fresh paper GIBS / C4 comparison

**Completed:** both sets of 860 targets, 24 trained checkpoints and held-out
predictions for all 1,000 trajectories. See [the report](../../results/fresh_all_tasks/REPORT.md)
and [the local UI](../../demo_ui/README.md). Human review remains pending.

The corrected ASU collection is complete: 50 tasks, 20 attempts each, 1,000
distinct graded trajectories. The current experiment in `results/fresh_all_tasks/`
uses four held-out task-group folds so every trajectory receives an out-of-fold
prediction. Historical Groq MCS masks are never used as targets for new Qwen runs.

## Method and fixed prototype choices

- Paper GIBS: real `microsoft/deberta-large-mnli`, pinned revision
  `7296194b9009373def4f7c5dad292651e4b5cf4e`, author single-string encoding,
  maximum bidirectional entailment, node/edge thresholds 0.7, the existing
  single-component MCS heuristic, and averaged node-membership targets.
- C4: the same successful reference bank, structured-field checks, symmetric
  truncation, multi-component MCS and context-supported targets. This is the
  project's adaptation, separately named.
- Predictors: frozen BERT CLS features, two GCN layers (128 hidden, dropout .1),
  Adam .001, final PDF Eq. 6 entropy + lambda=1 soft BCE. Explicit agent graph
  and fusion choices remain those disclosed in `gibs/learned/EVALUATION_PLAN.md`.
- Three seeds 7/17/27, maximum 150 epochs, validation-loss early stopping.
- Prototype reference bank: deterministic **up to 5 distinct successful
  references**, excluding the query's whole duplicate class; minimum 3.
  This cap was selected from local compute measurements before fresh accuracy
  evaluation. `--max-references 0` uses all eligible successes in a new experiment.
  This is not the paper's complete scale or original math/QA benchmark.
- Paper semantic NIBS Cos-Max/Mean, original tool_sim, random expectation and
  last-step-first are compared on exactly the same eligible test steps.

## Data isolation and evaluation

Preparation requires the completed 1,000-record collection unless the operator
explicitly requests a separate partial prototype with `--allow-partial`.
It freezes a sanitized snapshot, hashes, deduplication and task definitions.
Missing-reward and unbuildable trajectories are reported rather than hidden.

Task groups share user/reservation identifiers or identical scenario text.
The four test folds contain 260, 260, 240 and 240 trajectories; each task group
is held out exactly once per seed. This automatic grouping is not human
certification that every semantically similar scenario has been grouped.
Within fitting tasks, reserve about 20% per task/outcome stratum for validation.
All targets use successful **training-partition** references only. Task-local
reference banks remain fixed across folds where the task participates in fitting;
the code verifies this against each fold's actual training partition.
Held-out task graphs and references never enter fitting or early stopping.

There are 860 eligible teacher queries and 140 without three successful training
references. The latter do not provide supervised targets but still receive learned
out-of-fold predictions. Two methods, four folds and three seeds produce 24
checkpoints. Each of the 1,000 trajectories is scored once per method and seed.

NIBS receives benchmark-successful, same-task references during evaluation.
Learned inference receives only the query graph, without gold actions, outcome
or references. Test cases without enough NIBS references are excluded from the
common comparison but still receive saved learned predictions and coverage flags.
Always-fail tasks are not assigned invented NIBS scores.

Official reward is a reference-selection proxy, not step-level truth. Task 13
has already demonstrated a reward loophole. Reference-quality audits and
independent human labels are necessary before strong reliability claims.
The primary automatic metrics use the disclosed v2 verifier; unknown steps
are excluded from binary metrics, not silently counted as correct.

## Execution

The active target stage runs on a full NVIDIA A100 GPU on ASU Sol, using a fresh
CUDA cache. CPU/CUDA smoke checks pass for pinned DeBERTa inference; TF32 is
disabled and scores use FP32. Runtime versions and hardware are recorded in
`sol_runtime*.json`. Historical Mac teacher masks are kept separate.
The read-only Sol environment uses Torch 2.11.0 and Transformers 4.57.6;
local training uses Torch 2.5.1 and Transformers 4.51.3. This is a disclosed
cross-platform method implementation, not an exact original-environment reproduction.

`gibs.fresh.sol_followup` monitors the owned GPU job, retrieves teachers/pair
mappings, then trains and evaluates locally. It resumes timed-out/preempted jobs
within its explicit job-count bound. Other failures stop for inspection. The Mac
must remain awake and connected for follow-up and local fitting; the remote GPU
job can continue if the local monitor loses connectivity. Read live state in
`results/fresh_all_tasks/worker_state.json` and `followup.log`.

Manual preparation and subsequent local fitting use the same frozen output:

```bash
.venv/bin/python -m gibs.fresh.experiment prepare --crossfit --max-references 5 --output results/fresh_all_tasks
# On Sol, submit collection/sol_gibs_targets.sbatch for the target stage.
# After retrieving completed targets:
.venv/bin/python -m gibs.fresh.experiment train --output results/fresh_all_tasks
```

Use the same argument/output configuration when resuming. Pair-level results,
query targets and NLI scores are cached. The target stage can resume interrupted
work; changing the frozen data or teacher reference set is rejected.

Outputs in `results/fresh_all_tasks/` include `worker_state.json`, `plan.json`,
`input_audit.json`, `teacher_exclusions.json`, real pair mappings, fresh masks,
trained checkpoints, histories, per-step predictions, baseline metrics,
`REPORT.md`, and a blind two-reviewer sheet. Human validation is not automated
or claimed completed. Reports contain undefined metrics when labels lack both
classes rather than inventing an accuracy value.

## Checks actually performed

- A trained historical paper-GIBS checkpoint scored a new Task 20 trajectory,
  with reward/gold removed, producing 11 finite per-step scores.
- Fresh NLI/MCS was executed on a real new query/reference pair for both methods.
- Integration tests exercised training, evaluation, checkpoint reload and report
output using explicitly identified historical benchmark fixtures. That test
  is not misrepresented as fresh ASU training.
- Split/teacher tests reject cross-partition references, wrong query identities,
  invalid masks and accidental partial-data training.

The older single-holdout attempt in `results/fresh_comparison/` is stopped and
retained separately; its test partition covered 240 trajectories. It is not the
current all-task experiment. The optional `gibs.fresh.baseline_preview` command
computes reference baselines early under `baseline_preview/`; that preview
contains no fresh trained GIBS/C4 results.

See `results/paper_gibs_working/` for historical inference demo artifacts. The
fresh completed experiment is `results/fresh_all_tasks/`; its worker records
`completed`. Automatic-label results do not establish human-validated accuracy.
