"""
Phase 3B post-run checker (no API calls). Run on every new tau2-bench results.json BEFORE copying it into this repo.

    .venv/bin/python -B gibs/validation/phase3b_check_run.py <results.json> [--env ../tau2-bench/.env]

Checks:
  1. Secrets: the file must not contain the Groq key (read from the environment or the given .env, never printed),
     nor credential markers ("X-API-Key", "extra_headers", "api_key", "Authorization", "Bearer ", "gsk_").
  2. Configuration: tau2 commit, agent/user model and temperatures, max steps/errors, seed, policy hash.
  3. Usage: per-simulation prompt/completion tokens from message `usage`, and a cost estimate at the Groq list price
     supplied below (recorded `cost` fields are 0 because the cost table lacks this model).
Exit codes: 0 = secrets and configuration pass; 1 = a secret check failed; 2 = secrets pass but the run does not
have the approved Phase 3B configuration (agent/user model and temperature, commit, steps, errors, seed, policy,
and llm_args containing exactly `temperature`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

EXPECTED = {"git_commit": "5bfa7e37b36656b37dc6d022156be6563c1007f3",
            "policy_sha256_12": "10dc05254215",
            "agent_llm": "groq/openai/gpt-oss-20b", "agent_temperature": 1.0,
            "user_llm": "groq/openai/gpt-oss-20b", "user_temperature": 0.0,
            "max_steps": 200, "max_errors": 10, "seed": 300}
PRICE_PER_M = {"input": 0.075, "output": 0.30}      # Groq list price for openai/gpt-oss-20b (console.groq.com/docs/models)
MARKERS = ["X-API-Key", "extra_headers", "api_key", "Authorization", "Bearer ", "gsk_"]


def read_key(env_path: str | None) -> str | None:
    key = os.environ.get("GROQ_API_KEY")
    if not key and env_path and Path(env_path).exists():
        for line in Path(env_path).read_text().splitlines():
            m = re.match(r"\s*GROQ_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                key = m.group(1)
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--env", default=None)
    a = ap.parse_args()
    raw = Path(a.results).read_text()
    ok = True
    key = read_key(a.env)
    if key:
        found = key in raw
        print(f"secret: Groq key present in file: {'YES (FAIL)' if found else 'no'}")
        ok &= not found
    else:
        print("secret: Groq key not available to the checker (only markers are checked)")
    for mk in MARKERS:
        n = raw.count(mk)
        if n:
            print(f"secret: marker {mk!r} occurs {n} time(s) (FAIL)")
            ok = False
    d = json.loads(raw)
    i = d["info"]
    got = {"git_commit": i.get("git_commit"),
           "policy_sha256_12": hashlib.sha256(i["environment_info"]["policy"].encode()).hexdigest()[:12],
           "agent_llm": i["agent_info"]["llm"], "agent_temperature": (i["agent_info"].get("llm_args") or {}).get("temperature"),
           "user_llm": i["user_info"]["llm"], "user_temperature": (i["user_info"].get("llm_args") or {}).get("temperature"),
           "max_steps": i.get("max_steps"), "max_errors": i.get("max_errors"), "seed": i.get("seed")}
    config_ok = True
    for k, v in got.items():
        match = v == EXPECTED[k]
        config_ok &= match
        print(f"config: {k} = {v} {'' if match else '(differs from Phase 3B setting ' + repr(EXPECTED[k]) + ')'}")
    for role in ("agent_info", "user_info"):
        keys = sorted((i[role].get("llm_args") or {}).keys())
        match = keys == ["temperature"]          # temperature must be explicit; nothing else (e.g. headers) allowed
        config_ok &= match
        print(f"config: {role}.llm_args keys = {keys} {'' if match else '(expected exactly [temperature])'}")
    tot = Counter()
    for s in d["simulations"]:
        p = c = 0
        for m in s.get("messages") or []:
            u = m.get("usage") or {}
            p += u.get("prompt_tokens") or 0
            c += u.get("completion_tokens") or 0
        rw = (s.get("reward_info") or {}).get("reward")
        print(f"sim {s['id'][:8]} task {s['task_id']} term={s.get('termination_reason')} reward={rw} "
              f"prompt={p} completion={c}")
        tot["prompt"] += p
        tot["completion"] += c
        tot["sims"] += 1
    cost = tot["prompt"] / 1e6 * PRICE_PER_M["input"] + tot["completion"] / 1e6 * PRICE_PER_M["output"]
    print(f"usage: {tot['sims']} sims, prompt {tot['prompt']}, completion {tot['completion']}, "
          f"estimated list-price cost ${cost:.4f}")
    print("SECRETS:", "PASS" if ok else "FAIL")
    print("CONFIG:", "PASS" if config_ok else "FAIL (not a Phase 3B run with the approved settings)")
    print("RESULT:", "PASS" if ok and config_ok else "FAIL (do not copy into the repository)")
    sys.exit(0 if ok and config_ok else (1 if not ok else 2))


if __name__ == "__main__":
    main()
