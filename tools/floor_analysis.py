#!/usr/bin/env python3
"""Compute the structural floor of a test: the minimum possible makespan, and
hence the maximum achievable tp / norm_tp, from the test file alone.

makespan = last_token - first_arrival
         >= (last_arrival - first_arrival) + T_last
where T_last is the isolated critical path of the last-arriving request:
prefill (P PRE -> UP -> P PROC -> DOWN -> P POST) then L_out decode steps.
Every component is mandatory, so this is a true lower bound.
"""
import sys, bisect

def interp(rows, col, x):
    xs = [r[0] for r in rows if r[col] >= 0]
    ys = [r[col] for r in rows if r[col] >= 0]
    if not xs: return 0.0
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    i = bisect.bisect_left(xs, x)
    if xs[i] == x: return ys[i]
    x0,x1,y0,y1 = xs[i-1],xs[i],ys[i-1],ys[i]
    return y0 + (y1-y0)*(x-x0)/(x1-x0)

def analyse(path):
    L = [l for l in open(path).read().split('\n') if l.strip()]
    K,S,lat,bw,bpt,layers = L[0].split()
    K,S,lat,bw,bpt,layers = int(K),float(S),float(lat),float(bw),int(bpt),int(layers)
    SLO1,SLO2,tpUB,tpBase,distBase,wtp,wc = [float(x) for x in L[1].split()]
    n = int(L[2]); rows=[[float(v) for v in L[3+i].split()] for i in range(n)]
    rows.sort()
    R = int(L[3+n])
    reqs = [[float(p) for p in L[4+n+i].split()] for i in range(R)]
    b = 8.0*bpt/(bw*1e6)                       # ms of link time per token
    arrivals=[r[0] for r in reqs]
    first,last = min(arrivals), max(arrivals)
    span = last-first
    sumout = sum(int(r[2]) for r in reqs)
    li = next(int(r[1]) for r in reqs if r[0]==last)
    lo = next(int(r[2]) for r in reqs if r[0]==last)
    tdr = (S+interp(rows,1,li)) + (lat+li*b) + (S+interp(rows,2,li)) + (lat+li*b) + (S+interp(rows,3,li))
    per_tok = (S+interp(rows,4,1)) + (lat+b) + (S+interp(rows,5,1)) + (lat+b) + (S+interp(rows,6,1))
    Tlast = tdr + lo*per_tok
    mk = span + Tlast
    tpmax = sumout/mk if mk>0 else 0
    ntp = (tpmax-tpBase)/(tpUB-tpBase) if tpUB!=tpBase else 0
    return dict(path=path,R=R,K=K,span=span,sumout=sumout,tdr=tdr,per_tok=per_tok,
                Tlast=Tlast,mkmin=mk,tpmax=tpmax,tpUB=tpUB,tpBase=tpBase,
                ntpmax=ntp,wtp=wtp,wc=wc,SLO1=SLO1,SLO2=SLO2,layers=layers)

for p in sys.argv[1:]:
    try: d=analyse(p)
    except Exception as e: print(f"{p}: ERR {e}"); continue
    print(f"\n=== {p} ===")
    print(f"  R={d['R']} K={d['K']} layers={d['layers']} sumL_out={d['sumout']}")
    print(f"  arrival span      {d['span']:>18,.1f}")
    print(f"  last req TDR      {d['tdr']:>18,.1f}   per-token {d['per_tok']:,.3f}")
    print(f"  T_last (floor)    {d['Tlast']:>18,.1f}")
    print(f"  makespan FLOOR    {d['mkmin']:>18,.1f}   (span is {100*d['span']/d['mkmin']:.2f}% of it)")
    print(f"  tp_max            {d['tpmax']:.9f}   tp_UB {d['tpUB']:.9f}  tp_base {d['tpBase']:.9f}")
    print(f"  ==> norm_tp CEILING = {d['ntpmax']:.4f}   (w_tp={d['wtp']:.2f} -> max tp score {1000*d['wtp']*min(1,max(0,d['ntpmax'])):.1f})")
