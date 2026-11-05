# Trained GIBS prototype for tool-using agents

For the newer unified **paper semantic NIBS / PDF GIBS / C4** comparison,
additional task cases and graph ablation, use [`gibs/comparison/`](../comparison/README.md).
This guide preserves the initial three-task learned-predictor experiment.

This adds the learned predictor missing from the earlier graph-consensus pipeline.
It uses the supplied research paper's core framework: MCS consensus supervision,
frozen BERT features, a two-layer graph convolutional network, and the final
entropy-plus-cross-entropy training objective (equation 6).

**It is a paper-inspired agent adaptation, not an exact reproduction of the
paper's experiments or released training script.** Read the comparison below
before describing it in a milestone submission.

## What was run

- Real recorded tau2-bench Airline tasks **9, 25 and 48**, 62 distinct trajectories,
  573 agent steps, with infrastructure failures and exact duplicates excluded.
- Frozen BERT-base CLS features, pinned model revision; two GCN layers with
  hidden size 128 and dropout 0.1. Only the 270,977 predictor parameters train.
- Three task-held-out folds and three initialization seeds (7, 17, 27).
- Two models: **paper_style**, trained on A node-consensus masks; and
  **agent_adapted**, trained on the project's C4 context-supported masks.
- 18 trained checkpoints in total, all reloaded and verified against their test
  predictions. No test task is used in optimization or early stopping.
- Comparisons against NIBS, direct A/C4 consensus, random ranking and
  last-step-first on exactly the same test queries.

See [the generated results report](../../results/gibs_learned/REPORT.md) and
[the evaluation plan](EVALUATION_PLAN.md). Both learned models underperform the tool_sim NIBS baseline
on the available rule-labelled steps. That is an experimental result, not a
reason to change the split or tune on test labels. Human validation remains pending.

## Run training and evaluation

An isolated `.venv` is already installed in this workspace. From the repository root:

```bash
.venv/bin/python -m gibs.learned.run_experiment
```

For a new checkout, create the environment and install the recorded dependency
versions first (skip venv creation if the environment already exists):

```bash
uv venv .venv --python python3.12
uv pip install --python .venv/bin/python -r gibs/requirements-learned-lock.txt
.venv/bin/python -m gibs.learned.run_experiment
```

BERT is downloaded on first use; its frozen text features are cached in
`~/.cache/stepwise_gibs/`. BERT extraction uses MPS when available; GCN training
uses CPU with two threads for repeatability. `--feature-device cpu` is supported.
Stored real DeBERTa/MCS results from the repository supply training targets, so
this command does not rerun NLI, generate new trajectories, or use paid APIs.
For a fresh dataset, the matching stage must first produce equivalent pair mappings.

The lightweight direct dependencies are in `gibs/requirements-learned.txt`;
the lock file records the full installed environment. The historical
`gibs/requirements-mcs.txt` describes a different NLI environment and is not the
installation command for this prototype.

## Score one recorded trajectory

This example uses the checkpoint whose held-out task was 25. It takes a raw
recorded conversation and outputs one score per agent tool call or message:

```bash
.venv/bin/python -m gibs.learned.run_experiment predict \
  --checkpoint results/gibs_learned/checkpoints/paper_style_heldout25_seed7.pt \
  --results results/probe/new_batch1/results.json \
  --run-id 6f12b024 \
  --output results/gibs_learned/task25_prediction.json
```

The prediction path uses only the selected trajectory's messages. It does not
read gold actions, rewards, correctness labels, or successful references into
the model. A file containing only `simulations` with `id`, `task_id` and `messages`
is sufficient. The output includes zero-based agent step indices, graph event
IDs and scores. The score is a learned mask inclusion value, not an established
calibrated correctness probability.

The feature cache is keyed by text, BERT revision, pooling and token limit.
Checkpoint loading verifies the BERT feature specification. Keep the pinned
feature encoder and trained checkpoint together.

## Same framework, explicit differences

| Component | Research paper | Agent prototype |
|---|---|---|
| Objective | Diagnose reasoning errors | Diagnose tool-use/dialogue errors |
| Data | GSM8K, Math, MoreHopQA | tau2-bench Airline trajectories |
| Graph | Results linked by reasoning operations | Tool results/messages linked through value provenance |
| Features | BERT step embeddings | Same pretrained BERT family, frozen CLS features |
| Predictor | Two-layer GCN and feature fusion | Two-layer GCN plus an explicit operation/context fusion MLP |
| Targets, paper_style | MCS node-consensus masks | Existing A m_node masks, recomputed over allowed reference IDs |
| Targets, agent_adapted | Not in paper | C4 m_ctx with exact field checks and matching fixes |
| Loss | Eq. 6 entropy + lambda CE | Same final objective, fixed lambda=1 |
| Training size | 2,000 graphs | 30–33 training graphs per fold |
| Validation | Validation-loss early stopping | Same criterion; task-held-out tests and class-separated validation |
| Evaluation labels | LLM judgments, additional human-labelled benchmark | Rule verifier only; independent human review outstanding |

Additional choices are disclosed rather than called exact replication:

- A node may have several incoming operation edges. They carry the same event
  operation text; the predictor emits one score per agent event rather than
  duplicating that event for every incoming edge.
- Directed GCN normalization includes self-loops. Mean graph context and operation
  features are fused with the node representation. The paper does not specify
  every fusion detail.
- The PDF's sparse-prior KL expression (equation 5) and its final entropy loss
  (equation 6) are different. This implementation follows **equation 6**.
- The active predictor in the authors' released `GIB_MCS_wo_mcs_feature.py` uses
  MLPs/mean pooling and does not call its declared GCN. We follow the PDF's
  stated GCN architecture, not that script's inactive components.

The source comparison was made against the supplied PDF and the
[author repository at commit 1ccc8b8](https://github.com/Xiao0o0o/stepwise-confidence-attribution/tree/1ccc8b8).

## What the results can establish

This is a working trainable prototype with real data, saved weights, standalone
inference and a baseline evaluation. It is not evidence that GIBS improves agent
debugging generally: all three tasks were previously inspected, most steps lack
labels, and only one wrong-argument example is available here. Baselines also
receive successful references at evaluation while the learned predictor does not.

Use the existing independent-review workflow in `nibs/README.md` to strengthen
ground truth. More training graphs and independently labelled errors are needed
before making claims comparable to the research paper.

## Tests

```bash
.venv/bin/python -m pytest gibs/tests -q
.venv/bin/python -m pytest nibs/tests -q
```

The learned-model tests check GCN normalization/graph dependence, equation-6 loss
and extreme logits, task/reference separation, lack of reward/gold feature
leakage, real data alignment, deterministic training and checkpoint reloads.
