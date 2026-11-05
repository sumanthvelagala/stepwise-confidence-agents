"""Wait for the bounded collection, then execute the fresh comparison once."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from collection.run_tau2 import clean_environment, write_json


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection',type=Path,default=root/'results/free_asu/main-qwen38-27b-serial-none')
    parser.add_argument('--output',type=Path,default=root/'results/fresh_comparison')
    parser.add_argument('--max-references',type=int,default=5,
                        help='Fixed successful-reference bank cap for this prototype; 0 uses all')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'.worker.lock').open('w') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit('A worker already owns this experiment') from None
        state={'status':'waiting_for_collection','pid':os.getpid(),'started_utc':datetime.now(timezone.utc).isoformat(),
               'collection':str(args.collection),'maximum_references':args.max_references}
        path=args.output/'worker_state.json';write_json(path,state)
        child=None
        def stop(_signum,_frame):
            if child is not None and child.poll() is None:
                child.send_signal(signal.SIGINT)
            else:
                state['status']='stopped';write_json(path,state)
                raise SystemExit(130)
        signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
        while True:
            try: current=json.loads((args.collection/'job_state.json').read_text())
            except (FileNotFoundError,json.JSONDecodeError):
                time.sleep(30);continue
            if current['status'].startswith('completed'):
                break
            if current['status']!='running':
                state['status']='collection_stopped';state['collection_status']=current['status']
                write_json(path,state);raise SystemExit(2)
            try: os.kill(current['pid'],0)
            except ProcessLookupError:
                state['status']='collection_process_missing';write_json(path,state);raise SystemExit(2)
            time.sleep(30)
        command=[sys.executable,'-m','gibs.fresh.experiment','all','--input',str(args.collection/'results.json'),
                 '--output',str(args.output),'--max-references',str(args.max_references)]
        env=clean_environment();env['PYTORCH_ENABLE_MPS_FALLBACK']='1'
        state['status']='running_fresh_comparison';state['command']=command
        state['experiment_started_utc']=datetime.now(timezone.utc).isoformat();write_json(path,state)
        child=subprocess.Popen(command,cwd=root,env=env)
        state['experiment_pid']=child.pid;write_json(path,state)
        code=child.wait()
        state['status']='completed' if code==0 else 'experiment_stopped_or_failed'
        state['exit_code']=code;state['ended_utc']=datetime.now(timezone.utc).isoformat()
        write_json(path,state)
        raise SystemExit(code)


if __name__=='__main__':main()
