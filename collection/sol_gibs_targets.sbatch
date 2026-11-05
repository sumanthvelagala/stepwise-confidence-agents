#!/usr/bin/env bash
#SBATCH --job-name=sca-mcs-all50
#SBATCH --account=class_cse598fall2026
#SBATCH --partition=public
#SBATCH --qos=class
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/ppudi/sca-free/logs/mcs-%j.log
set -euo pipefail
SCA_ROOT=/scratch/ppudi/sca-free
SCA_PY=/scratch/ppudi/vllm-stack/env-engine/bin/python
cd "$SCA_ROOT/project"
export HF_HOME="$SCA_ROOT/hf-cache"
export HF_HUB_OFFLINE=1
export STEPWISE_NLI_CACHE="$SCA_ROOT/nli-cache-cuda"
export NVIDIA_TF32_OVERRIDE=0
export PYTHON_DOTENV_DISABLED=1
export OMP_NUM_THREADS=2
mkdir -p "$STEPWISE_NLI_CACHE"
exec 9>results/fresh_all_tasks/.targets.lock
flock -n 9 || { echo 'Another target writer is active.' >&2; exit 2; }
"$SCA_PY" - <<'PY'
from pathlib import Path
import json,hashlib,importlib.metadata as md
import torch
from gibs.mcs.nli import DebertaEntailment
torch.set_num_threads(2)
plan=json.loads(Path('results/fresh_all_tasks/plan.json').read_text())
sources={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in plan['execution_source_sha256']}
assert sources==plan['execution_source_sha256'],'Prepared code changed before GPU execution'
assert torch.cuda.is_available(),'GPU allocation has no visible CUDA device'
torch.set_float32_matmul_precision('highest')
m=DebertaEntailment(device='cuda',batch_size=16,cache_dir=None,overlength='truncate')
pairs=[('The reservation was cancelled.','The reservation was cancelled.'),
       ('The reservation was cancelled.','The reservation was not cancelled.')]
gpu=m.entail_batch(pairs)
m.model.to('cpu');m.device='cpu';m.cache={}
cpu=m.entail_batch(pairs)
assert max(abs(a-b) for a,b in zip(gpu,cpu))<5e-4,(gpu,cpu)
assert gpu[0]>gpu[1],gpu
runtime={'job_id':__import__('os').environ['SLURM_JOB_ID'],'device':torch.cuda.get_device_name(),
         'versions':{p:md.version(p) for p in ['torch','transformers','numpy','networkx']},
         'execution_source_sha256':sources,'snapshot_sha256':plan['snapshot_sha256'],
         'nli':m.describe(),'gpu_smoke_probabilities':gpu,'cpu_smoke_probabilities':cpu,
         'cpu_cuda_parity':True,'primary_teacher_cache':'fresh CUDA cache; Mac masks are not mixed in'}
p=Path('results/fresh_all_tasks/sol_runtime.json');p.write_text(json.dumps(runtime,indent=2)+'\n')
p.with_name('sol_runtime-'+runtime['job_id']+'.json').write_text(json.dumps(runtime,indent=2)+'\n')
print(json.dumps(runtime),flush=True)
PY
child_pid=''
stop_job() {
  if [ -n "$child_pid" ]; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" || true
  fi
  exit 143
}
trap stop_job TERM INT
"$SCA_PY" -u -m gibs.fresh.experiment targets --nli-device cuda --nli-batch-size 16 \
  --output "$SCA_ROOT/project/results/fresh_all_tasks" &
child_pid=$!
wait "$child_pid"
