# Paper algorithms and C4: comparison plan

This plan precedes execution of the new semantic-NIBS comparison, released-code
control, graph ablation and additional-task evaluation. It extends, and does not
rewrite, the existing NIBS and learned-GIBS experiments. Prior results on tasks
9/25/48 are already known; no claim of preregistering those earlier observations.

## Requested primary methods

1. **Paper NIBS**: equation 2 with frozen BERT semantic cosine similarity, max and
   mean within each successful reference, then equal averaging across references.
   One candidate step is an operation text; successful reference steps are agent
   operations, each counted once. This replaces the prior tool-name/argument
   similarity. The prior `tool_sim` implementation remains an agent baseline.
2. **Paper GIBS (PDF specification)**: frozen BERT, two-layer GCN (128 hidden,
   dropout 0.1), operation/result features, equation-6 entropy + soft BCE to
   Appendix-C.2 `m_node`, computed from stored paper-style A MCS matches.
3. **C4 GIBS**: identical predictor and optimization; C4's `m_ctx` supplies the
   supervision. Keep original C4 matching unchanged to preserve a clean reference.

The supplied PDF does not fully specify fusion details. The released author's
active `wo_mcs_feature` predictor uses MLP/mean-pooling, not its declared GCN.
Therefore include a separately labelled **released-forward/loss control**, rather
than falsely describing one implementation as simultaneously identical to both.
The control reimplements the active node/edge MLP, graph pooling, predictor, mask
entropy and per-reference balanced edge-membership CE. Preserve skipping empty
MCS edge sets in that loss. Use the common train/validation split and successful+
failed training mixture for a controlled comparison; the release trains failed
graphs only and has a >15-node supervision shortcut, which we do NOT reproduce.
This control is not an end-to-end replication of the release's experiment.

Also report the authors' cosine-distance transformations (Cos-Max and Cos-Mean)
as separate NIBS controls. Their formulas differ from raw cosine in PDF equation
2. For these controls compare against all operation edges of each reference,
including multiplicity, as the release does. Agent-only scored events and user
context remain necessary domain adaptations.

Primary sources, checked directly:
- supplied `2605.19228v2.pdf`, equations 2/6, appendices C.2/D.3;
- https://github.com/Xiao0o0o/stepwise-confidence-attribution/tree/1ccc8b8
- `src/NIBS/similarity_based_baseline.py`, `src/GIBS/GIB_MCS_wo_mcs_feature.py`,
  `src/GIBS/find_mcs.py`, `src/dataset/bert_graph.py` at that commit.

## Graph-structure ablation (do not overwrite C4)

Add **C4-state-graph** as a predictor-input ablation with unchanged C4 targets:
- tool arguments connect to the latest prior non-error tool observation containing the
  value, falling back to the original earliest provenance when no such observation
  exists;
- messages connect to the most recent user turn and most recent tool observation;
- preserve all events, operation/result text, one score per agent event and a DAG
  with no future-to-past dependency edges.

This better represents explicit state refreshes and observation-to-message
relationships that the current value-only graph omits. It is a heuristic, not
proof of causality or policy compliance. Its benefit is tested, not assumed.
Matching targets are NOT recomputed on the new graph, so this isolates the
predictor representation. No claim that this is a new paper MCS algorithm.

## Real data, partitions and labels

- Core: the same 62 distinct trajectories from tasks 9/25/48; three leave-one-task-
  out folds, as before. Stratified class-separated validation within training tasks.
- Additional cases: tasks **3 and 40**, approximately 38 distinct trajectories.
  They were previously inspected in NIBS work, so call them external-to-training
  retrospective cases, not untouched holdouts. Train these models only on the
  original tasks 9/25/48, with class-separated validation. Never train or select
  checkpoints using tasks 3/40. Their automatic labels are narrow and task 3 has
  no verifier-labelled executed incorrect step, so some metrics are undefined.
- All trajectories: recorded tau2-bench Airline, same Groq model/user, temperature
  0, benchmark/policy identity checked, reward=None excluded, UUID/content dedup,
  query-class exclusion, >=3 successful references for applicable methods.
- Existing DeBERTa/MCS results are reused for training tasks, explicitly marked
  as stored, not freshly recomputed. No manufactured MCS masks for tasks 3/40.
- Features never include rewards/gold actions. Frozen BERT text embeddings may
  be cached globally because no encoder fitting occurs on this dataset.
- Verifier-v2 labels for evaluation only. Unknown steps never presumed correct.
  Full human validation remains outstanding; reuse the existing review sheet.

## Fixed training and evaluation

Seeds 7/17/27; Adam 1e-3; 150 epochs maximum; batch 8 graphs; early stopping on
validation objective only, patience 20, delta 1e-5. Same split across methods.
Run all variants; do not select the best on the test sets. Report mean/std across
seeds, not a best seed or an undisclosed ensemble.

Report all-agent and tool-only error-positive AUROC, grouped AP, top-1/top-3/MRR
for the first verifier-labelled executed incorrect action, and threshold-0.5
error detection/false alarms. Unknown steps still compete in localization.
Resolve rank ties by exact uniform expectation. Include denominators, label
coverage, reference access, sparse/difficult-negative limitations and failures.
Additional baselines: tool_sim NIBS, direct A/C4 consensus where available,
random expectation and last-step-first. Reference methods receive known-successful
same-task runs at evaluation; trained predictors receive only the query graph.

## Prototype outputs and checks

One command: `.venv/bin/python -m gibs.comparison.run`.
Write only `results/paper_comparison/`: report, metrics, per-step predictions,
training histories, checkpoints, input/source/teacher hashes, split/reference
manifests and example graph diagrams for tasks 3/25/40/48. Keep all prior results.

Acceptance: semantic-NIBS formula oracles and official-formula checks; released
forward/loss numerical checks; paper loss tests; graph causality/provenance
tests; train/validation/test and reference isolation; checkpoint reload equality;
query-only inference with no outcome/gold fields; identical evaluation populations.
No new LLM simulations, paid API calls, fabricated human labels or claims of
reproducing the paper's original math/QA benchmark numbers.
