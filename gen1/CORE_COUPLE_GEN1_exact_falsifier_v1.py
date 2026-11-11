"""Exact exchange verification. Portable release copy; see portability/PATCHES.md.
The regression snapshot is a subset; input_integrity retains archived provenance.
Use --output to select an output file (its parent must exist).
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as Q
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, combinations_with_replacement, product
import json
from math import comb, factorial, lcm
from pathlib import Path
import zipfile


# Sparse exact polynomials: exponent tuples -> Fraction coefficients.
def add(*ps):
    out = {}
    for p in ps:
        for m, c in p.items():
            out[m] = out.get(m, Q(0)) + c
    return {m: c for m, c in out.items() if c}


def scale(p, c):
    return {m: x * c for m, x in p.items() if x * c}


def mul(p, r):
    out = {}
    for a, x in p.items():
        for b, y in r.items():
            m = tuple(i + j for i, j in zip(a, b))
            out[m] = out.get(m, Q(0)) + x * y
    return {m: c for m, c in out.items() if c}


def const(x, d):
    return {(0,) * d: Q(x)} if x else {}


def var(i, d):
    return {tuple(int(i == j) for j in range(d)): Q(1)}


def power(p, n, d):
    r = const(1, d)
    for _ in range(n):
        r = mul(r, p)
    return r


def deriv(p, i=0):
    out = {}
    for m, c in p.items():
        if m[i]:
            e = list(m)
            e[i] -= 1
            out[tuple(e)] = c * m[i]
    return out


def evaluate(p, x):
    return sum((c * prod(z ** e for z, e in zip(x, m)) for m, c in p.items()), Q(0))


def prod(xs):
    out = 1
    for x in xs:
        out *= x
    return out


@lru_cache(None)
def counts(n, k):
    if k == 1:
        return ((n,),)
    return tuple((i,) + tail for i in range(n + 1) for tail in counts(n - i, k - 1))


def bumped(h, k):
    g = list(h)
    g[k] += 1
    return tuple(g)


def mass_poly(g, ps, d):
    n = sum(g)
    r = const(factorial(n) // prod(factorial(t) for t in g), d)
    for t, p in zip(g, ps):
        r = mul(r, power(p, t, d))
    return r


def expectation(n, ps, f, d=1):
    return add(*(scale(mass_poly(g, ps, d), f(g)) for g in counts(n, len(ps))))


@lru_cache(None)
def recourse(a, v, g, C):
    """Direct complete enumeration of processed grade-count allocations."""
    return max(sum(vk * yk for vk, yk in zip(v, y))
               for y in product(*(range(gk + 1) for gk in g))
               if sum(ak * yk for ak, yk in zip(a, y)) <= C)


def subset_recourse(a, v, g, C):
    """Independent item-subset enumeration, not count-allocation enumeration."""
    items = [(a[k], v[k]) for k in range(len(a)) for _ in range(g[k])]
    best = 0
    for mask in range(1 << len(items)):
        load = value = 0
        for i, (ak, vk) in enumerate(items):
            if mask & (1 << i):
                load += ak
                value += vk
        if load <= C:
            best = max(best, value)
    return best


def H(a, v, g, ca, cb):
    return recourse(a, v, g, cb) - recourse(a, v, g, ca)


def D(a, v, h, ca, cb, k, ell):
    return H(a, v, bumped(h, k), ca, cb) - H(a, v, bumped(h, ell), ca, cb)


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def render_poly(p):
    return {','.join(map(str, m)): str(c) for m, c in sorted(p.items())}


def rank(columns):
    """Exact rational column elimination on arbitrary hashable row labels."""
    pivots = {}
    for col in columns:
        r = dict(col)
        while r:
            pivot = min(r)
            if pivot not in pivots:
                pivots[pivot] = scale(r, 1 / r[pivot])
                break
            r = add(r, scale(pivots[pivot], -r[pivot]))
    return len(pivots)


def fiber_basis(ns, k):
    """All H coefficients -> nonconstant polynomial on the fixed uniform fiber.

    q uniform, r=(mu/k,...,mu/k). First S-1 state compositions are independent
    coordinates; last is eliminated by the item-share constraint.
    """
    s = len(ns)
    d = (s - 1) * (k - 1)
    ps = []
    for i in range(s - 1):
        row = [var(i * (k - 1) + j, d) for j in range(k - 1)]
        ps.append(row + [add(const(1, d), scale(add(*row), -1))])
    last = []
    for j in range(k - 1):
        last.append(scale(add(const(Q(sum(ns), k), d),
                              *(scale(ps[i][j], -ns[i]) for i in range(s - 1))), Q(1, ns[-1])))
    ps.append(last + [add(const(1, d), scale(add(*last), -1))])
    columns = []
    labels = []
    for i, n in enumerate(ns):
        for g in counts(n, k):
            p = scale(mass_poly(g, ps[i], d), Q(1, s))
            columns.append({m: c for m, c in p.items() if any(m)})
            labels.append((i, g))
    return columns, labels


def global_basis(ns, k):
    s = len(ns)
    d = s * (k - 1)
    ps = []
    for i in range(s):
        row = [var(i * (k - 1) + j, d) for j in range(k - 1)]
        ps.append(row + [add(const(1, d), scale(add(*row), -1))])
    columns = []
    for i, n in enumerate(ns):
        for g in counts(n, k):
            p = mass_poly(g, ps[i], d)
            col = {}
            for st, (u, t) in enumerate(combinations(range(s), 2)):
                for j in range(k - 1):
                    r = {}
                    if i == u:
                        r = scale(deriv(p, i * (k - 1) + j), Q(1, n))
                    if i == t:
                        r = scale(deriv(p, i * (k - 1) + j), -Q(1, n))
                    col.update({(st, j, m): c for m, c in r.items()})
            columns.append(col)
    return columns


def regression(z):
    out = {'failures': [], 'authority': 'archive frozen outputs, read-only'}
    frozen = json.loads(z.read('frozen_reproducibility/CORE_COUPLE_MDE3_exact_audit_results.json'))
    clean = json.loads(z.read('frozen_reproducibility/CORE_COUPLE_cleanroom_checker_results.json'))
    closed_checks = 0
    for m in range(2, 6):
        for n in range(1, 11):
            for C in range(m * n + 2):
                for vl in range(1, 4):
                    for vh in range(vl, 6):
                        for g in range(n + 1):
                            h = min(g, C)
                            closed = vh * h + vl * min(n - g, max(0, C - h) // m)
                            require(recourse((1, m), (vh, vl), (g, n - g), C) == closed, '2-grade recourse')
                            closed_checks += 1
    require(closed_checks == frozen['dominance_cases'], 'frozen recourse count')
    out['recourse_cases'] = closed_checks
    out['recourse_ranges'] = 'exact full frozen domain: m=2..5,n=1..10,C=0..mn+1,vL=1..3,vH=vL..5,g=0..n'
    # Independently reconstruct every frozen aligned sign test using direct recourse.
    ac = bc = sc = 0
    for m in range(2, 6):
        for n in range(1, 13):
            for vl in range(1, 5):
                for vh in range(vl, 7):
                    for ca in range(m * n + 1):
                        for r in range(1, 5):
                            cb = ca + r * m
                            if cb <= n or ca >= n:
                                ds = [D((1, m), (vh, vl), (g, n - 1 - g), ca, cb, 0, 1) for g in range(n)]
                                if cb <= n:
                                    ac += 1
                                    require(min(ds) >= 0, 'frozen A')
                                if ca >= n:
                                    bc += 1
                                    require(max(ds) <= 0, 'frozen B')
    for m in range(2, 6):
        for nl in range(1, 10):
            for nh in range(nl + 1, 13):
                for vl in range(1, 5):
                    for vh in range(vl, 7):
                        for ca in range(nl, nh + 1):
                            for r in range(1, 5):
                                cb = ca + r * m
                                if cb <= nh:
                                    sc += 1
                                    require(all(D((1,m),(vh,vl),(g,nl-1-g),ca,cb,0,1)<=0 for g in range(nl)), 'straddle low')
                                    require(all(D((1,m),(vh,vl),(g,nh-1-g),ca,cb,0,1)>=0 for g in range(nh)), 'straddle high')
    require((ac, bc, sc) == tuple(frozen[x] for x in ('A_cases','B_cases','S_cases')), 'frozen theorem counts')
    out['aligned_cases'] = {'A': ac, 'B': bc, 'straddling': sc}
    out['aligned_ranges'] = 'full frozen domains as stated in frozen source and manifest; direct integer recourse'
    residue_checks = 0
    for record in frozen['nonaligned_residue_counterexamples'].values():
        for label in ('A_counterexample','B_counterexample'):
            m, residue, n, vl, vh, ca, cb, expected_ds = record[label]
            require([D((1,m),(vh,vl),(g,n-1-g),ca,cb,0,1) for g in range(n)] == expected_ds,
                    'frozen nonaligned counterexample')
            residue_checks += 1
    out['frozen_nonaligned_counterexamples_rechecked'] = residue_checks
    eta_ps = [[add(const(Q(1,2),1),scale(var(0,1),Q(4,7))),
               add(const(Q(1,2),1),scale(var(0,1),-Q(4,7)))],
              [add(const(Q(1,2),1),scale(var(0,1),-Q(3,7))),
               add(const(Q(1,2),1),scale(var(0,1),Q(3,7)))]]
    delta = add(*(scale(expectation(n, p, lambda g:H((1,2),(2,1),g,2,4)),Q(1,2))
                  for n,p in zip((3,4),eta_ps)))
    expected = {(0,):Q(98441,76832),(1,):-Q(24696,76832),(2,):Q(50568,76832),
                (3,):Q(1120,76832),(4,):-Q(1296,76832)}
    require(delta == expected, 'locked frozen polynomial')
    for x, val in frozen['nonmonotone']['endpoints'].items():
        require(evaluate(delta, [Q(x)]) == Q(val), 'frozen endpoint')
    rhs = add(*(scale(expectation(n-1,p,lambda h:D((1,2),(2,1),h,2,4,0,1)),c)
                for n,p,c in zip((3,4),eta_ps,(Q(6,7),-Q(6,7)))))
    require(deriv(delta) == rhs, 'exact 2x2 derivative polynomial')
    out['locked_nonmonotone_polynomial'] = render_poly(delta)
    out['locked_2x2_derivative_identity'] = render_poly(rhs)
    for key in ('dominance_failures','A_failures','B_failures','S_failures'):
        require(not frozen[key], 'authority failures')
    out['cleanroom_reference_only'] = clean
    out['cleanroom_limitation'] = 'standalone cleanroom source absent; its checks are not claimed rerun'
    return out


FAMILIES = {
    2: [((1,2),(3,1)), ((1,3),(2,1))],
    3: [((1,1,2),(3,2,1)), ((1,2,2),(3,2,1)),
        ((1,2,3),(3,2,1)), ((2,3,4),(4,3,1)),
        ((1,2,3),(1,4,2))]  # Deliberately violates quality-value dominance.
}


def exchange_tests():
    cases = Counter()
    net_checks = 0
    for k, families in FAMILIES.items():
        for s in (2,3):
            for ns in combinations(range(1,5),s):
                for q in [tuple(Q(1,s) for _ in ns), tuple(Q(i+1,s*(s+1)//2) for i in range(s))]:
                    masses = [qi*n for qi,n in zip(q,ns)]
                    for p_mode in range(2):
                        ps = [tuple(Q(1,k) for _ in range(k)) if p_mode==0 else
                              tuple(Q(1+(j+i)%k,k*(k+1)//2) for j in range(k)) for i in range(s)]
                        for caps in [(0,2,4),(1,3,5),(2,4,6)]:
                            for a,v in families:
                                for u,t in combinations(range(s),2):
                                    for grade,ell in combinations(range(k),2):
                                        slope = [Q(0)]*s
                                        slope[u] = 1
                                        slope[t] = -masses[u]/masses[t]
                                        path = [[add(const(p,1),scale(var(0,1),slope[i]*((j==grade)-(j==ell))))
                                                 for j,p in enumerate(ps[i])] for i in range(s)]
                                        # Every grade's pooled expected count is exactly constant.
                                        for j in range(k):
                                            require(not deriv(add(*(scale(path[i][j],masses[i]) for i in range(s)))), 'matched path')
                                        js = [add(*(scale(expectation(n,path[i],lambda g:recourse(a,v,g,C)),q[i])
                                                   for i,n in enumerate(ns))) for C in caps]
                                        for ia,ib in combinations(range(3),2):
                                            ca,cb = caps[ia],caps[ib]
                                            direct = add(js[ib],scale(js[ia],-1))
                                            rhs = scale(add(expectation(ns[u]-1,path[u],lambda h:D(a,v,h,ca,cb,grade,ell)),
                                                            scale(expectation(ns[t]-1,path[t],lambda h:D(a,v,h,ca,cb,grade,ell)),-1)),masses[u])
                                            require(deriv(direct)==rhs, 'general exchange polynomial')
                                            cases[f'S={s},K={k}']+=1
                                            # Fixed costs have zero derivative; check net differences and cocycle.
                                            costs=(Q(0),Q(3,2),Q(13,4))
                                            net=add(direct,const(costs[ia]-costs[ib],1))
                                            require(deriv(net)==rhs,'net pair derivative')
                                        require(add(js[2],scale(js[0],-1)) == add(add(js[1],scale(js[0],-1)),add(js[2],scale(js[1],-1))), 'pair cocycle')
                                        net_checks+=1
    return {'cases_by_SK':dict(cases),'total_pair_identity_cases':sum(cases.values()),
            'M3_cocycle_cases':net_checks,'failures':[],
            'ranges':{'S':[2,3],'K':[2,3],'volumes':'all increasing S-tuples from 1..4',
                      'probabilities':'uniform q and q_i=(i+1)/sum(i+1); uniform p and cyclic (1..K)/sum(1..K)',
                      'capacities':[[0,2,4],[1,3,5],[2,4,6]],'families':FAMILIES,
                      'checks':'all state pairs, grade pairs, capacity pairs; equality of full exact directional polynomials'}}


def converse_tests():
    tests=[]
    for ns,k in [((2,2),2),((2,3),2),((1,3),2),((1,2,3),2),((2,2),3),((1,2,2),3)]:
        cols,_=fiber_basis(ns,k)
        null=len(cols)-rank(cols)
        glob=global_basis(ns,k)
        gn=len(glob)-rank(glob)
        expected=len(ns)+k-1
        require(gn==expected,'global affine dimension')
        if len(ns)>=3 or min(ns)==1:
            require(null==expected,'single-fiber corrected dimension')
        tests.append({'n':ns,'K':k,'H_coefficients':len(cols),'single_uniform_fiber_kernel_dimension':null,
                      'all_fibers_kernel_dimension':gn,'common_affine_dimension':expected})
    bounded=[]
    for ns,k in [((2,2),2),((1,1,1),2),((1,1),3)]:
        cols,labels=fiber_basis(ns,k)
        constant=nonaffine=0;first=None
        # Exact exhaustive coefficient-table search over {-1,0,1}.
        for ys in product((-1,0,1),repeat=len(cols)):
            p=add(*(scale(c,y) for c,y in zip(cols,ys)))
            if p:continue
            constant+=1
            tables=[{g:y for (i,g),y in zip(labels,ys) if i==s} for s in range(len(ns))]
            scores=[]
            affine=True
            for n,tab in zip(ns,tables):
                anchor=(0,)*(k-1)+(n,)
                A=tab[anchor]
                b=[Q(tab[tuple(n if j==u else 0 for j in range(k))]-A,n) for u in range(k-1)]
                affine &= all(y==A+sum(b[j]*g[j] for j in range(k-1)) for g,y in tab.items())
                scores.append(b)
            affine &= all(b==scores[0] for b in scores)
            if not affine:
                nonaffine+=1
                if first is None:first={'labels':labels,'values':ys}
        if len(ns)>=3 or min(ns)==1:require(nonaffine==0,'bounded corrected converse')
        bounded.append({'n':ns,'K':k,'tables_tested':3**len(cols),'invariant_tables':constant,
                        'non_common_affine_invariant_tables':nonaffine,'first_counterexample':first})
    # Smallest nonlinear full-support abstract table example: n=2 in two states.
    # p1=p, p2=1-p, q=1/2, pooled high fraction=1/2.
    p=var(0,1); one_minus=add(const(1,1),scale(p,-1))
    tab1=(0,0,1);tab2=(0,1,1)
    ev=add(scale(expectation(2,[p,one_minus],lambda g:tab1[g[0]]),Q(1,2)),
           scale(expectation(2,[one_minus,p],lambda g:tab2[g[0]]),Q(1,2)))
    require(ev==const(Q(1,2),1),'abstract fixed-fiber counterexample')
    # Distinct-volume version, not asserted to be generated by common recourse primitives.
    ev_distinct=add(scale(expectation(2,[p,one_minus],lambda g:(0,0,1)[g[0]]),Q(3,5)),
                    scale(expectation(3,[one_minus,p],lambda g:(0,1,Q(3,2),Q(3,2))[g[0]]),Q(2,5)))
    require(ev_distinct==const(Q(3,5),1),'distinct volume abstract counterexample')
    # Actual common-primitives recourse example with two labelled, equal-volume regimes.
    ev_rec=add(*(scale(expectation(3,ps,lambda g:H((1,1),(2,1),g,1,2)),Q(1,2))
                 for ps in ([p,one_minus],[one_minus,p])))
    require(ev_rec==const(Q(3,2),1),'recourse fixed-fiber counterexample')
    distinct_search={'configurations':0,'nonaffine_candidates':0,'invariant_nonaffine_counterexamples':[]}
    for n1 in range(1,6):
        for n2 in range(n1+1,7):
            for a in ((1,1),(1,2),(1,3),(2,3)):
                for v in ((2,1),(3,1),(3,2),(1,1)):
                    for ca in range(7):
                        for cb in range(ca+1,9):
                            distinct_search['configurations']+=1
                            hs=[tuple(H(a,v,(g,n-g),ca,cb) for g in range(n+1)) for n in (n1,n2)]
                            if all(all(t[i+2]-2*t[i+1]+t[i]==0 for i in range(len(t)-2)) for t in hs):continue
                            distinct_search['nonaffine_candidates']+=1
                            ep=add(scale(expectation(n1,[p,one_minus],lambda g:hs[0][g[0]]),Q(n2,n1+n2)),
                                   scale(expectation(n2,[one_minus,p],lambda g:hs[1][g[0]]),Q(n1,n1+n2)))
                            if not deriv(ep):
                                distinct_search['invariant_nonaffine_counterexamples'].append(
                                    {'n':[n1,n2],'a':a,'v':v,'ca':ca,'cb':cb,'H':hs})
    distinct_search['ranges']='K=2; 1<=n1<=5,n1<n2<=6; a={(1,1),(1,2),(1,3),(2,3)}; v={(2,1),(3,1),(3,2),(1,1)}; Ca=0..6,Cb=Ca+1..8; q=(n2,n1)/(n1+n2),p2=1-p1'
    return {'dimension_checks':tests,'bounded_search':bounded,'distinct_volume_common_recourse_search':distinct_search,'failures':[],
            'abstract_minimal_example':{'n':[2,2],'q':['1/2','1/2'],'p_high':['p','1-p'],
                 'H_by_high_count':[tab1,tab2],'expected_value':'1/2','scope':'arbitrary H tables; not claimed common-primitives recourse'},
            'distinct_volume_abstract_example':{'n':[2,3],'q':['3/5','2/5'],'p_high':['p','1-p'],
                 'H_by_high_count':[[0,0,1],[0,1,'3/2','3/2']],'expected_value':'3/5',
                 'scope':'arbitrary H tables; common-primitives distinct-volume recourse converse remains unclassified'},
            'common_recourse_equal_volume_example':{'n':[3,3],'q':['1/2','1/2'],'a':[1,1],'v':[2,1],
                 'capacities':[1,2],'H_by_high_count':[1,1,2,2],'expected_value':'3/2',
                 'scope':'two labelled regimes with equal n; not distinct return volumes'}}


def structural_tests():
    checks=independent=greedy=0
    # All ordered weak dominance chains in a small explicit box.
    for a in combinations_with_replacement(range(1,4),3):
        for w in combinations_with_replacement(range(1,4),3):
            v=tuple(reversed(w))
            for n in range(1,5):
                for g in counts(n,3):
                    for C in range(9):
                        rem=C;value=0
                        for ak,vk,gk in zip(a,v,g):
                            take=min(gk,rem//ak);rem-=ak*take;value+=vk*take
                        require(recourse(a,v,g,C)==value,'dominance-prefix lemma')
                        greedy+=1
                for h in counts(n-1,3):
                    for k,ell in combinations(range(3),2):
                        if a[k]!=a[ell]:continue
                        for ca,cb in combinations(range(9),2):
                            require(D(a,v,h,ca,cb,k,ell)>=0,'equal-load group theorem')
                            checks+=1
    for a,v in FAMILIES[3]:
        for n in range(0,6):
            for g in counts(n,3):
                for C in range(13):
                    require(recourse(a,v,g,C)==subset_recourse(a,v,g,C),'independent item subset check')
                    independent+=1
    locked=[]
    for name,n,ca,cb,h,k,ell in [
        ('strict_chain_scarce_lcm_failure',7,1,7,(0,0,6),0,1),
        ('strict_chain_baseline_lcm_failure',2,2,8,(0,1,0),0,2)]:
        a=(1,2,3);v=(3,2,1)
        val=D(a,v,h,ca,cb,k,ell)
        require(val==(-1 if 'scarce' in name else 1),'locked packing counterexample')
        gk=bumped(h,k);gl=bumped(h,ell)
        locked.append({'name':name,'n':n,'a':a,'v':v,'capacities':[ca,cb],
                       'increment_lcm_multiple':(cb-ca)//lcm(*a),'h':h,'k':k+1,'ell':ell+1,
                       'g_k':gk,'g_ell':gl,
                       'R_k':[recourse(a,v,gk,c) for c in (ca,cb)],
                       'R_ell':[recourse(a,v,gl,c) for c in (ca,cb)],'D':val})
    # Bounded adversarial search, including all h and ordered grade substitutions.
    search={}
    for regime in ('scarce','baseline'):
        tested=violations=0;first=None
        for a in ((1,1,2),(1,2,2),(1,2,3)):
            v=(3,2,1);inc=lcm(*a)
            for n in range(1,8):
                for ca in range(9):
                    cb=ca+inc
                    if not (cb<=n*a[0] if regime=='scarce' else ca>=n*a[0]):continue
                    for h in counts(n-1,3):
                        for k,ell in combinations(range(3),2):
                            val=D(a,v,h,ca,cb,k,ell);tested+=1
                            if val<0 if regime=='scarce' else val>0:
                                violations+=1
                                if first is None:first={'a':a,'v':v,'n':n,'ca':ca,'cb':cb,'h':h,'k':k+1,'ell':ell+1,'D':val}
        search[regime]={'tests':tested,'sign_violations':violations,'first':first}
    # Heterogeneous-load, three-grade directional consequence on a full path.
    # n_low=1 is fully served at Ca=2; upgrade grades 2->1 has equal load.
    p=var(0,1)
    low=[add(const(Q(1,3),1),p),add(const(Q(1,3),1),scale(p,-1)),const(Q(1,3),1)]
    high=[add(const(Q(1,3),1),scale(p,-Q(1,3))),
          add(const(Q(1,3),1),scale(p,Q(1,3))),const(Q(1,3),1)]
    delta=add(scale(expectation(1,low,lambda g:H((1,1,2),(3,2,1),g,2,3)),Q(1,2)),
              scale(expectation(3,high,lambda g:H((1,1,2),(3,2,1),g,2,3)),Q(1,2)))
    rhs=scale(expectation(2,high,lambda h:D((1,1,2),(3,2,1),h,2,3,0,1)),-Q(1,2))
    require(deriv(delta)==rhs,'structural directional path')
    require(D((1,1,2),(3,2,1),(2,0,0),2,3,0,1)==1,'strict structural event')
    directional={'a':[1,1,2],'v':[3,2,1],'n':[1,3],'q':['1/2','1/2'],
                 'capacities':[2,3],'eta_interval':['-1/3','1/3'],
                 'Delta_polynomial':render_poly(delta),'derivative_polynomial':render_poly(rhs),
                 'strict_derivative_bound':'Delta_prime <= -(1/2)*p_high,grade1^2 < 0 throughout this path',
                 'endpoint_values':{str(x):str(evaluate(delta,[x])) for x in (-Q(1,3),Q(0),Q(1,3))}}
    return {'equal_load_group_sign_cases':checks,'dominance_prefix_cases':greedy,
            'independent_subset_recourse_cases':independent,'failures':[],
            'ranges':{'equal_load_and_prefix':'K=3; all 1<=a1<=a2<=a3<=3; all 3>=v1>=v2>=v3>=1; n=1..4; C=0..8; all count vectors; equal-load grade pairs and all capacity pairs',
                      'independent_subset':'five K3 FAMILIES (one without dominance); n=0..5; C=0..12; every grade-count vector',
                      'adversarial_sign':'a in {(1,1,2),(1,2,2),(1,2,3)}, v=(3,2,1), n=1..7, Ca=0..8, Cb=Ca+lcm(a), regime-filtered; every h and k<ell'},
            'packing_counterexamples':locked,'adversarial_sign_search':search,
            'heterogeneous_load_directional_family_example':directional,
            'strict_equal_load_example':{'a':[1,1,2],'v':[3,2,1],'capacities':[1,2],
                                         'h':[1,0,0],'k':1,'ell':2,'D':D((1,1,2),(3,2,1),(1,0,0),1,2,0,1)}}


def decisions():
    # A fully exact multi-grade, three-volume, three-capacity decision reversal.
    a=(1,1,2);v=(3,2,1);ns=(2,3,4);q=(Q(1,3),)*3;caps=(1,2,3)
    base=[(Q(1,3),)*3 for _ in ns]
    masses=[qi*n for qi,n in zip(q,ns)]
    points=[]
    raw=[]
    for eta in (-Q(1,3),Q(0),Q(1,3)):
        ps=[list(p) for p in base]
        ps[0][0]+=eta;ps[0][1]-=eta
        ps[2][0]-=masses[0]/masses[2]*eta;ps[2][1]+=masses[0]/masses[2]*eta
        vals=[sum((q[i]*evaluate(expectation(n,[const(p,1) for p in ps[i]],lambda g:recourse(a,v,g,C)),[Q(0)])
                   for i,n in enumerate(ns)),Q(0)) for C in caps]
        raw.append(vals)
        points.append({'eta':str(eta),'p':[[str(p) for p in row] for row in ps],'operating_values':list(map(str,vals))})
    # All three capacity alternatives are uniquely optimal at a tested composition.
    costs=(Q(0),Q(17,10),Q(13,5))
    for pt,vals in zip(points,raw):
        js=[x-f for x,f in zip(vals,costs)]
        top=max(js);opt=[i+1 for i,x in enumerate(js) if x==top]
        require(opt==[i+1 for i,x in enumerate(js) if all(x>=y for y in js)],'pairwise optimality')
        pt.update(net_values=list(map(str,js)),argmax=opt,
                  pairwise_net={f'{i+1}->{j+1}':str(js[j]-js[i]) for i,j in combinations(range(3),2)})
    require(points[0]['argmax']!=points[2]['argmax'],'M3 reversal')
    require({pt['argmax'][0] for pt in points}=={1,2,3} and all(len(pt['argmax'])==1 for pt in points),
            'all three capacities attained uniquely')
    # Sign robustness without value invariance: C=3 made uniformly optimal by fixed costs.
    # On this entire model domain R_C>=0, R_C<=C*max(v)/min(a)<=9.
    robust_costs=(Q(0),Q(10),Q(20))
    for vals in raw:
        js=[x-f for x,f in zip(vals,robust_costs)]
        require(js[0]>max(js[1:]),'robust choice exact bound')
    return {'a':a,'v':v,'n':ns,'q':list(map(str,q)),'capacities':caps,'costs':list(map(str,costs)),
            'matched_exchange':'state1 grade1<-grade2; weighted opposite in state3; state2 fixed',
            'points':points,'pairwise_optimality_checks':len(points)*3,
            'uniform_sign_robust_example':{'costs':list(map(str,robust_costs)),'unique_choice':1,
                 'exact_certificate':'0<=R_C<=9 for all compositions; alternative1 J>=0; alternative2 J<=-1; alternative3 J<=-11'},
            'failures':[]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=Path(__file__).resolve().parents[1]/'input_snapshot/required_frozen_inputs_v1.zip')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('generated_results_v1.json'))
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    require(root.name=='gen1','output root')
    require(args.output.parent.is_dir(),'output parent must exist')
    with zipfile.ZipFile(args.archive) as z:
        before={n:sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
        baseline=root.parent/'input_snapshot/subset_checksums_v1.json'
        if baseline.exists():
            require(before==json.loads(baseline.read_text())['members'],'prework member hashes')
        result={'schema':'CORE_COUPLE_GEN1_exact_results_v1','arithmetic':'Python integer/Fraction sparse polynomials; no float or Monte Carlo',
                'classification':'A','regression':regression(z),'exchange_identity':exchange_tests(),
                'invariance_converse':converse_tests(),'remanufacturing_structure':structural_tests(),
                'M3_decisions':decisions()}
        after={n:sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
    require(before==after,'input member mutation')
    archive_hash=sha256(args.archive.read_bytes()).hexdigest()
    if baseline.exists():require(archive_hash==json.loads(baseline.read_text())['archive_sha256'],'archive hash mutation')
    # Retain the archived full-source-container receipt as provenance only.
    # Actual subset bytes are checked above and by verify_release.py.
    result['input_integrity']=json.loads((root.parent/'input_snapshot/source_input_receipt_v1.json').read_text())
    result['untested']=['non-multinomial conditional laws','continuous grades/volumes/capacities',
        'composition-dependent loads, recovery values, or fixed costs','correlated item grades within a regime',
        'global structural converse restricted to common-primitives distinct-volume S=2 recourse on a single fiber',
        'heterogeneous-load sign theorems beyond the explicitly proved equal-load-group result',
        'empirical prevalence, managerial validation, literature novelty']
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.output.resolve()),'sha256':sha256(args.output.read_bytes()).hexdigest(),
                      'classification':result['classification'],
                      'identity_cases':result['exchange_identity']['total_pair_identity_cases'],
                      'structural_cases':result['remanufacturing_structure']['equal_load_group_sign_cases'],
                      'frozen_unchanged':True},indent=2))


if __name__=='__main__':
    main()
