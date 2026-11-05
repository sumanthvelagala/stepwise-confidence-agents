"""Reference-cap comparisons must keep data, folds and executed math fixed."""
import copy
import hashlib
import json
import pytest
from gibs.fresh.reference_comparison import DESIGN_KEYS,verify_plans,verify_baseline,compare


def plans():
    baseline={k:'same' for k in DESIGN_KEYS}
    baseline.update({'minimum_references':3,'maximum_references':5,
                     'source_sha256':{'model.py':'same','cache.py':'preparation-version'},
                     'execution_source_sha256':{'cache.py':'runtime-version'}})
    trial=copy.deepcopy(baseline);trial['maximum_references']=0
    trial['source_sha256']['cache.py']='runtime-version'
    return baseline,trial


def test_runtime_verified_hash_supersedes_earlier_preparation_hash():
    b,t=plans();assert verify_plans(b,t)


def test_explicit_seventeen_reference_cap_is_supported():
    b,t=plans();t['maximum_references']=17;assert verify_plans(b,t)


@pytest.mark.parametrize('key',['snapshot_sha256','folds','seed','minimum_references','objective'])
def test_cannot_claim_reference_only_change_when_protocol_changed(key):
    b,t=plans();t[key]='changed'
    with pytest.raises(ValueError,match='Controlled design changed'):verify_plans(b,t)


def test_changed_executed_model_is_not_hidden_by_prepare_hash():
    b,t=plans();t['execution_source_sha256']['model.py']='changed'
    with pytest.raises(ValueError,match='Executed implementation changed'):verify_plans(b,t)


def test_baseline_protection_detects_overwritten_checkpoint(tmp_path):
    p=tmp_path/'checkpoint.pt';p.write_bytes(b'original saved weights')
    guard={'files':{'checkpoint.pt':hashlib.sha256(p.read_bytes()).hexdigest()}}
    verify_baseline(tmp_path,guard)
    p.write_bytes(b'replaced saved weights')
    with pytest.raises(ValueError,match='Protected baseline artifact changed'):verify_baseline(tmp_path,guard)


def test_report_compares_three_seed_means_instead_of_best_seed(tmp_path):
    # Synthetic reporting fixture only; no file enters research outputs.
    b,t=plans();before_dir=tmp_path/'baseline';after_dir=tmp_path/'trial'
    before_dir.mkdir();after_dir.mkdir()
    for folder,plan in [(before_dir,b),(after_dir,t)]:
        (folder/'plan.json').write_text(json.dumps(plan))
    def metrics(v):
        a={'macro_auroc':v,'localization':{'top1':v,'top3':v,'reciprocal_rank':v}}
        return {scope:{'aggregate':a} for scope in ['tool_calls','all_agent_steps']}
    def summary(vals):
        learned={m:{str(seed):metrics(v) for seed,v in zip([7,17,27],vals)} for m in ['paper_gibs_pdf','c4_gibs']}
        return {'n_input_runs':1000,'n_scored_oof_runs':1000,'n_tasks':50,'n_common_comparison_runs':911,
                'n_all_agent_steps':1000,'n_common_comparison_steps':911,'label_counts':{'test_fixture':1000},
                'seeds':[7,17,27],'snapshot_sha256':'test-fixture',
                'learned_common':learned,'learned_all':learned,'baselines':{'random_expected':metrics(.5)}}
    (before_dir/'summary.json').write_text(json.dumps(summary([.6,.8,.7])))
    (after_dir/'summary.json').write_text(json.dumps(summary([.9,.5,.7])))
    result=compare(before_dir,after_dir)
    row=result['scopes']['tool_calls']['paper_gibs_pdf']['auroc']
    assert row['trial']['n']==3 and row['trial']['mean']==pytest.approx(.7)
    assert row['delta']==pytest.approx(0)
    assert (after_dir/'REFERENCE_CAP_COMPARISON.md').exists()
