"""Fixed-window thinning of the frozen, mixed-family CP-new-high chain."""
from copy import deepcopy
import math
from pathlib import Path
import sys

_SCRIPTS = str(Path(__file__).resolve().parents[1] / 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
import compute_frontier as cf
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
