#!/usr/bin/env python3
"""Descending-Intelligence CP frontier calculator (single source of truth).

Confirmed design (2026-09-17):
- Identity = Model x Effort x Provider x Pricing/Data Plan (+ version snapshot).
- CP = score / cost_per_task. Cost basis (api/subscription/trial) never mixed:
  script groups by (benchmark, benchmark_version, cost_basis) only.
- Merged single-table mode (2026-09-24, privacy bucket retired by user):
  no per-bucket split; privacy column kept as display annotation only.
  --privacy-mode flag accepted for backward compat but ignored (no-op).
- FREE rows (is_free=true or cost<=0) never enter the numeric frontier.
- Tie-break: same score -> cheaper cost first (stable, order-independent).
- Epsilon anti-noise: keep a candidate only if
    cp > best_cp * (1 + eps_cp)
  AND (for real steps) the score gap vs last KEPT row >= eps_score.
  Same-tier rows (gap < eps_score) anchored to last real step: they may take
  over best_cp but do not move the score anchor. Strict >, equal CP keeps
  the higher-score row only.

CSV columns (required unless noted):
  identity,model,effort,provider,pricing_plan,model_version,
  benchmark,benchmark_version,cost_per_task,cost_basis,
  privacy (private-safe|other),is_free (true|false),
  evidence_url,checked_date,notes (optional),quota (optional, for free sidecar)
"""

import argparse
import csv
import sys
from collections import defaultdict


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="candidates.csv path")
    p.add_argument("--min-score", type=float, required=True,
                   help="minimum intelligence floor (required, no default)")
    p.add_argument("--max-cost", type=float, default=None,
                   help="optional absolute budget cap on cost_per_task")
    p.add_argument("--eps-score", type=float, default=2.0)
    p.add_argument("--eps-cp", type=float, default=0.05,
                   help="fraction, e.g. 0.05 = 5%%")
    p.add_argument("--privacy-mode", default="all",
                   choices=["private-safe", "other", "all"],
                   help="deprecated no-op (merged mode 2026-09-24); kept for compat")
    p.add_argument("--output", default=None, help="write markdown here (default stdout)")
    return p.parse_args()


def is_free_row(r):
    v = (r.get("is_free") or "").strip().lower()
    if v in ("true", "1", "yes", "y"):
        return True
    try:
        return float(r["cost_per_task"]) <= 0
    except (ValueError, TypeError, KeyError):
        return True


def compute_one_group(rows, min_score, max_cost, eps_score, eps_cp):
    """rows: list of dicts with float score/cost already parsed. Returns (kept, excluded)."""
    # Sort: score desc, cost asc. Python sort is stable.
    rows = sorted(rows, key=lambda r: (-r["_score"], r["_cost"]))
    kept, excluded = [], []
    best_cp = None
    anchor_score = None  # score of last kept row that moved the anchor (real step)

    for r in rows:
        s, c = r["_score"], r["_cost"]
        if s < min_score:
            excluded.append((r, f"below min-score floor ({s} < {min_score})"))
            continue
        if max_cost is not None and c > max_cost:
            excluded.append((r, f"over max-cost cap ({c} > {max_cost})"))
            continue
        cp = s / c
        r["_cp"] = cp
        if best_cp is None:
            kept.append((r, "highest-capability start of this bucket"))
            best_cp = cp
            anchor_score = s
            continue
        gap = anchor_score - s  # >= 0 given sort order
        if gap < 0:
            gap = 0.0  # defensive: unsorted input edge
        if cp <= best_cp * (1 + eps_cp):
            excluded.append((r, f"CP no new high ({cp:.2f} <= best {best_cp:.2f} x {1 + eps_cp:.2f})"))
            continue
        if gap < eps_score:
            # Same-tier takeover: efficiency win inside benchmark noise band.
            kept.append((r, f"same-tier (gap {gap:.2f} < {eps_score}) CP takeover +{(cp / best_cp - 1) * 100:.1f}%%"))
            best_cp = cp
            # anchor_score unchanged on purpose
        else:
            kept.append((r, f"CP new high +{(cp / best_cp - 1) * 100:.1f}%% at score step -{gap:.2f}"))
            best_cp = cp
            anchor_score = s
    return kept, excluded


def fmt_table(kept):
    lines = ["| Score | Identity | Cost/task | CP | Provider | Training bucket | 為什麼留下 |",
             "|---|---|---|---|---|---|---|"]
    for r, reason in kept:
        lines.append(
            f"| {r['_score']:g} | {r['identity']} | ${r['_cost']:.2f} "
            f"| {r['_cp']:.1f} | {r['provider']} | {r['privacy']} | {reason} |"
        )
    return "\n".join(lines)


def main():
    args = parse_args()
    with open(args.input, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))

    required = ["identity", "benchmark", "benchmark_version", "cost_per_task",
                "cost_basis", "privacy", "provider"]
    for col in required:
        if col not in (raw[0].keys() if raw else []):
            print(f"ERROR: missing column '{col}' in {args.input}", file=sys.stderr)
            sys.exit(2)

    free_rows = [r for r in raw if is_free_row(r)]
    paid = [r for r in raw if not is_free_row(r)]

    # Validate + parse numerics on paid rows (privacy kept as display only)
    groups = defaultdict(list)
    for r in paid:
        priv = (r.get("privacy") or "").strip()
        # NOTE: --privacy-mode is a deprecated no-op; no filtering here.
        try:
            s = float(r.get("score", ""))
            c = float(r["cost_per_task"])
        except (ValueError, TypeError):
            print(f"ERROR: row '{r.get('identity')}' has non-numeric score/cost",
                  file=sys.stderr)
            sys.exit(2)
        if c <= 0:
            print(f"ERROR: row '{r.get('identity')}' cost<=0 but is_free not set",
                  file=sys.stderr)
            sys.exit(2)
        r["_score"], r["_cost"] = s, c
        key = (r["benchmark"], r["benchmark_version"], r["cost_basis"])
        groups[key].append(r)

    out = []
    out.append(f"# Frontier result (as-of run: `{args.input}`)")
    out.append(f"- min-score={args.min_score:g}, max-cost="
               f"{args.max_cost if args.max_cost is not None else 'none'}, "
               f"eps_score={args.eps_score:g}, eps_cp={args.eps_cp * 100:.1f}%, "
               f"privacy-mode={args.privacy_mode}")
    out.append("- Rule: merged single table (privacy display only); FREE rows never in numeric frontier.")
    out.append("")

    if not groups:
        out.append("_No paid candidates after min-score filtering._")
    for key in sorted(groups):
        bench, ver, basis = key
        kept, excluded = compute_one_group(
            groups[key], args.min_score, args.max_cost, args.eps_score, args.eps_cp)
        out.append(f"## {bench} @ {ver} | basis={basis} "
                   f"(n={len(groups[key])})")
        out.append(fmt_table(kept) if kept else "_Empty frontier._")
        out.append("")
        if excluded:
            out.append("<details><summary>Dominated / excluded sample "
                       f"({len(excluded)}, top 5)</summary>\n")
            for r, reason in excluded[:5]:
                out.append(f"- {r['identity']} (S={r['_score']:g}, "
                           f"${r['_cost']:.2f}): {reason}")
            out.append("</details>\n")

    if free_rows:
        out.append(f"## FREE sidecar ({len(free_rows)}, excluded from frontier math)")
        for r in free_rows:
            out.append(f"- {r.get('identity')} | provider={r.get('provider')} | "
                       f"quota={r.get('quota', '?')} | privacy={r.get('privacy')} | "
                       f"evidence={r.get('evidence_url', '?')}")
    else:
        out.append("## FREE sidecar: none in this input.")

    text = "\n".join(out) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
