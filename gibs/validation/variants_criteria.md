# Variant comparison C0–C3: evaluation criteria (written before running the variants)

Pairs and expectations: unchanged `pairs.json` (sha256 `c075979c6f45f90d00426fe52da910a9d7794ec1a070bae48a06dfb08426d738`).
No expectation is revised after seeing results.

| Variant | Truncation of pairs > 512 tokens | MCS |
|---|---|---|
| C0 | author code (`truncation=True` on the joined string) | single component (PDF Alg. 4 as implemented) |
| C1 | symmetric [OURS] | single component |
| C2 | author code | multi-component [OURS] |
| C3 | symmetric [OURS] | multi-component [OURS] |

All four use configuration C otherwise: event-context topology, DeBERTa max-bidirectional, τe = τv = 0.7, the
source-node threshold, the all-candidates pool, size = edges + nodes, and structured-field validation.

## Measures (per variant, compared with C0)

1. Demonstrably incorrect steps (from `pairs.json`) left unmatched, `m_node` and `m_ctx`.
2. First unmatched agent step (node-level) vs the pre-registered prediction and vs the first demonstrably
   incorrect step.
3. Valid agent steps left unmatched in V2, V8 and V9 (success vs success).
4. Steps whose pair indicator changes relative to C0, separately for `m_node` and `m_ctx`.
5. NLI decisions that change between author and symmetric truncation (pairs > 512 tokens only), and resulting
   mapping changes.
6. Runtime: NLI directional pairs required, uncached forward passes, wall time.

## False match: definition fixed in advance

A **newly matched** agent step (unmatched in C0, matched in the variant), or a step whose mapped counterpart
changes, is a **false match** if any of the following holds:

- **(F-a)** it is listed as demonstrably incorrect in `pairs.json`;
- **(F-b)** its mapped reference step performs a different action: a different tool, or a message with a
  different communicative act (e.g. a refusal vs a confirmation, a question vs an answer). This is judged manually
  from the texts, and each judgement is reported with the texts;
- **(F-c)** its mapped reference step is a tool step whose structured fields conflict (the C validator should make
  this impossible; it is checked anyway).

Every newly matched step is listed with both texts, whether or not it is judged a false match.
