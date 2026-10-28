"""
Reproduces the Task 25 example in the top-level README.md (development task; no reserved evaluation task is touched).

    .venv/bin/python -B gibs/validation/readme_task25_example.py

Successful run: 0f0f7358-e7dc-439c-87e5-5389c81f6d8d  (results/pilot/task_25_topup/results.json)
Failed run:     6f12b024-a820-419e-af4d-13d02bf480c7  (results/probe/new_batch1/results.json)

What it does (frozen code; no threshold or rule changes):
  1. prints the relevant tool calls / results of both runs and their verifier-v2 labels;
  2. reads the STORED C4 consensus masks (gibs/validation/results_c4/task25_C4.json) and prints numerator/denominator;
     for contrast, the stored paper-style baseline A (results_pilot/task25_A.json);
  3. checks that Task 25 has no exact-duplicate classes, so the pilot leave-one-out references equal the
     deduplicated reference set of the Phase 2 protocol;
  4. recomputes node/edge compatibility (DeBERTa NLI scores + structured-field reasons) for the key step pairs and
     re-runs C4 on one pair to confirm it reproduces the stored mapping. NLI scores come from the on-disk cache
     (~/.cache/stepwise_nli); uncached forward passes are counted (first use downloads the model).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.mcs.consensus import pair_indicators  # noqa: E402
from gibs.mcs.mcs import _Scorer  # noqa: E402
from gibs.mcs.nli import DebertaEntailment, Similarity  # noqa: E402
from gibs.mcs.structured_fields import StructuredFieldValidator  # noqa: E402
from gibs.validation.dedup import duplicate_classes  # noqa: E402
from gibs.validation.run_c4 import C4  # noqa: E402
from gibs.validation.run_pilot import load_runs  # noqa: E402
from gibs.validation.step_verification_v2 import classify_steps_v2  # noqa: E402

OK_ID, FAIL_ID = "0f0f7358-e7dc-439c-87e5-5389c81f6d8d", "6f12b024-a820-419e-af4d-13d02bf480c7"
OK_STEP, FAIL_STEP = "s16", "s30"            # the successful (gold-equal) and the incorrect book_reservation
PAIR_REF = "ab3d173b"                        # one successful reference used to show a positive match


def tool_steps(run):
    for n in run["steps"]["nodes"]:
        if n.get("kind") == "tool_call":
            yield n


def main():
    runs = {r["id"]: r for r in load_runs("25")[0]}
    ok, fail = runs[OK_ID], runs[FAIL_ID]
    print("Task 25 runs loaded:", len(runs), "| successful:", sum(r["success"] for r in runs.values()))
    dups = [c for c in duplicate_classes([{"id": r["id"], "_sim": _raw(r)} for r in runs.values()]).values() if len(c) > 1]
    print("exact-duplicate classes in Task 25:", len(dups), "(0 => leave-one-out refs == deduplicated refs)")

    for run in (ok, fail):
        lab = classify_steps_v2(run["steps"], run["task"])
        print(f"\n=== {run['id']}  success={run['success']}  ({run['file']})")
        for n in tool_steps(run):
            obs = n["observation"]
            out = obs["content_raw"] if obs["error"] else obs["content_raw"][:120]
            print(f"  {n['id']:>4} {n['tool_call']['name']}  label={lab[n['id']]['label']}"
                  + (f"  ({lab[n['id']]['reason'][:110]})" if lab[n['id']]['reason'] else ""))
            if n["tool_call"]["name"] == "book_reservation":
                a = n["tool_call"]["arguments"]
                print("        flights:", [(f["flight_number"], f["date"]) for f in a["flights"]],
                      "| payments:", a["payment_methods"])
                print("        result:", ("ERROR " if obs["error"] else "") + out.replace("\n", " ")[:160])

    # stored consensus (C4 primary; A for contrast)
    for variant, path in (("C4", "gibs/validation/results_c4/task25_C4.json"), ("A", "gibs/validation/results_pilot/task25_A.json")):
        d = json.loads((REPO / path).read_text())
        for qid, step in ((OK_ID, OK_STEP), (FAIL_ID, FAIL_STEP)):
            q = next(x for x in d["queries"] if x["query"] == qid)
            prs = q["per_reference"]
            nn, nc = sum(p["node"][step] for p in prs), sum(p["ctx"][step] for p in prs)
            print(f"\n[{variant}] {qid[:8]} {step}: m_node = {nn}/{len(prs)} = {nn/len(prs):.3f}; "
                  f"m_ctx = {nc}/{len(prs)} = {nc/len(prs):.3f}  (refs: successful runs excluding the query)")

    # node compatibility (cached NLI) and a recomputed C4 match
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate").with_overlength(C4["overlength"])
    sim = Similarity(model, direction="max_bidirectional")
    ref = next(r for i, r in runs.items() if i.startswith(PAIR_REF))
    for qrun, qstep, rrun, rstep in ((fail, FAIL_STEP, ok, OK_STEP), (ok, OK_STEP, ref, _gold_step(ref))):
        g1, g2 = project(qrun["steps"], C4["topology"]), project(rrun["steps"], C4["topology"])
        sc, val = _Scorer(g1, g2, sim, C4["mcs"]), StructuredFieldValidator(qrun["steps"], rrun["steps"])
        print(f"\n--- node compatibility: {qrun['id'][:8]} {qstep}  vs  {rrun['id'][:8]} {rstep}")
        print(f"    target-node NLI (tool results)      = {sc.node_sim('N:' + qstep, 'N:' + rstep):.3f}")
        for e1 in g1.in_edges("N:" + qstep):
            for e2 in g2.in_edges("N:" + rstep):
                if g1.nodes[e1["src"]]["kind"] != g2.nodes[e2["src"]]["kind"]:
                    continue
                s_edge, s_src = sim(e1["text"], e2["text"]), sc.node_sim(e1["src"], e2["src"])
                reasons = val(g1, g2, e1, e2)
                if s_src < 0.7:
                    continue                                        # print only source-compatible edge pairs
                print(f"    edge {e1['id']} ~ {e2['id']}: edge NLI {s_edge:.3f}, source NLI {s_src:.3f} -> "
                      + ("REJECTED: " + "; ".join(reasons)[:230] if reasons else "compatible"))
        res = C4["matcher"](g1, g2, sim, C4["mcs"], field_check=val)
        ind = pair_indicators(g1, res)[qstep]
        stored = json.loads((REPO / "gibs/validation/results_c4/task25_C4.json").read_text())
        sp = next(p for q in stored["queries"] if q["query"] == qrun["id"] for p in q["per_reference"]
                  if p["reference"] == rrun["id"])
        print(f"    recomputed C4: node {'N:' + qstep} -> {res.node_map.get('N:' + qstep)}; node={ind['node_level']} "
              f"ctx={ind['context_step_level']} | stored: node={sp['node'][qstep]} ctx={sp['ctx'][qstep]} "
              f"-> {'identical' if (sp['node'][qstep], sp['ctx'][qstep]) == (ind['node_level'], ind['context_step_level']) and sp['node_map'].get('N:' + qstep) == res.node_map.get('N:' + qstep) else 'DIFFERENT'}")
    print(f"\nuncached NLI forward passes in this run: {model.n_forward}")


def _raw(run):
    """Raw simulation for content hashing."""
    d = json.loads((REPO / run["file"]).read_text())
    return next(s for s in d["simulations"] if s["id"] == run["id"])


def _gold_step(run):
    lab = classify_steps_v2(run["steps"], run["task"])
    return next(n["id"] for n in tool_steps(run) if n["tool_call"]["name"] == "book_reservation"
                and lab[n["id"]]["label"] == "valid")


if __name__ == "__main__":
    main()
