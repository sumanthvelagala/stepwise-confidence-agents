"""Build the two-setting comparison and five evidence-based demo cases.

Reads completed exports and reports only. Does not run models or change results.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nibs.evaluation_metrics import target_rank

DATA=ROOT/'demo_ui/dist/data'
METHODS=('paper_gibs_pdf','c4_gibs','paper_nibs_cos_mean','paper_nibs_cos_max','tool_sim_nibs')
NAMES={'paper_gibs_pdf':'GIBS','c4_gibs':'C4','paper_nibs_cos_mean':'NIBS Mean',
       'paper_nibs_cos_max':'NIBS Max','tool_sim_nibs':'tool_sim',
       'last_step_first':'Last-step-first','random_expected':'Random expectation'}
PLAIN_ERRORS={
    '53791b7d-4fff-4313-8fb0-5c65607ac2a7':'The agent sends a compensation certificate. The expected action list contains no write action, so the automatic verifier flags this as an extra action.',
    '1bbd75e4-f4f4-445e-86a6-a27f7a520b87':'The baggage update specifies one nonfree bag, while the expected call specifies zero. The automatic verifier flags this argument mismatch.',
    '1b84a141-f1a4-444c-ae3c-a3832e6ba4b7':'The agent combines three passengers in one booking, while the expected calls list the passengers separately. Payment allocations also differ. The verifier flags these passenger and payment mismatches.',
    '0857b47b-432c-478f-8ae8-f059ce8da11c':'The flight update selects HAT227 and HAT139, while the expected call selects HAT110 and HAT172. The automatic verifier flags the different itinerary.',
    '8cbb015d-dfb1-4f15-939b-570332b11463':'The agent cancels a reservation. The expected action list contains no write action, so the automatic verifier flags this cancellation. Inspect the transcript and policy before treating that label as human-verified truth.'}


def read_run(experiment,sid):
    text=(DATA/f'{experiment}/runs/{sid}.js').read_text()
    marker='window.TRACE_RUNS['+json.dumps(experiment)+']['+json.dumps(sid)+']='
    return json.loads(text.split(marker,1)[1][:-2])


def evidence(data,seed='7'):
    tools=[s for s in data['steps'] if s['kind']=='tool_call']
    error=next(s for s in tools if s['event']==data['run']['first_error'])
    result={}
    for method in METHODS:
        def score(s):
            v=s['scores'][method]
            return v[seed] if isinstance(v,dict) else v
        values=[score(s) for s in tools]
        ranks=target_rank(values,tools.index(error))
        low=min(values)
        result[method]={'error_score':score(error),**ranks,
                        'lowest_steps':[s['index'] for s,v in zip(tools,values) if v==low],
                        'lowest_score':low}
    targets={m:{'references':len(t['references']),'error_target':t['mask'][error['index']],
                'error_support_count':sum(p['mask'][error['event']] for p in t['references'])}
             for m,t in data['teachers'].items()}
    return {'methods':result,'targets':targets,'error_step':error['index'],
            'error_event':error['event'],'error_tool':error['tool'],'error_reason':error['reason']}


def build():
    dashboards={k:json.loads((DATA/f'{k}/dashboard.json').read_text()) for k in ('cap5','cap17')}
    assert dashboards['cap5']['meta']['snapshot_sha256']==dashboards['cap17']['meta']['snapshot_sha256']
    saved=json.loads((ROOT/'results/fresh_refs_3_17/REFERENCE_CAP_COMPARISON.json').read_text())
    assert saved['controlled_design_verified']
    candidates=[]
    for run in dashboards['cap17']['runs']:
        if run['success'] or not run['first_error'] or not run['teacher_available'] or not run['nibs_available']:
            continue
        a=read_run('cap5',run['id']);b=read_run('cap17',run['id'])
        ea,eb=evidence(a),evidence(b)
        assert ea['error_event']==eb['error_event']
        candidates.append({'run_id':run['id'],'task':run['task'],'tool_steps':run['tool_steps'],
                           'goal':next(t['goal'] for t in dashboards['cap17']['tasks'] if t['id']==run['task']),
                           'cap5':ea,'cap17':eb})
    def hit(c,experiment,method):return c[experiment]['methods'][method]['top1']==1
    def miss(c,experiment,method):return c[experiment]['methods'][method]['top1']==0
    specifications=[
        ('more_refs_help','More references help GIBS','GIBS improves on this run',
         lambda c:miss(c,'cap5','paper_gibs_pdf') and hit(c,'cap17','paper_gibs_pdf'),
         'At seed 7, GIBS misses the first labelled tool error with cap 5 and identifies it uniquely with cap 17. The graph and error label are unchanged; targets and learned weights come from the corresponding experiment.'),
        ('c4_regresses','C4 loses the first error','More references do not always help',
         lambda c:hit(c,'cap5','c4_gibs') and miss(c,'cap17','c4_gibs'),
         'At seed 7, C4 identifies the first labelled tool error with cap 5 but ranks another tool step lower with cap 17. This is an example of regression, not proof of a specific optimization cause.'),
        ('gibs_success','GIBS finds the first error','A GIBS localization success',
         lambda c:hit(c,'cap17','paper_gibs_pdf') and miss(c,'cap17','paper_nibs_cos_mean'),
         'At seed 7 under cap 17, GIBS assigns the first labelled tool error the unique lowest tool score; NIBS Mean ranks another step lower. A localization success does not mean the underlying booking task succeeded.'),
        ('nibs_beats_gibs','NIBS catches what GIBS misses','Direct matching wins this example',
         lambda c:hit(c,'cap17','paper_nibs_cos_mean') and miss(c,'cap17','paper_gibs_pdf'),
         'At seed 7 under cap 17, NIBS Mean uniquely identifies the first labelled tool error while GIBS misses it. NIBS has successful same-task references at scoring time; the held-out GCN sees only the query graph.'),
        ('gibs_failure','GIBS misses in both settings','A high-agreement target can still be wrong',
         lambda c:miss(c,'cap5','paper_gibs_pdf') and miss(c,'cap17','paper_gibs_pdf')
                  and c['cap17']['targets']['paper_gibs_pdf']['error_target']>=.8,
         'At seed 7, GIBS misses this error in both settings, although the cap-17 MCS teacher gives the erroneous step at least 0.8 support. This shows why agreement with successful structures is not correctness ground truth. Independent human validation is still needed.')]
    used=set();tasks=set();chosen={}
    for key,title,kicker,predicate,explanation in specifications:
        options=[c for c in candidates if c['run_id'] not in used and predicate(c)]
        assert options,'No genuine example found for '+key
        options.sort(key=lambda c:(c['task'] in tasks,abs(c['tool_steps']-7),int(c['task']),c['run_id']))
        selected=options[0];used.add(selected['run_id']);tasks.add(selected['task'])
        chosen[key]={'id':key,'title':title,'kicker':kicker,'explanation':explanation,
                     'plain_error':PLAIN_ERRORS[selected['run_id']],
                     'seed':'7','default_experiment':'cap17',**selected}
    # Present the success, miss and direct-reference contrast before the two changes.
    examples=[chosen[k] for k in ['gibs_success','nibs_beats_gibs','gibs_failure','more_refs_help','c4_regresses']]
    comparison={k:saved[k] for k in ['comparison','controlled_design_verified','n_common_runs',
                                   'n_all_scored_runs','human_validation','scopes']}
    comparison.update({'generated_utc':datetime.now(timezone.utc).isoformat(),
                       'snapshot_sha256':dashboards['cap17']['meta']['snapshot_sha256'],
                       'examples':examples,'example_seed':'7',
                       'example_selection':'Post-hoc illustrative cases chosen by actual tool-only first-error rankings, with MCS targets available. Not a representative sample or a new aggregate estimate.'})
    payload=json.dumps(comparison,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    (DATA/'comparison.json').write_text(payload+'\n')
    (DATA/'comparison.js').write_text('window.TRACE_COMPARISON='+payload+';\n')
    lines=['# Phase 2 demonstration: reference cap 5 versus cap 17','',
           'Same 1,000 tau2 Airline trajectories, all 50 tasks, frozen input, four task-group folds, seeds 7/17/27, graph implementation, architecture and objective. Minimum three references in both experiments. Only the maximum reference cap changes.',
           'Training targets use successful training-only references; NIBS evaluation uses its broader successful same-task reference bank. Actual cap-17 training counts range from 3 to 16. No new trajectories or LLM training were required.',
           'Each experiment has 860 targets per teacher family and 24 GCN checkpoints. All 1,000 trajectories receive held-out learned predictions. The common comparison has 911 queries; tool AUROC uses 26 tasks with both labelled classes and localization uses 173 eligible failed queries.',
           'Independent human review is pending. Unverified steps are not assumed correct. Learned results are three-seed means; differences are descriptive, with no significance test. These are our agent-benchmark results, not values copied from the paper.','',
           '## Main findings','',
           '- GIBS improves: tool AUROC 0.700 → 0.723 and first-error Top-1 34.1% → 40.7% (+6.6 percentage points).',
           '- C4 declines: tool AUROC 0.719 → 0.706 and Top-1 52.2% → 49.3% (−2.9 percentage points).',
           '- tool_sim has the best tool AUROC; NIBS Mean has the best first-error Top-1. GIBS/C4 still trail last-step-first (66.5%) on localization.',
           '- The reference-access difference, imperfect teacher targets and incomplete automatic labels limit conclusions. Extra references do not guarantee improved error detection.',
           '- A plausible explanation is that extra matches change the supervision targets; why C4 regresses specifically needs further diagnosis. This experiment does not isolate the mechanism.','']
    for scope in ['tool_calls','all_agent_steps']:
        lines+=['## '+scope.replace('_',' ').title(),'','| Method | 3–5 AUROC | 3–17 AUROC | 3–5 Top-1 | 3–17 Top-1 |','|---|---:|---:|---:|---:|']
        for method,vals in comparison['scopes'][scope].items():
            a,t=vals['auroc'],vals['top1']
            lines.append(f"| {NAMES[method]} | {a['five']['mean']:.4f} | {a['trial']['mean']:.4f} | {100*t['five']['mean']:.1f}% | {100*t['trial']['mean']:.1f}% |")
        lines.append('')
    lines+=['## Five actual examples','',comparison['example_selection'],
            'Every example below is a failed benchmark run. Success means identifying its first automatically labelled tool error, not solving the airline task. Predictions shown are from held-out seed-7 models. MCS targets are post-hoc diagnostics; they were not supplied to held-out inference.','']
    for i,e in enumerate(examples,1):
        b=e['cap17'];lines += [f"### {i}. {e['title']}",'',f"Task {e['task']} · run `{e['run_id']}` · seed 7.",
            '',e['goal'],'',e['plain_error'],'',e['explanation'],'',f"First labelled tool error: step {b['error_step']+1}, `{b['error_tool']}`. Verifier reason: {b['error_reason']}",'',
            '| Method | 3–5 error score | 3–5 rank | 3–17 error score | 3–17 rank |','|---|---:|---:|---:|---:|']
        for method in METHODS:
            a=e['cap5']['methods'][method];b=e['cap17']['methods'][method]
            lines.append(f"| {NAMES[method]} | {a['error_score']:.4f} | {a['rank_min']}–{a['rank_max']} | {b['error_score']:.4f} | {b['rank_min']}–{b['rank_max']} |")
        lines+=['','Rank 1 is the lowest tool score. Rank ranges show exact score ties; a tie is not counted as a unique hit.','']
        for cap in ['cap5','cap17']:
            for method,t in e[cap]['targets'].items():
                lines.append(f"- {cap}, {NAMES[method]}: error target {t['error_target']:.4f} = {t['error_support_count']:g} / {t['references']} successful-reference support indicators.")
        lines+=['',f"Local UI: `#explorer?experiment=cap17&run={e['run_id']}&example={e['id']}`. Inspect Step scores → Trajectory graph → MCS & targets → Transcript. Switch the active experiment to compare the same execution.",'']
    lines+=['## What remains','',
            'Human review of the proposed 20–30 failed runs, stakeholder feedback, and missing ACC@80%/ECE remain separate. Phase 3 deployment, monitoring and guardrails are not established by this read-only results UI.',
            '',f"Frozen input SHA256: `{comparison['snapshot_sha256']}`",'']
    report='\n'.join(lines)
    (ROOT/'demo_ui/DEMO_REPORT.md').write_text(report)
    (DATA/'COMPARISON_REPORT.md').write_text(report)
    print(json.dumps({'examples':[{k:e[k] for k in ['id','task','run_id']} for e in examples],
                      'comparison':'both completed experiments','report':'demo_ui/DEMO_REPORT.md'},indent=2))


if __name__=='__main__':build()
