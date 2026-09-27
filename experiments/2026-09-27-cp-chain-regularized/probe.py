"""Compare bounded-denominator knee diagnostics; no production ranking writes.

The 2-point regularization scale is the previously accepted representative
neighborhood, not a fitted parameter or an AA confidence interval.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'previous_probe', ROOT / 'experiments/2026-09-27-cp-chain-sensitivity/probe.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

MODES = ('raw', 'floor', 'smooth', 'chord', 'raw_window_edges', 'window')
SCALE = 2.
PERTURBATIONS = (('score', .1), ('score', .25), ('cost', .01), ('cost', .05))


def denominator(gap, mode, scale):
    assert gap > 0 and scale > 0
    if mode in ('raw', 'raw_window_edges'):
        return gap
    if mode == 'floor':
        return max(gap, scale)
    if mode == 'smooth':
        return math.hypot(gap, scale)
    raise ValueError(mode)


def window_strengths(items, scale, endpoint):
    values = {r['identity']: endpoint for r in items}

    def interpolated_log_cp(score):
        for a, b in zip(items, items[1:]):
            if a['_score'] >= score >= b['_score']:
                weight = (a['_score']-score)/(a['_score']-b['_score'])
                return math.log(a['_cp']) + weight*math.log(b['_cp']/a['_cp'])
        raise ValueError('outside observed chain')

    for b in items:
        # Compare equal score spans rather than differently sized adjacent
        # segments. Interpolation is a diagnostic, not a measured identity.
        # No extrapolation at unsupported edges.
        if (b['_score']+scale > items[0]['_score'] or
                b['_score']-scale < items[-1]['_score']):
            continue
        y = math.log(b['_cp'])
        incoming = y-interpolated_log_cp(b['_score']+scale)
        outgoing = interpolated_log_cp(b['_score']-scale)-y
        values[b['identity']] = math.log(incoming/outgoing)
    return values


def thin(rows, mode, distance=2., endpoint=0., dynamic=True, scale=SCALE):
    current = list(rows)
    trace = []

    def strengths(items):
        if mode == 'window':
            return window_strengths(items, scale, endpoint)
        if mode == 'chord':
            values = {r['identity']: endpoint for r in items}
            for a, b, c in zip(items, items[1:], items[2:]):
                left = a['_score']-b['_score']
                right = b['_score']-c['_score']
                gain_left = math.log(b['_cp']/a['_cp'])
                gain_right = math.log(c['_cp']/b['_cp'])
                # Signed distance in log-CP from the neighboring chord;
                # a sub-resolution total span attenuates, never amplifies it.
                values[b['identity']] = (
                    right*gain_left-left*gain_right) / max(left+right, scale)
            return values
        gains = [math.log(b['_cp']/a['_cp']) /
                 denominator(a['_score']-b['_score'], mode, scale)
                 for a, b in zip(items, items[1:])]
        values = {r['identity']: (math.log(gains[i-1]/gains[i])
                                 if 0 < i < len(items)-1 else endpoint)
                  for i, r in enumerate(items)}
        if mode == 'raw_window_edges':
            for r in items:
                if (r['_score']+scale > items[0]['_score'] or
                        r['_score']-scale < items[-1]['_score']):
                    values[r['identity']] = endpoint
        return values

    initial = strengths(current)
    while True:
        strength = strengths(current) if dynamic else initial
        pool = [(r, [o for o in current if o is not r and
                     abs(r['_score']-o['_score']) < distance]) for r in current]
        pool = [(r, near) for r, near in pool if near]
        if not pool:
            break
        winner, removed = min(pool, key=lambda p: (
            -strength[p[0]['identity']], -p[0]['_cp'], -p[0]['_score'], p[0]['identity']))
        trace.append(dict(winner=winner['identity'], strength=strength[winner['identity']],
                          removed=previous.identities(removed)))
        current = [r for r in current if r not in removed]
    assert all(a['_score']-b['_score'] >= distance and a['_cp'] < b['_cp']
               for a, b in zip(current, current[1:]))
    assert all(any(abs(r['_score']-o['_score']) < distance for o in current) for r in rows)
    return current, trace


def names(rows):
    return set(previous.identities(rows))


def non_claude(items):
    return {name for name in items if not previous.extra._is_claude(name)}


def changed(diff):
    return bool(diff['added'] or diff['removed'])


def perturbations(original, baseline_chain, mode, scope):
    baseline, _ = thin(baseline_chain, mode)
    base = names(baseline)
    output = []
    for field, amount in PERTURBATIONS:
        cases, skips = [], []
        max_recommendation_delta = 0
        for i, row in enumerate(original):
            for sign in (-1, 1):
                altered = copy.deepcopy(original)
                if field == 'score':
                    altered[i]['_score'] += sign*amount
                else:
                    altered[i]['_cost'] *= 1+sign*amount
                if scope == 'full_pipeline':
                    current_chain = previous.chain(altered)
                else:
                    for r in altered:
                        r['_cp'] = r['_score']/r['_cost']
                    if not all(a['_score'] > b['_score'] and a['_cp'] < b['_cp']
                               for a, b in zip(altered, altered[1:])):
                        skips.append(dict(identity=row['identity'], sign=sign,
                                          reason='chain ordering/CP monotonicity changed'))
                        continue
                    current_chain = altered
                kept, _ = thin(current_chain, mode)
                diff = previous.delta(kept, base)
                if changed(diff):
                    count = len(non_claude(names(kept)) ^ non_claude(base))
                    max_recommendation_delta = max(max_recommendation_delta, count)
                    cases.append(dict(changed_identity=row['identity'], sign=sign,
                        non_claude_changed=count > 0,
                        chain_diff=previous.delta(current_chain, names(baseline_chain)), **diff))
        output.append(dict(scope=scope, field=field, amount=amount,
            total=2*len(original), skipped=len(skips), changed=len(cases),
            non_claude_changed=sum(c['non_claude_changed'] for c in cases),
            max_non_claude_symmetric_difference=max_recommendation_delta,
            cases=cases, skip_details=skips))
    return output


def main():
    assert hashlib.sha256(previous.SOURCE.read_bytes()).hexdigest() == previous.EXPECTED
    raw = previous.extra.load_rows(str(previous.SOURCE))
    adjusted = previous.extra.adjust_rows([r for r in raw if not previous.unavailable_reason(r)])
    chain = previous.chain(adjusted)
    assert len(raw) == 155 and len(adjusted) == 154 and len(chain) == 19
    raw_kept, raw_trace = previous.thin(chain)
    control, control_trace = thin(chain, 'raw')
    assert previous.identities(raw_kept) == previous.identities(control)
    assert raw_trace == control_trace
    original_result = json.loads((ROOT / 'experiments/2026-09-27-cp-chain-sensitivity/result.json').read_text())
    result = dict(source_sha256=previous.EXPECTED, scale=SCALE,
                  neighborhood=2., modes={})
    # Analytic checks: linear log-CP has no knee; a slope drop from .5 to .1
    # around Score6 must have strength ln(5), including interpolated windows.
    straight = [dict(identity=str(s), _score=s, _cp=math.exp(.1*(10-s)))
                for s in (10., 9., 6., 3., 2.)]
    assert all(abs(v) < 1e-12 for v in window_strengths(straight, 2., 0.).values())
    knee = [dict(identity=str(s), _score=s,
                 _cp=math.exp(.5*(10-s) if s >= 6 else 2+.1*(6-s)))
            for s in (10., 9., 6., 3., 2.)]
    strengths = window_strengths(knee, 2., 0.)
    assert math.isclose(strengths['6.0'], math.log(5), abs_tol=1e-12)
    scaled = [dict(r, _cp=r['_cp']*1000) for r in knee]
    assert all(math.isclose(strengths[k], v, abs_tol=1e-12)
               for k, v in window_strengths(scaled, 2., 0.).items())
    result['analytic_checks'] = ['linear log-CP zero', 'interpolated slope ratio ln(5)',
                                 'uniform CP scaling invariant']
    for mode in MODES:
        baseline, trace = thin(chain, mode)
        entry = dict(baseline=[dict(identity=r['identity'], score=r['_score'],
                                   cost_adj=r['_cost'], cp_adj=r['_cp']) for r in baseline],
                     compared_with_raw=previous.delta(baseline, names(raw_kept)), trace=trace,
                     perturbations=perturbations(chain, chain, mode, 'stage2_only') +
                                   perturbations(adjusted, chain, mode, 'full_pipeline'))
        if mode == 'raw':
            for old, new in zip(original_result['perturbations'], entry['perturbations']):
                for key in ('scope', 'field', 'amount', 'total', 'skipped', 'changed'):
                    assert old[key] == new[key], (key, old, new)
                old_cases = [{k: c[k] for k in ('changed_identity', 'sign', 'added', 'removed')}
                             for c in old['cases'] if 'added' in c]
                new_cases = [{k: c[k] for k in ('changed_identity', 'sign', 'added', 'removed')}
                             for c in new['cases']]
                assert old_cases == new_cases
        entry['thresholds_fixed_scale'] = []
        for distance in (1.5, 1.75, 1.9, 2., 2.1, 2.25, 2.5):
            kept, _ = thin(chain, mode, distance=distance)
            entry['thresholds_fixed_scale'].append(dict(distance=distance, count=len(kept),
                                                        **previous.delta(kept, names(baseline))))
        if mode == 'window':
            entry['window_width_fixed_neighborhood'] = []
            for width in (1.5, 1.75, 2., 2.25, 2.5):
                kept, _ = thin(chain, mode, scale=width)
                entry['window_width_fixed_neighborhood'].append(dict(width=width,
                    **previous.delta(kept, names(baseline))))
        entry['endpoint_sensitivity'] = []
        for endpoint in (-1., 0., 1.):
            kept, _ = thin(chain, mode, endpoint=endpoint)
            entry['endpoint_sensitivity'].append(dict(endpoint=endpoint,
                                                     **previous.delta(kept, names(baseline))))
        static, _ = thin(chain, mode, dynamic=False)
        entry['static_priority'] = previous.delta(static, names(baseline))
        rng = random.Random(20260927)
        for _ in range(20):
            shuffled = copy.deepcopy(adjusted)
            rng.shuffle(shuffled)
            kept, _ = thin(previous.chain(shuffled), mode)
            assert previous.identities(kept) == previous.identities(baseline)
        entry['input_order_checks'] = 20
        score_cases = next(p['cases'] for p in entry['perturbations']
                           if p['scope'] == 'full_pipeline' and p['field'] == 'score'
                           and p['amount'] == .25)
        entry['original_counterexamples'] = []
        for name, sign in [('GPT-6 Astra max AA-public published-price', 1),
                           ('GPT-6 Astra xhigh AA-public published-price', -1)]:
            matches = [c for c in score_cases if c['changed_identity'] == name and c['sign'] == sign]
            entry['original_counterexamples'].append(dict(identity=name, score_delta=sign*.25,
                changed=bool(matches), difference=matches[0] if matches else None))
        artificial = original_result['synthetic_endpoint_example']['input']
        kept, _ = thin(artificial, mode)
        assert 'top' not in names(kept)
        entry['synthetic_endpoint_kept'] = previous.identities(kept)
        result['modes'][mode] = entry
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
