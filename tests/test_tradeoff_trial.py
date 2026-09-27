import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tradeoff_trial as trial
from ladder_extra import adjust_rows


ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "runs/2026-09-26-general-grok16/candidates.csv"
APPROVED_SHA256 = "e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22"


def row(name, score, cost, **changes):
    base = dict(identity=name, score=str(score), cost_per_task=str(cost),
                benchmark="General", benchmark_version="v1", cost_basis="api",
                provider="Example", privacy="", notes="GRADE-A measured",
                checked_date="2026-09-26", evidence_url="https://example.org")
    return dict(base, **changes)


def analyze(*rows, eps=2):
    return trial.analyze(adjust_rows(list(rows)), min_score=0, eps_score=eps)


class GeometryTests(unittest.TestCase):
    def test_both_axes_and_one_strict_required_with_real_witness(self):
        result = analyze(row("cheap", 10, 1), row("upgrade", 12, 2),
                         row("expensive inferior", 11, 3), row("same score costly", 12, 4),
                         row("same cost weaker", 9, 1))
        self.assertEqual([r["identity"] for r in result["retained"]], ["cheap", "upgrade"])
        witnesses = {r["identity"]: r["witness"] for r in result["dominated"]}
        self.assertEqual(witnesses["expensive inferior"], "upgrade")
        self.assertEqual(witnesses["same score costly"], "upgrade")
        self.assertEqual(witnesses["same cost weaker"], "cheap")
        self.assertEqual(result["counts"], {"input": 5, "potential_tradeoffs": 2, "dominated": 3})

    def test_identical_score_and_cost_routes_are_equivalent_not_lost(self):
        result = analyze(row("route A", 10, 1), row("route B", 10, 1), row("expensive", 9, 2))
        self.assertEqual({r["identity"] for r in result["retained"]}, {"route A", "route B"})
        self.assertEqual(result["dominated"][0]["witness"], "route A")
        self.assertIsNone(result["retained"][0]["upgrade"])
        self.assertIsNone(result["retained"][1]["upgrade"])

    def test_same_price_peers_share_the_same_strictly_cheaper_upgrade_baseline(self):
        result = analyze(row("cheap A", 10, 1), row("cheap B", 10, 1),
                         row("middle A", 12, 2), row("middle B", 12, 2),
                         row("top", 15, 3))
        got = {r["identity"]: r["upgrade"] for r in result["retained"]}
        self.assertIsNone(got["cheap A"])
        self.assertIsNone(got["cheap B"])
        self.assertEqual(got["middle A"], got["middle B"])
        self.assertIn(got["middle B"]["cheaper_identity"], {"cheap A", "cheap B"})
        self.assertEqual(got["middle B"]["delta_score"], 2)
        self.assertEqual(got["middle B"]["cost_multiple"], 2)
        self.assertEqual(got["middle B"]["delta_cost_adj"], 1)
        self.assertFalse(got["middle B"]["within_noise"])
        self.assertIn(got["top"]["cheaper_identity"], {"middle A", "middle B"})
        self.assertEqual(got["top"]["cost_multiple"], 1.5)

    def test_no_chain_deletion_and_exact_noise_boundary(self):
        result = analyze(row("bottom", 10, 1), row("small", 11.9, 2),
                         row("boundary", 13.9, 4), row("top", 14, 20))
        self.assertEqual([r["identity"] for r in result["retained"]],
                         ["bottom", "small", "boundary", "top"])
        self.assertLess(result["retained"][0]["cost_adj"], result["retained"][-1]["cost_adj"])
        upgrades = {r["identity"]: r["upgrade"] for r in result["retained"]}
        self.assertEqual(upgrades["small"]["cheaper_identity"], "bottom")
        self.assertAlmostEqual(upgrades["small"]["delta_score"], 1.9)
        self.assertTrue(upgrades["small"]["within_noise"])
        self.assertEqual(upgrades["boundary"]["cost_multiple"], 2)
        self.assertAlmostEqual(upgrades["boundary"]["delta_score"], 2)
        self.assertFalse(upgrades["boundary"]["within_noise"])
        self.assertAlmostEqual(upgrades["top"]["delta_cost_adj"], 16)
        self.assertEqual(upgrades["top"]["cheaper_identity"], "boundary")

    def test_scenario_adjustment_and_unadjusted_original_costs(self):
        result = analyze(row("GPT-X", 12, 9), row("Grok-4.7", 14, 16),
                         row("Muse Contributor", 16, 2, pricing_plan="Contributor"),
                         row("Other", 10, 3))
        rows = {r["identity"]: r for r in result["retained"]}
        self.assertEqual(rows["GPT-X"]["cost_adj"], .5)
        self.assertEqual(rows["GPT-X"]["cost_orig"], 9)
        self.assertEqual(rows["Grok-4.7"]["cost_adj"], 1)
        self.assertEqual(rows["Muse Contributor"]["factor"], 1)
        self.assertEqual(rows["Muse Contributor"]["cost_orig"], 2)
        self.assertEqual(rows["Muse Contributor"]["upgrade"]["cost_multiple"], 2)
        self.assertIn("Other", {r["identity"] for r in result["dominated"]})

    def test_reject_mixed_source_group_even_if_one_row_dominated(self):
        for field in ("benchmark", "benchmark_version", "cost_basis"):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "single benchmark"):
                analyze(row("a", 10, 1), row("b", 9, 3, **{field: "different"}))

    def test_claude_is_comparison_only_even_if_highest_score(self):
        result = analyze(row("Claude Opus", 30, 5), row("GPT-X", 10, 18))
        self.assertFalse(result["retained"][0]["comparison_only"])
        self.assertTrue(result["retained"][1]["comparison_only"])


class RenderingAndCliTests(unittest.TestCase):
    def test_html_is_self_contained_escaped_and_collapses_noise_not_rows(self):
        result = analyze(row("base <script>alert(1)</script>", 10, 1,
                             notes='GRADE-B <img src=x onerror=1>', evidence_url='javascript:evil()'),
                         row("little", 11, 2), row("big", 14, 4), row("worse", 9, 5))
        html = trial.render_html(result, "historical.csv")
        self.assertIn("<!doctype html>", html.lower())
        self.assertIn("<style>", html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("<link", html.lower())
        self.assertNotIn("javascript:evil()\"", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;img", html)
        self.assertIn("<details", html)
        self.assertIn("little", html)
        self.assertIn("worse", html)
        self.assertIn("Claude", html)
        self.assertIn("完整保留", html)

    def test_custom_factors_are_labeled_not_hardcoded_in_reports(self):
        result = trial.analyze(adjust_rows([row("GPT-X", 10, 6), row("Grok 4.7", 12, 8)],
                                           factor=3, grok_factor=4), min_score=0, eps_score=2)
        result["policy"].update(factor=3, grok_factor=4)
        self.assertIn("GPT ×3", trial.render_html(result, "source.csv"))
        self.assertIn("Grok ×4", trial.render_markdown(result, "source.csv"))

    def test_cli_requires_reason_and_does_not_overwrite_existing_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.csv"
            shutil.copyfile(APPROVED, source)
            out = Path(tmp) / "out"
            cli = [sys.executable, str(ROOT / "scripts/tradeoff_trial.py"),
                   "--input", str(source), "--output-dir", str(out), "--min-score", "0"]
            missing = subprocess.run(cli, text=True, capture_output=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse(out.exists())
            run = subprocess.run(cli + ["--min-score-reason", "Full historical illustration"],
                                 text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(set(p.name for p in out.iterdir()),
                             {"result.json", "report.md", "report.html", "README.md"})
            result = json.loads((out / "result.json").read_text())
            self.assertEqual(result["counts"]["input"], 155)
            self.assertEqual(result["source_sha256"], APPROVED_SHA256)
            self.assertIn(APPROVED_SHA256, (out / "README.md").read_text())
            repeat = subprocess.run(cli + ["--min-score-reason", "Full historical illustration"],
                                    text=True, capture_output=True)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertIn("exists", repeat.stderr)

    def test_cli_rejects_different_bytes_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.csv"
            source.write_bytes(APPROVED.read_bytes() + b"\n")
            out = Path(tmp) / "report"
            run = subprocess.run([sys.executable, str(ROOT / "scripts/tradeoff_trial.py"),
                                  "--input", str(source), "--output-dir", str(out),
                                  "--min-score", "0", "--min-score-reason", "historical full set"],
                                 text=True, capture_output=True)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertIn("snapshot", run.stderr.lower())
            self.assertFalse(out.exists())


class ApprovedSnapshotRegressionTests(unittest.TestCase):
    def test_fixed_source_coverage_geometry_witnesses_and_noise_annotations(self):
        self.assertEqual(hashlib.sha256(APPROVED.read_bytes()).hexdigest(), APPROVED_SHA256)
        with APPROVED.open(newline="", encoding="utf-8") as f:
            raw = list(csv.DictReader(f))
        result = trial.analyze(adjust_rows(raw), min_score=0, eps_score=2)
        self.assertEqual(result["counts"],
                         {"input": 155, "potential_tradeoffs": 21, "dominated": 134})
        retained, dominated = result["retained"], result["dominated"]
        self.assertEqual({r["identity"] for r in raw},
                         {r["identity"] for r in retained + dominated})
        self.assertEqual(len(retained) + len(dominated), 155)
        self.assertEqual(sum(bool(r["upgrade"] and r["upgrade"]["within_noise"])
                             for r in retained), 13)
        for r in dominated:
            witness = next(w for w in retained if w["identity"] == r["witness"])
            self.assertGreaterEqual(witness["score"], r["score"])
            self.assertLessEqual(witness["cost_adj"], r["cost_adj"])
            self.assertTrue(witness["score"] > r["score"] or
                            witness["cost_adj"] < r["cost_adj"])
        for r in retained:
            self.assertFalse(any(w["score"] >= r["score"] and
                                 w["cost_adj"] <= r["cost_adj"] and
                                 (w["score"] > r["score"] or w["cost_adj"] < r["cost_adj"])
                                 for w in retained if w is not r))
            cheaper = [w for w in retained if w["cost_adj"] < r["cost_adj"]]
            upgrade = r["upgrade"]
            if not cheaper:
                self.assertIsNone(upgrade)
            else:
                baseline = next(w for w in retained if w["identity"] == upgrade["cheaper_identity"])
                self.assertEqual(baseline["cost_adj"], max(w["cost_adj"] for w in cheaper))
                self.assertTrue(math.isclose(upgrade["delta_score"], r["score"] - baseline["score"]))
                self.assertTrue(math.isclose(upgrade["cost_multiple"], r["cost_adj"] / baseline["cost_adj"]))
                self.assertTrue(math.isclose(upgrade["delta_cost_adj"],
                                             r["cost_adj"] - baseline["cost_adj"]))
                self.assertEqual(upgrade["within_noise"], upgrade["delta_score"] < 2)


if __name__ == "__main__":
    unittest.main()
