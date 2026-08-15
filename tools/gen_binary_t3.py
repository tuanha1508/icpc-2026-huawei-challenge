#!/usr/bin/env python3
"""Generate #3-shaped tests where dist_base = 0 is DERIVED, not assumed.

PROBLEM.md:581 confirms dist_base is the reference scheduler's own dist, so
dist_base = 0 exactly when the one-request-at-a-time reference meets BOTH SLOs.
Then the waiting component is binary: 1 if we also meet both, 0 otherwise.

That is the hypothesis for judge test 3 -- the setter would not pick
SLO2 = 63.058 if the minimum single-request round trip were 132.8, so our TPOT
is contention-inflated and the reference (which has the machine to itself)
meets its targets. Every local t3 file has dist_base hardcoded to 1.21, so none
of them can test this.

Keeps only tests that are genuinely #3-shaped:
  reference meets both SLOs  (dist_base = 0)  AND  our solver misses them.
"""
from __future__ import annotations
import sys, os, math, subprocess
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'tools')
from fit_t3c import mk, ex, SLO1, SLO2, TP_UB

f = lambda x: f"{x:.9f}"
SOLVER = './build/local/solver'


def emit(path, K, S, lat, bw, bpt, layers, LIN, LOUT, R, gapf, dp, ppc):
    cols, rows, reqs, cfg, tpr, tdrr, tpotr = mk(K, S, lat, bw, bpt, layers,
                                                 LIN, LOUT, R, gapf, dp, ppc)
    a, c = ex(tdrr, tpotr)
    db = math.sqrt(a * a + c * c)
    o = [f"{K} {f(S)} {f(lat)} {f(bw)} {bpt} {layers}",
         f"{f(SLO1)} {f(SLO2)} {f(TP_UB)} {f(tpr)} {f(db)} {f(0.0)} {f(1.0)}",
         str(len(rows))]
    for r in rows:
        o.append(str(int(r[0])) + " " + " ".join(f(v) for v in r[1:]))
    o.append(str(len(reqs)))
    for arr, li, lo in reqs:
        o.append(f"{f(arr)} {li} {lo}")
    open(path, 'w').write("\n".join(o) + "\n")
    return db, tpr, tdrr, tpotr


def run(p, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    try:
        r = subprocess.run([sys.executable, 'tools/interactor.py', '--test', p,
                            '--solver', SOLVER], capture_output=True, text=True,
                           timeout=600, env=e)
        line = next(l for l in r.stdout.splitlines() if l.startswith('score='))
        g = lambda k: float(line.split(k + '=')[1].split()[0].rstrip(')'))
        return g('score'), g('tp'), g('tdr'), g('tpot'), g('dist')
    except Exception:
        return None


def trial(item):
    i, p = item
    (K, LOUT, LIN, dp, ppc, lat, bw, bpt, gapf, R) = p
    path = f"/tmp/bt3_{i}.txt"
    try:
        db, tpr, tdrr, tpotr = emit(path, K, 10.0, lat, bw, bpt, 8, LIN, LOUT,
                                    R, gapf, dp, ppc)
    except Exception:
        return None
    if db != 0.0:                       # reference must meet BOTH SLOs
        os.unlink(path)
        return None
    got = run(path)
    if not got:
        os.unlink(path)
        return None
    sc, tp, tdr, tpot, dist = got
    if dist <= 0.0:                     # we already meet them -> not #3-shaped
        os.unlink(path)
        return None
    return (dist, p, sc, tp, tdr, tpot, tdrr, tpotr, path)


GRID = [(K, LOUT, LIN, dp, ppc, lat, bw, bpt, gapf, R)
        for K in (2, 4)
        for LOUT in (4, 8, 16)
        for LIN in (512, 2048)
        for dp in (3.0, 8.0, 20.0)
        for ppc in (60.0, 200.0, 500.0)
        for lat in (0.5, 5.0)
        for bw in (1.0, 5.0)
        for bpt in (5000, 50000)
        for gapf in (0.05, 0.15, 0.35)
        for R in (30,)]

if __name__ == '__main__':
    print(f"searching {len(GRID)} candidates for dist_base == 0 AND we miss ...")
    res = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 8) as exx:
        for r in exx.map(trial, enumerate(GRID)):
            if r:
                res.append(r)
    res.sort(key=lambda x: -x[0])
    print(f"found {len(res)} #3-shaped tests (reference meets both, we do not)\n")
    print(f"{'dist':>7} {'K':>2} {'Lout':>4} {'Lin':>5} {'gap':>5} {'tdr':>9} "
          f"{'tpot':>7} | {'ref tdr':>9} {'ref tpot':>8}  (SLO 913.2 / 63.06)")
    keep = []
    for r in res[:8]:
        (dist, p, sc, tp, tdr, tpot, tdrr, tpotr, path) = r
        print(f"{dist:7.3f} {p[0]:2d} {p[1]:4d} {p[2]:5d} {p[8]:5.2f} {tdr:9.1f} "
              f"{tpot:7.2f} | {tdrr:9.1f} {tpotr:8.2f}")
        keep.append(r)
    for n, r in enumerate(keep[:4]):
        dst = f"data/judgecal/bt3_{n+1}.txt"
        os.replace(r[8], dst)
        print(f"  wrote {dst}")
    for r in res:
        if os.path.exists(r[8]):
            os.unlink(r[8])
