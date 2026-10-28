# Validation of graph-matching configurations A / B / C

Stage: similarity-methodology validation only. **No GCN training and no full-task consensus scoring were done.**
The consensus targets below (`m_node`, `m_ctx`) are consensus signals, **not ground-truth step correctness**.

| File | Content |
|---|---|
| `pairs.json` | pre-registered pairs, evidence for demonstrably incorrect steps, and expected behaviour |
| `run_validation.py` | the experiment (reuses the step graph, projection, NLI and MCS code; C is an optional hook) |
| `results/runs.json` | every mapping, candidate, rejection, truncated comparison and cost, per pair and configuration |
| `results/tables.md` | generated summary and per-step tables (A/B/C side by side, reasons for every unmatched step) |

**Pre-registration.** `pairs.json` was written before configuration C existed and before any A/B/C run
(sha256 `c075979c6f45f90d00426fe52da910a9d7794ec1a070bae48a06dfb08426d738`, 2026-10-27 04:22 UTC; the same hash
is recorded in `runs.json`). Caveat: V1 and V2 had already been run under B in the previous stage, so their B
expectations are not blind. "Demonstrably incorrect" labels rest on task policy, NL assertions, gold actions and the
DB check, assigned by one annotator (me). They are not inferred from reward alone.

## 1. Configurations

| | A: paper-style baseline | B: event-context | C: event-context + structured fields |
|---|---|---|---|
| Projection | paper-literal: dependency edges only; dependency-free events hang from ROOT ([CODE] `NodeRaw` style) | event-context: + context edge from the preceding event [OURS] | as B |
| NLI | DeBERTa-large-MNLI, max of both directions [CODE], `a [SEP] b` string [CODE], truncation at 512 [CODE] | same | same |
| Thresholds | τe = τv = 0.7 [PDF] | same | same |
| Source-node threshold | yes (PDF prose, R3) | yes | yes |
| Expansion pool | all passing pairs (R4); top-10 seeds [PDF] | same | same |
| Size | edges + nodes [CODE] | same | same |
| Event-kind restriction | **off** (the paper has no node types) | on [OURS] | on [OURS] |
| Structured fields | no | no | **yes [OURS]**: extra rejections only (`gibs/mcs/structured_fields.py`) |

**Remaining deviations of A from the paper and author code.** Configuration A can't be literal, because our
trajectories are not `ReasoningGraph`s:
1. Every event (agent message, tool call + observation, user turn) becomes a step; there is no LLM-elicited
   `depends_on`, and value provenance is used instead.
2. ROOT↔ROOT = 1 without NLI. [CODE] runs NLI on "Problem/Initial State" against itself.
3. Source-node threshold (R3) and the all-candidates pool (R4) follow our reading of the PDF; [CODE] differs.
4. Only agent events are scored, and `m_ctx` is ours.
5. Rendering of tool calls and observations as text is ours.
6. [CODE] details not reproduced: the >15-node MCS skip, edge-level loss, and the comma-splitting bug.

**Structured-field rules (C).** A candidate whose NLI scores pass is **rejected only for a hard incompatibility**:
- the tool names differ;
- a decision-critical argument conflicts or is present in only one call: for writes, the arguments that determine
  the DB state; for reads, the arguments that identify what is read;
- error status differs;
- a reservation or user record conflicts on `status`, `created_at`, flights (number, date), passengers (name, DOB),
  payments, cabin, baggage, insurance, `membership`, `payment_methods` or `reservations`.

**Ordinary differences** are left to NLI: free-text arguments (transfer `summary`), flight prices, payment-key
spelling (`id`/`payment_id`), error wording and search-result lists. They are logged as `ignored`.

## 2. Pairs and coverage (selected before running)

| Pair | Task | Query (reward) | Reference | Category | Demonstrably incorrect step(s), evidence in `pairs.json` |
|---|---|---|---|---|---|
| V1 | 48 | 7f5cbcd7 (0) | c890f90b | success vs failure | s6 `cancel_reservation` (policy; NL assertion) |
| V2 | 48 | c890f90b (1) | 655b2a43 | success vs success, different paths | — |
| V3 | 40 | b4901df6 (0) | f6000fbe | success vs failure; similar observations, different critical field (DOB) | s10 update with DOB contradicting the record |
| V4 | 25 | d7a124a4 (0) | ab3d173b | success vs failure; identical write calls after differently worded confirmations | s40 cancels the existing reservation |
| V5 | 34 | 2a9a7a9b (0) | b47dbb44 | success vs failure | s12 `cancel_reservation` despite "keep original" |
| V6 | 9 | 68290327 (0) | 67030d75 | success vs failure | s10 offers a prohibited cancellation; s12 performs it |
| V7 | 4 (GPU) | 259d9890 (0) | ce8b1b6b | success vs failure; similar user records, different `payment_methods` | s12 compensation attempt; s20 certificate issued |
| V8 | 4 (GPU) | ce8b1b6b (1) | 54ecc816 | success vs success, different paths | — |
| V9 | 38 | c59e7ab6 (1) | 2a47da10 | success vs success, different paths | — |

**Category not available.** No pair of a passing and a failing run in our data has identical tool calls under
*contradictory* user instructions. The closest is V4: same-intent confirmations worded differently. The
contradictory case is covered only by synthetic unit tests (`test_consensus.py`, `test_structured_fields.py`).

## 3. Comparison (all 9 pairs; per-step tables in `results/tables.md`)

| Measure | A | B | C |
|---|---|---|---|
| First unmatched agent step as pre-registered (7 pairs with a prediction) | 6/7 | 6/7 | 6/7 |
| First unmatched step **is** the first demonstrably incorrect step (6 failure pairs) | 2/6 (V1, V6) | 2/6 | 2/6 |
| Demonstrably incorrect steps left unmatched (`m_node` / `m_ctx`) | 8/8 / 8/8 | 8/8 / 8/8 | 8/8 / 8/8 |
| Valid steps unmatched, success vs success: V2 / V8 / V9 (node-level) | 2/6, 8/10, 7/10 | 3/6, 8/10, 8/10 | 3/6, 8/10, 8/10 |
| Steps where `m_ctx` < `m_node` | 1 | 4 | 4 |
| Structured-field rejections | — | — | 2 |
| Mappings different from B | — | — | **none (9/9 identical)** |
| Truncated comparisons that fed a decision (decision flips under an alternative truncation) | 135 (2) | 217 (2) | 217 (2) |
| Compatible but excluded edges: disconnected / mapping conflict or BFS order | 5 / 9 | 11 / 8 | 9 / 8 |
| Directional NLI pairs required (cache-independent cost) | 3,770 | 3,792 | 3,792 |

Per pair, first unmatched agent step (node-level), identical in A, B and C except where noted:

| Pair | First unmatched | Pre-registered | Matches first incorrect step? | Why unmatched |
|---|---|---|---|---|
| V1 | s6 cancel | s6 ✓ | yes | best operation similarity to any reference step ≈ 0.1 |
| V2 | s6 refusal | s6 ✓ | n/a | no counterpart (the reference takes a different valid path) |
| V3 | s6 asks for DOB | s6 ✓ | no: precedes s10 | no counterpart. s10 update: NLI 0.457 (C also: `args.passengers` DOB conflict) |
| V4 | s2 `get_user_details('?')` | s2 ✓ | no: precedes s40 | erroneous but harmless lookup; no counterpart |
| V5 | s2 lookup | s2 ✓ | no: precedes s12 | different opening context; only the greeting matched |
| V6 | s10 offer to cancel | s10 ✓ | yes | no counterpart (the reference transfers) |
| V7 | s0 greeting | s12 ✗ | no | **connectivity**: the identical greeting (0.991) is a separate, smaller matched piece |
| V8 | s0 (B, C) / s2 (A) | no prediction | n/a | B/C: greeting disconnected; A: ROOT reconnects it |
| V9 | s4 (B, C) / s6 (A) | no prediction | n/a | B: paraphrased user turn breaks the chain; A and B: **truncation** (see F4) |

## 4. Findings

**F1. Every demonstrably incorrect action is unmatched, but so are many valid steps.** All 8 incorrect steps get
neither consensus target in every configuration. Only in 2/6 failure pairs is the *first* unmatched step the
incorrect one. In V3, V4 and V5 an earlier, benign divergence comes first: asking for the DOB, a harmless erroneous
lookup, a different opening. In successful-vs-successful pairs, 3/6 to 8/10 valid agent steps are unmatched (B).
With different valid paths, the MCS largely reflects the shared connected prefix.

**F2. Structured fields (C) changed no mapping in this sample.** The two rejections were real hard
incompatibilities:
- **V3:** the confirmation message whose source is the wrong-DOB update (`args.passengers`/`result.passengers`:
  1992-07-15 vs 1989-12-13). NLI rated the source observations 0.974.
- **V7:** a post-certificate `get_user_details` record (`result.payment_methods` contains `certificate_3221322`).
  NLI rated the source records 0.766 and the target observations 0.977.

Both elements were already unmapped in B through connectivity or thresholds. The field checks against each
unmatched tool step's best NLI partner (column "Field check" in `tables.md`) correctly separate hard conflicts (V3
s10; V7 s24, s32, s42) from compatible repeats (V7 s16, s26, s28: identical re-lookups excluded by injectivity).
C costs no extra NLI calls; field checks took ≤ 0.11 s per pair.

**F3. The context-aware target behaves as designed.** `m_ctx` < `m_node` for V3 s8 (lookup after the
user-supplied DOB turn), V4 s18 (identical booking call after a differently worded confirmation), V7 s4 and V8 s16.
Each is an identical or compatible call whose immediate context differs. In A there is no context edge, so this
happens once.

**F4. Author-code truncation produces false negatives for very long texts.** In V9, the two `get_user_details`
observations are **identical** (698 tokens each). Truncating the single joined `a [SEP] b` string at 512 tokens
leaves no hypothesis text, and DeBERTa scores 0.205. Pair encoding with `longest_first` truncation scores 0.994. The
threshold decision flips, and the identical lookups `s6`/`s8` are unmatched in A, B and C. Configuration C cannot
repair this, because it only rejects. In V1–V8 no truncated comparison flipped (0 flips among the other
truncated comparisons), but truncation is pervasive: V4 alone has 103–140 truncated comparisons.

**F5. The connected-subgraph restriction excludes compatible steps.** V7/V8: the identical greeting (0.991) is
dropped because it forms a smaller piece. V2: the identical transfer notice. V9: an identical `get_flight_status`.
A recovers some of these through ROOT (V2 s10, V8 s0) but loses context sensitivity. Mapping conflicts (8–9 edges)
are mostly repeated identical calls that injectivity limits to one counterpart (V4 s26, V7 s16, s26).

**F6. Runtime.**
- **Load and total time:** model load 5.3 s; the whole experiment took about 10 min wall time on MPS.
- **Per pass:** uncached scoring costs about 0.18 s per directional pair with long texts (A: 2,973 passes in 539 s).
- **Cache order:** B and C mostly hit the cache because A ran first, so their 21 s / 0.4 s are not comparable.
  Use the cache-independent counts: 184–886 directional pairs per pair-configuration, growing with |E1|·|E2|.
- **Longest pairs:** V4 (Task 25, 50 query edges) and V7 (51 messages).

## 5. Failure cases and limitations

* **Benign early divergence precedes the error** (V3, V4, V5). The first unmatched step is not a reliable error
  locator when dialogues diverge harmlessly before the mistake.
* **Connectivity artifacts** (V7 greeting). The first unmatched step can be an identical step that is merely
  disconnected. Any first-unmatched evaluation must separate "no counterpart" from "disconnected".
* **Paraphrased user turns** (V9 s4; probe P11) break the event-context chain at τ = 0.7.
* **Truncation false negatives** (F4) on observations longer than about 500 tokens.
* **Sample.** 9 pairs; mostly the Groq T=0 regime (V7/V8 are GPU T=1); V1/V2 not blind for B; one annotator for
  incorrect-step evidence; the contradictory-instruction category exists only synthetically.
* **The structured rules are hand-written for the airline tools.** Unknown tools fall back to tool-name equality.
  The field list is a judgement about DB-relevant fields, not a learned or validated set.

## 6. Recommendation

1. **For subsequent consensus-mask generation, use C as the primary adapted configuration and A as the paper-style
   comparison, reporting `m_node` and `m_ctx` separately.**
   - C matched B on every observed mapping at no extra NLI cost.
   - It adds traceable protection against the NLI blind spot measured earlier (probe P07/P08) and seen here (V3, V7).
   - It keeps B's context sensitivity (F3).
   - A should be kept because it is the closest to the paper, and it recovers some disconnected steps (F5).
2. **Do not start full-task scoring until truncation is resolved (F4).** The smallest change is to switch only
   overlength pairs from the author-code single-string truncation to pair encoding with `longest_first`
   truncation. That is a documented deviation from [CODE]: it gives 0.994 instead of 0.205 on identical texts. The
   alternative is a compact text rendering of tool results. Either needs your approval.
3. **Expect low recall for valid steps after a divergence** (F1, F5). With about 10 references per task, `m` may
   still be informative in aggregate, but this sample does not show that. If you want to address it, a
   multi-component MCS is a further deviation from the paper's single-seed algorithm and should be a separate,
   approved experiment.

Stopped here, as requested: no GCN training and no full-task scoring.
