# All-reference ablation — minimum three retained

This is a separate, controlled experiment. The completed five-reference run
remains unchanged in `../fresh_all_tasks/`.

- Same exact frozen dataset: 1,000 trajectories, all 50 Airline tasks.
- Same task-group folds (260 / 260 / 240 / 240 test trajectories), seeds 7/17/27,
  graph projection, model architecture, loss, fitting settings and verifier.
- Same minimum of three successful training references, excluding the query's
  exact-content class. Same 860 teacher-eligible queries.
- **Only the reference maximum changes: five → all eligible.** Training-target
  references still come only from the training partition. NIBS evaluation uses
  all eligible successful references under its existing evaluation-access rule.
- Eligible training-reference counts range from 3 to 16, not a fixed 17.
- Each method now needs 10,051 MCS pair mappings: 4,228 cached pairs from the
  completed run are reused, and 5,823 pairs are added. Old averaged teacher masks
  and learned checkpoints are not reused; new masks and predictors are computed.
- Existing CUDA NLI probability cache and frozen BERT features can be reused.
  There are no new LLM-generation calls or paid API requests.

`ABLATION_DESIGN.json` records the reference counts and controlled-design checks.
`baseline_protection.json` stores hashes of the original report, data and 24
checkpoints. Runtime-verified baseline source hashes take precedence over its
earlier preparation hashes. The new frozen input is the exact baseline file.

Execution: Sol A100 targets → local 24-model training/evaluation → verified
five-versus-all comparison. The monitor retries read-only connection failures
with backoff and resumes timeout/preemption within an eight-allocation bound.
Keep this Mac awake and the ASU VPN connected for retrieval and local fitting.

Check `worker_state.json` and `followup.log` for current progress. On completion,
`REFERENCE_CAP_COMPARISON.md` / `.json` compare the runs on identical populations,
including tool-only and all-agent scopes, three-seed dispersion and all-query
learned coverage. Differences are descriptive, not significance tests.

Human validation is still pending. Review templates from the completed run
remain available in `../fresh_all_tasks/human_review/review/`; the unfinished
human review is not claimed complete by starting this ablation.
