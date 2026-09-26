#!/usr/bin/env python3
"""Efficiency ladder display layer (OMO-free, 2026-09-24).

Pipeline: candidates.csv -> compute_one_group (frozen math) -> dedup_bands
(0.5eps chaining + pinned) -> config verify -> ladder.md render.

Constraints:
- scripts/compute_frontier.py is FROZEN: imported, never edited.
- scripts/recommend.py is RETIRED: never imported here; config-match
  semantics (norm / ref_tokens / match_rows) are copied, not imported.
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

try:
    import compute_frontier as cf
except ImportError:  # allow `python3 scripts/ladder.py` from anywhere
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import compute_frontier as cf


# ---------------------------------------------------------------- Step 1: dedup

def keep_key(r):
    return (-r["_cp"], -r["_score"], r["_cost"])


def dedup_bands(rows, eps_score):
    """rows: score-desc list with _score/_cost/_cp. Returns (final, cuts)."""
    rows = sorted(rows, key=lambda r: (-r["_score"], r["_cost"]))
    if not rows:
        return [], {}
    pinned = {max(rows, key=lambda r: r["_score"])["identity"],
              max(rows, key=lambda r: r["_cp"])["identity"]}
    th = 0.5 * eps_score
    bands, cur = [], [rows[0]]
    for r in rows[1:]:
        if cur[-1]["_score"] - r["_score"] < th:
            cur.append(r)
        else:
            bands.append(cur)
            cur = [r]
    bands.append(cur)
    final, cuts = [], {}
    for b in bands:
        if len(b) == 1:
            final.append(b[0])
            continue
        w = sorted(b, key=keep_key)
        if len(b) == 2:
            keep = w[0]
            if w[0]["identity"] not in pinned and w[1]["identity"] in pinned:
                keep = w[1]
            drop = b[1] if keep is b[0] else b[0]
            final.append(keep)
            cuts[drop["identity"]] = keep["identity"]
            continue
        w = list(b)
        while len(w) > 2:
            mid = len(w) // 2
            a, c = w[mid - 1], w[mid]
            drop = c if keep_key(c) >= keep_key(a) else a
            if drop["identity"] in pinned:
                drop = a if drop is c else c
                if drop["identity"] in pinned:
                    break
            w.remove(drop)
            anchor = b[0]
            cuts[drop["identity"]] = sorted(w, key=keep_key)[0]["identity"]
        final.extend(w)
    final.sort(key=lambda r: (-r["_score"], r["_cost"]))
    return final, cuts


# ------------------------------------------------------- Step 2: config match

def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip()


def ref_tokens(ref):
    """'provider/model#variant' -> token list; variant none -> non reasoning."""
    body = ref.split("#", 1)
    toks = norm(body[0].split("/", 1)[1] if "/" in body[0] else body[0]).split()
    if len(body) == 2:
        v = norm(body[1])
        toks += ["non", "reasoning"] if v == "none" else v.split()
    return [t for t in toks if t]


def _subseq(qtoks, itoks):
    i = 0
    for t in itoks:
        if i < len(qtoks) and t == qtoks[i]:
            i += 1
            if i == len(qtoks):
                return True
    return not qtoks


def split_ref(ref):
    """Split a config ref into (model_part_tokens, variant_part_tokens).

    Reuses ref_tokens output shape: model part = ref_tokens(model part
    before '#'); variant part = ref_tokens('#'+variant) so '#none' still
    yields ['non', 'reasoning']. ref_tokens() itself is unchanged.
    """
    body = (ref or "").split("#", 1)
    model_toks = ref_tokens(body[0])
    var_toks = ref_tokens("#" + body[1]) if len(body) == 2 else []
    return model_toks, var_toks


def match_rows(tokens, rows):
    return match_ref(tokens, None, rows)


def match_ref(model_toks, var_toks, rows):
    """Two-part match: BOTH parts must be ordered-subsequences.

    Empty variant part = true. Exact-prefix priority on the model part,
    then keep-key (-score, cost) best.
    """
    model_toks = model_toks or []
    var_toks = var_toks or []
    cands = [r for r in rows
             if _subseq(model_toks, norm(r["identity"]).split())
             and _subseq(var_toks, norm(r["identity"]).split())]
    if not cands:
        return None
    exact = [r for r in cands
             if norm(r["identity"]).split()[:len(model_toks)] == model_toks]
    pool = exact or cands
    return min(pool, key=lambda r: (-r["_score"], r["_cost"]))


def _match_identity(ref, identities):
    """Two-part subsequence match over bare identities (no stats for drops)."""
    model_toks, var_toks = split_ref(ref)
    pseudo = [{"identity": i, "_score": 0.0, "_cost": float("inf")}
              for i in identities]
    m = match_ref(model_toks, var_toks, pseudo)
    return m["identity"] if m else None


CLAUDE_FAMS = ("claude", "opus", "fable", "sonnet", "haiku")


def _is_claude(identity):
    return any(t in CLAUDE_FAMS for t in norm(identity).split())


def verify_ref(ref, final, cuts=None, excluded=None):
    """Verify one config ref against the final ladder.

    2-arg call verify_ref(ref, final) is the tested shape; cuts/excluded
    are optional so callers can also report cut-winner detail.
    """
    final = final or []
    model_toks, var_toks = split_ref(ref)
    hit = match_ref(model_toks, var_toks, final)
    if hit is not None:
        s = (f"OK（S={hit['_score']:g} ${hit['_cost']:.4f} "
             f"CP={hit['_cp']:.1f} {hit['identity']}）")
        if _is_claude(hit["identity"]):
            s += "；⚠ Claude-family 永不推薦（禁令 14）"
        return s
    if cuts:
        drop_id = _match_identity(ref, list(cuts))
        if drop_id is not None:
            winner = cuts[drop_id]
            wrow = next((r for r in final if r["identity"] == winner), None)
            if wrow is not None:
                s = (f"⚠ 被帶內去重淘汰（同帶贏家 S={wrow['_score']:g} "
                     f"${wrow['_cost']:.4f} CP={wrow['_cp']:.1f} {winner}）")
            else:
                s = f"⚠ 被帶內去重淘汰（同帶贏家 {winner}）"
            if _is_claude(drop_id):
                s += "；⚠ Claude-family 永不推薦（禁令 14）"
            return s
    peak = max(final, key=lambda r: r["_cp"], default=None)
    if peak is None:
        return "⚠ 不在表上（空表，無 CP 峰值建議）"
    s = (f"⚠ 不在表上，建議 CP 峰值 {peak['identity']}（S={peak['_score']:g} "
         f"${peak['_cost']:.4f} CP={peak['_cp']:.1f}）")
    if _is_claude(peak["identity"]):
        s += "；⚠ Claude-family 永不推薦（禁令 14）"
    return s


def load_config_refs(path):
    """Return {model?, general?, explore?} refs; {} + stderr warning on error."""
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            cfg = json.load(f)
        out = {}
        if isinstance(cfg.get("model"), str) and cfg["model"].strip():
            out["model"] = cfg["model"].strip()
        agents = cfg.get("agents") or {}
        if isinstance(agents, dict):
            for k in ("general", "explore"):
                sub = agents.get(k)
                m = sub.get("model") if isinstance(sub, dict) else None
                if isinstance(m, str) and m.strip():
                    out[k] = m.strip()
        return out
    except Exception as e:
        print(f"WARNING: cannot load config refs from {path}: {e}",
              file=sys.stderr)
        return {}


def group_rows(paid):
    groups = defaultdict(list)
    for r in paid:
        groups[(r["benchmark"], r["benchmark_version"],
                r["cost_basis"])].append(r)
    return dict(groups)


def _stat(r, key, money=False):
    v = r.get(key)
    if not isinstance(v, (int, float)):
        return "?"
    if money:
        return f"${v:.4f}"
    if key == "_cp":
        return f"{v:.1f}"
    return f"{v:g}"


def grade_of(r):
    notes = (r.get("notes") or "")
    if notes.startswith("GRADE-A"):
        return "A"
    if notes.startswith("GRADE-B"):
        return "B"
    return "GRADE未知"


# ---------------------------------------------------------- Step 3: CLI/render

def parse_args():
    p = argparse.ArgumentParser(description="Efficiency ladder display layer")
    p.add_argument("--input", required=True, help="candidates.csv path")
    p.add_argument("--min-score", type=float, required=True,
                   help="minimum intelligence floor (required, no default)")
    p.add_argument("--max-cost", type=float, default=None)
    p.add_argument("--eps-score", type=float, default=2.0)
    p.add_argument("--eps-cp", type=float, default=0.05)
    p.add_argument("--config",
                   default="~/.config/opencode/opencode.json")
    p.add_argument("--output", default=None,
                   help="write ladder.md here (default stdout)")
    return p.parse_args()


def main():
    args = parse_args()
    with open(args.input, newline="", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))

    required = ["identity", "benchmark", "benchmark_version", "cost_per_task",
                "cost_basis", "privacy", "provider"]
    for col in required:
        if col not in (raw[0].keys() if raw else []):
            print(f"ERROR: missing column '{col}' in {args.input}",
                  file=sys.stderr)
            sys.exit(2)

    paid = [r for r in raw if not cf.is_free_row(r)]
    for r in paid:
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

    groups = group_rows(paid)

    out = [f"# Ladder（as-of run: `{args.input}`)",
           f"- min-score={args.min_score:g}, max-cost="
           f"{args.max_cost if args.max_cost is not None else 'none'}, "
           f"eps_score={args.eps_score:g}（規約預設；AA 當版 CI 未公布則沿用上一版）, "
           f"eps_cp={args.eps_cp * 100:.1f}%（成本側容忍度，固定）",
           "- 去重規則：0.5eps 連帶＋pinned（全表最高分行＋最高 CP 行自動 pinned，不參與被砍）",
           "- privacy：純註記（2026-09-24 取消分桶；evidence_url + checked_date 見行，不分組不過濾）",
           ""]
    if not groups:
        out.append("_No paid candidates._")

    all_final, all_cuts, by_ident = [], {}, {}
    for key in sorted(groups):
        bench, ver, basis = key
        kept, excluded = cf.compute_one_group(
            groups[key], args.min_score, args.max_cost,
            args.eps_score, args.eps_cp)
        for r, _ in kept:
            by_ident[r["identity"]] = r
        final, cuts = dedup_bands([r for r, _ in kept], args.eps_score)
        all_final.extend(final)
        all_cuts.update(cuts)
        for r in final:
            by_ident[r["identity"]] = r

        out.append(f"## 階梯表：{bench} @ {ver} | basis={basis} "
                   f"(n={len(final)})")
        out.append("| # | Score | Cost/task | CP | Identity | GRADE | 註記 |")
        out.append("|---|---|---|---|---|---|---|")
        for i, r in enumerate(final, 1):
            out.append(
                f"| {i} | {r['_score']:g} | ${r['_cost']:.4f} | {r['_cp']:.1f} "
                f"| {r['identity']} | {grade_of(r)} | {(r.get('notes') or '').strip()} |")
        out.append("")
        if cuts:
            out.append(f"### Cut 名單（{len(cuts)}）")
            for drop, win in cuts.items():
                d = by_ident.get(drop, {})
                w = by_ident.get(win, {})
                out.append(
                    f"- {drop} (S={_stat(d, '_score')}, "
                    f"CP={_stat(d, '_cp')} | {grade_of(d)}) → "
                    f"同帶贏家 {win} (S={_stat(w, '_score')}, "
                    f"CP={_stat(w, '_cp')} | {grade_of(w)})")
            out.append("")
        if excluded:
            out.append(f"<details><summary>Excluded sample "
                       f"({len(excluded)}, top 5)</summary>\n")
            for r, reason in excluded[:5]:
                out.append(f"- {r['identity']} (S={r['_score']:g}, "
                           f"${r['_cost']:.4f}): {reason}")
            out.append("</details>\n")

    b_rows = [r for r in all_final if grade_of(r) == "B"]
    b_wins = sorted({w for w in all_cuts.values()
                     if grade_of(by_ident.get(w, {})) == "B"})
    if b_rows or b_wins:
        out.append("## B-caveat（禁令 9）")
        if b_rows:
            out.append(f"- B 級行在表上：{', '.join(r['identity'] for r in b_rows)}")
        if b_wins:
            out.append(f"- B 級行決定 cut：{', '.join(b_wins)}（推導價參戰，公式＋假設見該行註記）")
        out.append("")

    refs = load_config_refs(args.config)
    out.append(f"## 配置驗證（config: `{args.config}`）")
    if not refs:
        out.append("（跳過：config 缺失、無效或無 refs；見 stderr 警告，exit 0）")
    else:
        labels = (("model", "root"), ("general", "general"),
                  ("explore", "explore"))
        for k, label in labels:
            if k in refs:
                out.append(f"- {label} `{refs[k]}` → "
                           f"{verify_ref(refs[k], all_final, all_cuts)}")
    out.append("")

    text = "\n".join(out)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
