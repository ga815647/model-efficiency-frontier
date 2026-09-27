"""Model/plan/effort eligibility, independent of the plan's token rates."""
import re
from html.parser import HTMLParser

from scripts.aa_public import SourceError

MODELS_URL = 'https://dev.meta.ai/docs/models'
# Direct first-party models page checked 2026-09-27; historical recalculation
# must not treat the invalid identity as available on the snapshot date.
PROOF_DATE = '2026-09-27'
CLAIM = ('Supports all reasoning effort levels, including the "max" level for '
         'extended reasoning (available on Standard tier only).')
MODEL_ITEM = ('Muse Spark 1.3 ( muse-spark-1.3 ): the latest version, tuned for agentic '
              'workflows (multi-step tool, browser, and long-horizon tasks) with improved '
              'coding over 1.2. ' + CLAIM + ' Recommended for new work.')


class _ModelItems(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.items = []
        self.current = None
        self.code = None
        self.strong = None

    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            if self.depth == 0:
                self.current = {'text': [], 'codes': [], 'strong': []}
            self.depth += 1
        elif self.depth and tag == 'code':
            self.code = []
        elif self.depth and tag == 'strong':
            self.strong = []

    def handle_data(self, data):
        if self.depth:
            self.current['text'].append(data)
            if self.code is not None:
                self.code.append(data)
            if self.strong is not None:
                self.strong.append(data)

    def handle_endtag(self, tag):
        if tag == 'code' and self.code is not None:
            self.current['codes'].append(''.join(self.code).strip())
            self.code = None
        elif tag == 'strong' and self.strong is not None:
            self.current['strong'].append(''.join(self.strong).strip())
            self.strong = None
        elif tag == 'li' and self.depth:
            self.depth -= 1
            if not self.depth:
                self.items.append(self.current)
                self.current = None


def parse_meta_models(html: str) -> dict:
    """Require the exact positive claim in the exact model's active list item."""
    parser = _ModelItems()
    parser.feed(html)
    matches = [item for item in parser.items if 'muse-spark-1.3' in item['codes']]
    if len(matches) != 1 or matches[0]['strong'][:1] != ['Muse Spark 1.3']:
        raise SourceError('model_capability_drift', MODELS_URL, 'Muse Spark 1.3 model item/ID missing or ambiguous')
    text = ' '.join(' '.join(matches[0]['text']).split())
    if text != MODEL_ITEM:
        raise SourceError('model_capability_drift', MODELS_URL, 'Muse Spark 1.3 max plan claim changed')
    return {'source_url': MODELS_URL, 'model_id': 'muse-spark-1.3', 'max_plan': 'Standard',
            'contributor_max_available': False, 'claim': CLAIM}


def unavailable_reason(row: dict) -> str | None:
    """Match only the disproven identity, not other families/plans/efforts."""
    model = row.get('model') or ''
    identity = row.get('identity') or ''
    if not model:
        model = re.sub(r'\s+(?:max|xhigh|high|medium|low)\s+Meta Contributor$', '', identity, flags=re.I)
    model_key = re.sub(r'[\s_-]+', '-', model.strip().lower())
    plan = (row.get('pricing_plan') or '').strip().lower()
    effort = (row.get('effort') or '').strip().lower()
    if not plan and identity.lower().endswith(' meta contributor'):
        plan = 'contributor'
    if not effort and re.search(r'\smax\s+Meta Contributor$', identity, re.I):
        effort = 'max'
    if model_key == 'muse-spark-1.3' and plan == 'contributor' and effort == 'max':
        return f'Muse Spark 1.3 max unavailable on Contributor; max Standard tier only ({MODELS_URL}; checked {PROOF_DATE})'
    return None
