"""Compare the frozen five-reference experiment with the all-reference ablation."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics

from collection.run_tau2 import write_json

DESIGN_KEYS=('snapshot_sha256','input_sha256','runs','seed','split','folds','grouping',
             'architecture','objective','minimum_references','model','methods',
             'collection_configuration')


def verify_plans(baseline,trial):
    for key in DESIGN_KEYS:
        if baseline[key]!=trial[key]:raise ValueError(f'Controlled design changed: {key}')
    # The first preparation preceded the documented cache/resumption fixes.
    # Runtime-verified execution hashes are authoritative for files they cover.
    bcode={**baseline.get('source_sha256',{}),**baseline.get('execution_source_sha256',{})}
    tcode={**trial.get('source_sha256',{}),**trial.get('execution_source_sha256',{})}
    for name,digest in bcode.items():
        if tcode.get(name)!=digest:raise ValueError(f'Executed implementation changed: {name}')
    if baseline['minimum_references']!=3 or baseline['maximum_references']!=5 or trial['maximum_references'] not in {0,17}:
        raise ValueError('Expected minimum 3, maximum 5 versus all eligible or maximum 17 references')
    return True


def verify_baseline(directory,protection):
    for name,digest in protection['files'].items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Protected baseline artifact changed: {name}')


def value(metrics,scope,key):
    a=metrics[scope]['aggregate']
    return a['macro_auroc'] if key=='auroc' else a['localization'][key]


def aggregate(summary,method,scope,key,population='learned_common'):
    if method in summary.get('baselines',{}):vals=[value(summary['baselines'][method],scope,key)]
    else:vals=[value(v,scope,key) for v in summary[population][method].values()]
    vals=[v for v in vals if v is not None]
    return {'mean':statistics.mean(vals) if vals else None,
            'std':statistics.pstdev(vals) if vals else None,'n':len(vals)}


def compare(baseline_dir,trial_dir):
    baseline_dir=Path(baseline_dir);trial_dir=Path(trial_dir)
    bp=json.loads((baseline_dir/'plan.json').read_text());tp=json.loads((trial_dir/'plan.json').read_text())
    verify_plans(bp,tp)
    guard=trial_dir/'baseline_protection.json'
    if guard.exists():verify_baseline(baseline_dir,json.loads(guard.read_text()))
    before=json.loads((baseline_dir/'summary.json').read_text());after=json.loads((trial_dir/'summary.json').read_text())
    for key in ['n_input_runs','n_scored_oof_runs','n_tasks','n_common_comparison_runs',
                'n_all_agent_steps','n_common_comparison_steps','label_counts','seeds','snapshot_sha256']:
        if before[key]!=after[key]:raise ValueError(f'Evaluation population changed: {key}')
    assert after['n_scored_oof_runs']==1000 and after['n_tasks']==50
    methods=list(after['learned_common'])+list(after['baselines'])
    cap=tp['maximum_references'];trial_label='all eligible' if cap==0 else f'maximum {cap}'
    result={'comparison':f'Minimum 3 fixed; reference maximum 5 versus {trial_label}',
            'baseline_maximum_references':5,'trial_maximum_references':cap,
            'controlled_design_verified':True,'baseline_directory':str(baseline_dir),
            'trial_directory':str(trial_dir),'n_common_runs':after['n_common_comparison_runs'],
            'n_all_scored_runs':after['n_scored_oof_runs'],'human_validation':'pending','scopes':{}}
    lines=[f'# Reference-cap ablation: maximum 5 versus {trial_label}','',
           'Same data, task-group folds, seeds, model implementation and minimum-three rule. Only the maximum reference cap changes.',
           'Both training-target references and NIBS evaluation references use the new cap; their original partition-access rules are unchanged.',
           f'{after["n_common_comparison_runs"]} runs in the common comparison; all 1,000 receive held-out learned scores.',
           'Automatic labels; independent human validation pending. Learned values are means over three seeds; deltas are descriptive, not significance tests.','']
    for scope in ['tool_calls','all_agent_steps']:
        out={};lines += ['## '+scope.replace('_',' '),'',
            f'| Method | Cap-5 AUROC | {trial_label} AUROC | Delta | Cap-5 Top-1 | {trial_label} Top-1 | Delta |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for method in methods:
            out[method]={}
            for metric in ['auroc','top1','top3','reciprocal_rank']:
                a=aggregate(before,method,scope,metric);b=aggregate(after,method,scope,metric)
                out[method][metric]={'five':a,'trial':b,'delta':None if a['mean'] is None or b['mean'] is None else b['mean']-a['mean']}
            a=out[method]['auroc'];t=out[method]['top1']
            f=lambda v:'N/A' if v is None else f'{v:.3f}'
            lines.append(f'| {method} | {f(a["five"]["mean"])} | {f(a["trial"]["mean"])} | {f(a["delta"])} | '
                         f'{f(t["five"]["mean"])} | {f(t["trial"]["mean"])} | {f(t["delta"])} |')
        result['scopes'][scope]=out;lines.append('')
    result['all_query_learned']={}
    for method in after['learned_all']:
        result['all_query_learned'][method]={scope:{metric:{
            'five':aggregate(before,method,scope,metric,'learned_all'),
            'trial':aggregate(after,method,scope,metric,'learned_all')}
            for metric in ['auroc','top1','top3','reciprocal_rank']} for scope in ['tool_calls','all_agent_steps']}
    lines+=['See REFERENCE_CAP_COMPARISON.json for per-seed dispersion and separate all-query learned results.',
            'No new trajectories were generated. Baseline artifacts were preserved. The human review and missing ACC@80%/ECE work remain separate.','']
    write_json(trial_dir/'REFERENCE_CAP_COMPARISON.json',result)
    (trial_dir/'REFERENCE_CAP_COMPARISON.md').write_text('\n'.join(lines))
    print(f'Completed verified cap-5 versus {trial_label} comparison.',flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--trial',type=Path,required=True)
    args=p.parse_args();compare(args.baseline,args.trial)
