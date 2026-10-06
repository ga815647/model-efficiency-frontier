"""Display source-only observations after the caller has validated their proof."""


def source_observations(records, source_map):
    from scripts.public_identity import model_effort
    from scripts.aa_public import SourceError
    states = source_map.get('reconciliation', {}).get('status_by_slug', {})
    observations = []
    for row in records:
        if row['slug'] not in states or states[row['slug']]['state'] == 'usable_paid':
            continue
        try:
            model, effort, _ = model_effort(row['name'], row['slug'])
        except SourceError:
            # Source-only historical qualifiers need not pass the usable-row
            # effort parser. Preserve the record; never infer another effort.
            model, effort = row['name'], None
        observations.append(dict(name=row['name'], model=model, effort=effort,
                                 slug=row['slug'], **states[row['slug']]))
    return observations
