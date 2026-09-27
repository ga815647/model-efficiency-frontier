"""Exploratory sensitivity diagnostics, NOT a production ranking entry point.

Run from any directory; uses only the fixed historical input and current frozen
CP-new-high implementation. Perturbations are hypothetical, not new observations
or confidence intervals. Output JSON is written to stdout.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
import compute_frontier as cf
import ladder_extra as extra
from scripts.meta_availability import unavailable_reason

SOURCE = ROOT / 'runs/2026-09-26-general-grok16/candidates.csv'
EXPECTED = 'e3916f8405904154f0e1dc648588bb08ce92f483cd616ba9be0ff2e5c726ed22'


def chain(rows):
    kept, _ = cf.compute_one_group(copy.deepcopy(rows), 0, None, 2, .05)
    return [r for r, _ in kept]


def thin(rows, distance=2., endpoint=0., dynamic=True):
    rows = copy.deepcopy(rows)
    original = rows[:]
    trace = []

    def strengths(current):
        gains = [math.log(b['_cp'] / a['_cp']) / (a['_score'] - b['_score'])
                 for a, b in zip(current, current[1:])]
        return {r['identity']: (math.log(gains[i-1] / gains[i])
                               if 0 < i < len(current)-1 else endpoint)
                for i, r in enumerate(current)}

    initial = strengths(rows)
    while True:
        values = strengths(rows) if dynamic else initial
        pool = []
        for r in rows:
            near = [o for o in rows if o is not r and
                    abs(o['_score'] - r['_score']) < distance]
            if near:
                pool.append((r, near))
        if not pool:
            break
        winner, removed = min(pool, key=lambda p: (
            -values[p[0]['identity']], -p[0]['_cp'], -p[0]['_score'], p[0]['identity']))
        trace.append(dict(winner=winner['identity'], strength=values[winner['identity']],
                          removed=[r['identity'] for r in removed]))
        rows = [r for r in rows if r not in removed]
    assert all(a['_score'] - b['_score'] >= distance for a, b in zip(rows, rows[1:]))
    assert all(a['_cp'] < b['_cp'] for a, b in zip(rows, rows[1:]))
    assert all(any(abs(r['_score'] - o['_score']) < distance for o in rows)
               for r in original)
    return rows, trace


def identities(rows):
    return [r['identity'] for r in rows]


def delta(rows, base):
    current = set(identities(rows))
    return dict(added=sorted(current-base), removed=sorted(base-current))


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    raw = extra.load_rows(str(SOURCE))
    eligible = [r for r in raw if not unavailable_reason(r)]
    assert len(raw) == 155 and len(eligible) == 154
    adjusted = extra.adjust_rows(eligible)
    baseline_chain = chain(adjusted)
    baseline, trace = thin(baseline_chain)
    base = set(identities(baseline))
    assert len(baseline_chain) == 19 and len(baseline) == 10
    assert all(any(abs(r['_score']-o['_score']) < 2 for o in baseline)
               for r in baseline_chain)
    result = dict(source_sha256=EXPECTED, candidate_count=len(adjusted),
                  chain=[dict(identity=r['identity'], score=r['_score'],
                              cost_adj=r['_cost'], cp_adj=r['_cp']) for r in baseline_chain],
                  baseline=identities(baseline), trace=trace)
    result['thresholds'] = []
    for distance in (1.5, 1.75, 1.9, 2., 2.1, 2.25, 2.5):
        kept, _ = thin(baseline_chain, distance)
        result['thresholds'].append(dict(distance=distance, count=len(kept), **delta(kept, base)))
    result['endpoint_sensitivity'] = []
    for endpoint in (-1., 0., 1.):
        kept, _ = thin(baseline_chain, endpoint=endpoint)
        result['endpoint_sensitivity'].append(dict(endpoint=endpoint, **delta(kept, base)))
    static, static_trace = thin(baseline_chain, dynamic=False)
    result['static_priority'] = dict(**delta(static, base), trace=static_trace)
    rng = random.Random(20260927)
    for _ in range(20):
        shuffled = copy.deepcopy(adjusted)
        rng.shuffle(shuffled)
        kept, _ = thin(chain(shuffled))
        assert identities(kept) == identities(baseline)
    result['input_order_checks'] = 20
    artificial = [dict(identity=name, _score=score, _cp=cp, _cost=score/cp)
                  for name, score, cp in [('top', 10., 1.), ('middle', 9., 3.),
                                          ('tail', 6., 4.)]]
    artificial_kept, artificial_trace = thin(artificial)
    assert 'top' not in identities(artificial_kept)
    result['synthetic_endpoint_example'] = dict(
        purpose='Prove neutral endpoints do not pin the highest score; not model evidence',
        input=artificial, kept=identities(artificial_kept), trace=artificial_trace)
    result['perturbations'] = []
    for scope, original in (('stage2_only', baseline_chain), ('full_pipeline', adjusted)):
        for field, amount in (('score', .1), ('score', .25), ('cost', .01), ('cost', .05)):
            cases = []
            frequencies = {name: 0 for name in sorted(base)}
            for i, row in enumerate(original):
                for sign in (-1, 1):
                    perturbed = copy.deepcopy(original)
                    if field == 'score':
                        perturbed[i]['_score'] += sign*amount
                    else:
                        perturbed[i]['_cost'] *= 1 + sign*amount
                    if scope == 'full_pipeline':
                        current = chain(perturbed)
                    else:
                        # Isolate stage 2: only compare cases preserving chain order
                        # and CP monotonicity. Invalid cases are counted explicitly.
                        for r in perturbed:
                            r['_cp'] = r['_score']/r['_cost']
                        if not all(a['_score'] > b['_score'] and a['_cp'] < b['_cp']
                                   for a,b in zip(perturbed, perturbed[1:])):
                            cases.append(dict(changed_identity=row['identity'], sign=sign,
                                              skipped='chain ordering/CP monotonicity changed'))
                            continue
                        current = perturbed
                    kept, _ = thin(current)
                    for name in identities(kept):
                        if name in frequencies:
                            frequencies[name] += 1
                    diff = delta(kept, base)
                    if diff['added'] or diff['removed']:
                        cases.append(dict(changed_identity=row['identity'], sign=sign, **diff))
            skipped = sum('skipped' in c for c in cases)
            result['perturbations'].append(dict(scope=scope, field=field, amount=amount,
                total=2*len(original), skipped=skipped, changed=sum('added' in c for c in cases),
                retention_counts=frequencies, cases=cases))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
