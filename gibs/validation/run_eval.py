"""
Phase 2B frozen evaluation (gibs/validation/EVALUATION_PROTOCOL.md): Tasks 1, 28, 5.
C4 = primary tool-call matcher; C5 / C6 = exploratory message scoring. Labels: verifier v2. References: distinct
successful content classes, the query's own class excluded. OUR adaptations, not the paper's GIBS.

    .venv/bin/python -B gibs/validation/run_eval.py compute [task ...]   # resumable per query; lock-protected
    .venv/bin/python -B gibs/validation/run_eval.py analyze

Writes only to gibs/validation/results_eval/. Never touches pilot / variant results.
Security: from a results file's `info` block only agent llm name and temperature are read; step graphs are built with
info=None and nothing from `info` is written.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import itertools
import json
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from gibs.graph.event_projection import project  # noqa: E402
from gibs.graph.step_graph import build_step_graph  # noqa: E402
from gibs.mcs.consensus import pair_indicators  # noqa: E402
from gibs.mcs.nli import Similarity  # noqa: E402
from gibs.mcs.structured_fields import StructuredFieldValidator, _norm, compare_tool_events  # noqa: E402
from gibs.mcs.two_stage import extend_messages, freeze_tool_part, outcome_key, project_c5  # noqa: E402
from gibs.validation.dedup import content_hash, references_for, representatives  # noqa: E402
from gibs.validation.run_c4 import C4  # noqa: E402
from gibs.validation.step_verification_v2 import classify_steps_v2  # noqa: E402

OUT = REPO / "gibs/validation/results_eval"
EVAL_TASKS = {"1": 0.0, "28": 0.0, "5": 1.0}           # task -> agent temperature of the single regime used
K_VALUES = [1, 2, 3, 5, 8]
N_SUBSETS = 50
THRESH = 0.5
VARIANTS = ("C4", "C5", "C6")
TRANSFER_MESSAGE = "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."


# --------------------------------------------------------------------------------------------- loading
def load_task(task_id: str) -> list[dict]:
    want_t = EVAL_TASKS[task_id]
    runs, task_def, seen = [], None, set()
    for f in sorted(glob.glob(str(REPO / "results/**/results.json"), recursive=True)):
        d = json.load(open(f))
        temp = (((d.get("info") or {}).get("agent_info") or {}).get("llm_args") or {}).get("temperature")
        tdef = next((t for t in d.get("tasks", []) if str(t["id"]) == task_id), None)
        for s in d["simulations"]:
            rw = (s.get("reward_info") or {}).get("reward")
            if str(s["task_id"]) != task_id or rw is None or s["id"] in seen or temp != want_t:
                continue
            seen.add(s["id"])
            task_def = task_def or tdef
            runs.append({"id": s["id"], "_sim": s, "success": rw >= 0.5, "file": str(Path(f).relative_to(REPO)),
                         "task": tdef or task_def})
    for r in runs:
        r["steps"] = build_step_graph(r["_sim"], None, r["task"])
        r["labels"] = classify_steps_v2(r["steps"], r["task"])
    return runs


def label_key(node: dict, label: dict) -> tuple | None:
    """Key of a v2-valid step, used for reference ceilings (EVALUATION_PROTOCOL §4)."""
    if label["label"] != "valid":
        return None
    if node.get("kind") == "tool_call":
        args = {k: _norm(v) for k, v in (node["tool_call"]["arguments"] or {}).items()}
        return ("tool", node["tool_call"]["name"], json.dumps(args, sort_keys=True, default=str))
    return ("transfer_message",)


def exact_key(node: dict) -> tuple | None:
    """Exact-step oracle key of a tool-call step: tool name, raw arguments, normalized outcome."""
    if node.get("kind") != "tool_call":
        return None
    return (node["tool_call"]["name"], json.dumps(node["tool_call"]["arguments"] or {}, sort_keys=True),
            outcome_key(node))


def subset_seed(task: str, query: str, k: int, variant_free: str = "phase2b") -> int:
    return int(hashlib.sha256(f"{variant_free}|{task}|{query}|{k}".encode()).hexdigest()[:8], 16)


def subsets(n: int, k: int, seed: int) -> list[tuple]:
    """All combinations if C(n,k) <= N_SUBSETS, else N_SUBSETS distinct random combinations (deterministic seed)."""
    if comb(n, k) <= N_SUBSETS:
        return list(itertools.combinations(range(n), k))
    rng, seen = random.Random(seed), set()
    while len(seen) < N_SUBSETS:
        seen.add(tuple(sorted(rng.sample(range(n), k))))
    return sorted(seen)


# --------------------------------------------------------------------------------------------- compute
def match_pair(q, r, sim):
    """C4, then C5 / C6 from C4's tool part. Returns per-variant indicators and maps."""
    q4, r4 = project(q["steps"], C4["topology"]), project(r["steps"], C4["topology"])
    res4 = C4["matcher"](q4, r4, sim, C4["mcs"], field_check=StructuredFieldValidator(q["steps"], r["steps"]))
    fv, fe = freeze_tool_part(q4, res4.node_map, res4.edge_map)
    q5, r5 = project_c5(q["steps"]), project_c5(r["steps"])
    kw = dict(cfg=C4["mcs"], field_check=StructuredFieldValidator(q["steps"], r["steps"]))
    res5 = extend_messages(q5, r5, sim, fv, fe, **kw)
    res6 = extend_messages(q5, r5, sim, fv, fe, outcome_route=True, query_steps=q["steps"],
                           reference_steps=r["steps"], **kw)
    out = {"reference": r["id"]}
    for v, g, res in (("C4", q4, res4), ("C5", q5, res5), ("C6", q5, res6)):
        ind = pair_indicators(g, res)
        out[v] = {"node": {e: x["node_level"] for e, x in ind.items()},
                  "ctx": {e: x["context_step_level"] for e, x in ind.items()},
                  "node_map": res.node_map, "edge_map": res.edge_map}
    out["C6"]["outcome_route_edges"] = res6.outcome_route_edges
    return out


def compute(tasks=None):
    from gibs.mcs.nli import DebertaEntailment
    OUT.mkdir(parents=True, exist_ok=True)
    lock = OUT / ".lock"
    if lock.exists():
        pid = int(lock.read_text().strip() or 0)
        try:
            os.kill(pid, 0)
            sys.exit(f"another run_eval process ({pid}) holds {lock}; refusing to start a duplicate")
        except OSError:
            pass                                                     # stale lock
    lock.write_text(str(os.getpid()))
    try:
        model = DebertaEntailment(encoding="code_sep_string", overlength="truncate").with_overlength(C4["overlength"])
        sim = Similarity(model, direction="max_bidirectional")
        (OUT / "model.json").write_text(json.dumps(model.describe(), indent=2) + "\n")
        for t in (tasks or list(EVAL_TASKS)):
            part = OUT / "partial" / f"task{t}"
            part.mkdir(parents=True, exist_ok=True)
            runs = load_task(t)
            reps = representatives(runs)
            succ = [r for r in reps if r["success"]]
            t0, f0 = time.time(), model.n_forward
            for qi, q in enumerate(reps):
                path = part / f"{q['id']}.json"
                if path.exists():
                    continue
                refs = references_for(q, succ)
                per_ref = [match_pair(q, r, sim) for r in refs]
                self_match = match_pair(q, q, sim) if (q["success"] and q["multiplicity"] > 1) else None
                path.write_text(json.dumps({"query": q["id"], "success": q["success"],
                                            "multiplicity": q["multiplicity"], "duplicates": q["duplicates"],
                                            "per_reference": per_ref, "self_match": self_match}) + "\n")
                print(f"T{t}: query {qi + 1}/{len(reps)} ({q['id'][:8]}, refs={len(refs)}) "
                      f"elapsed={time.time() - t0:.0f}s forward={model.n_forward - f0}", flush=True)
            (OUT / f"task{t}_cost.json").write_text(json.dumps({"seconds_this_session": round(time.time() - t0, 1),
                                                                "nli_forward_passes_uncached": model.n_forward - f0}) + "\n")
            print(f"T{t}: done", flush=True)
    finally:
        lock.unlink(missing_ok=True)


# --------------------------------------------------------------------------------------------- analyze
def r3(x):
    return None if x is None else round(x, 3)


def bins(xs):
    edges = [("0", lambda x: x == 0), ("(0,.25)", lambda x: 0 < x < .25), ("[.25,.5)", lambda x: .25 <= x < .5),
             ("[.5,.75)", lambda x: .5 <= x < .75), ("[.75,1)", lambda x: .75 <= x < 1), ("1", lambda x: x == 1)]
    return [sum(f(x) for x in xs) for _, f in edges]


def dist(xs):
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": r3(statistics.mean(xs)), "median": r3(statistics.median(xs)), "bins": bins(xs)}


def analyze():
    from gibs.mcs.nli import DebertaEntailment
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate").with_overlength(C4["overlength"])
    sim = Similarity(model, direction="max_bidirectional")
    S = {"protocol": "gibs/validation/EVALUATION_PROTOCOL.md", "tasks": {}, "checks": Counter()}
    rows_all = []
    for t in EVAL_TASKS:
        runs = load_task(t)
        by_id = {r["id"]: r for r in runs}
        reps = representatives(runs)
        rep_of = {}
        for rep in reps:
            for rid in [rep["id"]] + rep["duplicates"]:
                rep_of[rid] = rep["id"]
        Q = {q["id"]: json.loads((OUT / "partial" / f"task{t}" / f"{q['id']}.json").read_text()) for q in reps}
        nodes = {r["id"]: {n["id"]: n for n in r["steps"]["nodes"]} for r in runs}
        keys = {r["id"]: {n["id"]: label_key(n, r["labels"][n["id"]]) for n in r["steps"]["nodes"] if n["type"] == "AgentStep"}
                for r in runs}
        refkeys = {rid: {k for k in ks.values() if k} for rid, ks in keys.items()}
        exacts = {r["id"]: defaultdict(set) for r in runs}
        for r in runs:
            for n in r["steps"]["nodes"]:
                ek = exact_key(n)
                if ek:
                    exacts[r["id"]][ek].add("N:" + n["id"])
        T = {"n_runs": len(runs), "n_success": sum(r["success"] for r in runs), "n_classes": len(reps),
             "n_success_classes": sum(r["success"] for r in reps),
             "duplicate_classes": [[r["id"][:8]] + [d[:8] for d in r["duplicates"]] for r in reps if r["duplicates"]]}
        # ---- S1, S2, S3 checks
        for qid, qd in Q.items():
            for pr in qd["per_reference"]:
                S["checks"]["pairs"] += 1
                S["checks"]["S3_own_class_in_refs"] += rep_of[pr["reference"]] == rep_of[qid]
                g4 = project(by_id[qid]["steps"], "paper_literal")
                tools = {n for n, d in g4.nodes.items() if d["kind"] == "tool_result"}
                for v in ("C5", "C6"):
                    S["checks"]["S1_tool_score_diff"] += sum(pr[v][key][n[2:]] != pr["C4"][key][n[2:]]
                                                             for key in ("node", "ctx") for n in tools)
                    S["checks"]["S1_tool_map_diff"] += {n: m for n, m in pr[v]["node_map"].items() if n in tools} != \
                        {n: m for n, m in pr["C4"]["node_map"].items() if n in tools}
                for n1, n2 in pr["C4"]["node_map"].items():
                    if not n1.startswith("N:s"):
                        continue
                    a, b = nodes[qid][n1[2:]], nodes[pr["reference"]].get(n2[2:]) if n2.startswith("N:") else None
                    if b is None or b["type"] != "AgentStep" or a.get("kind") != b.get("kind"):
                        S["checks"]["S2_cross_kind"] += 1
                    elif a.get("kind") == "tool_call" and not compare_tool_events(a, b).compatible:
                        S["checks"]["S2_tool_conflict"] += 1
        # ---- per-step rows (distinct-class view)
        rows = []
        for qid, qd in Q.items():
            prs = qd["per_reference"]
            n = len(prs)
            if not n:
                continue
            for ev, lab in by_id[qid]["labels"].items():
                node = nodes[qid][ev]
                k = keys[qid][ev]
                cap = sum(k in refkeys[p["reference"]] for p in prs) / n if k else None
                ek = exact_key(node)
                exact_avail = [bool(ek and exacts[p["reference"]].get(ek)) for p in prs]
                row = {"task": t, "run": qid[:8], "success": qd["success"], "multiplicity": qd["multiplicity"],
                       "step": ev, "kind": node.get("kind"),
                       "what": node["tool_call"]["name"] if node.get("kind") == "tool_call" else "message",
                       "label": lab["label"], "n_refs": n, "cap": r3(cap), "exact": r3(sum(exact_avail) / n) if ek else None,
                       "text": (node["op_text"] or "")[:90]}
                for v in VARIANTS:
                    row[f"m_node_{v}"] = r3(sum(p[v]["node"][ev] for p in prs) / n)
                    row[f"m_ctx_{v}"] = r3(sum(p[v]["ctx"][ev] for p in prs) / n)
                if ek:   # exact-step recall components (C4)
                    hit_node = sum(1 for p, av in zip(prs, exact_avail)
                                   if av and p["C4"]["node_map"].get("N:" + ev) in exacts[p["reference"]][ek])
                    hit_ctx = sum(1 for p, av in zip(prs, exact_avail)
                                  if av and p["C4"]["node_map"].get("N:" + ev) in exacts[p["reference"]][ek]
                                  and p["C4"]["ctx"][ev])
                    over = sum(1 for p, av in zip(prs, exact_avail) if not av and p["C4"]["node"][ev])
                    row.update({"exact_pairs": sum(exact_avail), "exact_hit_node": hit_node, "exact_hit_ctx": hit_ctx,
                                "nonexact_supported_pairs": over})
                rows.append(row)
        rows_all += rows
        # ---- §7.1 coverage of labelled valid steps
        cov = {}
        for v in VARIANTS:
            for kind in ("tool_call", "message"):
                if kind == "tool_call" and v != "C4":
                    continue
                vs = [r for r in rows if r["label"] == "valid" and r["kind"] == kind]
                for grp, sel in (("all", vs), ("success", [r for r in vs if r["success"]]),
                                 ("failed", [r for r in vs if not r["success"]])):
                    if not sel:
                        continue
                    ctx = [r[f"m_ctx_{v}"] for r in sel]
                    nod = [r[f"m_node_{v}"] for r in sel]
                    norm = [r[f"m_ctx_{v}"] / r["cap"] for r in sel if r["cap"]]
                    cov[f"{v}|{kind}|{grp}"] = {"n": len(sel), "coverage_ctx@0.5": r3(sum(x >= THRESH for x in ctx) / len(sel)),
                                                "coverage_node@0.5": r3(sum(x >= THRESH for x in nod) / len(sel)),
                                                "m_ctx": dist(ctx), "m_node": dist(nod),
                                                "ceiling_normalised_mean": r3(statistics.mean(norm)) if norm else None,
                                                "n_cap_zero": sum(1 for r in sel if not r["cap"]),
                                                "cap": dist([r["cap"] for r in sel])}
        T["coverage"] = cov
        # ---- §7.2 exact-step recall (tool calls; C4)
        er = Counter()
        for r in rows:
            if r.get("exact_pairs") is not None:
                er["pairs_with_exact"] += r["exact_pairs"]
                er["hit_node"] += r["exact_hit_node"]
                er["hit_ctx"] += r["exact_hit_ctx"]
                er["nonexact_supported_pairs"] += r["nonexact_supported_pairs"]
                er["tool_steps"] += 1
                er["tool_steps_with_exact"] += r["exact_pairs"] > 0
        T["exact_recall"] = {**er, "recall_node": r3(er["hit_node"] / er["pairs_with_exact"]) if er["pairs_with_exact"] else None,
                             "recall_ctx": r3(er["hit_ctx"] / er["pairs_with_exact"]) if er["pairs_with_exact"] else None}
        by_label = defaultdict(Counter)
        for r in rows:
            if r.get("exact_pairs") is not None:
                c = by_label[r["label"]]
                c["pairs"] += r["exact_pairs"]; c["node"] += r["exact_hit_node"]; c["ctx"] += r["exact_hit_ctx"]
        T["exact_recall_by_label"] = {k: {**c, "recall_node": r3(c["node"] / c["pairs"]) if c["pairs"] else None,
                                          "recall_ctx": r3(c["ctx"] / c["pairs"]) if c["pairs"] else None}
                                      for k, c in by_label.items()}
        # ---- §7.3 every labelled valid tool step < 0.5 (C4): per-reference mechanism
        low = []
        for r in rows:
            if r["label"] != "valid" or r["kind"] != "tool_call" or r["m_ctx_C4"] >= THRESH:
                continue
            qid = next(q for q in Q if q.startswith(r["run"]))
            k = keys[qid][r["step"]]
            mech = Counter()
            g1 = project(by_id[qid]["steps"], "paper_literal")
            for p in Q[qid]["per_reference"]:
                rid = p["reference"]
                if p["C4"]["ctx"][r["step"]]:
                    mech["supported"] += 1
                elif k not in refkeys[rid]:
                    mech["(a) reference lacks the step"] += 1
                elif p["C4"]["node"][r["step"]]:
                    mech["(b) node mapped, an incoming edge not"] += 1
                else:
                    g2 = project(by_id[rid]["steps"], "paper_literal")
                    targets = [nid for nid, kk in keys[rid].items() if kk == k]
                    val = StructuredFieldValidator(by_id[qid]["steps"], by_id[rid]["steps"])
                    cand = False
                    for e1 in g1.in_edges("N:" + r["step"]):
                        for tn in targets:
                            for e2 in g2.in_edges("N:" + tn):
                                ok = (sim(e1["text"], e2["text"]) >= 0.7 and sim(g1.nodes[e1["dst"]]["text"], g2.nodes[e2["dst"]]["text"]) >= 0.7
                                      and (g1.nodes[e1["src"]]["kind"] == g2.nodes[e2["src"]]["kind"]) and
                                      (e1["src"] == "ROOT" == e2["src"] or (e1["src"] != "ROOT" and e2["src"] != "ROOT" and
                                       sim(g1.nodes[e1["src"]]["text"], g2.nodes[e2["src"]]["text"]) >= 0.7))
                                      and not val(g1, g2, e1, e2))
                                cand = cand or ok
                    mech["(d) candidate exists, not selected" if cand else "(c) no candidate (NLI / source / field)"] += 1
            low.append({**{k2: r[k2] for k2 in ("run", "step", "what", "success", "m_node_C4", "m_ctx_C4", "cap", "text")},
                        "mechanisms": dict(mech)})
        T["low_valid_tool_steps"] = low
        # ---- §7.4 reference-count sensitivity
        sens = {}
        for v in VARIANTS:
            for scope in ("valid", "all"):
                for k in K_VALUES + ["all"]:
                    devs, vals, unexp, nsub = [], [], 0, 0
                    for qid, qd in Q.items():
                        prs = qd["per_reference"]
                        n = len(prs)
                        kk = n if k == "all" else k
                        if not n or kk > n:
                            continue
                        subs = [tuple(range(n))] if k == "all" else subsets(n, kk, subset_seed(t, qid, kk))
                        nsub += len(subs)
                        for ev, lab in by_id[qid]["labels"].items():
                            node = nodes[qid][ev]
                            relevant = (node.get("kind") == "tool_call") == (v == "C4")
                            if not relevant or (scope == "valid" and lab["label"] != "valid"):
                                continue
                            full = sum(p[v]["ctx"][ev] for p in prs) / n
                            for sub in subs:
                                m = sum(prs[i][v]["ctx"][ev] for i in sub) / len(sub)
                                devs.append(abs(m - full))
                                if lab["label"] == "valid":
                                    vals.append(m)
                                    unexp += m < THRESH
                    if devs:
                        sd = sorted(devs)
                        sens[f"{v}|{scope}|{k}"] = {"n_obs": len(devs), "n_subsets": nsub,
                                                    "mean_abs_dev": r3(statistics.mean(devs)),
                                                    "median_abs_dev": r3(statistics.median(devs)),
                                                    "p90_abs_dev": r3(sd[int(0.9 * (len(sd) - 1))]),
                                                    "mean_valid": r3(statistics.mean(vals)) if vals else None,
                                                    "unexpected_rate": r3(unexp / len(vals)) if vals else None}
        T["sensitivity"] = sens
        # ---- deduplication effect (per-run, pilot-style LOO with duplicates retained), C4 tool + C5/C6 messages
        dup = {}
        succ_runs = [r for r in runs if r["success"]]
        for v in VARIANTS:
            kind = "tool_call" if v == "C4" else "message"
            ded, ret = [], []
            for r in runs:
                qrep = rep_of[r["id"]]
                qd = Q[qrep]
                by_ref = {p["reference"]: p for p in qd["per_reference"]}
                for ev, lab in r["labels"].items():
                    if lab["label"] != "valid" or nodes[r["id"]][ev].get("kind") != kind:
                        continue
                    if qd["per_reference"]:
                        ded.append(sum(p[v]["ctx"][ev] for p in qd["per_reference"]) / len(qd["per_reference"]))
                    vals = []
                    for y in succ_runs:
                        if y["id"] == r["id"]:
                            continue
                        yrep = rep_of[y["id"]]
                        p = qd["self_match"] if yrep == qrep else by_ref.get(yrep)
                        if p is None:
                            continue
                        vals.append(p[v]["ctx"][ev])
                    if vals:
                        ret.append(sum(vals) / len(vals))
            dup[v] = {"dedup_per_class": dist(ded), "duplicates_retained_per_run": dist(ret),
                      "coverage_dedup": r3(sum(x >= THRESH for x in ded) / len(ded)) if ded else None,
                      "coverage_retained": r3(sum(x >= THRESH for x in ret) / len(ret)) if ret else None}
        T["dedup_effect"] = dup
        # ---- messages: C5 vs C6, outcome-route matches (all listed)
        om = []
        for qid, qd in Q.items():
            for p in qd["per_reference"]:
                for e in p["C6"]["outcome_route_edges"]:
                    s1, d1 = e.split("->")
                    e2 = p["C6"]["edge_map"][e]
                    qm, rm = nodes[qid][d1[2:]], nodes[p["reference"]][e2.split("->")[1][2:]]
                    om.append({"query": qid[:8], "q_success": qd["success"], "q_msg": d1[2:], "q_label": by_id[qid]["labels"][d1[2:]]["label"],
                               "reference": p["reference"][:8], "r_msg": rm["id"], "tool": nodes[qid][s1[2:]]["tool_call"]["name"],
                               "identical_text": (qm.get("content") or "").strip() == (rm.get("content") or "").strip(),
                               "q_text": qm.get("content"), "r_text": rm.get("content")})
        T["outcome_route_matches"] = om
        msg = {}
        for v in ("C4", "C5", "C6"):
            c = Counter()
            for qid, qd in Q.items():
                for p in qd["per_reference"]:
                    for ev in p[v]["node"]:
                        if nodes[qid][ev].get("kind") != "message":
                            continue
                        c["indicators"] += 1; c["node"] += p[v]["node"][ev]; c["ctx"] += p[v]["ctx"][ev]
            msg[v] = dict(c)
        T["message_coverage_indicators"] = msg
        # ---- agent-setup descriptors
        tool_seqs = {tuple(n["tool_call"]["name"] for n in r["steps"]["nodes"] if n.get("kind") == "tool_call") for r in reps}
        T["setup_descriptors"] = {
            "distinct_tool_sequences": len(tool_seqs),
            "successful_classes_without_tool_calls": sum(1 for r in reps if r["success"] and not any(
                n.get("kind") == "tool_call" for n in r["steps"]["nodes"])),
            "mean_agent_steps": r3(statistics.mean(sum(n["type"] == "AgentStep" for n in r["steps"]["nodes"]) for r in reps)),
            "tool_steps_with_any_exact_counterpart": r3(er["tool_steps_with_exact"] / er["tool_steps"]) if er["tool_steps"] else None,
            "mean_m_ctx_all_tool_steps_C4": r3(statistics.mean([r["m_ctx_C4"] for r in rows if r["kind"] == "tool_call"]))
            if any(r["kind"] == "tool_call" for r in rows) else None,
            "mean_m_ctx_all_messages_C5": r3(statistics.mean([r["m_ctx_C5"] for r in rows if r["kind"] == "message"])),
            "mean_m_ctx_all_messages_C6": r3(statistics.mean([r["m_ctx_C6"] for r in rows if r["kind"] == "message"])),
        }
        T["label_counts"] = {f"{a}|{b}|{c}": n for (a, b, c), n in
                             Counter((r["label"], r["kind"], "success" if r["success"] else "failed") for r in rows).items()}
        cost = OUT / f"task{t}_cost.json"
        T["cost"] = json.loads(cost.read_text()) if cost.exists() else None
        S["tasks"][t] = T
    S["checks"] = dict(S["checks"])
    S["analysis_nli_forward_passes_uncached"] = model.n_forward
    (OUT / "eval_summary.json").write_text(json.dumps(S, indent=1, ensure_ascii=False, default=str) + "\n")
    with open(OUT / "per_step_eval.csv", "w", newline="") as f:
        fields = sorted({k for r in rows_all for k in r}, key=lambda k: list(rows_all[0]).index(k) if k in rows_all[0] else 99)
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows_all)
    print(json.dumps(S["checks"], indent=1))
    print(f"wrote {OUT}/eval_summary.json, per_step_eval.csv; analysis uncached NLI passes: {model.n_forward}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "compute":
        compute(sys.argv[2:] or None)
    elif cmd == "analyze":
        analyze()
