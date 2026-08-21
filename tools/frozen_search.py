#!/usr/bin/env python3
"""Coordinate descent over the GLOBAL defaults -- the ungated path the 20
frozen final tests take, which is what the ranking is actually computed from
(PROBLEM.md:608). Costs no submission slots: the corpus exercises this path
directly because no dist_base-keyed gate can fire on it.

Starts from r264 (global nfactor 0 + dgfrac 0.18).
"""
import os, subprocess, sys, json, glob

SOLVER = '/Users/tuna/.claude/jobs/24f36c4f/tmp/chk_r264'
TESTS  = sorted(glob.glob('/Users/tuna/.claude/jobs/24f36c4f/tmp/g3c/*.txt'))

GRID = {
    'A_DGFRAC':   ['0.16','0.18','0.20','0.22'],
    'A_DPOSTFRAC':['0.05','0.10','0.15','0.20','0.30'],
    'A_BALW':     ['-1','0','1','2','4','8'],
    'A_MARGINAL': ['0','1'],
    'A_PFVAL':    ['14','30','50','70'],
    'A_RPRIO':    ['P','D'],
    'A_ORDER':    ['S','F','L'],
    'A_PFAIR':    ['0','2','4'],
    'A_MAXG':     ['0','64','512'],
    'A_RUSE':     ['0','4','8'],
}
BASE = {'A_DGFRAC':'0.18','A_DPOSTFRAC':'0.15','A_BALW':'-1','A_MARGINAL':'1',
        'A_PFVAL':'30','A_RPRIO':'P','A_ORDER':'S','A_PFAIR':'2',
        'A_MAXG':'0','A_RUSE':'0'}

def score(cfg):
    env = dict(os.environ)
    for k, v in cfg.items():
        if v in ('0',) and k in ('A_MAXG','A_RUSE','A_PFAIR'):
            env.pop(k, None)          # 0 means "leave the compiled default"
        else:
            env[k] = v
    tot = 0.0
    for t in TESTS:
        try:
            r = subprocess.run(['./sim/fast_interactor', t, SOLVER],
                               capture_output=True, text=True, timeout=30, env=env)
        except subprocess.TimeoutExpired:
            return None
        o = r.stdout.strip().split('\n')[0] if r.stdout else ''
        if not o.startswith('score='): return None
        tot += float(o.split()[0].split('=')[1])
    return tot

cur = dict(BASE)
best = score(cur)
n = len(TESTS)
print(f"start: sum {best:.1f}  mean {best/n:.3f}  over {n} ungated tests", flush=True)
improved = True
rounds = 0
while improved and rounds < 4:
    improved = False; rounds += 1
    for k, vals in GRID.items():
        for v in vals:
            if v == cur[k]: continue
            trial = dict(cur); trial[k] = v
            s = score(trial)
            if s and s > best + 1e-6:
                print(f"  round {rounds}: {k} {cur[k]} -> {v}   mean {best/n:.3f} -> {s/n:.3f}", flush=True)
                cur, best, improved = trial, s, True
    print(f"round {rounds} done: mean {best/n:.3f}", flush=True)
print("\nBEST GLOBAL CONFIG (frozen path):")
for k in sorted(cur):
    mark = "  <-- changed" if cur[k] != BASE[k] else ""
    print(f"  {k:<14} {cur[k]}{mark}")
print(f"mean {best/n:.3f}   (r264 start was {score(BASE)/n:.3f})")
json.dump(cur, open('/Users/tuna/.claude/jobs/24f36c4f/tmp/frozen_best.json','w'), indent=1)
