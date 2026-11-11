"""GEN2 residual-capacity falsifier, Python >=3.10, standard library only.

See the manuscript supplement for the analytical derivation. Direct count-allocation enumeration supplies
the independent recourse truth; prefix/residue formulas are predictions checked
against it. No GEN1 module is imported or executed. No input is written.

python CORE_COUPLE_GEN2_exact_falsifier_v1.py
python CORE_COUPLE_GEN2_exact_falsifier_v1.py --output CORE_COUPLE_GEN2_exact_results_rerun_v1.json
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from fractions import Fraction as Q
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, combinations_with_replacement, product
import argparse
import json
from math import lcm
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
CMAX = 12


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def serial(x):
    if isinstance(x, Q):
        return str(x)
    if isinstance(x, dict):
        return {str(k): serial(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [serial(v) for v in x]
    return x


def sign(x):
    return (x > 0) - (x < 0)


def h_vectors(max_total):
    for total in range(max_total + 1):
        for x in range(total + 1):
            for y in range(total - x + 1):
                yield (x, y, total - x - y)


def plus(h, grade):
    g = list(h)
    g[grade] += 1
    return tuple(g)


@lru_cache(None)
def direct_values(a, v, g, cmax=CMAX):
    """Enumerate every integer processed-count allocation once, then all capacities.

    No greedy/prefix assumption enters this truth implementation.
    """
    best_at_load = [0] * (cmax + 1)
    for y in product(*(range(t + 1) for t in g)):
        load = sum(ak * t for ak, t in zip(a, y))
        if load <= cmax:
            value = sum(vk * t for vk, t in zip(v, y))
            best_at_load[load] = max(best_at_load[load], value)
    for c in range(1, cmax + 1):
        best_at_load[c] = max(best_at_load[c], best_at_load[c - 1])
    return tuple(best_at_load)


def subset_value(a, v, g, c):
    """Independent complete item-subset enumeration at one capacity."""
    items = [(a[j], v[j]) for j in range(len(a)) for _ in range(g[j])]
    answer = 0
    for mask in range(1 << len(items)):
        load = value = 0
        for i, (ak, vk) in enumerate(items):
            if (mask >> i) & 1:
                load += ak
                value += vk
        if load <= c:
            answer = max(answer, value)
    return answer


def background(a, v, h):
    grades = [j for j in range(len(a)) for _ in range(h[j])]
    B = [0]
    W = [0]
    for j in grades:
        B.append(B[-1] + a[j])
        W.append(W[-1] + v[j])
    return grades, B, W


def prefix_record(a, v, g, c):
    grades, B, W = background(a, v, g)
    m = bisect_right(B, c) - 1
    y = tuple(sum(j == t for j in grades[:m]) for t in range(len(a)))
    return {'allocation': y, 'load': B[m], 'value': W[m], 'slack': c - B[m]}


def state(a, v, h, k, ell, c, bg=None):
    """The proved residual prediction, never using direct recourse values."""
    grades, B, W = bg if bg is not None else background(a, v, h)
    theta_k = sum(a[j] * h[j] for j in range(k)) + a[k]
    theta_l = sum(a[j] * h[j] for j in range(ell)) + a[ell]
    delta = a[ell] - a[k]
    premium = v[k] - v[ell]
    out = {'capacity': c, 'theta_k': theta_k, 'theta_l': theta_l,
           'delta': delta, 'premium': premium, 'phase': 'E', 'tag': 'E',
           'rho': None, 'next_load': None, 'next_grade': None,
           'displaced_grade': None, 'admitted_grade': None,
           'displaced_value': 0, 'admitted_value': 0, 'gain': 0}
    if c < theta_k:
        return out
    middle = c < theta_l
    left = c - (a[k] if middle else a[ell])
    right = c if middle else c - a[k]
    m0 = bisect_right(B, left) - 1
    m1 = bisect_right(B, right) - 1
    require(0 <= m1 - m0 <= 1, 'at-most-one displacement/admission')
    rho = left - B[m0]
    jnext = grades[m0] if m0 < len(grades) else None
    width = a[k] if middle else delta
    hit = jnext is not None and rho + width >= a[jnext]
    require(hit == (m1 > m0), 'residual threshold equivalence')
    out.update(phase='M' if middle else 'L', rho=rho,
               next_load=a[jnext] if jnext is not None else None,
               next_grade=jnext + 1 if jnext is not None else None,
               background_prefix_left=m0, background_prefix_right=m1,
               threshold_left=left, threshold_right=right)
    if middle:
        d = v[jnext] if hit else 0
        out.update(tag='MD' if hit else 'MN', gain=v[k] - d,
                   displaced_grade=jnext + 1 if hit else None, displaced_value=d)
        if hit:
            require(k <= jnext < ell and v[ell] <= d <= v[k], 'displacement grade/value bounds')
    else:
        u = v[jnext] if hit else 0
        out.update(tag='LU' if hit else 'L0', gain=premium + u,
                   admitted_grade=jnext + 1 if hit else None, admitted_value=u)
        if hit:
            require(jnext >= ell and 0 < u <= v[ell], 'admission grade/value bounds')
    require(0 <= out['gain'] <= v[k], 'upgrade gain global bounds')
    return out


def minimal_chain_gain(h, k, ell, c):
    """Independent explicit residue formulas derived before the search."""
    x, y, z = h
    b = x + 2 * y
    if (k, ell) == (0, 1):
        if c <= x:
            return 0
        if c == x + 1:
            return 3
        t = c - 2 - x
        if t < 2 * y:
            return 1 + 2 * (t % 2 == 1)
        u = t - 2 * y
        return 1 + (0 <= u < 3 * z and u % 3 == 2)
    if (k, ell) == (1, 2):
        if c < b + 2:
            return 0
        if c == b + 2:
            return 2
        t = c - 3 - b
        return 1 + (0 <= t < 3 * z and t % 3 == 2)
    require((k, ell) == (0, 2), 'strict-chain upgrade')
    if c <= x:
        return 0
    if c < b + 3:
        return 1 if c <= b and (c - x) % 2 == 0 else 3
    t = c - 3 - b
    return 2 + (0 <= t < 3 * z and t % 3 in (1, 2))


def table_difference(sa, sb, v, ell):
    """Operational sign table: no optimal values or direct U_b-U_a used."""
    A, B = sa['tag'], sb['tag']
    da, db = sa['displaced_value'], sb['displaced_value']
    ua, ub = sa['admitted_value'], sb['admitted_value']
    premium = sa['premium']
    if A == 'E':
        return sb['gain']
    if A == 'MD':
        if B == 'MD':
            require(da >= db, 'displaced values progress down grade chain')
            return da - db
        if B == 'MN':
            return da
        if B == 'L0':
            return da - v[ell]
        if B == 'LU':
            return da - v[ell] + ub
    if A == 'MN':
        if B == 'MD':
            return -db
        if B == 'MN':
            return 0
        if B == 'L0':
            return -v[ell]
        if B == 'LU':
            return ub - v[ell]
    if A == 'L0':
        if B == 'L0':
            return 0
        if B == 'LU':
            return ub
    if A == 'LU':
        if B == 'L0':
            return -ua
        if B == 'LU':
            require(ua >= ub, 'admitted values progress down grade chain')
            return ub - ua
    raise AssertionError(('impossible phase transition', A, B, premium))


def witness_key(case):
    return (sum(case['h']) + 1, max(case['a']), sum(case['a']), tuple(case['a']),
            max(case['v']), sum(case['v']), tuple(case['v']), case['cb'], case['ca'],
            tuple(case['h']), case['k'], case['ell'])


def witness(a, v, h, k, ell, ca, cb, sa, sb, d):
    ga, gb = plus(h, ell), plus(h, k)
    return {'a': a, 'v': v, 'h': h, 'n': sum(h) + 1, 'k': k + 1, 'ell': ell + 1,
            'ca': ca, 'cb': cb, 'D': d, 'residual_a': sa, 'residual_b': sb,
            'before': {str(c): prefix_record(a, v, ga, c) for c in (ca, cb)},
            'after': {str(c): prefix_record(a, v, gb, c) for c in (ca, cb)}}


RULES = {
    'exact_residual_nonnegative': ('all', 'D>=0', 'both'),
    'exact_residual_nonpositive': ('all', 'D<=0', 'both'),
    'exact_residual_zero': ('all', 'D=0', 'both'),
    'late_new_admission_strict_positive': ('both late', 'D>0', 'both'),
    'baseline_early_nonnegative': ('all', 'D>=0', 'sufficient'),
    'baseline_middle_displacement_nonnegative': ('all', 'D>=0', 'sufficient'),
    'baseline_middle_no_displacement_nonpositive': ('all', 'D<=0', 'sufficient'),
    'late_no_admissions_zero': ('both late', 'D=0', 'sufficient'),
    'late_same_next_grade_aligned_zero': ('both late', 'D=0', 'sufficient'),
    'rejected_late_residual_nondecrease_nonnegative': ('both late', 'D>=0', 'unproved reduction'),
    'rejected_late_equal_admission_status_zero': ('both late', 'D=0', 'unproved reduction'),
    'rejected_late_any_expanded_admission_positive': ('both late', 'D>0', 'unproved reduction'),
    'rejected_late_always_nonpositive': ('both late', 'D<=0', 'unproved reduction'),
    'excluded_LCM_scarce_nonnegative': ('all', 'D>=0', 'GEN1 excluded rule'),
    'excluded_LCM_all_best_capable_nonpositive': ('all', 'D<=0', 'GEN1 excluded rule')
}


def rule_inputs(a, v, h, k, ell, ca, cb, sa, sb, d, predicted):
    late = sa['phase'] == sb['phase'] == 'L'
    ia, ib = sa['tag'] == 'LU', sb['tag'] == 'LU'
    samegrade = late and sa['next_grade'] is not None and sa['next_grade'] == sb['next_grade']
    conditions = {
        'exact_residual_nonnegative': predicted >= 0,
        'exact_residual_nonpositive': predicted <= 0,
        'exact_residual_zero': predicted == 0,
        'late_new_admission_strict_positive': not ia and ib,
        'baseline_early_nonnegative': sa['tag'] == 'E',
        'baseline_middle_displacement_nonnegative': sa['tag'] == 'MD',
        'baseline_middle_no_displacement_nonpositive': sa['tag'] == 'MN',
        'late_no_admissions_zero': not ia and not ib,
        'late_same_next_grade_aligned_zero': samegrade and (cb - ca) % sa['next_load'] == 0,
        'rejected_late_residual_nondecrease_nonnegative': late and sb['rho'] >= sa['rho'],
        'rejected_late_equal_admission_status_zero': ia == ib,
        'rejected_late_any_expanded_admission_positive': ib,
        'rejected_late_always_nonpositive': True,
        'excluded_LCM_scarce_nonnegative': cb <= (sum(h) + 1) * a[0] and (cb - ca) % lcm(*a) == 0,
        'excluded_LCM_all_best_capable_nonpositive': ca >= (sum(h) + 1) * a[0] and (cb - ca) % lcm(*a) == 0
    }
    targets = {'D>=0': d >= 0, 'D<=0': d <= 0, 'D=0': d == 0, 'D>0': d > 0}
    return late, conditions, targets


def bounded_search():
    stats = {name: {'applicable_cases': 0, 'condition_true': 0, 'target_true': 0,
                    'sufficiency_failures': 0, 'necessity_failures': 0,
                    'smallest_sufficiency_counterexample': None,
                    'smallest_necessity_counterexample': None}
             for name in RULES}
    cells = defaultdict(Counter)
    detailed_cells = defaultdict(Counter)
    total = equal = gainchecks = prefixchecks = 0
    all_signs = Counter()
    for a in combinations_with_replacement(range(1, 5), 3):
        for vv in combinations_with_replacement(range(1, 4), 3):
            v = tuple(reversed(vv))
            for h in h_vectors(4):
                bg = background(a, v, h)
                for k, ell in combinations(range(3), 2):
                    after = direct_values(a, v, plus(h, k))
                    before = direct_values(a, v, plus(h, ell))
                    states = [state(a, v, h, k, ell, c, bg) for c in range(CMAX + 1)]
                    for c, s in enumerate(states):
                        require(after[c] - before[c] == s['gain'], 'insertion residual identity')
                        gainchecks += 1
                        for g, truth in ((plus(h, k), after), (plus(h, ell), before)):
                            require(prefix_record(a, v, g, c)['value'] == truth[c], 'prefix solution vs direct counts')
                            prefixchecks += 1
                    for ca, cb in combinations(range(CMAX + 1), 2):
                        sa, sb = states[ca], states[cb]
                        d = (after[cb] - before[cb]) - (after[ca] - before[ca])
                        predicted = table_difference(sa, sb, v, ell)
                        require(d == predicted, 'complete operational sign table')
                        if a[k] == a[ell]:
                            require(d >= 0 and sa['tag'] != 'MN' and sb['tag'] != 'MN'
                                    and sa['tag'] != 'LU' and sb['tag'] != 'LU', 'T5 limiting case')
                            equal += 1
                            continue
                        total += 1
                        sg = str(sign(d))
                        all_signs[sg] += 1
                        cells[(sa['tag'], sb['tag'])][sg] += 1
                        descriptor = (sa['tag'], sb['tag'], a[ell] - a[k],
                                      sa['rho'], sa['next_load'], sa['displaced_grade'], sa['admitted_grade'],
                                      sb['rho'], sb['next_load'], sb['displaced_grade'], sb['admitted_grade'])
                        detailed_cells[descriptor][sg] += 1
                        late, conditions, targets = rule_inputs(a, v, h, k, ell, ca, cb, sa, sb, d, predicted)
                        candidate = None
                        for name, (domain, target, claim) in RULES.items():
                            if domain == 'both late' and not late:
                                continue
                            s = stats[name]
                            x, y = conditions[name], targets[target]
                            s['applicable_cases'] += 1
                            s['condition_true'] += bool(x)
                            s['target_true'] += bool(y)
                            for kind, failed in (('sufficiency', x and not y), ('necessity', y and not x)):
                                if failed:
                                    s[kind + '_failures'] += 1
                                    old = s['smallest_' + kind + '_counterexample']
                                    if old is None or (sum(h)+1, max(a), sum(a), a, max(v), sum(v), v, cb, ca, h, k+1, ell+1) < witness_key(old):
                                        if candidate is None:
                                            candidate = witness(a, v, h, k, ell, ca, cb, sa, sb, d)
                                        s['smallest_' + kind + '_counterexample'] = candidate
    for name, s in stats.items():
        suff = s['sufficiency_failures'] == 0
        nec = s['necessity_failures'] == 0
        s['finite_domain_status'] = 'both' if suff and nec else 'sufficient_only' if suff else 'necessary_only' if nec else 'neither'
        s['domain'], s['target'], s['analytical_status'] = RULES[name]
        if RULES[name][2] in ('both', 'sufficient'):
            require(suff, 'proved sufficient rule failed: ' + name)
        if RULES[name][2] == 'both':
            require(nec, 'proved equivalence failed: ' + name)
        if name.startswith(('rejected_', 'excluded_')):
            require(not suff, 'declared rejected candidate lacks witness: ' + name)
    records = []
    names = ('state_a','state_b','delta','rho_a','next_load_a','displaced_grade_a','admitted_grade_a',
             'rho_b','next_load_b','displaced_grade_b','admitted_grade_b')
    for desc, signs in sorted(detailed_cells.items(), key=lambda kv: repr(kv[0])):
        records.append({'descriptor': dict(zip(names, desc)), 'sign_counts': dict(signs), 'cases': sum(signs.values())})
    return {'cross_load_pairs': total, 'equal_load_pairs': equal,
            'single_capacity_gain_identity_checks': gainchecks,
            'prefix_value_vs_count_allocation_checks': prefixchecks,
            'cross_load_sign_counts': dict(all_signs), 'candidate_rules': stats,
            'phase_pair_classification': [{'state_a': a, 'state_b': b, 'sign_counts': dict(signs), 'cases': sum(signs.values())}
                                           for (a,b),signs in sorted(cells.items())],
            'residual_descriptor_fields': names, 'residual_descriptor_cell_count': len(records),
            'residual_descriptor_classification': records,
            'smallest_order': 'n, max(a), sum(a), a lexicographic, max(v), sum(v), v lexicographic, Cb, Ca, h lexicographic, k, ell; minimum over complete main domain',
            'domain': {'K':3, 'loads':'all 1<=a1<=a2<=a3<=4',
                       'values':'all 3>=v1>=v2>=v3>=1', 'background':'all h>=0 with sum(h)=0..4 (n=1..5)',
                       'capacities':'all integer 0<=Ca<Cb<=12', 'upgrades':'all k<ell; cross-load and equal-load recorded separately'},
            'failures_of_proved_claims': []}


def strict_and_rational_checks():
    strict_gains = strict_pairs = rational_gains = rational_pairs = 0
    for a, v, limit in [((1,2,3),(3,2,1),6), ((1,2,3),(Q(7,3),Q(5,3),Q(2,3)),2)]:
        rational = isinstance(v[0], Q)
        for h in h_vectors(limit):
            for k, ell in combinations(range(3),2):
                before = direct_values(a,v,plus(h,ell))
                after = direct_values(a,v,plus(h,k))
                ss = [state(a,v,h,k,ell,c) for c in range(CMAX+1)]
                for c,s in enumerate(ss):
                    require(after[c]-before[c] == s['gain'], 'strict/rational residual identity')
                    if not rational:
                        require(s['gain'] == minimal_chain_gain(h,k,ell,c), 'minimal strict-chain explicit residue formula')
                        strict_gains += 1
                    else:
                        rational_gains += 1
                for ca,cb in combinations(range(CMAX+1),2):
                    d = (after[cb]-before[cb])-(after[ca]-before[ca])
                    require(d == table_difference(ss[ca],ss[cb],v,ell), 'strict/rational sign table')
                    if rational:
                        rational_pairs += 1
                    else:
                        strict_pairs += 1
    return {'strict_chain_single_capacity_formula_checks': strict_gains,
            'strict_chain_capacity_pair_checks': strict_pairs,
            'strict_chain_domain':'a=(1,2,3),v=(3,2,1); all sum(h)=0..6; all k<ell; C=0..12 and all capacity pairs',
            'rational_single_capacity_identity_checks': rational_gains,
            'rational_pair_checks': rational_pairs,
            'rational_domain':'a=(1,2,3),v=(7/3,5/3,2/3); all sum(h)=0..2; all k<ell; C=0..12 and all pairs',
            'failures':[]}


def independent_subsets():
    tested = 0
    families = [((1,2,3),(3,2,1)), ((1,1,2),(3,2,1)),
                ((2,3,4),(3,2,1)), ((1,3,4),(2,2,1))]
    for a,v in families:
        for g in h_vectors(5):
            vals = direct_values(a,v,g)
            for c in range(CMAX+1):
                require(vals[c] == subset_value(a,v,g,c), 'independent item subset recourse')
                tested += 1
    return {'comparisons':tested, 'families':families,
            'domain':'all grade-count vectors of size 0..5; C=0..12; direct counts vs independent individual subsets',
            'failures':[]}


def locked_regression(gen1):
    r = json.loads(gen1.read_text())
    structure = r['remanufacturing_structure']
    cases = []
    def check(name,a,v,h,k,ell,ca,cb,expected):
        before=direct_values(a,v,plus(h,ell));after=direct_values(a,v,plus(h,k))
        d=(after[cb]-before[cb])-(after[ca]-before[ca])
        sa=state(a,v,h,k,ell,ca);sb=state(a,v,h,k,ell,cb)
        require(d==expected and table_difference(sa,sb,v,ell)==d, 'locked ' + name)
        entry=witness(a,v,h,k,ell,ca,cb,sa,sb,d)
        entry['name']=name
        # Independent enumeration includes every one of the four recourse values.
        for g,values in ((plus(h,k),after),(plus(h,ell),before)):
            for c in (ca,cb):
                require(subset_value(a,v,g,c)==values[c], 'locked subset ' + name)
        cases.append(entry)
    for item in structure['packing_counterexamples']:
        ca,cb=item['capacities']
        check(item['name'],tuple(item['a']),tuple(item['v']),tuple(item['h']),item['k']-1,item['ell']-1,ca,cb,item['D'])
    for regime, item in structure['adversarial_sign_search'].items():
        t=item['first']
        check('GEN1_first_'+regime,tuple(t['a']),tuple(t['v']),tuple(t['h']),t['k']-1,t['ell']-1,t['ca'],t['cb'],t['D'])
    t=structure['strict_equal_load_example'];ca,cb=t['capacities']
    check('GEN1_strict_equal_load_positive',tuple(t['a']),tuple(t['v']),tuple(t['h']),t['k']-1,t['ell']-1,ca,cb,t['D'])
    check('GEN1_directional_strict_event',(1,1,2),(3,2,1),(2,0,0),0,1,2,3,1)
    # Reconstruct all three locked GEN1 directional expectations exactly.
    directional=structure['heterogeneous_load_directional_family_example']
    exp_values={}
    for eta in (-Q(1,3),Q(0),Q(1,3)):
        ps=[(Q(1,3)+eta,Q(1,3)-eta,Q(1,3)),
            (Q(1,3)-eta/3,Q(1,3)+eta/3,Q(1,3))]
        val=Q(0)
        from math import factorial
        for n,p in zip((1,3),ps):
            for g in (x for x in h_vectors(n) if sum(x)==n):
                mass=Q(factorial(n),factorial(g[0])*factorial(g[1])*factorial(g[2]))
                for pk,gk in zip(p,g):
                    mass*=pk**gk
                vals=direct_values((1,1,2),(3,2,1),g)
                val+=Q(1,2)*mass*(vals[3]-vals[2])
        require(str(val)==directional['endpoint_values'][str(eta)], 'GEN1 directional expectation')
        exp_values[str(eta)]=str(val)
    # Preserve the GEN1 three-alternative operational example without executing GEN1.
    m3 = r['M3_decisions']
    m3_points = []
    for pt in m3['points']:
        ps = [[Q(p) for p in row] for row in pt['p']]
        values = []
        for cap in m3['capacities']:
            value = Q(0)
            for n, q, p in zip(m3['n'], map(Q,m3['q']), ps):
                for g in (x for x in h_vectors(n) if sum(x)==n):
                    mass=Q(factorial(n),factorial(g[0])*factorial(g[1])*factorial(g[2]))
                    for pk,gk in zip(p,g):
                        mass*=pk**gk
                    value+=q*mass*direct_values(tuple(m3['a']),tuple(m3['v']),g)[cap]
            values.append(value)
        require(list(map(str,values))==pt['operating_values'],'GEN1 M3 operating values')
        net=[value-Q(cost) for value,cost in zip(values,m3['costs'])]
        require(list(map(str,net))==pt['net_values'],'GEN1 M3 net values')
        opt=[i+1 for i,value in enumerate(net) if value==max(net)]
        require(opt==pt['argmax'],'GEN1 M3 argmax')
        m3_points.append({'eta':pt['eta'],'operating_values':list(map(str,values)),
                          'net_values':list(map(str,net)),'argmax':opt})
    return {'locked_substitution_cases':len(cases),'locked_four_value_subset_checks':4*len(cases),
            'cases':cases,'directional_exact_expectation_checks':len(exp_values),'directional_values':exp_values,
            'M3_operating_value_checks':len(m3_points)*3,'M3_points':m3_points,
            'authority_results_sha256':sha256(gen1.read_bytes()).hexdigest(),'failures':[]}


def analytic_descriptor_exclusions():
    # These explicit analytical witnesses isolate losses of information in descriptors.
    examples=[]
    for name,a,v,h,k,ell,ca,cb,expected in [
        ('live_next_load_changes_at_equal_residue',(1,2,3),(3,2,1),(0,1,1),0,1,3,5,-2),
        ('two_admissions_with_different_values',(1,2,3),(3,2,1),(0,1,1),0,1,3,6,-1)]:
        sa=state(a,v,h,k,ell,ca);sb=state(a,v,h,k,ell,cb)
        before=direct_values(a,v,plus(h,ell));after=direct_values(a,v,plus(h,k))
        d=(after[cb]-before[cb])-(after[ca]-before[ca])
        require(d==expected and table_difference(sa,sb,v,ell)==d,'analytical descriptor exclusion')
        item=witness(a,v,h,k,ell,ca,cb,sa,sb,d);item['name']=name
        examples.append(item)
    return examples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'generated_results_v1.json')
    parser.add_argument('--gen1-results',type=Path,default=PROJECT/'gen1/expected/CORE_COUPLE_GEN1_exact_results_v1.json')
    args=parser.parse_args()
    require(ROOT.name=='gen2' and args.output.parent.is_dir(),'output parent must exist')
    gen1_before=sha256(args.gen1_results.read_bytes()).hexdigest()
    result={'schema':'CORE_COUPLE_GEN2_exact_results_v1','classification':'A — MATERIAL STRUCTURAL THEOREM',
            'arithmetic':'integer/Fraction; no float, Monte Carlo, or numerical derivative',
            'locked_GEN1_regression':locked_regression(args.gen1_results),
            'analytic_descriptor_exclusions':analytic_descriptor_exclusions(),
            'main_complete_domain':bounded_search(),
            'strict_chain_and_rational_checks':strict_and_rational_checks(),
            'independent_item_subset_checks':independent_subsets(),
            'analytical_evidence':'P1_GEN2_FIRST_DERIVATION_v1.md and P1_GEN2_SCIENTIFIC_RESULT_v1.md; enumeration is not proof',
            'recommendation':'STOP THEORY AND INTEGRATE',
            'untested':['K>3 computational domains (the theorem is proved for finite K)',
                        'loads>4, values outside stated integer box except explicit rational cases, and counts/capacities beyond declared domains',
                        'unordered loads/values, nonpositive values, parameter changes during substitution',
                        'empirical validity, literature novelty, journal readiness, managerial prevalence']}
    require(sha256(args.gen1_results.read_bytes()).hexdigest()==gen1_before,'GEN1 changed')
    args.output.write_text(json.dumps(serial(result),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.output.resolve()),'sha256':sha256(args.output.read_bytes()).hexdigest(),
                      'cross_load_cases':result['main_complete_domain']['cross_load_pairs'],
                      'equal_load_cases':result['main_complete_domain']['equal_load_pairs'],
                      'classification':result['classification']},indent=2))


if __name__=='__main__':
    main()
