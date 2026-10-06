"""Display source-only observations after the caller has validated their proof."""


def source_observations(records, source_map):
    states = source_map.get('reconciliation', {}).get('status_by_slug', {})
    return [dict(name=r['name'], slug=r['slug'], state=states[r['slug']]['state'],
                 reason=states[r['slug']]['reason']) for r in records
            if r['slug'] in states and states[r['slug']]['state'] != 'usable_paid']
