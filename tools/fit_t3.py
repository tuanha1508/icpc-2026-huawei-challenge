#!/usr/bin/env python3
"""Fit the #3 regime (heavy overlap + huge L_in + small L_out) to its magnitudes."""
import sys, subprocess, itertools
sys.path.insert(0,'tools')
from gen_test import Curve, reference_schedule
f=lambda x:f"{x:.9f}"; SOLVER='./build/local/solver'
TGT=dict(tdr=1355.547361, tpot=132.844473, tp=0.004408)

def build(path,K,S,lat,bw,bpt,layers,LIN,LOUT,R,gapf,dp,ppc,SLO1,SLO2,tpb,tpUB,db):
    b=8.0*bpt/(bw*1e6)
    rows=[(1,20.0,ppc,20.0,dp,dp,dp),(4,20.0,ppc,20.0,dp*1.3,dp*1.3,dp*1.3),
          (64,20.0,ppc,20.0,dp*2.0,dp*2.0,dp*2.0),(LIN,20.0,ppc,20.0,dp*3.0,dp*3.0,dp*3.0)]
    rows=sorted({r[0]:r for r in rows}.values())
    cols=[Curve([(int(r[0]),r[1+c]) for r in rows]) for c in range(6)]
    loop1=3*S+cols[3].at(1)+cols[4].at(1)+cols[5].at(1)+2*(lat+b)
    life=2*S+cols[0].at(LIN)+cols[1].at(LIN)+cols[2].at(LIN)+2*(lat+LIN*b)+LOUT*loop1
    reqs=[(i*life*gapf,LIN,LOUT) for i in range(R)]
    o=[f"{K} {f(S)} {f(lat)} {f(bw)} {bpt} {layers}",
       f"{f(SLO1)} {f(SLO2)} {f(tpUB)} {f(tpb)} {f(db)} {f(0.0)} {f(1.0)}",str(len(rows))]
    for r in rows: o.append(str(int(r[0]))+" "+" ".join(f(v) for v in r[1:]))
    o.append(str(len(reqs)))
    for a,li,lo in reqs: o.append(f"{f(a)} {li} {lo}")
    open(path,'w').write("\n".join(o)+"\n")
    return cols,reqs,dict(S=S,lat=lat,bw=bw,bpt=bpt)

def run(p):
    r=subprocess.run([sys.executable,'tools/interactor.py','--test',p,'--solver',SOLVER],
                     capture_output=True,text=True,timeout=900)
    for l in r.stdout.splitlines():
        if l.startswith('score='):
            g=lambda k: float(l.split(k+'=')[1].split()[0].rstrip(')'))
            return g('tp'),g('tdr'),g('tpot')
    return None

best=None
for LOUT in (2,3,5):
 for gapf in (0.15,0.3,0.5):
  for dp in (8.0,20.0,35.0):
   for ppc in (150.0,400.0,900.0):
    for lat in (0.5,5.0):
     for bpt,bw in ((50000,5.0),(200000,20.0)):
      cols,reqs,cfg=build('/tmp/f.txt',1,10.0,lat,bw,bpt,8,1024,LOUT,60,gapf,dp,ppc,
                          913.203,63.058,0.003119,0.005255,1.21)
      got=run('/tmp/f.txt')
      if not got: continue
      tp,tdr,tpot=got
      err=abs(tdr-TGT['tdr'])/TGT['tdr']+abs(tpot-TGT['tpot'])/TGT['tpot']
      if best is None or err<best[0]:
          tpr,tdrr,tpotr=reference_schedule(cfg,[[a,li,lo] for a,li,lo in reqs],cols)
          best=(err,LOUT,gapf,dp,ppc,lat,bpt,bw,tdr,tpot,tp,tpotr,tpr)
if best:
    e,LOUT,gapf,dp,ppc,lat,bpt,bw,tdr,tpot,tp,tpotr,tpr=best
    print(f"BEST FIT  err={e:.3f}")
    print(f"  L_out={LOUT} gap={gapf} dp={dp} pproc={ppc} lat={lat} bpt={bpt} bw={bw}")
    print(f"  ours : tdr={tdr:10.1f}  tpot={tpot:8.2f}  tp={tp:.6f}")
    print(f"  #3   : tdr={TGT['tdr']:10.1f}  tpot={TGT['tpot']:8.2f}  tp={TGT['tp']:.6f}")
    print(f"  ref  : tpot={tpotr:8.2f}  tp={tpr:.6f}   -> tpot ratio {tpot/tpotr:.2f}, tp ratio {tp/tpr:.2f}")
    build('data/judgecal/t3_fit.txt',1,10.0,lat,bw,bpt,8,1024,LOUT,60,gapf,dp,ppc,
          913.203,63.058,0.003119,0.005255,1.21)
    print("  written -> data/judgecal/t3_fit.txt")
