# Variant comparison C0–C3: symmetric truncation and multi-component MCS

Stage: methodology validation. **No full-task consensus scoring and no GCN training were done.** Configuration C
remains the primary adaptation and A the paper-style baseline. This report does **not** claim C improves on B: the
previous validation found identical final mappings for B and C.

| File | Content |
|---|---|
| `variants_criteria.md` | measures and the false-match definition, written before running |
| `run_variants.py` | the experiment (reuses `run_validation.analyse`; same nine pairs, unchanged `pairs.json`) |
| `results_variants/variants.json`, `results_variants/tables.md` | all outputs and generated tables |

`pairs.json` was not modified (sha256 `c075979c…d738`, recorded in `variants.json`). The original A/B/C validation
still reproduces exactly after the refactor of `run_validation.analyse` (all fields except timing and cache
counters were checked), and its original result files are kept.

## 1. What was added (all [OURS], none paper-specified)

| Change | Where | Default | What it does |
|---|---|---|---|
| Symmetric truncation | `DebertaEntailment(overlength="symmetric")`, `symmetric_input_ids` in `gibs/mcs/nli.py` | off (`"truncate"` = author code, kept) | Only for pairs longer than 512 tokens. Splits the author-code token sequence `[CLS] a [SEP] b [SEP]` into its two texts and head-truncates each to a fair share of the budget (each gets half; a shorter text is kept whole and the other gets the rest). Total ≤ 512, both texts always present. Pairs that fit are encoded byte-identically to before. Separate cache key. |
| Multi-component MCS | `find_mcs_multi` in `gibs/mcs/multi_component.py` | off (`find_mcs` unchanged) | Component 0 is the unchanged single-component result. Further components are seeded from the top 10 remaining candidates that are consistent with the **global** node map, and grown with the same BFS and compatibility rules checked against the global maps. Node and edge mappings are one-to-one across all components. It does not union independent MCS results. It uses the same candidate list, so the 0.7 thresholds and the structured-field rejections are inherited. |

Unit tests (`gibs/tests/test_variants.py`, 11 tests; the whole suite is 60 passed) cover:
- identical long texts: both represented, total ≤ 512;
- the author-code truncation dropping the second text;
- a short text paired with a long one being kept whole;
- short pairs being byte-identical to before;
- a conflicting field at the head surviving truncation;
- multi-component recovering a disconnected identical step;
- component 0 equalling the baseline;
- one-to-one mappings with duplicated calls;
- contradictory instructions still giving `m_ctx` = 0;
- field-rejected pairs never being added.

## 2. Symmetric truncation on real texts (DeBERTa scores, max of both directions)

| Case | Joined tokens | Author code | Symmetric | Decision changes? |
|---|---|---|---|---|
| Identical long user records (V9) | 1,396 | **0.205** | **0.993** | **yes** (false negative fixed) |
| Identical lookup observations (P06) | 584 | 0.978 | 0.980 | no |
| Cancel vs lookup observation, `status` cancelled vs null (P07) | 613 | 0.978 | 0.973 | no (still a false positive for NLI) |
| Update observations, different DOB (P08) | 584 | 0.974 | 0.969 | no (still a false positive for NLI) |
| User records before vs after certificate (V7) | 1,030 | 0.766 | 0.991 | no (passes either way; C's field check rejects it) |
| Short pair: identical greeting | 22 | 0.991 | 0.991 | identical score |
| Short pair: cancel vs lookup call (P05) | 40 | 0.0004 | 0.0004 | identical score |

Across all NLI comparisons used by C0 on the nine pairs (1,896 unique text pairs, each scored in both directions; **39 over 512 tokens**),
symmetric truncation changed **1 decision**: the V9 identical user records. Symmetric truncation repairs
truncation-induced false negatives on identical or near-identical long records. It does **not** make DeBERTa
sensitive to single conflicting fields (P07, P08). That remains the job of the structured-field check.

## 3. Results per variant (nine pre-registered pairs)

| Measure | C0 | C1 (symmetric) | C2 (multi-component) | C3 (both) |
|---|---|---|---|---|
| Demonstrably incorrect steps left unmatched, `m_node` / `m_ctx` | 8/8 / 8/8 | 8/8 / 8/8 | 8/8 / 8/8 | 8/8 / 8/8 |
| First unmatched step = first demonstrably incorrect step (6 failure pairs) | 2/6 | 2/6 | 2/6 | 2/6 |
| First unmatched step as pre-registered (7 predictions) | 6/7 | 6/7 | 5/7 | 5/7 |
| Valid steps unmatched, V2 (node / ctx) | 3/6 / 3/6 | 3/6 / 3/6 | **1/6** / 2/6 | **1/6** / 2/6 |
| Valid steps unmatched, V8 | 8/10 / 9/10 | 8/10 / 9/10 | 7/10 / 8/10 | 7/10 / 8/10 |
| Valid steps unmatched, V9 | 8/10 / 8/10 | 6/10 / 8/10 | 5/10 / 8/10 | **4/10 / 6/10** |
| Agent steps unmatched, all pairs (node / ctx) | 75 / 79 | 73 / 79 | 65 / 76 | 64 / 74 |
| Step indicators changed vs C0, `m_node` (gained / lost) | — | +4 / −2 | +10 / −0 | +11 / −0 |
| Step indicators changed vs C0, `m_ctx` (gained / lost) | — | +2 / −2 | +3 / −0 | +5 / −0 |
| Pairs whose final mapping changed | — | 1/9 (V9) | 6/9 | 6/9 |
| Additional components added | — | — | 7 in 6 pairs | 6 in 6 pairs |
| False matches (pre-specified criteria) | — | 0 | 0 | 0 |

Notes on the table:
- **C1 alone in V9 is a trade-off, not a pure gain.** With a single component, repairing the user-record
  comparison makes a *different* component the largest. Steps s4, s6, s8 and s12 are gained and the greeting
  steps s0 and s2 are lost. C3 keeps both.
- **The two pre-registration misses in C2/C3 are consequences of recovery, not errors.**
  - V5: the lookup `s2` is now matched through a second component (the identical call), so the first unmatched
    step moves to `s4` (`get_user_details`, which the reference never calls). It still precedes the incorrect
    `s12`.
  - V7: the greeting is recovered, so the first unmatched step moves from `s0` to `s2`, an agent message with no
    counterpart. The prediction was `s12`, so it was already a miss in C0.
- **The first-unmatched step still equals the incorrect action in only 2/6 failure pairs** (V1, V6) in every
  variant. Benign earlier divergences (V3, V4, V5, V7) are unaffected by these changes.

## 4. False-match review (every newly matched or re-mapped step; criteria fixed beforehand)

| Pair · variant | Step | C0 → variant (node/ctx) | Query step | Reference step | Verdict |
|---|---|---|---|---|---|
| V2 · C2, C3 | s10 | 0/0 → 1/1 | "YOU ARE BEING TRANSFERRED…" | identical | correct recovery |
| V2 · C2, C3 | s8 | 0/0 → 1/0 | `transfer_to_human_agents(summary=…claims booking was made 10 hours ago…)` | `transfer_to_human_agents(summary=…cannot cancel basic economy…)` | not false (same action). The node is mapped only as the source of the matched s10 edge; its own operation is not (summaries 0.28), so `m_ctx` = 0 |
| V3 · C2, C3 | s12 | 0/0 → 1/0 | "updated… Mei Garcia **(DOB: 1992-07-15)**" | "updated… Mei Garcia." | **borderline**: same communicative act, so not false by the criteria. It relays the incorrect DOB, and max-bidirectional NLI accepts it because the reference is entailed by the longer query text. It is matched only as the source of its successor edge. `m_ctx` stays 0 because C's field check rejects its context edge from the wrong update |
| V5 · C2, C3 | s2 | 0/0 → 1/0 | `get_reservation_details(HXDUBJ)` | identical call and observation | correct (the context differs, so `m_ctx` = 0) |
| V5 · C2, C3 | s8 | 0/0 → 1/0 | `search_direct_flight(2024-05-23, SFO→IAH)` | identical | correct (context differs) |
| V7, V8 · C2, C3 | s0 | 0/0 → 1/1 | greeting | identical | correct recovery |
| V9 · C1, C2, C3 | s4 | 0/0 → 1/0 | "help locate it… provide your user ID" | "help locate your most recent booking… share your user ID" | correct (paraphrase) |
| V9 · C1, C3 | s6, s8 | 0/0 → 1/1 | `get_user_details`, `get_reservation_details(SDZQKO)` | identical | correct (repaired by symmetric truncation) |
| V9 · C2 | s8 | 0/0 → 1/0 | `get_reservation_details(SDZQKO)` | identical | correct |
| V9 · all | s12 | 0/0 → 1/0 | `get_flight_status(HAT228, 2024-05-27)` | identical | correct (context differs) |
| V9 · C1 | s0, s2 | 1/1 → 0/0 | greeting; asks for reservation ID | — | **lost** in C1 only (single-component trade-off) |

**No demonstrably incorrect step became matched in any variant, and no tool step was matched across a structured
conflict.**

## 5. Runtime and cost

* The cache-independent NLI work is identical for all variants: the same 1,896 unique text pairs (92–440 per
  pair, each scored in both directions). Symmetric truncation re-scores only the 39 overlength comparisons (×2 directions). Multi-component
  matching needs no extra NLI calls: it reuses the candidate list.
* Wall time for the whole run was 39 s (mostly cache hits). Multi-component overhead was ≤ 0.2 s per pair on the
  largest graph (V4: 50 query edges). The uncached forward passes were the symmetric re-scoring and flip checks
  (≤ 11 per pair).

## 6. Limitations

* **Symmetric truncation keeps the head of each text.** A conflicting field near the end of a long record can still
  be cut, although NLI ignores such conflicts anyway (P07, P08). The structured-field check is unaffected by
  truncation because it uses the full parsed observation.
* **Node-level membership through a successor edge** (V2 s8, V3 s12) counts a step as consensus-supported without
  its own operation matching. That is the paper's definition. With more components this happens more often, and
  `m_ctx` is the signal that withholds support in both observed cases.
* **Additional components can be single edges** (`min_edges` = 1). In this sample all were correct, but generic
  short texts (greetings, transfer notices) are the typical recovered steps, and they carry little diagnostic
  information.
* **Sample.** 9 pairs, one annotator, and V1/V2 not blind (as before). The verdicts in §4 apply manual criteria
  that were fixed in advance.

## 7. Recommendation

1. **Adopt C3 (symmetric truncation + multi-component MCS) as the candidate configuration for consensus-mask
   generation, report C0 alongside it, and keep A as the paper-style baseline.** In this sample, C3:
   - recovered the most valid steps in the success-vs-success pairs: V2 3 → 1, V8 8 → 7, V9 8 → 4 unmatched
     (node-level);
   - introduced no false matches under the pre-specified criteria;
   - left every demonstrably incorrect action unmatched;
   - added no NLI cost.
   Both changes are our adaptations and must be reported as deviations from the PDF (single-component Alg. 4) and
   the author code (single-string truncation).
2. **Do not adopt C1 alone.** In V9 it trades matched steps between components rather than recovering them.
3. **Report `m_node` and `m_ctx` side by side.** The multi-component variant increases node-level support through
   successor edges (V2 s8, V3 s12); `m_ctx` is the conservative target in those cases.
4. **These changes do not fix error localisation:** the first unmatched step is still the incorrect action in only
   2/6 failure pairs. Whether aggregated masks over about 10 references are informative still has to be shown
   with full-task scoring, which needs your approval.

Stopped here: no full-task consensus scoring and no GCN training.
