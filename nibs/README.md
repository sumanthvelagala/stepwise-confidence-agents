# NIBS scoring and evaluation

The original tool-only NIBS scorer is implemented. The evaluation below measures
how its existing scores relate to rule-derived step labels and prepares independent
human review. No GIBS predictor, training, API access or neural-model installation
is needed.

## Run the evaluation

From the repository root:

```bash
python3 -B nibs/run_evaluation.py
```

Python 3.10+ and its standard library are sufficient. This uses only the five
original milestone tasks (3, 9, 25, 40, 48), with the recorded Groq agent and user
at temperature 0. It excludes infrastructure errors and duplicate content, and
removes the query's entire class from successful references. It does not alter
the legacy scorer or earlier experiment outputs.

Open [the generated report](../results/nibs_evaluation/REPORT.md) for per-task
AUROC, average precision, first-labelled-error top-1/top-3 localization, random
and last-step-first baselines, and limitations. Scores and rankings are in
`per_step.csv` and `localization.csv` beside it. All of these tasks have been
inspected before: the evaluation is retrospective, not a new held-out experiment.
The [protocol](EVALUATION_PROTOCOL.md) specifies eligibility and denominators.

For separate outputs or one milestone task:

```bash
python3 -B nibs/run_evaluation.py --tasks 25 --output /tmp/nibs-task25-evaluation
```

## Finish independent human review

1. Give two reviewers separate copies of
   `results/nibs_evaluation/review/labels.csv`. Both independently inspect every
   agent step in the failed trajectories. Keep generated scores/reports hidden.
2. `context_file` paths are relative to `results/nibs_evaluation/`. Each JSON
   contains task instructions, benchmark gold actions, policy, transcript and a
   mapping from the zero-based agent `step_index` to its raw `message_index` and
   graph `event_id`. These are synthetic benchmark customers.
3. Enter `correct`, `incorrect`, `ambiguous`, or `tool_or_env_error` in the
   appropriate reviewer column. Review the action using information available at
   that point. A later task failure does not make every earlier step incorrect.
   If failure is due to an omitted action, record that in notes rather than
   inventing an executed incorrect step.
4. Combine the two independent columns in the master CSV without changing its
   identity columns. A third reviewer resolves disagreements in
   `adjudicated_label`. Leave unresolved cases blank. Do not fill labels merely
   to make a result look complete.
5. Recompute using the completed sheet:

```bash
python3 -B nibs/run_evaluation.py \
  --human-labels results/nibs_evaluation/review/labels.csv
```

`summary.json` then contains reviewer agreement, Cohen's kappa and separate human
metrics; `human_localization.csv` contains per-run human-target rankings. Only
fully reviewed failed trajectories enter human performance metrics. Disagreements
without adjudication and partially labelled trajectories are reported as incomplete.
Rerunning preserves the sheet; a context manifest prevents reusing reviews after
the source trajectories, task specifications or policy change.

Automatic labels are **not human ground truth**. In particular, NIBS's tool-only
similarity treats all text messages as matching; high message scores cannot
establish that their content is correct. The first labelled incorrect action is
also not necessarily the causal failure point.

## Tests

The new evaluation tests require no third-party packages:

```bash
python3 -B -m unittest nibs.tests.test_evaluation -v
```

The existing NIBS suite uses pytest:

```bash
python3 -B -m pytest nibs/tests -q
```
