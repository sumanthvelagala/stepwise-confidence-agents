# All-task, out-of-fold paper GIBS / C4 comparison

1000 trajectories across 50 tasks. Four held-out task-group folds, three seeds.
Every learned prediction is from a model that excluded that trajectory’s entire task group from fitting.
911 trajectories have enough references for the common NIBS/GIBS/C4 comparison.
NIBS-unavailable tasks still receive learned predictions and remain in per_task.csv.
Automatic labels; independent human validation pending. Undefined AUROC is shown as N/A.

| Method | Common tool macro AUROC | Common tool first-error top-1 |
|---|---|---|
| paper_gibs_pdf | 0.723 | 0.407 |
| c4_gibs | 0.706 | 0.493 |
| tool_sim_nibs | 0.994 | 0.615 |
| paper_nibs_cos_max | 0.916 | 0.543 |
| paper_nibs_cos_mean | 0.731 | 0.723 |
| random_expected | 0.500 | 0.143 |
| last_step_first | 0.726 | 0.665 |

| Task | Saved trajectories | Common-comparison trajectories | NIBS Max AUROC | GIBS AUROC | C4 AUROC |
|---|---|---|---|---|---|
| 0 | 20 | 20 | N/A | N/A | N/A |
| 1 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 2 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 3 | 20 | 20 | N/A | N/A | N/A |
| 4 | 20 | 20 | N/A | N/A | N/A |
| 5 | 20 | 20 | 1.000 | 0.942 | 1.000 |
| 6 | 20 | 20 | N/A | N/A | N/A |
| 7 | 20 | 0 | N/A | N/A | N/A |
| 8 | 20 | 20 | N/A | N/A | N/A |
| 9 | 20 | 20 | 1.000 | 0.848 | 0.874 |
| 10 | 20 | 20 | N/A | N/A | N/A |
| 11 | 20 | 20 | 0.967 | 0.750 | 0.544 |
| 12 | 20 | 20 | 0.926 | 0.453 | 0.397 |
| 13 | 20 | 20 | N/A | N/A | N/A |
| 14 | 20 | 0 | N/A | N/A | N/A |
| 15 | 20 | 20 | 1.000 | 0.857 | 0.626 |
| 16 | 20 | 20 | 1.000 | 0.932 | 0.523 |
| 17 | 20 | 20 | 1.000 | 0.359 | 0.661 |
| 18 | 20 | 20 | 0.764 | 0.500 | 0.519 |
| 19 | 20 | 20 | 1.000 | 0.037 | 0.000 |
| 20 | 20 | 17 | N/A | N/A | N/A |
| 21 | 20 | 17 | 0.312 | 0.906 | 0.462 |
| 22 | 20 | 20 | 0.859 | 0.303 | 0.552 |
| 23 | 20 | 20 | 0.978 | 0.649 | 0.163 |
| 24 | 20 | 20 | 0.292 | 0.493 | 0.497 |
| 25 | 20 | 20 | N/A | N/A | N/A |
| 26 | 20 | 20 | N/A | N/A | N/A |
| 27 | 20 | 20 | 1.000 | 0.139 | 1.000 |
| 28 | 20 | 20 | N/A | N/A | N/A |
| 29 | 20 | 0 | N/A | N/A | N/A |
| 30 | 20 | 20 | N/A | N/A | N/A |
| 31 | 20 | 20 | N/A | N/A | N/A |
| 32 | 20 | 17 | N/A | N/A | N/A |
| 33 | 20 | 20 | 0.790 | 0.439 | 0.483 |
| 34 | 20 | 20 | N/A | N/A | N/A |
| 35 | 20 | 20 | 1.000 | 0.779 | 0.333 |
| 36 | 20 | 20 | N/A | N/A | N/A |
| 37 | 20 | 20 | 0.931 | 0.776 | 0.849 |
| 38 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 39 | 20 | 20 | 1.000 | 0.862 | 0.962 |
| 40 | 20 | 20 | N/A | N/A | N/A |
| 41 | 20 | 20 | 1.000 | 0.947 | 0.998 |
| 42 | 20 | 20 | 1.000 | 0.836 | 0.902 |
| 43 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 44 | 20 | 0 | N/A | N/A | N/A |
| 45 | 20 | 20 | N/A | N/A | N/A |
| 46 | 20 | 20 | N/A | N/A | N/A |
| 47 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 48 | 20 | 20 | 1.000 | 1.000 | 1.000 |
| 49 | 20 | 20 | N/A | N/A | N/A |

See summary.json for separate all-query learned metrics, class counts and exact denominators.
No original math/QA benchmark reproduction, calibrated correctness or human-verified improvement is claimed.
