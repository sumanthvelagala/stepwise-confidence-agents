"""
Interactive terminal annotator for steps_to_annotate.csv

Controls per step:
  c  → correct
  i  → incorrect
  e  → tool_error
  s  → skip (leave blank)
  b  → back (re-do previous step in this run)
  q  → quit and save

Run:
  python3 annotate.py
  python3 annotate.py --task 1       # only task 1
  python3 annotate.py --task 1 --run 2   # start from run index 2 (0-based)
"""

import csv
import sys
import os
import argparse
from pathlib import Path

CSV        = Path('annotations/steps_to_annotate_all.csv')
RESULTS    = Path('results/free_asu/main-qwen38-27b-serial-none/results.json')

LABEL_MAP = {'c': 'correct', 'i': 'incorrect', 'e': 'tool_error', 's': ''}

def load_policy():
    import json
    data = json.load(open(RESULTS))
    return data['info']['environment_info'].get('policy', '')

def load():
    with open(CSV) as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []
    with open(CSV) as f:
        fieldnames = csv.DictReader(f).fieldnames
    return rows, fieldnames

def save(rows, fieldnames):
    with open(CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def color(text, code):
    return f'\033[{code}m{text}\033[0m'

def label_color(lbl):
    if lbl == 'correct':   return color(lbl, '32')   # green
    if lbl == 'incorrect': return color(lbl, '31')   # red
    if lbl == 'tool_error': return color(lbl, '33')  # yellow
    return color('unlabeled', '90')

def wrap(text, width=100, indent='    '):
    import textwrap
    return '\n'.join(indent + line for line in textwrap.wrap(text, width))

def print_msg(role_label, role_code, text, width=92):
    import textwrap
    prefix    = f'  {role_label}  '
    cont      = ' ' * len(prefix)
    lines     = textwrap.wrap(text, width - len(prefix)) or ['']
    print(color(prefix, role_code) + lines[0])
    for line in lines[1:]:
        print(cont + line)
    print()

def show_step(s, step_num, total, policy=''):
    os.system('clear')
    task    = s['task_id']
    run     = s['run_id'][:8]
    outcome = s.get('outcome', '')
    out_str = ''
    if outcome == 'pass':
        out_str = '  ' + color('PASS', '32;1')
    elif outcome == 'fail':
        out_str = '  ' + color('FAIL', '31;1')
    print(color(f'═══ Task {task} │ Run {run}… │ Step {step_num}/{total} ═══', '1') + out_str)
    print()

    # Policy panel
    if policy:
        print(color('  POLICY', '1;33'))
        print(color('  ' + '─' * 76, '90'))
        for line in policy.splitlines():
            print('  ' + line)
        print(color('  ' + '─' * 76, '90'))
        print()

    # Full conversation thread leading up to this step
    ctx = s.get('conversation_context', '').strip()
    if ctx:
        print(color('  CONVERSATION', '1'))
        print(color('  ' + '─' * 76, '90'))
        for part in ctx.split(' || '):
            if part.startswith('[user] '):
                print_msg('USER   ▸', '35', part[7:])
            elif part.startswith('[assistant] '):
                print_msg('AGENT  ▸', '34', part[12:])
            elif part.startswith('[agent tool] '):
                print_msg('TOOL   ▸', '36', part[13:])
            elif part.startswith('[tool] '):
                print_msg('RESULT ▸', '33', part[7:])
        print(color('  ' + '─' * 76, '90'))
        print()

    # Current step being labelled
    kind = s['kind']
    tool = s['tool']
    if kind == 'tool_call':
        print(color(f'  ▶  LABEL THIS STEP  │  tool_call → {tool}', '1;36'))
    else:
        print(color(f'  ▶  LABEL THIS STEP  │  agent message', '1;34'))
    print()
    print(color('  OP TEXT:', '33'))
    print(wrap(s['op_text'], width=100))
    print()
    if kind == 'tool_call':
        print(color('  TOOL RESULT:', '33'))
        print(wrap(s['result_text'], width=100))
        print()

    if s['gold_actions']:
        print(color('  GOLD ACTIONS:', '90'))
        print(wrap(s['gold_actions'], width=100))
        print()
    if s['nl_assertions']:
        print(color('  NL ASSERTIONS:', '90'))
        print(wrap(s['nl_assertions'], width=100))
        print()
    cur = s['label']
    print(color(f'  Current label: {label_color(cur) if cur else color("(none)", "90")}', '0'))
    print()
    print(color('  [c] correct   [i] incorrect   [e] tool_error   [s] skip   [b] back   [p] policy   [q] quit', '90'))
    print()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task',    type=int, default=None)
    parser.add_argument('--outcome', type=str, default=None, choices=['pass', 'fail'],
                        help='only annotate runs with this outcome (pass or fail)')
    parser.add_argument('--run',    type=int, default=0,    help='run index to start from (0-based)')
    parser.add_argument('--step',   type=int, default=0,    help='step index within first run to start from (0-based)')
    parser.add_argument('--run-id', type=str, default=None, help='jump directly to a specific run ID (prefix ok)')
    args = parser.parse_args()

    rows, fieldnames = load()
    policy = load_policy()

    # Build run groups: list of (task_id, run_id, [row_indices])
    run_groups = {}
    for i, r in enumerate(rows):
        key = (int(r['task_id']), r['run_id'])
        run_groups.setdefault(key, []).append(i)

    # Filter and sort
    keys = sorted(run_groups.keys())
    if args.task is not None:
        keys = [k for k in keys if k[0] == args.task]
    if args.outcome is not None:
        keys = [k for k in keys
                if rows[run_groups[k][0]].get('outcome', '') == args.outcome]

    if args.run_id is not None:
        keys = [k for k in keys if k[1].startswith(args.run_id)]
        if not keys:
            print(f'No run found matching --run-id {args.run_id}')
            sys.exit(1)
    else:
        keys = keys[args.run:]

    total_runs = len(keys)
    for run_num, key in enumerate(keys):
        tid, rid = key
        indices  = run_groups[key]
        steps    = [rows[i] for i in indices]
        total_s  = len(steps)

        step_ptr = args.step if run_num == 0 else 0
        while step_ptr < total_s:
            s = steps[step_ptr]
            show_step(s, step_ptr + 1, total_s, policy)
            print(f'  Run {run_num+1}/{total_runs} │ ', end='', flush=True)

            inp = input('Label: ').strip().lower()

            if inp == 'q':
                save(rows, fieldnames)
                print('\nSaved. Bye!')
                sys.exit(0)
            elif inp == 'p':
                os.system('clear')
                print(color('═══ AIRLINE AGENT POLICY ═══', '1'))
                print()
                print(policy)
                print()
                input(color('  Press Enter to go back…', '90'))
                continue
            elif inp == 'b':
                if step_ptr > 0:
                    step_ptr -= 1
                continue
            elif inp in LABEL_MAP:
                rows[indices[step_ptr]]['label'] = LABEL_MAP[inp]
                rows[indices[step_ptr]]['reason'] = ''
                step_ptr += 1
            else:
                # invalid input, re-show
                continue

        # auto-save after each run
        save(rows, fieldnames)
        labeled = sum(1 for r in rows if r['label'])
        print(color(f'\n  ✓ Run saved. Total labeled: {labeled}/{len(rows)}', '32'))
        input('  Press Enter for next run…')

    save(rows, fieldnames)
    print(color('\nAll done!', '32'))

if __name__ == '__main__':
    main()
