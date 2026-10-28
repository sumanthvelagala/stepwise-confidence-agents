# Inspection: is tool-outcome-supported message matching sound?

**Inspection only.** No C6 code, no new NLI scores, no previous result modified.

Inputs:
- the 66 pilot trajectories;
- stored C3, C4 and C5 mappings (`results_pilot/`, `results_c4/`, `results_c5/`);
- deterministic comparisons of tool payloads with the existing structured-field rules: exact field or text equality,
  no similarity model.

Where a step needed "do the two messages entail each other?", the **stored C4 message mapping** is used as evidence
that NLI passed. Estimates built on it are upper bounds and are labelled **[EST]**.

Evidence tags:
- **[OBS]**: read from payloads or stored results.
- **[EST]**: an estimate.
- **[HYP]**: untested.

## 1. What tool results contain

There are 149 agent messages that immediately follow a tool call, grouped below by tool [OBS].

| Tool (task) | Messages after it | Result payload | Information in the result |
|---|---|---|---|
| `transfer_to_human_agents` (T48 10, T9 17, T25 1) | 28 | the plain string `Transfer successful` | **only that the call executed.** Not the summary, not the reason, not whether a transfer was appropriate |
| `book_reservation`, success (T25) | 20 | the full reservation record: id, flights + dates, passengers, payment_history, bags, insurance, status, created_at | everything the booking changed |
| `book_reservation`, error (T25) | 9 | `Error: Payment amount does not add up, total price is 375, but paid 299` | the failure and the amounts |
| `cancel_reservation` (T48 13, T9 3, T25 1) | 17 | the full record with status cancelled | what was cancelled |
| `update_reservation_flights` (T9) | 2 | the full updated record | the new flights |
| `get_reservation_details` (T48 15, T9 1, T25 22) | 38 | the full record | the record that was read |
| `get_user_details` (T25: 19 errors, 2 successes) | 21 | `Error: User ? not found` / `User user123 not found`, or the user record | the lookup failed on a placeholder id, or the record |
| `search_direct_flight`, `search_onestop_flight` | 10 | a list of flights, or `[]` | the available flights |
| `get_flight_status` | 3 | `available` | one word |

## 2. Three separate concepts

| Concept | Where it can be read | Pilot evidence |
|---|---|---|
| **A. Tool execution succeeded** | the observation's error flag | always available |
| **B. The action was correct under the request and policy** | **not** in the tool result. Needs the task's gold actions or policy (our independent labels) | T25 `6f12b024 s30`: execution succeeded and the result is a valid record, yet [VER] incorrect (May 21 / HAT267 instead of May 17 / HAT251). Transfer results are identical whether or not a transfer was appropriate |
| **C. The message accurately describes what happened** | partly checkable by comparing the message's stated facts with its own tool result | **All 20 T25 booking confirmations state flights and dates consistent with their own result, including the confirmation of the incorrect booking** (`6f12b024 s32`: HAT097 + HAT267, 2024-05-21 = its result). All 17 cancellation and 2 update confirmations name the result's reservation id. 0 of 9 messages after an errored booking claim success |

**Counter-examples to C, all in the pilot:**
- T9 `7cd3469e s14`, a **successful** run, ends with "YOU ARE BEING TRANSFERRED…", but no transfer call exists. The
  message claims an outcome that did not happen.
- T9 `7e3e8b73 s20`, a failed run, follows a successful transfer but also reports "Your reservation IFOYYZ has been
  cancelled". That is an *earlier* prohibited action, which the immediate tool outcome says nothing about.

**Consequence.** A tool outcome can support concept C, and only for facts that appear in the outcome. It cannot
support concept B. A message can be fully accurate (C) about an incorrect action (not B).

So outcome-based support can only be sound as a **cross-run** comparison: the query's outcome must equal a
reference's outcome. A within-run check that the message agrees with its own result would pass `6f12b024 s32`.

## 3. Would outcome-based support recover the valid transfer messages? [OBS + EST]

For every (valid transfer message, reference) pair where C4 had already mapped the message to the reference's
message, the reference's preceding tool call is also `transfer_to_human_agents`, with a **byte-identical** result
(`Transfer successful`, category `raw_identical`: T48 90 pairs, T9 210 pairs).

| Task | C3 `m_ctx` | C4 | C5 | **Outcome-supported upper bound [EST]** |
|---|---|---|---|---|
| T48 (10 messages) | 1.000 | 1.000 | 0.089 | **1.000** for every run |
| T9 (14 messages) | 0.938 | 0.996 | 0.232 | **0.938** for every run (15 of 16 references; the 16th, `7cd3469e`, has no transfer call) |
| T25 (1 message, failed run) | 0 | 0 | 0 | 0 (no successful run transfers) |

**Yes:** outcome support recovers them. The loss in C5 comes entirely from the transfer *summary* (free-text call
argument) failing NLI, and the message does not depend on the summary.

## 4. Could it support the T25 wrong-booking confirmation (`6f12b024 s32`)? [OBS]

**No**, as long as outcome equality is defined on the structured result fields.

C4 had mapped s32 to 15 reference messages:
- **14 of them follow the reference's gold booking.** In every case the results conflict on
  `result.flights` (`(HAT097, 2024-05-21), (HAT267, 2024-05-21)` ≠ `(HAT097, 2024-05-17), (HAT251, 2024-05-17)`) and on
  `result.payment_history` (card 171 ≠ 247).
- **1 follows a user turn** (`cd5be315 s24`), so there is no tool outcome to pair with.

No reference contains the same outcome, so the wrong confirmation stays unsupported.

**Conditions under which it would be supported:**
1. The outcome comparison is weakened, e.g. to error-flag-only or to NLI on the record text. The probe showed NLI
   scores such records about 0.97 despite conflicting fields (P07, P08).
2. The comparison becomes a within-run accuracy check (§2).
3. The reference pool contains another "successful" run with the same wrong booking. This is possible if success is
   judged loosely; not the case here.

## 5. Can tool outcomes fix the remaining false message matches? [OBS]

**No.**

**Correction to REPORT_c5 §4.2 and §5.** The "ask for date of birth ↔ present plan and ask for yes" pairs do **not**
follow user turns. I stated that without checking. Every one of the 7 pairs inspected follows the same successful
lookup, `get_reservation_details(G72NSF)` at `s8`:
- the 3 C3-origin panel pairs;
- the 4 C5 sample pairs.

C4 matches that lookup to an identical lookup (`record_equal`), which is why stage 2 accepts the message edge.

- **The outcomes are identical** in both runs: same reservation record.
- **What differs is the dialogue state.** In one run the agent still needs the passenger's date of birth; in the
  other it already has it, from an earlier user turn. Neither the immediately preceding outcome nor the message's
  context edge carries that.
- **The confusion is in message-level NLI**: the plan table includes the date of birth, so entailment passes in
  one direction.

Outcome support would leave these pairs exactly as they are.

**The same holds for the T9 pair `d5b7b555 s16 → 7cd3469e s14`.**
- Both follow `search_direct_flight(JFK→MCO, 2024-05-22)` → `[]`, an identical outcome.
- The messages perform different acts: a reservation status table vs "no flights; transferring you".
- The reference message claims a transfer that never happened.

## 6. The smallest defensible improvement

**Proposal (not implemented). "Outcome alignment" for messages whose preceding tool call is unmatched in stage 1.**

In C5's stage 2, a message context candidate whose query source is a tool node **not** matched by C4 would be
allowed **only if all** of the following hold:

1. **Same tool:** the reference source is the same tool.
2. **Exact outcome equality**, deterministic, with no similarity threshold:
   - both successful, and either the structured records are field-equal (existing `RESERVATION_FIELDS` /
     `USER_FIELDS`) or, for unstructured results, the raw result text is identical;
   - or both errors with identical error text.
3. **One-to-one:** the reference tool node is not stage-1-mapped to a different query node, and is not
   outcome-aligned to another query node.
4. **Unchanged message checks:** the message edge itself passes NLI ≥ 0.7, the kind restriction, and the target
   check.

**The tool node is not added to the node map.** The alignment is recorded separately and used only for the
message's context support. Tool scores therefore stay **identical to C4 by construction**, preserving the C5
invariance.

**Assumptions:**
- A1: a message's context is its immediately preceding tool **outcome**, not the call's free-text arguments.
- A2: exact equality of the outcome (record fields or raw text) means the same world-state change or observation
  was reported.
- A3: messages describe that outcome. Section 2 shows this fails for messages that also report earlier actions
  (`7e3e8b73 s20`).

**Potential false positives:**
1. **Identical outcomes from different calls.** Examples:
   - `[]` from searches on different dates or routes;
   - `Transfer successful` whether or not a transfer was appropriate;
   - `available` for different flights;
   - identical error strings.
   In the pilot, **0** outcome-equal pairs had conflicting call arguments [OBS], but nothing prevents this in
   general. A guard is to keep the existing **call-field** check where `CALL_FIELDS` defines fields: search
   date/route, flight number. This would not affect transfers, which have none.
2. **Messages that also narrate earlier actions** (`7e3e8b73 s20`). Support then rests on NLI between the whole
   messages.
3. **Accurate confirmations of incorrect actions** are blocked only because references contain no matching outcome.
   This is a property of the reference pool, not a guarantee.
4. **Transfer appropriateness** remains unjudged. Outcome support for a transfer message says "a transfer
   happened, as in correct runs", not "transferring was right".

**Expected tradeoffs [EST]:**
- **Gains:**
  - valid transfer messages back to about 1.0 (T48) and 0.938 (T9);
  - the T25 wrong-booking confirmation stays at 0;
  - tool scores unchanged.
- **No effect** on the date-of-birth/plan false matches or on other message-level NLI confusions (§5).
- **Semantics change** from "same message after the same matched action" to "same message after the same
  outcome". `m_ctx` for messages would then mean outcome-consistent consensus, not action-consistent consensus.
- **Scope:** in the pilot it would mainly affect messages after transfer calls.
  - C5 dropped 82 (T48) + 194 (T9) message candidates as `dropped_tool_unmatched`, and only 1 in T25.
  - [HYP] Most of these follow transfer calls, the only frequently unmatched tool that is followed by a message. The
    per-tool split of dropped candidates was not stored, so this is not verified.

**Not proposed (insufficient support):**
- **Within-run message–outcome consistency as a consensus signal.** It cannot detect incorrect actions (§2). It may
  be useful later as a separate accuracy flag, for example to catch `7cd3469e s14`.
- **Any change aimed at the date-of-birth/plan confusions through tool outcomes.** Those need dialogue-state
  evidence or a better message comparator, and are outside this proposal.

## 7. Files and reproducibility

- **New:** this file only. The inspection scripts were run from the session scratchpad and are not part of the
  repository.
- **Data used:** stored outputs and trajectory payloads only. 0 NLI forward passes.
- **REPORT_c5.md** is **not** edited. The erratum in §5 above should be applied to REPORT_c5 §4.2 (line 173) and §5
  (line 200) on your approval.
