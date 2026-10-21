# Requirements: Stepwise Confidence Attribution (SCA) for Tool-Using Agents

## 1. Project summary

This is a research project testing whether the method from the paper *"Diagnosing Multi-step Reasoning Failures in Black-box LLMs via Stepwise Confidence Attribution"* (arXiv 2605.19228, ICML 2026) transfers from math/QA reasoning to **tool-using agents**.

**Paper's core idea:** sample the same task N=20 times, keep the runs that succeeded, and score each step of any run by how well it matches what the successful runs have in common. Steps that match the consensus are likely fine; steps that deviate are likely the error. The paper's simple, training-free version is called **NIBS**. The learned, graph-based version is **GIBS**.

**This project's question:** does the "successful runs share structure; failed runs deviate" assumption still hold when each step is a tool call plus an observation, in a multi-turn environment?

**Phase scope:** this document covers **Phase 1 (NIBS only)**. GIBS is out of scope until Phase 1 shows the consensus assumption holds.

## 2. Research questions

| ID | Question | How it is answered |
|---|---|---|
| RQ1 | Do successful runs overlap more with each other than failed runs do? | Distribution of per-run mean NIBS score, split by success vs failure |
| RQ2 | Do step scores locate the failing step better than baselines? | AUROC / AUCPR / ACC@80% / ECE and first-error detection against step labels |
| RQ3 | Does feedback on low-confidence steps help a retry? | Retry success rate, with step-level feedback vs "you failed" only (later phase) |
| RQ4 | When does the method break? | Compare results across tasks/domains by success rate, trajectory length, etc. |

**Phase 1 delivers RQ1 and RQ2. RQ3 and RQ4 are later phases**, but the data and code should be structured so they can be added.

## 3. Environment and data

### 3.1 Primary benchmark: τ²-bench

- Repo: `github.com/sierra-research/tau2-bench`. Domains: `airline` (50 tasks), `retail` (114/115 tasks), `telecom` (114 tasks).
- The repo includes tasks, databases and policies (the dataset) plus the simulator code. It does **not** ship a large set of ready-made trajectories; we generate them.
- Install per the repo README (`uv sync`, API keys in `.env`; it uses LiteLLM). Run via the `tau2 run` CLI, e.g. `tau2 run --domain airline --agent-llm <model> --user-llm <model> --num-trials N --num-tasks M`. Results are saved under `data/simulations/`.
- **Pin the exact commit/version used and record it in `results/run_metadata.json`.** The benchmark's tasks and graders have been revised over time, so scores from different versions are not comparable.
- **Do not assume the output JSON schema.** The first coding task is to inspect a real saved simulation file and write the parser against it (see 5.2).

### 3.2 Not in Phase 1

AppWorld, WebShop, ALFWorld, Who&When, TRAIL. They may be added later for contrast and validation.

## 4. Phases and compute

| Phase | Goal | Compute |
|---|---|---|
| 1a. Smoke test | Verify the pipeline end to end on a tiny sample | Groq free tier (or any free API) |
| 1b. Pilot | Measure per-task success rates; check model choice | Free GPU (Colab/Kaggle) or local model served with vLLM/Ollama |
| 1c. Main run | Full NIBS experiment | Decided after pilot |

**Free-tier constraint (important for 1a):** Groq's free tier is limited by tokens per minute and per day, and limits apply per organization (and per model). A τ²-bench conversation re-sends the policy, tool definitions and history on every LLM call, so a single conversation can consume a large share of a day's budget. The smoke test must therefore be tiny (e.g., 2–3 short tasks x 3–5 runs). Treat 1a as a pipeline check only, not as results.

**Rate-limit handling is required** (see 5.1): exponential backoff on HTTP 429, resumable runs.

## 5. Functional requirements

### 5.1 Run orchestration (`runner/`)

- R-1.1: A config file selects domain, task IDs, number of trials per task (N), agent model, user-simulator model, temperature, and max steps.
- R-1.2: Run the agent N times per task by wrapping the τ²-bench CLI or Python API (whichever is more robust). Default N=20 for real runs; N=3–5 for smoke tests.
- R-1.3: **Resumable:** skip any (task, trial) pair whose output file already exists; never re-run completed work after a crash or rate-limit stop.
- R-1.4: **Retry with exponential backoff** on rate-limit/transient errors; log each retry.
- R-1.5: Agent temperature defaults to 1.0 (matching the paper). The simulated user should be a fixed model at low temperature and kept identical across all runs of an experiment. Record both settings.
- R-1.6: Where feasible, enable tool-response caching/replay so identical tool calls return identical observations across trials of the same task. If not feasible in the environment, document this as a known confound.
- R-1.7: The agent model must support tool calling. Prefer a recent open-weight Qwen3-family model. Avoid Llama-3.1-8B as the agent (reported to fail nearly all agentic tasks in a separate evaluation).
- R-1.8: Log token usage per run so cost and rate-limit budgets can be estimated.

### 5.2 Trajectory parsing (`parsing/`)

Convert each raw τ²-bench simulation into a normalized trajectory (schema in section 6).

- R-2.1: Write the parser after inspecting a real output file. Document the raw schema you found in `docs/raw_schema.md`.
- R-2.2: Each **step** corresponds to one agent iteration: optional thought/message text, tool name, tool arguments, and the tool's observation.
- R-2.3: Agent messages to the user with no tool call are still steps (tool = `null`, with the message text).
- R-2.4: Only the **agent's decisions** (thought + tool call) are scored. Observations and simulated-user messages are stored as context, not scored.
- R-2.5: Record the final success/failure label from the environment's own grader, plus the reward value if one is given. If a reward is non-binary, record it and the threshold used for "success".
- R-2.6: Normalize arguments for comparison: lowercase strings, strip whitespace, canonicalize numbers and key order.
- R-2.7: Record **dependency edges** where detectable: step j depends on step i if a value in step j's arguments first appears in step i's observation. (Used by later phases and by the "milestone" ablation; implement now, use later.)

### 5.3 Similarity (`similarity/`)

Implement a pluggable similarity function `sim(step_a, step_b) -> float in [0, 1]`.

- R-3.1: **Tool similarity:** 0 if tool names differ; otherwise the fraction of argument keys whose normalized values match.
- R-3.2: **Text similarity** of the thought/message, with two interchangeable backends:
  - `cosine`: sentence/BERT embedding cosine similarity.
  - `nli`: entailment probability from an NLI model (the paper used a DeBERTa-MNLI model).
- R-3.3: **Hybrid:** `sim = alpha * tool_sim + (1 - alpha) * text_sim`. `alpha` is configurable; the experiment sweeps `alpha` in {0.5, 0.7, 1.0}. At `alpha = 1.0` the thought is ignored, which tests whether tool calls alone carry the signal.
- R-3.4: For steps with no tool call, fall back to text similarity only.
- R-3.5: Cache embeddings/NLI scores on disk keyed by text hash; NLI over many step pairs is the main compute cost.

### 5.4 NIBS scoring (`scoring/nibs.py`)

For a run R and the set S of successful runs of the same task:

1. Reference set = S minus R (**leave-one-out**; required, otherwise a successful run matches itself and scores 1.0).
2. For each scored step s in R and each reference run T: compute `best(s, T) = max over steps t in T of sim(s, t)` (Max variant) or the mean over t (Mean variant).
3. Step confidence = average of `best(s, T)` over all reference runs T.

- R-4.1: Support both `max` and `mean` aggregation (configurable).
- R-4.2: **Minimum references:** if a task has fewer than `k_min` successful runs after leave-one-out (default `k_min = 3`), skip the task and record it in `results/skipped_tasks.json` with the reason and the success count. Report the skipped fraction.
- R-4.3: Output one score per scored step, stored alongside the trajectory.
- R-4.4: Scoring is deterministic given the cached similarity values.
- R-4.5 (optional ablation): **milestone-conditioned matching**, where a step only matches reference steps that occur after the same already-completed milestone (e.g., after the user's record was fetched). Implement only after the basic version works.

### 5.5 Step labels (`labeling/`)

Ground truth for RQ2 comes from a judge, as in the paper, plus a human-checked subset.

- R-5.1: **LLM judge:** given the task description, policy, and the trajectory so far, return a binary label (1 = step is correct/acceptable, 0 = step is wrong) for each scored step. The judge model and prompt are configurable and versioned in `labeling/prompts/`.
- R-5.2: The judge should be told whether the run succeeded or failed, and be able to mark tool/observation failures separately from agent errors (label values: `ok`, `agent_error`, `tool_or_env_error`).
- R-5.3: Export a **human labeling sheet** (CSV) of a random sample of about 300 steps, containing the context and the judge's label, with an empty column for the human label. Provide a script that loads the completed sheet and reports judge-vs-human agreement (accuracy and Cohen's kappa).
- R-5.4: Report judge agreement with humans alongside all RQ2 results. (The original paper did not report this.)

### 5.6 Evaluation (`evaluation/`)

- R-6.1 **RQ1 diagnostic:** for every run, compute the mean step score; plot the distribution for successful vs failed runs (histogram or violin), and report the mean and a significance test (e.g., Mann-Whitney U) comparing the two. Also compute the pairwise overlap analogue where feasible.
- R-6.2 **RQ2 metrics**, computed over steps, treating label 0 (error) as the positive class where applicable:
  - AUROC
  - AUCPR
  - ACC@80% (accuracy of the steps remaining after removing the 20% lowest-confidence steps)
  - ECE (calibration, 10 bins)
- R-6.3 **First-error detection:** among failed runs, the fraction where the first step scored below a threshold matches the first step the judge labeled wrong (also report top-k variants).
- R-6.4 **Baselines** (same metrics):
  - random scores
  - "blame the last step"
  - mean token log-probability and token entropy per step, **only when using a local model that exposes logprobs**
  - LLM-as-judge confidence (optional)
- R-6.5 Report results overall and **broken down by**: domain, number of successful runs per task, and trajectory length. (This groundwork supports RQ4.)
- R-6.6 Save all figures and tables to `results/` as PNG and CSV.

## 6. Data schema

Normalized trajectory, one JSON file per (task, trial) at `data/trajectories/{domain}/{task_id}/{trial}.json`:

```json
{
  "task_id": "17",
  "domain": "airline",
  "trial": 4,
  "agent_model": "...",
  "user_model": "...",
  "temperature": 1.0,
  "success": false,
  "reward": 0.0,
  "steps": [
    {
      "idx": 0,
      "thought": "I need the user's reservations first",
      "tool": "get_user_details",
      "args": {"user_id": "sara_22"},
      "obs": "...",
      "depends_on": [],
      "scored": true
    }
  ],
  "meta": {"tokens_in": 0, "tokens_out": 0, "tau2_version": "<commit>"}
}
```

Scores are written to `data/scores/{domain}/{task_id}/{trial}.json` as a list of `{idx, score}` plus the config used (alpha, backend, aggregation).

## 7. Non-functional requirements

- **Language:** Python 3.10+. Use `uv` or `pip` with a pinned `requirements.txt` / `pyproject.toml`.
- **Reproducibility:** every result file records config, model names, seeds where applicable, and the τ²-bench version.
- **Resumability and caching** everywhere that calls an LLM or an NLI model.
- **Configuration:** one YAML config per experiment in `configs/`; no hard-coded model names or paths.
- **Secrets:** API keys in `.env` only; never committed. Provide `.env.example`.
- **Testing:** unit tests (pytest) for the parser, normalization, similarity, and NIBS scoring on small hand-made fixtures. Include a test that a successful run scored against itself is excluded (leave-one-out) and a test for the `k_min` skip rule.
- **Logging:** structured logs for run progress, retries and skipped tasks.
- **Readability:** type hints and short docstrings; a `README.md` with the exact commands for each phase.

## 8. Suggested repo layout

```
.
├── requirements.md
├── README.md
├── pyproject.toml
├── .env.example
├── configs/            # per-experiment YAML
├── runner/             # run orchestration, retry/backoff, resume
├── parsing/            # raw tau2 output -> normalized trajectory
├── similarity/         # tool, text (cosine/nli), hybrid
├── scoring/            # nibs.py
├── labeling/           # llm judge, human-sheet export/import
├── evaluation/         # metrics, plots, baselines
├── data/               # trajectories/, scores/, (gitignored)
├── results/            # figures, tables, skipped_tasks.json
├── docs/               # raw_schema.md, notes
└── tests/
```

## 9. Implementation order (milestones)

1. **Setup:** clone τ²-bench, install, confirm one task runs with a free API model. Save a raw output file.
2. **Inspect and parse:** document the raw schema; write the parser and normalizer; tests.
3. **Runner:** config-driven, resumable, with backoff; run the smoke test (2–3 tasks x 3–5 trials).
4. **Similarity + NIBS:** implement and unit-test; run on smoke-test data to confirm the code works (results not meaningful at this size).
5. **Pilot:** run about 10–20 tasks x 20 trials on a local/free-GPU model; compute per-task success counts and decide whether the model is in a usable success-rate range (see 10).
6. **Labeling:** LLM judge, then the human sheet for about 300 steps.
7. **Evaluation:** RQ1 plot and RQ2 metrics with baselines.
8. **Write-up of findings,** including skipped tasks and the breakdowns.

## 10. Acceptance criteria for Phase 1

- Pipeline runs end to end from config to results tables on at least one domain.
- **Pilot check:** the chosen agent model has a spread of per-task success counts, with a meaningful share of tasks having between `k_min` and N-1 successes out of N. If nearly all tasks are all-fail or all-succeed, change the model or domain before the main run.
- RQ1 plot and test are produced.
- RQ2 metrics are produced for NIBS (`max`/`mean`, `cosine`/`nli`, three `alpha` values) and for each baseline.
- Skipped-task statistics are reported.
- Judge-vs-human agreement is reported on the human-labeled subset.
- Unit tests pass.

## 11. Known risks and limitations (document in the final write-up)

- **Consensus is not correctness.** Valid but unusual strategies will score low; a popular wrong shortcut is not penalized if it also appears in successful runs.
- **Too few successes** on hard tasks removes them from the analysis. Hard tasks are exactly where failure diagnosis matters most.
- **Harmless detours** (exploration, recovery from errors) get low scores without being errors. Track whether low scores land on harmful steps or harmless ones.
- **Observation variation** between runs can add noise unless tool responses are cached.
- **Simulated user variation:** if the user simulator is not fixed, runs of the same task do not share the same input; log this as a factor.
- **The judge is an LLM,** which is the very kind of evaluator the original paper criticizes; hence the human-labeled subset.
- **Version drift:** τ²-bench tasks and graders change; pin the version.

## 12. Open questions for the developer to resolve (ask before assuming)

1. Exact raw output schema of τ²-bench simulations (see 5.2).
2. Whether tool-response caching/replay can be added cleanly to the environment (R-1.6).
3. Whether the benchmark reward is binary or partial in the chosen domains.
4. Which free/local agent model is available with working tool calling, and what its token limits are.
5. Which model to use for the simulated user and the labeling judge under free-tier limits.

## 13. Out of scope for Phase 1

GIBS (graph construction, MCS, GCN training), the retry-with-feedback experiment (RQ3), run-time intervention, process-reward-model training, and additional benchmarks (AppWorld, WebShop, ALFWorld, Who&When, TRAIL).

## 14. Reference

- Paper: *Diagnosing Multi-step Reasoning Failures in Black-box LLMs via Stepwise Confidence Attribution*, arXiv 2605.19228. NIBS definition: score a step by its (Max or Mean) similarity to steps in each correct sample, averaged across the correct samples, using BERT cosine or NLI entailment.
- Benchmark: `github.com/sierra-research/tau2-bench`.