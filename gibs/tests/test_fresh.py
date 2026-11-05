"""Fresh-data split and teacher integrity; no model calls/downloads."""
import argparse
import json
from pathlib import Path

import pytest

from gibs.fresh.experiment import prepare, read_teachers, references, scenario_groups, split_runs
from gibs.fresh.folds import grouped_folds


def test_shared_entities_and_identical_scenarios_cannot_cross_test_boundary():
    tasks=[{'id':str(i),'user_scenario':{'instructions':{'known_info':f'user_{chr(97+i)}_123',
                                                       'reason_for_call':f'case {i}'}}} for i in range(8)]
    tasks[1]['user_scenario']['instructions']['known_info']='user_a_123'
    tasks[2]['user_scenario']['instructions']['reason_for_call']='case 1'
    groups=scenario_groups(tasks)
    assert any({'0','1','2'} <= set(ids) for ids in groups.values())
    runs=[{'id':f'{i}-{j}','task_id':str(i),'content_hash':f'h{i}-{j}','success':bool(j%2)}
          for i in range(8) for j in range(8)]
    split,_=split_runs(runs,tasks)
    again,_=split_runs(list(reversed(runs)),list(reversed(tasks)))
    assert {p:[r['id'] for r in rs] for p,rs in split.items()} == {p:[r['id'] for r in rs] for p,rs in again.items()}
    test_tasks={r['task_id'] for r in split['test']}
    assert not test_tasks & {r['task_id'] for r in split['train']+split['validation']}
    for ids in groups.values():
        assert not (set(ids)&test_tasks) or set(ids)<=test_tasks


def test_reference_bank_excludes_query_class_wrong_task_and_failures():
    q={'id':'q','task_id':'1','content_hash':'same','success':False}
    pool=[q,{**q,'id':'copy','success':True},{**q,'id':'other','content_hash':'x','task_id':'2','success':True},
          {**q,'id':'failed','content_hash':'f'},
          {**q,'id':'reference','content_hash':'r','success':True}]
    assert [r['id'] for r in references(q,pool)]==['reference']


def test_four_folds_cover_every_query_once_and_share_only_training_legal_teachers():
    from gibs.fresh.experiment import order
    tasks=[{'id':str(i),'user_scenario':{'instructions':{'known_info':f'user_{chr(97+i)}_123',
             'reason_for_call':f'case {i}'}}} for i in range(8)]
    runs=[{'id':f'{i}-{j}','task_id':str(i),'content_hash':f'h{i}-{j}','success':j<6}
          for i in range(8) for j in range(10)]
    global_split,folds,_=grouped_folds(runs,tasks,scenario_groups,order)
    heldout=[r['id'] for f in folds.values() for r in f['test']]
    assert len(heldout)==len(set(heldout))==len(runs)
    for split in folds.values():
        test_tasks={r['task_id'] for r in split['test']}
        train_ids={r['id'] for r in split['train']}
        assert not test_tasks & {r['task_id'] for r in split['train']+split['validation']}
        for q in split['train']+split['validation']:
            common=references(q,global_split['train'],5)
            local=references(q,split['train'],5)
            assert [r['id'] for r in common]==[r['id'] for r in local]
            assert {r['id'] for r in local}<=train_ids


def test_partial_collection_requires_explicit_opt_in(tmp_path):
    path=tmp_path/'results.json';path.write_text(json.dumps({'simulations':[]}))
    args=argparse.Namespace(output=tmp_path/'out',input=path,allow_partial=False,expected_runs=1000)
    with pytest.raises(ValueError,match='incomplete'):
        prepare(args)
    assert not (args.output/'input/results.json').exists()


def test_teacher_from_another_query_or_validation_reference_is_rejected(tmp_path):
    def run(sid,success):
        return {'id':sid,'task_id':'1','success':success,'content_hash':sid,'nodes':[{'id':'s0'}]}
    reference=run('reference',True);q=run('query',False);v=run('validation',False)
    split={'train':[reference,q],'validation':[v],'test':[]}
    plan={'maximum_references':0,'minimum_references':1,'snapshot_sha256':'frozen'}
    folder=tmp_path/'teachers/paper_gibs_pdf';folder.mkdir(parents=True)
    for r in [q,v]:
        (folder/f'{r["id"]}.json').write_text(json.dumps({'query':r['id'],'references':['reference'],
             'snapshot_sha256':'frozen','events':['s0'],'mask':[.5]}))
    masks=read_teachers(plan,split,'paper_gibs_pdf',tmp_path)
    assert set(masks)=={'query','validation'}
    bad=json.loads((folder/'query.json').read_text());bad['query']='another-query'
    (folder/'query.json').write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='identity/reference'):
        read_teachers(plan,split,'paper_gibs_pdf',tmp_path)
    bad['query']='query';bad['references']=['validation']
    (folder/'query.json').write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='identity/reference'):
        read_teachers(plan,split,'paper_gibs_pdf',tmp_path)


def test_training_reporting_and_reload_with_recorded_historical_fixture(tmp_path,monkeypatch):
    # Exercise the new training/reporting path with existing real graph targets.
    # This is an integration fixture, not a claimed fresh ASU training result.
    import gibs.fresh.experiment as fresh
    from gibs.learned.data import StoredTeachers,fold_split,load_dataset
    runs,_,_=load_dataset()
    split=fold_split(runs,'25')
    stored=StoredTeachers(runs)
    plan={'split':{p:[r['id'] for r in rs] for p,rs in split.items()},
          'minimum_references':3,'maximum_references':0,'snapshot_sha256':'historical-integration-fixture'}
    for method,key in [('paper_gibs_pdf','paper_style'),('c4_gibs','agent_adapted')]:
        folder=tmp_path/'teachers'/method;folder.mkdir(parents=True)
        for q in split['train']+split['validation']:
            target,_=stored.target(key,q,split['train'])
            refs=references(q,split['train'])
            (folder/f'{q["id"]}.json').write_text(json.dumps({'query':q['id'],'references':[r['id'] for r in refs],
                'mask':target.tolist(),'events':[n['id'] for n in q['nodes']],
                'snapshot_sha256':plan['snapshot_sha256']}))
    monkeypatch.setattr(fresh,'load',lambda args:(plan,runs,split))
    args=argparse.Namespace(output=tmp_path,feature_device='cpu',epochs=3,seeds=[7])
    fresh.train_and_evaluate(args)
    summary=json.loads((tmp_path/'summary.json').read_text())
    histories=json.loads((tmp_path/'training_histories.json').read_text())
    assert set(summary['learned'])=={'paper_gibs_pdf','c4_gibs'}
    assert summary['n_common_test_runs']>0
    assert all(h['max_weight_change']>0 for h in histories.values())
    assert (tmp_path/'REPORT.md').exists()
    assert (tmp_path/'human_review/review/labels.csv').exists()
    assert len(list((tmp_path/'checkpoints').glob('*.pt')))==2


def test_crossfit_reports_every_task_and_scores_every_query_once(tmp_path,monkeypatch):
    # Synthetic plumbing fixture only: never written into research results.
    import torch
    import gibs.fresh.experiment as fresh
    from gibs.fresh.crossfit import run
    tasks=[{'id':str(i),'user_scenario':{'instructions':{'known_info':f'user_{chr(97+i)}_123',
            'reason_for_call':f'case {i}'}}} for i in range(8)]
    runs=[]
    for i in range(8):
        for j in range(10):
            good=j<6;sid=f'{i}-{j}'
            steps=[{'idx':k,'tool':name,'args':{'value':j}} for k,name in enumerate(['lookup','write'])]
            nodes=[{'id':f's{k}','kind':'tool_call','tool_call':{'name':name}} for k,name in enumerate(['lookup','write'])]
            runs.append({'id':sid,'task_id':str(i),'content_hash':sid,'success':good,'multiplicity':1,
                         'nodes':nodes,'parsed':{'steps':steps},'message_indices':[0,1],
                         'labels':{'s0':{'label':'valid','reason':'fixture'},
                                   's1':{'label':'valid' if good else 'incorrect','reason':'fixture'}},
                         'task':tasks[i],'policy':'unit test only','source':'synthetic fixture',
                         '_sim':{'id':sid,'task_id':str(i),'messages':[{'role':'assistant','content':'fixture'}]*2}})
    teacher_split,folds,_=grouped_folds(runs,tasks,fresh.scenario_groups,fresh.order)
    plan={'minimum_references':3,'maximum_references':5,'snapshot_sha256':'synthetic-test-only',
          'folds':{name:{p:[r['id'] for r in rs] for p,rs in f.items()} for name,f in folds.items()}}
    torch.manual_seed(7)
    feats={r['id']:{'results':torch.randn(3,768),'operations':torch.randn(3,768),
                   'adjacency':torch.eye(3),'agent_indices':torch.tensor([1,2])} for r in runs}
    monkeypatch.setattr(fresh,'features',lambda runs,device:(feats,{'unit_test_only':True}))
    for method in fresh.METHODS:
        folder=tmp_path/'teachers'/method;folder.mkdir(parents=True)
        for q in teacher_split['train']+teacher_split['validation']:
            refs=references(q,teacher_split['train'],5)
            (folder/f'{q["id"]}.json').write_text(json.dumps({'query':q['id'],'references':[r['id'] for r in refs],
                 'mask':[1.,.2],'events':['s0','s1'],'snapshot_sha256':plan['snapshot_sha256']}))
    args=argparse.Namespace(output=tmp_path,feature_device='cpu',epochs=1,seeds=[7])
    run(args,plan,runs,teacher_split)
    summary=json.loads((tmp_path/'summary.json').read_text())
    assert summary['n_scored_oof_runs']==80 and summary['n_tasks']==8
    assert len(list((tmp_path/'checkpoints').glob('*.pt')))==8
    for method in fresh.METHODS:
        pred=json.loads((tmp_path/f'query_only_predictions/{method}_seed7.json').read_text())
        assert set(pred['scores'])=={r['id'] for r in runs}
    import csv
    table=list(csv.DictReader((tmp_path/'per_task.csv').open()))
    assert {r['task_id'] for r in table}=={str(i) for i in range(8)}
