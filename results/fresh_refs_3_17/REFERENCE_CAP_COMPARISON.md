# Reference-cap ablation: maximum 5 versus maximum 17

Same data, task-group folds, seeds, model implementation and minimum-three rule. Only the maximum reference cap changes.
Both training-target references and NIBS evaluation references use the new cap; their original partition-access rules are unchanged.
911 runs in the common comparison; all 1,000 receive held-out learned scores.
Automatic labels; independent human validation pending. Learned values are means over three seeds; deltas are descriptive, not significance tests.

## tool calls

| Method | Cap-5 AUROC | maximum 17 AUROC | Delta | Cap-5 Top-1 | maximum 17 Top-1 | Delta |
|---|---:|---:|---:|---:|---:|---:|
| paper_gibs_pdf | 0.700 | 0.723 | 0.023 | 0.341 | 0.407 | 0.066 |
| c4_gibs | 0.719 | 0.706 | -0.014 | 0.522 | 0.493 | -0.029 |
| tool_sim_nibs | 0.994 | 0.994 | 0.001 | 0.590 | 0.615 | 0.026 |
| paper_nibs_cos_max | 0.931 | 0.916 | -0.014 | 0.572 | 0.543 | -0.029 |
| paper_nibs_cos_mean | 0.724 | 0.731 | 0.008 | 0.717 | 0.723 | 0.006 |
| random_expected | 0.500 | 0.500 | 0.000 | 0.143 | 0.143 | 0.000 |
| last_step_first | 0.726 | 0.726 | 0.000 | 0.665 | 0.665 | 0.000 |

## all agent steps

| Method | Cap-5 AUROC | maximum 17 AUROC | Delta | Cap-5 Top-1 | maximum 17 Top-1 | Delta |
|---|---:|---:|---:|---:|---:|---:|
| paper_gibs_pdf | 0.735 | 0.746 | 0.012 | 0.312 | 0.382 | 0.069 |
| c4_gibs | 0.705 | 0.689 | -0.016 | 0.459 | 0.410 | -0.048 |
| tool_sim_nibs | 0.995 | 0.996 | 0.001 | 0.590 | 0.615 | 0.026 |
| paper_nibs_cos_max | 0.913 | 0.876 | -0.038 | 0.012 | 0.000 | -0.012 |
| paper_nibs_cos_mean | 0.728 | 0.727 | -0.002 | 0.162 | 0.162 | 0.000 |
| random_expected | 0.500 | 0.500 | 0.000 | 0.063 | 0.063 | 0.000 |
| last_step_first | 0.601 | 0.601 | 0.000 | 0.000 | 0.000 | 0.000 |

See REFERENCE_CAP_COMPARISON.json for per-seed dispersion and separate all-query learned results.
No new trajectories were generated. Baseline artifacts were preserved. The human review and missing ACC@80%/ECE work remain separate.
