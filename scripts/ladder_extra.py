#!/usr/bin/env python3
"""Personal GPT ×18 / user-specified Grok ×16 scenario; source stays intact.

Public interfaces for the renderer:
  parse_args(argv=None) -> argparse.Namespace
  load_rows(path) -> list[dict] (raw CSV strings, required columns checked)
  adjust_rows(rows, factor=18, prefix="GPT-", grok_factor=16) -> new paid
      rows with _score, _cost_orig, _cp_orig, _cost, _factor; originals unchanged.
  compute_groups(rows, args) -> dict[(benchmark, version, basis), dict] with
      kept: [(row, reason)], final: [row], cuts: {drop: winner},
      excluded: [(row, reason)]. Input rows must be from adjust_rows;
      frozen math adds _cp to rows it evaluates (excluded floor/cap rows
       can lack _cp). Final and rendered table are score-desc.
"""

import argparse
import csv
from datetime import date
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import compute_frontier as cf
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.meta_availability import unavailable_reason


def parse_args(argv=None):
    """Parse scenario options; argparse errors exit 2 (including ladder.md)."""
    p = argparse.ArgumentParser(description="Personal usage-factor ladder scenario")
    p.add_argument("--input", required=True)
    p.add_argument("--output")
    p.add_argument("--factor", type=float, default=18)
    p.add_argument("--prefix", default="GPT-")
    p.add_argument("--grok-factor", type=float, default=16)
    p.add_argument("--min-score", type=float, required=True)
    p.add_argument("--min-score-reason")
    p.add_argument("--max-cost", type=float)
    p.add_argument("--eps-score", type=float, default=2.0)
    p.add_argument("--eps-cp", type=float, default=0.05)
    p.add_argument("--monthly-tasks", type=float)
    p.add_argument("--subscription-total", type=float, default=79)
    args = p.parse_args(argv)
    for field, minimum in (("factor", "positive"), ("grok_factor", "positive"),
                           ("min_score", "finite"),
                           ("max_cost", "positive"), ("eps_score", "positive"),
                           ("eps_cp", "nonnegative"), ("monthly_tasks", "nonnegative"),
                           ("subscription_total", "positive")):
        value = getattr(args, field)
        if value is not None and (not math.isfinite(value)
                                  or minimum == "positive" and value <= 0
                                  or minimum == "nonnegative" and value < 0):
            p.error(f"--{field.replace('_', '-')} must be finite"
                    + (f" and {minimum}" if minimum != "finite" else ""))
    if not args.prefix:
        p.error("--prefix must not be empty")
    if args.output and args.output.replace("\\", "/").rstrip("/").split("/")[-1] == "ladder.md":
        p.error("--output must not overwrite ladder.md")
    return args


def load_rows(path):
    """Read CSV without changing values; reject incomplete required fields."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = ("identity", "score", "benchmark", "benchmark_version",
                    "cost_per_task", "cost_basis", "privacy", "provider")
        for column in required:
            if column not in (reader.fieldnames or ()):
                raise ValueError(f"missing column '{column}' in {path}")
        rows = list(reader)
        for number, row in enumerate(rows, 2):
            if str(row.get("is_free") or "").strip().lower() in ("true", "1", "yes", "y"):
                continue
            for column in ("identity", "score", "cost_per_task", "benchmark",
                           "benchmark_version", "cost_basis"):
                if not isinstance(row.get(column), str) or not row[column].strip():
                    raise ValueError(f"{path} row {number}: missing {column}")
        return rows


def _grok(row):
    return bool(re.match(r"^grok(?:$|[^a-z0-9])", row["identity"], re.IGNORECASE))


def adjust_rows(rows, factor=18, prefix="GPT-", grok_factor=16):
    """Build independent paid-row copies with original and scenario costs."""
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("factor must be finite and positive")
    if not math.isfinite(grok_factor) or grok_factor <= 0:
        raise ValueError("grok_factor must be finite and positive")
    result = []
    for source in rows:
        if str(source.get("is_free") or "").strip().lower() in ("true", "1", "yes", "y"):
            continue
        if not isinstance(source.get("identity"), str) or not source["identity"].strip():
            raise ValueError("paid row missing identity")
        try:
            s, c = float(source["score"]), float(source["cost_per_task"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f"invalid paid score/cost: {source.get('identity')}") from exc
        if not math.isfinite(s) or not math.isfinite(c) or c <= 0:
            raise ValueError(f"invalid paid score/cost: {source.get('identity')}")
        if cf.is_free_row(source):
            continue
        r = dict(source)
        # Contributor remains at its documented original price, even if its
        # model name happens to belong to a scenario family.
        applied = (1 if _contributor(r) else factor if r["identity"].startswith(prefix)
                   else grok_factor if _grok(r) else 1)
        cost_adj = c / applied
        cp_orig = s / c
        cp_adj = s / cost_adj if cost_adj else float("inf")
        if not (math.isfinite(cost_adj) and cost_adj > 0
                and math.isfinite(cp_orig) and math.isfinite(cp_adj)):
            raise ValueError(f"invalid adjusted cost/CP: {r['identity']}")
        r.update(_score=s, _cost_orig=c, _cp_orig=cp_orig, _cost=cost_adj,
                 _factor=applied)
        result.append(r)
    return result


# Small display-layer helpers copied from ladder.py; intentionally no ladder import.
# Extra-only divergence: two pinned rows in a two-row band both survive.
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
            if all(r["identity"] in pinned for r in b):
                final.extend(b)
                continue
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


def group_rows(paid):
    groups = defaultdict(list)
    for r in paid:
        groups[(r["benchmark"], r["benchmark_version"],
                r["cost_basis"])].append(r)
    return dict(groups)


def grade_of(r):
    notes = (r.get("notes") or "")
    if notes.startswith("GRADE-A"):
        return "A"
    if notes.startswith("GRADE-B"):
        return "B"
    return "GRADE未知"


CLAUDE_FAMS = ("claude", "opus", "fable", "sonnet", "haiku")


def _is_claude(identity):
    return any(t in CLAUDE_FAMS for t in re.sub(
        r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (identity or "").lower())).strip().split())


def compute_groups(rows, args):
    """Compute each paid scenario group with frozen math, then band-dedup."""
    results = {}
    for key, members in group_rows(rows).items():
        available, unavailable = [], []
        for row in members:
            reason = unavailable_reason(row)
            if reason:
                unavailable.append((row, reason))
            else:
                available.append(row)
        kept, excluded = cf.compute_one_group(available, args.min_score,
                                               args.max_cost, args.eps_score, args.eps_cp)
        excluded.extend(unavailable)
        final, cuts = dedup_bands([r for r, _ in kept], args.eps_score)
        results[key] = dict(kept=kept, final=final, cuts=cuts, excluded=excluded)
    return results


def api_comparison(cost_orig, monthly_tasks, subscription_total):
    """Compare a hypothetical full-month API bill, never an assumed N=0."""
    formula = f'N × ${cost_orig:g} vs ${subscription_total:g}'
    if monthly_tasks is None:
        return f'N 未定，只給公式不給結論：{formula}'
    monthly_api = monthly_tasks * cost_orig
    if not math.isfinite(monthly_api):
        raise ValueError('monthly API cost overflow: N × Cost_orig must be finite')
    choice = '開外部API' if monthly_api < subscription_total else '續訂閱'
    return (f'{choice}（此用量假設下）：{monthly_tasks:g} × ${cost_orig:g} '
            f'= ${monthly_api:g} vs ${subscription_total:g}')


def _cp_adj(row):
    # Frozen math does not attach _cp to rows excluded at floor/cap.
    return row.get("_cp", row["_score"] / row["_cost"])


def _reason(reason):
    """The frozen calculator calls adjusted CP simply 'CP'; relabel for readers."""
    return re.sub(r"\bCP\b", "CP_adj", reason)


def _safe(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _contributor(row):
    return ("contributor" in (row.get("pricing_plan") or "").lower()
             or "contributor" in row["identity"].lower())


def _scenario_label(row, args):
    if row["_factor"] == 1:
        return "×1"
    return (f"GPT ×{args.factor:g}" if row["identity"].startswith(args.prefix)
            else f"Grok ×{args.grok_factor:g}")


def _stat(row):
    return f"S={row['_score']:g}, Cost_orig=${row['_cost_orig']:.4f}, CP_orig={row['_cp_orig']:.2f}, CP_adj={_cp_adj(row):.2f}"


def _pick(label, row):
    if row is None:
        return f"- {label}：從缺（無非 Claude 的階梯候選）"
    return f"- {label}：{_safe(row['identity'])}（S={row['_score']:g}, CP_adj={_cp_adj(row):.2f}）"


def select_picks(final: list[dict]) -> dict:
    """Select the existing three non-Claude final rows, without changing tie breaks."""
    pickable = [r for r in final if not _is_claude(r["identity"])]
    by_score = sorted(pickable, key=lambda r: (-r["_score"], r["_cost"]))
    return {
        "strong": by_score[0] if by_score else None,
        "middle": by_score[len(by_score) // 2] if by_score else None,
        "cheap": min(pickable, key=lambda r: (-r["_cp"], -r["_score"], r["_cost"]))
        if pickable else None,
    }


def render(groups, rows, args, title="# 番外篇 / 個人實測係數估算；Notion 主展示（非官方 AA 成本）"):
    """Render each benchmark/version/basis independently; final remains score-desc."""
    source_dates = sorted({(r.get("checked_date") or "").strip() for r in rows
                           if (r.get("checked_date") or "").strip()})
    all_urls = {(r.get("evidence_url") or "").strip() for r in rows
                if (r.get("evidence_url") or "").strip()}
    aa_urls = {url for url in all_urls if "artificialanalysis.ai" in url}
    urls = sorted(aa_urls or all_urls)
    pricing_urls = sorted(all_urls - set(urls))
    reason = args.min_score_reason or (
        "同版本候選全量情境比較，floor=0；實際來源日期以快照欄位為準"
        if args.min_score == 0 else "使用者指定門檻；未另提供門檻理由")
    out = [title,
           f"- 原因：ChatGPT 訂閱用好用滿，個人實測約 18.9 倍 API 用量；預設保守取整採 ×18（本次 ×{args.factor:g}），並非實測 18，也非 AA 實測。",
             f"- 細節：factor={args.factor:g}（GPT 預設 ×18；原始實測約 18.9），prefix={_safe(args.prefix)}；grok-factor={args.grok_factor:g}（Grok 預設 ×16：使用者指定情境，非實測、非 AA 實測）；GPT 訂閱 $20+$59 組合（預設合計 $79）；各家匹配行 cost_adj=cost_orig/該行係數、CP_adj=CP_orig×該行係數，其他及 Contributor ×1；N 用滿水位由使用者指定。",
            "- CP_orig、CP_adj 由原始未四捨五入的 Score 與 Cost_orig 計算，表中數字僅供顯示時取整。",
           f"- 不進正式表：正式表 `{Path(args.input).parent / 'ladder.md'}` 保持原狀；此為獨立情境估算。",
            f"- 來源快照日期（checked_date）：{', '.join(source_dates) if source_dates else '未提供'}；生成日期：{date.today().isoformat()}；來源檔：`{args.input}`。生成報表不執行抓取；資料取得日期以輸入快照及其 notes 為準。",
           f"- benchmark 來源 URL：{', '.join(urls) if urls else '未提供（空快照）'}",
           f"- min-score={args.min_score:g}（floor 理由：{_safe(reason)}）；max-cost={args.max_cost if args.max_cost is not None else 'none'}（以情境 cost_adj 比較）；eps_score={args.eps_score:g}（規約預設，AA CI 未公布沿用）；eps_cp={args.eps_cp * 100:g}%（固定成本側容忍度）。",
            f"- privacy：純註記（2026-09-24 取消分桶；不過濾付費行）。GRADE A/B 為原價證據等級，GPT ×{args.factor:g} 與 Grok ×{args.grok_factor:g} 皆為情境估算，不升格為 AA 實測或 GRADE-B。",
           "- `AA-median Free` 是 AA API 資料的 provider/plan 標記（跨 provider median），不是零成本 API 或可免費取得相同服務的推論；只有明確 is_free=true/yes/1/y 的行不進數字運算。",
            "- 算法按 Score 由高到低建立 CP_adj 新高與連帶去重；下表按 Score 由高到低展示（強→弱），CP_adj 為效率欄而非排序鍵。",
           ""]
    if pricing_urls:
        out.insert(next(i for i, line in enumerate(out) if line.startswith("- privacy：")),
                   f"- 其他定價／計算證據 URL：{', '.join(pricing_urls)}")
    if not groups:
        out += ["_無付費候選。_", "", "## 檔位結論", _pick("攻堅", None),
                _pick("平衡", None), _pick("省錢", None), "", "## 外部 API 試算",
                "- 從缺（無非 Claude API 價格可比較）。N 是 benchmark 等價任務量，不是一般聊天次數。", ""]
    for key, result in sorted(groups.items()):
        bench, version, basis = key
        final, cuts, excluded = result["final"], result["cuts"], result["excluded"]
        candidates = {r["identity"]: r for r, _ in result["kept"] + excluded}
        display = sorted(final, key=lambda r: (-r["_score"], r["_cost"]))
        out += [f"## 階梯表：{_safe(bench)} @ {_safe(version)} | basis={_safe(basis)} (n={len(final)}；Score 降序)",
                  "| # | Score | Cost_orig | CP_orig | CP_adj | Identity | 情境係數 | GRADE | 註記 |",
                "|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(display, 1):
            note = _safe(r.get("notes"))
            if r["_factor"] != 1:
                note += f"；情境：cost_adj=Cost_orig/{r['_factor']:g}, CP_adj=CP_orig×{r['_factor']:g}"
            out.append(f"| {i} | {r['_score']:g} | ${r['_cost_orig']:.4f} | {r['_cp_orig']:.2f} | {r['_cp']:.2f} | {_safe(r['identity'])} | {_scenario_label(r, args)} | {grade_of(r)} | {note} |")
        out.append("")
        out.append(f"### Cut 名單（{len(cuts)}）")
        for dropped, winner in cuts.items():
            r = candidates[dropped]
            w = candidates[winner]
            out.append(f"- {_safe(dropped)}（{_stat(r)}；GRADE {grade_of(r)}）→ 同帶贏家 {_safe(winner)}（{_stat(w)}；GRADE {grade_of(w)}）")
        if not cuts:
            out.append("- 無")
        out += ["", f"<details><summary>Excluded sample ({len(excluded)}, top 5)</summary>", ""]
        for r, why in excluded[:5]:
            out.append(f"- {_safe(r['identity'])}（{_stat(r)}；GRADE {grade_of(r)}）：{_safe(_reason(why))}")
        out += ["</details>", ""]

        out.append("## Contributor 狀態（所有此組 Contributor，不受 excluded top 5 節錄影響）")
        contributors = [r for r in candidates.values() if _contributor(r)]
        for r in contributors:
            identity = r["identity"]
            exclusion = next((why for e, why in excluded if e is r), None)
            if identity in cuts:
                status = f"cut → 同帶贏家 {_safe(cuts[identity])}"
            elif exclusion is not None:
                status = f"excluded：{_safe(_reason(exclusion))}"
            else:
                status = "保留階梯" if r in final else "未進最終階梯"
            out.append(f"- {_safe(identity)}（{_stat(r)}；GRADE {grade_of(r)}）：{status}；原價依據：{_safe(r.get('notes')) or '未提供'}")
        if not contributors:
            out.append("- 無 Contributor 行")
        out.append("")

        out.append("## Grok 狀態（所有此組 Grok，包含 excluded；Contributor 原價不調整）")
        groks = [r for r in candidates.values() if _grok(r)]
        for r in groks:
            identity = r["identity"]
            exclusion = next((why for e, why in excluded if e is r), None)
            if identity in cuts:
                status = f"cut → 同帶贏家 {_safe(cuts[identity])}"
            elif exclusion is not None:
                status = f"excluded：{_safe(_reason(exclusion))}"
            else:
                status = "保留階梯" if r in final else "未進最終階梯"
            out.append(f"- {_safe(identity)}（{_stat(r)}；{_scenario_label(r, args)}；GRADE {grade_of(r)}）：{status}；原價依據：{_safe(r.get('notes')) or '未提供'}")
        if not groks:
            out.append("- 無 Grok 行")
        out.append("")

        b_rows = [r for r in candidates.values() if grade_of(r) == "B"]
        if b_rows:
            out += ["### B-caveat（原價證據等級，不是情境係數的等級）",
                    "- GRADE-B 推導原價照常參戰，包括保留、決定 cut、或 CP_adj 新高而擋下其他行；其公式與假設見 notes。"
                     f" GPT ×{args.factor:g} / Grok ×{args.grok_factor:g} 調整另行標示，不冒充 AA 實測。",
                    f"- 此組 B 行：{', '.join(_safe(r['identity']) for r in b_rows)}", ""]

        picks = select_picks(final)
        strong, middle, cheap = (picks[name] for name in ("strong", "middle", "cheap"))
        out += ["## 檔位結論（僅非 Claude final）", _pick("攻堅", strong),
                _pick("平衡", middle), _pick("省錢", cheap), "",
                "## 外部 API 試算（僅情境；不影響階梯）",
                "- N 是每月 benchmark 等價任務量，不是一般聊天次數；每項 API 成本以省錢 pick 的 Cost_orig 而非 cost_adj 計。",
                 f"- 訂閱組合 $20+$59（總額 ${args.subscription_total:g}，$79 僅適用 GPT 訂閱組合假設，非 Grok 訂閱價格）。已付訂閱的增量決策不同，不能無條件建議新購／續訂。"]
        if cheap is None or basis != "api":
            out.append("- 從缺（無非 Claude API basis 省錢 pick 可作 API 價格比較）。")
        elif not cheap["identity"].startswith(args.prefix) or _contributor(cheap):
            monthly_api = (args.monthly_tasks * cheap["_cost_orig"]
                           if args.monthly_tasks is not None else None)
            if monthly_api is not None and not math.isfinite(monthly_api):
                raise ValueError("monthly API cost overflow: N × Cost_orig must be finite")
            estimate = (f"N × ${cheap['_cost_orig']:g}" if monthly_api is None else
                        f"{args.monthly_tasks:g} × ${cheap['_cost_orig']:g} = ${monthly_api:g}")
            out.append(f"- {_safe(cheap['identity'])}：API 原價試算 {estimate}；非 GPT 訂閱組合，無對應訂閱價格，不以 ${args.subscription_total:g} 判定續訂或開 API。")
        else:
            out.append(f"- {_safe(cheap['identity'])}：{api_comparison(cheap['_cost_orig'], args.monthly_tasks, args.subscription_total)}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv=None):
    args = parse_args(argv)
    source = Path(args.input)
    destination = Path(args.output) if args.output else source.parent / "ladder-extra.md"
    official = source.parent / "ladder.md"
    try:
        if (destination.name == "ladder.md" or destination.resolve().name == "ladder.md"
                or destination.resolve() == source.resolve()
                or destination.exists() and (
                    os.path.samefile(destination, source)
                    or official.exists() and os.path.samefile(destination, official))):
            raise ValueError(f"output is protected (source CSV or official ladder.md): {destination}")
        raw = load_rows(source)
        paid = adjust_rows(raw, args.factor, args.prefix, args.grok_factor)
        text = render(compute_groups(paid, args), paid, args)
        destination.write_text(text, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
