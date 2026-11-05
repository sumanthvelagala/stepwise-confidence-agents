"""Paper GIBS and C4 on a frozen ASU dataset: prepare -> targets -> train/evaluate.

Never read historical teachers for fresh query IDs. Paper targets use real
DeBERTa/MCS; C4 changes only the teacher. Gold actions never enter prediction.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
import torch

from collection.audit import audit
from collection.run_tau2 import COMMIT,write_json
from gibs.comparison.graphs import projection, spec, tensors
from gibs.comparison.run import fit, load_checkpoint
from gibs.comparison.semantic_nibs import reference_scores
from gibs.graph.step_graph import build_step_graph
from gibs.learned.data import BERT_MODEL, BERT_REVISION, MAX_LENGTH, FrozenBert
from gibs.learned.run_experiment import aggregate_seed_metrics, evaluate, predict_graph
from gibs.mcs.consensus import pair_indicators
from gibs.mcs.mcs import MCSConfig, find_mcs
from gibs.mcs.multi_component import find_mcs_multi
from gibs.mcs.nli import DebertaEntailment, Similarity
from gibs.mcs.structured_fields import StructuredFieldValidator
from gibs.validation.dataset_audit import canon
from nibs.run_evaluation import (REPO, deduplicate, file_hash, fmt, load_runs, review_export,write_csv)
from nibs.scoring.nibs import score_run
from nibs.similarity.similarity import tool_sim

SEED = 20261029
MODEL = 'openai/qwen38-27b'
METHODS = ('paper_gibs_pdf', 'c4_gibs')


def order(value):
    return hashlib.sha256(f'{SEED}|{value}'.encode()).hexdigest()


def scenario_groups(tasks):
    """Keep shared user/reservation IDs and identical scenario text together.

    This conservative automatic grouping is disclosed, not a claim that a human
    has certified all semantically related scenarios as independent.
    """
    parent = {str(t['id']): str(t['id']) for t in tasks}
    def root(t):
        while parent[t] != t:
            parent[t] = parent[parent[t]]
            t = parent[t]
        return t
    owners = {}
    for task in tasks:
        tid = str(task['id'])
        ins = (task.get('user_scenario') or {}).get('instructions') or {}
        if not isinstance(ins, dict):
            ins = {'reason_for_call': str(ins)}
        known = ins.get('known_info') or ''
        tokens = re.findall(r'\b[a-z]+_[a-z]+_\d+\b|\b[A-Z0-9]{6}\b', known)
        reason = ' '.join((ins.get('reason_for_call') or '').lower().split())
        keys = ['entity:' + t for t in tokens] + (['reason:' + reason] if reason else [])
        for key in keys:
            if key in owners:
                parent[root(tid)] = root(owners[key])
            owners[key] = tid
    groups = defaultdict(list)
    for tid in parent:
        groups[root(tid)].append(tid)
    return {min(ids, key=int): sorted(ids, key=int) for ids in groups.values()}


def split_runs(runs, tasks):
    groups = scenario_groups(tasks)
    occupied = {r['task_id'] for r in runs}
    groups = {g: [t for t in tids if t in occupied] for g, tids in groups.items() if occupied.intersection(tids)}
    if len(groups) < 3:
        raise ValueError('Need at least three scenario groups for an independent test partition')
    ordered = sorted(groups, key=order)
    test_tasks = {t for g in ordered[:max(1, round(.25 * len(ordered)))] for t in groups[g]}
    train, validation, test = [], [], []
    strata = defaultdict(list)
    for r in runs:
        if r['task_id'] in test_tasks:
            test.append(r)
        else:
            strata[(r['task_id'], r['success'])].append(r)
    for key, values in sorted(strata.items()):
        values = sorted(values, key=lambda r: order(r['content_hash']))
        n = min(len(values)-1, max(1, round(.2 * len(values))))
        validation.extend(values[:n]); train.extend(values[n:])
    if not all((train, validation, test)):
        raise ValueError('Empty training, validation or test partition')
    if {r['task_id'] for r in test} & {r['task_id'] for r in train + validation}:
        raise ValueError('Task leakage')
    parts = [{r['content_hash'] for r in p} for p in (train, validation, test)]
    if any(parts[i] & parts[j] for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError('Duplicate-content leakage')
    return {name: sorted(rows,key=lambda r:r['id']) for name,rows in
            {'train': train, 'validation': validation, 'test': test}.items()}, groups


def references(query, pool, limit=0):
    refs = [r for r in pool if r['success'] and r['task_id'] == query['task_id']
            and r['content_hash'] != query['content_hash']]
    refs.sort(key=lambda r: order(r['content_hash']))
    return refs[:limit] if limit else refs


def prepare(args):
    config_path = args.output / 'plan.json'
    if config_path.exists():
        existing = json.loads(config_path.read_text())
        if bool(existing.get('folds')) != bool(getattr(args,'crossfit',False)):
            raise ValueError('Evaluation mode changed; preserve the old experiment and choose a new output')
        if not args.allow_partial and existing.get('input_records', existing['runs']) != args.expected_runs:
            raise ValueError('Existing snapshot is partial; use an explicit separate prototype output')
        print('Frozen plan exists; preserving its input snapshot.', flush=True)
        return
    payload = args.input.read_bytes()
    raw = json.loads(payload)
    if not args.allow_partial and len(raw['simulations']) != args.expected_runs:
        raise ValueError('Collection is incomplete; do not silently train on a moving partial dataset')
    checked = audit(raw)
    manifest_path = args.input.parent / 'collection_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    config = manifest['configuration']
    if config['tau2_commit'] != COMMIT or config['model'] != 'qwen38-27b' or not config.get('reasoning_passthrough') \
            or config.get('parallel_tool_calls_requested') is not False:
        raise ValueError('Input is not the corrected, pinned ASU collection')
    if checked['totals'].get('responses_with_reasoning',0):
        raise ValueError('Observed reasoning contradicts the collection contract; review serving before training')
    usable = {r['run_id'] for r in checked['runs'] if r['graph_compatible'] and r['official_outcome'] != 'infrastructure_error'}
    source_info = raw.get('info') or {}
    info = {key: {'llm': (source_info.get(key) or {}).get('llm'),
                  'llm_args': {'temperature': ((source_info.get(key) or {}).get('llm_args') or {}).get('temperature')}}
            for key in ('agent_info','user_info')}
    info['environment_info'] = {k: (source_info.get('environment_info') or {}).get(k) for k in ('domain_name','policy')}
    info['git_commit'] = source_info.get('git_commit')
    clean = {'info': info, 'tasks': raw['tasks'], 'simulations': [s for s in raw['simulations'] if s['id'] in usable]}
    write_json(args.output / 'input/results.json', clean)
    runs, excluded, inputs, identities = load_runs(args.output / 'input', [str(t['id']) for t in raw['tasks']],
                                                   model=MODEL, agent_temperature=1., user_temperature=0.)
    runs, counts = deduplicate(runs)
    folds=None
    if getattr(args,'crossfit',False):
        from gibs.fresh.folds import grouped_folds
        split,folds,groups=grouped_folds(runs,raw['tasks'],scenario_groups,order)
    else:
        split, groups = split_runs(runs, raw['tasks'])
    plan = {'input_sha256': hashlib.sha256(payload).hexdigest(), 'source': str(args.input),
            'snapshot_sha256': file_hash(args.output / 'input/results.json'),
            'model': MODEL, 'runs': len(runs), 'input_records': len(raw['simulations']), 'counts': counts, 'seed': SEED,
            'collection_configuration': config,
            'grouping': groups, 'grouping_limit': 'Shared entities and exact scenario text; semantic-family independence is not human-certified',
            'split': {p: [r['id'] for r in rs] for p,rs in split.items()},
            'evaluation_mode':'four_fold_oof' if folds else 'single_holdout',
            'minimum_references': args.min_references, 'maximum_references': args.max_references,
            'methods': METHODS, 'architecture': 'pdf_gcn', 'objective': 'Eq6 entropy + lambda=1 soft BCE',
            'label_status': 'Automatic verifier candidates only; independent human validation pending',
            'reference_quality': 'Official benchmark success; missing-action and verifier flags require review; no human-correctness claim',
            'data_exclusions': excluded, 'task_identities': identities,
            'source_sha256': {name:file_hash(REPO/name) for name in (
                'gibs/fresh/experiment.py','gibs/learned/model.py','gibs/learned/data.py',
                'gibs/mcs/nli.py','gibs/mcs/mcs.py','gibs/mcs/multi_component.py',
                'gibs/mcs/structured_fields.py','gibs/graph/step_graph.py','gibs/graph/event_projection.py')}}
    if folds:
        plan['folds']={name:{p:[r['id'] for r in rs] for p,rs in fold.items()} for name,fold in folds.items()}
    write_json(args.output / 'input_audit.json', checked)
    write_json(config_path, plan)
    print(f'Frozen {len(runs)} distinct trajectories; split counts: ' + str({p:len(rs) for p,rs in split.items()}), flush=True)


def load(args):
    plan = json.loads((args.output / 'plan.json').read_text())
    if file_hash(args.output / 'input/results.json') != plan['snapshot_sha256']:
        raise ValueError('Frozen snapshot changed')
    raw = json.loads((args.output / 'input/results.json').read_text())
    runs, _, _, _ = load_runs(args.output / 'input', [str(t['id']) for t in raw['tasks']],
                              model=MODEL, agent_temperature=1., user_temperature=0.)
    runs, _ = deduplicate(runs)
    by_id = {r['id']:r for r in runs}
    return plan, runs, {p:[by_id[sid] for sid in ids] for p,ids in plan['split'].items()}


def targets(args):
    plan, runs, split = load(args)
    eligible, skipped = [], []
    for q in split['train'] + split['validation']:
        refs = references(q, split['train'], plan['maximum_references'])
        if len(refs) < plan['minimum_references']:
            skipped.append({'run_id':q['id'], 'task':q['task_id'], 'references':len(refs)})
        else:
            eligible.append((q,refs))
    write_json(args.output / 'teacher_exclusions.json', skipped)
    if not any(q['id'] in set(plan['split']['train']) for q,_ in eligible):
        raise ValueError('No train queries with enough training-only successful references')
    if not any(q['id'] in set(plan['split']['validation']) for q,_ in eligible):
        raise ValueError('No validation queries with enough training-only successful references')
    base = DebertaEntailment(encoding='code_sep_string', overlength='truncate', device=args.nli_device, batch_size=args.nli_batch_size)
    symmetric = base.with_overlength('symmetric')
    variants = {'paper_gibs_pdf': (base, find_mcs, MCSConfig(require_same_kind=False)),
                'c4_gibs': (symmetric, find_mcs_multi, MCSConfig())}
    similarities = {m: Similarity(v[0], direction='max_bidirectional') for m,v in variants.items()}
    graphs = {r['id']: projection(r['_sim']) for r in runs}
    steps = {r['id']: build_step_graph(r['_sim']) for r in runs}
    write_json(args.output / 'nli_model.json', base.describe())
    started = time.perf_counter()
    for qi,(q,refs) in enumerate(eligible):
        for method,(model, matcher, cfg) in variants.items():
            path = args.output / f'teachers/{method}/{q["id"]}.json'
            if path.exists():
                stored = json.loads(path.read_text())
                if stored['references'] != [r['id'] for r in refs] or stored['snapshot_sha256'] != plan['snapshot_sha256']:
                    raise ValueError('Stored fresh teacher belongs to another reference set/snapshot')
                continue
            masks = []
            for r in refs:
                pair_path = args.output / f'pairs/{method}/{q["id"]}_{r["id"]}.json'
                if pair_path.exists():
                    pair = json.loads(pair_path.read_text())
                else:
                    validator = StructuredFieldValidator(steps[q['id']],steps[r['id']]) if method == 'c4_gibs' else None
                    result = matcher(graphs[q['id']],graphs[r['id']],similarities[method],cfg,field_check=validator)
                    key = 'context_step_level' if method == 'c4_gibs' else 'node_level'
                    indicator = pair_indicators(graphs[q['id']],result)
                    pair = {'mask':{event:float(row[key]) for event,row in indicator.items()},
                            'node_map':result.node_map,'edge_map':result.edge_map}
                    write_json(pair_path,pair)
                masks.append([pair['mask'][n['id']] for n in q['nodes']])
            target = np.mean(masks,axis=0).tolist()
            write_json(path,{'query':q['id'],'references':[r['id'] for r in refs],'mask':target,
                             'events':[n['id'] for n in q['nodes']],'snapshot_sha256':plan['snapshot_sha256']})
        print(f'Fresh MCS teachers {qi+1}/{len(eligible)}; elapsed {time.perf_counter()-started:.0f}s',flush=True)


def features(runs,device):
    specs = {r['id']:spec(projection(r['_sim'])) for r in runs}
    if any(specs[r['id']]['agent_events'] != [n['id'] for n in r['nodes']] for r in runs):
        raise ValueError('Feature/scorer event alignment changed')
    encoder = FrozenBert(device=device)
    embeddings = encoder.encode([text for s in specs.values() for key in ('result_texts','operation_texts') for text in s[key]])
    return {sid:tensors(s,embeddings) for sid,s in specs.items()}, encoder.description


def read_teachers(plan, split, method, output):
    masks = {}
    train_ids = {q['id'] for q in split['train']}
    for q in split['train'] + split['validation']:
        refs = references(q, split['train'], plan['maximum_references'])
        if len(refs) < plan['minimum_references']:
            continue
        path = output / f'teachers/{method}/{q["id"]}.json'
        if not path.exists():
            raise ValueError('Fresh targets are incomplete; run targets before training')
        teacher = json.loads(path.read_text())
        if teacher['query'] != q['id'] or teacher['snapshot_sha256'] != plan['snapshot_sha256'] \
                or teacher['references'] != [r['id'] for r in refs] or not set(teacher['references']) <= train_ids:
            raise ValueError('Teacher identity/reference leakage or changed input')
        if teacher['events'] != [n['id'] for n in q['nodes']]:
            raise ValueError('Teacher step alignment mismatch')
        mask = torch.tensor(teacher['mask'], dtype=torch.float32)
        if len(mask) != len(q['nodes']) or not torch.isfinite(mask).all() or not ((mask >= 0) & (mask <= 1)).all():
            raise ValueError('Invalid consensus mask')
        masks[q['id']] = mask
    return masks


def train_and_evaluate(args):
    plan, runs, split = load(args)
    if plan.get('folds'):
        from gibs.fresh.crossfit import run
        return run(args,plan,runs,split)
    all_masks = {method: read_teachers(plan, split, method, args.output) for method in METHODS}
    if any(not any(r['id'] in masks for r in split[part]) for masks in all_masks.values() for part in ('train','validation')):
        raise ValueError('No eligible training or validation queries with sufficient references')
    feats, bert = features(runs,args.feature_device)
    base, reference_manifest, coverage = [], {}, []
    bank = {r['id']:r for r in runs}
    for q in split['test']:
        refs = references(q,runs,plan['maximum_references'])
        if len(refs) < plan['minimum_references']:
            coverage.append({'run_id':q['id'],'task':q['task_id'],'references':len(refs),'reason':'NIBS unavailable; excluded only from common comparison'})
            continue
        reference_manifest[q['id']] = [r['id'] for r in refs]
        tool = score_run(q['parsed'],[r['parsed'] for r in refs],tool_sim,'max')
        qp=feats[q['id']]; matrix=qp['operations'][qp['agent_indices']].numpy()
        rs=[feats[r['id']]['operations'][feats[r['id']]['agent_indices']].numpy() for r in refs]
        maximum,average=reference_scores(matrix,rs)
        for i,(node,scored) in enumerate(zip(q['nodes'],tool)):
            label=q['labels'][node['id']]
            base.append({'task_id':q['task_id'],'run_id':q['id'],'step_index':i,'event_id':node['id'],
                         'message_index':q['message_indices'][i],'success':q['success'],'kind':node['kind'],
                         'tool':(node.get('tool_call') or {}).get('name',''),'multiplicity':q['multiplicity'],
                         'n_references':len(refs),'label':{'valid':'correct'}.get(label['label'],label['label']),
                         'verifier_label':label['label'],'label_reason':label['reason'] or '',
                         'confidence':scored['score'],'paper_nibs_cos_max':maximum[i],'paper_nibs_cos_mean':average[i],
                         'source':q['source']})
    if not base:
        raise ValueError('No common test population with successful references; do not report an invented baseline')
    baseline={'tool_sim_nibs':evaluate(base)[0]}
    for name in ('paper_nibs_cos_max','paper_nibs_cos_mean'):
        baseline[name]=evaluate([{**r,'confidence':r[name]} for r in base])[0]
    for name in ('random_expected','last_step_first'):
        baseline[name]=evaluate(base,name)[0]
    learned,histories,predictions={}, {},[]
    for method in METHODS:
        masks=all_masks[method]
        fitting={p:[q for q in split[p] if q['id'] in masks] for p in ('train','validation')}
        fitting['test']=split['test']
        learned[method]={}
        for seed in args.seeds:
            print(f'Training {method}, seed {seed}, {len(fitting["train"])} graphs',flush=True)
            model,history=fit(fitting,feats,masks,method,seed,args.epochs)
            checkpoint={'state_dict':model.state_dict(),'model_config':model.config,'architecture':'pdf_gcn',
                        'method':method,'structure':'original','seed':seed,'bert_model':BERT_MODEL,'bert_revision':BERT_REVISION,
                        'max_length':MAX_LENGTH,'train_ids':[r['id'] for r in fitting['train']],
                        'validation_ids':[r['id'] for r in fitting['validation']],'test_ids':plan['split']['test'],
                        'training_reference_pool_ids':plan['split']['train'],'snapshot_sha256':plan['snapshot_sha256']}
            path=args.output/f'checkpoints/{method}_seed{seed}.pt';path.parent.mkdir(parents=True,exist_ok=True)
            torch.save(checkpoint,path); reloaded,_=load_checkpoint(path)
            scores={q['id']:predict_graph(model,feats[q['id']]) for q in split['test']}
            if any(scores[q['id']]!=predict_graph(reloaded,feats[q['id']]) for q in split['test']):
                raise ValueError('Saved checkpoint predictions changed on reload')
            rows=[{**r,'confidence':scores[r['run_id']][r['step_index']],'method':method,'seed':seed} for r in base]
            learned[method][str(seed)]=evaluate(rows)[0];predictions.extend(rows)
            histories[f'{method}_{seed}']=history
            write_json(args.output/f'query_only_predictions/{method}_seed{seed}.json',scores)
    write_json(args.output/'evaluation_references.json',reference_manifest)
    write_json(args.output/'evaluation_coverage_exclusions.json',coverage)
    write_json(args.output/'training_histories.json',histories)
    write_csv(args.output/'per_step.csv',predictions,list(predictions[0]))
    selected=[bank[sid] for sid in reference_manifest]
    review_export(args.output/'human_review',selected,base)
    summary={'n_input_runs':len(runs),'n_common_test_runs':len(selected),'n_common_test_steps':len(base),
             'label_counts':dict(Counter(r['label'] for r in base)),'baselines':baseline,'learned':learned,'bert':bert,
             'seeds':args.seeds,'snapshot_sha256':plan['snapshot_sha256'],'human_validation':'pending'}
    write_json(args.output/'summary.json',summary)
    lines=['# Fresh ASU paper GIBS / C4 comparison','',
           'Real tau2 Airline data; PDF architecture/objective on agent graphs. Automatic labels; human validation pending.','',
           f'{len(runs)} distinct input trajectories; {len(selected)} test trajectories / {len(base)} steps in the common comparison.',
           '','| Method | Tool macro AUROC | Tool first-error top-1 |','|---|---|---|']
    for method,values in learned.items():
        a=aggregate_seed_metrics(values)['tool_calls']
        lines.append(f'| {method} | {fmt(a["macro_auroc"]["mean"])} | {fmt(a["top1"]["mean"])} |')
    for method,values in baseline.items():
        a=values['tool_calls']['aggregate']
        lines.append(f'| {method} | {fmt(a["macro_auroc"])} | {fmt(a["localization"]["top1"])} |')
    lines+=['','Reference methods receive successful same-task examples at evaluation; learned models receive only query graphs.',
            'No claim of original math/QA benchmark reproduction, calibrated correctness, or guaranteed C4 improvement.',
            'Grouping uses shared entities and exact scenario text; semantic-family independence is not human-certified.',
            'Inspect reference-quality flags, coverage exclusions, exact denominators and human-review sheets before accuracy claims.','']
    (args.output/'REPORT.md').write_text('\n'.join(lines))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','targets','train','all'])
    parser.add_argument('--input',type=Path,default=REPO/'results/free_asu/main-qwen38-27b-serial-none/results.json')
    parser.add_argument('--output',type=Path,default=REPO/'results/fresh_comparison')
    parser.add_argument('--expected-runs',type=int,default=1000)
    parser.add_argument('--allow-partial',action='store_true')
    parser.add_argument('--crossfit',action='store_true',help='Four held-out task-group folds, covering every trajectory')
    parser.add_argument('--min-references',type=int,default=3)
    parser.add_argument('--max-references',type=int,default=0,help='0 = all eligible successful references')
    parser.add_argument('--nli-device',choices=['cpu','mps','cuda'],default='mps')
    parser.add_argument('--nli-batch-size',type=int,default=4)
    parser.add_argument('--feature-device',choices=['cpu','mps','cuda'],default='mps')
    parser.add_argument('--epochs',type=int,default=150)
    parser.add_argument('--seeds',type=int,nargs='+',default=[7,17,27])
    args=parser.parse_args(argv)
    if args.epochs < 1 or len(set(args.seeds)) != len(args.seeds) or args.expected_runs < 1 or args.nli_batch_size < 1:
        parser.error('Positive counts/epochs and distinct training seeds required')
    if args.min_references<1 or args.max_references<0 or (args.max_references and args.max_references<args.min_references):
        parser.error('Invalid reference limits')
    args.output.mkdir(parents=True,exist_ok=True)
    import fcntl
    with (args.output/'.experiment.lock').open('w') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit('Another fresh experiment owns this output directory') from None
        torch.set_num_threads(2)
        if args.stage in ('prepare','all'): prepare(args)
        if args.stage in ('targets','all'): targets(args)
        if args.stage in ('train','all'): train_and_evaluate(args)


if __name__=='__main__': main()
