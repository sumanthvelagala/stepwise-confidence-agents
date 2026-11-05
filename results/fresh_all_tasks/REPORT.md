# All-task, out-of-fold paper GIBS / C4 comparison

1000 trajectories across 50 tasks. Four held-out task-group folds, three seeds.
Every learned prediction is from a model that excluded that trajectory’s entire task group from fitting.
911 trajectories have enough references for the common NIBS/GIBS/C4 comparison.
NIBS-unavailable tasks still receive learned predictions and remain in per_task.csv.
Automatic labels; independent human validation pending. Undefined AUROC is shown as N/A.

| Method | Common tool macro AUROC | Common tool first-error top-1 |
|---|---|---|
| paper_gibs_pdf | 0.700 | 0.341 |
| c4_gibs | 0.719 | 0.522 |
| tool_sim_nibs | 0.994 | 0.590 |
| paper_nibs_cos_max | 0.931 | 0.572 |
| paper_nibs_cos_mean | 0.724 | 0.717 |
| random_expected | 0.500 | 0.143 |
| last_step_first | 0.726 | 0.665 |

| Task | Saved trajectories | Common-comparison trajectories | NIBS Max AUROC | GIBS AUROC | C4 AUROC |
|---|---|---|---|---|---|
| 0 | 20 | 20 | N/A | N/A | N/A |
| 1 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 2 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 3 | 20 | 20 | N/A | N/A | N/A |
| 4 | 20 | 20 | N/A | N/A | N/A |
| 5 | 20 | 20 | 1.000 | 0.833 | 1.000 |
| 6 | 20 | 20 | N/A | N/A | N/A |
| 7 | 20 | 0 | N/A | N/A | N/A |
| 8 | 20 | 20 | N/A | N/A | N/A |
| 9 | 20 | 20 | 1.000 | 0.783 | 0.852 |
| 10 | 20 | 20 | N/A | N/A | N/A |
| 11 | 20 | 20 | 0.967 | 0.794 | 0.656 |
| 12 | 20 | 20 | 0.926 | 0.313 | 0.295 |
| 13 | 20 | 20 | N/A | N/A | N/A |
| 14 | 20 | 0 | N/A | N/A | N/A |
| 15 | 20 | 20 | 1.000 | 0.824 | 0.729 |
| 16 | 20 | 20 | 1.000 | 0.803 | 0.678 |
| 17 | 20 | 20 | 1.000 | 0.384 | 0.586 |
| 18 | 20 | 20 | 0.729 | 0.438 | 0.521 |
| 19 | 20 | 20 | 1.000 | 0.000 | 0.000 |
| 20 | 20 | 17 | N/A | N/A | N/A |
| 21 | 20 | 17 | 0.312 | 0.927 | 0.524 |
| 22 | 20 | 20 | 0.818 | 0.374 | 0.478 |
| 23 | 20 | 20 | 0.978 | 0.651 | 0.335 |
| 24 | 20 | 20 | 0.875 | 0.517 | 0.295 |
| 25 | 20 | 20 | N/A | N/A | N/A |
| 26 | 20 | 20 | N/A | N/A | N/A |
| 27 | 20 | 20 | 0.833 | 0.556 | 1.000 |
| 28 | 20 | 20 | N/A | N/A | N/A |
| 29 | 20 | 0 | N/A | N/A | N/A |
| 30 | 20 | 20 | N/A | N/A | N/A |
| 31 | 20 | 20 | N/A | N/A | N/A |
| 32 | 20 | 17 | N/A | N/A | N/A |
| 33 | 20 | 20 | 0.824 | 0.373 | 0.710 |
| 34 | 20 | 20 | N/A | N/A | N/A |
| 35 | 20 | 20 | 1.000 | 0.821 | 0.296 |
| 36 | 20 | 20 | N/A | N/A | N/A |
| 37 | 20 | 20 | 0.931 | 0.814 | 0.848 |
| 38 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 39 | 20 | 20 | 1.000 | 0.812 | 0.979 |
| 40 | 20 | 20 | N/A | N/A | N/A |
| 41 | 20 | 20 | 1.000 | 0.639 | 1.000 |
| 42 | 20 | 20 | 1.000 | 0.550 | 0.918 |
| 43 | 20 | 20 | 1.000 | 0.991 | 1.000 |
| 44 | 20 | 0 | N/A | N/A | N/A |
| 45 | 20 | 20 | N/A | N/A | N/A |
| 46 | 20 | 20 | N/A | N/A | N/A |
| 47 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 48 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 49 | 20 | 20 | N/A | N/A | N/A |

See summary.json for separate all-query learned metrics, class counts and exact denominators.
No original math/QA benchmark reproduction, calibrated correctness or human-verified improvement is claimed.
