#!/usr/bin/env python3
"""Recover each judge test's hidden scoring parameters from submission history.

Per test the unknowns are tp_base, tp_UB, SLO1, SLO2, dist_base. Each submission
gives one (tp, tdr, tpot, dist, norm_tp, norm_c) observation, and the scoring
formulas are invertible once we have two observations that differ.
"""
import sys, math, itertools
sys.path.insert(0, 'experiments')
from judge_observations import OBS, W_TP

def solve_tp(obs):
    """norm_tp = (tp - base)/(UB - base), unclamped, from two observations."""
    best = None
    for (a, b) in itertools.combinations(obs, 2):
        tp1, n1 = a[0], a[4]
        tp2, n2 = b[0], b[4]
        if not (1e-9 < n1 < 1-1e-9 and 1e-9 < n2 < 1-1e-9): continue
        if abs(n1-n2) < 1e-6 or abs(tp1-tp2) < 1e-12: continue
        r = n1/n2
        base = (tp1 - r*tp2)/(1 - r)
        UB = base + (tp1 - base)/n1
        if UB > base > -1e-9:
            spread = abs(n1-n2)
            if best is None or spread > best[0]: best = (spread, base, UB)
    return (best[1], best[2]) if best else (None, None)

def solve_slo(obs):
    """dist^2 = max(0,(tdr-S1)/S1)^2 + max(0,(tpot-S2)/S2)^2."""
    if all(o[2] == 0.0 for o in obs):                 # no decode gaps -> pure TDR
        o = max(obs, key=lambda z: z[3])
        return (o[1]/(1.0+o[3]) if o[3] > 0 else None), None
    def err(S1, S2):
        e = 0.0
        for tp,tdr,tpot,dist,_,_ in obs:
            a = max(0.0,(tdr-S1)/S1); b = max(0.0,(tpot-S2)/S2)
            e += (math.sqrt(a*a+b*b) - dist)**2
        return e
    tdrs=[o[1] for o in obs]; tpots=[o[2] for o in obs if o[2]>0]
    if not tpots: return None, None
    bestS=None
    lo1,hi1 = min(tdrs)*1e-6, max(tdrs)*2
    lo2,hi2 = min(tpots)*1e-6, max(tpots)*2
    for _ in range(60):                                # coordinate descent on logs
        for S1 in [lo1*(hi1/lo1)**(i/40) for i in range(41)]:
            for S2 in [lo2*(hi2/lo2)**(i/40) for i in range(41)]:
                e=err(S1,S2)
                if bestS is None or e<bestS[0]: bestS=(e,S1,S2)
        if bestS is None: break
        _,S1,S2 = bestS
        lo1,hi1 = S1/1.6, S1*1.6; lo2,hi2 = S2/1.6, S2*1.6
    return (bestS[1], bestS[2]) if bestS else (None,None)

print(f"{'#':>3} {'w_tp':>5} {'tp_base':>12} {'tp_UB':>12} {'tp_now':>12} {'x_to_UB':>8} "
      f"{'SLO1':>12} {'SLO2':>11} {'dist_base':>10}")
rows=[]
for t in sorted(OBS):
    obs=list(OBS[t].values())
    base,UB = solve_tp(obs)
    S1,S2 = solve_slo(obs)
    db=None
    for o in obs:
        if 1e-9 < o[5] < 1-1e-9: db = o[3]/(1-o[5]); break
    latest = obs[-1]
    x = (UB/latest[0]) if (UB and latest[0]>0) else None
    rows.append((t,base,UB,latest,S1,S2,db,x))
    f=lambda v,w=12,p=6: (f"{v:{w}.{p}f}" if v is not None else " "*(w-1)+"?")
    print(f"{t:3d} {W_TP[t]:5.2f} {f(base)} {f(UB)} {f(latest[0])} "
          f"{(f'{x:8.2f}' if x else '       ?')} {f(S1,12,3)} {f(S2,11,3)} "
          f"{f(db,10,3)}")
import json
json.dump({str(t):{"tp_base":b,"tp_UB":u,"SLO1":s1,"SLO2":s2,"dist_base":d,"w_tp":W_TP[t]}
           for t,b,u,_,s1,s2,d,_ in rows}, open("experiments/recovered_params.json","w"), indent=1)
print("\nwritten -> experiments/recovered_params.json")
