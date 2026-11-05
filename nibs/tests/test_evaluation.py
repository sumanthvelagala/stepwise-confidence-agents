"""Metric oracles and data-integrity tests; no APIs, downloads or training."""
import csv
import itertools
import json
import tempfile
import unittest
from pathlib import Path

from nibs.evaluation_metrics import (agreement, binary_metrics, mean, random_binary_metrics,
                                     random_target_rank, target_rank)
from nibs.run_evaluation import (REVIEW_COLUMNS, analyze, deduplicate, import_human, load_runs,
                                main, review_export, score_queries, write_csv)


class MetricTests(unittest.TestCase):
    def test_auroc_direction_ties_and_missing_class(self):
        rows = [{"label": "correct", "confidence": 1},
                {"label": "incorrect", "confidence": 0},
                {"label": "unverified", "confidence": .5}]
        self.assertEqual(binary_metrics(rows)["auroc_error_positive"], 1)
        self.assertEqual(binary_metrics([{**r, "confidence": .5} for r in rows])["auroc_error_positive"], .5)
        self.assertIsNone(binary_metrics(rows[:1])["auroc_error_positive"])
        self.assertEqual(binary_metrics(rows)["average_precision_error_positive"], 1)

    def test_grouped_ap_is_not_optimistic_about_ties(self):
        rows = [{"label": x, "confidence": 0} for x in ["correct", "incorrect", "correct"]]
        self.assertAlmostEqual(binary_metrics(rows)["average_precision_error_positive"], 1 / 3)

    def test_tie_localization_matches_all_permutations(self):
        scores = [0, .5, .5, .5, 1]
        m = target_rank(scores, 2)
        ranks = [list(p).index(2) + 2 for p in itertools.permutations([1, 2, 3])]
        self.assertEqual((m["rank_min"], m["rank_max"]), (2, 4))
        self.assertEqual(m["top1"], 0)
        self.assertAlmostEqual(m["top3"], mean(r <= 3 for r in ranks))
        self.assertAlmostEqual(m["reciprocal_rank"], mean(1 / r for r in ranks))

    def test_random_baseline_matches_exhaustive_orders(self):
        for n_correct, n_errors in [(2, 1), (1, 2), (2, 2), (0, 2)]:
            labels = ["correct"] * n_correct + ["incorrect"] * n_errors
            aps, aucs = [], []
            for perm in itertools.permutations(range(len(labels))):
                rows = [{"label": labels[i], "confidence": rank / len(labels)} for rank, i in enumerate(perm)]
                result = binary_metrics(rows)
                aps.append(result["average_precision_error_positive"])
                if result["auroc_error_positive"] is not None:
                    aucs.append(result["auroc_error_positive"])
            expected = random_binary_metrics(n_correct, n_errors)
            self.assertAlmostEqual(expected["average_precision_error_positive"], mean(aps))
            if aucs:
                self.assertAlmostEqual(expected["auroc_error_positive"], mean(aucs))
        random_rank = random_target_rank(5)
        self.assertEqual(random_rank["top1"], .2)
        self.assertEqual(random_rank["top3"], .6)

    def test_kappa_and_degenerate_agreement(self):
        pairs = [("correct", "correct"), ("correct", "incorrect"),
                 ("incorrect", "correct"), ("incorrect", "incorrect")]
        self.assertEqual(agreement(pairs)["cohens_kappa"], 0)
        self.assertIsNone(agreement([("correct", "correct")])["cohens_kappa"])

    def test_unverified_steps_compete_in_localization(self):
        rows = [{"task_id": "25", "run_id": "r", "step_index": i, "event_id": f"s{i}",
                 "success": False, "kind": "tool_call", "label": label, "confidence": score}
                for i, (label, score) in enumerate([("unverified", 0), ("incorrect", .5), ("correct", 1)])]
        results, _ = analyze(rows)
        m = results["all_agent_steps"]["tasks"]["25"]["methods"]["nibs"]
        self.assertEqual(m["auroc_error_positive"], 1)
        self.assertEqual(m["localization"]["top1"], 0)
        self.assertEqual(m["localization"]["top3"], 1)

    def test_empty_tool_scope_keeps_failed_run_in_denominator(self):
        row = {"task_id": "25", "run_id": "r", "step_index": 0, "event_id": "s0",
               "success": False, "kind": "message", "label": "unverified", "confidence": 1}
        results, _ = analyze([row])
        tools = results["tool_calls"]["tasks"]["25"]
        self.assertEqual(tools["n_failed_queries"], 1)
        self.assertEqual(tools["failed_queries_without_labelled_error"], 1)
        self.assertEqual(tools["failed_queries_without_candidates"], 1)

    def test_high_error_score_can_rank_well_but_miss_cutoff(self):
        rows = [{"label": "correct", "confidence": 1}, {"label": "incorrect", "confidence": .904},
                {"label": "incorrect", "confidence": .5}]
        metrics = binary_metrics(rows)
        self.assertEqual(metrics["auroc_error_positive"], 1)
        self.assertEqual(metrics["error_detection_at_0.5"], 0)


def raw_run(sid, correct=True):
    rid = "ABC123" if correct else "BAD123"
    return {"id": sid, "task_id": "25", "trial": 0,
            "reward_info": {"reward": 1.0 if correct else 0.0},
            "messages": [{"role": "user", "content": f"Request variant {sid}; cancel ABC123."},
                         {"role": "assistant", "content": "I will cancel it.",
                          "tool_calls": [{"id": "call1", "name": "cancel_reservation", "arguments": {"reservation_id": rid}}]},
                         {"role": "tool", "id": "call1", "content": json.dumps({"reservation_id": rid, "status": "cancelled"})},
                         {"role": "assistant", "content": "Done."}]}


def write_fixture(root, n_success=4):
    task = {"id": "25", "user_scenario": {"instructions": "Cancel ABC123"},
            "evaluation_criteria": {"actions": [{"name": "cancel_reservation", "arguments": {"reservation_id": "ABC123"}}]}}
    data = {"info": {"agent_info": {"llm": "groq/openai/gpt-oss-20b", "llm_args": {"temperature": 0.0, "secret": "NEVER_EXPORT_PROVIDER_METADATA"}},
                     "user_info": {"llm": "groq/openai/gpt-oss-20b", "llm_args": {"temperature": 0.0}},
                     "git_commit": "test", "environment_info": {"domain_name": "airline", "policy": "Test policy"}},
            "tasks": [task], "simulations": [raw_run(f"success{i}") for i in range(n_success)] + [raw_run("failed", False)]}
    p = root / "fixture/results.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(data))
    return data, p


class PipelineTests(unittest.TestCase):
    def test_post_leave_one_out_reference_minimum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, 3)
            loaded, _, _, _ = load_runs(root, ["25"])
            reps, _ = deduplicate(loaded)
            rows, eligible, skipped, _ = score_queries(reps, 3)
            self.assertEqual(len(eligible), 1)
            self.assertFalse(eligible[0]["success"])
            self.assertEqual(len(skipped), 3)
            self.assertTrue(all(r["n_references"] == 3 for r in rows))

    def test_duplicate_query_class_excluded_and_conflicts_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, p = write_fixture(root)
            duplicate = json.loads(json.dumps(data["simulations"][0]))
            duplicate["id"] = "copy"
            data["simulations"].append(duplicate)
            p.write_text(json.dumps(data))
            loaded, _, _, _ = load_runs(root, ["25"])
            reps, counts = deduplicate(loaded)
            self.assertEqual(counts["25"]["runs"], 6)
            self.assertEqual(len(reps), 5)
            _, eligible, _, refs = score_queries(reps, 3)
            for query in eligible:
                self.assertNotIn(query["id"], refs[query["id"]])
                self.assertFalse(set(query["duplicates"]) & set(refs[query["id"]]))
            loaded[-1]["success"] = not loaded[-1]["success"]
            with self.assertRaises(ValueError):
                deduplicate(loaded)

    def test_full_run_blind_review_and_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root, out = Path(directory) / "input", Path(directory) / "output"
            write_fixture(root)
            main(["--results-root", str(root), "--output", str(out), "--tasks", "25"])
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary["dataset"]["25"]["scored_queries"], 5)
            self.assertEqual(summary["n_steps"], 10)
            text = "\n".join(p.read_text() for p in out.rglob("*") if p.is_file())
            self.assertNotIn("NEVER_EXPORT_PROVIDER_METADATA", text)
            with (out / "review/labels.csv").open(newline="") as f:
                review = list(csv.DictReader(f))
            self.assertEqual(len(review), 2)
            self.assertNotIn("confidence", review[0])
            self.assertNotIn("label_reason", review[0])
            # A partial sheet cannot produce human performance claims.
            review[0]["reviewer_1"] = review[0]["reviewer_2"] = "incorrect"
            write_csv(out / "review/labels.csv", review, REVIEW_COLUMNS)
            main(["--results-root", str(root), "--output", str(out), "--tasks", "25", "--human-labels", str(out / "review/labels.csv")])
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary["human_review"]["n_complete_runs"], 0)
            # Rerunning preserved the actual entries.
            with (out / "review/labels.csv").open(newline="") as f:
                self.assertEqual(next(csv.DictReader(f))["reviewer_1"], "incorrect")
            review[1]["reviewer_1"] = review[1]["reviewer_2"] = "correct"
            write_csv(out / "review/labels.csv", review, REVIEW_COLUMNS)
            main(["--results-root", str(root), "--output", str(out), "--tasks", "25", "--human-labels", str(out / "review/labels.csv")])
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary["human_review"]["n_complete_runs"], 1)
            self.assertEqual(summary["human_review"]["agreement"]["cohens_kappa"], 1)
            # Edited step identities must fail, not be silently reattached.
            review[0]["event_id"] = "wrong"
            write_csv(out / "review/labels.csv", review, REVIEW_COLUMNS)
            loaded, _, _, _ = load_runs(root, ["25"])
            reps, _ = deduplicate(loaded)
            rows, eligible, _, _ = score_queries(reps, 3)
            expected = [{**r, "context_file": f"review/context/task{r['task_id']}_{r['run_id']}.json"}
                        for r in rows if not r["success"]]
            with self.assertRaises(ValueError):
                import_human(out / "review/labels.csv", expected, rows)


if __name__ == "__main__":
    unittest.main()
