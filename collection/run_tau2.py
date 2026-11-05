"""Run pinned tau2 using local Ollama or ASU's free hosted service."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import urllib.parse
import urllib.request

COMMIT = "5bfa7e37b36656b37dc6d022156be6563c1007f3"
POLICY_SHA = "10dc05254215"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def local_url(value):
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("only a local loopback Ollama server is allowed")
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("base URL must contain only loopback host and port")
    return value.rstrip("/")


def clean_environment():
    # tau2 loads dotenv automatically; disable it for this no-API-cost collection.
    env = {k: v for k, v in os.environ.items()
           if not (k.endswith("_API_KEY") or k in {"GPU_API_BASE", "OPENAI_API_BASE", "OPENAI_BASE_URL", "ANTHROPIC_BASE_URL"})}
    env.update({"PYTHON_DOTENV_DISABLED": "1", "LITELLM_LOCAL_MODEL_COST_MAP": "True",
                "OLLAMA_NO_CLOUD": "1", "DO_NOT_TRACK": "1"})
    return env


def task_definitions(tau2_dir, selected):
    commit = subprocess.check_output(["git", "-C", str(tau2_dir), "rev-parse", "HEAD"], text=True).strip()
    if commit != COMMIT:
        raise ValueError("tau2 benchmark commit differs from the pinned existing dataset")
    folder = tau2_dir / "data/tau2/domains/airline"
    policy = (folder / "policy.md").read_bytes()
    if hashlib.sha256(policy).hexdigest()[:12] != POLICY_SHA:
        raise ValueError("airline policy differs from the existing benchmark")
    tasks = json.loads((folder / "tasks.json").read_text())
    available = {str(t["id"]): t for t in tasks}
    ids = sorted(available, key=int) if selected is None else sorted(set(selected), key=int)
    if not set(ids) <= set(available):
        raise ValueError("unknown Airline task ID")
    for tid in ids:
        basis = set(available[tid]["evaluation_criteria"]["reward_basis"])
        if not basis <= {"DB", "COMMUNICATE"}:
            raise ValueError("selected task could require an external LLM evaluator")
    return ids, {tid: hashlib.sha256(json.dumps(available[tid], sort_keys=True).encode()).hexdigest() for tid in ids}


def model_identity(base, model):
    with urllib.request.urlopen(base + "/api/tags", timeout=15) as response:
        tags = json.load(response).get("models", [])
    match = next((m for m in tags if m.get("name") == model or m.get("model") == model), None)
    if match is None:
        raise ValueError("requested model is not installed in the local Ollama server")
    request = urllib.request.Request(base + "/api/show", data=json.dumps({"model": model}).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        details = json.load(response)
    if details.get("remote_model") or details.get("remote_host") or model.endswith((":cloud", "-cloud")):
        raise ValueError("cloud-backed Ollama models are not allowed in this free local collection")
    if "tools" not in details.get("capabilities", []):
        raise ValueError("model does not advertise tool calling")
    return {"name": model, "digest": match.get("digest"), "details": details.get("details"),
            "capabilities": details.get("capabilities")}


def command(args, tasks, output):
    shared = {"api_base": args.base_url, "max_tokens": args.max_tokens,
              "reasoning_effort": "none"}
    if getattr(args, "backend", "ollama") == "asu":
        from collection.asu import BASE_URL
        if args.base_url != BASE_URL:
            raise ValueError("ASU credentials can only be used with ASU's exact free API endpoint")
        shared["extra_headers"] = {"x-obleth-boons": "off"}
        # LiteLLM 1.81.11 otherwise silently drops this field for custom model
        # names under the OpenAI-compatible provider when drop_params is true.
        shared["allowed_openai_params"] = ["reasoning_effort", "parallel_tool_calls"]
        shared["parallel_tool_calls"] = False
        # ASU documents zero charges. These are LiteLLM bookkeeping fields,
        # not model-generation parameters; avoid unknown-price error spam.
        shared.update({"input_cost_per_token": 0.0, "output_cost_per_token": 0.0})
        model = "openai/" + args.model
    else:
        shared["num_ctx"] = args.context
        model = "ollama_chat/" + args.model
    return [str(args.tau2_dir / ".venv/bin/tau2"), "run", "--domain", "airline",
            "--agent-llm", model, "--agent-llm-args", json.dumps({**shared, "temperature": 1.0}),
            "--user-llm", model, "--user-llm-args", json.dumps({**shared, "temperature": 0.0}),
            "--task-ids", *tasks, "--num-trials", str(args.trials), "--max-concurrency", str(args.concurrency),
            "--max-steps", "200", "--max-errors", "10", "--seed", "300", "--timeout", str(args.simulation_timeout),
            "--save-to", str(output.resolve()), "--auto-resume", "--log-level", "ERROR", "--llm-log-mode", "latest"]


def summarize(path):
    if not path.exists():
        return {"simulations": 0, "outcomes": {}, "tasks": {}}
    data = json.loads(path.read_text())
    totals, by_task = Counter(), {}
    for sim in data.get("simulations", []):
        reward = (sim.get("reward_info") or {}).get("reward")
        outcome = "infrastructure_error" if reward is None else "success" if reward >= .5 else "failure"
        totals[outcome] += 1
        by_task.setdefault(str(sim["task_id"]), Counter())[outcome] += 1
    return {"simulations": sum(totals.values()), "outcomes": dict(totals),
            "tasks": {tid: dict(counts) for tid, counts in sorted(by_task.items(), key=lambda item: int(item[0]))}}


def validate_smoke(path):
    data = json.loads(path.read_text())
    simulations = data.get("simulations", [])
    if len(simulations) != 1 or (simulations[0].get("reward_info") or {}).get("reward") is None:
        raise ValueError("smoke test did not produce one graded trajectory")
    if not any(m.get("tool_calls") for m in simulations[0].get("messages", [])):
        raise ValueError("smoke test contains no tool call")
    from gibs.graph.step_graph import build_step_graph
    graph = build_step_graph(simulations[0])
    return {"passed": True, "reward": simulations[0]["reward_info"]["reward"],
            "graph_agent_steps": sum(n["type"] == "AgentStep" for n in graph["nodes"])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau2-dir", type=Path, default=Path(__file__).resolve().parents[2] / "tau2-bench")
    parser.add_argument("--backend", choices=["ollama", "asu"], default="ollama")
    parser.add_argument("--base-url")
    parser.add_argument("--model")
    parser.add_argument("--key-file", type=Path, default=Path(__file__).resolve().parents[1] / ".env.asu")
    parser.add_argument("--list-models", action="store_true", help="List ASU catalog metadata, without generating text")
    parser.add_argument("--tasks", nargs="+")
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--context", type=int, default=32768)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--simulation-timeout", type=int, default=1200)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--require-tool-smoke", action="store_true")
    parser.add_argument("--infra-error-limit", type=int, default=10,
                        help="Checkpoint and stop after this many infrastructure failures (default 10)")
    args = parser.parse_args(argv)
    if args.backend == "asu":
        from collection import asu
        if args.base_url not in (None, asu.BASE_URL):
            parser.error("ASU mode only permits https://openai.rc.asu.edu/v1")
        args.base_url = asu.BASE_URL
        if args.list_models:
            print(json.dumps(asu.list_models(asu.load_key(args.key_file)), indent=2))
            return
        if not args.model and not args.status:
            parser.error("ASU mode needs --model from --list-models")
    else:
        args.base_url = local_url(args.base_url or "http://127.0.0.1:11434")
        args.model = args.model or "qwen3:8b"
        if args.list_models:
            parser.error("--list-models is available for --backend asu")
    if args.output is None:
        parser.error("--output is required for collection/status")
    args.tau2_dir = args.tau2_dir.resolve()
    args.output = args.output.resolve()
    if args.status:
        print(json.dumps(summarize(args.output / "results.json"), indent=2))
        return
    if min(args.trials, args.concurrency, args.context, args.max_tokens, args.simulation_timeout, args.infra_error_limit) < 1:
        parser.error("positive trial, concurrency, context and timeout settings required")
    if args.trials > 40 or args.concurrency > 4:
        parser.error("use at most 40 trials/task and 4 simultaneous simulations per collection job")
    tasks, task_hashes = task_definitions(args.tau2_dir, args.tasks)
    cli = command(args, tasks, args.output)
    identity = {"tau2_commit": COMMIT, "task_sha256": task_hashes, "model": args.model,
                "agent_temperature": 1.0, "user_temperature": 0.0, "thinking": False,
                "context": args.context, "max_tokens": args.max_tokens, "max_steps": 200,
                "max_errors": 10, "seed": 300, "concurrency": args.concurrency,
                "simulation_timeout": args.simulation_timeout, "trials": args.trials}
    if args.backend == "asu":
        identity.pop("thinking")
        identity.update({"backend": "asu", "reasoning_effort_requested": "none",
                         "reasoning_passthrough": True,
                         "parallel_tool_calls_requested": False,
                         "gateway_addons": "off", "context_note": "Context is checked against catalog; server controls its window"})
    if args.dry_run:
        print(json.dumps({"configuration": identity, "target_trajectories": len(tasks) * args.trials,
                          "command": cli, "paid_api_calls": False}, indent=2))
        return
    environment = clean_environment()
    if args.backend == "asu":
        key = asu.load_key(args.key_file)
        identity["model_weights"] = asu.model_identity(asu.list_models(key), args.model, args.context)
        environment["OPENAI_API_KEY"] = key
    else:
        identity["model_weights"] = model_identity(args.base_url, args.model)
    manifest_path = args.output / "collection_manifest.json"
    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if existing and existing["configuration"] != identity:
        raise ValueError("collection configuration/model digest changed; choose a new output directory")
    args.output.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (args.output / ".collection.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another collector is already using this output directory") from None
        before = summarize(args.output / "results.json")
        # Native tau2 resume removes infrastructure errors. Preserve each pre-resume
        # dataset so all attempted trajectories remain available for an audit.
        if before["outcomes"].get("infrastructure_error", 0):
            import shutil
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            archive = args.output / "attempt_snapshots" / (stamp + ".json")
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.output / "results.json", archive)
        manifest = {"configuration": identity, "target_trajectories": len(tasks) * args.trials,
                    "paid_api_calls": False, "endpoint": args.base_url,
                    "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "collection_source_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                                 for name in ("run_tau2.py", "asu.py")},
                    "started_utc": datetime.now(timezone.utc).isoformat(), "before": before,
                    "infra_error_limit": args.infra_error_limit,
                    "invocations": existing.get("invocations", [])}
        write_json(manifest_path, manifest)
        print(f"Collecting {len(tasks)} tasks x {args.trials} trials; {args.backend}, no paid API.", flush=True)
        child = subprocess.Popen(cli, cwd=args.tau2_dir, env=environment, start_new_session=True)
        def stop(_signum, _frame):
            os.killpg(child.pid, signal.SIGINT)
        previous = {s: signal.signal(s, stop) for s in (signal.SIGTERM, signal.SIGINT)}
        try:
            while True:
                try:
                    code = child.wait(timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    try:
                        status = summarize(args.output / "results.json")
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue  # A native checkpoint may be in the middle of a write.
                    if status["outcomes"].get("infrastructure_error", 0) >= args.infra_error_limit:
                        manifest["stop_reason"] = "infrastructure_error_limit"
                        print("Infrastructure error limit reached; stopping collection with its checkpoint.", flush=True)
                        stop(None, None)
                        code = child.wait()
                        if not code:
                            code = 2
                        break
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            manifest["ended_utc"] = datetime.now(timezone.utc).isoformat()
            manifest["after"] = summarize(args.output / "results.json")
            manifest["invocations"].append({k: manifest[k] for k in ("started_utc", "ended_utc", "endpoint", "source_sha256", "collection_source_sha256", "before", "after")})
            write_json(manifest_path, manifest)
            write_json(args.output / "collection_summary.json", manifest["after"])
        print(json.dumps(manifest["after"], indent=2), flush=True)
        if code:
            raise SystemExit(code)
        if args.require_tool_smoke:
            try:
                smoke = validate_smoke(args.output / "results.json")
            except ValueError as exc:
                write_json(args.output / "smoke_check.json", {"passed": False, "reason": str(exc)})
                raise
            write_json(args.output / "smoke_check.json", smoke)


if __name__ == "__main__":
    main()
