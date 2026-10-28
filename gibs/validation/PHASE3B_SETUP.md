# Phase 3B: environment setup for Groq-based collection (preparation only)

**Status: nothing has been installed, no API call has been made, no trajectory has been generated.**

**Network use so far:** only unauthenticated reads of public pages:
- the τ²-bench GitHub repository (commit metadata, `pyproject.toml`, `uv.lock`, `.gitignore`, CLI source);
- Groq's public documentation.

## 1. What the existing runs used (from non-secret metadata in all 27 results files)

| Setting | Groq runs (24 files; T = 0 regime) | Old GPU runs (3 files; **endpoint disabled**) |
|---|---|---|
| τ²-bench `git_commit` | `5bfa7e37b36656b37dc6d022156be6563c1007f3` (2026-09-28), all files | same |
| Package | `tau2` 1.0.1; Python ≥ 3.12, < 3.14; `uv.lock` pins `litellm` 1.81.11 | same |
| Agent / user implementation | `llm_agent` / `user_simulator` | same |
| Agent model, temperature | `groq/openai/gpt-oss-20b`, **0.0** | `openai/gpt-oss:20b`, 1.0 |
| User model, temperature | `groq/openai/gpt-oss-20b`, 0.0 | `openai/gpt-oss:20b`, 0.0 |
| `max_steps` / `max_errors` | 200 / 10 | 50 / 10 |
| Seed | 42 (Oct 2 batches) or 300 (later batches; the CLI default) | 300 |
| Airline policy text | sha256 `10dc05254215…`, identical in all files | same |
| User-simulator guidelines | sha256 `740a29dfa64d…`, identical | same |
| `llm_args` recorded in output | `{"temperature": …}` only | **also `extra_headers` containing the X-API-Key**, which is how the key leaked |

- **Optional LLM features were not used:** `review`, `hallucination_check` and `auth_classification` are null in all
  470 simulations, so no extra LLM calls were made.
- **Usage was recorded:** messages carry token `usage`. The recorded `cost` is 0 because the cost table has no price
  for this model; **it is not evidence of free usage.**

## 2. Groq model facts (public docs, checked 2026-10-27)

| Item | Value |
|---|---|
| Model ID | `openai/gpt-oss-20b`, production model, no deprecation notice. τ²-bench addresses it through litellm as `groq/openai/gpt-oss-20b`, the identifier the earlier runs used |
| Tool calling | **supported**; **parallel tool calls not supported**. That is consistent with τ²-bench airline and with our step-graph builder, which rejects parallel calls |
| Price | **$0.075 per million input tokens and $0.30 per million output tokens.** Not free on paid plans |
| Free-plan limits | 30 requests/min, 1,000 requests/day, **8K tokens/min, 200K tokens/day** |
| Developer-plan limits (model page) | 250K tokens/min, 1K requests/min. Daily caps were not stated; check the account dashboard |
| Rate-limit signalling | HTTP 429 with `retry-after`; `x-ratelimit-*` headers |

## 3. Usage and cost estimate (from recorded usage; agent temperature 0 runs)

| Task | Prompt tokens / sim (mean) | Completion tokens / sim (mean) |
|---|---|---|
| 7 | 47,093 | 4,607 |
| 8 | 48,956 | 5,428 |
| 21 | 35,748 | 3,260 |
| 29 | 73,570 | 5,055 |
| 33 | 87,473 | 11,097 |
| 35 | 83,953 | 7,941 |
| 42 | 57,007 | 3,453 |

- **Stage 0 (10 simulations per task, 70 in total):** about **4.3M prompt + 0.41M completion tokens**, i.e. about
  **$0.45 at list price**.
- [EST] Allowing ×2 for longer temperature-1.0 dialogues and infrastructure retries: **≤ about $1**.
- **Smoke test (1 simulation, Task 13):** about 15K prompt + 1.6K completion tokens, i.e. about **$0.002**.

**Rate-limit fit:**
- **Free plan: not feasible.** One simulation uses 50–100K tokens, so 200K tokens/day allows only about 2–4
  simulations per day, and 8K tokens/min would trigger 429s inside a single simulation.
- **Developer plan: fits.** It allows 250K tokens/min and 1K requests/min with sequential runs
  (`--max-concurrency 1`).
- **Action needed: confirm which plan the Groq account is on** (§7).

## 4. Installation (isolated; outside this repository)

```bash
# 1. uv (package manager required by tau2 1.0.1)
brew install uv

# 2. τ²-bench at the exact commit used for all existing runs, as a sibling of this repo
cd ~/Desktop/AA/Project
git clone https://github.com/sierra-research/tau2-bench.git
cd tau2-bench
git checkout 5bfa7e37b36656b37dc6d022156be6563c1007f3

# 3. Isolated environment from the lock file (core only: text-mode airline), using the local Python 3.13
uv sync --frozen --python /opt/homebrew/bin/python3.13

# 4. Sanity check (no API calls)
uv run tau2 --help
uv run python -c "import tau2, litellm; print(tau2.__file__, litellm.__version__)"   # expect litellm 1.81.11
```

Why this layout:
- `--frozen` installs exactly the pinned dependency set; nothing is re-resolved.
- The environment lives in `tau2-bench/.venv`, separate from the GIBS `.venv`.
- The sibling location matches the README's `../tau2-bench` layout.
- Upstream `.gitignore` already ignores `.env` and `data/simulations/*`.

## 5. Credentials

- **Groq.** Create `~/Desktop/AA/Project/tau2-bench/.env` **yourself**, containing a single line:
  `GROQ_API_KEY=<your key>`. It is outside this repository and ignored upstream. I will not read or print it, except
  through the checker in §6, which only tests for its presence in output files.
- **Pass the key only through the environment, never in `--agent-llm-args`.** τ²-bench writes `llm_args` verbatim
  into `results.json`, which is how the GPU key leaked.
- **Unset other provider keys during runs** (`env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY …`). An unexpected call to
  a default OpenAI model then fails instead of being billed. τ²-bench's NL-assertion and env-interface defaults are
  `gpt-4.1`, but airline reward is DB + COMMUNICATE, and existing runs show no such calls.
- **GPU endpoint: disabled.**
  - Do not use `run_tau2_gpu.py`, `GPU_API_KEY` or `GPU_API_BASE`.
  - **Outstanding security action:** the exposed X-API-Key (public repository, commit `184159b`,
    `results/probe/task_{2,4,5}/results.json`) must be **revoked by the endpoint administrator and the revocation
    confirmed**.
  - Purging it from public git history is a separate decision for the repository owners.

## 6. Smoke test (1 simulation; needs your approval because it is a paid call on non-free plans)

> **Superseded:** use the command in §9. Run `.venv/bin/tau2`, not `uv run tau2`, because the installation needed
> one package outside the lock (§8).

**Task 13** is short (8–10 messages), makes a tool call (`transfer_to_human_agents`), and is **not in any Phase 2 or
Phase 3 evaluation split**. The smoke-test output is excluded from every dataset.

```bash
cd ~/Desktop/AA/Project/tau2-bench
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY \
  uv run tau2 run \
    --domain airline \
    --agent-llm groq/openai/gpt-oss-20b --agent-llm-args '{"temperature": 1.0}' \
    --user-llm  groq/openai/gpt-oss-20b --user-llm-args  '{"temperature": 0.0}' \
    --task-ids 13 --num-trials 1 \
    --max-concurrency 1 --max-steps 200 --max-errors 10 --seed 300 \
    --save-to phase3b_smoke_task13 --auto-resume
```

- **Output:** `tau2-bench/data/simulations/phase3b_smoke_task13/results.json`, outside this repository. The CLI help
  states this location; the run confirms it.
- **Post-run check (no API calls; exit code 1 on any secret):**

```bash
cd ~/Desktop/AA/Project/stepwise-confidence-agents
.venv/bin/python -B gibs/validation/phase3b_check_run.py \
  ../tau2-bench/data/simulations/phase3b_smoke_task13/results.json --env ../tau2-bench/.env
```

  It verifies:
  - the Groq key is absent from the file;
  - no credential markers are present;
  - `llm_args` = `{temperature}` only;
  - commit, models, temperatures (agent 1.0, user 0.0), steps, errors, seed and policy hash;
  - recorded token usage and the list-price cost.

  It was tested on existing files: it passes a Groq run and **fails** the leaked GPU-run files without printing the
  secret.
- **Copy rule:** only a file that passes is copied into the repository, under `results/phase3b/smoke/`, and labelled
  as a smoke test.

**Smoke-test success criteria:**
- the simulation ends with `user_stop` (or a reward), not `infrastructure_error`;
- it contains at least one tool call;
- recorded `llm` and temperatures are as above;
- the checker passes;
- recorded usage is within 2× of the estimate.

## 7. Information or action needed from you before the smoke test

1. **Groq plan and limits.** Free or Developer, the account's daily caps, and approval of the spend: about $0.002
   for the smoke test; about $0.5–1 for Stage 0 later.
2. **Create `tau2-bench/.env` with `GROQ_API_KEY`** after I run steps 1–4 of §4, or tell me to proceed with the
   install first.
3. **Approve the installation** in §4 (Homebrew `uv`; clone into `~/Desktop/AA/Project/tau2-bench`).
4. **Choose the user-simulator temperature.** I propose 0.0, as in every earlier run; only the agent temperature
   changes to 1.0.
5. **Choose the seed.** I propose 300, the CLI default used by most earlier batches. Repeated trials of one task
   differ through agent sampling at temperature 1.0.
6. **Security, outstanding:** confirmation that the old GPU endpoint key has been revoked. It does not block
   Groq-only work, but remains open.

Stage-0 collection (70 simulations) will **not** start until the smoke test passes and you approve it. The
collection wrapper must be resumable, sequential, use backoff on 429, and cap at 10 simulations per task. It will be
written and shown to you before use.

---

## 8. Installation log (2026-10-27; approved settings; no provider API calls)

| Step | Result |
|---|---|
| `brew install uv` | uv 0.13.6 |
| Clone and checkout | `~/Desktop/AA/Project/tau2-bench` @ `5bfa7e37b36656b37dc6d022156be6563c1007f3`, clean |
| `uv sync --frozen` on Python 3.13 | installed, **but `import tau2` failed**: (1) `websockets` is imported unconditionally, though it is only in the `voice` extra; (2) **`audioop` was removed from the Python 3.13 standard library**, and the lock has no `audioop-lts` |
| **Deviation 1: interpreter** | the environment was rebuilt with `uv sync --frozen --python /opt/anaconda3/bin/python3.12` (local CPython 3.12.7; isolated `.venv`). Python 3.12 is inside the declared range (≥ 3.12, < 3.14) |
| **Deviation 2: one extra package** | `uv pip install websockets==15.0.1`, **the version pinned in `uv.lock`**. The full `voice` extra (68 packages, including native PyAudio) was **not** installed |
| Verification | `tau2` 1.0.1, `litellm` 1.81.11; airline domain, `llm_agent` and `user_simulator` registered; LLM cache disabled; defaults: max steps 200, max errors 10, seed 300; `tau2 run --help` lists every required option |
| Benchmark identity (offline) | installed airline `policy.md` sha256 `10dc05254215…` = the recorded runs. **All 49 recorded tasks have identical gold actions, reward basis, NL assertions and user instructions** |
| No network needed | `import tau2` and `tau2 run --help` succeed with all HTTP(S) traffic routed to a dead local proxy. `LITELLM_LOCAL_MODEL_COST_MAP=True` stops litellm from downloading its price map |
| Credentials | `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GPU_API_KEY`, `GPU_API_BASE` and `OPENAI_API_BASE` are all unset. No `.env` exists. `.env` is ignored by upstream `.gitignore` |
| Template | `tau2-bench/.env.phase3b.template` contains only `GROQ_API_KEY=YOUR_KEY_HERE`. It is git-ignored through the clone's local `.git/info/exclude`; no tracked file changed |
| Secret scanner | 24 / 24 clean Groq results files pass (no false positives). 3 / 3 leaked GPU-run files fail. A planted fake key is detected through both the environment variable and `--env` paths, and **is not printed** |

**Important consequence of deviation 2:** run τ²-bench with **`.venv/bin/tau2`**, **not** `uv run tau2`. `uv run`
re-syncs the environment to the lock and would remove `websockets`.

## 9. Smoke-test command (awaiting approval; 1 simulation of Task 13, about $0.002 at list price)

```bash
cd ~/Desktop/AA/Project/tau2-bench
# prerequisite: create .env from .env.phase3b.template with your real key (by you)
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u GPU_API_KEY -u GPU_API_BASE -u OPENAI_API_BASE \
    LITELLM_LOCAL_MODEL_COST_MAP=True \
  .venv/bin/tau2 run \
    --domain airline \
    --agent-llm groq/openai/gpt-oss-20b --agent-llm-args '{"temperature": 1.0}' \
    --user-llm  groq/openai/gpt-oss-20b --user-llm-args  '{"temperature": 0.0}' \
    --task-ids 13 --num-trials 1 \
    --max-concurrency 1 --max-steps 200 --max-errors 10 --seed 300 \
    --save-to phase3b_smoke_task13 --auto-resume

cd ~/Desktop/AA/Project/stepwise-confidence-agents
.venv/bin/python -B gibs/validation/phase3b_check_run.py \
  ../tau2-bench/data/simulations/phase3b_smoke_task13/results.json --env ../tau2-bench/.env
```

## 10. Reproducible bootstrap and final pre-smoke verification (2026-10-27; no API calls, no simulations)

**Bootstrap script:** `bash gibs/validation/phase3b_bootstrap.sh`, with `TAU2_DIR` and `PY312` overridable. It:
1. clones τ²-bench if absent and checks out `5bfa7e37…` detached; it **refuses to continue if tracked upstream files
   are modified**;
2. verifies the sha256 of `uv.lock` (`6404e490…`) and `pyproject.toml` (`3c718fbc…`);
3. runs `uv sync --frozen` on CPython 3.12, an exact sync that removes anything not in the lock;
4. installs `websockets==15.0.1` with **`--require-hashes`, using the hashes recorded in `uv.lock`**;
5. verifies imports **offline**: provider keys unset, HTTP(S) routed to a dead proxy, versions asserted;
6. creates the placeholder-only template, git-ignored through `.git/info/exclude`. It never reads or writes `.env`.

**Idempotency:**
- Runs 1 and 2 on the existing environment, and run 3 after deleting `.venv`, produce **identical `uv pip freeze`
  output** (76 packages).
- HEAD = `5bfa7e37…`; 0 tracked upstream files modified.
- Python 3.12.7, tau2 1.0.1, litellm 1.81.11, websockets 15.0.1.

**Explicit temperatures.** The smoke-test arguments were parsed by τ²-bench's own `add_run_args` parser, offline:

| Argument | Parsed value |
|---|---|
| `agent_llm` | `groq/openai/gpt-oss-20b` |
| `agent_llm_args` | `{'temperature': 1.0}` |
| `user_llm` | `groq/openai/gpt-oss-20b` |
| `user_llm_args` | `{'temperature': 0.0}` |
| `task_ids` | `['13']` |
| `max_steps` / `max_errors` / `seed` | 200 / 10 / 300 |
| `save_to` | `phase3b_smoke_task13` |

Without the flags, the agent would default to temperature 0.0. Output path: `DATA_DIR/simulations/<save_to>/results.json`
= `tau2-bench/data/simulations/phase3b_smoke_task13/results.json`, ignored upstream (`data/simulations/*`).

**Checker** (`phase3b_check_run.py`):
- **Exit codes:** 0 = secrets and configuration pass; 1 = secret failure; 2 = configuration mismatch.
- **Configuration checked:** agent **and** user model and temperature, commit, steps, errors, seed, policy hash, and
  `llm_args` containing exactly `temperature`, for both agent and user.

The tests below use synthetic checker fixtures, edited copies of an existing file that were deleted after testing:

| Case | Exit |
|---|---|
| legitimate Phase-3B-configured file | **0** |
| same, with an infrastructure-error simulation | **0** |
| wrong user temperature | 2 |
| extra `llm_args` key | 2 |
| wrong user model | 2 |
| missing user temperature | 2 |
| 24 existing temperature-0 Groq files | 2 each (configuration only; **0 secret false positives**) |
| 3 leaked GPU files | 1 each |
| planted fake key (environment and `--env`) | detected; value never printed |

Limitation: an explicit user temperature of 0.0 is recorded identically to the default. Explicitness is guaranteed by
the command, not by the output.
