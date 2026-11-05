# Learned GIBS prototype on tau2-bench Airline

**A trained, paper-inspired agent adaptation; retrospective automatic-label evaluation. Human validation is pending.**

## What ran

- 62 distinct real benchmark trajectories, 573 agent steps, tasks 9/25/48.
- Frozen BERT CLS features (google-bert/bert-base-uncased, revision 86b5e0934494bd15c9632b12f734a8a67f723594, 256 tokens).
- A two-layer GCN (128 hidden units, dropout 0.1), operation encoder and graph/step fusion MLP.
- Actual Adam training of the predictor with equation 6: entropy + soft cross-entropy to MCS consensus masks.
- Three leave-one-task-out folds, seeds [7, 17, 27]; validation loss selects checkpoints. BERT is not fine-tuned.
- All test-task graphs excluded from optimization, training pseudo-target references, validation targets and early stopping.
- Saved real DeBERTa+MCS pair mappings reused; NLI/MCS were not recomputed in this experiment.

## Is this the same as the paper?

**The core framework is the same. The task representation and experiment are adaptations, so this is not an exact reproduction.**

| Aspect | Paper | This prototype |
|---|---|---|
| Data | GSM8K, Math, MoreHopQA reasoning | Recorded multi-turn Airline tool-use trajectories |
| Step | Operation/result reasoning pair | Tool call/result or agent message; user turns supply context |
| Dependencies | Structured reasoning generation | Deterministic value provenance from recorded events |
| Features/network | BERT + two-layer GCN, hidden 128, dropout 0.1 | Same stated components; explicit mean graph context and fusion MLP |
| Primary teacher | MCS consensus node masks | Existing paper-style A, m_node; no structured checks |
| Adapted teacher | Not in paper | C4 m_ctx, structured field checks, symmetric truncation, multiple components |
| Objective | Final Eq. 6 entropy + lambda CE | Eq. 6 with lambda=1; not a sparse-prior KL implementation |
| Training scale | 2,000 graphs | Tens of training graphs per fold |
| Evaluation labels | LLM judge (plus paper human benchmark experiments) | Existing narrow rule-based verifier; human review pending |
| Inference | Trained predictor, query graph | Query-only inference, without gold labels/references |

The released author script's active wo_mcs_feature forward path uses MLPs/mean pooling rather than its declared GCN. We follow the paper's stated GCN architecture, not that script bit-for-bit. The exact fusion, event-level prediction and lambda are disclosed implementation choices. The paper's Eq. 5 KL and Eq. 6 entropy objectives differ; Eq. 6 is used.

## Evaluation against baselines

Learned results are mean +/- population standard deviation across seeds, without ensembling. Each seed's scores are out-of-fold: the model scoring a task never trained on that task. These tasks were previously inspected during method development, so this is not an untouched test.

### all agent steps

| Method | Macro AUROC | First-labelled-error top-1 | Top-3 | MRR |
|---|---|---|---|---|
| gibs_paper_style | 0.715 +/- 0.018 | 0.275 +/- 0.154 | 0.706 +/- 0.173 | 0.524 +/- 0.120 |
| gibs_agent_adapted | 0.765 +/- 0.049 | 0.098 +/- 0.100 | 0.745 +/- 0.100 | 0.430 +/- 0.084 |
| nibs | 1.000 | 0.791 | 0.962 | 0.871 |
| consensus_A | 0.987 | 0.278 | 0.746 | 0.524 |
| consensus_C4 | 0.992 | 0.273 | 0.761 | 0.529 |
| random_expected | 0.500 | 0.128 | 0.385 | 0.336 |
| last_step_first | 0.641 | 0.000 | 0.765 | 0.403 |

### tool calls

| Method | Macro AUROC | First-labelled-error top-1 | Top-3 | MRR |
|---|---|---|---|---|
| gibs_paper_style | 0.550 +/- 0.038 | 0.686 +/- 0.055 | 0.863 +/- 0.055 | 0.791 +/- 0.036 |
| gibs_agent_adapted | 0.628 +/- 0.101 | 0.725 +/- 0.073 | 0.902 +/- 0.028 | 0.826 +/- 0.052 |
| nibs | 1.000 | 0.791 | 0.962 | 0.871 |
| consensus_A | 1.000 | 0.742 | 0.874 | 0.830 |
| consensus_C4 | 1.000 | 0.767 | 0.947 | 0.858 |
| random_expected | 0.500 | 0.347 | 0.775 | 0.584 |
| last_step_first | 0.686 | 0.824 | 0.882 | 0.871 |

### Per-task learned AUROC (mean +/- std over seeds)

| Method | Task 9 | Task 25 | Task 48 |
|---|---|---|---|
| gibs_paper_style | 0.562 +/- 0.058 | 0.583 +/- 0.012 | 1.000 +/- 0.000 |
| gibs_agent_adapted | 0.636 +/- 0.166 | 0.658 +/- 0.118 | 1.000 +/- 0.000 |

The complete per-seed/per-task average precision, detection/false-alarm rates and localization denominators are in summary.json. per_step.csv preserves every prediction and seed.

## Limits and interpretation

- Baselines NIBS/A/C4 have known-successful same-task references at evaluation; learned inference has only its query. This is an explicit difference in inference resources.
- Labels cover selected gold reads/writes and a fixed transfer message. Unknown steps are not assumed correct. Localization targets the first verifier-labelled executed incorrect step, not proven causal failure.
- Binary labels: {'unverified': 478, 'valid': 74, 'incorrect': 21}. Most steps lack correctness labels.
- Almost all incorrect steps use a tool absent from successful runs. Only one difficult wrong-booking example exists in this three-task evaluation.
- The available number of graphs is far below the paper's training scale. Three seeds describe training variability, not statistical confidence intervals.
- C4's messages remain exploratory. A good consensus fit does not establish calibrated correctness probabilities.
- Both GCN layers can use the complete recorded trajectory. This prototype is an offline diagnostic, not a causal online monitor.
- Compare with direct consensus as well as NIBS: learning can lose useful reference information or generalize poorly. No improvement is assumed.

## Training and acceptance checks

BERT unique texts: 406; texts truncated at 256 tokens: 43.
Trained models: 18. Every best checkpoint reloads with identical test predictions, weights change, and scores are finite in [0,1].

| Method | Held-out task | Seed | Train / validation / test graphs | Best epoch | Validation loss |
|---|---|---|---|---|---|
| paper_style | 9 | 7 | 31 / 10 / 21 | 61 | 0.674 |
| paper_style | 9 | 17 | 31 / 10 / 21 | 40 | 0.684 |
| paper_style | 9 | 27 | 31 / 10 / 21 | 41 | 0.693 |
| paper_style | 25 | 7 | 30 / 10 / 22 | 34 | 0.584 |
| paper_style | 25 | 17 | 30 / 10 / 22 | 32 | 0.583 |
| paper_style | 25 | 27 | 30 / 10 / 22 | 37 | 0.578 |
| paper_style | 48 | 7 | 33 / 10 / 19 | 78 | 0.714 |
| paper_style | 48 | 17 | 33 / 10 / 19 | 39 | 0.725 |
| paper_style | 48 | 27 | 33 / 10 / 19 | 93 | 0.720 |
| agent_adapted | 9 | 7 | 31 / 10 / 21 | 77 | 0.664 |
| agent_adapted | 9 | 17 | 31 / 10 / 21 | 39 | 0.676 |
| agent_adapted | 9 | 27 | 31 / 10 / 21 | 57 | 0.670 |
| agent_adapted | 25 | 7 | 30 / 10 / 22 | 31 | 0.563 |
| agent_adapted | 25 | 17 | 30 / 10 / 22 | 32 | 0.555 |
| agent_adapted | 25 | 27 | 30 / 10 / 22 | 36 | 0.559 |
| agent_adapted | 48 | 7 | 33 / 10 / 19 | 78 | 0.745 |
| agent_adapted | 48 | 17 | 33 / 10 / 19 | 68 | 0.739 |
| agent_adapted | 48 | 27 | 33 / 10 / 19 | 95 | 0.752 |

Split, target-reference and source-file hashes are in manifest.json. Checkpoints include architecture, BERT revision, split IDs and learned weights. Training histories are in training_history.json.

## Reproduce and use

```bash
uv venv .venv --python python3.12
uv pip install --python .venv/bin/python -r gibs/requirements-learned.txt
.venv/bin/python -m gibs.learned.run_experiment
```

See gibs/learned/README.md for standalone query-only prediction and the complete paper/adaptation explanation. The baseline protocol is gibs/learned/EVALUATION_PLAN.md. Independent human review remains the next validity step.
