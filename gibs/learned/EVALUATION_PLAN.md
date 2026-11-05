# Learned GIBS prototype: evaluation plan

Written before training the new predictor. This is a **paper-inspired agent
adaptation**, not a reproduction of the paper's published benchmark results.

## Method and paper provenance

Primary reference: supplied arXiv **2605.19228v2**, sections 4.3–4.4, equation 6,
Appendices C.2 and D.3. The author repository at commit `1ccc8b8` is a secondary
reference: https://github.com/Xiao0o0o/stepwise-confidence-attribution/tree/1ccc8b8.

- Frozen `google-bert/bert-base-uncased`, revision
  `86b5e0934494bd15c9632b12f734a8a67f723594`, CLS features, 256-token truncation
  (authors' BERT feature script), with explicit truncation counts.
- Nodes are results; incoming operation text represents the step. Root/user
  events supply context. Value-provenance dependencies come from the existing
  agent parser, not LangFun-generated reasoning dependencies.
- Two GCN layers, hidden size 128, dropout 0.1. Use directed source-to-target
  propagation with self-loops and symmetric degree normalization, implemented
  directly in PyTorch. Mean graph context and operation features are fused with
  the result-node representation by an MLP to predict one mask per agent step.
  The paper does not fully specify this fusion; mean incoming operation embeddings
  and one score per agent event are explicit implementation choices.
- Train on both successful and failed training trajectories with soft MCS
  consensus targets. Minimize **equation 6**, binary mask entropy + lambda * soft
  binary cross-entropy, lambda=1 fixed. This follows the stated final objective
  and the active author loss, not an implementation of the separate sparse-prior
  KL expression in equation 5. These expressions are not interchangeable.
- Paper-style version: existing variant **A**, `m_node` (Appendix C.2). No
  structured-field check, single-component MCS, author-style text truncation.
- Agent-adapted version: existing **C4**, `m_ctx`, including structured-field
  checks, symmetric NLI truncation and multi-component matching. This changes
  supervision, not the predictor architecture. Message targets remain exploratory.

The active forward path in the released `GIB_MCS_wo_mcs_feature.py` uses node/edge
MLPs and mean pooling; it does not call its declared GCN during prediction.
Our implementation follows the **paper's stated two-layer GCN design**. We do
not claim bit-for-bit reproduction of that released script.

## Data and splits

- Recorded tau2-bench Airline tasks **9, 25, 48**, Groq `gpt-oss-20b`, agent/user
  temperature 0. These are previously exposed development tasks. Existing saved
  A and C4 query/reference node/edge indicators cover these tasks; reuse those
  recorded DeBERTa-MNLI+MCS results rather than redownloading/recomputing NLI.
  Record their file hashes and recorded NLI configuration.
- Remove infrastructure errors and exact duplicate content. Exclude the entire
  query class from successful references, require >=3 references for a target.
- Three leave-one-task-out folds. The test task contributes **no gradients,
  training/validation targets, references for those targets, or early stopping**.
- In each remaining task/outcome stratum, deterministically reserve 20% of classes
  for validation (ceil, keeping >=1 training example), based on hashed UUID and a
  fixed split seed of 20261028. Do not stratify by step labels or confidence.
- Training and validation pseudo-targets use only successful **training-split**
  references of the same task. No validation/test reference leakage into fitting.
- Seeds **7, 17, 27**. Adam 1e-3, maximum 150 epochs, batch size 8 graphs,
  early stopping patience 20, minimum delta 1e-5, validation loss only. Frozen
  BERT features are computed once; only GCN/MLP parameters are optimized.
- The paper trains on 2,000 graphs; this prototype has only about 62 distinct
  trajectories, with even fewer training examples per fold. No comparable-scale
  or statistical-generalization claim is appropriate.

## Baselines and metrics

On the identical out-of-fold test queries:

1. Existing tool-only **NIBS** (max aggregation).
2. Direct **A m_node** and **C4 m_ctx** reference consensus (diagnose whether
   training improves on or loses information from its teacher).
3. Random ranking (exact analytical expectation) and last-step-first ranking.

Reference methods use known-successful, same-task reference runs at evaluation,
excluding the query class; learned inference uses **only the query graph**.
This difference in reference access must be reported, not hidden.

Use verifier v2 labels only for evaluation: valid vs executed incorrect actions;
unverified and attempted_incorrect excluded from binary metrics. Report all-agent
and tool-only AUROC, grouped-threshold average precision, error detection/false
alarms at 0.5, and first-verifier-labelled-error top-1/top-3/MRR, with exact uniform
tie handling. All candidate steps, including unverified ones, compete in ranking.
Report per task and per seed; aggregate out-of-fold metrics across tasks within
each seed, then mean/standard deviation across seeds. Do not silently ensemble.

Also report mask-target validation loss, training history, data/label counts,
unknown-label fraction, model size, runtime, truncation, splits and references.
Independent human labels remain pending. With almost all negatives structurally
easy and only one difficult wrong booking in these three tasks, high AUROC is not
proof of subtle action-error detection. Failure and no improvement are valid results.

## Prototype acceptance

- A real BERT model is loaded and GCN weights actually change during training.
- Saved best checkpoints reload and reproduce per-step predictions.
- Every test trajectory gets one finite score per agent step, in [0,1].
- Split/reference leakage, parser alignment and duplicate-class checks pass.
- Both learned versions and all baselines are evaluated on the same queries.
- A standalone inference command accepts a recorded trajectory without reading
  rewards, benchmark gold actions, step labels or reference trajectories.
- Preserve all existing NIBS, graph-matching code and historical results.

Outputs: `results/gibs_learned/` report, per-step/seed predictions, metrics,
training history, split manifest, checkpoints and provenance. Large frozen BERT
features are cached outside tracked outputs. No LLM generation, paid API calls
or new human labels are part of this run.
