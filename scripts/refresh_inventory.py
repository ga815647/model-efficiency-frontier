"""Pure classification and tracking for precision-preserving AA public records."""
from scripts.aa_public import LEADERBOARD, SourceError

POLICY = 'observed-inventory-v1'
DISCLOSURE_PREFIX = '來源退出：'


def classify_record(record: dict) -> dict:
    if record.get('deprecated') is True:
        return {'state': 'retired', 'reason': 'deprecated'}
    if record['is_estimated']:
        return {'state': 'observed_unusable', 'reason': 'estimated'}
    if record['score'] is None:
        return {'state': 'observed_unusable', 'reason': 'missing_score'}
    if record['cost_per_task'] is None:
        return {'state': 'observed_unusable', 'reason': 'missing_task_cost'}
    if record['cost_per_task'] == 0:
        return {'state': 'observed_unusable', 'reason': 'zero_cost'}
    return {'state': 'usable_paid', 'reason': None}


def build_reconciliation(records: list[dict], previous_slugs: set[str]) -> dict:
    status = {row['slug']: classify_record(row) for row in records}
    usable = {slug for slug, fact in status.items() if fact['state'] == 'usable_paid'}
    retired = {slug for slug, fact in status.items() if fact['state'] == 'retired'}
    return dict(policy=POLICY, previous_tracked_slugs=sorted(previous_slugs),
                observed_slugs=sorted(status), tracked_slugs=sorted((previous_slugs | usable) - retired),
                retired_slugs=sorted(retired), status_by_slug=status)


def blocking_candidates(reconciliation: dict) -> dict[str, list[str]]:
    previous = set(reconciliation['previous_tracked_slugs'])
    status = reconciliation['status_by_slug']
    return dict(missing=sorted(previous - set(status)),
                unusable=sorted(slug for slug in previous & set(status)
                                if status[slug]['state'] == 'observed_unusable'
                                and status[slug]['reason'] != 'missing_task_cost'))


def tracked_public_slugs(source_map: dict | None, fallback: set[str]) -> set[str]:
    """Read tracking from a complete new map; only absent sections are legacy.

    Provenance/policy trust is established by the caller, not by this reader.
    A present malformed section must never silently downgrade to paid inventory.
    """
    if source_map is None or 'reconciliation' not in source_map:
        return set(fallback)
    rec = source_map['reconciliation']

    def invalid():
        raise SourceError('previous_inventory_missing', LEADERBOARD, 'invalid reconciliation')

    fields = {'policy', 'previous_tracked_slugs', 'observed_slugs', 'tracked_slugs',
              'retired_slugs', 'status_by_slug'}
    if not isinstance(rec, dict) or set(rec) != fields or rec['policy'] != POLICY:
        invalid()
    for key in ('previous_tracked_slugs', 'observed_slugs', 'tracked_slugs', 'retired_slugs'):
        slugs = rec[key]
        if (not isinstance(slugs, list)
                or any(not isinstance(slug, str) or not slug for slug in slugs)
                or slugs != sorted(set(slugs))):
            invalid()
    status = rec['status_by_slug']
    if not isinstance(status, dict) or set(status) != set(rec['observed_slugs']):
        invalid()
    allowed = {('usable_paid', None), ('retired', 'deprecated'),
               ('observed_unusable', 'estimated'), ('observed_unusable', 'missing_score'),
               ('observed_unusable', 'missing_task_cost'), ('observed_unusable', 'zero_cost')}
    for fact in status.values():
        if (not isinstance(fact, dict) or set(fact) != {'state', 'reason'}
                or not isinstance(fact['state'], str)
                or (fact['reason'] is not None and not isinstance(fact['reason'], str))
                or (fact['state'], fact['reason']) not in allowed):
            invalid()
    usable = {slug for slug, fact in status.items() if fact['state'] == 'usable_paid'}
    retired = {slug for slug, fact in status.items() if fact['state'] == 'retired'}
    if (set(rec['retired_slugs']) != retired
            or set(rec['tracked_slugs']) != (set(rec['previous_tracked_slugs']) | usable) - retired):
        invalid()
    return set(rec['tracked_slugs'])


def source_exit_caveats(records: list[dict], reconciliation: dict) -> list[str]:
    names = {row['slug']: row['name'] for row in records}
    previous = set(reconciliation['previous_tracked_slugs'])
    status = reconciliation['status_by_slug']
    caveats = []
    for slug in sorted(previous & set(status)):
        fact = status[slug]
        if fact['state'] == 'retired':
            detail = '來源標示淘汰，本次未參戰，已退出後續強制追蹤。'
        elif fact['state'] == 'observed_unusable' and fact['reason'] == 'missing_task_cost':
            detail = '當前 task cost 缺值，本次未參戰，未沿用舊價。'
        else:
            continue
        caveats.append(f'{DISCLOSURE_PREFIX}{names[slug]}（{slug}）：{detail}')
    return caveats
