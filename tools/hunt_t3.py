#!/usr/bin/env python3
"""Search physical parameter space for a config reproducing judge test #3.

#3's signature is a contradiction that must be reproduced ALL AT ONCE:
    tdr  ~ 1355.5      tpot ~ 132.84      tp ~ 0.004408
    norm_tp = 0.60  -> our makespan BEATS the sequential reference
    norm_c  = 0     -> our dist is NOT better than the reference's
The last two together force tpot_ref << tpot_ours: the reference, which always
uses groups of 1, gets roughly HALF our inter-token gap. Any config that
reproduces `tpot_ours / tpot_ref ~ 2` tells us what structurally inflates it.
"""
import itertools, random, subprocess, sys, os, math
sys.path.insert(0, 'tools')
from gen_test import Curve, reference_schedule

f = lambda x: f"{x:.9f}"
SOLVER = './build/local/solver'

def write(path, K,S,lat,bw,bpt,layers, SLO1,SLO2,tpUB,tpb,db, rows, reqs):
    o=[f"{K} {f(S)} {f(lat)} {f(bw)} {bpt} {layers}",
       f"{f(SLO1)} {f(SLO2)} {f(tpUB)} {f(tpb)} {f(db)} {f(0.0)} {f(1.0)}", str(len(rows))]
    for r in rows: o.append(str(r[0])+" "+" ".join(f(v) for v in r[1:]))
    o.append(str(len(reqs)))
    for a,li,lo in reqs: o.append(f"{f(a)} {li} {lo}")
    open(path,'w').write("\n".join(o)+"\n")

def run(path):
    r=subprocess.run([sys.executable,'tools/interactor.py','--test',path,'--solver',SOLVER],
                     capture_output=True,text=True,timeout=600)
    for line in r.stdout.splitlines():
        if line.startswith('score='):
            g=lambda k: float(line.split(k+'=')[1].split()[0].rstrip(')'))
            return g('tp'), g('tdr'), g('tpot')
    return None

rng=random.Random(20260815)
print(f"{'K':>2} {'S':>5} {'lat':>6} {'Lin':>5} {'Lout':>5} {'gapf':>5} "
      f"{'tdr':>9} {'tpot':>8} {'tpot_ref':>9} {'ratio':>6} {'tp/tp_ref':>9}")
hits=[]
for trial in range(40):
    K=rng.choice([1,2,4,8]); S=rng.choice([1.0,3.0,5.0,10.0])
    lat=rng.choice([0.5,5.0,20.0,50.0]); bw=rng.choice([0.05,0.5,5.0,50.0])
    bpt=rng.choice([1000,50000,500000]); layers=rng.choice([1,8,64])
    LIN=rng.choice([16,128,1024,4096]); LOUT=rng.choice([2,5,20,100])
    R=rng.choice([40,120]); gapf=rng.choice([0.3,0.6,1.0,2.0])
    b=8.0*bpt/(bw*1e6)
    dp=rng.choice([1.0,10.0,60.0]); steep=rng.choice([1.0,1.5,2.5])
    rows=[]
    for bs in (1,2,4,16,64,LIN if LIN not in (1,2,4,16,64) else 256):
        sc=bs**0.5 if steep>1 else 1.0
        rows.append((bs, 20.0, 5.0*bs, 20.0, dp*sc*steep/2.5+dp, dp*sc, dp*sc))
    rows=sorted(set(rows))
    cols=[Curve([(int(r[0]), r[1+c]) for r in rows]) for c in range(6)]
    loop1=3*S+cols[3].at(1)+cols[4].at(1)+cols[5].at(1)+2*(lat+b)
    life=2*S+cols[0].at(LIN)+cols[1].at(LIN)+cols[2].at(LIN)+2*(lat+LIN*b)+LOUT*loop1
    reqs=[(i*life*gapf, LIN, LOUT) for i in range(R)]
    cfg=dict(S=S,lat=lat,bw=bw,bpt=bpt)
    tpr,tdrr,tpotr = reference_schedule(cfg,[[a,li,lo] for a,li,lo in reqs],cols)
    write('/tmp/h.txt',K,S,lat,bw,bpt,layers, max(tdrr*0.5,1.0), max(tpotr*0.5,0.001),
          tpr*3, tpr, 1.0, rows, reqs)
    got=run('/tmp/h.txt')
    if not got: continue
    tp,tdr,tpot=got
    ratio = tpot/tpotr if tpotr>0 else 0
    tprat = tp/tpr if tpr>0 else 0
    flag = "  <== #3 SIGNATURE" if (ratio>1.6 and tprat>1.05) else ""
    print(f"{K:2d} {S:5.1f} {lat:6.1f} {LIN:5d} {LOUT:5d} {gapf:5.2f} "
          f"{tdr:9.1f} {tpot:8.2f} {tpotr:9.2f} {ratio:6.2f} {tprat:9.2f}{flag}")
    if ratio>1.6 and tprat>1.05: hits.append((K,S,lat,LIN,LOUT,gapf,ratio,tprat))
print()
print(f"configs reproducing the #3 signature (tpot ~2x reference AND tp beats reference): {len(hits)}")
for h in hits: print("   ",h)
