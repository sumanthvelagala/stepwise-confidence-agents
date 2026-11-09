"""
Export ALL run steps (pass + fail) for all eligible tasks to CSV for annotation.

Each row = one AgentStep from any run with a valid reward.
Columns:
  task_id, run_id, outcome, step_idx, kind, tool, op_text, result_text,
  conversation_context, gold_actions, nl_assertions, label, reason

Usage:
    python3 export_annotation_csv.py
Writes: annotations/steps_to_annotate_all.csv  (merges existing labels from steps_to_annotate.csv)
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, '.')
from gibs.graph.step_graph import build_step_graph

# All 24 tasks with pass rate 3-17 (strict) from Pardha's 1000-trajectory dataset
ELIGIBLE = [1, 2, 9, 11, 12, 15, 16, 17, 18, 20, 21, 22, 23, 24,
            32, 33, 35, 37, 39, 40, 41, 42, 43, 47]

OUT     = Path('annotations/steps_to_annotate_all.csv')
OLD_CSV = Path('annotations/steps_to_annotate.csv')
OUT.parent.mkdir(exist_ok=True)

data = json.load(open('results/free_asu/main-qwen38-27b-serial-none/results.json'))
info = data['info']
tasks_map = {int(t['id']): t for t in data['tasks']}

COLUMNS = [
    'task_id', 'run_id', 'outcome', 'step_idx', 'kind', 'tool',
    'op_text', 'result_text',
    'conversation_context',
    'gold_actions', 'nl_assertions',
    'label',   # fill: correct / incorrect / tool_error
    'reason',  # fill: why
]


def gold_actions_str(task):
    actions = (task.get('evaluation_criteria') or {}).get('actions') or []
    return ' | '.join(
        f'{a["name"]}({json.dumps(a.get("arguments", {}))})'
        for a in actions
    )


def nl_assertions_str(task):
    nl = (task.get('evaluation_criteria') or {}).get('nl_assertions') or []
    return ' | '.join(nl)


def conversation_context(sim, up_to_msg_idx):
    """Return conversation text up to (not including) this message index."""
    messages = sim.get('messages') or []
    lines = []
    for m in messages[:up_to_msg_idx]:
        role = m.get('role', '')
        content = (m.get('content') or '').strip().replace('\n', ' ')
        calls = m.get('tool_calls') or []
        if calls:
            for c in calls:
                lines.append(
                    f'[agent tool] {c.get("name")}({json.dumps(c.get("arguments") or {})})'
                )
        elif content:
            lines.append(f'[{role}] {content}')
    return ' || '.join(lines)


rows = []
skipped = 0

for tid in ELIGIBLE:
    task = tasks_map.get(tid)
    if task is None:
        print(f'Task {tid}: not found in dataset, skipping')
        continue

    gold = gold_actions_str(task)
    nl   = nl_assertions_str(task)

    all_sims = [s for s in data['simulations']
                if int(s['task_id']) == tid
                and (s.get('reward_info') or {}).get('reward') is not None]

    for sim in all_sims:
        reward  = (sim.get('reward_info') or {}).get('reward', 0.0)
        outcome = 'pass' if reward >= 0.5 else 'fail'

        try:
            sg = build_step_graph(sim, info, task)
        except Exception as e:
            print(f'  skip run {sim["id"]}: {e}')
            skipped += 1
            continue

        for step_idx, node in enumerate(sg['nodes']):
            if node['type'] != 'AgentStep':
                continue

            kind   = node.get('kind', 'message')
            tool   = node.get('tool_call', {}).get('name', '') if kind == 'tool_call' else ''
            op     = (node.get('op_text') or '').replace('\n', ' ')
            result = (node.get('result_text') or '').replace('\n', ' ')

            # find context: match by raw message index stored in node
            ctx = ''
            raw_indices = node.get('raw_message_indices') or []
            if raw_indices:
                ctx = conversation_context(sim, raw_indices[0])

            rows.append({
                'task_id':              tid,
                'run_id':               sim['id'],
                'outcome':              outcome,
                'step_idx':             step_idx,
                'kind':                 kind,
                'tool':                 tool,
                'op_text':              op,
                'result_text':          result,
                'conversation_context': ctx,
                'gold_actions':         gold,
                'nl_assertions':        nl,
                'label':                '',
                'reason':               '',
            })

# Merge existing labels from old CSV (matched by run_id + step_idx)
existing_labels = {}
if OLD_CSV.exists():
    with open(OLD_CSV) as f:
        for row in csv.DictReader(f):
            if row.get('label'):
                key = (row['run_id'], row['step_idx'])
                existing_labels[key] = {'label': row['label'], 'reason': row.get('reason', '')}
    print(f'Loaded {len(existing_labels)} existing labels from {OLD_CSV}')

carried = 0
for row in rows:
    key = (row['run_id'], str(row['step_idx']))
    if key in existing_labels:
        row['label']  = existing_labels[key]['label']
        row['reason'] = existing_labels[key]['reason']
        carried += 1

with open(OUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)

print(f'\nExported {len(rows)} steps to {OUT}  (skipped {skipped} runs)')
print(f'Carried over {carried} existing labels from {OLD_CSV.name}')
print('\nPer task:')
by_task = {}
for r in rows:
    by_task.setdefault(r['task_id'], 0)
    by_task[r['task_id']] += 1
for tid, n in sorted(by_task.items()):
    print(f'  Task {tid:2d}: {n} steps')
