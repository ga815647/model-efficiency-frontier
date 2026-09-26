#!/usr/bin/env python3
"""Official-chain three-pick recommendation output (Phase 2, display layer).

Design (AGENTS.md, official-chain landing 2026-09-24):
- Frontier MATH is never reimplemented here: grouping/eps/frontier all come
  from compute_frontier.compute_one_group (sole legal implementation).
- Per-group output: 最適合 (chain head band pick) / 平衡 (chain mid band
  pick) / floor (chain tail band pick; tail unmatched -> fallback evidence
  bottom = lowest-score usable paid row in same benchmark+version,
  with reason; unchanged).
- Band rule: anchor = chain-rung best-match row (existing ordered-token
  match; unmatched -> 無AA分數→退回, no band, never substituted);
  band = [anchor_score - band_eps_mult*eps_score, +inf) (capped at max
  score in input); pick = highest-CP paid row in band passing
  min-score/max-cost (tie: higher score, then cheaper). Floor role uses
  the same rule on the tail anchor.
- Pick exclusion: --exclude-family substrings (case-insensitive) exclude
  rows from PICKS ONLY (frontier math untouched). Default excludes the
  Claude family (no-Claude forward policy: never 最適合/平衡/floor).
  Rows with effort=default carry a (default-effort caveat) tag.
- Suppression (top-down, CP only): if an upper role's pick CP >= a lower
  role's pick CP, the lower shows 從缺 + ⚠ + reason (score diff noted,
  not used for the decision). Lower-beats-upper keeps both.
- Chain matching: --chain-head/--chain-mid/--chain-tail are identity
  substrings, matched case-insensitively after normalizing non-alphanumerics
  to spaces, as ordered-token-subsequence (so "deepseek flash" matches
  "Codex DeepSeek V4 Flash 0731 max ..."). "|" separates alternatives
  (match if any alternative matches). Multiple matched rows -> highest
  score wins (tie: cheaper). No match -> `無AA分數→退回`, never substituted.
- A>=B invariant: --coding-floor gives the coding-side floor; any group
  floor below it emits a WARNING (stderr + output) but exit stays 0.
- Tier display (old 5-tier matrix) is DEPRECATED: kept only as secondary
  output behind --show-tiers; default output is the three-pick table.
- --privacy-mode flag accepted for backward compat but ignored (no-op).
- Latency columns (ttft_s, time_per_task_s) are optional, AA-measured only;
  shown as annotations when present, never enter math.

Default groups are the official native groups (AGENTS.md §1, OmO
agent-model-matching.md @ HEAD 60cfa1a 2026-09-24): lanes
(daily-normal, geeky-normal, geeky-heavy), curated agents (explore,
librarian — byte-identical chains, two entries sharing one query set),
categories (quick, visual-engineering, writing). Override with
--group-name + --chain-head/--chain-mid/--chain-tail (comma-separated
lists align by position; a single value broadcasts).
"""

import argparse
import csv
import re
import sys
from collections import defaultdict

import compute_frontier as cf

K_TIER = 3.5  # deprecated tier display only
TIERS = ["T1", "T2", "T3", "T4", "T5"]

DEFAULT_GROUPS = [
    {"name": "daily-normal",
     "head": "opus 5 5 medium",
     "mid": "kimi k3 max",
     "tail": "glm 5 3 max"},
    {"name": "geeky-normal",
     "head": "gpt 5 6 sol medium",
     "mid": "",
     "tail": ""},
    {"name": "geeky-heavy",
     "head": "gpt 6 astra xhigh",
     "mid": "",
     "tail": ""},
    {"name": "explore",
     "head": "kimi for coding highspeed off",
     "mid": "gpt 6 luna fast low | gpt 6 luna low | deepseek flash | qwen3 7 plus | minimax m2 7",
     "tail": "haiku"},
    {"name": "librarian",
     "head": "kimi for coding highspeed off",
     "mid": "gpt 6 luna fast low | gpt 6 luna low | deepseek flash | qwen3 7 plus | minimax m2 7",
     "tail": "haiku"},
    {"name": "quick",
     "head": "gpt 6 luna fast low | gpt 6 luna low",
     "mid": "deepseek flash",
     "tail": "haiku"},
    {"name": "visual-engineering",
     "head": "claude fable 5 1 max",
     "mid": "opus 5 5 max",
     "tail": "kimi k3 max"},
    {"name": "writing",
     "head": "claude fable 5 1 low",
     "mid": "opus 5 5 low",
     "tail": "opus 4 6 max"},
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--min-score", type=float, required=True)
    p.add_argument("--max-cost", type=float, default=None)
    p.add_argument("--eps-score", type=float, default=2.0)
    p.add_argument("--eps-cp", type=float, default=0.05)
    p.add_argument("--privacy-mode", default="all",
                   choices=["private-safe", "other", "all"],
                   help="deprecated no-op (merged mode 2026-09-24); kept for compat")
    p.add_argument("--group-name", default=None,
                   help="comma-separated group labels (default: official "
                        "native groups: daily-normal, geeky-normal, "
                        "geeky-heavy, explore, librarian, quick, "
                        "visual-engineering, writing)")
    p.add_argument("--chain-head", default=None,
                   help="comma-separated head substrs ('|' = alternatives)")
    p.add_argument("--chain-mid", default=None,
                   help="comma-separated mid substrs ('|' = alternatives)")
    p.add_argument("--chain-tail", default=None,
                   help="comma-separated tail substrs ('|' = alternatives)")
    p.add_argument("--coding-floor", type=float, default=None,
                   help="coding-side floor for A>=B invariant check (warning only)")
    p.add_argument("--band-eps-mult", type=float, default=1.0,
                   help="band lower edge = anchor - band_eps_mult*eps_score")
    p.add_argument("--exclude-family", default="claude,opus,fable,sonnet,haiku",
                   help="comma-separated substrings (case-insensitive) excluded "
                        "from PICKS ONLY; frontier math untouched. Empty string "
                        "disables.")
    p.add_argument("--show-tiers", action="store_true",
                   help="also emit deprecated 5-tier display matrix")
    p.add_argument("--output", default=None)
    return p.parse_args()


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip()


def match_query(query, identity):
    """Ordered-token-subsequence match; '|' = alternatives. Empty query never matches."""
    itoks = norm(identity).split()
    for alt in (query or "").split("|"):
        qtoks = norm(alt).split()
        if not qtoks:
            continue
        i = 0
        for t in itoks:
            if t == qtoks[i]:
                i += 1
                if i == len(qtoks):
                    return True
    return False


def find_best(rows, query):
    cands = [r for r in rows if match_query(query, r["identity"])]
    if not cands:
        return None
    # Prefer exact-prefix token match (query tokens == identity leading
    # tokens) so 'gpt 6 luna low' does not anchor 'gpt 5 6 luna low'
    # (norm splits '5.6' -> '5 6', making the former a subsequence of the
    # latter). Fall back to subsequence behavior when no exact hit.
    exact = [r for r in cands if any(
        norm(r["identity"]).split()[:len(qtoks)] == qtoks
        for alt in (query or "").split("|")
        for qtoks in [norm(alt).split()] if qtoks)]
    pool = exact or cands
    return min(pool, key=lambda r: (-r["_score"], r["_cost"]))


def cp_of(r):
    return r.get("_cp", r["_score"] / r["_cost"])


def excluded_by_family(identity, fams):
    low = (identity or "").lower()
    return any(f and f in low for f in fams)


def band_pick(paid, query, band_mult, eps_score, min_score, max_cost, fams):
    """Anchor = best-match row; band = [anchor - mult*eps, +inf).

    Returns (anchor, pick, band_lo). Unmatched anchor -> (None, None, None).
    Pick = highest-CP paid row in band passing min/max-cost, excluding
    --exclude-family rows (tie: higher score, then cheaper).
    """
    anchor = find_best(paid, query)
    if anchor is None:
        return None, None, None
    band_lo = anchor["_score"] - band_mult * eps_score
    cands = [r for r in paid
             if r["_score"] >= band_lo
             and r["_score"] >= min_score
             and (max_cost is None or r["_cost"] <= max_cost)
             and not excluded_by_family(r["identity"], fams)]
    if not cands:
        return anchor, None, band_lo
    pick = min(cands, key=lambda r: (-cp_of(r), -r["_score"], r["_cost"]))
    return anchor, pick, band_lo


def default_effort_tag(r):
    return "；(default-effort caveat)" \
        if (r.get("effort") or "").strip().lower() == "default" else ""


def grade_of(r):
    notes = r.get("notes") or ""
    if notes.startswith("GRADE-A"):
        return "GRADE-A"
    if notes.startswith("GRADE-B"):
        return "GRADE-B"
    return "GRADE未知"


def speed_tag(r, show_speed):
    if not show_speed:
        return ""
    t, d = (r.get("ttft_s") or "").strip(), \
        (r.get("time_per_task_s") or "").strip()
    if t or d:
        return f"；TTFT {t or '?'}s／每任務 {d or '?'}s"
    return ""


def fmt_row(r, show_speed):
    return (f"{r['identity']}（S={r['_score']:g}, ${r['_cost']:.2f}, "
            f"CP={r.get('_cp', r['_score'] / r['_cost']):.1f}, "
            f"effort={r.get('effort', '?')}, {grade_of(r)}"
            f"{speed_tag(r, show_speed)}）")


def split_list(s):
    return [x.strip() for x in s.split(",")] if s is not None else None


def resolve_groups(args):
    if args.group_name is None and args.chain_head is None \
            and args.chain_mid is None and args.chain_tail is None:
        return DEFAULT_GROUPS
    names = split_list(args.group_name) or ["custom"]
    heads = split_list(args.chain_head) or [""]
    mids = split_list(args.chain_mid) or [""]
    tails = split_list(args.chain_tail) or [""]
    n = max(len(names), len(heads), len(mids), len(tails))

    def broadcast(lst, label):
        if len(lst) == 1:
            return lst * n
        if len(lst) == n:
            return lst
        print(f"ERROR: --{label} count {len(lst)} matches neither 1 nor "
              f"group count {n}", file=sys.stderr)
        sys.exit(2)

    names, heads, mids, tails = broadcast(names, "group-name"), \
        broadcast(heads, "chain-head"), broadcast(mids, "chain-mid"), \
        broadcast(tails, "chain-tail")
    return [{"name": a, "head": b, "mid": c, "tail": d}
            for a, b, c, d in zip(names, heads, mids, tails)]


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    required = ["identity", "benchmark", "benchmark_version", "cost_per_task",
                "cost_basis", "privacy", "provider"]
    for col in required:
        if col not in (raw[0].keys() if raw else []):
            print(f"ERROR: missing column '{col}' in {path}", file=sys.stderr)
            sys.exit(2)
    free_rows = [r for r in raw if cf.is_free_row(r)]
    paid = []
    for r in [x for x in raw if not cf.is_free_row(x)]:
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
        paid.append(r)
    return paid, free_rows, (raw[0].keys() if raw else [])


def tier_of(score, peak, width):
    if score >= peak + 2 * width:
        return "T1"
    if score >= peak + width:
        return "T2"
    if score >= peak:
        return "T3"
    if score >= peak - width:
        return "T4"
    return "T5"


def main():
    args = parse_args()
    groups_spec = resolve_groups(args)
    paid, free_rows, fieldnames = load_rows(args.input)
    show_speed = "ttft_s" in fieldnames or "time_per_task_s" in fieldnames

    # Frontier math ONLY via compute_frontier.
    by_key = defaultdict(list)
    for r in paid:
        by_key[(r["benchmark"], r["benchmark_version"], r["cost_basis"])].append(r)
    kept_all, excluded_all = [], []
    for key in sorted(by_key):
        kept, excluded = cf.compute_one_group(
            by_key[key], args.min_score, args.max_cost,
            args.eps_score, args.eps_cp)
        kept_all.extend(kept)
        excluded_all.extend(excluded)

    out = []
    out.append(f"# Recommendation (official-chain three-pick; as-of run: `{args.input}`)")
    out.append(f"- min-score={args.min_score:g}, max-cost="
               f"{args.max_cost if args.max_cost is not None else 'none'}, "
               f"eps_score={args.eps_score:g}, eps_cp={args.eps_cp * 100:.1f}%, "
               f"privacy-mode={args.privacy_mode} (no-op), "
               f"coding-floor={args.coding_floor if args.coding_floor is not None else 'none'}")
    out.append("- Rule: frontier math by compute_frontier only; chain picks are "
               "display lookups (identity substring, ordered-token match); "
               "unmatched chain rung = 無AA分數→退回, never substituted; "
               "FREE rows excluded.")
    out.append("")

    fams = [x.strip().lower() for x in (args.exclude_family or "").split(",")
            if x.strip()]
    out.append(f"- band rule: band=[anchor-{args.band_eps_mult:g}*eps_score,+inf), "
               f"pick=highest-CP in band (tie: higher score, then cheaper); "
               f"picks exclude family [{','.join(fams) or 'none'}] (math untouched); "
               f"suppression top-down on CP only (upper CP >= lower CP -> lower 從缺).")
    out.append("")

    warnings = []
    for g in groups_spec:
        out.append(f"## Group {g['name']}")
        roles = []
        floor_val = None
        for role, label in (("head", "最適合"), ("mid", "平衡"), ("tail", "floor")):
            q = g[role]
            anchor, pick, band_lo = band_pick(
                paid, q, args.band_eps_mult, args.eps_score,
                args.min_score, args.max_cost, fams)
            roles.append({"role": role, "label": label, "q": q,
                          "anchor": anchor, "pick": pick, "band_lo": band_lo})
        # Suppression top-down, CP only: upper pick CP >= lower pick CP
        # -> lower 從缺 (score diff noted, never used for the decision).
        for i in range(1, len(roles)):
            for j in range(i):
                up, lo = roles[j], roles[i]
                if up["pick"] is not None and lo["pick"] is not None \
                        and cp_of(up["pick"]) >= cp_of(lo["pick"]):
                    lo["suppressed_by"] = up
                    break
        for ent in roles:
            role, label, q = ent["role"], ent["label"], ent["q"]
            anchor, pick, band_lo = ent["anchor"], ent["pick"], ent["band_lo"]
            if anchor is None:
                if role == "tail":
                    if kept_all:
                        usable = [r for r in paid if r["_score"] >= args.min_score
                                  and (args.max_cost is None or r["_cost"] <= args.max_cost)]
                        bottom = min(usable if usable else [t[0] for t in kept_all],
                                     key=lambda r: (r["_score"], r["_cost"]))
                        floor_val = bottom["_score"]
                        out.append(f"- floor：{floor_val:g}（chain tail `{q}` 無AA分數→退回 → "
                                   f"fallback evidence bottom：{fmt_row(bottom, show_speed)}；"
                                   f"同 benchmark 同版本內最低可用實測行）")
                    else:
                        floor_val = None
                        out.append(f"- floor：無可用行（chain tail `{q}` 無AA分數→退回，"
                                   f"且 frontier kept 為空）")
                else:
                    out.append(f"- {label} (chain {role} `{q}`)："
                               f"無AA分數→退回（本 input 無匹配行，不代入、不推定）")
                continue
            band_txt = (f"band [{band_lo:g},+inf), anchor {fmt_row(anchor, show_speed)}")
            if pick is None:
                out.append(f"- {label} (chain {role} `{q}`；{band_txt})："
                           f"band 內無可用 pick（min/max-cost 或 family 排除後從缺）")
                continue
            if "suppressed_by" in ent:
                up = ent["suppressed_by"]
                sd = pick["_score"] - up["pick"]["_score"]
                out.append(f"- {label} (chain {role} `{q}`；{band_txt})：從缺 "
                           f"(upper {up['label']} CP {cp_of(up['pick']):.1f} >= "
                           f"本檔 CP {cp_of(pick):.1f}；⚠ score diff {sd:+g} 僅註記；"
                           f"本檔原 pick {fmt_row(pick, show_speed)})")
                continue
            flag = (f"；⚠ below min-score {args.min_score:g}"
                    if pick["_score"] < args.min_score else "")
            if role == "tail":
                floor_val = pick["_score"]
                out.append(f"- floor (chain tail `{q}`；{band_txt})：{floor_val:g}（band CP-best "
                           f"{fmt_row(pick, show_speed)}{default_effort_tag(pick)}{flag}）")
            else:
                out.append(f"- {label} (chain {role} `{q}`；{band_txt})：★ "
                           f"{fmt_row(pick, show_speed)}{default_effort_tag(pick)}{flag}")
        if args.coding_floor is not None and floor_val is not None \
                and floor_val < args.coding_floor:
            w = (f"WARNING: group {g['name']} floor {floor_val:g} < "
                 f"coding-floor {args.coding_floor:g} (A>=B violated)")
            warnings.append(w)
            out.append(f"- ⚠ {w}")
        out.append("")

    if warnings:
        for w in warnings:
            print(w, file=sys.stderr)
    else:
        out.append(f"A>=B check: {'pass (all group floors >= coding-floor)' if args.coding_floor is not None else 'skipped (--coding-floor not given)'}.")
        out.append("")

    out.append(f"FREE sidecar: {len(free_rows)} row(s), excluded from math.")
    out.append("Tier display: deprecated secondary output "
               f"({'shown below via --show-tiers' if args.show_tiers else 'hidden; pass --show-tiers to restore'}).")

    if args.show_tiers:
        out.append("")
        out.append("## (Deprecated) 5-tier display matrix")
        if kept_all:
            width = K_TIER * args.eps_score
            peak_row = max(kept_all, key=lambda t: t[0]["_cp"])
            peak, peak_cp = peak_row[0]["_score"], peak_row[0]["_cp"]
            out.append(f"- anchor=overall CP peak ({peak_row[0]['identity']} "
                       f"S={peak:g} CP={peak_cp:.1f}); width=3.5 x eps_score={width:g}")
            out.append("| 級別 | merged |")
            out.append("|---|---|")
            for tier in TIERS:
                kept = [(r, reason) for r, reason in kept_all
                        if tier_of(r["_score"], peak, width) == tier]
                out_rows = [(r, reason) for r, reason in excluded_all
                            if tier_of(r["_score"], peak, width) == tier]
                if not kept:
                    cell = "從缺"
                    if out_rows:
                        cell += "（" + "、".join(
                            r["identity"] for r, _ in out_rows) + " 全被淘汰，不推）"
                else:
                    atk = min(kept, key=lambda t: (-t[0]["_score"], t[0]["_cost"]))
                    val = max(kept, key=lambda t: t[0]["_cp"])
                    if atk[0]["identity"] == val[0]["identity"]:
                        cell = (f"★ {atk[0]['identity']}（S={atk[0]['_score']:g}, "
                                f"${atk[0]['_cost']:.2f}, CP={atk[0]['_cp']:.1f}）攻堅＝省錢")
                    else:
                        cell = (f"攻堅 ★ {atk[0]['identity']}（S={atk[0]['_score']:g}, "
                                f"${atk[0]['_cost']:.2f}）；省錢 ★ "
                                f"{val[0]['identity']}（CP={val[0]['_cp']:.1f}）")
                    if out_rows:
                        cell += "；不推：" + "、".join(
                            r["identity"] for r, _ in out_rows)
                out.append(f"| {tier} | {cell} |")
        else:
            out.append("_No kept rows; tier matrix empty._")

    text = "\n".join(out) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
