# Paper NIBS, paper GIBS, and your C4

This is the unified prototype requested for the milestone: paper semantic NIBS,
the PDF's learned GIBS formulation, and the project's C4 variant, with recorded
agent data and an explicit baseline evaluation. Original implementations and
earlier results are preserved.

## Run everything

The workspace `.venv` already has the dependencies. From the repository root:

```bash
.venv/bin/python -m gibs.comparison.run
```

For a fresh environment, use `gibs/requirements-learned-lock.txt` as described in
`gibs/learned/README.md`. BERT is downloaded once; frozen embeddings and pinned
author source files are cached under `~/.cache/stepwise_gibs/`.

Open [REPORT.md](../../results/paper_comparison/REPORT.md) after the run. Outputs
include per-step scores, metrics, checkpoints, histories, graph examples and
input/source/split/reference hashes. [EVALUATION_PLAN.md](EVALUATION_PLAN.md)
records the methods and partitions before this comparison ran.

## What the three names mean

| Requested method | Actual implementation |
|---|---|
| **Paper NIBS** | PDF Eq. 2 with frozen BERT cosine similarity on operation texts. Max/mean within each successful run, then an equal average across references. No predictor training. |
| **Paper GIBS** | PDF Eq. 6 and Appendix C.2: train a BERT-feature/two-layer-GCN predictor on MCS node-consensus targets from successful references. |
| **Your C4** | Train the same GCN on C4's structured-field-aware, context-supported targets. Original C4 is kept unchanged. |

The older `tool_sim` NIBS is also evaluated, but is explicitly labelled as an
agent baseline. It is **not** called the paper's semantic implementation.
Only cosine NIBS variants are executed here; the paper's NLI variants are not
silently substituted or claimed as executed.

## Paper versus released code: important distinctions

The methods are applied to a necessary agent-data adapter: tool operations and
results replace reasoning operations/results; user turns supply context. We do
not claim to reproduce the paper's math/QA data or its published benchmark scores.

The PDF specifies a two-layer GCN. The active `GIB_MCS_wo_mcs_feature.py` forward
in the release uses node/edge MLPs and mean pooling. We therefore run both:

- `paper_gibs_pdf`: follows the PDF's stated GCN architecture and Eq. 6;
- `released_gibs_control`: reimplements the active released forward and balanced
  per-reference edge-mask loss, including skipping empty edge matches.

The control uses the common split and successful+failed training mixture to
make the comparison controlled. It does not reproduce the release's failed-only
training loop, >15-node supervision shortcut, or all unused parameters.
It must not be described as an exact end-to-end replication of the release.

Likewise, the released NIBS cosine code applies `1/(1 + cosine_distance)` after
within-reference reduction. We retain these as separate controls instead of
calling that transformation raw cosine from Eq. 2. Released controls retain
reference edge multiplicity; primary Eq. 2 NIBS counts agent steps once.

The source-check command verifies the selected numerical equations against the
authors' actual pinned code, using the same weights and test features:

```bash
.venv/bin/python -m gibs.comparison.verify_sources
```

It downloads/hash-checks four files at commit `1ccc8b8`, then executes only
selected definitions in a minimal namespace, without importing upstream training
scripts or loading upstream models. See
[source_verification.json](../../results/paper_comparison/source_verification.json).
The check is also part of the main comparison command.

## Different examples and graph structure

The original three-task study still uses tasks 9, 25 and 48 with task-held-out
test folds. A separate experiment trains only on those tasks and tests on
**tasks 3 and 40**, which were not used to fit those models. They are previously
inspected project tasks, not untouched holdouts. Task 3 lacks automatic labels
for executed errors, so its AUROC is undefined rather than assumed perfect.

We keep C4 and add **C4-state-graph** as a separate predictor-input ablation:

1. When an argument value occurs in several earlier events, connect it to the
   latest non-error tool observation containing it. Fall back to the original
   earliest provenance if no such tool observation exists.
2. Connect each agent message to the most recent user turn and tool observation.
3. Retain all events, operation/result texts, agent step IDs, and forward-only
   dependency edges.

This makes state refreshes and tool-result-to-message relationships explicit.
It is a heuristic, not an assertion that the latest observation caused the
decision. C4 matching targets remain the original stored targets; the experiment
isolates **predictor adjacency**, not a new MCS target-generation method.

Both successes and failures from tasks 3/25/40/48 are exported as Mermaid diagrams
and graph JSON under `results/paper_comparison/graphs/`. Case selection uses task,
outcome and smallest UUID, not whether a method scores well. All graph variants
are reported; no test-result-based winner is silently selected.

## Score one trajectory

Paper NIBS (successful references are read from the recorded dataset):

```bash
.venv/bin/python -m gibs.comparison.predict \
  --method paper_nibs_cos_max \
  --results results/probe/new_batch1/results.json --run-id 6f12b024 \
  --output results/paper_comparison/task25_paper_nibs.json
```

Paper GIBS trained without task 25:

```bash
.venv/bin/python -m gibs.comparison.predict \
  --method paper_gibs_pdf \
  --checkpoint results/paper_comparison/checkpoints/core_oof_paper_gibs_pdf_25_seed7.pt \
  --results results/probe/new_batch1/results.json --run-id 6f12b024 \
  --output results/paper_comparison/task25_paper_gibs.json
```

C4 on the same query:

```bash
.venv/bin/python -m gibs.comparison.predict \
  --method c4_gibs \
  --checkpoint results/paper_comparison/checkpoints/core_oof_c4_gibs_25_seed7.pt \
  --results results/probe/new_batch1/results.json --run-id 6f12b024 \
  --output results/paper_comparison/task25_c4.json
```

Each output has one score per agent step. Query rewards, gold actions and labels
are excluded from features. Learned methods need no successful references during
prediction; NIBS does. That difference is disclosed in the evaluation.

## Evaluation limits and next action

The code provides a working prototype and a baseline comparison, not a guarantee
of higher accuracy. Labels are currently rule-derived and sparse; many errors
are easy absent-tool cases. The additional-task executed-error evidence is only
one Task 40 action. Use the prepared independent-review sheet and workflow in
`nibs/README.md` before making human-validated failure-localization claims.

```bash
.venv/bin/python -m pytest gibs/tests -q
.venv/bin/python -m pytest nibs/tests -q
```
