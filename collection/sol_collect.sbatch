#!/usr/bin/env bash
#SBATCH --job-name=sca-tau2-free
#SBATCH --account=class_cse598fall2026
#SBATCH --partition=public
#SBATCH --qos=class
#SBATCH --gres=gpu:a100.20gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --signal=B:TERM@120
#SBATCH --output=/scratch/ppudi/sca-free/logs/collect-%j.log
set -euo pipefail

SCA_ROOT="${SCA_ROOT:-/scratch/ppudi/sca-free}"
MODEL="${MODEL:-qwen3:8b}"
MODE="${MODE:-smoke}"
CLIENT="$SCA_ROOT/tau2-bench/.venv/bin/python"
module load ollama/0.30.3
export OLLAMA_MODELS="$SCA_ROOT/ollama-models"
export OLLAMA_NO_CLOUD=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_CONTEXT_LENGTH=32768
export OLLAMA_KEEP_ALIVE=30m
PORT="$($CLIENT -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
export OLLAMA_HOST="127.0.0.1:$PORT"
mkdir -p "$SCA_ROOT/logs" "$OLLAMA_MODELS"
ollama serve > "$SCA_ROOT/logs/ollama-$SLURM_JOB_ID.log" 2>&1 &
SERVER_PID=$!
COLLECT_PID=""
cleanup() {
  if [ -n "$COLLECT_PID" ]; then
    kill -TERM "$COLLECT_PID" 2>/dev/null || true
    wait "$COLLECT_PID" 2>/dev/null || true
  fi
  kill -TERM "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT TERM INT
for _attempt in $(seq 1 60); do
  kill -0 "$SERVER_PID" || exit 1
  if curl --silent --fail "http://$OLLAMA_HOST/api/tags" >/dev/null; then break; fi
  sleep 2
done
curl --silent --fail "http://$OLLAMA_HOST/api/tags" >/dev/null
ollama pull "$MODEL"
ARGS=(--tau2-dir "$SCA_ROOT/tau2-bench" --base-url "http://$OLLAMA_HOST" --model "$MODEL")
if [ "$MODE" = smoke ]; then
  ARGS+=(--tasks 13 --trials 1 --simulation-timeout 600 --require-tool-smoke --output "$SCA_ROOT/outputs/smoke-qwen3-8b")
elif [ "$MODE" = pilot ]; then
  ARGS+=(--trials 3 --output "$SCA_ROOT/outputs/pilot-qwen3-8b")
elif [ "$MODE" = full ]; then
  ARGS+=(--trials 20 --output "$SCA_ROOT/outputs/full-qwen3-8b")
else
  printf 'Unknown MODE: %s\n' "$MODE" >&2
  exit 1
fi
"$CLIENT" "$SCA_ROOT/project/run_tau2.py" "${ARGS[@]}" &
COLLECT_PID=$!
wait "$COLLECT_PID"
COLLECT_PID=""
