"""Self-contained, offline-readable view of the same calculated result payload."""

from html import escape


def _text(value):
    return escape('—' if value is None or value == '' else str(value), quote=True)


def _num(value, decimals=2):
    return f'{value:,.{decimals}f}'


def _row(row, rank):
    return (f'<tr data-rank="{rank}"><td class="rank">{rank}</td>'
            f'<td class="model"><strong>{_text(row["identity"])}</strong>'
            f'<small>{_text(row["effort"])} · grade {_text(row["grade"])}</small></td>'
            f'<td>{_num(row["score"])}</td><td>${_num(row["cost_orig"], 4)}</td>'
            f'<td>×{_text(row["factor"])}</td><td>{_num(row["cp_adj"])}</td></tr>')


def render_html(calculation: dict) -> str:
    """Render only payload data: no network, JavaScript, or recalculation."""
    ladder = calculation['ladder']
    picks = calculation['picks']
    statuses = calculation['candidate_statuses']
    cards = []
    for key, title, subtitle in (('strong', '攻堅', '最高分'),
                                  ('middle', '平衡', '階梯中段'),
                                  ('cheap', '省錢', '最高 CP_adj')):
        row = picks[key]
        if row:
            body = (f'<strong>{_text(row["identity"])}</strong><span>'
                    f'Score {_num(row["score"])} · CP_adj {_num(row["cp_adj"])}</span>')
        else:
            body = '<strong>從缺</strong><span>無非 Claude 階梯候選</span>'
        cards.append(f'<article class="card"><div class="eyebrow">{title} · {subtitle}</div>{body}</article>')
    def states(name, predicate):
        selected = [r for r in statuses if predicate(r)]
        items = ''.join(
            f'<li><strong>{_text(r["identity"])}</strong> <span class="badge">{_text(r["status"])}</span>'
            f'<div class="muted">Score {_num(r["score"])} · Cost_orig ${_num(r["cost_orig"],4)}'
            f' · ×{_text(r["factor"])} · CP_adj {_num(r["cp_adj"])} · GRADE {_text(r["grade"])}</div>'
            f'<p>{_text(r["reason"])}{(" → " + _text(r["winner"])) if r["winner"] else ""}</p>'
            f'<small>來源：{_text(r["source_url"])} · {_text(r["source_date"])}<br>{_text(r["notes"])}</small></li>' for r in selected)
        return f'<section class="panel"><h2>{name} 狀態 <span class="count">{len(selected)}</span></h2><ul class="states">{items}</ul></section>'
    meta = (f'{_text(calculation["benchmark"])} · {_text(calculation["benchmark_version"])}'
            f' ({_text(calculation["version_status"])}) · {_text(calculation["cost_basis"])}')
    source = calculation['source_snapshot']
    caveats = ''.join(f'<li>{_text(c)}</li>' for c in calculation['caveats'])
    dates = ', '.join(str(d) for d in calculation['source_dates'])
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>模型效率前線｜情境結報</title>
<style>
:root {{ color-scheme: light; --ink:#172b37; --muted:#516573; --line:#d9e2e5; --accent:#146a65; --bg:#f3f6f5; }}
* {{ box-sizing:border-box; }} body {{ margin:0; font:16px/1.55 system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--ink); }}
main {{ max-width:1120px; margin:auto; padding:clamp(16px,4vw,48px); }} h1 {{ font-size:clamp(1.9rem,4vw,3rem); line-height:1.18; margin:.3em 0; }} h2 {{ font-size:1.25rem; margin:0 0 1rem; }}
.eyebrow {{ color:var(--accent); font-size:.82rem; font-weight:700; letter-spacing:.08em; }} .intro {{ color:var(--muted); overflow-wrap:anywhere; }}
.cards {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:28px 0; }}
.card,.panel {{ background:white; border:1px solid var(--line); border-radius:14px; box-shadow:0 4px 20px #14332b09; }}
.card {{ padding:20px; min-width:0; }} .card strong {{ display:block; font-size:1.08rem; margin:12px 0; overflow-wrap:anywhere; }} .card span,.muted,small {{ color:var(--muted); }}
.panel {{ padding:clamp(16px,3vw,28px); margin:18px 0; }} .table-wrap {{ overflow-x:auto; }} table {{ border-collapse:collapse; width:100%; min-width:690px; }} th {{ color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.04em; text-align:left; }} th,td {{ border-bottom:1px solid var(--line); padding:12px 10px; vertical-align:top; }} tbody tr:last-child td {{ border:0; }} td:not(.model) {{ white-space:nowrap; font-variant-numeric:tabular-nums; }} .model strong,.model small {{ display:block; overflow-wrap:anywhere; }} .rank {{ color:var(--accent); font-weight:bold; }}
.states {{ list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }} .states li {{ border:1px solid var(--line); border-radius:10px; padding:14px; min-width:0; overflow-wrap:anywhere; }} .states p {{ margin:.3rem 0; }} .states small {{ display:block; }} .badge {{ display:inline-block; color:var(--accent); background:#e8f4f1; border-radius:20px; padding:1px 8px; font-size:.75rem; }} .count {{ color:var(--accent); }} .source {{ overflow-wrap:anywhere; }}
@media(max-width:720px) {{ .cards,.states {{ grid-template-columns:1fr; }} .card {{ padding:16px; }} main {{ padding:16px; }} }}
</style></head><body><main>
<header><div class="eyebrow">MODEL EFFICIENCY FRONTIER · PERSONAL SCENARIO</div><h1>模型效率前線</h1><p class="intro">Score 降序 · 原價與情境係數分列 · Claude 僅比較，不列推薦</p><p class="intro">{meta}</p></header>
<section class="cards" aria-label="三檔推薦">{''.join(cards)}</section>
<section class="panel"><h2>效率階梯 <span class="count">{len(ladder)}</span></h2><div class="table-wrap"><table><thead><tr><th>#</th><th>模型身份</th><th>Score</th><th>Cost_orig</th><th>係數</th><th>CP_adj</th></tr></thead><tbody>{''.join(_row(row, i) for i,row in enumerate(ladder,1))}</tbody></table></div></section>
{states('Grok', lambda r: r['model'].lower().startswith('grok') or r['identity'].lower().startswith(('grok ', 'grok-')))}
{states('Contributor', lambda r: 'contributor' in r['identity'].lower() or 'contributor' in r['notes'].lower() and r['grade'] == 'B')}
<section class="panel source"><h2>來源與限制</h2><p>來源日期：{_text(dates)} · 快照：{_text(source['path'])} @ {_text(source['commit'])}</p><p>cost_adj = Cost_orig ÷ 係數；CP_adj = Score ÷ cost_adj。GPT ×18 為個人情境；Grok ×16 非實測。Contributor ×1。價格為原始來源價，非折扣後實測價。</p><ul>{caveats}</ul></section>
</main></body></html>'''
