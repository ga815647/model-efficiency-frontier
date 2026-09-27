#!/usr/bin/env python3
"""NONPRODUCTION two-axis tradeoff diagnostic for one immutable AA snapshot.

This is not the frozen CP-new-high ladder, a new recommendation policy, or an
AA cost estimator. The only price transformation is ladder_extra.adjust_rows.
"""

import argparse
import html
import json
import math
import shlex
import sys
from pathlib import Path

from ladder_extra import adjust_rows, grade_of, load_rows, _is_claude


def _dominates(a, b):
    return (a["_score"] >= b["_score"] and a["_cost"] <= b["_cost"]
            and (a["_score"] > b["_score"] or a["_cost"] < b["_cost"]))


def _item(row):
    return dict(identity=row["identity"], score=row["_score"],
                cost_orig=row["_cost_orig"], cost_adj=row["_cost"],
                factor=row["_factor"], grade=grade_of(row),
                notes=row.get("notes") or "", checked_date=row.get("checked_date") or "",
                evidence_url=row.get("evidence_url") or "",
                comparison_only=_is_claude(row["identity"]))


def analyze(rows, *, min_score, eps_score):
    """Exact Pareto dominance; keep equivalent routes and all small upgrades."""
    if not math.isfinite(min_score) or not math.isfinite(eps_score) or eps_score <= 0:
        raise ValueError("min_score must be finite and eps_score finite and positive")
    groups = {(r["benchmark"], r["benchmark_version"], r["cost_basis"]) for r in rows}
    if len(groups) > 1:
        raise ValueError("requires a single benchmark, version and cost basis")
    selected = [r for r in rows if r["_score"] >= min_score]
    # A dominated witness must itself be retained: a finite partial order
    # always has a maximal witness. Choose the cheapest, then strongest.
    frontier = [r for r in selected if not any(_dominates(other, r) for other in selected)]
    by_cost = sorted(frontier, key=lambda r: (r["_cost"], -r["_score"], r["identity"]))
    upgrades = {}
    cheaper = None
    for r in by_cost:
        if cheaper is not None and r["_cost"] > cheaper["_cost"]:
            delta = r["_score"] - cheaper["_score"]
            upgrades[r["identity"]] = dict(cheaper_identity=cheaper["identity"],
                                           delta_score=delta,
                                           cost_multiple=r["_cost"] / cheaper["_cost"],
                                           delta_cost_adj=r["_cost"] - cheaper["_cost"],
                                           within_noise=delta < eps_score)
        else:
            upgrades[r["identity"]] = None
        # Equal-cost peers are equivalent and compare against the same cheaper
        # point, not against each other.
        if cheaper is None or r["_cost"] > cheaper["_cost"]:
            cheaper = r
    retained = []
    for r in by_cost:
        item = _item(r)
        item["upgrade"] = upgrades[r["identity"]]
        retained.append(item)
    dominated = []
    for r in sorted((r for r in selected if r not in frontier),
                    key=lambda r: (-r["_score"], r["_cost"], r["identity"])):
        witness = next(w for w in by_cost if _dominates(w, r))
        item = _item(r)
        item["witness"] = witness["identity"]
        dominated.append(item)
    result = dict(group=list(next(iter(groups))) if groups else None,
                  source_dates=sorted({r.get("checked_date", "") for r in rows
                                       if r.get("checked_date")}),
                  policy=dict(min_score=min_score, eps_score=eps_score,
                              dominance="score >= and cost_adj <=, at least one strict",
                              scenario="GPT / factor; Grok / grok_factor; Contributor ×1"),
                  counts=dict(input=len(rows), potential_tradeoffs=len(retained),
                              dominated=len(dominated)),
                  retained=retained, dominated=dominated)
    if len(selected) != len(rows):
        result["floor_excluded"] = [_item(r) for r in rows if r not in selected]
        result["counts"]["floor_excluded"] = len(rows) - len(selected)
    return result


def _num(value):
    return f"{value:,.6g}"


def _h(value):
    return html.escape(str(value), quote=True)


def _md(value):
    return _h(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _context(result, source):
    group = result["group"] or ["未提供", "未提供", "未提供"]
    dates = ", ".join(result["source_dates"]) or "未提供"
    reason = result["policy"].get("min_score_reason", "未提供")
    return (f"來源快照 {dates}（不是本報告日期新抓取）；來源檔 {source}；"
            f"{group[0]} / {group[1]}（公開榜單版本由同日 release 跨頁推定，"
            f"非榜單標示或 API envelope 證明）/ {group[2]}；"
            f"min-score={_num(result['policy']['min_score'])}（{reason}）；"
            f"eps_score={_num(result['policy']['eps_score'])}，本版 CI 未公布，沿用規約。")


def _upgrade_text(item):
    u = item["upgrade"]
    if u is None:
        return "最低情境成本／同價等價路線；無更便宜比較對象"
    label = "分差未越噪音門檻" if u["within_noise"] else "分數差異達門檻"
    return (f"相較 {u['cheaper_identity']}：ΔScore +{_num(u['delta_score'])}；"
            f"情境成本 ×{_num(u['cost_multiple'])}；"
            f"ΔCost_adj +${_num(u['delta_cost_adj'])}/AA task；{label}")


def render_markdown(result, source):
    c = result["counts"]
    factor = _num(result["policy"].get("factor", 18))
    grok_factor = _num(result["policy"].get("grok_factor", 16))
    lines = ["# 選擇地形｜雙軸取捨試驗（非正式推薦）", "",
             _md(_context(result, source)), "",
             f"**輸入 {c['input']} · 潛在取捨 {c['potential_tradeoffs']} · 被支配 {c['dominated']}**",
             "", "本試驗只移除同時不較強且不較便宜的行（至少一軸嚴格較差）。"
             "同 Score／同 Cost_adj 的不同 route 全保留；與正式 CP-new-high 階梯可刻意不同。"
             "不設 5% 效用刪除門檻，不鏈式刪除微幅升級。Claude 僅比較，不推薦。", "",
             f"Cost_adj = Cost_orig / 情境係數：GPT ×{factor}（預設 ×18 源自個人約 ×18.9 實測保守取整；當次係數非實測），"
             f"Grok ×{grok_factor} 為用戶指定情境（非實測）；Contributor ×1。"
             "這些不是實際 API 價格或 AA 實測調整價。原價證據 GRADE-B 仍有推導假設，"
             "Contributor cache-write 以一般 input 價計是未經 Meta 明確證實的關鍵假設。", "",
             "ΔScore < eps_score 只標記『分差未越噪音門檻』；達門檻也不證明實務能力不同，"
             "未達也不證明能力相同。所有保留點仍完整列出。", "",
             "## 全部潛在取捨（Score 降序；升級基準是緊鄰的更便宜保留價位）", "",
             "| # | Identity | Score | Cost_adj $/AA task | Cost_orig $/AA task | 係數 | 證據 | 對更便宜點的升級 |",
             "|---:|---|---:|---:|---:|---:|---|---|"]
    for i, r in enumerate(sorted(result["retained"],
                                 key=lambda r: (-r["score"], r["cost_adj"], r["identity"])), 1):
        lines.append(f"| {i} | {_md(r['identity'])}{'（Claude：僅比較）' if r['comparison_only'] else ''} "
                     f"| {_num(r['score'])} | {_num(r['cost_adj'])} | {_num(r['cost_orig'])} "
                     f"| ×{_num(r['factor'])} | {_md(r['grade'])} | {_md(_upgrade_text(r))} |")
    lines += ["", f"## 被支配行（{len(result['dominated'])}；每行附實際支配者）", ""]
    for r in result["dominated"]:
        lines.append(f"- {_md(r['identity'])}（Score {_num(r['score'])}、Cost_adj "
                     f"${_num(r['cost_adj'])}、Cost_orig ${_num(r['cost_orig'])}、"
                     f"GRADE {_md(r['grade'])}）← {_md(r['witness'])}")
    if not result["dominated"]:
        lines.append("- 無")
    if result.get("floor_excluded"):
        lines += ["", "## 低於指定 min-score 的行（非支配刪除）", ""]
        lines += [f"- {_md(r['identity'])}" for r in result["floor_excluded"]]
    lines += ["", "詳細全精度數據與每行 notes／URL 見 result.json。"
              "來源研究限制見原 run-notes.md；本試驗沒有擷取新資料，亦不取代正式三 picks。", ""]
    return "\n".join(lines)


def render_html(result, source):
    c = result["counts"]
    factor = _h(_num(result["policy"].get("factor", 18)))
    grok_factor = _h(_num(result["policy"].get("grok_factor", 16)))
    show = []
    noise = []
    for r in sorted(result["retained"],
                    key=lambda r: (-r["score"], r["cost_adj"], r["identity"])):
        u = r["upgrade"]
        item = (f'<article class="step"><div class="step-top"><span class="score">'
                f'{_h(_num(r["score"]))}<small> score</small></span>'
                f'<span class="cost">${_h(_num(r["cost_adj"]))}<small> / AA task · 情境</small></span></div>'
                f'<h3>{_h(r["identity"])}</h3><p class="upgrade">{_h(_upgrade_text(r))}</p>'
                f'<p class="meta">原價 ${_h(_num(r["cost_orig"]))} · ×{_h(_num(r["factor"]))}'
                f' · GRADE {_h(r["grade"])}'
                f'{" · Claude：僅比較，絕不推薦" if r["comparison_only"] else ""}</p></article>')
        (noise if u and u["within_noise"] else show).append(item)
    rows = []
    for i, r in enumerate(sorted(result["retained"],
                                 key=lambda r: (-r["score"], r["cost_adj"], r["identity"])), 1):
        rows.append(f'<tr><td>{i}</td><th scope="row">{_h(r["identity"])}'
                    f'{" · 僅比較" if r["comparison_only"] else ""}</th>'
                    f'<td>{_h(_num(r["score"]))}</td><td>${_h(_num(r["cost_adj"]))}</td>'
                    f'<td>${_h(_num(r["cost_orig"]))}</td><td>×{_h(_num(r["factor"]))}</td>'
                    f'<td>{_h(r["grade"])}</td><td>{_h(_upgrade_text(r))}</td></tr>')
    dropped = []
    for r in result["dominated"]:
        dropped.append(f'<li><strong>{_h(r["identity"])}</strong> · Score {_h(_num(r["score"]))}'
                       f' · Cost_adj ${_h(_num(r["cost_adj"]))} · Cost_orig '
                       f'${_h(_num(r["cost_orig"]))} · GRADE {_h(r["grade"])}'
                       f' ← 實際支配者 <strong>{_h(r["witness"])}</strong></li>')
    floor = result.get("floor_excluded", [])
    evidence = []
    for r in result["retained"] + result["dominated"]:
        if r["grade"] == "B":
            url = r["evidence_url"]
            safe_url = url if url.startswith(("https://", "http://")) else "非 HTTP(S) 證據 URL，未顯示"
            evidence.append(f'<li><strong>{_h(r["identity"])}</strong> · {_h(r["notes"])}'
                            f' · URL: {_h(safe_url)}</li>')
    floor_section = (f'<details><summary>低於 min-score（{len(floor)}；非支配刪除）</summary>'
                     f'<ul>{"".join("<li>" + _h(r["identity"]) + "</li>" for r in floor)}</ul></details>'
                     if floor else "")
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>選擇地形 · 2026-09-26 歷史快照試驗</title>
<style>
:root {{ color-scheme: light; --ink:#142837; --muted:#526674; --bg:#f4f5ee; --card:#fffefa; --line:#d5dcd6; --accent:#086b61; --warm:#b85f35; }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.6 system-ui,-apple-system,'Noto Sans TC',sans-serif }}
main {{ max-width:1100px; margin:auto; padding:clamp(20px,4vw,54px) }}
.eyebrow {{ text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; color:var(--accent) }}
h1,h2,h3 {{ line-height:1.2 }} h1 {{ font-size:clamp(2.15rem,5vw,4rem); margin:.2em 0 }} h2 {{ margin:2.2em 0 .6em; font-size:1.5rem }} h3 {{ margin:.25em 0 .5em; font-size:1.05rem; overflow-wrap:anywhere }}
.lead {{ max-width:74ch; font-size:1.08rem }} .muted,.meta {{ color:var(--muted) }} .meta {{ font-size:.83rem }}
.source {{ border-left:4px solid var(--accent); padding:10px 16px; background:#eaf0eb; overflow-wrap:anywhere }}
.stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:30px 0 }}
.stat {{ background:var(--ink); color:white; padding:18px; border-radius:12px }} .stat b {{ display:block; font-size:clamp(1.7rem,4vw,2.6rem); line-height:1.1 }} .stat span {{ font-size:.85rem; opacity:.8 }}
.steps {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr)); gap:12px }}
.step {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:17px; break-inside:avoid }}
.step-top {{ display:flex; justify-content:space-between; gap:12px; font-variant-numeric:tabular-nums }} .score {{ font-size:1.6rem; font-weight:800 }} .cost {{ color:var(--accent); font-size:1.3rem; font-weight:750; text-align:right }}
small {{ display:block; font-size:.66rem; font-weight:500; color:var(--muted) }} .upgrade {{ border-top:1px solid var(--line); padding-top:9px; margin-bottom:4px; font-size:.91rem }}
details {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 16px; margin:16px 0 }} summary {{ cursor:pointer; font-weight:750 }} details .steps {{ margin-top:16px }}
.scroll {{ overflow-x:auto; background:var(--card); border-radius:10px; border:1px solid var(--line) }} table {{ border-collapse:collapse; width:100%; min-width:880px; font-size:.83rem }} th,td {{ text-align:left; vertical-align:top; padding:10px; border-bottom:1px solid var(--line) }} thead {{ background:#e5ede8; position:sticky; top:0 }} tbody tr:nth-child(even) {{ background:#f5f7f2 }} td:nth-child(3),td:nth-child(4),td:nth-child(5) {{ white-space:nowrap; font-variant-numeric:tabular-nums }}
ul {{ padding-left:1.4em }} li {{ margin:.5em 0; overflow-wrap:anywhere }} .note {{ background:#fff1e7; border-left:4px solid var(--warm); padding:12px 16px; margin:18px 0 }}
@media(max-width:640px) {{ .stats {{ gap:6px }} .stat {{ padding:11px }} .stat span {{ font-size:.7rem }} }}
@media print {{ body {{ background:white; font-size:10pt }} main {{ max-width:none; padding:0 }} .stat {{ color:var(--ink); background:#eee }} details {{ break-inside:auto }} details:not([open]) > *:not(summary) {{ display:block }} .steps {{ grid-template-columns:repeat(2,1fr) }} thead {{ position:static }} }}
</style></head><body><main>
<header><p class="eyebrow">Historical snapshot / diagnostic only</p><h1>選擇地形</h1><p class="lead">哪一階值得保留？先把所有真實的價格／分數取捨攤開，再看每次升級多花多少。這不是正式推薦，也沒有 5% 效用刪除門檻。</p>
<p class="source">{_h(_context(result, source))}</p></header>
<section class="stats" aria-label="試驗數量"><div class="stat"><b>{c['input']}</b><span>輸入候選</span></div><div class="stat"><b>{c['potential_tradeoffs']}</b><span>潛在取捨</span></div><div class="stat"><b>{c['dominated']}</b><span>被雙軸支配</span></div></section>
<p class="note">Cost_adj = Cost_orig ÷ 情境係數，不是實際 API 報價。GPT ×{factor}（預設 ×18 源於個人約 ×18.9 實測的保守取整；當次係數非實測）；Grok ×{grok_factor} 是用戶指定情境、非實測；Contributor ×1。原價 GRADE-B 為推導值，其 cache-write 以一般 input 價計仍是未獲 Meta 明確確認的假設。Claude 全部僅比較，絕不推薦。</p>
<section><h2>逐階升級 · 看得到代價</h2><p class="muted">每張卡對照「緊鄰的更便宜保留價位」，不是與正式 ladder 階梯相比。ΔScore &lt; {_h(_num(result['policy']['eps_score']))} 只表示未越噪音門檻；兩側皆非能力相等／不同的實務證明。最高分高價選項保留供比較。</p><div class="steps">{''.join(show)}</div>
<details><summary>分差未越噪音門檻 · {len(noise)} 項（完整保留，點開看升級）</summary><div class="steps">{''.join(noise)}</div></details></section>
<section><h2>全部潛在取捨 · Score 降序</h2><p class="muted">全表不折疊；同分同價的不同 route 各佔一行。數字為顯示取整；完整精度見 result.json。</p>
<div class="scroll"><table><thead><tr><th>#</th><th>Identity</th><th>Score</th><th>Cost_adj $/AA task</th><th>Cost_orig $/AA task</th><th>係數</th><th>GRADE</th><th>相較更便宜點</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section><h2>支配關係與證據</h2><p class="muted">只有 Score 不低且 Cost_adj 不高、至少一軸嚴格較好的候選才可作支配者。沒有按 CP 或相近分數刪行。</p>
<details><summary>被支配 {len(dropped)} 行 · 展開全部實際 witness</summary><ul>{''.join(dropped)}</ul></details>{floor_section}
<details><summary>GRADE-B 原價證據與假設 · {len(evidence)} 行</summary><ul>{''.join(evidence)}</ul></details></section>
<footer class="muted"><p>僅 2026-09-26 公開快照的離線情境重算；公開版號由跨頁推定。原價、版本限制、GRADE-B 假設詳見原 run-notes.md。沒有新資料擷取，亦不取代正式 CP-new-high 或三 picks。可列印；所有資源內嵌，無 CDN、字體下載或 JavaScript。</p></footer>
</main></body></html>'''


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--factor", type=float, default=18)
    parser.add_argument("--grok-factor", type=float, default=16)
    parser.add_argument("--eps-score", type=float, default=2)
    parser.add_argument("--min-score", type=float, required=True)
    parser.add_argument("--min-score-reason", required=True)
    args = parser.parse_args(argv)
    if not args.min_score_reason.strip():
        parser.error("--min-score-reason must not be blank")
    for key in ("factor", "grok_factor", "eps_score"):
        value = getattr(args, key)
        if not math.isfinite(value) or value <= 0:
            parser.error(f"--{key.replace('_','-')} must be finite and positive")
    if not math.isfinite(args.min_score):
        parser.error("--min-score must be finite")
    return args


def main(argv=None):
    args = parse_args(argv)
    out = Path(args.output_dir)
    try:
        if out.exists():
            raise ValueError(f"output directory already exists: {out}")
        rows = adjust_rows(load_rows(args.input), factor=args.factor,
                           grok_factor=args.grok_factor)
        result = analyze(rows, min_score=args.min_score, eps_score=args.eps_score)
        result["policy"].update(factor=args.factor, grok_factor=args.grok_factor,
                                min_score_reason=args.min_score_reason)
        result["source"] = str(args.input)
        md = render_markdown(result, args.input)
        page = render_html(result, args.input)
        readme = ("# 雙軸取捨：非正式歷史快照試驗\n\n"
                  "開啟 [report.html](report.html) 看自包含視覺報告；[report.md](report.md) "
                  "為完整文字表，[result.json](result.json) 為全精度機器可讀數據。"
                  "這不是正式 ladder / 三 picks；沒有抓取新資料或改寫原 run。\n\n"
                  "## 重算（請用新目錄，不覆寫本快照）\n\n"
                  "```sh\npython3 scripts/tradeoff_trial.py "
                  f"--input {args.input} --output-dir /tmp/opencode/tradeoff-replay "
                  f"--factor {args.factor:g} --grok-factor {args.grok_factor:g} "
                  f"--eps-score {args.eps_score:g} --min-score {args.min_score:g} "
                  f"--min-score-reason {shlex.quote(args.min_score_reason)}\n```\n\n"
                  "原價／推定版本及 Contributor cache-write 假設詳見 "
                  "`runs/2026-09-26-general-grok16/run-notes.md`。\n")
        out.mkdir(parents=True, exist_ok=False)
        (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                                allow_nan=False) + "\n", encoding="utf-8")
        (out / "report.md").write_text(md, encoding="utf-8")
        (out / "report.html").write_text(page, encoding="utf-8")
        (out / "README.md").write_text(readme, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
