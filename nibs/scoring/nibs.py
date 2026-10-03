from __future__ import annotations


def _scored_steps(run: dict) -> list[dict]:
    return [s for s in run.get("steps", []) if s.get("scored", True)]


def best_match(step: dict, ref_steps: list[dict], sim_fn, aggregation: str = "max") -> float:
    """Similarity of step against all steps in one reference run (max or mean)."""
    if not ref_steps:
        return 0.0
    scores = [sim_fn(step, t) for t in ref_steps]
    return max(scores) if aggregation == "max" else sum(scores) / len(scores)


def score_run(run: dict, reference_runs: list[dict], sim_fn, aggregation: str = "max") -> list[dict]:
    """Score every step in run against reference_runs. Returns [{"idx": int, "score": float}]."""
    results = []
    for step in _scored_steps(run):
        if not reference_runs:
            score = 0.0
        else:
            per_ref = [best_match(step, _scored_steps(ref), sim_fn, aggregation) for ref in reference_runs]
            score = sum(per_ref) / len(per_ref)
        results.append({"idx": step["idx"], "score": score})
    return results


def score_task(runs: list[dict], sim_fn, aggregation: str = "max", k_min: int = 3) -> dict:
    """
    Score all runs for one task using leave-one-out reference sets.
    Skips if fewer than k_min successful runs exist.
    """
    successful = [r for r in runs if r.get("success")]

    if len(successful) < k_min:
        return {"skipped": True, "reason": f"only {len(successful)} successful run(s), need at least {k_min}", "success_count": len(successful)}

    results = []
    for run in runs:
        refs = [r for r in successful if r is not run]  # leave-one-out
        if not refs:
            continue
        results.append({
            "task_id": run["task_id"],
            "trial": run["trial"],
            "success": run["success"],
            "step_scores": score_run(run, refs, sim_fn, aggregation),
        })

    return {"skipped": False, "success_count": len(successful), "results": results}
