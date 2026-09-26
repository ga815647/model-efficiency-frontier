"""Reconcile an acquired public CSV against its evidence and result rows."""

import csv
import io


class InventoryError(ValueError):
    """Published source inventory disagrees with its CSV, result or evidence."""


def validate_fresh_inventory(data: bytes, source_map: dict, envelope: dict, *, error_code: str) -> None:
    """Require a complete paid slug/effort inventory, not just a matching CSV digest."""
    try:
        if type(source_map) is not dict or type(source_map.get('inventory')) is not dict:
            raise ValueError('invalid inventory')
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
            evidence = sources[row['model_version']]
            if (float(row['score']) != float(evidence['score']) or
                    float(row['cost_per_task']) != float(evidence['cost_per_task']) or
                    row['checked_date'] != evidence['checked_date'] or
                    row['evidence_url'] != evidence['source_url']):
                raise ValueError('public evidence disagreement')
        by_contributor = {(r['slug'], r['effort']): r for r in contributions}
        for row in contributor:
            evidence = by_contributor[(row['model_version'].split('@', 1)[0], row['effort'])]
            if row['cost_per_task'] != str(evidence['derived_cost']):
                raise ValueError('Contributor evidence disagreement')
    except (KeyError, ValueError, TypeError, UnicodeError, OverflowError) as exc:
        raise InventoryError(error_code) from exc
