# NIBS retrospective evaluation

This evaluates the existing tool-only NIBS implementation on the five original
milestone tasks: **3, 9, 25, 40, 48**. These tasks have already been inspected and
used during development. This is a retrospective diagnostic, not an untouched
test set or evidence of generalization. The protocol is written before executing
the new evaluation; it does not retrospectively preregister prior work.

## Data and scoring

- Read recorded `results/**/results.json`; do not generate simulations or call APIs.
- Restrict agent and user to `groq/openai/gpt-oss-20b`, temperature 0.0, with
  the recorded benchmark commit and policy identical within each task.
- Exclude missing rewards (infrastructure errors). Remove repeated simulation IDs
  and exact-content duplicate trajectories. Conflicting duplicate outcomes or
  task specifications are errors, not silently resolved.
- Use one representative per content class, the smallest UUID. References are
  successful classes of the same task, excluding the query's entire class.
- Require **3 references after leave-one-out for each query**. This follows the
  original requirements. The old `score_task` checks the count before leave-one-out;
  it is left unchanged. Every exclusion and denominator is reported.
- Reuse `parse_simulation`, `score_run`, and `tool_sim` unchanged, with max
  aggregation. Match against all agent steps in each reference, as in the pilot.
- Index agent steps from zero; preserve the separate graph event ID and raw
  message index. Assert parser/verifier alignment before assigning labels.
- Export every scored agent step, including messages. `tool_sim` treats any two
  messages as identical, so message scores do not measure semantic correctness.

## Automatic labels and metrics

Use existing verifier v2, which compares selected fields with benchmark gold
actions and does not read run reward. Its labels are rule-derived candidates,
**not independent human ground truth**. Unverified steps are never presumed correct.
The scorer never receives gold actions, labels or reward except reference selection.

- Correct = `valid`; error = `incorrect` (executed write). Report
  `attempted_incorrect` and `unverified` separately; exclude both from binary metrics.
- Report metrics separately for **all agent steps** and **tool calls only**.
- Error-positive AUROC uses `1 - confidence`; ties count one half. Undefined when
  either class is absent. AUCPR is reported as grouped-threshold average precision.
- Report low-confidence (<0.5) error detection and correct-step false alarms.
  The cutoff is descriptive, not calibrated or tuned here.
- In failed queries with an explicit error label, rank **all** candidate steps in
  the scope, including unverified steps, by ascending confidence. Target the first
  verifier-labelled incorrect step. This is a proxy, not causal/true first-error
  localization. Report top-1, top-3, expected rank and mean reciprocal rank.
- Resolve score ties by uniform random ordering within the tie: report exact
  expected metrics, rather than favoring the earliest step. Export rank bounds.
- Baselines: exact expectation of independent continuous uniform random scoring,
  and last-step-first ranking (confidence decreases linearly from 1 to 0 over the
  candidate positions within each trajectory/scope; singleton confidence is 0).
  Random top-k is min(k,n)/n for one target, and
  random expected reciprocal rank is H_n/n. AUROC expectation is 0.5.
- Aggregate AUROC within task (macro and positive-negative-pair weighted); do not
  present a cross-task pooled AUROC as an independent test. Report localization
  denominator, failed queries without a labelled error, label coverage and
  same-tool versus structurally absent-tool errors.
- The milestone's AUROC >0.6 on three tasks and localization above random are
  checked descriptively. Sparse/easy negatives cannot establish general efficacy.

## Human review

Export all steps of eligible failed queries, with task instructions, policy and
sanitized conversation context. The review sheet hides scores and automatic
labels. Two reviewers independently enter `correct`, `incorrect`, `ambiguous`, or
`tool_or_env_error`. A third reviewer adjudicates disagreements. Do not fabricate
human labels or treat this model as a human reviewer.

`--human-labels` validates the sheet against the current dataset identities.
Human localization is computed only for fully reviewed trajectories (all agent
steps resolved), and only if at least one step is labelled incorrect. Ambiguous
and environment-error steps remain ranking candidates but are excluded from binary
correctness metrics. Partial reviews are reported, not represented as complete.
Report reviewer agreement and Cohen's kappa. Existing review entries are never
overwritten by rerunning the evaluation.

## Outputs and reproducibility

Run `python3 -B nibs/run_evaluation.py`. Standard library only; no model downloads,
training or provider credentials. Outputs are isolated in `results/nibs_evaluation/`:
`summary.json`, `per_step.csv`, `localization.csv`, `REPORT.md`, `review/labels.csv`,
and per-run review context. The manifest records selected-file hashes, method-code
hashes, reference IDs and excluded runs. No raw provider metadata is exported.
Existing NIBS/GIBS results and implementations remain unchanged.
