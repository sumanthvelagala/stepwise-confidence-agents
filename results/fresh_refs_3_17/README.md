# Reference cap 17 experiment

Minimum 3, maximum 17 successful references. Same frozen 1,000 trajectories from all 50 Airline tasks, task-group folds and three seeds as the completed cap-5 experiment in ../fresh_all_tasks. No new trajectories or paid API calls.

There are 860 eligible teacher queries; their training reference sets contain 3–16 successes. These sets were verified identical to the uncapped sets. Each method needs 10,051 pair mappings; existing immutable CUDA pair caches are reused, then targets are averaged again. NIBS is recalculated using the actual cap of 17, since its evaluation reference bank differs from the teacher training bank.

Sol computes MCS targets; the local follow-up then retrieves targets, trains 24 GCN checkpoints, evaluates held-out predictions for all 1,000 runs, and generates REFERENCE_CAP_COMPARISON.md/json against cap 5. Higher scores are not guaranteed. Automatic labels; human validation remains pending.

The earlier uncapped job was superseded at the user's request. Pair-cache files may be hard-linked because completed pairs are immutable; teacher masks and checkpoints are newly produced. The original cap-5 files are protected by baseline_protection.json.

Keep this Mac available and the ASU VPN connected for retrieval and local training. Current status: worker_state.json and followup.log.
