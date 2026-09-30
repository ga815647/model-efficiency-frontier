"""Read-only Markdown / offline HTML projections of a validated v2 calculation.

Selection, validation and acquisition belong to the caller. The shared table
projection preserves payload order and only derives display-only score gaps.
Source URLs are deliberately plain text, never active links.
"""
from html import escape
import re

from scripts.refresh_inventory import DISCLOSURE_PREFIX


_ANCHORS = (('highest_retained_score', '最強保留檔'),
            ('lowest_retained_cost', '最低情境成本保留檔'))
_COLUMNS = ('身份', 'Score', 'Cost_orig', 'Cost_adj', 'CP_adj', 'factor', 'GRADE', '用途', '升級比較')


def _text(value):
    return '—' if value is None else str(value)


def _html(value):
    return escape(_text(value), quote=True)


def _markdown(value):
    # Escape raw HTML and Markdown syntax independently from HTML rendering.
    value = _text(value).replace('\r\n', '\n').replace('\r', '\n')
    value = re.sub(r'([\\`*_{}\[\]()#!~])', r'\\\1', value)
    return escape(value, quote=True).replace('|', '&#124;').replace('\n', '<br>')


def _number(value):
    return f'{value:.6f}'.rstrip('0').rstrip('.')


def _upgrade(row):
    upgrade = row['upgrade']
    if upgrade is None:
        return '—'
    return (f'相對 {upgrade["cheaper_identity"]}：'
            f'ΔScore {_number(upgrade["delta_score"])}；'
            f'成本倍率 {_number(upgrade["cost_multiple"])}；'
            f'ΔCost_adj ${_number(upgrade["delta_cost_adj"])}')


def _cells(row):
    return (row['identity'], _number(row['score']), '$' + _number(row['cost_orig']),
            '$' + _number(row['cost_adj']), _number(row['cp_adj']), '×' + str(row['factor']),
            'GRADE-' + row['grade'], '僅比較' if row['comparison_only'] else '非Claude', _upgrade(row))


def _tables(calculation):
    """Presentation sections shared by both formats; never sort or select models."""
    statuses = calculation['candidate_statuses']
    by_id = {row['identity']: row for row in statuses}
    yield 'ladder', '已選好階梯 · Score降序', ('#',) + _COLUMNS, [
        (rank,) + _cells(row) for rank, row in enumerate(calculation['ladder'], 1)]
    cuts = []
    for step in calculation['selection_trace']:
        winner = by_id[step['winner']]
        support = ('缺雙側視窗、依CP解平手；中性0，非真實雙側轉折證據'
                   if step['support'] == 'neutral_missing_window' else
                   '完整雙側視窗 log-CP 轉折')
        for identity in step['removed']:
            row = by_id[identity]
            cuts.append((step['step'], identity, step['winner'], 'GRADE-' + winner['grade'],
                         f'{abs(row["score"] - winner["score"]):.6f}', row['reason'],
                         _number(step['strength']), support))
    yield 'cuts', '第二階段 cut · 原行 → 最終代表', (
        '步驟', '原行', '最終代表', '代表GRADE', '分差', '原因', 'k', '支持證據'), cuts
    audit_columns = _COLUMNS + ('狀態', '原因', '代表', '來源日期', '來源URL', '原始註記')
    for key, title, rows in (
            ('excluded', '第一階段／能力不可用 excluded', [r for r in statuses if r['status'] == 'excluded']),
            ('grok', 'Grok 全部狀態', [r for r in statuses if r['is_grok']]),
            ('contributor', 'Contributor 全部狀態', [r for r in statuses if r['is_contributor']]),
            ('audit', '完整候選稽核', statuses)):
        yield key, title, audit_columns, [
            _cells(r) + (r['status'], r['reason'], r['winner'], r['source_date'], r['source_url'], r['notes'])
            for r in rows]
    yield 'grade-b', 'GRADE-B 依賴診斷', ('A身份', '有B', '無B'), [
        (effect['identity'], '有B：' + ('保留' if effect['with_b_retained'] else '不保留'),
         '無B：' + ('保留' if effect['without_b_retained'] else '不保留'))
        for effect in calculation['grade_b_effects']]


def _metadata(calculation):
    params = calculation['parameters']
    source = calculation['source_snapshot']
    version = calculation['version_status']
    yield (f'{calculation["benchmark"]} · {calculation["benchmark_version"]} · '
           f'{"推定" if version == "inferred" else version} ({version}) · cost basis：{calculation["cost_basis"]}')
    yield '來源日期：' + ', '.join(calculation['source_dates'])
    yield '來源 locator：' + ' · '.join(f'{key}={value}' for key, value in source.items())
    yield (f'min_score={params["min_score"]}；理由：{params["min_score_reason"]}；'
           f'max_cost（Cost_adj）={_text(params["max_cost"])}；原始付費候選={calculation["candidate_count"]}')
    yield (f'政策：{calculation["selection_policy"]}；'
           f'第一階段 eps_score={calculation["eps"]["score"]}、eps_cp={calculation["eps"]["cp"]}；'
           f'固定視窗半寬={calculation["selection_parameters"]["window_score"]}、'
           f'替代半徑={calculation["selection_parameters"]["replacement_score"]}')
    yield 'Privacy／配額／速度僅註記，不參與選檔；Claude僅比較、不推薦。'


def _context(calculation):
    params = calculation['parameters']
    yield (f'cost_adj = Cost_orig ÷ factor；CP_adj = Score ÷ cost_adj。GPT ×{params["gpt_factor"]} '
           f'為個人情境；Grok ×{params["grok_factor"]} 為用戶指定情境、非實測。Contributor ×1。'
           '預設GPT ×18來自個人約18.9倍保守取整，非AA實測；原價及成本GRADE與情境係數分開。')
    yield ('GRADE-B 成本公式與假設見原始註記。B組移除診斷只標示A行保留狀態改變，'
           '非單一B的唯一因果證明；A代表也可能受B間接影響。空診斷表示未列出A行保留變化。')
    yield ('固定政策限制：硬2分邊界、缺窗中性規則及逐次選擇仍可能跳變；'
           '不到2分不宣稱能力相同，轉折不是任務成功率或購買效用。')
    yield ('$20+$59=$79只屬GPT特定訂閱組合假設；N未提供，不產生新月費決策，'
           '不從非GPT入口推論續訂，不自動續訂。')
    yield from calculation['caveats']


def _source_exits(calculation: dict) -> list[str]:
    return [line for line in calculation['caveats'] if line.startswith(DISCLOSURE_PREFIX)]


def render_markdown(calculation: dict) -> str:
    """Render a v2 calculation without mutating it or recalculating identities."""
    lines = ['# 模型效率前線｜固定視窗階梯', '']
    lines.extend('- ' + _markdown(line) for line in _metadata(calculation))
    lines.append('')
    for key, title in _ANCHORS:
        row = calculation['anchors'][key]
        lines.append(f'- {title}：{_markdown(row["identity"]) if row else "從缺"}')
    exits = _source_exits(calculation)
    if exits:
        lines.extend(['', '## 本次來源退出', ''])
        lines.extend('- ' + _markdown(line) for line in exits)
    for _, title, columns, rows in _tables(calculation):
        lines.extend(['', '## ' + title, ''])
        if not rows:
            lines.append('無')
            continue
        lines.append('| ' + ' | '.join(_markdown(c) for c in columns) + ' |')
        lines.append('| ' + ' | '.join('---' for _ in columns) + ' |')
        lines.extend('| ' + ' | '.join(_markdown(c) for c in row) + ' |' for row in rows)
    lines.extend(['', '## 來源與限制', ''])
    lines.extend('- ' + _markdown(line) for line in _context(calculation))
    return '\n'.join(lines) + '\n'


_CSS = '''
:root { color-scheme:light; --ink:#172b37; --muted:#516573; --line:#d9e2e5; --accent:#146a65; }
* { box-sizing:border-box; } body { margin:0; font:16px/1.55 system-ui,-apple-system,sans-serif; background:#f3f6f5; color:var(--ink); }
main { max-width:1120px; margin:auto; padding:clamp(16px,4vw,48px); }
h1 { font-size:clamp(1.9rem,4vw,3rem); line-height:1.18; } h2 { font-size:1.25rem; }
.cards { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin:28px 0; }
.card,.panel { background:white; border:1px solid var(--line); border-radius:14px; padding:clamp(16px,3vw,28px); min-width:0; margin:18px 0; overflow-wrap:anywhere; }
.card strong { display:block; } .card span,.intro,small { color:var(--muted); } .intro { overflow-wrap:anywhere; }
.table-wrap { overflow-x:auto; max-width:100%; } table { border-collapse:collapse; width:100%; min-width:960px; }
th,td { text-align:left; padding:12px 10px; border-bottom:1px solid var(--line); vertical-align:top; min-width:90px; }
th { color:var(--muted); font-size:.8rem; } td { font-variant-numeric:tabular-nums; }
td.model { min-width:220px; } td.notes { min-width:220px; } summary { cursor:pointer; color:var(--accent); }
.rank { color:var(--accent); font-weight:bold; } .comparison { color:var(--accent); font-weight:bold; }
@media(max-width:720px) { .cards { grid-template-columns:1fr; } main { padding:16px; } }
'''


def render_html(calculation: dict) -> str:
    """Return a single offline document. All source strings are escaped text."""
    cards = []
    for key, title in _ANCHORS:
        row = calculation['anchors'][key]
        body = (_html(row['identity']) if row else '從缺')
        detail = (f'Score {_number(row["score"])} · Cost_adj ${_number(row["cost_adj"])}'
                  if row else '無非Claude保留行')
        cards.append(f'<article class="card"><h2>{title}</h2><strong>{body}</strong><span>{_html(detail)}</span></article>')
    sections = []
    for key, title, columns, rows in _tables(calculation):
        body = []
        for rank, row in enumerate(rows, 1):
            cells = []
            for column, value in zip(columns, row):
                content = _html(value)
                css = ''
                if column == '原始註記':
                    content = f'<details><summary>原始註記</summary><small>{content}</small></details>'
                    css = 'notes'
                elif column == '身份':
                    css = 'model'
                elif column == '用途' and value == '僅比較':
                    css = 'comparison'
                cells.append(f'<td class="{css}">{content}</td>')
            attr = f' data-rank="{rank}"' if key == 'ladder' else ''
            body.append(f'<tr{attr}>{"".join(cells)}</tr>')
        table = ('<div class="table-wrap"><table><thead><tr>' +
                 ''.join(f'<th scope="col">{_html(c)}</th>' for c in columns) +
                 '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div>') if rows else '<p>無</p>'
        sections.append(f'<section class="panel" data-family="{key}"><h2>{title} ({len(rows)})</h2>{table}</section>')
    context = ''.join(f'<li>{_html(line)}</li>' for line in _context(calculation))
    metadata = ''.join(f'<p class="intro">{_html(line)}</p>' for line in _metadata(calculation))
    exits = _source_exits(calculation)
    exit_section = ('<section class="panel" data-family="source-exits"><h2>本次來源退出</h2><ul>' +
                    ''.join('<li>' + _html(line) + '</li>' for line in exits) + '</ul></section>') if exits else ''
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>模型效率前線｜固定視窗階梯</title><style>{_CSS}</style></head><body><main>
<header><h1>模型效率前線</h1><p class="intro">CP-new-high → 固定2分視窗 · Score降序 · Claude僅比較</p>{metadata}</header>
<section class="cards" aria-label="保留檔入口">{''.join(cards)}</section>
{exit_section}
{''.join(sections)}
<section class="panel"><h2>來源與限制</h2><ul>{context}</ul></section>
</main></body></html>'''
