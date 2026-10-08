# Step-Level Confidence Estimation for LLM Agents

**CSE598 Capstone — Team 11**

Adapting NIBS (Naive Influence-Based Scoring) from the paper [*Diagnosing Multi-step Reasoning Failures in Black-box LLMs via Stepwise Confidence Attribution*](https://arxiv.org/abs/2605.19228) (ICML 2026) to tool-using LLM agents evaluated on tau2-bench.

---

## Repo structure

```
nibs/
├── parsing/parser.py        # parse tau2-bench results.json → trajectory dicts
├── scoring/nibs.py          # NIBS algorithm (leave-one-out, best_match, score_task)
├── similarity/similarity.py # tool_sim, text_sim, hybrid_sim
├── tests/                   # unit tests (no API calls required)
└── run_nibs.py              # CLI entry point

results/
├── pilot/
│   ├── tasks_1_3_9_38/results.json    # 20-trial runs — tasks 1,3,9,38
│   └── tasks_25_40_48/results.json    # 20-trial runs — tasks 25,40,48
├── probe/
│   ├── batch_1action/results.json     # 3-trial probe — tasks 5,6,11,15,19,24
│   ├── batch_2action/results.json     # 3-trial probe — tasks 1,3,9,14,21,38
│   ├── batch_3to4action/results.json  # 3-trial probe — tasks 2,17,22,23,29,37
│   ├── new_batch1/results.json        # 3-trial probe — tasks 13,16,20,25,27,35
│   ├── new_batch2/results.json        # 3-trial probe — tasks 36,40,45,47,48,49
│   ├── remaining_batch/results.json   # 3-trial probe — tasks 4,10,12,18,26,28,30,31,34,39,41,42,43,46
│   └── ratelimit_tasks/results.json   # 3-trial probe — tasks 34,35,42,44,45 (sequential retry)
└── nibs_all_tasks.json                # NIBS scores output

docs/
└── diagnostic_agent_design.md          # design doc for future diagnostic agent
```

---

## Dependencies

**Core NIBS code** — standard library only. No pip installs required.

**To collect trajectories** — tau2-bench + a Groq API key.

**To run tests** — pytest only.

```bash
pip install pytest
```

---

## Setup

### 1. Clone this repo

```bash
git clone <repo-url>
cd <repo>
```

### 2. Install tau2-bench

tau2-bench is the benchmark framework. It is not included in this repo.

```bash
git clone https://github.com/sierra-research/tau2-bench
cd tau2-bench
pip install -e ".[dev]"
cd ..
```

Verify:
```bash
tau2 --help
```

### 3. Set up API key

Create `tau2-bench/.env`:
```
GROQ_API_KEY=your_groq_key_here
```

Get a free key at [console.groq.com](https://console.groq.com). We use `groq/gpt-oss-20b` — cheapest model with reliable tool calling.

---

## Collecting trajectories

### Probe phase — find tasks with variance

NIBS requires tasks where the model sometimes passes and sometimes genuinely fails. Run 3 trials on a batch of tasks first:

```bash
cd tau2-bench
tau2 run \
  --agent-llm groq/gpt-oss-20b \
  --user-llm groq/gpt-oss-20b \
  --domain airline \
  --task-ids 1 2 3 4 5 6 \
  --num-trials 3 \
  --save-to probe_batch1
```

Results saved to `tau2-bench/data/simulations/probe_batch1/results.json`.

Check results — keep only tasks with both `reward=1.0` and `reward=0.0` runs. Drop tasks that always pass, always fail, or have all infrastructure errors (`reward=None`).

### Pilot phase — 20 trials on selected tasks

```bash
tau2 run \
  --agent-llm groq/gpt-oss-20b \
  --user-llm groq/gpt-oss-20b \
  --domain airline \
  --task-ids 3 9 25 40 48 \
  --num-trials 20 \
  --save-to pilot_tasks_main
```

> **Note:** tau2-bench prompts before overwriting an existing results file. Use a new `--save-to` name each run or delete the old file first.

### Reward values

| Value | Meaning |
|---|---|
| `1.0` | Genuine pass |
| `0.0` | Genuine fail |
| `None` | Infrastructure error — model returned empty/malformed response. Excluded from NIBS automatically. |

---

## Running NIBS

```bash
cd nibs
python run_nibs.py \
  ../tau2-bench/data/simulations/pilot_tasks_main/results.json \
  --aggregation max \
  --k-min 3 \
  --output ../results/nibs_scores.json
```

Pass multiple files to merge tasks across runs:

```bash
python run_nibs.py \
  ../results/pilot/tasks_1_3_9_38/results.json \
  ../results/pilot/tasks_25_40_48/results.json \
  --output ../results/nibs_all_tasks.json
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--aggregation` | `max` | How best_match aggregates — `max` or `mean` |
| `--k-min` | `3` | Minimum successful runs to score a task |
| `--output` | None | Save full scored results as JSON |

### Example output

```
Tasks: ['3', '9', '25', '40', '48']

Task 3:  successes=8  fails=9
  avg score — success: 0.852  fail: 0.849  gap: +0.003

Task 40: successes=18  fails=2
  avg score — success: 1.000  fail: 0.800  gap: +0.200
```

---

## Running tests

```bash
cd nibs
python -m pytest tests/ -v
```

All tests run without API calls.

---

## How NIBS works

For each task with N runs (some pass, some fail):

1. **Reference set** — for run R, the reference set is all successful runs except R (leave-one-out)
2. **best_match(step, ref_run)** — similarity of a step against all steps in one reference run, aggregated by max or mean
3. **step_confidence(step)** — average of best_match across all reference runs
4. **Similarity** — `tool_sim`: 0.0 if tool names differ, else fraction of matching argument values. No model downloads needed.

A low step_confidence flags a step as anomalous relative to what successful runs did.

---

## Results

| Task | Gap (success − fail) | Interpretation |
|------|----------------------|----------------|
| 40 | +0.200 | NIBS pinpoints exact failing step (step 4, score=0.0) |
| 25 | +0.140 | Clear separation |
| 9  | +0.121 | Clear separation |
| 3  | +0.003 | Near zero — failures are policy-level, not tool-selection errors |
| 48 | -0.029 | Reversed — agent uses correct tools but fails at reasoning. Reveals limit of tool_sim, motivates GIBS |
