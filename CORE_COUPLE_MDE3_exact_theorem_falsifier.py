from collections import defaultdict
from fractions import Fraction
from math import comb
import json
try:
 import sympy as sp
except Exception:
 sp=None


def R_brute(C,n,g,m,vH,vL):
    best=-10**9
    for h in range(g+1):
        for l in range(n-g+1):
            if h+m*l<=C:
                best=max(best,vH*h+vL*l)
    return best

def R(C,n,g,m,vH,vL):
    h=min(g,C)
    l=min(n-g,max(0,C-h)//m)
    return vH*h+vL*l

def H(C0,C1,n,g,m,vH,vL): return R(C1,n,g,m,vH,vL)-R(C0,n,g,m,vH,vL)
def Ds(C0,C1,n,m,vH,vL):
    hs=[H(C0,C1,n,g,m,vH,vL) for g in range(n+1)]
    return hs,[hs[i+1]-hs[i] for i in range(n)]

summary={}
# Independent dominance verifier with brute force
count=0; bad=[]
for m in range(2,6):
 for n in range(1,11):
  for C in range(0,m*n+2):
   for vL in range(1,4):
    for vH in range(vL,6):
     for g in range(n+1):
      count+=1
      if R_brute(C,n,g,m,vH,vL)!=R(C,n,g,m,vH,vL):
       bad.append((m,n,C,vL,vH,g))
summary['dominance_cases']=count; summary['dominance_failures']=bad[:10]

# aligned theorem sweep (exact integer arithmetic)
cntA=cntB=cntS=0; badA=[];badB=[];badS=[]
for m in range(2,6):
 for n in range(1,13):
  for vL in range(1,5):
   for vH in range(vL,7):
    for C0 in range(0,m*n+1):
     for r in range(1,5):
      C1=C0+r*m
      _,d=Ds(C0,C1,n,m,vH,vL)
      if C1<=n:
       cntA+=1
       if any(x<0 for x in d): badA.append((m,n,vL,vH,C0,C1,d))
      if C0>=n:
       cntB+=1
       if any(x>0 for x in d): badB.append((m,n,vL,vH,C0,C1,d))
for m in range(2,6):
 for nL in range(1,10):
  for nH in range(nL+1,13):
   for vL in range(1,5):
    for vH in range(vL,7):
     for C0 in range(0,nH+1):
      for r in range(1,5):
       C1=C0+r*m
       if nL<=C0<C1<=nH:
        cntS+=1
        _,dL=Ds(C0,C1,nL,m,vH,vL)
        _,dH=Ds(C0,C1,nH,m,vH,vL)
        if any(x>0 for x in dL) or any(x<0 for x in dH): badS.append((m,nL,nH,vL,vH,C0,C1,dL,dH))
summary.update(A_cases=cntA,A_failures=badA[:10],B_cases=cntB,B_failures=badB[:10],S_cases=cntS,S_failures=badS[:10])

# nonaligned counterexamples by residue
res={}
for m in range(2,6):
 for rem in range(1,m):
  exA=exB=None
  for n in range(1,10):
   if exA and exB: break
   for vL in range(1,3):
    for vH in range(vL,5):
     for C0 in range(0,m*n+1):
      for dcap in range(rem,2*m+1,m):
       if dcap<=0: continue
       C1=C0+dcap
       _,d=Ds(C0,C1,n,m,vH,vL)
       if exA is None and C1<=n and any(x<0 for x in d): exA=(m,rem,n,vL,vH,C0,C1,d)
       if exB is None and C0>=n and any(x>0 for x in d): exB=(m,rem,n,vL,vH,C0,C1,d)
       if exA and exB: break
      if exA and exB: break
    if exA and exB: break
  res[f'm={m},rem={rem}']={'A_counterexample':exA,'B_counterexample':exB}
summary['nonaligned_residue_counterexamples']=res

# nonmonotone example exact polynomial via sympy
if sp:
 eta=sp.symbols('eta', real=True)
 def R0(C,n,g): return R(C,n,g,2,2,1)
 def b_exp(n,C0,C1,p):
  return sp.expand(sum(sp.binomial(n,g)*p**g*(1-p)**(n-g)*(R0(C1,n,g)-R0(C0,n,g)) for g in range(n+1)))
 pL=sp.Rational(1,2)+sp.Rational(4,7)*eta
 pH=sp.Rational(1,2)-sp.Rational(3,7)*eta
 Delta=sp.factor(sp.Rational(1,2)*b_exp(3,2,4,pL)+sp.Rational(1,2)*b_exp(4,2,4,pH))
 dD=sp.factor(sp.diff(Delta,eta))
 crit=[r for r in sp.nroots(sp.Poly(sp.diff(Delta,eta),eta)) if abs(sp.im(r))<1e-12 and -0.875<=float(sp.re(r))<=0.875]
 rootsF=[r for r in sp.nroots(sp.Poly(Delta-sp.Rational(63,50),eta)) if abs(sp.im(r))<1e-12 and -0.875<=float(sp.re(r))<=0.875]
 summary['nonmonotone']={
  'Delta_polynomial':str(Delta),
  'derivative':str(dD),
  'endpoints':{'-7/8':str(sp.simplify(Delta.subs(eta,sp.Rational(-7,8)))),'0':str(sp.simplify(Delta.subs(eta,0))),'7/8':str(sp.simplify(Delta.subs(eta,sp.Rational(7,8))))},
  'critical_eta':[float(sp.re(r)) for r in crit],
  'critical_Delta':[float(Delta.subs(eta,sp.re(r))) for r in crit],
  'F_1_26_roots':[float(sp.re(r)) for r in rootsF]
 }

out='/mnt/data/CORE_COUPLE_MDE3_exact_audit_results.json'
with open(out,'w',encoding='utf-8') as f: json.dump(summary,f,indent=2)
print(json.dumps({
 'dominance_cases':count,'dominance_failures':len(bad),
 'A_cases':cntA,'A_failures':len(badA),
 'B_cases':cntB,'B_failures':len(badB),
 'S_cases':cntS,'S_failures':len(badS),
 'nonaligned':res,
 'nonmonotone':summary.get('nonmonotone')
},indent=2))
print('saved',out)
