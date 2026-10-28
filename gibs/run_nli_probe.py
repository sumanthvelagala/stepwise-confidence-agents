"""
NLI validation probe: does DeBERTa-large-MNLI separate the distinctions our MCS relies on, at tau = 0.7?

Every pair is taken from real trajectories via the v0.2 step graph, so the strings are exactly what MCS would
compare. `a` is always the failed-run (query) text and `b` the passing-run (reference) text. Expectations were
written before running the model and are not adjusted afterwards.

Usage:  .venv/bin/python gibs/run_nli_probe.py [--out-dir gibs/examples/task48_pair] [--cpu-check 6]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from gibs.graph.step_graph import build_step_graph, load_simulation  # noqa: E402
from gibs.mcs.nli import DebertaEntailment  # noqa: E402

TAU = 0.7
F_48 = "results/pilot/tasks_25_40_48/results.json"
F_40 = "results/probe/new_batch2/results.json"
F_25 = "results/probe/new_batch1/results.json"
F_25P = "results/pilot/tasks_25_40_48/results.json"
F_3P, F_3F = "results/pilot/task_3_topup/results.json", "results/pilot/tasks_1_3_9_38/results.json"
F_34, F_34T = "results/pilot/task_34/results.json", "results/pilot/task_34_topup/results.json"

# (id, category, description, (file, sim, raw_msg_index, field) for a=failed, same for b=passing, expectation, why)
PAIRS = [
    ("P01", "identical tool call", "T48 get_reservation_details(3RK2T9): fail vs pass",
     (F_48, "7f5cbcd7", 4, "op"), (F_48, "c890f90b", 4, "op"), "high", "identical strings"),
    ("P02", "identical message", "T48 greeting: fail vs pass",
     (F_48, "7f5cbcd7", 0, "op"), (F_48, "c890f90b", 0, "op"), "high", "identical strings"),
    ("P03", "same tool, different value", "T40 update_reservation_passengers: dob 1992-07-15 (fail) vs 1989-12-13",
     (F_40, "b4901df6", 10, "op"), (F_40, "f6000fbe", 8, "op"), "low", "different passenger DOB is a different action"),
    ("P04", "same tool, different value", "T25 final book_reservation: 2024-05-21/HAT267 (fail) vs 2024-05-17/HAT251",
     (F_25, "6f12b024", "last:book_reservation", "op"), (F_25P, "pass:last:book_reservation", None, "op"),
     "low", "different date and flight"),
    ("P05", "different tool, same argument", "T48 cancel_reservation(3RK2T9) vs get_reservation_details(3RK2T9)",
     (F_48, "7f5cbcd7", 6, "op"), (F_48, "c890f90b", 4, "op"), "low", "write vs read"),
    ("P06", "identical observation", "T48 lookup observation: fail vs pass",
     (F_48, "7f5cbcd7", 4, "result"), (F_48, "c890f90b", 4, "result"), "high", "identical strings"),
    ("P07", "near-duplicate observation", "T48 cancel observation (status cancelled, refund -280) vs lookup observation",
     (F_48, "7f5cbcd7", 6, "result"), (F_48, "c890f90b", 4, "result"), "low",
     "status changed to cancelled and a refund was issued"),
    ("P08", "near-duplicate observation", "T40 update observation: dob 1992-07-15 (fail) vs 1989-12-13",
     (F_40, "b4901df6", 10, "result"), (F_40, "f6000fbe", 8, "result"), "low", "different stored DOB"),
    ("P09", "user turn, same content", "T48 user gives IDs: fail vs pass (paraphrase)",
     (F_48, "7f5cbcd7", 3, "op"), (F_48, "c890f90b", 3, "op"), "high", "same IDs and claim"),
    ("P10", "user turn, different content", "T48 'thanks for confirming the cancellation' (fail) vs 'please re-check / appeal'",
     (F_48, "7f5cbcd7", 9, "op"), (F_48, "c890f90b", 7, "op"), "low", "different conversational state"),
    ("P11", "user turn, same instruction", "T34 'cancel the entire request, keep original' (fail) vs same intent (pass)",
     (F_34, "2a9a7a9b", 11, "op"), (F_34, "b47dbb44", 15, "op"), "high", "same instruction, different wording"),
    ("P12", "user turn, contradictory instruction", "T34 'proceed with all changes' (fail) vs 'do not proceed' (pass)",
     (F_34T, "40eebde5", 11, "op"), (F_34, "b47dbb44", 15, "op"), "low", "opposite instructions"),
    ("P13", "agent message, same content", "T48 ask for user ID and reservation ID: fail vs pass (paraphrase)",
     (F_48, "7f5cbcd7", 2, "op"), (F_48, "c890f90b", 2, "op"), "high", "same request, pass also asks for a reason"),
    ("P14", "agent message, contradictory", "T48 'cancelled, full refund' (fail) vs 'cannot cancel' (pass)",
     (F_48, "7f5cbcd7", 8, "op"), (F_48, "c890f90b", 6, "op"), "low", "opposite outcomes"),
    ("P15", "agent message, different number", "T3 'allowed 6 checked suitcases' (fail) vs 'allowed 4' (pass)",
     (F_3F, "5973decc", 4, "op"), (F_3P, "b4010f2d", 6, "op"), "low", "different count is a different answer"),
    ("P16", "agent message, different content", "T48 farewell (fail) vs transfer notice (pass)",
     (F_48, "7f5cbcd7", 12, "op"), (F_48, "c890f90b", 10, "op"), "low", "different act"),
]

_graphs: dict[tuple[str, str], dict] = {}


def _graph(file: str, prefix: str) -> dict:
    if (file, prefix) not in _graphs:
        _graphs[(file, prefix)] = build_step_graph(*load_simulation(str(REPO / file), prefix), source_file=file)
    return _graphs[(file, prefix)]


def _last_successful_call(file: str, prefix: str, tool: str) -> int:
    g = _graph(file, prefix)
    idx = [n["raw_message_indices"][0] for n in g["nodes"] if n.get("kind") == "tool_call"
           and n["tool_call"]["name"] == tool and not n["observation"]["error"]]
    if not idx:
        raise ValueError(f"{prefix}: no successful {tool}")
    return idx[-1]


def resolve(spec) -> tuple[str, dict]:
    file, prefix, idx, field = spec
    if isinstance(prefix, str) and prefix.startswith("pass:last:"):     # first passing run with a successful call
        tool = prefix.split(":", 2)[2]
        data = json.load(open(REPO / file))
        for s in data["simulations"]:
            if s["task_id"] == "25" and (s.get("reward_info") or {}).get("reward") == 1.0:
                prefix = s["id"][:8]
                idx = f"last:{tool}"
                break
    if isinstance(idx, str) and idx.startswith("last:"):
        idx = _last_successful_call(file, prefix, idx.split(":", 1)[1])
    g = _graph(file, prefix)
    node = next(n for n in g["nodes"] if idx in n["raw_message_indices"])
    text = node["op_text"] if field == "op" else node["result_text"]
    return text, {"file": file, "simulation": prefix, "raw_message_index": idx, "node": node["id"], "field": field}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(REPO / "gibs/examples/task48_pair"))
    ap.add_argument("--cpu-check", type=int, default=6, help="re-score the first N pairs on CPU for comparison")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for pid, cat, desc, sa, sb, expect, why in PAIRS:
        a, src_a = resolve(sa)
        b, src_b = resolve(sb)
        rows.append({"id": pid, "category": cat, "description": desc, "expectation": expect, "rationale": why,
                     "a_failed_run": src_a, "b_passing_run": src_b, "a_text": a, "b_text": b})

    t0 = time.time()
    model = DebertaEntailment(encoding="code_sep_string", overlength="truncate")   # author-code length handling
    load_s = time.time() - t0
    pair_model = model.with_encoding("pair")    # same weights; tokenizer pair encoding instead of the CODE string

    for r in rows:
        r["tokens_code_sep"] = model.token_length(r["a_text"], r["b_text"])
        r["tokens_dropped_a_to_b"] = max(0, r["tokens_code_sep"] - model.max_length)
        r["tokens_dropped_b_to_a"] = max(0, model.token_length(r["b_text"], r["a_text"]) - model.max_length)
        r["truncated"] = bool(r["tokens_dropped_a_to_b"] or r["tokens_dropped_b_to_a"])
        r["tokens_pair"] = pair_model.token_length(r["a_text"], r["b_text"])
        ids_code = model.encode([(r["a_text"], r["b_text"])], pad=False)["input_ids"][0]
        ids_pair = pair_model.encode([(r["a_text"], r["b_text"])], pad=False)["input_ids"][0]
        r["identical_token_ids"] = list(ids_code) == list(ids_pair)

    t1 = time.time()
    fwd = model.entail_batch([(r["a_text"], r["b_text"]) for r in rows])
    bwd = model.entail_batch([(r["b_text"], r["a_text"]) for r in rows])
    score_s = time.time() - t1
    fwd_pair = pair_model.entail_batch([(r["a_text"], r["b_text"]) for r in rows])
    bwd_pair = pair_model.entail_batch([(r["b_text"], r["a_text"]) for r in rows])
    for r, f, b, fp, bp in zip(rows, fwd, bwd, fwd_pair, bwd_pair):
        mx = max(f, b)
        r.update({"p_a_entails_b": f, "p_b_entails_a": b,
                  "sim_max_bidirectional": mx, "sim_one_way": f,
                  "match_max_bidirectional": mx >= TAU, "match_one_way": f >= TAU,
                  "pair_encoding_max_bidirectional": max(fp, bp),
                  "abs_diff_encodings": abs(max(fp, bp) - mx)})
        want = r["expectation"] == "high"
        r["as_expected_max_bidirectional"] = r["match_max_bidirectional"] == want
        r["as_expected_one_way"] = r["match_one_way"] == want

    cpu_rows = []
    if args.cpu_check and model.device != "cpu":
        cpu = DebertaEntailment(encoding="code_sep_string", device="cpu", cache_dir=None, overlength="truncate")
        sub = rows[: args.cpu_check]
        cf = cpu.entail_batch([(r["a_text"], r["b_text"]) for r in sub])
        cb = cpu.entail_batch([(r["b_text"], r["a_text"]) for r in sub])
        cpu_rows = [{"id": r["id"], "mps_max": r["sim_max_bidirectional"], "cpu_max": max(f, b),
                     "abs_diff": abs(r["sim_max_bidirectional"] - max(f, b))} for r, f, b in zip(sub, cf, cb)]

    summary = {
        "model": model.describe(), "tau": TAU, "n_pairs": len(rows),
        "load_seconds": round(load_s, 1), "scoring_seconds_both_directions_uncached": round(score_s, 1),
        "as_expected_max_bidirectional": sum(r["as_expected_max_bidirectional"] for r in rows),
        "as_expected_one_way": sum(r["as_expected_one_way"] for r in rows),
        "max_tokens": max(r["tokens_code_sep"] for r in rows),
        "truncated_pairs": [r["id"] for r in rows if r["truncated"]],
        "as_expected_max_bidirectional_untruncated_only":
            f'{sum(r["as_expected_max_bidirectional"] for r in rows if not r["truncated"])}/'
            f'{sum(not r["truncated"] for r in rows)}',
        "encodings_identical_token_ids": sum(r["identical_token_ids"] for r in rows),
        "max_abs_diff_between_encodings": max(r["abs_diff_encodings"] for r in rows),
        "cpu_vs_device_check": cpu_rows,
    }
    (out_dir / "nli_probe.json").write_text(json.dumps({"summary": summary, "pairs": rows}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    for r in rows:
        print(f"{r['id']} {r['category']:<36} exp={r['expectation']:<4} a=>b={r['p_a_entails_b']:.3f} "
              f"b=>a={r['p_b_entails_a']:.3f} max={r['sim_max_bidirectional']:.3f} "
              f"{'OK ' if r['as_expected_max_bidirectional'] else 'MISS'} | one-way "
              f"{'OK ' if r['as_expected_one_way'] else 'MISS'} | tok={r['tokens_code_sep']}"
              f"{' TRUNCATED' if r['truncated'] else ''}")


if __name__ == "__main__":
    main()
