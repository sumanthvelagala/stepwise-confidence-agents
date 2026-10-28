"""
Controlled comparison of experimental variants of configuration C on the pre-registered pairs (pairs.json):

  C0  C unchanged (author-code truncation, single-component MCS)
  C1  symmetric truncation only            [OURS]
  C2  multi-component MCS only             [OURS]
  C3  both                                 [OURS]

Criteria were fixed beforehand in variants_criteria.md. Usage:
    .venv/bin/python gibs/validation/run_variants.py
Writes gibs/validation/results_variants/{variants.json, tables.md}.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.step_graph import build_step_graph, load_simulation  # noqa: E402
from gibs.mcs.mcs import find_mcs  # noqa: E402
from gibs.mcs.multi_component import find_mcs_multi  # noqa: E402
from gibs.mcs.nli import DebertaEntailment  # noqa: E402
from gibs.validation.run_validation import CONFIGS, PAIRS, TAU, analyse  # noqa: E402

OUT = REPO / "gibs/validation/results_variants"
VARIANTS = {   # name: (truncation mode, matcher)
    "C0": ("truncate", find_mcs),
    "C1": ("symmetric", find_mcs),
    "C2": ("truncate", find_mcs_multi),
    "C3": ("symmetric", find_mcs_multi),
}

# real-data truncation checks (texts taken from step graphs): (label, file, sim, node, field, file, sim, node, field)
TRUNCATION_CASES = [
    ("identical long user records (V9, 698 tokens each)", "results/pilot/task_38_topup1/results.json", "c59e7ab6", "s6",
     "result", "results/pilot/task_38_topup1/results.json", "2a47da10", "s6", "result"),
    ("identical lookup observations (T48 probe P06)", "results/pilot/tasks_25_40_48/results.json", "7f5cbcd7", "s4",
     "result", "results/pilot/tasks_25_40_48/results.json", "c890f90b", "s4", "result"),
    ("cancel vs lookup observation: status cancelled vs null (P07)", "results/pilot/tasks_25_40_48/results.json",
     "7f5cbcd7", "s6", "result", "results/pilot/tasks_25_40_48/results.json", "c890f90b", "s4", "result"),
    ("update observations: different DOB (P08)", "results/probe/new_batch2/results.json", "b4901df6", "s10", "result",
     "results/probe/new_batch2/results.json", "f6000fbe", "s8", "result"),
    ("user records before vs after certificate: payment_methods differ (V7)", "results/probe/task_4/results.json",
     "259d9890", "s24", "result", "results/probe/task_4/results.json", "ce8b1b6b", "s2", "result"),
    ("short unchanged pair: identical greeting", "results/pilot/tasks_25_40_48/results.json", "7f5cbcd7", "s0", "op",
     "results/pilot/tasks_25_40_48/results.json", "c890f90b", "s0", "op"),
    ("short unchanged pair: cancel vs lookup call (P05)", "results/pilot/tasks_25_40_48/results.json", "7f5cbcd7",
     "s6", "op", "results/pilot/tasks_25_40_48/results.json", "c890f90b", "s4", "op"),
]


def text_of(file, sim, node, field, _cache={}):
    if (file, sim) not in _cache:
        _cache[(file, sim)] = build_step_graph(*load_simulation(str(REPO / file), sim))
    n = next(x for x in _cache[(file, sim)]["nodes"] if x["id"] == node)
    return n["op_text"] if field == "op" else n["result_text"]


def maxsim(model, a, b):
    f, r = model.entail_batch([(a, b), (b, a)])
    return max(f, r)


def main():
    spec = json.loads(PAIRS.read_text())
    digest = hashlib.sha256(PAIRS.read_bytes()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    author = DebertaEntailment(encoding="code_sep_string", overlength="truncate")
    symmetric = author.with_overlength("symmetric")
    models = {"truncate": author, "symmetric": symmetric}

    # 1. truncation checks on real texts
    trunc_cases = []
    for label, f1, s1, n1, fl1, f2, s2, n2, fl2 in TRUNCATION_CASES:
        a, b = text_of(f1, s1, n1, fl1), text_of(f2, s2, n2, fl2)
        n_tok = author.token_length(a, b)
        sa, ss = maxsim(author, a, b), maxsim(symmetric, a, b)
        trunc_cases.append({"case": label, "joined_tokens": n_tok, "overlength": n_tok > author.max_length,
                            "identical_texts": a == b, "author_truncation": round(sa, 4),
                            "symmetric_truncation": round(ss, 4), "decision_author": sa >= TAU,
                            "decision_symmetric": ss >= TAU, "unchanged_score": abs(sa - ss) < 1e-9})
        print("truncation check:", trunc_cases[-1], flush=True)

    # 2. variants on the pre-registered pairs
    runs, nli_flips = [], []
    for p in spec["pairs"]:
        q_steps = build_step_graph(*load_simulation(str(REPO / p["query"]["file"]), p["query"]["sim"]))
        r_steps = build_step_graph(*load_simulation(str(REPO / p["reference"]["file"]), p["reference"]["sim"]))
        r_by_id = {n["id"]: n for n in r_steps["nodes"]}
        incorrect = [d["step"] for d in p.get("demonstrably_incorrect", [])]
        per_variant = {}
        for name, (mode, matcher) in VARIANTS.items():
            cfg = {**CONFIGS["C"], "matcher": matcher, "label": f"{name}: C + truncation={mode}, "
                   f"mcs={'multi' if matcher is find_mcs_multi else 'single'}"}
            other = models["symmetric" if mode == "truncate" else "truncate"]
            f0, n0, t0 = author.n_forward + symmetric.n_forward, author.n_requested + symmetric.n_requested, time.time()
            out = analyse(models[mode], other, q_steps, r_steps, name, cfg=cfg, return_nli_pairs=True)
            out["cost"] = {"seconds": round(time.time() - t0, 2),
                           "nli_directional_pairs_required": out["cost"]["nli_directional_pairs_required"],
                           "nli_forward_passes_uncached_incl_flip_check":
                               author.n_forward + symmetric.n_forward - f0}
            pairs_used = out.pop("_nli_pairs")
            if name == "C0":   # NLI decisions that differ between the two truncation modes (overlength pairs only)
                over = [(a, b) for a, b in pairs_used if author.token_length(a, b) > author.max_length
                        or author.token_length(b, a) > author.max_length]
                changed = []
                for a, b in over:
                    sa, ss = maxsim(author, a, b), maxsim(symmetric, a, b)
                    if (sa >= TAU) != (ss >= TAU):
                        changed.append({"a": a[:120], "b": b[:120], "author": round(sa, 4), "symmetric": round(ss, 4)})
                nli_flips.append({"pair": p["id"], "nli_comparisons": len(pairs_used), "overlength": len(over),
                                  "decisions_changed": len(changed), "examples": changed[:5]})
            ec = {"expected_first_unmatched": p["expected_first_unmatched"].get("C"),
                  "first_unmatched": out["first_unmatched_node_level"],
                  "demonstrably_incorrect_steps": incorrect,
                  "first_unmatched_is_first_incorrect": bool(incorrect) and out["first_unmatched_node_level"] == incorrect[0],
                  "incorrect_unmatched_node": {s: s in out["unmatched_node_level"] for s in incorrect},
                  "incorrect_unmatched_ctx": {s: s in out["unmatched_context_step_level"] for s in incorrect}}
            out.update({"pair": p["id"], "task": p["task"], "variant": name, "category": p["category"],
                        "expectation_check": ec, "n_agent_steps": len(out["steps"])})
            per_variant[name] = out
        # changes relative to C0
        base = {s["event"]: s for s in per_variant["C0"]["steps"]}
        for name, out in per_variant.items():
            changes = []
            for s in out["steps"]:
                b = base[s["event"]]
                if (s["node_level"], s["context_step_level"], s["mapped_to"]) != \
                        (b["node_level"], b["context_step_level"], b["mapped_to"]):
                    ref_event = (s["mapped_to"] or "")[2:] or None
                    changes.append({
                        "event": s["event"], "C0_node": b["node_level"], "node": s["node_level"],
                        "C0_ctx": b["context_step_level"], "ctx": s["context_step_level"],
                        "C0_mapped_to": b["mapped_to"], "mapped_to": s["mapped_to"],
                        "query_text": s["operation"],
                        "reference_text": (r_by_id[ref_event]["op_text"][:110] if ref_event in r_by_id else None),
                        "is_demonstrably_incorrect": s["event"] in incorrect,
                    })
            out["changes_vs_C0"] = changes
            runs.append(out)
            print(f"{p['id']} {name}: unmatched(node)={len(out['unmatched_node_level'])}/{out['n_agent_steps']} "
                  f"unmatched(ctx)={len(out['unmatched_context_step_level'])} first={out['first_unmatched_node_level']} "
                  f"changes={[(c['event'], int(c['node']), int(c['ctx'])) for c in changes]} "
                  f"components={len(out.get('components', [])) or 1} cost={out['cost']}", flush=True)

    report = {"pairs_file_sha256": digest, "model": author.describe(), "tau": TAU,
              "truncation_checks": trunc_cases, "nli_decision_changes_author_vs_symmetric": nli_flips, "runs": runs}
    (OUT / "variants.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (OUT / "tables.md").write_text(tables(report, spec))
    print(f"wrote {OUT}")


def tables(report, spec) -> str:
    by = {(r["pair"], r["variant"]): r for r in report["runs"]}
    L = ["# Variant comparison C0–C3 (generated by run_variants.py)", "",
         f"pairs.json sha256 `{report['pairs_file_sha256']}`", "", "## Truncation checks on real texts", "",
         "| Case | Joined tokens | Identical | Author truncation | Symmetric | Decision changes |", "|---|---|---|---|---|---|"]
    for t in report["truncation_checks"]:
        L.append(f"| {t['case']} | {t['joined_tokens']} | {t['identical_texts']} | {t['author_truncation']:.3f} | "
                 f"{t['symmetric_truncation']:.3f} | {t['decision_author'] != t['decision_symmetric']} |")
    L += ["", "## NLI decisions changed by symmetric truncation (comparisons used by C0)", "",
          "| Pair | NLI comparisons | Overlength | Decisions changed |", "|---|---|---|---|"]
    for f in report["nli_decision_changes_author_vs_symmetric"]:
        L.append(f"| {f['pair']} | {f['nli_comparisons']} | {f['overlength']} | {f['decisions_changed']} |")
    L += ["", "## Per pair and variant", "",
          "| Pair | Variant | Unmatched (node) | Unmatched (ctx) | First unmatched | Pre-registered | Incorrect unmatched (node/ctx) | Steps changed vs C0 | Components | NLI pairs / uncached | Seconds |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in spec["pairs"]:
        for v in VARIANTS:
            r = by[(p["id"], v)]
            ec = r["expectation_check"]
            inc = ", ".join(f"{s}: {int(ec['incorrect_unmatched_node'][s])}/{int(ec['incorrect_unmatched_ctx'][s])}"
                            for s in ec["demonstrably_incorrect_steps"]) or "n/a"
            exp = ec["expected_first_unmatched"]
            exp_s = "no prediction" if exp is None else f"{exp} {'✓' if exp == ec['first_unmatched'] else '✗'}"
            ch = ", ".join(f"{c['event']}({int(c['C0_node'])}{int(c['C0_ctx'])}→{int(c['node'])}{int(c['ctx'])})"
                           for c in r["changes_vs_C0"]) or "—"
            L.append(f"| {p['id']} | {v} | {len(r['unmatched_node_level'])}/{r['n_agent_steps']} | "
                     f"{len(r['unmatched_context_step_level'])}/{r['n_agent_steps']} | {ec['first_unmatched'] or '—'} | "
                     f"{exp_s} | {inc} | {ch} | {len(r.get('components', [])) or 1} | "
                     f"{r['cost']['nli_directional_pairs_required']} / {r['cost']['nli_forward_passes_uncached_incl_flip_check']} | "
                     f"{r['cost']['seconds']} |")
    L += ["", "## Newly matched or re-mapped steps (for the false-match review)", "",
          "| Pair | Variant | Step | C0 node/ctx → variant | Mapped to | Query text | Reference text | Demonstrably incorrect |",
          "|---|---|---|---|---|---|---|---|"]
    for r in report["runs"]:
        for c in r["changes_vs_C0"]:
            L.append(f"| {r['pair']} | {r['variant']} | {c['event']} | {int(c['C0_node'])}/{int(c['C0_ctx'])} → "
                     f"{int(c['node'])}/{int(c['ctx'])} | {c['mapped_to']} | {(c['query_text'] or '').replace('|', '/')} | "
                     f"{(c['reference_text'] or '—').replace('|', '/')} | {c['is_demonstrably_incorrect']} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
