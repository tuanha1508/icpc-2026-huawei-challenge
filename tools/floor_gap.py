#!/usr/bin/env python3
"""Separate reachable waiting headroom from irreducible floor, per test.

Motivation: the judge's norm_c < 1 looks like headroom, but much of it is
physically unreachable. Every request must serially walk

    P PRE (S+pre) -> UP(L_in) -> P PROC (S+proc) -> DOWN(L_in) -> P POST (S+post)

so mean_tdr can never drop below the mean of that chain, no matter how good the
scheduler is. Test #3 is the cautionary case: its floor is exactly 1360.000 and
our solver already achieves exactly 1360.000, while SLO1 = 842.881 sits BELOW the
floor. Its apparent "+499 points" of waiting headroom is unreachable, which is
why all 16 scheduling knobs are exact no-ops there.

This tool reports, per test file:
    floor      mean unloaded tdr (irreducible)
    achieved   mean tdr our solver actually gets
    gap        achieved - floor  = the only part scheduling can ever remove
    pts        points recoverable by closing the whole gap

Usage:
    python3 tools/floor_gap.py --solver Codex/build/v75-fit data/judgecal/*.txt
"""

from __future__ import annotations

import argparse
import bisect
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import interactor  # noqa: E402


def parse(path: str):
    v = open(path).read().split()
    i = 0

    def n():
        nonlocal i
        x = v[i]
        i += 1
        return x

    cfg = dict(K=int(n()), S=float(n()), lat=float(n()), bw=float(n()),
               bpt=int(n()), layers=int(n()))
    sc = dict(SLO1=float(n()), SLO2=float(n()), tp_UB=float(n()),
              tp_base=float(n()), dist_base=float(n()), w_tp=float(n()),
              w_c=float(n()))
    N = int(n())
    rows = [[int(n())] + [float(n()) for _ in range(6)] for _ in range(N)]
    R = int(n())
    reqs = [(float(n()), int(n()), int(n())) for _ in range(R)]
    return cfg, sc, rows, reqs


def curve_at(rows, c, x):
    xs = [r[0] for r in rows if r[1 + c] >= 0]
    ys = [r[1 + c] for r in rows if r[1 + c] >= 0]
    if not xs:
        return 0.0
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    j = bisect.bisect_left(xs, x)
    if xs[j] == x:
        return ys[j]
    return ys[j - 1] + (ys[j] - ys[j - 1]) * (x - xs[j - 1]) / (xs[j] - xs[j - 1])


def tdr_floor(cfg, rows, reqs) -> float:
    """Mean of the irreducible serial prefill chain, one request at a time."""
    S = cfg["S"]

    def tx(ln):
        return cfg["lat"] + 8.0 * (ln * cfg["bpt"]) / (cfg["bw"] * 1e6)

    tot = 0.0
    for _at, lin, _lo in reqs:
        tot += ((S + curve_at(rows, 0, lin)) + tx(lin)
                + (S + curve_at(rows, 1, lin)) + tx(lin)
                + (S + curve_at(rows, 2, lin)))
    return tot / len(reqs)


def score_of(sc, tdr, tpot, comp_tp):
    ex_tdr = max(0.0, (tdr - sc["SLO1"]) / sc["SLO1"])
    ex_tpot = max(0.0, (tpot - sc["SLO2"]) / sc["SLO2"])
    dist = math.sqrt(ex_tdr ** 2 + ex_tpot ** 2)
    if sc["dist_base"] > 0:
        comp_c = max(0.0, 1.0 - dist / sc["dist_base"])
    else:
        comp_c = 1.0 if dist == 0 else 0.0
    return 1000.0 * (sc["w_tp"] * comp_tp + sc["w_c"] * comp_c)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", required=True)
    ap.add_argument("tests", nargs="+")
    args = ap.parse_args()

    print(f"{'test':<18}{'w_tp':>6}{'floor':>12}{'achieved':>12}{'gap':>11}"
          f"{'gap%':>7}{'pts_if_closed':>14}")
    for path in args.tests:
        try:
            cfg, sc, rows, reqs = parse(path)
        except Exception as exc:
            print(f"{os.path.basename(path):<18} parse error: {exc}")
            continue
        floor = tdr_floor(cfg, rows, reqs)
        it = interactor.Interactor(path)
        res = it.run([args.solver])
        if not res.get("ok"):
            print(f"{os.path.basename(path):<18} INVALID")
            continue
        ach, tpot, ctp = res["tdr"], res["tpot"], res["comp_tp"]
        gap = ach - floor
        now = score_of(sc, ach, tpot, ctp)
        best = score_of(sc, max(floor, 0.0), tpot, ctp)
        print(f"{os.path.basename(path)[:17]:<18}{sc['w_tp']:>6.2f}"
              f"{floor:>12.1f}{ach:>12.1f}{gap:>11.1f}"
              f"{100.0 * gap / ach if ach else 0:>6.1f}%{best - now:>14.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
