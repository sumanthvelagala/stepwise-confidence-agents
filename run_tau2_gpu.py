"""
Wrapper to run tau2-bench CLI against the GPU endpoint.
Patches litellm SSL verification before tau2 imports its httpx sessions.

Reads GPU_API_KEY and GPU_API_BASE from .env in the project root.

Usage (run from inside tau2-bench/):
    python ../run_tau2_gpu.py run \
        --domain airline \
        --agent-llm openai/gpt-oss:20b \
        --agent-llm-args '{"temperature": 1.0, "extra_headers": {"X-API-Key": "'"$GPU_API_KEY"'"}}' \
        --user-llm openai/gpt-oss:20b \
        --user-llm-args '{"temperature": 0.0, "extra_headers": {"X-API-Key": "'"$GPU_API_KEY"'"}}' \
        --num-trials 20 \
        --task-ids 1 2 3 \
        --save-to ../results/oss20b_temp1/tasks_1_2_3/
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from tau2-bench/)
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

gpu_api_key = os.environ.get("GPU_API_KEY")
gpu_api_base = os.environ.get("GPU_API_BASE", "https://gpt-chat.dohsnow.com/v1")

if not gpu_api_key:
    print("ERROR: GPU_API_KEY not set in .env")
    sys.exit(1)

# Must be set before tau2 imports litellm
os.environ["OPENAI_API_BASE"] = gpu_api_base
os.environ["OPENAI_API_KEY"] = "dummy"  # real auth is via X-API-Key header

import litellm
import httpx

litellm.ssl_verify = False  # endpoint uses self-signed cert

# Inject API key into sys.argv before tau2 parses it
sys.argv = [
    arg.replace("GPU_API_KEY_PLACEHOLDER", gpu_api_key)
    for arg in sys.argv
]

# Import tau2 — llm_utils.py will create httpx sessions at import time
from tau2.cli import main

# After import, patch the sessions to use verify=False
# (llm_utils.py recreates them without ssl_verify, so we override here)
_limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
litellm.client_session = httpx.Client(limits=_limits, verify=False)
litellm.aclient_session = httpx.AsyncClient(limits=_limits, verify=False)

main()
