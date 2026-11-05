# Paper NIBS, paper GIBS and C4: real-data prototype

**Retrospective benchmark experiment; automatic labels; independent human validation outstanding.**

## What is implemented

| Method | Implementation | Status relative to paper |
|---|---|---|
| paper_nibs_cos_max / mean | BERT cosine, within-reference max/mean, average over successful references | PDF Eq. 2 semantic NIBS on agent operations |
| paper_gibs_pdf | BERT + two GCN layers; entropy + soft CE to A m_node | PDF architecture/objective; explicit agent graph/fusion choices |
| c4_gibs | Same GCN; C4 m_ctx targets | Project adaptation, not a paper method |
| c4_state_graph | Same C4 targets, revised predictor graph | Separate graph ablation; original C4 preserved |
| released_gibs_control | Active author MLP/pooling forward and balanced edge-mask loss | Code-equation control; common training mixture/splits differ from release |
| released_nibs_cos_max / mean | Author inverse-cosine-distance formulas, reference edges incl. multiplicity | Code-formula controls |
| tool_sim_nibs | Existing tool names/arguments comparison | Agent baseline, NOT the paper's semantic NIBS |

The paper and released script are not identical. The PDF describes a GCN; the release's active forward uses MLPs/mean pooling. Both are exposed rather than silently substituting one. The release also trains failed graphs only and skips supervision above 15 nodes; this controlled runner uses mixed graphs and complete stored mappings. No claim of exact original math/QA benchmark replication is made.

## Evaluation populations

All data: 100 distinct trajectories, 796 agent steps. Recorded tau2-bench Airline, Groq agent/user at temperature 0; missing rewards and exact duplicates excluded.

- **Core OOF:** tasks 9/25/48, each test task excluded from fitting and validation; 3 seeds.
- **Additional cases:** tasks 3/40, excluded from training and validation in a separate experiment trained on 9/25/48. These were previously inspected in NIBS work, so they are not untouched holdouts.
- Successful references for training targets come only from the training partition. Reference baselines use known-successful same-task runs at evaluation; learned inference uses only the query graph.
- Stored real DeBERTa/MCS mappings supply core-task targets; this run does not recompute NLI or invent targets for additional tasks.

## core_oof

Label counts: `{'unverified': 478, 'valid': 74, 'incorrect': 21}`. Unknown and attempted errors are excluded from binary metrics; unknown steps still compete in localization.

### tool calls

| Method | Macro AUROC | Top-1 | Top-3 | MRR |
|---|---|---|---|---|
| paper_gibs_pdf | 0.550 +/- 0.038 | 0.686 +/- 0.055 | 0.863 +/- 0.055 | 0.791 +/- 0.036 |
| c4_gibs | 0.628 +/- 0.101 | 0.725 +/- 0.073 | 0.902 +/- 0.028 | 0.826 +/- 0.052 |
| c4_state_graph | 0.727 +/- 0.011 | 0.608 +/- 0.028 | 0.784 +/- 0.028 | 0.734 +/- 0.013 |
| released_gibs_control | 0.639 +/- 0.033 | 0.686 +/- 0.028 | 0.863 +/- 0.055 | 0.801 +/- 0.026 |
| tool_sim_nibs | 1.000 | 0.791 | 0.962 | 0.871 |
| paper_nibs_cos_max | 0.583 | 0.529 | 0.706 | 0.668 |
| paper_nibs_cos_mean | 0.603 | 0.706 | 0.882 | 0.811 |
| released_nibs_cos_max | 0.583 | 0.529 | 0.706 | 0.668 |
| released_nibs_cos_mean | 0.895 | 0.706 | 0.941 | 0.824 |
| random_expected | 0.500 | 0.347 | 0.775 | 0.584 |
| last_step_first | 0.686 | 0.824 | 0.882 | 0.871 |
| direct_A | 1.000 | 0.742 | 0.874 | 0.830 |
| direct_C4 | 1.000 | 0.767 | 0.947 | 0.858 |

### all agent steps

| Method | Macro AUROC | Top-1 | Top-3 | MRR |
|---|---|---|---|---|
| paper_gibs_pdf | 0.715 +/- 0.018 | 0.275 +/- 0.154 | 0.706 +/- 0.173 | 0.524 +/- 0.120 |
| c4_gibs | 0.765 +/- 0.049 | 0.098 +/- 0.100 | 0.745 +/- 0.100 | 0.430 +/- 0.084 |
| c4_state_graph | 0.857 +/- 0.008 | 0.000 +/- 0.000 | 0.412 +/- 0.083 | 0.312 +/- 0.026 |
| released_gibs_control | 0.804 +/- 0.041 | 0.039 +/- 0.028 | 0.549 +/- 0.073 | 0.360 +/- 0.028 |
| tool_sim_nibs | 1.000 | 0.791 | 0.962 | 0.871 |
| paper_nibs_cos_max | 0.705 | 0.000 | 0.176 | 0.196 |
| paper_nibs_cos_mean | 0.535 | 0.353 | 0.647 | 0.548 |
| released_nibs_cos_max | 0.705 | 0.000 | 0.176 | 0.196 |
| released_nibs_cos_mean | 0.883 | 0.471 | 0.706 | 0.626 |
| random_expected | 0.500 | 0.128 | 0.385 | 0.336 |
| last_step_first | 0.641 | 0.000 | 0.765 | 0.403 |
| direct_A | 0.987 | 0.278 | 0.746 | 0.524 |
| direct_C4 | 0.992 | 0.273 | 0.761 | 0.529 |

All learned results are mean +/- population standard deviation over seeds, not confidence intervals. Macro AUROC averages only tasks containing both explicit correctness labels; inspect summary.json denominators. Additional task 3 has no labelled executed error, so its AUROC/localization is undefined.

## additional_cases

Label counts: `{'unverified': 152, 'valid': 69, 'attempted_incorrect': 1, 'incorrect': 1}`. Unknown and attempted errors are excluded from binary metrics; unknown steps still compete in localization.

### tool calls

| Method | Macro AUROC | Top-1 | Top-3 | MRR |
|---|---|---|---|---|
| paper_gibs_pdf | 0.679 +/- 0.227 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 |
| c4_gibs | 0.679 +/- 0.227 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 |
| c4_state_graph | 0.519 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 |
| released_gibs_control | 0.617 +/- 0.017 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 |
| tool_sim_nibs | 1.000 | 1.000 | 1.000 | 1.000 |
| paper_nibs_cos_max | 1.000 | 1.000 | 1.000 | 1.000 |
| paper_nibs_cos_mean | 1.000 | 1.000 | 1.000 | 1.000 |
| released_nibs_cos_max | 1.000 | 1.000 | 1.000 | 1.000 |
| released_nibs_cos_mean | 1.000 | 1.000 | 1.000 | 1.000 |
| random_expected | 0.500 | 0.500 | 1.000 | 0.750 |
| last_step_first | 0.759 | 1.000 | 1.000 | 1.000 |

### all agent steps

| Method | Macro AUROC | Top-1 | Top-3 | MRR |
|---|---|---|---|---|
| paper_gibs_pdf | 0.690 +/- 0.219 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 |
| c4_gibs | 0.690 +/- 0.219 | 0.333 +/- 0.471 | 1.000 +/- 0.000 | 0.667 +/- 0.236 |
| c4_state_graph | 0.536 +/- 0.000 | 0.000 +/- 0.000 | 1.000 +/- 0.000 | 0.500 +/- 0.000 |
| released_gibs_control | 0.631 +/- 0.017 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 |
| tool_sim_nibs | 1.000 | 1.000 | 1.000 | 1.000 |
| paper_nibs_cos_max | 0.964 | 0.000 | 0.000 | 0.250 |
| paper_nibs_cos_mean | 1.000 | 1.000 | 1.000 | 1.000 |
| released_nibs_cos_max | 0.964 | 0.000 | 0.000 | 0.250 |
| released_nibs_cos_mean | 1.000 | 1.000 | 1.000 | 1.000 |
| random_expected | 0.500 | 0.143 | 0.429 | 0.370 |
| last_step_first | 0.964 | 0.000 | 1.000 | 0.500 |

All learned results are mean +/- population standard deviation over seeds, not confidence intervals. Macro AUROC averages only tasks containing both explicit correctness labels; inspect summary.json denominators. Additional task 3 has no labelled executed error, so its AUROC/localization is undefined.

## Graph experiment

Original C4 matcher/targets remain unchanged. The separate state graph uses the latest prior non-error tool observation containing an argument value, and links messages to the most recent user and tool observation. All dependency edges point forward. This is a heuristic representation, not causal or policy verification.

Compare c4_state_graph against c4_gibs: only predictor adjacency changes, while text features, targets, splits, seeds and optimization stay fixed. A gain or loss is reported as observed, not selected away.

Example diagrams and edge lists are in graphs/. They include failed/successful cases from additional tasks 3/40 as well as familiar tasks 25/48. These demonstrations are not independent accuracy evidence.

## Limits

- Small data, previously exposed task scenarios, incomplete rule labels and very few same-tool wrong-argument examples.
- Paper algorithms are applied to an agent graph adapter; the original paper datasets, generated reasoning graphs, 2,000-graph training scale and full evaluation are not reproduced.
- Cosine scores and learned masks are not established calibrated correctness probabilities. Raw cosine can be negative.
- A high AUROC on tools absent from successful references does not establish subtle action-error detection.
- The first verifier-labelled incorrect action is a localization proxy; omissions and policy/message mistakes may remain unlabelled.
- BERT is frozen. Text truncation and representation may lose exact dates/IDs; the learned C4 model does not enforce its teacher's field checks at inference.
- Complete the existing independent human-review sheet before making human-validated claims.

## Reproduce

```bash
.venv/bin/python -m gibs.comparison.run
```

See gibs/comparison/README.md and EVALUATION_PLAN.md. Per-step predictions, metrics, trained checkpoints, histories and provenance are stored alongside this report. Earlier results are preserved.
