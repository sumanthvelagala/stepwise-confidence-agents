"""Retrospective NIBS evaluation; see nibs/EVALUATION_PROTOCOL.md.

    python3 -B nibs/run_evaluation.py
    python3 -B nibs/run_evaluation.py --human-labels path/to/completed_labels.csv

Standard library only. No API calls, model downloads, GIBS matching or training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from nibs.parsing.parser import normalize_args, parse_simulation
from nibs.scoring.nibs import score_run
from nibs.similarity.similarity import tool_sim
from nibs.evaluation_metrics import (agreement, binary_metrics, localization_summary, mean,
                                     random_binary_metrics, random_target_rank, target_rank)
from gibs.graph.step_graph import build_step_graph
from gibs.validation.dedup import content_hash, references_for, representatives
from gibs.validation.step_verification_v2 import VERSION, classify_steps_v2

DEFAULT_TASKS = ("3", "9", "25", "40", "48")
MODEL = "groq/openai/gpt-oss-20b"
HUMAN_LABELS = {"correct", "incorrect", "ambiguous", "tool_or_env_error"}
REVIEW_COLUMNS = ["task_id", "run_id", "step_index", "event_id", "kind", "tool",
                  "context_file", "reviewer_1", "reviewer_2", "adjudicated_label", "notes"]
SOURCE_FILES = ["nibs/run_evaluation.py", "nibs/evaluation_metrics.py", "nibs/EVALUATION_PROTOCOL.md",
                "nibs/parsing/parser.py", "nibs/scoring/nibs.py", "nibs/similarity/similarity.py",
                "gibs/graph/step_graph.py", "gibs/validation/step_verification.py",
                "gibs/validation/step_verification_v2.py", "gibs/mcs/structured_fields.py",
                "gibs/validation/dedup.py", "gibs/validation/dataset_audit.py"]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_runs(root, tasks, *, model=MODEL, agent_temperature=0.0, user_temperature=0.0):
    """Whitelist metadata. Never copy raw provider settings into derived artifacts."""
    selected, seen, excluded, inputs, identities = [], {}, Counter(), {}, {}
    for path in sorted(root.rglob("results.json")):
        data = json.loads(path.read_text())
        relevant = [s for s in data.get("simulations", []) if str(s["task_id"]) in tasks]
        if not relevant:
            continue
        info = data.get("info") or {}
        agent, user = info.get("agent_info") or {}, info.get("user_info") or {}
        if (agent.get("llm") != model or (agent.get("llm_args") or {}).get("temperature") != agent_temperature
                or user.get("llm") != model or (user.get("llm_args") or {}).get("temperature") != user_temperature):
            excluded["different_model_or_temperature"] += len(relevant)
            continue
        definitions = {str(t["id"]): t for t in data.get("tasks", [])}
        source = str(path.relative_to(root))
        inputs[source] = file_hash(path)
        policy = (info.get("environment_info") or {}).get("policy")
        for sim in relevant:
            tid, sid = str(sim["task_id"]), sim["id"]
            reward = (sim.get("reward_info") or {}).get("reward")
            fingerprint = (content_hash(sim), reward, tid)
            if sid in seen:
                if seen[sid] != fingerprint:
                    raise ValueError(f"conflicting simulation ID: {sid}")
                excluded["repeated_simulation_id"] += 1
                continue
            seen[sid] = fingerprint
            if reward is None:
                excluded["infrastructure_error"] += 1
                continue
            task = definitions.get(tid)
            if task is None:
                raise ValueError(f"missing task definition for {tid}")
            identity = {"task_hash": digest(task), "policy_hash": digest(policy),
                        "benchmark_commit": info.get("git_commit")}
            if tid in identities and identities[tid] != identity:
                raise ValueError(f"inconsistent task/policy/benchmark for task {tid}")
            identities[tid] = identity
            # Only these non-secret settings reach the legacy parser.
            parsed = parse_simulation(sim, {"agent_info": {"llm": model},
                                            "environment_info": {"domain_name": "airline"}})
            graph = build_step_graph(sim, None, task)
            nodes = [n for n in graph["nodes"] if n["type"] == "AgentStep"]
            raw_steps = [(i, m) for i, m in enumerate(sim.get("messages") or [])
                         if m.get("role") == "assistant"]
            if len(nodes) != len(parsed["steps"]) or len(raw_steps) != len(nodes):
                raise ValueError(f"parser/verifier step count mismatch: {sid}")
            for step, node, (_, raw) in zip(parsed["steps"], nodes, raw_steps):
                calls = raw.get("tool_calls") or []
                if len(calls) > 1:
                    raise ValueError(f"unsupported parallel calls: {sid}")
                call = node.get("tool_call") or {}
                if step["tool"] != call.get("name"):
                    raise ValueError(f"tool alignment mismatch: {sid}")
                if step["tool"] and step["args"] != normalize_args(call["arguments"] or {}):
                    raise ValueError(f"argument alignment mismatch: {sid}")
            selected.append({"id": sid, "_sim": sim, "success": parsed["success"],
                             "task_id": tid, "parsed": parsed, "nodes": nodes,
                             "message_indices": [i for i, _ in raw_steps],
                             "labels": classify_steps_v2(graph, task), "task": task,
                             "policy": policy, "source": source})
    return selected, dict(excluded), inputs, identities


def deduplicate(runs):
    """Separate task identities even if transcript content happens to coincide."""
    out, counts = [], {}
    for task in sorted({r["task_id"] for r in runs}, key=int):
        task_runs = [r for r in runs if r["task_id"] == task]
        outcomes = defaultdict(set)
        for r in task_runs:
            outcomes[content_hash(r["_sim"])].add(r["success"])
        if any(len(v) > 1 for v in outcomes.values()):
            raise ValueError(f"conflicting outcomes in duplicate class, task {task}")
        reps = representatives(task_runs)
        counts[task] = {"runs": len(task_runs), "successes": sum(r["success"] for r in task_runs),
                        "failures": sum(not r["success"] for r in task_runs),
                        "content_classes": len(reps),
                        "successful_classes": sum(r["success"] for r in reps)}
        out.extend(reps)
    return out, counts


def score_queries(runs, min_refs):
    rows, eligible, skipped, reference_manifest = [], [], [], {}
    for q in runs:
        successes = [r for r in runs if r["task_id"] == q["task_id"] and r["success"]]
        refs = references_for(q, successes)
        if len(refs) < min_refs:
            skipped.append({"run_id": q["id"], "task_id": q["task_id"], "success": q["success"],
                            "n_references": len(refs), "reason": "fewer than required references after exclusion"})
            continue
        eligible.append(q)
        reference_manifest[q["id"]] = [r["id"] for r in refs]
        scores = score_run(q["parsed"], [r["parsed"] for r in refs], tool_sim, "max")
        valid_ref_tools = {n["tool_call"]["name"] for r in refs for n in r["nodes"]
                           if n.get("kind") == "tool_call" and r["labels"][n["id"]]["label"] == "valid"}
        any_ref_tools = {n["tool_call"]["name"] for r in refs for n in r["nodes"] if n.get("kind") == "tool_call"}
        for step, node, mi, scored in zip(q["parsed"]["steps"], q["nodes"], q["message_indices"], scores):
            raw_label = q["labels"][node["id"]]
            label = {"valid": "correct", "incorrect": "incorrect"}.get(raw_label["label"], raw_label["label"])
            tool = step["tool"] or ""
            rows.append({"task_id": q["task_id"], "run_id": q["id"], "step_index": step["idx"],
                         "event_id": node["id"], "message_index": mi,
                         "success": q["success"], "multiplicity": q["multiplicity"],
                         "kind": "tool_call" if tool else "message", "tool": tool,
                         "n_references": len(refs), "confidence": scored["score"],
                         "label": label, "verifier_label": raw_label["label"],
                         "label_reason": raw_label["reason"] or "",
                         "tool_in_successful_references": tool in any_ref_tools,
                         "tool_valid_in_successful_references": tool in valid_ref_tools,
                         "source": q["source"]})
    return rows, eligible, skipped, reference_manifest


def analyze(rows):
    result, localization = {}, []
    for scope in ("all_agent_steps", "tool_calls"):
        scoped = [r for r in rows if scope == "all_agent_steps" or r["kind"] == "tool_call"]
        groups = defaultdict(list)
        for r in scoped:
            groups[r["run_id"]].append(dict(r))
        for group in groups.values():
            group.sort(key=lambda r: r["step_index"])
            for i, row in enumerate(group):
                row["last_step_confidence"] = 1 - i / (len(group) - 1) if len(group) > 1 else 0.0
            if group[0]["success"]:
                continue
            target = next((i for i, r in enumerate(group) if r["label"] == "incorrect"), None)
            if target is None:
                continue
            for method, metrics in (("nibs", target_rank([r["confidence"] for r in group], target)),
                                    ("random_expected", random_target_rank(len(group))),
                                    ("last_step_first", target_rank([r["last_step_confidence"] for r in group], target))):
                localization.append({"scope": scope, "method": method, "task_id": group[0]["task_id"],
                                     "run_id": group[0]["run_id"], "target_step_index": group[target]["step_index"],
                                     "target_event_id": group[target]["event_id"], **metrics})
        task_metrics = {}
        for tid in sorted({r["task_id"] for r in rows}, key=int):
            task_rows = [r for group in groups.values() for r in group if r["task_id"] == tid]
            methods = {"nibs": binary_metrics(task_rows),
                       "last_step_first": binary_metrics(task_rows, "last_step_confidence")}
            methods["random_expected"] = random_binary_metrics(methods["nibs"]["n_correct"], methods["nibs"]["n_incorrect"])
            failed_ids = {r["run_id"] for r in rows if r["task_id"] == tid and not r["success"]}
            failed = [groups.get(rid, []) for rid in failed_ids]
            for method in methods:
                loc = [r for r in localization if r["scope"] == scope and r["task_id"] == tid and r["method"] == method]
                methods[method]["localization"] = localization_summary(loc)
            label_counts = Counter(r["label"] for r in task_rows)
            task_metrics[tid] = {"n_steps": len(task_rows), "label_counts": dict(label_counts),
                                 "n_failed_queries": len(failed),
                                 "failed_queries_without_candidates": sum(not g for g in failed),
                                 "failed_queries_without_labelled_error": sum(not any(r["label"] == "incorrect" for r in g) for g in failed),
                                 "methods": methods}
        aggregates = {}
        for method in ("nibs", "random_expected", "last_step_first"):
            available = [v["methods"][method] for v in task_metrics.values() if v["methods"][method]["n_pairs"]]
            pairs = sum(m["n_pairs"] for m in available)
            aggregates[method] = {"n_tasks_with_both_classes": len(available),
                                  "macro_auroc": mean(m["auroc_error_positive"] for m in available),
                                  "within_task_pair_weighted_auroc": sum(m["auroc_error_positive"] * m["n_pairs"] for m in available) / pairs if pairs else None,
                                  "localization": localization_summary(r for r in localization if r["scope"] == scope and r["method"] == method)}
        result[scope] = {"tasks": task_metrics, "aggregate": aggregates}
    return result, localization


def review_export(out, runs, rows):
    # Prevent already-started reviews from being silently reattached to changed context.
    manifest = {run["id"]: {"content_hash": run["content_hash"], "task_hash": digest(run["task"]),
                            "policy_hash": digest(run["policy"])}
                for run in runs if not run["success"]}
    manifest_path = out / "review/manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("review context changed; choose a new output directory to preserve existing reviews")
    write_json(manifest_path, manifest)
    review_rows = []
    for run in runs:
        if run["success"]:
            continue
        relative = f"review/context/task{run['task_id']}_{run['id']}.json"
        messages = []
        for i, m in enumerate(run["_sim"].get("messages") or []):
            # Do not export raw_data, llm_args, provider headers or other metadata.
            messages.append({"message_index": i, "role": m.get("role"), "content": m.get("content"),
                             "error": bool(m.get("error")),
                             "tool_calls": [{"name": c.get("name"), "arguments": c.get("arguments") or {}}
                                            for c in m.get("tool_calls") or []]})
        context = {"task_id": run["task_id"], "run_id": run["id"], "task": run["task"],
                   "policy": run["policy"], "messages": messages,
                   "agent_steps": [{"step_index": s["idx"], "event_id": n["id"], "message_index": mi}
                                   for s, n, mi in zip(run["parsed"]["steps"], run["nodes"], run["message_indices"])]}
        write_json(out / relative, context)
        for row in rows:
            if row["run_id"] == run["id"]:
                review_rows.append({**{k: row[k] for k in REVIEW_COLUMNS if k in row}, "context_file": relative,
                                    "reviewer_1": "", "reviewer_2": "", "adjudicated_label": "", "notes": ""})
    path = out / "review/labels.csv"
    if path.exists():
        with path.open(newline="") as f:
            existing = list(csv.DictReader(f))
        keys = lambda rs: [(str(r["task_id"]), r["run_id"], str(r["step_index"]), r["event_id"]) for r in rs]
        if keys(existing) != keys(review_rows):
            raise ValueError("existing review sheet belongs to a different selection; choose a new output directory")
    else:
        write_csv(path, review_rows, REVIEW_COLUMNS)
    return review_rows


def import_human(path, expected, scored_rows):
    expected_by_key = {(r["run_id"], str(r["step_index"])): r for r in expected}
    resolved, pairs, seen = {}, [], set()
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if not set(REVIEW_COLUMNS).issubset(reader.fieldnames or []):
            raise ValueError("human sheet is missing required columns")
        for row in reader:
            key = row["run_id"], row["step_index"]
            if key not in expected_by_key or key in seen:
                raise ValueError("unknown or duplicate step identity in human sheet")
            seen.add(key)
            original = expected_by_key[key]
            if any(row[k] != str(original[k]) for k in ("task_id", "event_id", "kind", "tool", "context_file")):
                raise ValueError("modified step metadata in human sheet")
            a, b, final = (row[k].strip() for k in ("reviewer_1", "reviewer_2", "adjudicated_label"))
            if any(x and x not in HUMAN_LABELS for x in (a, b, final)):
                raise ValueError("unsupported human label")
            if final and not (a and b):
                raise ValueError("adjudication requires both independent labels")
            if a and b:
                pairs.append((a, b))
                if a == b:
                    if final and final != a:
                        raise ValueError("adjudication conflicts with agreed reviewer labels")
                    resolved[key] = a
                elif final:
                    resolved[key] = final
    if seen != set(expected_by_key):
        raise ValueError("human sheet must preserve every exported step identity, including blank rows")
    per_run = defaultdict(list)
    for key in expected_by_key:
        per_run[key[0]].append(key)
    complete = {rid for rid, keys in per_run.items() if all(k in resolved for k in keys)}
    rows = [{**r, "label": resolved[(r["run_id"], str(r["step_index"]))]}
            for r in scored_rows if r["run_id"] in complete]
    metrics, loc = analyze(rows)
    return {"agreement": agreement(pairs), "n_resolved_steps": len(resolved),
            "n_review_runs": len(per_run), "n_complete_runs": len(complete),
            "n_incomplete_runs": len(per_run) - len(complete),
            "note": "Metrics use complete failed runs only; correct steps in successful runs are not human-reviewed here.",
            "metrics": metrics}, loc


def fmt(x):
    return "—" if x is None else f"{x:.3f}"


def report(summary):
    all_agg = summary["automatic_metrics"]["all_agent_steps"]["aggregate"]
    tool_agg = summary["automatic_metrics"]["tool_calls"]["aggregate"]
    lines = ["# NIBS retrospective evaluation", "",
             "**Status: automatic-label diagnostic. Independent human review is pending unless explicitly reported below.**", "",
             "The original tool-only NIBS implementation was evaluated without training or model/API calls. "
             "The selected milestone tasks were already exposed during development; these are not independent test results.", "",
             "## Main findings", "",
             f"- NIBS macro AUROC: {fmt(all_agg['nibs']['macro_auroc'])} on {all_agg['nibs']['n_tasks_with_both_classes']} tasks with both automatic labels. This excludes unverified steps.",
             f"- {summary['error_profile']['tool_absent_from_references']} incorrect actions use tools absent from every successful reference. These are easier than wrong-argument errors.",
             "- Inspect the same-tool cases below: high scores can miss wrong arguments even when labelled-subset AUROC is perfect.",
             f"- Tool-only localization top-1: NIBS {fmt(tool_agg['nibs']['localization']['top1'])}, last-step-first {fmt(tool_agg['last_step_first']['localization']['top1'])}. Compare both before claiming a benefit over simple baselines.", "",
             "## Dataset and references", "",
             "| Task | Runs (success / failed) | Content classes | Successful classes | Scored queries |", "|---|---|---|---|---|"]
    for tid, d in summary["dataset"].items():
        lines.append(f"| {tid} | {d['runs']} ({d['successes']} / {d['failures']}) | {d['content_classes']} | {d['successful_classes']} | {d['scored_queries']} |")
    lines += ["", f"Exclusions before scoring: `{summary['excluded']}`. Queries excluded for insufficient references: {len(summary['skipped_queries'])}.",
              "References are distinct successful trajectories of the same task, with the query's entire content class removed. "
              f"Each scored query has at least {summary['min_references']} references. Each content class contributes once.", "",
              "## Rule-label coverage", "", f"All scored agent steps: **{summary['n_steps']}**. Label counts: `{summary['label_counts']}`.", "",
              "Only `valid` and `incorrect` enter binary metrics. Attempted errors and unverified steps are excluded. "
              "Unverified steps still compete in localization rankings. Labels compare selected fields with gold actions, "
              "not human reasoning judgments; they share field definitions with the structured matcher and do not prove causality.", ""]
    for scope, scope_data in summary["automatic_metrics"].items():
        lines += [f"## {scope.replace('_', ' ').capitalize()}", "",
                  "AUROC is error-positive (low confidence = error). AP uses grouped thresholds. "
                  "Top-k targets the first verifier-labelled executed incorrect action in a failed run.", "",
                  "| Task | Correct / incorrect | NIBS AUROC | Random AUROC | Last-first AUROC | NIBS AP | Eligible failed runs / total | NIBS top-1 / top-3 | Random top-1 / top-3 | Last-first top-1 / top-3 |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for tid, d in scope_data["tasks"].items():
            n, r, last = (d["methods"][m] for m in ("nibs", "random_expected", "last_step_first"))
            nl, rl, ll = (x["localization"] for x in (n, r, last))
            lines.append(f"| {tid} | {n['n_correct']} / {n['n_incorrect']} | {fmt(n['auroc_error_positive'])} | {fmt(r['auroc_error_positive'])} | {fmt(last['auroc_error_positive'])} | {fmt(n['average_precision_error_positive'])} | {nl['n_failed_queries_with_labelled_error']} / {d['n_failed_queries']} | {fmt(nl['top1'])} / {fmt(nl['top3'])} | {fmt(rl['top1'])} / {fmt(rl['top3'])} | {fmt(ll['top1'])} / {fmt(ll['top3'])} |")
        lines += ["", "| Method | Tasks with both labels | Macro AUROC | Within-task pair-weighted AUROC | Localization runs | Top-1 | Top-3 | MRR |", "|---|---|---|---|---|---|---|---|"]
        for method, d in scope_data["aggregate"].items():
            loc = d["localization"]
            lines.append(f"| {method} | {d['n_tasks_with_both_classes']} | {fmt(d['macro_auroc'])} | {fmt(d['within_task_pair_weighted_auroc'])} | {loc['n_failed_queries_with_labelled_error']} | {fmt(loc['top1'])} | {fmt(loc['top3'])} | {fmt(loc['reciprocal_rank'])} |")
        lines += ["", "Ties use exact expected rank/top-k under uniform tie-breaking; random is its analytical expectation, not a selected seed. "
                  "A high AUROC on tools absent from successful references is weak evidence of subtle error detection.", ""]
    lines += ["## Trajectory score gap", "", "These are mean scores per trajectory (all agent steps), then averaged within outcome. "
              "They do not measure step correctness. A missing outcome group produces no gap.", "",
              "| Task | Mean successful | Mean failed | Gap |", "|---|---|---|---|"]
    for tid, d in summary["score_gap"].items():
        lines.append(f"| {tid} | {fmt(d['successful'])} | {fmt(d['failed'])} | {fmt(d['gap'])} |")
    lines += ["", "## Difficult errors and milestone checks", "",
              f"Executed incorrect steps using a tool that is valid in a successful reference: **{summary['error_profile']['same_tool_valid_reference']}**. "
              f"Incorrect steps whose tool is absent from all successful references: **{summary['error_profile']['tool_absent_from_references']}**. "
              f"Other incorrect steps: **{summary['error_profile']['other']}**.", "",
              "The following are the subtle same-tool cases. A score below 0.5 is a flag; exactly 0.5 is not.", "",
              "| Task | Run | Step (zero-based) / event | Tool | NIBS confidence | Flagged at <0.5? |", "|---|---|---|---|---|---|"]
    for case in summary["same_tool_errors"]:
        lines.append(f"| {case['task_id']} | {case['run_id'][:8]} | {case['step_index']} / {case['event_id']} | {case['tool']} | {fmt(case['confidence'])} | {'yes' if case['confidence'] < .5 else 'no'} |")
    lines += ["", "A threshold failure and a ranking success can coexist: a wrong step can score below every labelled-correct "
              "step yet still have high absolute confidence. Unverified steps may rank below it, lowering localization accuracy.", "",
              f"All-agent AUROC >0.6 on {summary['milestone_checks']['tasks_auroc_above_0.6']} tasks; "
              f"the milestone target of at least three tasks is **{'met numerically' if summary['milestone_checks']['auroc_target_met'] else 'not met'}**. "
              "This is a descriptive check with sparse rule labels, not statistical validation.", "",
              f"All-agent top-1 exceeds random expectation: **{summary['milestone_checks']['top1_above_random']}**. "
              f"Top-3 exceeds random expectation: **{summary['milestone_checks']['top3_above_random']}**.", "",
              "## Human review", "",
              "`review/labels.csv` contains every agent step in eligible failed queries. Context files provide task instructions, "
              "policy, transcript and step-to-message mapping. Scores and automatic labels are hidden. Give reviewers separate "
              "copies, then combine their columns in the master sheet. Enter independent labels "
              "in reviewer_1 and reviewer_2; adjudicate disagreements in adjudicated_label. Allowed values: correct, incorrect, "
              "ambiguous, tool_or_env_error. Existing entries are preserved on rerun.", "",
              "After review: `python3 -B nibs/run_evaluation.py --human-labels results/nibs_evaluation/review/labels.csv`.", ""]
    if summary.get("human_review"):
        h = summary["human_review"]
        lines += [f"Complete reviewed failed runs: **{h['n_complete_runs']} / {h['n_review_runs']}**. "
                  f"Double-labelled steps: {h['agreement']['n_double_labelled']}; "
                  f"agreement {fmt(h['agreement']['agreement'])}; Cohen's kappa {fmt(h['agreement']['cohens_kappa'])}.", "",
                  "Human metrics and denominators are in summary.json; per-run rankings are in human_localization.csv. "
                  "Incomplete runs are excluded from human metrics.", ""]
        lines += ["| Human-reviewed scope | Method | Tasks with both labels | Macro AUROC | Localization runs | Top-1 | Top-3 |", "|---|---|---|---|---|---|---|"]
        for scope, data in h["metrics"].items():
            for method, data in data["aggregate"].items():
                loc = data["localization"]
                lines.append(f"| {scope} | {method} | {data['n_tasks_with_both_classes']} | {fmt(data['macro_auroc'])} | {loc['n_failed_queries_with_labelled_error']} | {fmt(loc['top1'])} | {fmt(loc['top3'])} |")
        lines.append("")
    lines += ["## Limits and next action", "",
              "- Task exposure, few difficult negatives, and incomplete labels prevent a general failure-localization claim.",
              "- NIBS tool_sim scores any two plain-text messages as 1, regardless of meaning. High message scores are not evidence of correctness.",
              "- A low score can reflect an uncommon valid path. It is not a calibrated probability of error.",
              "- First labelled incorrect action can differ from the true first error or causal failure. Omitted actions have no step to rank.",
              "- Finish independent review before interpreting these numbers as human-validated results. More diagnostic data may still be necessary.",
              "- Full GIBS training is outside this NIBS evaluation.", "",
              "## Reproduce", "", "```bash", "python3 -B nibs/run_evaluation.py", "```", "",
              "See nibs/EVALUATION_PROTOCOL.md. summary.json records file/code hashes, reference IDs, exclusions and metrics. "
              "The original scorer and historical experiment files are unchanged.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=REPO / "results")
    parser.add_argument("--output", type=Path, default=REPO / "results/nibs_evaluation")
    parser.add_argument("--tasks", nargs="+", default=list(DEFAULT_TASKS), choices=DEFAULT_TASKS)
    parser.add_argument("--min-references", type=int, default=3)
    parser.add_argument("--human-labels", type=Path)
    args = parser.parse_args(argv)
    if args.min_references < 1:
        parser.error("--min-references must be positive")
    tasks = sorted(set(args.tasks), key=int)
    loaded, excluded, inputs, identities = load_runs(args.results_root, tasks)
    if set(tasks) != {r["task_id"] for r in loaded}:
        raise ValueError("one or more requested tasks has no usable runs in the selected regime")
    reps, dataset = deduplicate(loaded)
    rows, eligible, skipped, refs = score_queries(reps, args.min_references)
    if not rows:
        raise ValueError("no queries have sufficient references")
    metrics, localization = analyze(rows)
    gaps = {}
    for tid in tasks:
        groups = defaultdict(list)
        for r in rows:
            if r["task_id"] == tid:
                groups[(r["run_id"], r["success"])].append(r["confidence"])
        s = mean(mean(v) for (_, success), v in groups.items() if success)
        f = mean(mean(v) for (_, success), v in groups.items() if not success)
        gaps[tid] = {"successful": s, "failed": f, "gap": s - f if s is not None and f is not None else None}
        dataset[tid]["scored_queries"] = sum(r["task_id"] == tid for r in eligible)
    errors = [r for r in rows if r["label"] == "incorrect"]
    same = sum(r["tool_valid_in_successful_references"] for r in errors)
    absent = sum(not r["tool_in_successful_references"] for r in errors)
    agg = metrics["all_agent_steps"]["aggregate"]
    task_passes = sum((d["methods"]["nibs"]["auroc_error_positive"] or 0) > .6
                      for d in metrics["all_agent_steps"]["tasks"].values())
    better = lambda k: (None if agg["nibs"]["localization"][k] is None else
                         agg["nibs"]["localization"][k] > agg["random_expected"]["localization"][k])
    summary = {"protocol": "nibs/EVALUATION_PROTOCOL.md", "evaluation_type": "retrospective_development_tasks",
               "model": MODEL, "agent_temperature": 0.0, "user_temperature": 0.0,
               "verifier_version": VERSION, "min_references": args.min_references,
               "dataset": dataset, "excluded": excluded, "skipped_queries": skipped,
               "n_steps": len(rows), "label_counts": dict(Counter(r["label"] for r in rows)),
               "error_profile": {"same_tool_valid_reference": same, "tool_absent_from_references": absent,
                                 "other": len(errors) - same - absent},
               "same_tool_errors": [{k: r[k] for k in ("task_id", "run_id", "step_index", "event_id", "tool", "confidence", "label_reason")}
                                    for r in errors if r["tool_valid_in_successful_references"]],
               "automatic_metrics": metrics, "score_gap": gaps,
               "milestone_checks": {"tasks_auroc_above_0.6": task_passes, "auroc_target_met": task_passes >= 3,
                                    "top1_above_random": better("top1"), "top3_above_random": better("top3")},
               "provenance": {"input_file_sha256": inputs, "task_identities": identities,
                              "code_sha256": {p: file_hash(REPO / p) for p in SOURCE_FILES},
                              "references": refs,
                              "queries": [{"run_id": r["id"], "task_id": r["task_id"],
                                           "content_hash": r["content_hash"], "multiplicity": r["multiplicity"],
                                           "duplicate_ids": r["duplicates"]} for r in eligible]}}
    expected = review_export(args.output, eligible, rows)
    summary["human_review_pending_steps"] = len(expected)
    if args.human_labels:
        human, human_loc = import_human(args.human_labels, expected, rows)
        summary["human_review"] = human
        summary["human_review_pending_steps"] = len(expected) - human["n_resolved_steps"]
        summary["provenance"]["human_labels_sha256"] = file_hash(args.human_labels)
        write_csv(args.output / "human_localization.csv", human_loc,
                  ["scope", "method", "task_id", "run_id", "target_step_index", "target_event_id",
                   "n_candidates", "rank_min", "rank_max", "expected_rank", "top1", "top3", "reciprocal_rank"])
    write_json(args.output / "summary.json", summary)
    write_csv(args.output / "per_step.csv", rows, list(rows[0]))
    write_csv(args.output / "localization.csv", localization,
              ["scope", "method", "task_id", "run_id", "target_step_index", "target_event_id",
               "n_candidates", "rank_min", "rank_max", "expected_rank", "top1", "top3", "reciprocal_rank"])
    (args.output / "REPORT.md").write_text(report(summary))
    print(f"Scored {len(eligible)} distinct trajectories; {len(rows)} agent steps; {len(errors)} rule-labelled executed errors.")
    print(f"Automatic-label macro AUROC: {fmt(agg['nibs']['macro_auroc'])}; "
          f"top-1: {fmt(agg['nibs']['localization']['top1'])} vs random {fmt(agg['random_expected']['localization']['top1'])}.")
    print(f"Independent human review pending: {summary['human_review_pending_steps']} steps. Report: {args.output / 'REPORT.md'}")


if __name__ == "__main__":
    main()
