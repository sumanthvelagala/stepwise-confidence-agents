# 1,000 Airline trajectories and completed baseline results

This collection contains **50 tau2-bench Airline tasks × 20 runs = 1,000 distinct graded trajectories**.
There are **680 official benchmark passes and 320 failures**. These are simulated
benchmark customers and airline data. The task pass rate is not confidence-method accuracy.

## Files

- `results.json`: complete generated dataset. Each entry in `simulations` is one
  trajectory, with messages, tool calls/results, and benchmark reward. `tasks`
  contains the 50 task definitions; `info` records benchmark/model metadata.
- `COLLECTION_RESULTS.md` / `.json`: collection totals, quality flags and per-task outcomes.
- `PROVENANCE.json`: hashes and the relationship to the metadata-reduced snapshot
  used for the completed baseline evaluation. Tasks and trajectories are identical.
- `SHA256SUMS`: integrity hashes for this publication.
- [Baseline report](../../fresh_all_tasks/baseline_preview/REPORT.md),
  [per-task results](../../fresh_all_tasks/baseline_preview/per_task.csv), and
  [full metrics](../../fresh_all_tasks/baseline_preview/summary.json): completed NIBS
  and simple-baseline evaluation. The adjacent `per_step.csv` contains scores;
  reference IDs and coverage exclusions are also provided.

## Collection configuration

- Model: ASU-hosted `openai/qwen38-27b` for both assistant and user simulator.
- Assistant temperature **1.0**; user temperature **0.0**.
- 20 runs per task; seed 300; max steps 200; max errors 10.
- Reasoning and parallel tool calls disabled with explicit parameter passthrough.
- tau2-bench commit: `5bfa7e37b36656b37dc6d022156be6563c1007f3`.
- No paid model API was used for this collection.

## Baseline evaluation and limits

All 1,000 trajectories are retained. **911** have at least three other successful,
same-task references for NIBS; up to five deterministic references are used.
The baseline AUROC covers 26 tasks with both automatic label classes; first-error
localization covers 173 failed trajectories with labelled tool errors. Most agent
steps are unverified. These are automatic-label results, not human-validated accuracy.

Official benchmark success does not certify every action: 30 passing runs have
missing-expected-tool review flags. Temperature 1.0/0.0 does not guarantee mixed
outcomes or a 50:50 pass/fail ratio. The paper does not specify that ratio.

Fresh **GIBS/C4 MCS generation and GCN training/evaluation are in progress**.
Their unfinished masks, checkpoints and learned metrics are not included here.
Existing historical experiments elsewhere in the repository use different data.
This publication transfers the method to Airline; it does not reproduce the
paper's original math/QA benchmark. New collection/evaluation implementation
changes are not part of this data-only publication.

## Read the dataset

```python
import json
from pathlib import Path

path = Path("results/free_asu/main-qwen38-27b-serial-none/results.json")
data = json.loads(path.read_text())
assert len(data["simulations"]) == 1000
print(data["simulations"][0]["task_id"])
```
