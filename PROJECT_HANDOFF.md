# Whole-project handoff — step-level-Pardha

This branch contains the implementation, experiment artifacts and local Phase 2 demo as of November 5, 2026.

## Start here

- Project overview and implementation: `README.md`.
- Current comparison: `results/fresh_refs_3_17/REFERENCE_CAP_COMPARISON.md`.
- Both settings and five real demonstration cases: `demo_ui/DEMO_REPORT.md`.
- Demo instructions: `demo_ui/README.md`. Open `demo_ui/dist/index.html` directly, or serve `demo_ui/dist/` with Python's HTTP server.
- Completed minimum-3/maximum-5 experiment: `results/fresh_all_tasks/`.
- Completed minimum-3/maximum-17 experiment: `results/fresh_refs_3_17/`.
- Main trajectory collection: `results/free_asu/main-qwen38-27b-serial-none/`.
- Exact frozen experiment input: `results/fresh_refs_3_17/input/results.json`.
- Implementation and automated checks: `gibs/`, `nibs/`, `collection/`.
- Earlier pilot, ablation and preflight artifacts are preserved under their original directories. Their statuses and dates distinguish them from completed experiments.

## Completed evidence

The dataset contains 1,000 trajectories across 50 Airline tasks, with 680 benchmark passes and 320 failures. Each reference-setting experiment has 860 eligible targets per teacher family, 24 GCN checkpoints, and held-out learned predictions for all 1,000 trajectories. The common reference-method comparison contains 911 trajectories. There are 48 GCN checkpoints across these two completed settings; additional historical checkpoints are also preserved.

The demo switches between both settings and includes actual graphs, successful references, MCS mappings/targets, per-step predictions and training histories. Its five example claims are verified against saved predictions. Human review remains pending, and these are paper-method adaptations to tau2 Airline rather than a reproduction of the original math/QA benchmarks.

## Credentials and local state

Credentials, environment files, virtual environments, local test caches, process locks and the local server PID file are excluded. `PUBLICATION_AUDIT.json` records any credential redactions applied to this publication copy. Original working files on the author's Mac were not modified by publication sanitization.

A publication redaction can change an affected historical metadata file's bytes; historical checksum records describe the original run artifact unless that file is explicitly listed as a sanitized publication. Scientific input snapshots and completed experiment artifacts retain their saved provenance where no credential redaction was needed.

The repository does not vendor frozen Hugging Face model caches or the external tau2-bench dependency. Follow the implementation READMEs and dependency requirements to recreate the environment. The recorded-results UI runs without model APIs or training.
