"""Evaluate reference baselines before the more expensive learned models finish."""
import argparse
from collections import Counter
from pathlib import Path

import torch

from collection.run_tau2 import write_json
from gibs.fresh.crossfit import rows_and_baselines
from gibs.fresh.experiment import load, features, references
from nibs.run_evaluation import fmt, write_csv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('results/fresh_all_tasks'))
    args=parser.parse_args()
    torch.set_num_threads(2)
    plan,runs,_=load(args)
    feats,bert=features(runs,'mps')
    rows,common,metrics,refs,unavailable=rows_and_baselines(runs,feats,plan,references)
    folder=args.output/'baseline_preview'
    summary={'status':'baselines_only; GIBS/C4 pending','snapshot_sha256':plan['snapshot_sha256'],
             'n_input_runs':len(runs),'n_tasks':len({r['task_id'] for r in runs}),
             'n_common_runs':len({r['run_id'] for r in common}),'n_agent_steps':len(rows),
             'n_common_agent_steps':len(common),'label_counts':dict(Counter(r['label'] for r in rows)),
             'baselines':metrics,'bert':bert,'human_validation':'pending'}
    write_json(folder/'summary.json',summary)
    write_json(folder/'evaluation_references.json',refs)
    write_json(folder/'reference_coverage_exclusions.json',unavailable)
    task_rows=[]
    for task in sorted({r['task_id'] for r in runs},key=int):
        task_runs=[r for r in runs if r['task_id']==task]
        row={'task_id':task,'trajectories':len(task_runs),'benchmark_passes':sum(r['success'] for r in task_runs),
             'nibs_available_trajectories':sum(r['id'] in refs for r in task_runs)}
        for method,metric in metrics.items():
            item=metric['tool_calls']['tasks'].get(task,{})
            row[method+'_auroc']=item.get('auroc_error_positive')
        task_rows.append(row)
    write_csv(folder/'per_task.csv',task_rows,list(task_rows[0]))
    write_csv(folder/'per_step.csv',rows,list(rows[0]))
    lines=['# All-task baseline results; learned comparison pending','',
           f'{len(runs)} distinct trajectories across {summary["n_tasks"]} tasks; '
           f'{summary["n_common_runs"]} trajectories have enough same-task successful references.',
           'Automatic verifier labels only; independent human review remains pending. Unknown steps are excluded from binary metrics.',
           'Reference methods receive successful examples at evaluation. These scores do not establish calibrated confidence.',
           '','| Method | Tool macro AUROC | Tool first-error top-1 |','|---|---|---|']
    for method,metric in metrics.items():
        a=metric['tool_calls']['aggregate']
        lines.append(f'| {method} | {fmt(a["macro_auroc"])} | {fmt(a["localization"]["top1"])} |')
    lines+=['','See per_task.csv for all 50 tasks and summary.json for exact evaluation denominators.',
            'Missing references or missing label classes produce unavailable scores, not invented accuracy.',
            'Paper GIBS and C4 are still computing; this is a baseline preview only.','']
    (folder/'REPORT.md').write_text('\n'.join(lines))
    print(f'Completed baseline preview: {len(runs)} trajectories, {summary["n_common_runs"]} reference-eligible.',flush=True)


if __name__=='__main__':main()
