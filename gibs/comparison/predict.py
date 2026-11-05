"""Score one raw trajectory with a paper NIBS variant or trained comparison model."""
import argparse
import json
from pathlib import Path

import torch

from gibs.comparison.graphs import projection, spec, tensors
from gibs.comparison.run import METHODS, load_checkpoint
from gibs.comparison.semantic_nibs import reference_scores
from gibs.learned.data import FrozenBert
from gibs.learned.run_experiment import predict_graph
from gibs.validation.dataset_audit import canon
from nibs.run_evaluation import REPO, deduplicate, load_runs, write_json

NIBS_METHODS = ("paper_nibs_cos_max", "paper_nibs_cos_mean", "released_nibs_cos_max", "released_nibs_cos_mean")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=(*NIBS_METHODS, *METHODS), required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--reference-root", type=Path, default=REPO / "results")
    parser.add_argument("--output", type=Path, default=REPO / "results/paper_comparison/prediction.json")
    args = parser.parse_args(argv)
    torch.set_num_threads(2)
    data = json.loads(args.results.read_text())
    matches = [s for s in data.get("simulations", []) if str(s.get("id", "")).startswith(args.run_id)]
    if len(matches) != 1:
        parser.error("run ID must identify exactly one trajectory")
    raw = matches[0]
    sim = {k: raw[k] for k in ("id", "task_id", "messages")}
    refs = []
    if args.method in NIBS_METHODS:
        pool, _, _, _ = load_runs(args.reference_root, [str(sim["task_id"])])
        pool, _ = deduplicate(pool)
        refs = [r for r in pool if r["success"] and r["content_hash"] != canon(sim)]
        if len(refs) < 3:
            parser.error("NIBS requires at least three distinct successful references, excluding the query class")
        structure = "original"
        model = None
    else:
        if args.checkpoint is None:
            parser.error("learned methods require --checkpoint")
        model, checkpoint = load_checkpoint(args.checkpoint)
        if checkpoint["method"] != args.method:
            parser.error("checkpoint method does not match --method")
        structure = checkpoint["structure"]
    specs = {"query": spec(projection(sim, structure))}
    specs.update({r["id"]: spec(projection(r["_sim"])) for r in refs})
    if not specs["query"]["agent_indices"]:
        parser.error("trajectory has no agent steps")
    bert = FrozenBert(device="cpu")
    embeddings = bert.encode([text for s in specs.values() for field in ("result_texts", "operation_texts") for text in s[field]])
    features = {sid: tensors(s, embeddings) for sid, s in specs.items()}
    if model is not None:
        scores = predict_graph(model, features["query"])
    else:
        q = features["query"]["operations"][features["query"]["agent_indices"]].numpy()
        released = args.method.startswith("released_")
        references = [(features[r["id"]]["edge_operations"] if released else
                       features[r["id"]]["operations"][features[r["id"]]["agent_indices"]]).numpy() for r in refs]
        maximum, average = reference_scores(q, references, released=released)
        scores = maximum if args.method.endswith("max") else average
    write_json(args.output, {"method": args.method, "run_id": sim["id"], "task_id": str(sim["task_id"]),
                            "graph_structure": structure, "query_gold_or_reward_used": False,
                            "reference_ids": [r["id"] for r in refs],
                            "steps": [{"step_index": i, "event_id": event, "confidence": confidence}
                                      for i, (event, confidence) in enumerate(zip(specs["query"]["agent_events"], scores))]})
    print(f"Scored {len(scores)} steps with {args.method}: {args.output}")


if __name__ == "__main__":
    main()
