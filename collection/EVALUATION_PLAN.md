# Fresh, free open-weight tau2 collection

The user authorized more tasks/trajectories with **no paid model APIs**, using
ASU Sol access. This applies the paper's methods to tau2 Airline; it does not
turn Airline into the paper's original math/QA benchmark.

## Collection

- Pin tau2 commit `5bfa7e37b36656b37dc6d022156be6563c1007f3` and the existing
  airline policy. All 50 tasks (IDs 0–49), DB/COMMUNICATE reward only.
- Serve open-weight `qwen3:8b` through Ollama 0.30.3 on a Sol GPU compute node.
  Record the model's immutable weight digest/quantization, software, seeds and
  generated usage. Never start model inference on the login node.
- Alternative: ASU's free hosted API, using an explicitly selected active
  tool-capable chat model from its authenticated catalog. Record metadata and
  request reasoning effort `none`; the gateway can substitute a supported level.
  Disable gateway add-ons. Hosted immutable weight revisions are not exposed.
  Treat each hosted model as a separate collection regime and never merge it
  silently with local Qwen or historical Groq runs.
- Agent temperature 1.0, user temperature 0.0, thinking disabled for both.
  Context 32,768, output cap 2,048 tokens/call; max steps 200; max errors 10;
  benchmark seed 300. Tau2 derives a reproducible seed for each trial.
- Same model simulates the customer. Treat simulator correctness as a separate
  validity concern, to be checked by reviewing representative transcripts.
- Smoke: Task 13, one trajectory, excluded from the research dataset. Require
  a graded outcome, a tool call and compatibility with the graph parser.
- Pilot: all 50 tasks × 3 attempts = 150 trajectories. Used to assess serving,
  runtime, infrastructure failures, tool calling and available success/failure
  variation; no confidence-method tuning or winner selection.
- Main target: all 50 × 20 = 1,000 trajectories, matching the paper's repeated
  sampling count per problem. It is a collection target, not a statistical
  requirement or guaranteed completed dataset. Limit each Sol allocation to
  24 hours and checkpoint; resume the identical configuration if needed.
- Keep smoke, pilot, main and old Groq temperature-0 data separate. The new
  Qwen regime is not directly interchangeable with the old agent regime.
- Infrastructure errors are preserved/reported separately; native tau2 resume
  retries infrastructure failures. The wrapper archives the current results
  before such a retry; include snapshots when reporting total attempted runs.
- Do not filter out always-success/always-fail tasks silently. Report the
  fraction lacking successful references or labelled errors before choosing the
  evaluable subset.

## Evaluation after collection

1. Verify configuration, tool schema, outcome/usage records, and model digest.
   Deduplicate UUID/content classes and exclude the query's whole class from
   successful references. Report unbuildable parallel-call trajectories; never
   silently turn several calls into one.
2. Freeze a manifest and task-family train/validation/test assignment before
   confidence scores are computed. Closely related scenarios must stay together.
   Reserve new test families from training, reference construction for training
   targets, early stopping and tuning. Record any prior exposure separately.
3. Construct **fresh** paper-style and C4 MCS targets on training/validation
   trajectories using only successful training references. Historical Groq MCS
   targets cannot be reused for newly generated Qwen trajectories.
4. Run semantic paper NIBS (Cos-Max/Mean), paper-spec GIBS and C4 GIBS. Include
   tool_sim, direct consensus and random/position baselines. Keep graph ablations
   separately named and do not pick one based on test results.
5. Independently label a representative set of correct and incorrect actions,
   especially wrong-argument same-tool cases, with two blind reviewers and
   adjudication. Rules can propose labels but are not human ground truth.
6. Report error-positive AUROC/AP, first-error top-1/top-3/MRR, false alarms,
   label coverage, exact denominators and reference access. Separate tool calls
   from exploratory messages; low support is not proof of an error.

The existing comparison scripts currently evaluate the historical Groq regime.
Fresh Qwen data require the manifest/split/teacher stage above before retraining.
Do not claim that launching collection has completed the new experiment.

## Cost and access

Ollama mode permits only loopback, rejects cloud-backed models, strips provider
credentials and disables dotenv loading. ASU mode allows only the exact free
ASU API endpoint and loads a separately supplied Voyager key. No paid model API is used.
Sol allocation/fairshare, storage and elapsed GPU time are consumed normally.
Credentials/MFA are not stored or requested in source files. The local key file
is ignored by git and excluded from cluster uploads.
