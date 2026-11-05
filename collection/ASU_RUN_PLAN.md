# ASU collection plan — October 29, 2026

The ASU key was supplied locally by the user and authenticated successfully.
Only ASU Research Computing's no-charge endpoint is used. The key remains in
the ignored `.env.asu`, with file permissions 600; it is not embedded in code,
commands, reports or cluster uploads.

## Engineering checks and model choice

Three Task 13 smoke attempts are separate from research data:

| Model | Recorded observation |
| --- | --- |
| qwen3-30b-a3b | Graded success, but no expected transfer tool call; customer also claimed to have updated the booking. |
| qwen3-235b-a22b | Graded success and made the transfer call; customer changed the instructed maximum payment from $100 to $150. |
| qwen38-27b | Graded success and made the transfer call; customer stayed in role in the inspected transcript. The agent still inferred a one-way request without confirmation. |

Select `qwen38-27b` for collection based on these serving/simulator checks.
This is a limited engineering check, not evidence of general model superiority
or human-verified trajectory correctness. Selection used no NIBS/GIBS/C4 scores.
Retain all smoke attempts. The hosted weight revision is not exposed.

During the first hosted pilot, responses exposed a client issue: LiteLLM 1.81.11
silently dropped `reasoning_effort` for the custom ASU model ID. Its metadata
recorded a **request**, not proof that the server received it. The direct API
probe honored `none`, but benchmark responses contained reasoning. The first
pilot was stopped and preserved; it is excluded from the corrected collection.
The fix explicitly allows passthrough of `reasoning_effort`; offline inspection
of LiteLLM confirmed it changes the forwarded field from absent to `none`.
Corrected outputs have the suffix `-none`, and their manifest includes
`reasoning_passthrough: true`. Inspect the corrected benchmark responses again
before scaling. This fixes serving behavior without changing benchmark prompts.

The corrected Task 13 attempt was graded a success but contained no tool call,
so it failed the engineering tool-use gate. Preserve it as a failed smoke check.
The follow-up corrected **Task 25 booking smoke passed**: 11 graph agent steps,
one database booking action, the expected split payment, and no reasoning output
in any of its 16 model responses. Use that to establish end-to-end tool/database
compatibility; it does not validate all tasks or all customer behaviors.

The next pilot exposed multi-call assistant turns on tasks 0 and 9, which the
current step graph cannot represent. Preserve those attempts and their audit;
do not collapse calls or silently discard them. ASU requests now explicitly set
`parallel_tool_calls: false`, with passthrough enabled, consistent with Airline's
one-call-per-turn policy. Final collection paths have suffix **`-serial-none`**
and the manifest records the requested serial-call constraint. Check observed
responses as well; a requested constraint alone is not a compatibility guarantee.

## Frozen generation settings

- Pinned Airline benchmark: `5bfa7e37b36656b37dc6d022156be6563c1007f3`.
- Agent and customer: `openai/qwen38-27b`, through ASU's explicit endpoint.
- Agent temperature 1; customer temperature 0; reasoning effort requested `none`.
- Gateway add-ons off; fixed model name (no automatic routing).
- Parallel tool calls explicitly disabled, consistent with the benchmark policy.
- Output limit 2,048 tokens/call, 200 steps, 10 tool errors, seed 300.
- Four concurrent simulations, 1,200-second native simulation timeout.
- Stop/checkpoint at ten infrastructure failures; preserve pre-resume snapshots.
- Token pricing in LiteLLM is explicitly zero for bookkeeping; ASU's policy is
  the basis for no-charge status. Token usage is still recorded.

## Pilot and main collection

The original Sol plan proposed a 150-attempt pilot. For this hosted route, first
use **10 tasks × 1 attempt** as a smaller engineering gate: tasks
0, 3, 9, 13, 20, 25, 34, 40, 45, 48. These cover cancellation restrictions,
membership, flight changes, bookings/payment constraints, escalation and user
pressure. Historical development tasks are included to check parser compatibility.

Inspect serving errors, graph compatibility and representative conversations.
Do not select confidence methods or tune their hyperparameters on this pilot.
If collection is healthy, launch a separate **50 tasks × 20 attempts = 1,000**
main target using the same generation settings. More attempts do not by
themselves establish step-level correctness or better confidence scores.

Smoke, pilot and main have separate paths. Native trial seeds repeat across
these invocations, so treat pilot exposure as disclosed engineering exposure,
not as an independent untouched test set. Deduplicate main data before analysis.

## Interpretation and next experiment

Keep the official benchmark reward unchanged. Audit expected tool-name coverage
separately: it does not verify arguments, policy compliance, alternatives or the
customer simulator. Task 13 demonstrates that a DB/COMMUNICATE reward can pass
without an expected escalation action. Review reference quality before treating
rewarded trajectories as successful reasoning references.

The current learned comparison uses historical Groq trajectories and stored
teachers. New ASU trajectories need their own split, reference audit, fresh MCS
targets, retraining and independent labels before a new GIBS/C4 result is claimed.
See [EVALUATION_PLAN.md](EVALUATION_PLAN.md). This applies the paper's methods to
Airline; it is not a reproduction of its math/QA benchmark.
