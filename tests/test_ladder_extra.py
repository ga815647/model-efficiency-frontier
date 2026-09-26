import csv
import contextlib
import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ladder_extra import adjust_rows
import ladder_extra as extra
import ladder


class AdjustmentTests(unittest.TestCase):
    def test_adjustment_keeps_original_and_other_models(self):
        rows = [dict(identity="GPT-X", score="40", cost_per_task="2"),
                dict(identity="Other", score="40", cost_per_task="2")]
        got = adjust_rows(rows)
        self.assertAlmostEqual(got[0]["_cost"], 2 / 18)
        self.assertEqual(got[1]["_cost"], 2)
        self.assertEqual(got[0]["_cost_orig"], 2)
        self.assertEqual(got[0]["_cp_orig"], 20)
        self.assertEqual(rows[0]["cost_per_task"], "2")
        self.assertNotIn("_score", rows[0])

    def test_nonfinite_factor_rejected(self):
        for factor in (0, -1, float("nan"), float("inf")):
            with self.subTest(factor=factor), self.assertRaises(ValueError):
                adjust_rows([], factor)

    def test_invalid_paid_numeric_values_are_not_mistaken_for_free(self):
        for field, value in (("cost_per_task", "nan"),
                             ("cost_per_task", "inf"),
                             ("cost_per_task", "0"),
                             ("cost_per_task", "-1"),
                             ("cost_per_task", "oops"),
                             ("score", "nan"), ("score", "inf"),
                             ("score", "oops")):
            with self.subTest(field=field, value=value):
                row = dict(identity="GPT-X", score="40", cost_per_task="2")
                row[field] = value
                with self.assertRaises(ValueError):
                    adjust_rows([row])

    def test_only_explicit_free_skips_invalid_values(self):
        free = dict(identity="Quota", is_free=" YES ", score="bad", cost_per_task="0")
        self.assertEqual(adjust_rows([free]), [])
        with self.assertRaises(ValueError):
            adjust_rows([dict(free, is_free="false")])

    def test_paid_row_requires_an_identity(self):
        for row in (dict(score="40", cost_per_task="2"),
                    dict(identity=None, score="40", cost_per_task="2"),
                    dict(identity="", score="40", cost_per_task="2")):
            with self.subTest(row=row), self.assertRaises(ValueError):
                adjust_rows([row])

    def test_extreme_arithmetic_rejected_before_frozen_math(self):
        cases = (("1e-308", "1e-308", "1e308"),  # adjusted cost underflows
                 ("1e308", "1e308", "1e-308"),  # adjusted cost overflows
                 ("1", "1e308", "2"),           # adjusted CP overflows
                 ("1e-308", "1e308", "1"))     # original CP overflows
        for cost, score, factor in cases:
            with self.subTest(cost=cost, score=score, factor=factor):
                with self.assertRaises(ValueError):
                    adjust_rows([dict(identity="GPT-X", score=score,
                                      cost_per_task=cost)], float(factor))

    def test_real_snapshot_family_factors_keep_original_cost(self):
        path = Path(__file__).resolve().parents[1] / "runs/2026-09-24-general-v5/candidates.csv"
        rows = extra.load_rows(path)
        adjusted = adjust_rows(rows)
        self.assertGreater(len(adjusted), 20)
        self.assertTrue(any("Contributor" in r["identity"] for r in adjusted))
        for r in adjusted:
            with self.subTest(identity=r["identity"]):
                if r["identity"].startswith("GPT-"):
                    self.assertAlmostEqual(r["_score"] / r["_cost"],
                                           r["_cp_orig"] * 18, delta=1e-6)
                elif r["identity"].lower().startswith("grok "):
                    self.assertAlmostEqual(r["_score"] / r["_cost"],
                                           r["_cp_orig"] * 16, delta=1e-6)
                else:
                    self.assertEqual(r["_cost"], r["_cost_orig"])

    def test_mixed_family_adjustment_uses_one_factor_and_exempts_contributor(self):
        rows = [candidate("GPT-6 Sol", 36, 18), candidate("gRoK-4.7 high", 32, 16),
                candidate("Grok 4.7 xhigh", 48, 16), candidate("Grokish", 20, 16),
                candidate("Pre-Grok 4.7", 20, 16), candidate("Other", 20, 16),
                dict(candidate("Grok 4.7 Contributor", 20, 16), pricing_plan="Contributor"),
                dict(candidate("GPT-6 Contributor", 20, 18), pricing_plan="Contributor")]
        got = adjust_rows(rows)
        self.assertEqual([r["_cost"] for r in got],
                         [1, 1, 1, 16, 16, 16, 16, 18])
        self.assertEqual([r["_factor"] for r in got], [18, 16, 16, 1, 1, 1, 1, 1])
        self.assertEqual(got[1]["_cp_orig"], 2)
        self.assertEqual(got[1]["_score"] / got[1]["_cost"], 32)
        self.assertEqual(rows[1]["cost_per_task"], "16")

    def test_custom_grok_factor_and_gpt_override_do_not_compound(self):
        rows = [candidate("GPT-Grok", 36, 36), candidate("Grok-4.7", 36, 36)]
        got = adjust_rows(rows, factor=3, grok_factor=4)
        self.assertEqual([r["_cost"] for r in got], [12, 9])
        self.assertEqual([r["_factor"] for r in got], [3, 4])

    def test_invalid_grok_factor_rejected_by_library(self):
        for factor in (0, -1, float("nan"), float("inf"), float("-inf")):
            with self.subTest(factor=factor), self.assertRaises(ValueError):
                adjust_rows([], grok_factor=factor)


def candidate(identity, score, cost, benchmark="General", version="v1", basis="api"):
    return dict(identity=identity, score=str(score), cost_per_task=str(cost),
                benchmark=benchmark, benchmark_version=version, cost_basis=basis,
                 privacy="other", provider="Example", notes="GRADE-B ratio")


def write_candidates(path, rows):
    columns = list(candidate("sample", 1, 1)) + ["checked_date", "evidence_url", "pricing_plan"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_cli(*args):
    script = Path(__file__).resolve().parents[1] / "scripts/ladder_extra.py"
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          text=True, capture_output=True)


class InputAndComputationTests(unittest.TestCase):
    def test_csv_requires_expected_columns_even_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            path.write_text("identity,score,cost_per_task\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                extra.load_rows(path)

    def test_csv_load_keeps_raw_values_for_adjustment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            row = candidate("GPT-X", 40, 2)
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=row)
                writer.writeheader()
                writer.writerow(row)
            self.assertEqual(extra.load_rows(path), [row])

    def test_short_csv_row_reports_input_error_without_overwriting_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("Complete", 45, 2)])
            with source.open("a", encoding="utf-8") as f:
                f.write("Short,40,2\n")
            output = source.parent / "ladder-extra.md"
            output.write_text("previous result\n", encoding="utf-8")

            result = run_cli("--input", source, "--min-score", "0")

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("row 3", result.stderr)
            self.assertIn("benchmark", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous result\n")

    def test_blank_grouping_value_reports_row_and_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("Incomplete", 40, 2, benchmark=" ")])

            result = run_cli("--input", source, "--min-score", "0")

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("row 2", result.stderr)
            self.assertIn("benchmark", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse((source.parent / "ladder-extra.md").exists())

    def test_required_paid_row_values_report_numbered_errors(self):
        for column in ("identity", "score", "cost_per_task", "benchmark",
                       "benchmark_version", "cost_basis"):
            with self.subTest(column=column), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "input.csv"
                row = candidate("Incomplete", 40, 2)
                row[column] = " "
                write_candidates(source, [row])
                result = run_cli("--input", source, "--min-score", "0")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("row 2", result.stderr)
                self.assertIn(column, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((source.parent / "ladder-extra.md").exists())

    def test_all_explicitly_free_rows_with_blank_scores_and_zero_cost_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            fields = list(candidate("sample", 1, 1)) + ["is_free"]
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerow(dict(candidate("Quota", "", 0, benchmark=""), is_free="true"))
                writer.writerow(dict(candidate("", "", 0, basis=""), is_free=" YES "))

            result = run_cli("--input", source, "--min-score", "0")

            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text(encoding="utf-8")
            self.assertIn("_無付費候選。_", text)
            self.assertNotIn("## 階梯表：", text)

    def test_explicitly_nonfree_missing_score_keeps_row_number_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            fields = list(candidate("sample", 1, 1)) + ["is_free"]
            with source.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerow(dict(candidate("Paid", "", 2), is_free="false"))

            result = run_cli("--input", source, "--min-score", "0")

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("row 2: missing score", result.stderr)
            self.assertFalse((source.parent / "ladder-extra.md").exists())

    def test_missing_optional_checked_date_and_blank_privacy_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [dict(candidate("GPT-One", 40, 2), privacy="")])
            # DictReader yields None for a short optional trailing field.
            with source.open("a", encoding="utf-8") as f:
                f.write("GPT-Two,35,1,General,v1,api,,Example,GRADE-B ratio\n")

            result = run_cli("--input", source, "--min-score", "0")

            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text(encoding="utf-8")
            self.assertIn("來源快照日期（checked_date）：未提供", text)
            self.assertIn("GPT-One", text)
            self.assertIn("GPT-Two", text)

    def test_cli_validates_all_numeric_options_and_guards_original(self):
        base = ["--input", "snapshot.csv", "--min-score", "0"]
        got = extra.parse_args(base)
        self.assertEqual((got.factor, got.prefix, got.subscription_total), (18, "GPT-", 79))
        self.assertEqual(got.grok_factor, 16)
        for flag, value in (("--factor", "0"), ("--factor", "nan"),
                            ("--grok-factor", "0"), ("--grok-factor", "nan"),
                            ("--grok-factor", "inf"), ("--grok-factor", "-1"),
                            ("--min-score", "inf"), ("--max-cost", "0"),
                            ("--eps-score", "nan"), ("--eps-cp", "inf"),
                            ("--monthly-tasks", "-1"),
                            ("--subscription-total", "0"),
                            ("--prefix", ""), ("--output", "archive/ladder.md")):
            with self.subTest(flag=flag, value=value):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    extra.parse_args(base + [flag, value])
                self.assertEqual(raised.exception.code, 2)

    def test_adjusted_math_is_group_local_and_contributor_is_considered(self):
        rows = adjust_rows([candidate("Top", 50, 5),
                            candidate("GPT-Mid", 40, 4),
                            candidate("Muse Contributor", 39, 2.5),
                            candidate("Other version", 45, 1, version="v2"),
                            candidate("Other basis", 42, 1, basis="subscription-amortized")],
                           factor=2)
        groups = extra.compute_groups(rows, extra.parse_args(["--input", "x.csv", "--min-score", "0",
                                                              "--factor", "2"]))
        self.assertEqual(len(groups), 3)
        main = groups[("General", "v1", "api")]
        self.assertEqual([r["identity"] for r in main["final"]], ["Top", "GPT-Mid"])
        self.assertEqual(main["cuts"], {})
        self.assertEqual([r["identity"] for r, _ in main["excluded"]], ["Muse Contributor"])
        self.assertAlmostEqual(main["final"][1]["_cp"], 20)

    def test_copied_display_helpers_match_ladder_on_parity_fixtures(self):
        # Parity covers ordinary bands only; the extra-only dual-pinned
        # exception deliberately differs from the inherited ladder bug.
        rows = [dict(candidate(name, score, cost), _score=float(score),
                     _cost=float(cost), _cp=float(score) / float(cost))
                for name, score, cost in (("H", 50, 2), ("M", 49.5, 0.5),
                                          ("T", 49, 0.1), ("Far", 40, 1))]
        self.assertEqual(extra.keep_key(rows[0]), ladder.keep_key(rows[0]))
        self.assertEqual(extra.group_rows(rows), ladder.group_rows(rows))
        actual, cuts = extra.dedup_bands(rows, 2)
        expected, expected_cuts = ladder.dedup_bands(rows, 2)
        self.assertEqual([r["identity"] for r in actual], [r["identity"] for r in expected])
        self.assertEqual(cuts, expected_cuts)
        for identity in ("Claude Opus 5.5", "GPT-6 Sol", "Fable Test"):
            self.assertEqual(extra._is_claude(identity), ladder._is_claude(identity))
        for notes in ("GRADE-A observed", "GRADE-B derived", "unknown"):
            self.assertEqual(extra.grade_of({"notes": notes}), ladder.grade_of({"notes": notes}))

    def test_two_row_band_retains_both_pinned_extremes(self):
        top = {"identity": "Highest score", "_score": 50, "_cost": 10, "_cp": 5}
        peak = {"identity": "Highest CP", "_score": 49.5, "_cost": 1, "_cp": 49.5}
        final, cuts = extra.dedup_bands([peak, top], 2)
        self.assertEqual([row["identity"] for row in final], ["Highest score", "Highest CP"])
        self.assertEqual(cuts, {})


class DecisionTests(unittest.TestCase):
    def test_missing_usage_is_not_zero(self):
        from ladder_extra import api_comparison
        self.assertIn('N 未定', api_comparison(2, None, 79))
        self.assertIn('開外部API', api_comparison(2, 0, 79))
        self.assertIn('續訂閱', api_comparison(2, 40, 79))

    def test_finite_monthly_inputs_with_overflow_do_not_produce_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("Other", 40, 2)])
            result = run_cli("--input", source, "--min-score", "0",
                             "--monthly-tasks", "1e308")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("monthly", result.stderr.lower())
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse((source.parent / "ladder-extra.md").exists())

    def test_factor_override_labels_table_and_unrounded_cp_formula(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("GPT-One", 40, 2)])
            result = run_cli("--input", source, "--min-score", "0", "--factor", "3")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text(encoding="utf-8")
            self.assertIn("| Identity | 情境係數 | GRADE |", text)
            self.assertIn("| GPT-One | GPT ×3 |", text)
            self.assertIn("CP_orig、CP_adj 由原始未四捨五入的 Score 與 Cost_orig 計算，表中數字僅供顯示時取整", text)

    def test_contributor_exclusion_visible_beyond_top_five(self):
        rows = [candidate("GPT-Head", 50, 10), candidate("GPT-Mid", 40, 2)]
        rows += [candidate(f"Other-{n}", 39-n, 5) for n in range(7)]
        contributor = candidate("Muse Contributor", 30, 1)
        contributor["pricing_plan"] = "Contributor"
        rows.append(contributor)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, rows)
            unadjusted = run_cli("--input", source, "--min-score", "0", "--factor", "1")
            self.assertEqual(unadjusted.returncode, 0, unadjusted.stderr)
            self.assertIn("Muse Contributor（S=30, Cost_orig=$1.0000, CP_orig=30.00, CP_adj=30.00；GRADE B）：保留階梯",
                          (source.parent / "ladder-extra.md").read_text())
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text(encoding="utf-8")
            self.assertIn("## Contributor 狀態", text)
            self.assertIn("Muse Contributor", text)
            self.assertIn("CP_orig=30", text)
            self.assertIn("CP_adj=30", text)
            self.assertIn("CP_adj no new high", text)
            self.assertIn("CP_adj", text)
            self.assertNotIn("CP no new high", text)

    def test_grok_status_includes_excluded_high_and_xhigh_beyond_sample(self):
        rows = [candidate("GPT-Head", 60, 2)]
        rows += [candidate(f"Other-{n}", 55-n, 8) for n in range(7)]
        rows += [candidate("Grok 4.7 high", 30, 16),
                 candidate("Grok 4.7 xhigh", 29, 16)]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, rows)
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text()
            status = text.split("## Grok 狀態", 1)[1].split("### B-caveat", 1)[0]
            self.assertIn("Grok 4.7 high（S=30, Cost_orig=$16.0000, CP_orig=1.88, CP_adj=30.00", status)
            self.assertIn("Grok 4.7 xhigh（S=29, Cost_orig=$16.0000", status)
            self.assertIn("excluded：CP_adj no new high", status)

    def test_mixed_family_score_order_and_grok_scenario_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            rows = [candidate("GPT-Top", 50, 180), candidate("grok-4.7 high", 45, 16),
                    candidate("Other Contributor", 40, 0.4)]
            for row in rows:
                row["checked_date"] = "2026-09-26"
            write_candidates(source, rows)
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text()
            table = text.split("## 階梯表：", 1)[1].split("### Cut 名單", 1)[0]
            self.assertLess(table.index("GPT-Top"), table.index("grok-4.7 high"))
            self.assertIn("| grok-4.7 high | Grok ×16 |", table)
            self.assertIn("| Other Contributor | ×1 |", table)
            self.assertIn("Grok ×16", text)
            self.assertIn("使用者指定情境", text)
            self.assertIn("非實測", text)
            self.assertIn("來源快照日期（checked_date）：2026-09-26", text)
            self.assertNotIn("未重新抓取 AA", text)

    def test_non_gpt_cheapest_does_not_recommend_grok_subscription_from_79(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("Grok 4.7 high", 50, 16)])
            result = run_cli("--input", source, "--min-score", "0", "--monthly-tasks", "100")
            self.assertEqual(result.returncode, 0, result.stderr)
            api = (source.parent / "ladder-extra.md").read_text().split("## 外部 API 試算", 1)[1]
            self.assertIn("$79 僅適用 GPT", api)
            self.assertNotIn("續訂閱", api)
            self.assertNotIn("開外部API", api)

    def test_override_labels_follow_effective_factors_in_caveat(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("GPT-Top", 50, 100),
                                      candidate("Grok 4.7", 40, 16)])
            result = run_cli("--input", source, "--min-score", "0",
                             "--factor", "3", "--grok-factor", "4")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text()
            self.assertIn("GPT ×3 / Grok ×4 調整", text)
            self.assertNotIn("GPT ×18 / Grok ×16 調整", text)

    def test_render_header_order_picks_and_undecided_api(self):
        rows = [candidate("Claude Opus", 60, 2),
                candidate("GPT-High", 50, 10),
                candidate("GPT-Mid", 40, 4),
                candidate("GPT-Low", 20, 0.4)]
        for row in rows:
            row.update(checked_date="2026-09-24", evidence_url="https://example.org/benchmark")
            row["notes"] = "GRADE-A measured"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, rows)
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text(encoding="utf-8")
            for marker in ("番外篇", "個人實測約 18.9", "保守", "×18", "$20+$59",
                           "不進正式表", "ladder.md", "2026-09-24", "生成日期",
                           "https://example.org/benchmark", "floor", "eps_score", "eps_cp",
                           "privacy", "Cost_orig", "CP_orig", "CP_adj", "GRADE",
                           "N 未定", "benchmark 等價任務", "AA-median Free"):
                with self.subTest(marker=marker):
                    self.assertIn(marker, text)
            table = text.split("## 階梯表：", 1)[1].split("### Cut 名單", 1)[0]
            numbered = [line.split(" | ") for line in table.splitlines() if line.startswith("| ") and line[2:3].isdigit()]
            self.assertEqual([(cells[0].lstrip("| "), cells[1], cells[5]) for cells in numbered],
                             [("1", "60", "Claude Opus"),
                              ("2", "50", "GPT-High"),
                              ("3", "40", "GPT-Mid"),
                              ("4", "20", "GPT-Low")])
            self.assertIn("下表按 Score 由高到低展示", text)
            self.assertIn("攻堅：GPT-High", text)
            self.assertIn("平衡：GPT-Mid", text)
            self.assertIn("省錢：GPT-Low", text)
            self.assertNotIn("攻堅：Claude", text)
            self.assertNotIn("平衡：Claude", text)

    def test_only_claude_final_has_no_recommendation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("Claude Opus", 60, 1)])
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text()
            self.assertEqual(text.count("：從缺（無非 Claude 的階梯候選）"), 3)
            self.assertIn("無非 Claude API basis", text)

    def test_empty_and_multiple_groups_keep_decisions_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [])
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("從缺", (source.parent / "ladder-extra.md").read_text())
            rows = [candidate("GPT-One", 40, 2),
                    candidate("GPT-Two", 45, 2, version="v2")]
            write_candidates(source, rows)
            result = run_cli("--input", source, "--min-score", "0", "--monthly-tasks", "2")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (source.parent / "ladder-extra.md").read_text()
            self.assertEqual(text.count("## 階梯表："), 2)
            self.assertIn("開外部API", text)

    def test_cli_invalid_and_no_clobber_including_hardlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("GPT-One", 40, 2)])
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            original = source.parent / "ladder.md"
            original.write_text("official", encoding="utf-8")
            for output in (original, source, source.parent / "alias.csv"):
                if output.name == "alias.csv":
                    output.hardlink_to(source)
                result = run_cli("--input", source, "--min-score", "0", "--output", output)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("ERROR", result.stderr.upper())
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
                self.assertEqual(original.read_text(), "official")
            for flag, value in (("--factor", "nan"), ("--eps-cp", "inf"),
                                ("--monthly-tasks", "nan"), ("--min-score", "nan")):
                result = run_cli("--input", source, "--min-score", "0", flag, value)
                self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_hardlink_alias_to_official_ladder_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            write_candidates(source, [candidate("GPT-One", 40, 2)])
            official = source.parent / "ladder.md"
            official.write_text("official content must not change\n", encoding="utf-8")
            alias = source.parent / "other-name.md"
            alias.hardlink_to(official)
            original_hash = hashlib.sha256(official.read_bytes()).hexdigest()
            original_mtime_ns = official.stat().st_mtime_ns

            result = run_cli("--input", source, "--min-score", "0", "--output", alias)

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("ERROR", result.stderr.upper())
            self.assertEqual(hashlib.sha256(official.read_bytes()).hexdigest(), original_hash)
            self.assertEqual(official.stat().st_mtime_ns, original_mtime_ns)
            self.assertEqual(hashlib.sha256(alias.read_bytes()).hexdigest(), original_hash)

    def test_csv_errors_return_2_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.csv"
            source.write_text("identity,score\n", encoding="utf-8")
            result = run_cli("--input", source, "--min-score", "0")
            self.assertEqual(result.returncode, 2)
            self.assertIn("missing column", result.stderr)
            self.assertFalse((source.parent / "ladder-extra.md").exists())
            result = run_cli("--input", source.parent / "absent.csv", "--min-score", "0")
            self.assertEqual(result.returncode, 2)
            self.assertIn("ERROR", result.stderr)

    def test_real_snapshot_scenario_keeps_original_immutable(self):
        run = Path(__file__).resolve().parents[1] / "runs/2026-09-24-general-v5"
        source, official = run / "candidates.csv", run / "ladder.md"
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, official)]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "ladder-extra.md"
            result = run_cli("--input", source, "--output", output, "--min-score", "0")
            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("來源快照日期（checked_date）：2026-09-24", text)
            self.assertIn("https://artificialanalysis.ai/api/v2/language/models/free", text)
            self.assertIn("其他定價／計算證據 URL：https://dev.meta.ai/docs/pricing-rate-limits", text)
            self.assertLess(text.index("min-score=0"), text.index("其他定價／計算證據 URL"))
            self.assertLess(text.index("其他定價／計算證據 URL"), text.index("- privacy："))
            self.assertIn("Muse Spark 1.3 xhigh Meta Contributor", text)
            self.assertIn("excluded：CP_adj no new high", text)
            self.assertIn("1.3678 (AA API Standard xhigh cost", text)
            self.assertIn("平衡：GPT-6 Sol medium", text)
            table = text.split("## 階梯表：", 1)[1].split("### Cut 名單", 1)[0]
            scores = [float(line.split(" | ")[1]) for line in table.splitlines()
                      if line.startswith("| ") and line[2:3].isdigit()]
            self.assertEqual(scores, [57.6, 52.4, 50.9, 49.6, 47.5, 45.8,
                                      39.8, 37.3, 33.9, 32.1, 29.5, 20.9])
            self.assertIn("| 1 | 57.6 | $5.9820 | 9.63 | 9.63 | Claude Opus", table)
            self.assertIn("| 2 | 52.4 | $2.3088 | 22.70 | 408.52 | GPT-6 Astra xhigh", table)
            self.assertIn("| 12 | 20.9 | $0.0045 | 4644.44 | 83600.00 | GPT-6 Luna low", table)
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (source, official)])
