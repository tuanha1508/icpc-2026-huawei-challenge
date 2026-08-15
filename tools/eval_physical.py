#!/usr/bin/env python3
"""Compare policy variants on calibration-independent quantities.

The local generator invents SLO1/SLO2/tp_UB, so local *scores* cannot predict
the judge. But throughput (tp) and mean TDR are physical outcomes of the
schedule and do not depend on that calibration at all -- and norm_tp is
monotone in tp while the TDR half of dist is monotone in tdr. So variants are
ranked here on tp (higher better) and tdr (lower better).

Usage:
  python3 tools/eval_physical.py --tests data/generated --solver ./build/local/solver \
      --vary A_PFAIR --values 1000000000,8,4,2,1,0
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PAT = re.compile(r"tp=([0-9.eE+-]+).*?tdr=([0-9.eE+-]+).*?tpot=([0-9.eE+-]+)")


def run(job):
    test, solver, env_over, itpath = job
    env = dict(os.environ)
    env.update(env_over)
    try:
        out = subprocess.run(
            [sys.executable, itpath, "--test", test, "--solver", solver],
            capture_output=True, text=True, env=env, timeout=1800,
        )
        line = out.stdout.strip()
        if line.startswith("INVALID"):
            return (test, env_over.get("__k", ""), None, None, None, False)
        m = PAT.search(line)
        if not m:
            return (test, env_over.get("__k", ""), None, None, None, False)
        return (test, env_over.get("__k", ""), float(m.group(1)),
                float(m.group(2)), float(m.group(3)), True)
    except Exception:
        return (test, env_over.get("__k", ""), None, None, None, False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", default="data/generated")
    ap.add_argument("--solver", default="./build/local/solver")
    ap.add_argument("--vary", required=True)
    ap.add_argument("--values", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()

    tests = sorted(str(p) for p in Path(args.tests).glob("*.txt"))
    itpath = str(Path(__file__).with_name("interactor.py"))
    vals = args.values.split(",")

    jobs = []
    for v in vals:
        for t in tests:
            jobs.append((t, args.solver, {args.vary: v, "__k": v}, itpath))

    res: dict[str, dict[str, tuple]] = {v: {} for v in vals}
    bad = []
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for test, key, tp, tdr, tpot, ok in ex.map(run, jobs):
            if not ok:
                bad.append((key, Path(test).name))
            res[key][test] = (tp, tdr, tpot)

    base = vals[0]
    print(f"\nbaseline {args.vary}={base}\n")
    print(f"{'value':>12} {'tp ratio':>10} {'tdr ratio':>10} {'tp wins':>8} "
          f"{'tdr wins':>9} {'invalid':>8}")
    for v in vals:
        rt, rd, wtp, wtd = [], [], 0, 0
        for t in tests:
            a, b = res[base].get(t), res[v].get(t)
            if not a or not b or a[0] is None or b[0] is None:
                continue
            if a[0] > 0:
                rt.append(b[0] / a[0])
                if b[0] > a[0] * 1.001:
                    wtp += 1
            if a[1] > 0:
                rd.append(b[1] / a[1])
                if b[1] < a[1] * 0.999:
                    wtd += 1
        inv = sum(1 for k, _ in bad if k == v)
        gt = sum(rt) / len(rt) if rt else 0
        gd = sum(rd) / len(rd) if rd else 0
        print(f"{v:>12} {gt:10.4f} {gd:10.4f} {wtp:8d} {wtd:9d} {inv:8d}")
    if bad:
        print("\nINVALID runs:", bad[:10])
    print("\ntp ratio > 1 is better; tdr ratio < 1 is better")
    return 0


if __name__ == "__main__":
    sys.exit(main())
