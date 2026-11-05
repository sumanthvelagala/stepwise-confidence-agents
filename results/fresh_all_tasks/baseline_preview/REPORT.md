# All-task baseline results; learned comparison pending

1000 distinct trajectories across 50 tasks; 911 trajectories have enough same-task successful references.
Automatic verifier labels only; independent human review remains pending. Unknown steps are excluded from binary metrics.
Reference methods receive successful examples at evaluation. These scores do not establish calibrated confidence.

| Method | Tool macro AUROC | Tool first-error top-1 |
|---|---|---|
| tool_sim_nibs | 0.994 | 0.590 |
| paper_nibs_cos_max | 0.931 | 0.572 |
| paper_nibs_cos_mean | 0.724 | 0.717 |
| random_expected | 0.500 | 0.143 |
| last_step_first | 0.726 | 0.665 |

See per_task.csv for all 50 tasks and summary.json for exact evaluation denominators.
Missing references or missing label classes produce unavailable scores, not invented accuracy.
Paper GIBS and C4 are still computing; this is a baseline preview only.
