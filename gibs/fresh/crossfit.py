"""Out-of-fold predictions for every task; missing references stay explicit."""
from collections import Counter
import json
from pathlib import Path
import statistics

import torch

from gibs.comparison.run import fit,load_checkpoint
from gibs.comparison.semantic_nibs import reference_scores
from gibs.learned.data import BERT_MODEL,BERT_REVISION,MAX_LENGTH
from gibs.learned.run_experiment import aggregate_seed_metrics,evaluate,predict_graph
from nibs.run_evaluation import fmt,review_export,write_csv
from collection.run_tau2 import write_json
from nibs.scoring.nibs import score_run
from nibs.similarity.similarity import tool_sim


def rows_and_baselines(runs,feats,plan,references):
    rows,ref_manifest,unavailable=[],{},[]
    for q in runs:
        refs=references(q,runs,plan['maximum_references'])
        available=len(refs)>=plan['minimum_references']
        if available:
            ref_manifest[q['id']]=[r['id'] for r in refs]
            tool=score_run(q['parsed'],[r['parsed'] for r in refs],tool_sim,'max')
            g=feats[q['id']];mat=g['operations'][g['agent_indices']].numpy()
            rm=[feats[r['id']]['operations'][feats[r['id']]['agent_indices']].numpy() for r in refs]
            maximum,average=reference_scores(mat,rm)
        else:
            unavailable.append({'run_id':q['id'],'task_id':q['task_id'],'references':len(refs)})
        for i,node in enumerate(q['nodes']):
            label=q['labels'][node['id']]
            rows.append({'task_id':q['task_id'],'run_id':q['id'],'step_index':i,'event_id':node['id'],
                         'message_index':q['message_indices'][i],'success':q['success'],'kind':node['kind'],
                         'tool':(node.get('tool_call') or {}).get('name',''),'multiplicity':q['multiplicity'],
                         'n_references':len(refs),'label':{'valid':'correct'}.get(label['label'],label['label']),
                         'verifier_label':label['label'],'label_reason':label['reason'] or '',
                         'confidence':tool[i]['score'] if available else None,
                         'paper_nibs_cos_max':maximum[i] if available else None,
                         'paper_nibs_cos_mean':average[i] if available else None,
                         'reference_available':available,'source':q['source']})
    common=[r for r in rows if r['reference_available']]
    baseline={}
    if common:
        baseline['tool_sim_nibs']=evaluate(common)[0]
        for name in ('paper_nibs_cos_max','paper_nibs_cos_mean'):
            baseline[name]=evaluate([{**r,'confidence':r[name]} for r in common])[0]
        for name in ('random_expected','last_step_first'):
            baseline[name]=evaluate(common,name)[0]
    return rows,common,baseline,ref_manifest,unavailable


def run(args,plan,runs,teacher_split):
    from gibs.fresh.experiment import METHODS,features,read_teachers,references
    by_id={r['id']:r for r in runs}
    # Task-local reference banks are unchanged across folds whenever the task is
    # in fitting. Validate each fold against its actual training-only pool.
    fold_data={name:{p:[by_id[sid] for sid in ids] for p,ids in fold.items()}
               for name,fold in plan['folds'].items()}
    masks={name:{method:read_teachers(plan,split,method,args.output) for method in METHODS}
           for name,split in fold_data.items()}
    feats,bert=features(runs,args.feature_device)
    base,common,baselines,ref_manifest,coverage=rows_and_baselines(runs,feats,plan,references)
    learned_common={m:{} for m in METHODS};learned_all={m:{} for m in METHODS}
    histories,predictions,fold_manifest={},[],{}
    for method in METHODS:
        for seed in args.seeds:
            all_scores={};assignment={}
            for fold,split in fold_data.items():
                target=masks[fold][method]
                fitting={p:[r for r in split[p] if r['id'] in target] for p in ('train','validation')}
                fitting['test']=split['test']
                if not fitting['train'] or not fitting['validation']:
                    raise ValueError('Fold lacks eligible training/validation targets')
                train_ids={r['id'] for r in fitting['train']}
                val_ids={r['id'] for r in fitting['validation']}
                test_ids={r['id'] for r in split['test']}
                test_tasks={r['task_id'] for r in split['test']}
                if test_tasks & {r['task_id'] for r in fitting['train']+fitting['validation']}:
                    raise ValueError('Task leakage into fitting')
                if train_ids & test_ids or val_ids & test_ids or train_ids & val_ids:
                    raise ValueError('Trajectory leakage')
                key=f'{fold}_{method}_seed{seed}'
                path=args.output/f'checkpoints/{key}.pt'
                if path.exists():
                    model,checkpoint=load_checkpoint(path)
                    if checkpoint.get('snapshot_sha256')!=plan['snapshot_sha256'] \
                            or set(checkpoint['train_ids'])!=train_ids or set(checkpoint['validation_ids'])!=val_ids \
                            or set(checkpoint['test_ids'])!=test_ids:
                        raise ValueError('Checkpoint belongs to another fold or dataset')
                    history=checkpoint['training_history']
                else:
                    print(f'Training {key}: {len(train_ids)} graphs; scoring {len(test_ids)} held-out trajectories',flush=True)
                    model,history=fit(fitting,feats,target,method,seed,args.epochs)
                    checkpoint={'state_dict':model.state_dict(),'model_config':model.config,'architecture':'pdf_gcn',
                                'method':method,'structure':'original','seed':seed,'fold':fold,
                                'bert_model':BERT_MODEL,'bert_revision':BERT_REVISION,'max_length':MAX_LENGTH,
                                'train_ids':sorted(train_ids),'validation_ids':sorted(val_ids),'test_ids':sorted(test_ids),
                                'training_reference_pool_ids':[r['id'] for r in split['train']],
                                'snapshot_sha256':plan['snapshot_sha256'],'training_history':history}
                    path.parent.mkdir(parents=True,exist_ok=True);torch.save(checkpoint,path)
                reloaded,_=load_checkpoint(path)
                for q in split['test']:
                    if q['id'] in all_scores:raise ValueError('A query was evaluated in multiple folds')
                    score=predict_graph(model,feats[q['id']])
                    if score!=predict_graph(reloaded,feats[q['id']]):raise ValueError('Checkpoint reload mismatch')
                    all_scores[q['id']]=score;assignment[q['id']]=fold
                histories[key]=history
                fold_manifest[key]={'train_ids':sorted(train_ids),'validation_ids':sorted(val_ids),'test_ids':sorted(test_ids),
                                    'target_reference_pool_ids':[r['id'] for r in split['train']]}
            if set(all_scores)!=set(by_id):raise ValueError('Out-of-fold predictions do not cover the full dataset')
            scored=[{**r,'confidence':all_scores[r['run_id']][r['step_index']],
                     'method':method,'seed':seed,'fold':assignment[r['run_id']]} for r in base]
            learned_all[method][str(seed)]=evaluate(scored)[0]
            shared=[r for r in scored if r['reference_available']]
            learned_common[method][str(seed)]=evaluate(shared)[0] if shared else None
            predictions.extend(scored)
            write_json(args.output/f'query_only_predictions/{method}_seed{seed}.json',
                       {'scores':all_scores,'heldout_fold':assignment,'training_gold_used_at_inference':False})
    common_runs={r['run_id'] for r in common}
    summary={'n_input_runs':len(runs),'n_scored_oof_runs':len(runs),'n_tasks':len({r['task_id'] for r in runs}),
             'n_common_comparison_runs':len(common_runs),'n_all_agent_steps':len(base),
             'n_common_comparison_steps':len(common),'label_counts':dict(Counter(r['label'] for r in base)),
             'evaluation':'Four-fold task-group out-of-fold; each query scored exactly once per seed',
             'baselines':baselines,'learned_common':learned_common,'learned_all':learned_all,
             'seeds':args.seeds,'bert':bert,'snapshot_sha256':plan['snapshot_sha256'],'human_validation':'pending'}
    write_json(args.output/'summary.json',summary)
    write_json(args.output/'fold_manifest.json',fold_manifest)
    write_json(args.output/'training_histories.json',histories)
    write_json(args.output/'evaluation_references.json',ref_manifest)
    write_json(args.output/'reference_coverage_exclusions.json',coverage)
    write_csv(args.output/'per_step.csv',predictions,list(predictions[0]))
    review_export(args.output/'human_review',runs,base)
    task_rows=[]
    for task in sorted({r['task_id'] for r in runs},key=int):
        q=[r for r in runs if r['task_id']==task]
        row={'task_id':task,'trajectories':len(q),'common_comparison_trajectories':sum(r['id'] in common_runs for r in q)}
        for method,values in baselines.items():
            item=values['tool_calls']['tasks'].get(task)
            row[method+'_auroc']=item['auroc_error_positive'] if item else None
        for method,values in learned_common.items():
            auc=[v['tool_calls']['tasks'].get(task,{}).get('auroc_error_positive') for v in values.values() if v]
            auc=[v for v in auc if v is not None]
            row[method+'_common_auroc']=statistics.mean(auc) if auc else None
        for method,values in learned_all.items():
            auc=[v['tool_calls']['tasks'].get(task,{}).get('auroc_error_positive') for v in values.values()]
            auc=[v for v in auc if v is not None]
            row[method+'_all_auroc']=statistics.mean(auc) if auc else None
        task_rows.append(row)
    columns=list(dict.fromkeys(key for row in task_rows for key in row))
    write_csv(args.output/'per_task.csv',task_rows,columns)
    lines=['# All-task, out-of-fold paper GIBS / C4 comparison','',
           f'{len(runs)} trajectories across {summary["n_tasks"]} tasks. Four held-out task-group folds, three seeds.',
           'Every learned prediction is from a model that excluded that trajectory’s entire task group from fitting.',
           f'{len(common_runs)} trajectories have enough references for the common NIBS/GIBS/C4 comparison.',
           'NIBS-unavailable tasks still receive learned predictions and remain in per_task.csv.',
           'Automatic labels; independent human validation pending. Undefined AUROC is shown as N/A.','',
           '| Method | Common tool macro AUROC | Common tool first-error top-1 |','|---|---|---|']
    for method,values in learned_common.items():
        valid={k:v for k,v in values.items() if v}
        if valid:
            a=aggregate_seed_metrics(valid)['tool_calls']
            lines.append(f'| {method} | {fmt(a["macro_auroc"]["mean"])} | {fmt(a["top1"]["mean"])} |')
    for method,values in baselines.items():
        a=values['tool_calls']['aggregate']
        lines.append(f'| {method} | {fmt(a["macro_auroc"])} | {fmt(a["localization"]["top1"])} |')
    lines+=['','| Task | Saved trajectories | Common-comparison trajectories | NIBS Max AUROC | GIBS AUROC | C4 AUROC |',
            '|---|---|---|---|---|---|']
    show=lambda value:'N/A' if value is None else f'{value:.3f}'
    for row in task_rows:
        lines.append(f'| {row["task_id"]} | {row["trajectories"]} | {row["common_comparison_trajectories"]} | '
                     f'{show(row.get("paper_nibs_cos_max_auroc"))} | {show(row.get("paper_gibs_pdf_common_auroc"))} | {show(row.get("c4_gibs_common_auroc"))} |')
    lines+=['','See summary.json for separate all-query learned metrics, class counts and exact denominators.',
            'No original math/QA benchmark reproduction, calibrated correctness or human-verified improvement is claimed.','']
    (args.output/'REPORT.md').write_text('\n'.join(lines))
    print(f'Completed {len(runs)} out-of-fold trajectories across all {summary["n_tasks"]} tasks.',flush=True)
