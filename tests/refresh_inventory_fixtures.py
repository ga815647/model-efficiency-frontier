from decimal import Decimal


def record(slug, *, name=None, score='40', cost='1', estimated=False, deprecated=False):
    scalar = lambda value: Decimal(value) if type(value) is str else value
    return dict(slug=slug, name=name or slug, creator='Fixture',
                score=scalar(score), cost_per_task=scalar(cost), is_estimated=estimated,
                deprecated=deprecated, price1m_input=None, price1m_output=None, cache_hit_price=None)
