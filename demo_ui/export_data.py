"""Export a static, read-only demo of the completed experiment.

Uses saved scores and genuine MCS mappings. No model calls, fitting, or changes
to original experiment artifacts. Only whitelisted transcript fields are exported.
Run: .venv/bin/python demo_ui/export_data.py
"""
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
import csv
import hashlib
import json
import math
import shutil
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gibs.comparison.graphs import projection
from gibs.learned.run_experiment import evaluate

DATA=Path(__file__).resolve().parent/'dist/data'
EXPERIMENTS={'cap5':ROOT/'results/fresh_all_tasks','cap17':ROOT/'results/fresh_refs_3_17'}
EXPERIMENT=EXPERIMENTS['cap5']
OUT=DATA/'cap5'
EXPERIMENT_ID='cap5'
LEARNED=('paper_gibs_pdf','c4_gibs')
SEEDS=('7','17','27')


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    path.write_text(payload+'\n')


def write_run(sid,value):
    path=OUT/f'runs/{sid}.js';path.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    key=json.dumps(EXPERIMENT_ID)
    path.write_text('window.TRACE_RUNS=window.TRACE_RUNS||{};window.TRACE_RUNS['+key+']=window.TRACE_RUNS['+key+']||{};window.TRACE_RUNS['+key+']['+json.dumps(sid)+']='+payload+';\n')


def typed(row):
    return {**row,'step_index':int(row['step_index']),'message_index':int(row['message_index']),
            'success':row['success']=='True','reference_available':row.get('reference_available')=='True',
            'confidence':float(row['confidence']) if row['confidence'] else None,
            'n_references':int(row['n_references']),
            'paper_nibs_cos_max':float(row['paper_nibs_cos_max']) if row['paper_nibs_cos_max'] else None,
            'paper_nibs_cos_mean':float(row['paper_nibs_cos_mean']) if row['paper_nibs_cos_mean'] else None}


def plain(value):
    if value is None:return ''
    return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)


def metric_subset(rows):
    metrics=evaluate(rows)[0]
    return {scope:data['aggregate'] for scope,data in metrics.items()}


def ranks(steps,key):
    tools=[s for s in steps if s['kind']=='tool_call']
    target=next((s for s in tools if s['label']=='incorrect'),None)
    if not target:return None
    values=[s['scores'].get(key) for s in tools]
    if any(v is None for v in values):return None
    low=min(values);tied=sum(v==low for v in values)
    return (1/tied if target['scores'][key]==low else 0)


def build(experiment_id):
    global EXPERIMENT,OUT,EXPERIMENT_ID
    EXPERIMENT_ID=experiment_id;EXPERIMENT=EXPERIMENTS[experiment_id];OUT=DATA/experiment_id
    state=read(EXPERIMENT/'worker_state.json')
    summary=read(EXPERIMENT/'summary.json')
    plan=read(EXPERIMENT/'plan.json')
    assert state['status']=='completed' and summary['n_scored_oof_runs']==1000
    source=EXPERIMENT/'input/results.json'
    assert sha(source)==plan['snapshot_sha256']
    raw=read(source);sims={s['id']:s for s in raw['simulations']};tasks={str(t['id']):t for t in raw['tasks']}
    refs=read(EXPERIMENT/'evaluation_references.json')
    rows_by_run=defaultdict(list);base_rows=[]
    with (EXPERIMENT/'baseline_preview/per_step.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            row=typed(row);base_rows.append(row)
            rows_by_run[row['run_id']].append(row)
    predictions={}
    for method in LEARNED:
        predictions[method]={seed:read(EXPERIMENT/f'query_only_predictions/{method}_seed{seed}.json') for seed in SEEDS}
        assert all(len(p['scores'])==1000 for p in predictions[method].values())
    teachers={m:{} for m in LEARNED}
    for method in LEARNED:
        for path in (EXPERIMENT/'teachers'/method).glob('*.json'):
            t=read(path);assert t['snapshot_sha256']==plan['snapshot_sha256']
            teachers[method][t['query']]=t
        assert len(teachers[method])==860
    graphs={sid:projection(sim) for sid,sim in sims.items()}
    run_index=[];details={}
    for sid,sim in sims.items():
        rows=sorted(rows_by_run[sid],key=lambda r:r['step_index']);graph=graphs[sid]
        steps=[]
        for row in rows:
            i=row['step_index']
            scores={'paper_nibs_cos_max':row['paper_nibs_cos_max'],
                    'paper_nibs_cos_mean':row['paper_nibs_cos_mean'],'tool_sim_nibs':row['confidence']}
            for method in LEARNED:
                scores[method]={seed:predictions[method][seed]['scores'][sid][i] for seed in SEEDS}
            message=sim['messages'][row['message_index']]
            calls=message.get('tool_calls') or []
            steps.append({'index':i,'event':row['event_id'],'kind':row['kind'],'tool':row['tool'],
                          'label':row['label'],'reason':row['label_reason'],'message_index':row['message_index'],
                          'content':plain(message.get('content')),'arguments':calls[0].get('arguments') if calls else None,
                          'scores':scores})
        mapped={s['event']:s for s in steps}
        nodes=[]
        for nid,n in graph.nodes.items():
            step=mapped.get(n['event'])
            label=(step['tool'] if step and step['tool'] else ('Assistant message' if step else 'User context'))
            if nid=='ROOT':label='Initial state'
            text=plain(n['text'])
            nodes.append({'id':nid,'event':n['event'],'kind':n['kind'],'scorable':n['scorable'],
                          'label':label,'text':text[:2400],'text_truncated':len(text)>2400})
        target_data={}
        for method in LEARNED:
            t=teachers[method].get(sid)
            if not t:continue
            pairs=[]
            for ref in t['references']:
                pair=read(EXPERIMENT/f'pairs/{method}/{sid}_{ref}.json')
                pairs.append({'id':ref,'mask':pair['mask'],'node_map':pair['node_map'],'edge_map':pair['edge_map']})
            target_data[method]={'events':t['events'],'mask':t['mask'],'references':pairs}
        messages=[]
        for i,m in enumerate(sim.get('messages') or []):
            messages.append({'index':i,'role':m.get('role'),'content':plain(m.get('content')),
                             'tool_calls':[{'name':c.get('name'),'arguments':c.get('arguments')} for c in m.get('tool_calls') or []],
                             'error':bool(m.get('error'))})
        first=next((s['event'] for s in steps if s['kind']=='tool_call' and s['label']=='incorrect'),None)
        fold=predictions[LEARNED[0]]['7']['heldout_fold'][sid]
        item={'id':sid,'task':str(sim['task_id']),'success':rows[0]['success'],'reward':sim['reward_info']['reward'],
              'steps':len(steps),'tool_steps':sum(s['kind']=='tool_call' for s in steps),
              'references':rows[0]['n_references'],'nibs_available':rows[0]['reference_available'],
              'teacher_available':sid in teachers[LEARNED[0]],'first_error':first,'fold':fold}
        run_index.append(item)
        details[sid]={'run':item,'steps':steps,'messages':messages,
                      'graph':{'nodes':nodes,'edges':graph.edges,'topology':graph.topology},
                      'teachers':target_data,'nibs_references':refs.get(sid,[])}
    # Post-hoc teacher diagnostic. All methods use the SAME 860 query subset.
    # Its same-task reference access is explicit; these are not held-out inputs.
    eligible=set(teachers[LEARNED[0]])
    diag_rows=[r for r in base_rows if r['run_id'] in eligible]
    diagnostics={'population':'860 MCS-target-eligible queries; post-hoc diagnostic, distinct from the primary 911 comparison',
                 'queries':len(eligible),'methods':{},'baseline_same_subset':{},'scope':'tool_calls'}
    for method in LEARNED:
        mapping={sid:dict(zip(t['events'],t['mask'])) for sid,t in teachers[method].items()}
        direct=[{**r,'confidence':mapping[r['run_id']][r['event_id']]} for r in diag_rows]
        learned={}
        for seed in SEEDS:
            learned[seed]=metric_subset([{**r,'confidence':predictions[method][seed]['scores'][r['run_id']][r['step_index']]} for r in diag_rows])
        hist={}
        for label in ['correct','incorrect','unverified']:
            t=[r['confidence'] for r in direct if r['kind']=='tool_call' and r['label']==label]
            hist[label]={'n':len(t),'mean_teacher_score':statistics.mean(t) if t else None}
        diagnostics['methods'][method]={'direct_teacher':metric_subset(direct),'learned':learned,'target_score_by_label':hist}
    for key in ['paper_nibs_cos_max','paper_nibs_cos_mean','tool_sim_nibs']:
        field='confidence' if key=='tool_sim_nibs' else key
        diagnostics['baseline_same_subset'][key]=metric_subset([{**r,'confidence':r[field]} for r in diag_rows])
    task_list=[]
    for tid,task in sorted(tasks.items(),key=lambda x:int(x[0])):
        rr=[r for r in run_index if r['task']==tid]
        ins=(task.get('user_scenario') or {}).get('instructions') or {}
        task_list.append({'id':tid,'goal':ins.get('reason_for_call','') if isinstance(ins,dict) else str(ins),
                          'instructions':ins if isinstance(ins,dict) else {'description':str(ins)},
                          'passes':sum(r['success'] for r in rr),'fails':sum(not r['success'] for r in rr),
                          'runs':len(rr),'nibs_eligible':sum(r['nibs_available'] for r in rr),
                          'teacher_eligible':sum(r['teacher_available'] for r in rr)})
    histories=read(EXPERIMENT/'training_histories.json')
    presets={}
    for item in sorted(run_index,key=lambda r:(int(r['task']),r['id'])):
        if item['success'] or not item['first_error'] or not item['teacher_available']:continue
        steps=details[item['id']]['steps']
        simplified=[]
        for step in steps:
            ss={k:(v['7'] if isinstance(v,dict) else v) for k,v in step['scores'].items()}
            simplified.append({**step,'scores':ss})
        a=ranks(simplified,'paper_nibs_cos_mean');b=ranks(simplified,'paper_gibs_pdf');c=ranks(simplified,'c4_gibs')
        if a==1 and b==0:presets.setdefault('nibs_catches',item['id'])
        if c==1 and b==0:presets.setdefault('c4_helps',item['id'])
        if a==0 and b==1:presets.setdefault('gibs_catches',item['id'])
    presets['successful_run']=next(r['id'] for r in run_index if r['task']=='25' and r['success'])
    meta={'experiment_id':experiment_id,'experiment_label':f"3–{plan['maximum_references']} references",
          'source_directory':str(EXPERIMENT.relative_to(ROOT)),
          'generated_utc':datetime.now(timezone.utc).isoformat(),'experiment_completed_utc':state['ended_utc'],
          'snapshot_sha256':plan['snapshot_sha256'],'summary_sha256':sha(EXPERIMENT/'summary.json'),
          'provider':'ASU-hosted Qwen3.8-27B','assistant_temperature':1,'user_temperature':0,
          'collection':read(ROOT/'results/free_asu/main-qwen38-27b-serial-none/COLLECTION_RESULTS.json'),
          'human_review':'Pending; no independent reviewer labels completed',
          'label_counts':summary['label_counts'],'phase':'Phase 2 prototype; recorded-results demonstration',
          'teacher_min_references':plan['minimum_references'],'teacher_max_references':plan['maximum_references'],
          'feature_tokens':256,'architecture':'2-layer GCN, hidden 128, dropout 0.1; frozen BERT features',
          'folds':{k:len(v['test']) for k,v in plan['folds'].items()},'presets':presets}
    OUT.mkdir(parents=True,exist_ok=True)
    dashboard={'meta':meta,'summary':summary,'tasks':task_list,'runs':run_index,
               'diagnostics':diagnostics,'histories':histories}
    write(OUT/'dashboard.json',dashboard)
    (OUT/'dashboard.js').write_text('window.TRACE_EXPERIMENTS=window.TRACE_EXPERIMENTS||{};window.TRACE_EXPERIMENTS['+json.dumps(experiment_id)+']='+json.dumps(dashboard,ensure_ascii=False,allow_nan=False,separators=(',',':'))+';\n')
    for sid,detail in details.items():write_run(sid,detail)
    # Replace only this exporter's old generated run JSONs; original experiment
    # results are untouched. JS data assets allow direct offline file opening.
    for stale in (OUT/'runs').glob('*.json'):stale.unlink()
    for name in ['REPORT.md','per_task.csv']:
        shutil.copy2(EXPERIMENT/name,OUT/name)
    write(OUT/'diagnostics.json',diagnostics)
    # Verify only whitelisted data were emitted; compare known local credential
    # values without ever printing them or exporting the environment.
    keys=[]
    for f in [ROOT/'.env.asu',ROOT/'.env']:
        if f.exists():
            for line in f.read_text().splitlines():
                if '=' in line and not line.lstrip().startswith('#'):
                    k,v=line.split('=',1);v=v.strip().strip('\"\'')
                    if any(t in k for t in ['KEY','TOKEN','SECRET']) and len(v)>10:keys.append(v.encode())
    for path in list(OUT.rglob('*.json'))+list(OUT.rglob('*.js')):
        payload=path.read_bytes()
        assert not any(k in payload for k in keys),'Credential detected in export; do not serve it'
    print(json.dumps({'exported_runs':len(details),'tasks':len(task_list),'agent_steps':len(base_rows),
                      'teacher_queries_per_method':len(eligible),'preset_ids':presets,
                      'export_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
                      'credential_scan':'pass','data_directory':str(OUT)},indent=2))


if __name__=='__main__':
    for experiment_id in EXPERIMENTS:build(experiment_id)
