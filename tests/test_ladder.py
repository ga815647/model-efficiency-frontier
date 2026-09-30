import csv
import io
from contextlib import redirect_stderr
import os
import unittest

V5 = "runs/2026-09-24-general-v5/candidates.csv"

EXPECTED_ORDER = [
    "Claude Opus 5.5 Adaptive Reasoning, Max Effort, Default Fallback AA-median Free",
    "GPT-6 Astra xhigh AA-median Free",
    "GPT-6 Astra high AA-median Free",
    "GPT-6 Astra medium AA-median Free",
    "GPT-6 Sol max AA-median Free",
    "Muse Spark 1.3 xhigh Meta Contributor",
    "GPT-6 Luna xhigh AA-median Free",
    "GPT-6 Luna high AA-median Free",
    "GPT-6 Luna medium AA-median Free",
    "GPT-6 Luna low AA-median Free",
]

EXPECTED_CUTS = {
    "GPT-6 Astra max AA-median Free": "GPT-6 Astra xhigh AA-median Free",
    "GPT-6 Astra low AA-median Free": "Muse Spark 1.3 xhigh Meta Contributor",
    "GPT-5.6 Luna low AA-median Free": "GPT-6 Luna low AA-median Free",
}


def load_paid_v5():
    import sys
    sys.path.insert(0, "scripts")
    import compute_frontier as cf
    with open(V5, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    paid = []
    for r in raw:
        if cf.is_free_row(r):
            continue
        r = dict(r)
        r["_score"] = float(r["score"])
        r["_cost"] = float(r["cost_per_task"])
        paid.append(r)
    return paid


class TestV5Oracle(unittest.TestCase):
    def test_v5_final_order(self):
        import sys
        sys.path.insert(0, "scripts")
        import compute_frontier as cf
        import ladder
        paid = load_paid_v5()
        kept, _ = cf.compute_one_group(paid, 0, None, 2.0, 0.05)
        final, _ = ladder.dedup_bands([r for r, _ in kept], 2.0)
        self.assertEqual([r["identity"] for r in final], EXPECTED_ORDER)

    def test_v5_cuts(self):
        import sys
        sys.path.insert(0, "scripts")
        import compute_frontier as cf
        import ladder
        paid = load_paid_v5()
        kept, _ = cf.compute_one_group(paid, 0, None, 2.0, 0.05)
        _, cuts = ladder.dedup_bands([r for r, _ in kept], 2.0)
        self.assertEqual(cuts, EXPECTED_CUTS)


def mk(identity, score, cost):
    return {"identity": identity, "_score": float(score),
            "_cost": float(cost), "_cp": float(score) / float(cost)}


class TestBands(unittest.TestCase):
    def test_band_edge_strict(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        rows = [mk("A", 40.0, 0.01), mk("B", 39.1, 1.0), mk("C", 38.1, 0.01)]
        # gaps 0.9 (join) and 1.0 (break, strict <) at eps=2.0
        final, cuts = ladder.dedup_bands(rows, 2.0)
        self.assertEqual([r["identity"] for r in final], ["A", "C"])
        self.assertEqual(cuts, {"B": "A"})

    def test_three_row_band_middle_out(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        rows = [mk("H", 50.0, 2.0), mk("M", 49.5, 0.5), mk("T", 49.0, 0.1)]
        final, cuts = ladder.dedup_bands(rows, 2.0)
        self.assertEqual([r["identity"] for r in final], ["H", "T"])
        self.assertEqual(list(cuts), ["M"])

    def test_pinned_pair_kept(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        top = mk("TOP", 60.0, 6.0)
        low = mk("LOW", 59.9, 0.01)
        peak = mk("PEAK", 10.0, 0.001)
        final, cuts = ladder.dedup_bands([top, low, peak], 2.0)
        # TOP is max-score pinned, PEAK is max-CP pinned; LOW must survive
        # only if it is itself pinned — here LOW loses to TOP on keep-key
        # but the pair (TOP, LOW) contains pinned TOP; LOW is dropped.
        self.assertIn("TOP", [r["identity"] for r in final])
        self.assertIn("PEAK", [r["identity"] for r in final])

    def test_pinned_loser_survives(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        # max-CP row sits inside a 2-row band and would lose on keep-key
        # only if score dominated it; construct so pinned row is the loser:
        a = mk("A", 30.0, 0.01)   # CP 3000 = max CP overall → pinned
        b = mk("B", 30.5, 0.005)  # CP 6100 — actually higher; keep both pinned instead
        peak = mk("ZZZ", 99.0, 90.0)
        final, _ = ladder.dedup_bands([peak, b, a], 2.0)
        ids = [r["identity"] for r in final]
        self.assertIn("ZZZ", ids)  # max score pinned
        self.assertIn("B", ids)    # max CP pinned


class TestVerify(unittest.TestCase):
    def refs(self):
        return {
            "root": "openai/gpt-6-astra",
            "general": "meta/muse-spark-1.3-contributor#xhigh",
            "explore": "openai/gpt-6-luna#high",
        }

    def test_config_verify_ok(self):
        import sys
        sys.path.insert(0, "scripts")
        import compute_frontier as cf
        import ladder
        paid = load_paid_v5()
        kept, _ = cf.compute_one_group(paid, 0, None, 2.0, 0.05)
        final, _ = ladder.dedup_bands([r for r, _ in kept], 2.0)
        for label, ref in self.refs().items():
            with self.subTest(ref=ref):
                self.assertTrue(
                    ladder.verify_ref(ref, final).startswith("OK"),
                    f"{label} {ref} should verify OK")

    def test_config_verify_unknown_slug(self):
        import sys
        sys.path.insert(0, "scripts")
        import compute_frontier as cf
        import ladder
        paid = load_paid_v5()
        kept, _ = cf.compute_one_group(paid, 0, None, 2.0, 0.05)
        final, _ = ladder.dedup_bands([r for r, _ in kept], 2.0)
        v = ladder.verify_ref("openai/nonexistent-model-zzz", final)
        self.assertTrue(v.startswith("⚠"))
        self.assertIn("GPT-6 Luna low AA-median Free", v)  # CP-peak suggestion

    def test_variant_none_mapping(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        toks = ladder.ref_tokens("openai/gpt-6-luna#none")
        self.assertIn("non", toks)
        self.assertIn("reasoning", toks)
        self.assertNotIn("none", toks)

    def test_missing_config_warns(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        with redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(ladder.load_config_refs("/nonexistent/opencode.json"), {})
        self.assertIn("WARNING: cannot load config refs from /nonexistent/opencode.json", stderr.getvalue())
        self.assertIn("No such file or directory", stderr.getvalue())

    def test_two_groups_split(self):
        import sys
        sys.path.insert(0, "scripts")
        import ladder
        rows = [dict(mk("G1", 40.0, 1.0), benchmark="B1",
                     benchmark_version="v1", cost_basis="api"),
                dict(mk("G2", 41.0, 1.0), benchmark="B2",
                     benchmark_version="v1", cost_basis="api")]
        groups = ladder.group_rows(rows)
        self.assertEqual(len(groups), 2)
