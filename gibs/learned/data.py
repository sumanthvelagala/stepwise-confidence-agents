"""Real trajectory loading, stored MCS teachers, frozen BERT and task-group splits."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from gibs.graph.step_graph import build_step_graph
from gibs.graph.event_projection import ROOT, project
from gibs.learned.model import normalized_adjacency
from nibs.run_evaluation import REPO, deduplicate, file_hash, load_runs, score_queries

BERT_MODEL = "google-bert/bert-base-uncased"
BERT_REVISION = "86b5e0934494bd15c9632b12f734a8a67f723594"
MAX_LENGTH = 256
TASKS = ("9", "25", "48")
SPLIT_SEED = 20261028
TEACHERS = {"paper_style": ("A", "node"), "agent_adapted": ("C4", "ctx")}


def load_dataset():
    loaded, excluded, inputs, identities = load_runs(REPO / "results", TASKS)
    reps, counts = deduplicate(loaded)
    rows, runs, skipped, refs = score_queries(reps, 3)
    if skipped:
        raise ValueError("prototype queries unexpectedly lack successful references")
    return runs, rows, {"tasks": counts, "excluded": excluded, "inputs": inputs,
                         "task_identities": identities, "baseline_references": refs}


def fold_split(runs, heldout):
    """Split by task first, then by class within training task/outcome strata."""
    strata = defaultdict(list)
    test = []
    for r in runs:
        if r["task_id"] == heldout:
            test.append(r)
        else:
            strata[(r["task_id"], r["success"])].append(r)
    train, validation = [], []
    for key, group in sorted(strata.items()):
        ordered = sorted(group, key=lambda r: hashlib.sha256(f"{SPLIT_SEED}|{r['id']}".encode()).hexdigest())
        nval = min(len(group) - 1, math.ceil(.2 * len(group)))
        validation.extend(ordered[:nval])
        train.extend(ordered[nval:])
    if not train or not validation or not test:
        raise ValueError("empty fold partition")
    partitions = [{r["content_hash"] for r in part} for part in (train, validation, test)]
    if any(partitions[i] & partitions[j] for i, j in ((0, 1), (0, 2), (1, 2))):
        raise ValueError("duplicate content crossed fold partitions")
    return {"train": sorted(train, key=lambda r: r["id"]),
            "validation": sorted(validation, key=lambda r: r["id"]),
            "test": sorted(test, key=lambda r: r["id"])}


class StoredTeachers:
    """Read historical real NLI/MCS mappings; restrict references before averaging."""
    def __init__(self, runs):
        self.data, self.provenance = {}, {}
        by_id = {r["id"]: r for r in runs}
        for method, (variant, indicator) in TEACHERS.items():
            self.data[method] = {}
            for task in TASKS:
                folder = "results_pilot" if variant == "A" else "results_c4"
                path = REPO / f"gibs/validation/{folder}/task{task}_{variant}.json"
                data = json.loads(path.read_text())
                model_path = path.parent / "model.json"
                self.provenance[str(path.relative_to(REPO))] = file_hash(path)
                self.provenance[str(model_path.relative_to(REPO))] = file_hash(model_path)
                for q in data["queries"]:
                    if q["query"] not in by_id:
                        continue  # exact-content duplicate classes are represented once
                    run = by_id[q["query"]]
                    if bool(q["success"]) != run["success"] or run["task_id"] != task:
                        raise ValueError("stored query outcome/task mismatch")
                    events = {n["id"] for n in run["nodes"]}
                    for pair in q["per_reference"]:
                        if set(pair[indicator]) != events:
                            raise ValueError("stored MCS / agent event alignment mismatch")
                    self.data[method][q["query"]] = {p["reference"]: p[indicator] for p in q["per_reference"]}
            if set(self.data[method]) != set(by_id):
                raise ValueError("stored teacher missing a query")

    def target(self, method, query, reference_pool):
        refs = [r for r in reference_pool if r["success"] and r["task_id"] == query["task_id"]
                and r["content_hash"] != query["content_hash"]]
        if len(refs) < 3:
            raise ValueError("training target has fewer than three training-only references")
        recorded = self.data[method][query["id"]]
        if any(r["id"] not in recorded for r in refs):
            raise ValueError("requested reference absent from stored MCS output")
        masks = [sum(recorded[r["id"]][n["id"]] for r in refs) / len(refs) for n in query["nodes"]]
        return torch.tensor(masks, dtype=torch.float32), [r["id"] for r in refs]


def graph_texts(sim):
    """Feature extraction deliberately receives no task definitions or outcomes."""
    graph = project(build_step_graph({"id": sim.get("id"), "task_id": sim.get("task_id"),
                                      "messages": sim.get("messages") or []}), "paper_literal")
    ids = list(graph.nodes)
    operations = {e["dst"]: e["text"] for e in graph.edges}
    return {"node_ids": ids,
            "result_texts": [graph.nodes[n]["text"] or "Problem/Initial State" for n in ids],
            "operation_texts": [operations.get(n, "Problem/Initial State") for n in ids],
            "edges": [(ids.index(e["src"]), ids.index(e["dst"])) for e in graph.edges],
            "agent_indices": [i for i, n in enumerate(ids) if graph.nodes[n]["scorable"]],
            "agent_events": [graph.nodes[n]["event"] for n in ids if graph.nodes[n]["scorable"]]}


class FrozenBert:
    def __init__(self, device="cpu", cache_dir=None):
        self.device = device
        self.cache_dir = Path(cache_dir or Path.home() / ".cache/stepwise_gibs")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.cache_dir / f"bert_{BERT_REVISION}_cls_{MAX_LENGTH}.npz"
        self.metadata_path = self.path.with_suffix(".json")
        self.values = {}
        self.lengths = {}
        if self.path.exists() and self.metadata_path.exists():
            with np.load(self.path, allow_pickle=False) as arrays:
                self.values = {key: arrays[key] for key in arrays.files}
            self.lengths = json.loads(self.metadata_path.read_text())

    @staticmethod
    def key(text):
        return hashlib.sha256(text.encode()).hexdigest()

    def encode(self, texts, batch_size=16):
        from transformers import AutoModel, AutoTokenizer
        unique = sorted(set(texts))
        missing = [t for t in unique if self.key(t) not in self.values]
        if missing:
            tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL, revision=BERT_REVISION)
            model = AutoModel.from_pretrained(BERT_MODEL, revision=BERT_REVISION, use_safetensors=True).to(self.device).eval()
            for parameter in model.parameters():
                parameter.requires_grad_(False)
            for start in range(0, len(missing), batch_size):
                batch = missing[start:start + batch_size]
                lengths = tokenizer(batch, truncation=False, return_length=True)["length"]
                inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=MAX_LENGTH)
                with torch.no_grad():
                    vectors = model(**{k: v.to(self.device) for k, v in inputs.items()}).last_hidden_state[:, 0].cpu().numpy()
                for text, length, vector in zip(batch, lengths, vectors):
                    self.values[self.key(text)] = vector
                    self.lengths[self.key(text)] = length
                if start % (batch_size * 10) == 0:
                    print(f"BERT features {min(start + len(batch), len(missing))}/{len(missing)}", flush=True)
            np.savez_compressed(self.path, **self.values)
            self.metadata_path.write_text(json.dumps(self.lengths, sort_keys=True) + "\n")
            del model
            if self.device == "mps":
                torch.mps.empty_cache()
        self.description = {"model": BERT_MODEL, "revision": BERT_REVISION, "pooling": "CLS", "max_length": MAX_LENGTH,
                            "device": self.device, "n_unique_texts": len(unique), "n_new_embeddings": len(missing),
                            "n_texts_truncated": sum(self.lengths[self.key(t)] > MAX_LENGTH for t in unique),
                            "frozen": True}
        return {t: self.values[self.key(t)] for t in unique}


def tensor_graph(spec, embeddings):
    return {"results": torch.tensor(np.stack([embeddings[t] for t in spec["result_texts"]]), dtype=torch.float32),
            "operations": torch.tensor(np.stack([embeddings[t] for t in spec["operation_texts"]]), dtype=torch.float32),
            "adjacency": normalized_adjacency(len(spec["node_ids"]), spec["edges"]),
            "agent_indices": torch.tensor(spec["agent_indices"], dtype=torch.long)}


def prepare_features(runs, bert):
    specs = {r["id"]: graph_texts(r["_sim"]) for r in runs}
    embeddings = bert.encode([t for spec in specs.values() for field in ("result_texts", "operation_texts") for t in spec[field]])
    for run in runs:
        if specs[run["id"]]["agent_events"] != [n["id"] for n in run["nodes"]]:
            raise ValueError("BERT graph / scorer step alignment mismatch")
    return {rid: tensor_graph(spec, embeddings) for rid, spec in specs.items()}
