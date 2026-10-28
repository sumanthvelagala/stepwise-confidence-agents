"""
Entailment scoring for MCS.

PDF (C.3, D.3): MCS uses an NLI model (DeBERTa-large-MNLI) with entailment thresholds. Direction, score type
and input format are not specified.
Author code (src/GIBS/find_mcs.py): `microsoft/deberta-large-mnli`; input is the single string
`text1 + ' [SEP] ' + text2`; softmax over logits, index 2 = ENTAILMENT; similarity = max of both directions.

Here:
  * `EntailmentModel.entail_batch` returns one-way P(entailment | premise, hypothesis).
  * `Similarity` turns that into the similarity used by MCS:
        'max_bidirectional' (author code; primary, R2)  = max(P(a=>b), P(b=>a))
        'one_way'           (ablation)                   = P(query => reference)
  * Inputs longer than the model limit (512 tokens). PDF: silent. Author code: `truncation=True`, which cuts the
    end of the joined string. `overlength='truncate'` reproduces that (R0) but records every truncated pair in
    `self.truncated` and caches it under a separate key; `overlength='error'` raises `OverlengthError` instead.
  * `overlength='symmetric'` [OURS, experimental variant C1/C3]: the two texts are truncated independently, each to
    a fair share of the token budget (see `symmetric_input_ids`), so both stay represented. Pairs that fit within
    the limit are encoded exactly as before. Cached under its own key.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Protocol

DIRECTIONS = ("max_bidirectional", "one_way")
DEFAULT_MODEL = "microsoft/deberta-large-mnli"
DEFAULT_CACHE_DIR = Path(os.environ.get("STEPWISE_NLI_CACHE", Path.home() / ".cache" / "stepwise_nli"))


class OverlengthError(ValueError):
    pass


OVERLENGTH_MODES = ("error", "truncate", "symmetric")


def symmetric_input_ids(tokenizer, a: str, b: str, max_length: int, encoding: str = "code_sep_string"):
    """[OURS] Token ids `[CLS] a' [SEP] b' [SEP]` where a', b' are head-truncated so that the total is <= max_length.

    The untruncated ids are produced with the same encoding as the non-truncated path (author-code string or pair
    encoding) and split at the separator, so tokenization of each text is unchanged. Budget for the two texts is
    max_length minus the special tokens ([CLS], separator block, final [SEP]). If both exceed half the budget, each gets half; otherwise the shorter text is kept
    whole and the longer one gets the remainder. Returns (ids, info).
    """
    if encoding == "code_sep_string":
        full = tokenizer(f"{a} [SEP] {b}", truncation=False)["input_ids"]
    else:
        full = tokenizer(a, b, truncation=False)["input_ids"]
    cls, sep = tokenizer.cls_token_id, tokenizer.sep_token_id
    if full[0] != cls or full[-1] != sep or sep not in full[1:-1]:
        raise ValueError("unexpected special-token layout")
    mid = full.index(sep, 1)
    end = mid
    while full[end + 1] == sep and end + 1 < len(full) - 1:   # pair encoding uses '[SEP] [SEP]' between texts
        end += 1
    sep_block = full[mid:end + 1]
    ids_a, ids_b = full[1:mid], full[end + 1:-1]
    budget = max_length - 2 - len(sep_block)
    la, lb = len(ids_a), len(ids_b)
    if la + lb <= budget:
        ka, kb = la, lb
    else:
        half = budget // 2
        if la <= half:
            ka, kb = la, budget - la
        elif lb <= half:
            ka, kb = budget - lb, lb
        else:
            ka, kb = half, budget - half
    ids = [cls] + ids_a[:ka] + sep_block + ids_b[:kb] + [sep]
    return ids, {"len_a": la, "len_b": lb, "kept_a": ka, "kept_b": kb, "total": len(ids),
                 "n_special": 2 + len(sep_block)}


class EntailmentModel(Protocol):
    def entail_batch(self, pairs: list[tuple[str, str]]) -> list[float]: ...


class StubEntailment:
    """Deterministic entailment table for tests. Identical strings entail each other with `identical`."""

    def __init__(self, table: dict[tuple[str, str], float] | None = None, default: float = 0.0,
                 identical: float = 1.0):
        self.table = dict(table or {})
        self.default = default
        self.identical = identical
        self.calls: list[tuple[str, str]] = []

    def entail_batch(self, pairs):
        self.calls += pairs
        return [self.identical if a == b else self.table.get((a, b), self.default) for a, b in pairs]


class DebertaEntailment:
    """`microsoft/deberta-large-mnli` with a persistent on-disk cache (outside the repository)."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None,
                 encoding: str = "code_sep_string", batch_size: int = 8, cache_dir: Path | None = DEFAULT_CACHE_DIR,
                 overlength: str = "error"):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        if encoding not in ("code_sep_string", "pair"):
            raise ValueError("encoding must be 'code_sep_string' (author code) or 'pair'")
        if overlength not in OVERLENGTH_MODES:
            raise ValueError(f"overlength must be one of {OVERLENGTH_MODES}")
        self.overlength = overlength
        self.truncated: set[tuple[str, str]] = set()
        self.n_forward = 0          # model forward passes (pairs actually scored, i.e. cache misses)
        self.n_requested = 0        # pairs requested, including cache hits
        self.torch = torch
        self.model_name = model_name
        self.encoding = encoding
        self.batch_size = batch_size
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, dtype=torch.float32)
        self.model.to(self.device).eval()
        labels = {v.lower(): int(k) for k, v in self.model.config.id2label.items()}
        self.entail_index = labels["entailment"]
        try:  # exact Hugging Face snapshot (commit) that was loaded
            from huggingface_hub import snapshot_download
            self.revision = Path(snapshot_download(model_name, local_files_only=True)).name
        except Exception:
            self.revision = getattr(self.model.config, "_commit_hash", None) or "unknown"
        self.max_length = min(self.tokenizer.model_max_length, self.model.config.max_position_embeddings)
        self.cache: dict[str, float] = {}
        self.cache_file = None
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            tag = f"{model_name.replace('/', '__')}__{self.revision[:12]}__{encoding}"
            self.cache_file = cache_dir / f"{tag}.jsonl"
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    for line in f:
                        rec = json.loads(line)
                        self.cache[rec["k"]] = rec["p"]

    def with_encoding(self, encoding: str) -> "DebertaEntailment":
        """Same loaded weights, different input encoding, separate cache."""
        import copy
        other = copy.copy(self)
        other.encoding = encoding
        other.cache = {}
        other.truncated = set()
        if self.cache_file is not None:
            other.cache_file = self.cache_file.with_name(self.cache_file.name.replace(self.encoding, encoding))
            if other.cache_file.exists():
                with open(other.cache_file) as f:
                    for line in f:
                        rec = json.loads(line)
                        other.cache[rec["k"]] = rec["p"]
        return other

    def with_overlength(self, overlength: str) -> "DebertaEntailment":
        """Same loaded weights and encoding, different handling of pairs longer than the model limit."""
        import copy
        if overlength not in OVERLENGTH_MODES:
            raise ValueError(f"overlength must be one of {OVERLENGTH_MODES}")
        other = copy.copy(self)
        other.overlength = overlength
        other.truncated = set()
        return other

    def describe(self) -> dict:
        import transformers
        return {"model": self.model_name, "revision": self.revision, "device": self.device,
                "encoding": self.encoding, "overlength": self.overlength, "entailment_index": self.entail_index,
                "id2label": self.model.config.id2label, "max_length": self.max_length,
                "torch": self.torch.__version__, "transformers": transformers.__version__}

    def _key(self, a: str, b: str, truncated: bool = False) -> str:
        tag = "" if not truncated else chr(0) + ("truncated" if self.overlength != "symmetric" else "symmetric")
        return hashlib.sha256(f"{a}\x00{b}{tag}".encode()).hexdigest()

    def encode(self, pairs: list[tuple[str, str]], pad: bool = True, truncate: bool = False):
        if truncate and self.overlength == "symmetric":
            rows = [symmetric_input_ids(self.tokenizer, a, b, self.max_length, self.encoding)[0] for a, b in pairs]
            width = max(len(r) for r in rows)
            pad_id = self.tokenizer.pad_token_id
            ids = self.torch.tensor([r + [pad_id] * (width - len(r)) for r in rows])
            mask = self.torch.tensor([[1] * len(r) + [0] * (width - len(r)) for r in rows])
            return {"input_ids": ids, "attention_mask": mask}
        kw = {"return_tensors": "pt", "padding": True} if pad else {}
        kw.update({"truncation": True, "max_length": self.max_length} if truncate else {"truncation": False})
        if self.encoding == "code_sep_string":
            return self.tokenizer([f"{a} [SEP] {b}" for a, b in pairs], **kw)   # author code: one string
        return self.tokenizer([a for a, _ in pairs], [b for _, b in pairs], **kw)

    def token_length(self, a: str, b: str) -> int:
        return len(self.encode([(a, b)], pad=False)["input_ids"][0])

    def entail_batch(self, pairs):
        unique = list(dict.fromkeys(pairs))
        self.n_requested += len(unique)
        long = {(a, b) for a, b in unique if self.token_length(a, b) > self.max_length}
        if long and self.overlength == "error":
            a, b = next(iter(long))
            raise OverlengthError(f"{len(long)} pair(s) exceed {self.max_length} tokens "
                                  f"(e.g. {self.token_length(a, b)} tokens; premise starts {a[:60]!r})")
        self.truncated |= long
        new = []
        with self.torch.no_grad():
            for truncate in (False, True):
                todo = [p for p in unique if (p in long) == truncate and self._key(*p, truncate) not in self.cache]
                for i in range(0, len(todo), self.batch_size):
                    chunk = todo[i:i + self.batch_size]
                    enc = {k: v.to(self.device) for k, v in self.encode(chunk, truncate=truncate).items()}
                    probs = self.torch.softmax(self.model(**enc).logits.float(), dim=-1)[:, self.entail_index]
                    self.n_forward += len(chunk)
                    for (a, b), p in zip(chunk, probs.cpu().tolist()):
                        self.cache[self._key(a, b, truncate)] = p
                        new.append({"k": self._key(a, b, truncate), "p": p})
        if new and self.cache_file is not None:
            with open(self.cache_file, "a") as f:
                for rec in new:
                    f.write(json.dumps(rec) + "\n")
        return [self.cache[self._key(a, b, (a, b) in long)] for a, b in pairs]


class Similarity:
    """Similarity between a query-graph text `a` and a reference-graph text `b`."""

    def __init__(self, model: EntailmentModel, direction: str = "max_bidirectional"):
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}")
        self.model = model
        self.direction = direction
        self._memo: dict[tuple[str, str], tuple[float, float | None]] = {}

    def prefetch(self, pairs: Iterable[tuple[str, str]]) -> None:
        pairs = [p for p in dict.fromkeys(pairs) if p not in self._memo]
        if not pairs:
            return
        fwd = self.model.entail_batch(pairs)
        bwd = self.model.entail_batch([(b, a) for a, b in pairs]) if self.direction == "max_bidirectional" \
            else [None] * len(pairs)
        for p, f, b in zip(pairs, fwd, bwd):
            self._memo[p] = (f, b)

    def directional(self, a: str, b: str) -> tuple[float, float | None]:
        if (a, b) not in self._memo:
            self.prefetch([(a, b)])
        return self._memo[(a, b)]

    def __call__(self, a: str, b: str) -> float:
        f, b_ = self.directional(a, b)
        return f if b_ is None else max(f, b_)
