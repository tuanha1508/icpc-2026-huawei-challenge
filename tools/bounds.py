#!/usr/bin/env python3
"""Resource-utilization lower bounds on makespan for a Problem A test.

Answers the only question that matters when tuning: is the scheduler leaving
score on the table, or is it already near the ceiling this test allows?

Every token crosses UP once and DOWN once, and every request's prefill crosses
both. The local computer E is touched twice per request (P PRE, P POST) and
twice per decode group-iteration (D PRE, D POST). Those are hard work
requirements, independent of any schedule, so dividing them by the number of
each resource gives a makespan lower bound.

Usage: python3 tools/bounds.py data/generated/decode_3.txt [--achieved 0.0161]
"""

from __future__ import annotations

import argparse
import sys
from bisect import bisect_left


class Curve:
    def __init__(self, pts):
        pts = sorted(pts)
        self.xs = [p[0] for p in pts]
        self.ys = [p[1] for p in pts]

    def at(self, x):
        if x <= self.xs[0]:
            return self.ys[0]
        if x >= self.xs[-1]:
            return self.ys[-1]
        i = bisect_left(self.xs, x)
        if self.xs[i] == x:
            return self.ys[i]
        x0, y0, x1, y1 = self.xs[i - 1], self.ys[i - 1], self.xs[i], self.ys[i]
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def load(path):
    v = open(path).read().split()
    i = 0

    def nx():
        nonlocal i
        r = v[i]
        i += 1
        return r

    cfg = {}
    cfg["K"] = int(nx()); cfg["S"] = float(nx()); cfg["lat"] = float(nx())
    cfg["bw"] = float(nx()); cfg["bpt"] = int(nx()); cfg["layers"] = int(nx())
    cfg["SLO1"] = float(nx()); cfg["SLO2"] = float(nx())
    cfg["tp_UB"] = float(nx()); cfg["tp_base"] = float(nx())
    cfg["dist_base"] = float(nx()); cfg["w_tp"] = float(nx()); cfg["w_c"] = float(nx())
    N = int(nx())
    rows = []
    for _ in range(N):
        bs = int(nx())
        rows.append([bs] + [float(nx()) for _ in range(6)])
    cols = [Curve([(int(r[0]), r[1 + c]) for r in rows if r[1 + c] >= 0])
            for c in range(6)]
    R = int(nx())
    reqs = [(float(nx()), int(nx()), int(nx())) for _ in range(R)]
    return cfg, cols, reqs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("test")
    ap.add_argument("--achieved", type=float, default=None,
                    help="tp actually achieved, for a gap report")
    args = ap.parse_args()

    cfg, cols, reqs = load(args.test)
    K, S = cfg["K"], cfg["S"]
    b = 8.0 * cfg["bpt"] / (cfg["bw"] * 1e6)     # ms of link time per token
    lat = cfg["lat"]

    R = len(reqs)
    sum_in = sum(r[1] for r in reqs)
    sum_out = sum(r[2] for r in reqs)
    span = max(r[0] for r in reqs) - min(r[0] for r in reqs)

    # Prefill work is schedule-independent.
    e_pre = sum(2 * S + cols[0].at(r[1]) + cols[2].at(r[1]) for r in reqs)
    rem_pre = sum(S + cols[1].at(r[1]) for r in reqs)
    link_pre = R * lat + sum_in * b               # each direction

    best = None
    for m in range(1, min(2000, max(2, R)) + 1):
        iters = sum_out / m                       # decode group-iterations
        e_dec = iters * (2 * S + cols[3].at(m) + cols[5].at(m))
        e_tot = e_pre + e_dec

        r_eff = min(K, m)
        per = max(1.0, m / r_eff)
        rem_dec = iters * r_eff * (S + cols[4].at(per))
        rem_tot = (rem_pre + rem_dec) / K

        up = link_pre + iters * r_eff * lat + sum_out * b
        down = link_pre + iters * r_eff * lat + sum_out * b

        mk = max(e_tot, rem_tot, up, down, span)
        tp = sum_out / mk
        if best is None or tp > best[0]:
            best = (tp, m, e_tot, rem_tot, up, mk)

    tp_max, m_star, e_tot, rem_tot, up, mk = best

    def clamp(x, base, target):
        if target == base:
            return 1.0 if x == target else 0.0
        return max(0.0, min(1.0, (x - base) / (target - base)))

    print(f"test           {args.test}")
    print(f"K={K} R={R} sum_Lin={sum_in} sum_Lout={sum_out} "
          f"arrival_span={span:.1f}ms")
    print(f"b (ms/token/direction) = {b:.6f}   latency = {lat:.4f}")
    print()
    print(f"best group size m*     = {m_star}")
    print(f"  E work               = {e_tot:12.1f} ms")
    print(f"  remote work / K      = {rem_tot:12.1f} ms")
    print(f"  UP link work         = {up:12.1f} ms   (prefill share "
          f"{100*(R*lat+sum_in*b)/up:.0f}%)")
    print(f"  arrival span         = {span:12.1f} ms")
    print(f"  --> makespan LB      = {mk:12.1f} ms   binding: "
          f"{max([('E',e_tot),('remote',rem_tot),('link',up),('span',span)], key=lambda z: z[1])[0]}")
    print()
    print(f"tp ceiling             = {tp_max:.6f} tokens/ms")
    print(f"tp_base                = {cfg['tp_base']:.6f}")
    print(f"tp_UB                  = {cfg['tp_UB']:.6f}")
    print(f"comp_tp ceiling        = {clamp(tp_max, cfg['tp_base'], cfg['tp_UB']):.3f}"
          f"   (w_tp={cfg['w_tp']}, w_c={cfg['w_c']}, dist_base={cfg['dist_base']:.4f})")
    if args.achieved is not None:
        print(f"achieved tp            = {args.achieved:.6f} "
              f"({100*args.achieved/tp_max:.1f}% of ceiling)")
        print(f"achieved comp_tp       = "
              f"{clamp(args.achieved, cfg['tp_base'], cfg['tp_UB']):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
