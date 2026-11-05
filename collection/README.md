# Free tau2 trajectories

We generate new agent attempts, then evaluate whether paper NIBS/GIBS and C4
can locate their mistakes. The open-weight LLM generates conversations/tool calls;
it is not the GIBS confidence predictor. See [EVALUATION_PLAN.md](EVALUATION_PLAN.md).

The previous `run_tau2_gpu.py` uses a retired external endpoint and is not used.
The new `run_tau2.py` supports local Ollama and ASU Research Computing's free
hosted API. Paid endpoints are rejected. Local model downloads are public;
Sol GPU allocation/fairshare is still used for the Ollama option.

## ASU hosted API (avoids a dedicated GPU allocation)

ASU documents the service as free at [LLM API Access](https://docs.rc.asu.edu/ai/api/).
Create your key in Voyager, Profile → Keys, and save it in the ignored local
`.env.asu` file as `ASU_API_KEY=...`. Do not put the key in a command or report.
The key is absent from CLI arguments and collection manifests.

```bash
python3 run_tau2.py --backend asu --list-models
```

Choose one active chat model advertising function calling and at least 32,768
context tokens, then use its exact catalog ID below:

```bash
python3 run_tau2.py --backend asu --model CATALOG_MODEL_ID \
  --tasks 13 --trials 1 --require-tool-smoke \
  --output results/free_asu/smoke
```

The selected hosted model and actual pilot settings are recorded in
[ASU_RUN_PLAN.md](ASU_RUN_PLAN.md). The hosted route first uses 10 tasks × 1
attempt as an engineering gate; use all 50 tasks × 20 trials for the subsequent
1,000-trajectory main target, in another output directory.
Only ASU's exact `https://openai.rc.asu.edu/v1` endpoint is permitted in this mode.
Gateway add-ons are disabled and a fixed catalog model is required (`auto` is
rejected). Catalog metadata are saved; hosted immutable weight digests are not
exposed, so revision reproducibility is weaker than local Ollama.

## Current Sol paths

- User/account: `ppudi`, `class_cse598fall2026`, QoS `class`.
- Root: `/scratch/ppudi/sca-free/`.
- Source snapshot: `project/`; separate pinned benchmark: `tau2-bench/`.
- Client Python: `tau2-bench/.venv/bin/python`; Ollama module: `ollama/0.30.3`.
- Outputs: `outputs/smoke-qwen3-8b`, `outputs/pilot-qwen3-8b`, `outputs/full-qwen3-8b`.
- Logs: `logs/setup-<job>.log`, `collect-<job>.log`, `ollama-<job>.log`.

## Submit and monitor

Connect through the ASU VPN, then `ssh sol`. After copying this project snapshot:

```bash
cd /scratch/ppudi/sca-free/project
sbatch collection/sol_setup.sbatch
```

Once the setup finishes, submit a smoke job (short allocation override):

```bash
sbatch --time=00:30:00 --export=ALL,MODE=smoke collection/sol_collect.sbatch
```

After smoke passes, use `MODE=pilot` for 150 attempts or `MODE=full` for the
1,000-attempt target. They are separate datasets. Repeat the same job mode/path
to resume; do not change model weights or generation settings in an existing run.

```bash
sbatch --export=ALL,MODE=pilot collection/sol_collect.sbatch
sbatch --export=ALL,MODE=full collection/sol_collect.sbatch
squeue -u ppudi
```

Only submit the desired next job; the commands above illustrate the modes,
not a requirement to launch them concurrently. The runner locks its output path
to prevent simultaneous writers. The wrapper archives results containing
infrastructure errors before native resume retries them. Slurm checkpoints completed trajectories when
interrupted; the next invocation resumes using tau2's recorded seeds.

```bash
/scratch/ppudi/sca-free/tau2-bench/.venv/bin/python run_tau2.py \
  --output /scratch/ppudi/sca-free/outputs/full-qwen3-8b --status
```

The model server is bound to loopback and started only inside the GPU allocation.
Its process is stopped when the job exits. The script records the immutable
model digest and refuses to resume with changed settings/weights. Smoke checks
require one graded trajectory, a tool call and graph-parser compatibility.

## Local use and dry run

```bash
python3 run_tau2.py --tau2-dir ../tau2-bench \
  --output /tmp/sca-collection-plan --dry-run
```

For a local model already installed in Ollama, start `ollama serve`, then provide
its exact local tag and loopback address. For example, Qwen3 4B fits this Mac
more comfortably than the 8B Sol model; record that as a separate regime/output.

```bash
python3 run_tau2.py --tau2-dir ../tau2-bench --model qwen3:4b \
  --tasks 13 --trials 1 --require-tool-smoke \
  --output /tmp/sca-local-smoke
```

The collection wrapper itself uses only Python's standard library. Actual
simulation runs use the benchmark's isolated Python environment.

## After generation

Inspect `collection_summary.json` and the result trajectories before scaling.
Run the separate audit to flag parser failures, duplicates and rewarded runs
missing expected tool names:

```bash
python3 -m collection.audit results/free_asu/pilot-qwen38-27b
```

These flags preserve the official reward and do not supply human step labels.
Do not claim that all failed runs contain an identifiable incorrect executed
action. The new Qwen regime needs fresh graph targets and independent evaluation
labels; old Groq consensus masks do not apply to its new trajectories.

Tests (no model calls): `python3 -m unittest collection.test_collection -v`.

Official operational references: [ASU Ollama guide](https://docs.rc.asu.edu/ollama/),
[resource requests](https://docs.rc.asu.edu/requesting-resources/), and
[partitions/QoS](https://docs.rc.asu.edu/partitions-and-qos/).
