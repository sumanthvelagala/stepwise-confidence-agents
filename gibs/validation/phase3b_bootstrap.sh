#!/usr/bin/env bash
# Phase 3B: recreate the tau2-bench environment used for Groq collection (see gibs/validation/PHASE3B_SETUP.md §8).
#
#   bash gibs/validation/phase3b_bootstrap.sh            # TAU2_DIR defaults to ../tau2-bench (sibling of this repo)
#
# Idempotent. Never makes provider API calls, never reads or writes .env, never modifies tracked upstream files.
# Network use: git clone/fetch (GitHub) and package downloads (PyPI) only, and only when not already present.
#
#   1. clone tau2-bench if absent; check out the exact commit (detached); refuse to continue if tracked files differ
#   2. verify uv.lock / pyproject.toml hashes
#   3. uv sync --frozen on CPython 3.12 (3.13 removed `audioop`, which tau2 imports)
#   4. install the one missing runtime import, websockets==15.0.1, with the sha256 hashes listed in uv.lock
#   5. verify imports with all provider keys unset and HTTP(S) routed to a dead proxy (proves no network is needed)
#   6. create the placeholder-only template .env.phase3b.template (git-ignored via .git/info/exclude)
set -euo pipefail

COMMIT="5bfa7e37b36656b37dc6d022156be6563c1007f3"
UV_LOCK_SHA256="6404e490ae418d1d62afda97641605dab1684c2b830b6b3de34e7685ef2153c7"
PYPROJECT_SHA256="3c718fbc3c1e350a4e36b465fee8f33db34eae75c97a18880cef46c14b96c77f"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TAU2_DIR="${TAU2_DIR:-$(cd "$REPO_DIR/.." && pwd)/tau2-bench}"
PY312="${PY312:-/opt/anaconda3/bin/python3.12}"

say() { printf '[bootstrap] %s\n' "$*"; }
die() { printf '[bootstrap] ERROR: %s\n' "$*" >&2; exit 1; }

command -v uv >/dev/null || die "uv not found (brew install uv)"
command -v git >/dev/null || die "git not found"
if [ ! -x "$PY312" ]; then PY312="$(uv python find 3.12 2>/dev/null || true)"; fi
[ -n "$PY312" ] && [ -x "$PY312" ] || die "no CPython 3.12 found; set PY312=/path/to/python3.12 (or: uv python install 3.12)"
"$PY312" -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version' || die "$PY312 is not Python 3.12"

# 1. checkout --------------------------------------------------------------------------------------------------
if [ ! -d "$TAU2_DIR/.git" ]; then
  say "cloning tau2-bench into $TAU2_DIR"
  git clone --quiet https://github.com/sierra-research/tau2-bench.git "$TAU2_DIR"
fi
cd "$TAU2_DIR"
if ! git cat-file -e "$COMMIT^{commit}" 2>/dev/null; then git fetch --quiet origin; fi
[ -z "$(git status --porcelain --untracked-files=no)" ] || die "tracked files in $TAU2_DIR are modified; refusing to continue"
git checkout --quiet --detach "$COMMIT"
[ "$(git rev-parse HEAD)" = "$COMMIT" ] || die "HEAD is not $COMMIT"
say "tau2-bench at $COMMIT (tracked files unmodified)"

# 2. lock integrity -------------------------------------------------------------------------------------------
[ "$(shasum -a 256 uv.lock | awk '{print $1}')" = "$UV_LOCK_SHA256" ] || die "uv.lock hash mismatch"
[ "$(shasum -a 256 pyproject.toml | awk '{print $1}')" = "$PYPROJECT_SHA256" ] || die "pyproject.toml hash mismatch"
say "uv.lock and pyproject.toml hashes verified"

# 3. locked core environment on Python 3.12 (exact sync: removes anything not in the lock) ---------------------
if [ -x .venv/bin/python ] && ! .venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 12)' 2>/dev/null; then
  say "existing .venv is not Python 3.12; removing it"
  rm -rf .venv
fi
uv sync --frozen --quiet --python "$PY312"
say "uv sync --frozen done ($(.venv/bin/python -c 'import sys; print(sys.version.split()[0])'))"

# 4. websockets==15.0.1 with the hashes recorded in uv.lock -----------------------------------------------------
REQ="$(mktemp -t phase3b_websockets_req)"
trap 'rm -f "$REQ"' EXIT
.venv/bin/python - "$REQ" <<'PY'
import sys, tomllib
lock = tomllib.load(open("uv.lock", "rb"))
pkg = [p for p in lock["package"] if p["name"] == "websockets"]
assert len(pkg) == 1 and pkg[0]["version"] == "15.0.1", "websockets 15.0.1 not uniquely pinned in uv.lock"
hashes = [w["hash"] for w in pkg[0].get("wheels", [])] + ([pkg[0]["sdist"]["hash"]] if "sdist" in pkg[0] else [])
assert hashes, "no hashes for websockets in uv.lock"
open(sys.argv[1], "w").write("websockets==15.0.1 " + " ".join(f"--hash={h}" for h in hashes) + "\n")
PY
uv pip install --quiet --python .venv/bin/python --require-hashes -r "$REQ"
say "websockets==15.0.1 installed with uv.lock hashes"

# 5. offline verification -------------------------------------------------------------------------------------
env -u GROQ_API_KEY -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u GPU_API_KEY -u GPU_API_BASE -u OPENAI_API_BASE \
    LITELLM_LOCAL_MODEL_COST_MAP=True HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 \
    ALL_PROXY=http://127.0.0.1:9 NO_PROXY= \
  .venv/bin/python - <<'PY' 2>/dev/null
import sys, importlib.metadata as md
import tau2, tau2.cli, tau2.config as c
want = {"tau2": "1.0.1", "litellm": "1.81.11", "websockets": "15.0.1"}
got = {k: md.version(k) for k in want}
assert sys.version_info[:2] == (3, 12), sys.version
assert got == want, got
assert (c.DEFAULT_MAX_STEPS, c.DEFAULT_MAX_ERRORS, c.DEFAULT_SEED, c.LLM_CACHE_ENABLED) == (200, 10, 300, False)
print(f"[bootstrap] verified offline: python {sys.version.split()[0]}, " + ", ".join(f"{k} {v}" for k, v in got.items()))
PY

# 6. placeholder-only credential template (never a real key) --------------------------------------------------
if [ ! -f .env.phase3b.template ]; then
  printf '# Phase 3B template. Copy to .env and replace the placeholder yourself. Never commit .env.\nGROQ_API_KEY=YOUR_KEY_HERE\n' > .env.phase3b.template
fi
grep -qx ".env.phase3b.template" .git/info/exclude || echo ".env.phase3b.template" >> .git/info/exclude
git check-ignore -q .env || die ".env is not git-ignored"
[ -z "$(git status --porcelain --untracked-files=no)" ] || die "tracked files changed during bootstrap"
say "done. .env present: $([ -f .env ] && echo yes || echo no) (create it yourself from .env.phase3b.template)"
