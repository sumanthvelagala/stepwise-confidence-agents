"""Four-fold task-group evaluation, sharing only task-local teacher calculations."""
from collections import Counter, defaultdict
import numpy as np


def task_split(runs, order):
    strata=defaultdict(list)
    for r in runs: strata[(r['task_id'],r['success'])].append(r)
    train,validation=[],[]
    for _,values in sorted(strata.items()):
        values=sorted(values,key=lambda r:order(r['content_hash']))
        n=min(len(values)-1,max(1,round(.2*len(values))))
        validation.extend(values[:n]);train.extend(values[n:])
    return {'train':sorted(train,key=lambda r:r['id']),
            'validation':sorted(validation,key=lambda r:r['id']),'test':[]}


def grouped_folds(runs,tasks,group_function,order):
    groups=group_function(tasks)
    occupied={r['task_id'] for r in runs}
    groups={g:[t for t in ids if t in occupied] for g,ids in groups.items() if occupied.intersection(ids)}
    if len(groups)<4: raise ValueError('Need at least four task groups')
    ordered=sorted(groups,key=order)
    folds={}
    for i,chunk in enumerate(np.array_split(ordered,4)):
        test_tasks={t for g in chunk for t in groups[str(g)]}
        split=task_split([r for r in runs if r['task_id'] not in test_tasks],order)
        split['test']=sorted([r for r in runs if r['task_id'] in test_tasks],key=lambda r:r['id'])
        if not all(split.values()): raise ValueError('Empty fold partition')
        hashes=[{r['content_hash'] for r in split[p]} for p in ('train','validation','test')]
        if any(hashes[a]&hashes[b] for a,b in ((0,1),(0,2),(1,2))):
            raise ValueError('Duplicate content crosses fold partitions')
        folds[f'fold{i}']=split
    tests=Counter(r['id'] for split in folds.values() for r in split['test'])
    if tests!=Counter({r['id']:1 for r in runs}): raise ValueError('Test coverage is not exactly once per trajectory')
    return task_split(runs,order),folds,groups
