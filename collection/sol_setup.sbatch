#!/usr/bin/env bash
#SBATCH --job-name=sca-tau2-setup
#SBATCH --account=class_cse598fall2026
#SBATCH --partition=public
#SBATCH --qos=class
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/ppudi/sca-free/logs/setup-%j.log
set -euo pipefail

SCA_ROOT="${SCA_ROOT:-/scratch/ppudi/sca-free}"
PY312="${PY312:-/scratch/ppudi/vllm-stack/env-router/bin/python}"
TAU2_DIR="$SCA_ROOT/tau2-bench"
COMMIT=5bfa7e37b36656b37dc6d022156be6563c1007f3
mkdir -p "$SCA_ROOT"
"$PY312" -c 'import sys; assert sys.version_info[:2] == (3, 12)'
if [ ! -x "$SCA_ROOT/setup-env/bin/python" ]; then
  "$PY312" -m venv "$SCA_ROOT/setup-env"
fi
source "$SCA_ROOT/setup-env/bin/activate"
python -m pip install --quiet uv==0.10.11
if [ ! -d "$TAU2_DIR/.git" ]; then
  git clone --quiet https://github.com/sierra-research/tau2-bench.git "$TAU2_DIR"
fi
cd "$TAU2_DIR"
test -z "$(git status --porcelain --untracked-files=no)"
git checkout --quiet --detach "$COMMIT"
python - <<'PY'
import hashlib
from pathlib import Path
for path, expected in {'uv.lock':'6404e490ae418d1d62afda97641605dab1684c2b830b6b3de34e7685ef2153c7',
                       'pyproject.toml':'3c718fbc3c1e350a4e36b465fee8f33db34eae75c97a18880cef46c14b96c77f'}.items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected, path
PY
uv sync --frozen --quiet --python "$PY312"
.venv/bin/python - <<'PY'
import tomllib
from pathlib import Path
lock=tomllib.loads(Path('uv.lock').read_text())
p=next(p for p in lock['package'] if p['name']=='websockets')
assert p['version']=='15.0.1'
hashes=[w['hash'] for w in p['wheels']]+[p['sdist']['hash']]
Path('/tmp/sca-websockets-'+str(__import__('os').getuid())+'.txt').write_text('websockets==15.0.1 '+' '.join('--hash='+h for h in hashes)+'\n')
PY
uv pip install --quiet --python .venv/bin/python --require-hashes -r "/tmp/sca-websockets-$(id -u).txt"
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u GROQ_API_KEY -u GPU_API_KEY \
  LITELLM_LOCAL_MODEL_COST_MAP=True PYTHON_DOTENV_DISABLED=1 \
  .venv/bin/python - <<'PY'
import sys,importlib.metadata as md
import tau2,tau2.cli
assert sys.version_info[:2]==(3,12)
assert md.version('tau2')=='1.0.1'
assert md.version('litellm')=='1.81.11'
print('Pinned tau2 client ready; no provider calls made.')
PY
