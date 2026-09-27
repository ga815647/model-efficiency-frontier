"""Independent analytical points and the immutable historical source."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'runs/2026-09-26-general-grok16/candidates.csv'


def point(name, score, cost, grade='A'):
    return dict(identity=name, model=name, effort='unspecified', provider='test',
        pricing_plan='Standard', benchmark='AA-Intelligence-Index',
        benchmark_version='AA-Intelligence-Index-v4.3.2', cost_basis='api',
        evidence_url='https://example.test/model', checked_date='2026-09-26',
        notes=f'GRADE-{grade} test evidence', _score=score, _cost=cost,
        _cost_orig=cost, _cp=score/cost, _cp_orig=score/cost, _factor=1)


def historical_rows():
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    import ladder_extra as extra
    return extra.adjust_rows(extra.load_rows(SNAPSHOT))
