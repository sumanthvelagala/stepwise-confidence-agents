"""Monitor the owned Sol target job, retrieve its outputs, then train locally."""
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

from collection.run_tau2 import clean_environment,write_json

ROOT=Path(__file__).resolve().parents[2]
REMOTE='/scratch/ppudi/sca-free/project/results/fresh_all_tasks'
SCRIPT='/scratch/ppudi/sca-free/project/collection/sol_gibs_targets.sbatch'


def ssh(command):
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=5',
                      '-o','ServerAliveCountMax=1','sol',command],capture_output=True,text=True,timeout=40)
    if p.returncode:raise RuntimeError('Sol SSH failed; reconnect VPN before resuming this monitor')
    return p.stdout.strip()


def job_status(job):
    live=ssh(f'squeue -h -j {int(job)} -o %T 2>/dev/null || true')
    if live:return live.splitlines()[0],None
    rows=ssh(f'sacct -n -P -j {int(job)} --starttime=1970-01-01 --format=JobIDRaw,State,ExitCode')
    for row in rows.splitlines():
        columns=row.split('|')
        if columns[0]==str(job):return columns[1].split()[0],columns[2]
    return 'ACCOUNTING_PENDING',None


def target_progress(job):
    log=ssh(f'tail -n 20 /scratch/ppudi/sca-free/logs/mcs-{int(job)}.log 2>/dev/null || true')
    matches=re.findall(r'Fresh MCS teachers (\d+)/(\d+); elapsed (\d+)s',log)
    if not matches:return None
    completed,total,elapsed=map(int,matches[-1])
    return {'completed_query_targets':completed,'total_eligible_queries':total,
            'elapsed_target_seconds_in_current_job':elapsed}


def resumable_timeout(job,status,code):
    if status in {'TIMEOUT','PREEMPTED'}:return True
    # The first submitted script requested TERM two minutes before its 4-hour
    # deadline. Slurm can record that checkpoint exit as FAILED / 143:0.
    # Resume only this deadline case, never an arbitrary failure or cancellation.
    if status!='FAILED' or code!='143:0':return False
    rows=ssh(f'sacct -n -P -j {int(job)} --starttime=1970-01-01 --format=JobIDRaw,ElapsedRaw,TimelimitRaw')
    for row in rows.splitlines():
        columns=row.split('|')
        if columns[0]==str(job) and columns[1].isdigit() and columns[2].isdigit():
            return int(columns[2])>0 and int(columns[1])>=int(columns[2])*60-180
    return False


def retrieve(output,remote=REMOTE):
    for folder in ('teachers','pairs'):
        (output/folder).mkdir(parents=True,exist_ok=True)
        subprocess.run(['rsync','-a',f'sol:{remote}/{folder}/',str(output/folder)+'/'],check=True)
    subprocess.run(['rsync','-a','--include=nli_model.json','--include=sol_runtime*.json',
                    '--exclude=*',f'sol:{remote}/',str(output)+'/'],check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-id',type=int,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'results/fresh_all_tasks')
    parser.add_argument('--max-gpu-jobs',type=int,default=3)
    parser.add_argument('--remote-output',default=REMOTE)
    parser.add_argument('--script',default=SCRIPT)
    parser.add_argument('--compare-with',type=Path)
    args=parser.parse_args()
    if Path(args.remote_output).name!=args.output.name:
        parser.error('Local and remote output directory names must match')
    if args.max_gpu_jobs<1:parser.error('Positive GPU allocation bound required')
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'.followup.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('An all-task follow-up is already active') from None
        state={'status':'monitoring_sol','pid':__import__('os').getpid(),'job_ids':[args.job_id],
               'started_utc':datetime.now(timezone.utc).isoformat(),'maximum_gpu_jobs':args.max_gpu_jobs,
               'remote_output':args.remote_output,'sbatch_script':args.script}
        path=args.output/'worker_state.json';write_json(path,state)
        job=args.job_id;failures=0
        try:
            while True:
                try:
                    status,code=job_status(job)
                    progress=target_progress(job) if status in {'RUNNING','COMPLETING','COMPLETED'} else None
                    failures=0
                except (RuntimeError,subprocess.TimeoutExpired):
                    failures+=1
                    state.update({'status':'waiting_for_sol_connection','connection_failures':failures,
                                  'connection_checked_utc':datetime.now(timezone.utc).isoformat()})
                    write_json(path,state)
                    time.sleep(60 if failures<3 else min(900,300*(failures-2)));continue
                state['status']='monitoring_sol';state.pop('connection_failures',None)
                state.update({'sol_job':job,'sol_status':status,'sol_exit_code':code,
                              'checked_utc':datetime.now(timezone.utc).isoformat()})
                if progress is not None:state['target_progress']=progress
                write_json(path,state)
                if status=='COMPLETED' and code=='0:0':
                    try:retrieve(args.output,args.remote_output)
                    except subprocess.CalledProcessError:
                        state['status']='waiting_for_target_download';write_json(path,state)
                        time.sleep(60);continue
                    break
                if resumable_timeout(job,status,code) and len(state['job_ids'])<args.max_gpu_jobs:
                    result=ssh('sbatch --parsable --gres=gpu:a100:1 '+shlex.quote(args.script))
                    job=int(result.split(';')[0]);state['job_ids'].append(job)
                    write_json(path,state);continue
                if status in {'FAILED','CANCELLED','OUT_OF_MEMORY','NODE_FAIL','TIMEOUT','PREEMPTED'}:
                    state['status']='gpu_job_needs_attention';write_json(path,state)
                    raise RuntimeError(f'Sol job {job} ended as {status}')
                time.sleep(60)
            state['status']='training_and_evaluating';write_json(path,state)
            plan=json.loads((args.output/'plan.json').read_text())
            for name,digest in plan.get('execution_source_sha256',{}).items():
                if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
                    raise RuntimeError(f'Frozen implementation changed before local training: {name}')
            write_json(args.output/'training_source_verification.json',
                       {'verified':True,'execution_source_sha256':plan.get('execution_source_sha256',{})})
            write_json(args.output/'training_runtime.json',{'python':sys.version,
                       'versions':{p:md.version(p) for p in ['torch','transformers','numpy']},
                       'targets':'Sol CUDA; NLI versions and hardware in sol_runtime.json'})
            env=clean_environment();env['PYTORCH_ENABLE_MPS_FALLBACK']='1'
            command=[sys.executable,'-u','-m','gibs.fresh.experiment','train','--output',str(args.output)]
            state['training_command']=command;write_json(path,state)
            child=subprocess.Popen(command,cwd=ROOT,env=env)
            state['training_pid']=child.pid;write_json(path,state)
            code=child.wait()
            if code:raise RuntimeError(f'Local training/evaluation exited with {code}')
            summary=json.loads((args.output/'summary.json').read_text())
            if (summary['n_scored_oof_runs'],summary['n_tasks'])!=(1000,50):
                raise RuntimeError('Full out-of-fold coverage was not achieved')
            if args.compare_with:
                state['status']='comparing_reference_caps';write_json(path,state)
                from gibs.fresh.reference_comparison import compare
                compare(args.compare_with,args.output)
                state['comparison_report']=str(args.output/'REFERENCE_CAP_COMPARISON.md')
            state['status']='completed';state['ended_utc']=datetime.now(timezone.utc).isoformat()
            write_json(path,state)
        except Exception as exc:
            state['error']=str(exc)
            if state['status'] not in {'sol_connection_lost','gpu_job_needs_attention'}:
                state['status']='followup_failed'
            write_json(path,state);raise


if __name__=='__main__':main()
