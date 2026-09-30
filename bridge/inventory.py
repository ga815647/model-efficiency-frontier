"""Reconcile an acquired public CSV against its evidence and result rows."""

import csv
import io
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation

from scripts.aa_public import LEADERBOARD, parse_leaderboard
from scripts.public_identity import public_identity
from scripts.refresh_inventory import (POLICY, DISCLOSURE_PREFIX, build_reconciliation,
                                      blocking_candidates, tracked_public_slugs, source_exit_caveats)


class InventoryError(ValueError):
    """Published source inventory disagrees with its CSV, result or evidence."""


def _strict_json(data: bytes) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('non-finite JSON constant')

    return json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)


def _validate_proof(source_map, envelope, public, evidence, expected_previous_slugs):
    if type(evidence) is not dict:
        raise ValueError('missing inventory proof')
    parsed = parse_leaderboard(evidence['leaderboard.html'].decode('utf-8'))
    sources = _strict_json(evidence['sources.json'])
    checked_date = sources['checked_date']
    if type(checked_date) is not str or date.fromisoformat(checked_date).isoformat() != checked_date:
        raise ValueError('invalid acquisition date')
    if sources['sha256_by_url'][LEADERBOARD] != hashlib.sha256(evidence['leaderboard.html']).hexdigest():
        raise ValueError('leaderboard hash mismatch')
    saved = _strict_json(evidence['leaderboard_records.json'])
    canonical = lambda value: json.dumps(value, default=str, sort_keys=True, allow_nan=False)
    if canonical(saved) != canonical(parsed):
        raise ValueError('parsed record mismatch')
    # This reader enforces exact fields, sorted unique arrays and typed states
    # before dict equality can accept coercive relations such as True == 1.
    tracked_public_slugs(source_map, set())
    rec = source_map['reconciliation']
    previous = set(rec['previous_tracked_slugs'])
    if expected_previous_slugs is not None and previous != expected_previous_slugs:
        raise ValueError('previous tracking mismatch')
    if rec != build_reconciliation(parsed, previous) or any(blocking_candidates(rec).values()):
        raise ValueError('reconciliation mismatch')
    usable = {slug for slug, fact in rec['status_by_slug'].items() if fact['state'] == 'usable_paid'}
    if usable != set(source_map['inventory']['slugs']) or usable != set(source_map['source_by_slug']):
        raise ValueError('usable inventory mismatch')
    excluded = [dict(slug=row['slug'], name=row['name'], reason=rec['status_by_slug'][row['slug']]['reason'])
                for row in parsed if row['slug'] not in usable]
    actual = source_map['excluded']
    if (type(actual) is not list or any(type(row) is not dict or
            set(row) != {'slug', 'name', 'reason'} or
            any(type(value) is not str for value in row.values()) for row in actual) or
            canonical(sorted(actual, key=lambda row: row['slug'])) !=
            canonical(sorted(excluded, key=lambda row: row['slug']))):
        raise ValueError('excluded inventory mismatch')
    by_slug = {row['slug']: row for row in parsed}
    dates = set()
    for row in public:
        item = by_slug[row['model_version']]
        fact = source_map['source_by_slug'][row['model_version']]
        if any(row[key] != value for key, value in public_identity(item).items()):
            raise ValueError('canonical public identity mismatch')
        if row['checked_date'] != checked_date or fact['checked_date'] != checked_date:
            raise ValueError('acquisition date mismatch')
        for key in ('score', 'cost_per_task'):
            if (isinstance(fact[key], bool) or fact[key] is None or
                    Decimal(row[key]) != Decimal(str(item[key])) or
                    Decimal(str(fact[key])) != Decimal(str(item[key]))):
                raise ValueError('precise public measurement mismatch')
        if row['evidence_url'] != LEADERBOARD or fact['source_url'] != LEADERBOARD:
            raise ValueError('public source mismatch')
        dates.add(row['checked_date'])
    if dates != {checked_date} or envelope['source_dates'] != [checked_date]:
        raise ValueError('source date mismatch')
    expected = source_exit_caveats(parsed, rec)
    actual = [c for c in envelope['caveats'] if c.startswith(DISCLOSURE_PREFIX)]
    if sorted(actual) != sorted(expected):
        raise ValueError('source exit disclosure mismatch')


def validate_fresh_inventory(data: bytes, source_map: dict, envelope: dict, *, error_code: str,
                             refresh_policy: str | None = None,
                             evidence: dict[str, bytes] | None = None,
                             expected_previous_slugs: set[str] | None = None) -> None:
    """Require a complete paid slug/effort inventory, not just a matching CSV digest."""
    try:
        if type(source_map) is not dict or type(source_map.get('inventory')) is not dict:
            raise ValueError('invalid inventory')
        if refresh_policy is None:
            if 'reconciliation' in source_map:
                raise ValueError('new inventory requires trusted policy')
        elif type(refresh_policy) is not str or refresh_policy != POLICY:
            raise ValueError('unknown refresh policy')
        inventory = source_map['inventory']
        slugs, efforts = inventory['slugs'], inventory['contributor_efforts']
        if (type(slugs) is not list or not slugs or type(efforts) is not list or
                any(type(x) is not str or not x for x in slugs + efforts) or
                len(slugs) != len(set(slugs)) or len(efforts) != len(set(efforts))):
            raise ValueError('invalid inventory sets')
        rows = list(csv.DictReader(io.StringIO(data.decode('utf-8'))))
        if len(rows) != envelope['candidate_count']:
            raise ValueError('candidate count')
        by_id = {r['identity']: r for r in envelope['candidate_statuses']}
        if len(by_id) != len(rows) or {r['identity'] for r in rows} != set(by_id):
            raise ValueError('candidate identities')
        public = [r for r in rows if r['pricing_plan'] != 'Contributor']
        contributor = [r for r in rows if r['pricing_plan'] == 'Contributor']
        csv_slugs = [r['model_version'] for r in public]
        csv_efforts = [r['effort'] for r in contributor]
        if (any(not s or ' slug=' + s + ';' not in r['notes'] for s, r in zip(csv_slugs, public)) or
                set(csv_slugs) != set(slugs) or len(csv_slugs) != len(slugs) or
                set(csv_efforts) != set(efforts) or len(csv_efforts) != len(efforts)):
            raise ValueError('CSV inventory disagreement')
        sources = source_map['source_by_slug']
        contributions = source_map['contributor']
        contributor_keys = [(r['model_version'].split('@', 1)[0], r['effort']) for r in contributor]
        if (type(sources) is not dict or set(sources) != set(csv_slugs) or
                type(contributions) is not list or len(contributions) != len(contributor) or
                {(r['slug'], r['effort']) for r in contributions} !=
                set(contributor_keys) or len(set(contributor_keys)) != len(contributor)):
            raise ValueError('source inventory disagreement')
        for row in rows:
            old = by_id[row['identity']]
            if (float(row['score']) != old['score'] or
                    float(row['cost_per_task']) != old['cost_orig'] or
                    row['checked_date'] != old['source_date'] or
                    row['evidence_url'] != old['source_url'] or
                    row['benchmark_version'] != envelope['benchmark_version'] or
                    row['benchmark'] != envelope['benchmark'] or row['cost_basis'] != envelope['cost_basis']):
                raise ValueError('result inventory disagreement')
        for row in public:
            fact = sources[row['model_version']]
            measurement = (lambda value: Decimal(str(value))) if refresh_policy == POLICY else float
            if (measurement(row['score']) != measurement(fact['score']) or
                    measurement(row['cost_per_task']) != measurement(fact['cost_per_task']) or
                    row['checked_date'] != fact['checked_date'] or
                    row['evidence_url'] != fact['source_url']):
                raise ValueError('public evidence disagreement')
        by_contributor = {(r['slug'], r['effort']): r for r in contributions}
        for row in contributor:
            fact = by_contributor[(row['model_version'].split('@', 1)[0], row['effort'])]
            if row['cost_per_task'] != str(fact['derived_cost']):
                raise ValueError('Contributor evidence disagreement')
        if refresh_policy == POLICY:
            _validate_proof(source_map, envelope, public, evidence, expected_previous_slugs)
    except (KeyError, ValueError, TypeError, UnicodeError, OverflowError, InvalidOperation, AttributeError) as exc:
        raise InventoryError(error_code) from exc
