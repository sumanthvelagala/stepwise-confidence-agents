"""Run a bounded ASU collection and audit its checkpoint on completion."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from collection.audit import audit
from collection.run_tau2 import summarize, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trials', type=int, default=20)
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--tasks', nargs='+')
    parser.add_argument('--tau2-dir', type=Path, default=Path(__file__).resolve().parents[2] / 'tau2-bench')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    command = [sys.executable, str(root / 'run_tau2.py'), '--backend', 'asu', '--model', args.model,
               '--tau2-dir', str(args.tau2_dir.resolve()), '--output', str(output),
               '--trials', str(args.trials), '--concurrency', str(args.concurrency),
               '--simulation-timeout', '1200', '--infra-error-limit', '10']
    if args.tasks:
        command += ['--tasks', *args.tasks]
    if args.dry_run:
        raise SystemExit(subprocess.call(command + ['--dry-run'], cwd=root))
    output.mkdir(parents=True, exist_ok=True)
    with (output / '.job.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('A collection job already owns this output directory') from None
        state = {'started_utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid(),
                 'status': 'running', 'command': command, 'paid_api_calls': False}
        write_json(output / 'job_state.json', state)
        child = subprocess.Popen(command, cwd=root)
        state['collector_pid'] = child.pid
        write_json(output / 'job_state.json', state)
        def stop(_signum, _frame):
            if child.poll() is None:
                child.send_signal(signal.SIGINT)
        previous = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
        try:
            code = child.wait()
            result_path = output / 'results.json'
            if result_path.exists():
                payload = result_path.read_bytes()
                result = audit(json.loads(payload))
                result['input_sha256'] = hashlib.sha256(payload).hexdigest()
                write_json(output / 'audit.json', result)
            state['summary'] = summarize(result_path)
            manifest_path = output / 'collection_manifest.json'
            if manifest_path.exists():
                state['target_trajectories'] = json.loads(manifest_path.read_text())['target_trajectories']
                if code == 0 and state['summary']['simulations'] != state['target_trajectories']:
                    code = 2
                    state['incomplete_reason'] = 'Recorded trajectory count differs from collection target'
            state['exit_code'] = code
            state['status'] = 'completed' if code == 0 else 'stopped_or_failed'
            if code == 0 and state['summary']['outcomes'].get('infrastructure_error', 0):
                state['status'] = 'completed_with_infrastructure_errors'
        except Exception:
            state['status'] = 'audit_or_job_error'
            raise
        finally:
            state['ended_utc'] = datetime.now(timezone.utc).isoformat()
            write_json(output / 'job_state.json', state)
            for signum, handler in previous.items():
                signal.signal(signum, handler)
        print(json.dumps(state, indent=2), flush=True)
        raise SystemExit(code)


if __name__ == '__main__':
    main()
