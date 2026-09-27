"""Fixed-window thinning of the frozen, mixed-family CP-new-high chain."""
from copy import deepcopy
import math
from pathlib import Path
import sys

_SCRIPTS = str(Path(__file__).resolve().parents[1] / 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
import compute_frontier as cf
import ladder_extra as extra
from scripts.meta_availability import unavailable_reason


class SelectionError(ValueError):
    """A selection cannot be calculated without invalid numeric operations."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def window_strengths(rows: list[dict]) -> dict[str, tuple[float, str]]:
    """Measure log-CP gains on the current descending-score chain, without extrapolation."""
    if len(rows) < 2:
        return {r['identity']: (0., 'neutral_missing_window') for r in rows}
    scores = [r['_score'] for r in rows]
    if not all(math.isfinite(r['_score']) and math.isfinite(r['_cp']) and r['_cp'] > 0
               for r in rows):
        raise SelectionError('selection_numeric')
    logs = [math.log(r['_cp']) for r in rows]

    def interpolate(score):
        for i in range(len(rows) - 1):
            if scores[i] >= score >= scores[i + 1]:
                fraction = (scores[i] - score) / (scores[i] - scores[i + 1])
                return logs[i] + fraction * (logs[i + 1] - logs[i])

    values = {}
    for i, row in enumerate(rows):
        score = scores[i]
        if score + 2.0 > scores[0] or score - 2.0 < scores[-1]:
            values[row['identity']] = (0., 'neutral_missing_window')
            continue
        left_gain = logs[i] - interpolate(score + 2.0)
        right_gain = interpolate(score - 2.0) - logs[i]
        if not all(math.isfinite(x) and x > 0 for x in (left_gain, right_gain)):
            raise SelectionError('selection_numeric')
        values[row['identity']] = (math.log(left_gain / right_gain), 'full_window')
    return values


def thin_chain(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Remove direct near-neighbors of the strongest representative, rebuilding each round."""
    current = deepcopy(rows)
    trace = []
    while len(current) > 1:
        pool = [r for r in current if any(
            other['identity'] != r['identity'] and abs(other['_score'] - r['_score']) < 2.0
            for other in current)]
        if not pool:
            break
        values = window_strengths(current)
        winner = min(pool, key=lambda r: (-values[r['identity']][0], -r['_cp'],
                                          -r['_score'], r['identity']))
        removed = [r['identity'] for r in current
                   if r['identity'] != winner['identity']
                   and abs(r['_score'] - winner['_score']) < 2.0]
        strength, support = values[winner['identity']]
        trace.append(dict(step=len(trace) + 1, winner=winner['identity'],
                          strength=strength, support=support, removed=removed))
        current = [r for r in current if r['identity'] not in removed]
    return current, trace


def select_chain(rows: list[dict], *, min_score: float, max_cost: float | None) -> dict:
    """Partition unavailable identities, run frozen selection, then thin its chain."""
    available, excluded = [], []
    for row in deepcopy(rows):
        reason = unavailable_reason(row)
        if reason:
            excluded.append((row, reason))
        else:
            available.append(row)
    kept, frozen_excluded = cf.compute_one_group(available, min_score, max_cost, 2., .05)
    chain = [row for row, _ in kept]
    final, trace = thin_chain(chain)
    cuts = {identity: step['winner'] for step in trace for identity in step['removed']}
    return dict(chain=chain, final=final, excluded=excluded + frozen_excluded,
                cuts=cuts, trace=trace)


def _project(row, status, reason=None, winner=None):
    """Project one adjusted candidate, preserving source evidence and original prices."""
    return {
        'identity': row['identity'], 'model': row.get('model') or '',
        'effort': row.get('effort') or '', 'score': row['_score'],
        'cost_orig': row['_cost_orig'], 'cost_adj': row['_cost'],
        'cp_orig': row['_cp_orig'], 'cp_adj': extra._cp_adj(row),
        'factor': row['_factor'], 'grade': extra.grade_of(row),
        'status': status, 'reason': extra._reason(reason) if reason else None,
        'winner': winner, 'source_url': row.get('evidence_url') or '',
        'source_date': row.get('checked_date') or '', 'notes': row.get('notes') or '',
        'is_grok': extra._grok(row), 'is_contributor': extra._contributor(row),
        'comparison_only': extra._is_claude(row['identity']), 'upgrade': None,
    }


def select_anchors(ladder: list[dict]) -> dict:
    """Choose two objective entry points from projected final non-Claude rows."""
    eligible = [r for r in ladder if not r['comparison_only']]
    return {
        'highest_retained_score': min(eligible, key=lambda r: (
            -r['score'], r['cost_adj'], r['identity'])) if eligible else None,
        'lowest_retained_cost': min(eligible, key=lambda r: (
            r['cost_adj'], -r['score'], r['identity'])) if eligible else None,
    }


def calculate_ladder(rows: list[dict], *, min_score: float, max_cost: float | None) -> dict:
    """Compose one main selection and an independent all-B-removed membership audit."""
    selection = select_chain(rows, min_score=min_score, max_cost=max_cost)
    final_ids = {r['identity'] for r in selection['final']}
    excluded = {r['identity']: (r, reason) for r, reason in selection['excluded']}
    chain = {r['identity']: r for r in selection['chain']}
    statuses = []
    for source in rows:
        identity = source['identity']
        if identity in final_ids:
            projected = _project(chain[identity], 'final')
        elif identity in selection['cuts']:
            projected = _project(chain[identity], 'cut', 'within_replacement_radius',
                                 selection['cuts'][identity])
        else:
            row, reason = excluded[identity]
            projected = _project(row, 'excluded', reason)
        statuses.append(projected)
    by_identity = {r['identity']: r for r in statuses}
    ladder = [by_identity[r['identity']] for r in selection['final']]
    eligible = [r for r in ladder if not r['comparison_only']]
    for upper, lower in zip(eligible, eligible[1:]):
        upper['upgrade'] = {
            'cheaper_identity': lower['identity'],
            'delta_score': upper['score'] - lower['score'],
            'cost_multiple': upper['cost_adj'] / lower['cost_adj'],
            'delta_cost_adj': upper['cost_adj'] - lower['cost_adj'],
        }

    grade_b_effects = []
    usable_b = any(extra.grade_of(r) == 'B' and not unavailable_reason(r)
                   and r['_score'] >= min_score
                   and (max_cost is None or r['_cost'] <= max_cost) for r in rows)
    if usable_b:
        without_b = select_chain(deepcopy([r for r in rows if extra.grade_of(r) != 'B']),
                                 min_score=min_score, max_cost=max_cost)
        without_b_ids = {r['identity'] for r in without_b['final']}
        for identity in sorted(r['identity'] for r in rows if extra.grade_of(r) == 'A'):
            with_retained, without_retained = identity in final_ids, identity in without_b_ids
            if with_retained != without_retained:
                grade_b_effects.append(dict(identity=identity, with_b_retained=with_retained,
                                            without_b_retained=without_retained))
    return dict(ladder=ladder, anchors=select_anchors(ladder), candidate_statuses=statuses,
                candidate_count=len(rows), chain_identities=[r['identity'] for r in selection['chain']],
                selection_trace=selection['trace'], grade_b_effects=grade_b_effects)
