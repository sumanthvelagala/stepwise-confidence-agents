# MCS and outcome-balance check

Checked UTC: 2026-10-29T17:17:08.976807+00:00

Fresh GCN fitting has not started. Real DeBERTa/MCS target creation is in progress.

| Method | Saved query masks | Saved query/reference MCS mappings |
|---|---:|---:|
| paper_gibs_pdf | 33 | 162 |
| c4_gibs | 33 | 158 |

Each pair JSON saves node_map, edge_map and per-step mask. Each teacher JSON saves reference IDs and averaged soft targets.
Paper GIBS uses node membership; C4 uses context-supported membership. Each eligible query uses 3–5 successful training-only references.

**Collection outcome balance: 680 pass / 320 fail. It is not a 50:50 dataset.**
20 runs per task does not imply 10 successes and 10 failures. Task 25 has 20 passes; task 7 has 20 failures.

Current splits preserve outcome strata; current GCN fitting uses equal query weighting, with no balanced outcome sampler or class weights.
Pass/fail balance concerns whole trajectories. GCN supervision is per-step fractional MCS consensus, so balancing trajectories does not automatically balance step targets.

See MCS_AND_BALANCE_AUDIT.json for eligible training/validation outcome counts per fold. These are audits of the running protocol; no balancing change or completed fresh fitting is claimed.
