# Consensus-mask pilot: plan (written before any pilot computation)

Scope: three tasks, leave-one-out consensus masks. **No full-corpus scoring and no GCN training.** Thresholds and
scoring rules are those already fixed (τe = τv = 0.7, K = 10, size = edges + nodes); nothing is tuned on pilot
results.

## Tasks (Groq regime, agent T=0; runs deduplicated by simulation UUID; infrastructure errors excluded)

| Task | Successful | Failed | Distinct successful tool sequences | Why |
|---|---|---|---|---|
| 48 | 10 | 13 | 2 | requested; many failures |
| 9 | 17 | 4 | 10 | diverse valid paths; prohibited cancellations |
| 25 | 19 | 3 | 11 | diverse valid paths; argument-level booking errors checkable against the gold action |

Excluded on cost: Task 38 (84k unique edge-text pairs) and Task 4 (66k), versus about 37k for the three above.

## Variants (same trajectory/reference sets for all)

| Variant | Definition | Status |
|---|---|---|
| A | paper-literal projection, no structured fields, no event-kind restriction, single-component MCS, author-code truncation | paper-style baseline |
| C0 | event-context projection + structured fields, single-component MCS, author-code truncation | our adaptation |
| C3 | C0 + symmetric truncation + multi-component MCS | **our adaptation, not the paper's algorithm** |

## Masks

For each task, with S = successful runs:
* successful query i: references S \ {i} (leave-one-out; a run is never its own reference);
* failed query: references S.

Per agent step j: `m_node` = fraction of references in whose MCS the step's result node is mapped (PDF C.2).
`m_ctx` = fraction in which all of the step's incoming edges are mapped (ours). Per-reference indicators are stored,
so masks for any reference subset can be computed without re-running MCS.

## Independent step verification (does NOT use the run's reward)

Rules derived only from each task's gold actions, NL assertions, and the airline policy text:

| Label | Rule |
|---|---|
| `incorrect` | **T48, T9** (gold actions contain no write; NL: "Agent does not cancel 3RK2T9" / "does not cancel IFOYYZ / NQNU5R", "M20IZO is not modified"): any **successful** write call (`book_reservation`, `cancel_reservation`, `send_certificate`, `update_reservation_*`; non-error observation). **T25**: a successful `book_reservation` whose DB-critical arguments (structured-field rules of configuration C) differ from the gold booking; any successful booking after a first gold-matching one (duplicate); any successful write other than `book_reservation` (the gold contains none). |
| `attempted_incorrect` | T48, T9: a write call that returned a tool error (prohibited attempt, no state change). |
| `valid` | A read call whose name and arguments equal a gold action (T48 `get_reservation_details(3RK2T9)`; T9 `search_direct_flight(JFK→MCO, 2024-05-22)`). T25: the first successful `book_reservation` whose DB-critical arguments equal the gold booking. All tasks: the policy-mandated message "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON." immediately after a successful `transfer_to_human_agents` call. |
| `unverified` | everything else. No correctness claim is made for these steps. |

"Unexpected" (fixed in advance):
* a `valid` step with consensus **< 0.5** is *unexpectedly low*;
* an `incorrect` step with consensus **≥ 0.5** is *unexpectedly high*.

Both are reported separately for `m_node` and `m_ctx` and for A, C0 and C3.

## Reference-count analysis

For each query and each k ∈ {1, 2, 3, 5, 8, all}: 50 random reference subsets of size k (seed 0; drawn from that
query's reference pool). Reported per k:
* mean absolute deviation of each step's mask from its full-pool value;
* mean mask of `valid` and `incorrect` steps;
* the number of unexpected cases.
