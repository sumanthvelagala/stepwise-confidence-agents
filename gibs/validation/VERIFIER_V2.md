# Step verifier v2: correction report

**Status:**
- v1 (`step_verification.py`) is unchanged. Every existing pilot, C4, C5 and C6 label and result was produced with
  v1 and stays as is.
- v2 (`step_verification_v2.py`, `VERSION = "2.0"`) is a separate module, to be used for new evaluations.
- Tests: `gibs/tests/test_step_verification_v2.py` (14).

## 1. The defects in v1

`classify_steps` (v1), for tasks whose gold actions contain writes:

1. **First-gold-only comparison.** It compares a successful write with `gold_same_tool[0]`, the **first** gold
   action of that tool, only. A write that equals a *later* gold action of the same tool is labelled `incorrect`.
2. **Global "done" flag.** After any gold-matching write it sets one flag shared by **all** tools. Every later
   successful write is then labelled "duplicate", even a correct write of a *different* tool that has its own gold
   action.

**Observed effect on the 346 valid runs (3,386 steps): exactly 5 false `incorrect` labels, all from defect 1.**
Defect 2 produced no wrong label in this data. It is demonstrated on a synthetic case.

| Task | Run | Step | Write | Gold | v1 | v2 |
|---|---|---|---|---|---|---|
| 7 | `39faed8b` (failed) | s8 | `cancel_reservation(59XX6W)` | g4 = `cancel_reservation(59XX6W)`; v1 compared it with g3 = `cancel(XEHM4B)` | incorrect | **valid (g4)** |
| 7 | `c0be2f86` (failed) | s18 | `cancel_reservation(59XX6W)` | g4 | incorrect | **valid (g4)** |
| 42 | `ec3d7c00` (failed) | s14 | `cancel_reservation(HSR97W)` | g9; v1 compared it with g8 = `cancel(FDZ0T5)` | incorrect | **valid (g9)** |
| 42 | `cdd54c3d` (failed) | s18 | `cancel_reservation(HSR97W)` | g9 | incorrect | **valid (g9)** |
| 42 | `69591e6d` (failed) | s26 | `cancel_reservation(HSR97W)`, after a correct `cancel(FDZ0T5)` | g9; v1 called it a "duplicate" (both defects) | incorrect | **valid (g9)** |

**Genuine negatives in the same runs remain `incorrect`:**
- T7 `c0be2f86 s16`: an update on the wrong reservation, with wrong flights.
- T42 `69591e6d s22`: cancels SE9KEL, which is not in the gold actions.

**No pilot label changes.** T48 and T9 have no gold writes, and T25 has one booking; a test asserts identical labels
for every T48, T9 and T25 run. Tasks 28, 1, 5 and 2 (the evaluation tasks) have no gold writes either, and v1 = v2
on all their steps.

## 2. v2 rule (only the write-matching branch changes)

For a **successful** write in a task with gold writes:
1. Collect all gold writes of the same tool.
2. Keep those whose DB-critical call fields (`CALL_FIELDS`, as in v1) do not conflict.
3. Label the write by the first match:
   - if one of them is **not yet matched**, the write is `valid`, and that gold action is consumed (one-to-one,
     multiset);
   - if all compatible ones are already matched, it is a **duplicate** → `incorrect`;
   - if none is compatible, it is `incorrect`, with the conflicts against **every** gold write of the tool listed;
   - if the gold actions contain no write of that tool, it is `incorrect` (unchanged).

**Unchanged from v1:**
- read calls (valid if equal to any gold read);
- the transfer-message rule;
- writes in tasks without gold writes (`incorrect` / `attempted_incorrect`);
- errored writes in tasks with gold writes (`unverified`).

## 3. Order and final database state: deliberately diagnostics only

`verify_run_v2` reports:

| Field | Meaning | Data |
|---|---|---|
| `missing_gold_writes` | gold writes never matched: errors of **omission**, which cannot be a step label | — |
| `order_inversions` | matched gold writes executed in a different relative order than listed | **0** runs with inversions in the data |
| `db_consistency` | does `expected_db_ok` (all gold writes matched and no incorrect successful write) agree with the benchmark's `db_match`? | **330 / 330 consistent**; 16 runs have no `db_check` (`max_steps` / `too_many_errors`) |

**Why order and DB state are not used for labels:**
- **Order.** τ²-bench scores the final DB, and gold lists are not guaranteed to encode a required order.
- **Independence.** `db_match` is part of the run's reward. Using it would make labels reward-derived, losing the
  independence the pilot required.

`db_consistency` is a weak sanity check. v1 is also consistent on these 330 runs, because the five affected runs
failed for other reasons, i.e. omitted writes.

## 4. Remaining ambiguities (unchanged in v2; documented)

| Case | v2 behaviour | Note |
|---|---|---|
| A write equal to a gold action on `CALL_FIELDS` but different on unchecked fields (e.g. prices) | valid | as v1; the field list is a design decision of configuration C |
| An errored write in a task with gold writes, including a prohibited tool | `unverified` | as v1. A stricter rule (`attempted_incorrect` when the tool is absent from the gold writes) would change labels and is not adopted |
| Two compatible gold writes with identical fields | consumed in gold order | labels are the same either way |
| Correct writes in a run that later fails | `valid` | step correctness ≠ run success (the five corrected labels are all in failed runs) |
| Messages, other than the policy transfer message | `unverified` | unchanged |

## 5. Files

- `gibs/validation/step_verification_v2.py` (new; imports v1 helpers unchanged).
- `gibs/tests/test_step_verification_v2.py` (new). It covers:
  - the five real false labels;
  - preserved true negatives;
  - pilot invariance;
  - duplicates beyond the gold count;
  - repeated identical gold actions;
  - order;
  - the global-flag defect;
  - all-gold conflict reasons;
  - unchanged branches;
  - omission and DB diagnostics.
