"""Label-bound Meta pricing and per-effort GRADE-B rescale."""
import re
from decimal import Decimal
from html import unescape
from html.parser import HTMLParser

from scripts.aa_public import SourceError

URL = 'https://dev.meta.ai/docs/pricing-rate-limits'


class _Cells(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cells, self.current = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cells = []
        elif tag in ('td', 'th') and self.cells is not None:
            self.current = ''

    def handle_data(self, text):
        if self.current is not None:
            self.current += text

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.current is not None:
            self.cells.append(self.current.strip())
            self.current = None
        elif tag == 'tr' and self.cells is not None:
            self.rows.append(self.cells)
            self.cells = None


def _table(section):
    match = re.search(r'<table\b[^>]*>.*?</table>', section, re.S | re.I)
    if not match:
        raise SourceError('pricing_markup', URL, 'labelled table missing')
    parser = _Cells()
    parser.feed(match[0])
    return parser.rows


def parse_meta_pricing(html: str) -> dict:
    sections = {}
    for plan in ('Standard', 'Contributor'):
        start = re.search(r'<h3\b[^>]*id="' + plan.lower() + r'-tier"', html, re.I)
        if not start:
            raise SourceError('pricing_markup', URL, f'{plan} heading missing')
        end = re.search(r'<h[23]\b', html[start.end():], re.I)
        sections[plan] = html[start.end():start.end()+end.start()] if end else html[start.end():]
    available = {}
    for plan, section in sections.items():
        before_table = section.split('<table', 1)[0]
        model_line = re.search(r'<p\b[^>]*>\s*Models:\s*(.*?)</p>', before_table, re.S | re.I)
        if not model_line:
            raise SourceError('model_missing', URL, plan + ' active model list missing')
        available[plan] = re.findall(r'<code\b[^>]*>\s*([^<]+)\s*</code>', model_line[1], re.I)
    if ('muse-spark-1.3-contributor' not in available['Contributor'] or
            'muse-spark-1.3' not in available['Standard']):
        raise SourceError('model_missing', URL, 'active model plan availability')
    contributor_terms = unescape(re.sub(r'<[^>]+>', ' ', sections['Contributor'].split('<table', 1)[0]))
    if 'permission to use your prompts and completions to train future Meta models' not in contributor_terms:
        raise SourceError('training_terms_missing', URL, 'Contributor active training terms missing')
    rates = {}
    for plan, section in sections.items():
        rows = _table(section)
        if not rows or [x.lower() for x in rows[0]] != ['usage', 'price per 1m tokens']:
            raise SourceError('pricing_semantics', URL, plan)
        price = {}
        for row in rows[1:]:
            if len(row) != 2 or row[0].lower() not in ('cached input', 'input', 'output') or not re.fullmatch(r'\$\d+(?:\.\d+)?', row[1]):
                raise SourceError('pricing_semantics', URL, plan)
            key = row[0].lower().replace(' ', '_')
            if key in price:
                raise SourceError('pricing_semantics', URL, 'duplicate rate')
            price[key] = Decimal(row[1][1:])
        if set(price) != {'cached_input', 'input', 'output'}:
            raise SourceError('pricing_missing', URL, plan)
        rates[plan] = price
    limits = {}
    for table in re.findall(r'<table\b[^>]*>.*?</table>', html, re.S | re.I):
        parser = _Cells(); parser.feed(table)
        if parser.rows and parser.rows[0] == ['Tier', 'Requests per minute (RPM)', 'Tokens per minute (TPM)']:
            for row in parser.rows[1:]:
                if len(row) == 3 and row[0] in rates and all(re.fullmatch(r'[\d,]+', x) for x in row[1:]):
                    limits[row[0]] = {'RPM': int(row[1].replace(',', '')), 'TPM': int(row[2].replace(',', ''))}
    if set(limits) != set(rates):
        raise SourceError('pricing_missing', URL, 'rate limits or training terms missing')
    return {'source_url': URL, 'models': available,
            'USD_per_1M_tokens': rates, 'rate_limits_per_team': limits,
            'training_note': 'Contributor permits prompts/completions for training; Standard does not. Notes only, no filtering.'}


def rescale_contributor(components: dict, prices: dict) -> Decimal:
    try:
        costs = {k: Decimal(str(components[k])) for k in ('total', 'input', 'nonCacheInput', 'cacheRead', 'cacheWrite', 'output')}
        rates = {p: {k: Decimal(str(prices[p][k])) for k in ('input', 'cached_input', 'output')}
                 for p in ('Standard', 'Contributor')}
        if any(not n.is_finite() or n < 0 for n in costs.values()) or any(
                not n.is_finite() or n <= 0 for v in rates.values() for n in v.values()):
            raise ValueError('non-positive or nonfinite components/rates')
    except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
        raise SourceError('components_missing', URL, 'required positive labelled components/rates') from exc
    # Public cost decompositions contain rounded floats. Permit 1e-10 relative
    # or 1e-12 absolute source rounding only, not missing price categories.
    for lhs, rhs in ((costs['input'], costs['nonCacheInput'] + costs['cacheRead'] + costs['cacheWrite']),
                     (costs['total'], costs['input'] + costs['output'])):
        if abs(lhs - rhs) > max(Decimal('1e-12'), abs(lhs) * Decimal('1e-10')):
            raise SourceError('components_inconsistent', URL, 'input/output sum differs from total')
    return ((costs['nonCacheInput'] + costs['cacheWrite']) * rates['Contributor']['input'] / rates['Standard']['input']
            + costs['cacheRead'] * rates['Contributor']['cached_input'] / rates['Standard']['cached_input']
            + costs['output'] * rates['Contributor']['output'] / rates['Standard']['output'])
