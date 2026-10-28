# Evaluation protocol: Phase 2B (FINAL; frozen before any evaluation computation)

**Version:** 2B-final, 2026-10-27. Supersedes the Phase 2A draft. Changes from the draft:
- Task 2 is deferred;
- exposure categories are added;
- the reference-subset scheme and the exact-step recall definitions are made precise;
- the evaluation script is fingerprinted.

No NLI or MCS had been run on the evaluation tasks when this version was written. The only prior execution of
`run_eval.py` was a smoke test of the code path, using a **stub** NLI model and writing to the session scratchpad;
it produced no scores.

**What is evaluated:**
- valid-step coverage, unmatched valid steps, reference-count sensitivity and exact-step recall of **C4** tool-call
  consensus;
- exploratory message coverage of **C5 / C6**.

**What is not evaluated:** discrimination of incorrect steps. No difficult negatives exist in these tasks
(DATASET_AUDIT §8). **No discrimination claim may be made from Phase 2B.**

## 1. Frozen method

| Role | Variant | Code path |
|---|---|---|
| **Primary: tool-call consensus** | C4 | `run_c4.C4`: paper-literal projection, DeBERTa max-bidirectional, symmetric truncation, τ = 0.7, top-K 10, R3 source check, `require_same_kind`, structured-field rejection, multi-component MCS |
| Exploratory: message scoring | C5 | `two_stage.extend_messages(outcome_route=False)` on C4's tool part |
| Exploratory: message scoring | C6 | `two_stage.extend_messages(outcome_route=True)` |

**Fixed settings:**
- **Model:** `microsoft/deberta-large-mnli` @ `7296194b9009373def4f7c5dad292651e4b5cf4e`, MPS, fp32. The existing NLI
  cache is reused wherever valid; its keys include model revision, encoding and truncation mode.
- **Provenance:** all three variants are our adaptations, not the paper's GIBS method. C6 outcome support does not
  establish policy correctness.
- **Labels:** verifier **v2** (`step_verification_v2.classify_steps_v2`). On Tasks 1, 28 and 5 there are no gold
  writes, so v1 = v2.

**Code fingerprints** (sha256, first 16 hex). Any mismatch at run time is a deviation:

| File | sha256 |
|---|---|
| `gibs/graph/step_graph.py` | `58ae3f564f444a42` |
| `gibs/graph/event_projection.py` | `7293379987b701ef` |
| `gibs/mcs/mcs.py` | `ce4755e9bf054e17` |
| `gibs/mcs/multi_component.py` | `244f1e032a649bd4` |
| `gibs/mcs/nli.py` | `9ab8a7097ccb89cb` |
| `gibs/mcs/structured_fields.py` | `d334c925677c7a21` |
| `gibs/mcs/consensus.py` | `a130e3c2e6a269aa` |
| `gibs/mcs/two_stage.py` | `74c2b99ec1b18cac` |
| `gibs/validation/run_c4.py` | `57cfde65d5215491` |
| `gibs/validation/step_verification_v2.py` | `5ddac0b0d1af2219` |
| `gibs/validation/dedup.py` | `b5c98733012c4742` |
| `gibs/validation/dataset_audit.py` (provides the content hash) | `04db9ed37be7bd3b` |
| `gibs/validation/run_eval.py` | `5e92380faa279237` |

## 2. Tasks, runs and exposure

| Task | Role | Regime | Files | Valid runs (success / failed) | Content classes (successful) | **Exposure category** |
|---|---|---|---|---|---|---|
| **28** | coverage and stability | Groq `gpt-oss-20b`, T = 0 | `pilot/task_28`, `probe/remaining_batch` | 21 / 0 | 16 (16) | **Untouched hold-out:** no recorded prior use in any method |
| **1** | coverage and stability | Groq, T = 0 | `pilot/task_1_topup`, `pilot/tasks_1_3_9_38`, `probe/batch_2action` | 22 / 2 | 23 (21) | **Previously exposed:** scored in earlier NIBS / WL-graph work; not used to design or tune A or C0–C6 |
| **5** | agent-setup shift | local `gpt-oss:20b`, **T = 1.0** | `probe/task_5` | 14 / 2 | 16 (14) | **Previously exposed:** scored in earlier WL-graph work; not used to design or tune A or C0–C6 |
| 2 | **deferred** | — | — | — | — | not evaluated in Phase 2B |

**Reporting rule.** Results on T1 and T5 are labelled "held-out from GIBS-variant development, previously exposed".
Only T28 results may be called an untouched hold-out.

**Run selection:**
- every run of the task with a reward, in the regime listed;
- runs without a reward (infrastructure errors) are excluded, as are T5's T = 0 runs, all of which are
  infrastructure errors;
- the loader is `run_eval.load_task`. Step graphs are built with `info=None`.

**Label profile** (v2; computed from labels only, before scoring):

| Task | Labelled valid tool calls | Labelled valid messages | Incorrect steps |
|---|---|---|---|
| 28 | 0 (gold actions empty) | 16 policy transfer messages | 0 |
| 1 | gold reads: `get_user_details` 21 successful + 2 failed classes; `get_reservation_details` 16 successful | 20 transfer messages | 2: prohibited cancellations, structural |
| 5 | 1 (failed run) | 6 successful + 1 failed transfer messages | 2: `send_certificate`, structural |

**Consequences:**
- **T1 is the only task with substantial labelled tool-call evidence.**
- **T28 and T5 contribute through exact-step recall** (label-free, §6.2) **and message scores.**
- T5 has 8 of 14 successful runs with no tool call at all.

## 3. References and duplicates

- **Content classes** (`dedup.py`):
  - T28 has duplicate classes of size 5 and 2;
  - T1 has one of size 2;
  - T5 has none.
  - A class is represented by its smallest UUID.
- **Queries:** every content class, scored once, with multiplicity recorded.
- **References for a query:** one representative of every **successful** class of the same task and regime,
  **excluding the query's entire own class**.
- **Duplicates-retained view** (secondary; §6.5): per run, the references are all other successful runs, including
  copies of itself. A copy's MCS equals the class representative's, and an own-class copy uses a stored self-match.
- **Reference ceiling:** `cap(s)` = the fraction of the query's references containing a v2-valid step with the same
  key: `(tool, normalized arguments)` for gold reads, or `transfer_message`.

## 4. Procedure

```
.venv/bin/python -B gibs/validation/run_eval.py compute     # one process; lock file; resumable per query
.venv/bin/python -B gibs/validation/run_eval.py analyze
```

- **Compute:** for each query class and each reference, run C4, then C5 and C6 from C4's tool part. Self-matches are
  computed only for successful classes with duplicates. Outputs go to `results_eval/partial/task{T}/{query}.json`.
- **Analyze:** reads only these files. It re-derives candidate existence for §6.3 **from the NLI cache only**;
  uncached passes are counted.
- **Cost estimate [HYP]:** T1 23 × ≤ 21, T28 16 × 15, T5 16 × ≤ 14 pairs, i.e. about 950 pairs, mostly uncached NLI.
  Expected to take hours. Run under `caffeinate`; one process only.

## 5. Pre-registered expectations

These are directional, and are reported as met or not met. They are not tuning targets.

| ID | Expectation |
|---|---|
| E1 | C4 = C5 = C6 on every tool-call step: scores and maps (check S1) |
| E2 | No v2-`incorrect` step has C4 `m_node` or `m_ctx` ≥ 0.5. These are structural negatives only, not discrimination evidence |
| E3 | T1 `get_user_details` (gold read): mean C4 `m_ctx` ≥ 0.75. T1 `get_reservation_details`: mean `m_ctx / cap` ≥ 0.75 |
| E4 | No labelled valid step has `m_node` > `cap` + 1/n_refs |
| E5 | Transfer messages (T1, T28, T5): C6 mean `m_ctx / cap` ≥ 0.8; C5 lower |
| E6 | At k = 5, C4 mean absolute deviation (all tool steps) ≤ 0.10 in T1 and T28; T5 greater than T28 |
| E7 | C4 exact-step recall (context-supported, §6.2) ≥ 0.8 in T1 and T28; lower in T5 |

## 6. Metrics

All metrics are reported per task × variant: counts, means, medians and six-bin distributions
`[0 | (0,.25) | [.25,.5) | [.5,.75) | [.75,1) | 1]`. The unit is the content class unless stated otherwise.

### 6.1 Valid-step coverage

Over v2-valid steps: C4 for tool calls; C4, C5 and C6 for messages. Split by successful vs failed query.

- **Coverage_ctx@0.5** = the fraction with `m_ctx` ≥ 0.5. **Coverage_node@0.5** likewise for `m_node`.
- The distributions of `m_ctx`, `m_node` and `cap`.
- **Ceiling-normalised mean** = mean of `m_ctx / cap` over steps with `cap` > 0. The number with `cap` = 0 is
  reported separately.

### 6.2 Exact-step recall (label-free; tool calls; C4)

**Exact counterpart.** For a query tool step `s` and a reference `r`, the exact counterparts are the tool steps of `r`
with an identical tool name, identical arguments (canonical JSON) and an identical normalized result
(`two_stage.outcome_key`). Pairs `(s, r)` where `r` has at least one exact counterpart are **exact pairs**.

| Measure | Definition |
|---|---|
| **Node recall** | the fraction of exact pairs in which `s`'s node is mapped to **one of its exact counterparts** |
| **Context-supported recall** | the fraction of exact pairs in which `s`'s node is mapped to an exact counterpart **and** the `ctx` indicator is true (all incoming edges mapped) |

Also reported:
- **non-exact-supported pairs:** pairs with no exact counterpart in which `s` is node-mapped. These may be
  legitimate paraphrase or field-compatible matches, and each type is reviewed;
- the number of tool steps with any exact counterpart;
- recall split by label.

Exact agreement is not correctness.

### 6.3 Unmatched valid steps

**Every** v2-valid tool step with C4 `m_ctx` < 0.5 is listed. For each reference, the outcome is classified as:

| Code | Outcome |
|---|---|
| — | supported (`ctx` true) |
| (a) | the reference lacks a step with the same key (reference frequency) |
| (b) | node mapped, but an incoming edge not |
| (c) | no candidate between the step's incoming edges and the counterpart's incoming edges (NLI < 0.7 on edge, target or source; kind; or field rejection) |
| (d) | a candidate exists but was not selected (MCS selection or one-to-one consistency) |

Valid messages with `m_ctx` < 0.5 are listed per variant.

### 6.4 Reference-count sensitivity (deterministic)

- **Grid:** k ∈ {1, 2, 3, 5, 8, all}. A k larger than a query's reference count is skipped for that query.
- **Subsets:**
  - if C(n, k) ≤ 50, **all** combinations;
  - otherwise **50 distinct** combinations drawn with `random.Random(seed)`, where `seed` = the first 8 hex of
    `sha256("phase2b|{task}|{query_uuid}|{k}")` interpreted as an integer (`run_eval.subset_seed`). Subsets are
    order-independent and reproducible.
- **Statistics** per variant × scope (valid steps; all steps of the variant's kind), over all
  (query, step, subset) observations:
  - mean, median and 90th-percentile absolute deviation from the full-pool value;
  - mean valid `m_ctx`;
  - unexpected rate (valid `m_ctx` < 0.5), with a note that it is discrete at small k;
  - the number of observations and subsets.

### 6.5 Deduplication effect

C4 (tool) and C5 / C6 (message) valid-step means and coverage@0.5, under the deduplicated class view (primary) and
the duplicates-retained per-run view (secondary).

### 6.6 Agent-setup shift (T5 vs T28 and T1; descriptive)

Per task:
- distinct tool sequences;
- successful classes without tool calls;
- mean agent steps;
- the share of tool steps with any exact counterpart;
- mean C4 `m_ctx` of all tool steps;
- mean C5 and C6 `m_ctx` of all messages.

There is no significance test.

### 6.7 Messages (exploratory)

- Context-supported and node indicators per variant.
- Valid transfer-message coverage (§6.1).
- **Every** C6 outcome-route match listed. All non-identical-text pairs, and all pairs whose query message is in a
  failed run or follows an incorrect step, are manually reviewed with the REPORT_c4 §5 categories.

### 6.8 Separation of causes (report section)

Each low score is attributed to exactly one of:
1. **reference frequency:** `cap` or exact availability, §6.1–6.3 code (a);
2. **matching failure:** codes (b), (c), (d), or exact-pair misses;
3. **deduplication:** §6.5;
4. **agent setup:** §6.6, only as a descriptive contrast.

## 7. Safety and validity checks

| Check | Condition |
|---|---|
| S1 | C5 and C6 tool-call scores and maps identical to C4 |
| S2 | No cross-kind mapping; no mapped tool pair with a structured-field conflict |
| S3 | No reference from the query's own content class |
| S4 | Run and class counts equal §2 and §3 |
| S5 | Code fingerprints equal §1 |
| S6 | Uncached NLI passes reported, for compute and for analysis |

## 8. Outputs

All outputs go to `gibs/validation/results_eval/`, and nothing elsewhere is modified:
- `partial/`;
- `eval_summary.json`;
- `per_step_eval.csv`;
- cost files.

The report is `REPORT_PHASE2B.md`.

## 9. Deviations log

(empty)
