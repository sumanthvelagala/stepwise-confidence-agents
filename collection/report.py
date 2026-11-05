"""Write a collection report only after all 50 x 20 graded attempts are saved."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from collection.audit import audit
from collection.run_tau2 import write_json
from gibs.validation.dataset_audit import canon


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    source=args.directory/'results.json';payload=source.read_bytes();data=json.loads(payload)
    sims=data['simulations']
    if len(sims)!=1000 or len({(str(s['task_id']),s['trial'],s['seed']) for s in sims})!=1000:
        raise ValueError('The 1,000 unique task/trial/seed records are not complete')
    counts=Counter(str(s['task_id']) for s in sims)
    if counts != Counter({str(i):20 for i in range(50)}):
        raise ValueError('Expected exactly 20 saved attempts for each of 50 tasks')
    checked=audit(data)
    if checked['totals'].get('infrastructure_error',0):
        raise ValueError('Retry infrastructure failures before reporting 1,000 graded trajectories')
    manifest=json.loads((args.directory/'collection_manifest.json').read_text())
    success=checked['totals'].get('success',0);failed=checked['totals'].get('failure',0)
    classes=defaultdict(set)
    for sim in sims:
        if sim['reward_info']['reward']>=.5: classes[str(sim['task_id'])].add(canon(sim))
    result={'saved_graded_trajectories':1000,'tasks':50,'attempts_per_task':20,
            'official_benchmark_successes':success,'official_benchmark_failures':failed,
            'official_benchmark_pass_rate':success/1000,'distinct_task_content_classes':checked['distinct_task_content_classes'],
            'unbuildable_graphs':checked['totals'].get('unbuildable_graphs',0),
            'reward_success_missing_expected_tool_names':checked['totals'].get('reward_success_missing_expected_tool_names',0),
            'input_sha256':hashlib.sha256(payload).hexdigest(),
            'pre_resume_snapshots':len(list((args.directory/'attempt_snapshots').glob('*.json'))),
            'model':manifest['configuration']['model'],'confidence_method_accuracy':'Not measured by this collection report'}
    write_json(args.directory/'COLLECTION_RESULTS.json',result)
    lines=['# Completed ASU trajectory collection','',
           f'**1,000 graded trajectories: {success} official benchmark passes and {failed} failures ({success/10:.1f}% pass rate).**','',
           'This is the generating airline agent’s task pass rate. It is not NIBS/GIBS/C4 error-detection accuracy.',
           'Customers and the airline database are simulated benchmark data.','',
           f'- All 50 Airline tasks have exactly 20 saved task/trial/seed combinations.',
           f'- Distinct task/content classes: {checked["distinct_task_content_classes"]}.',
           f'- Graph-parser failures: {result["unbuildable_graphs"]}.',
           f'- Reward-success runs missing expected tool names: {result["reward_success_missing_expected_tool_names"]}; review flags, not relabelled failures.',
           f'- Model: `{result["model"]}` through ASU’s no-charge API.',
           '- Agent temperature 1, customer temperature 0; reasoning and parallel calls disabled.',
           '- Failed infrastructure attempts remain in pre-resume snapshots; native internal retries are not a complete API-request ledger.',
           '- Official reward does not verify every step. Reference review and independent labels remain necessary.',
           '', '| Task | Graded | Pass | Fail | Distinct successful classes |','|---|---|---|---|---|']
    for tid in sorted(counts,key=int):
        c=checked['per_task'][tid]
        lines.append(f'| {tid} | 20 | {c.get("success",0)} | {c.get("failure",0)} | {len(classes[tid])} |')
    lines+=['','The separate fresh comparison worker computes new paper/C4 MCS targets, trains the graph predictors,',
            'and evaluates them against NIBS and simple baselines. The all-task out-of-fold results belong in `results/fresh_all_tasks/`.',
            'Do not substitute the agent pass rate above for confidence-method accuracy.','',f'Input SHA256: `{result["input_sha256"]}`','']
    (args.directory/'COLLECTION_RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
