#!/usr/bin/env python3
"""Sweep solver policy knobs over a corpus and rank by mean score.

The solver reads its knobs from the environment (A_NFACTOR, A_EPRIO, A_PIECES,
A_RPRIO), which are unset on the judge, so sweeping here does not change the
submitted behaviour -- it only tells us what the compiled-in defaults should be.

Usage:
    python3 tools/sweep_policy.py --tests data/generated --solver ./build/local/solver
"""

from __future__ import annotations

import argparse
import itertools
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run_one(args) -> tuple[str, str, float, bool]:
    test, solver, env_over, itpath = args
    env = dict(os.environ)
    env.update(env_over)
    try:
        out = subprocess.run(
            [sys.executable, itpath, "--test", test, "--solver", solver, "--quiet"],
            capture_output=True, text=True, env=env, timeout=900,
        )
        line = out.stdout.strip().splitlines()
        if out.returncode != 0 or not line:
            return (test, str(env_over), 0.0, False)
        return (test, str(env_over), float(line[-1]), True)
    except Exception:
        return (test, str(env_over), 0.0, False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", default="data/generated")
    ap.add_argument("--solver", default="./build/local/solver")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--nfactor", default="0.5,1,2,4,1e18")
    ap.add_argument("--eprio", default="ACDB,ABCD,CDAB,ACBD")
    ap.add_argument("--pieces", default="1,4")
    args = ap.parse_args()

    tests = sorted(str(p) for p in Path(args.tests).glob("*.txt"))
    if not tests:
        print("no tests found", file=sys.stderr)
        return 1
    itpath = str(Path(__file__).with_name("interactor.py"))

    combos = []
    for nf, ep, pc in itertools.product(
        args.nfactor.split(","), args.eprio.split(","), args.pieces.split(",")
    ):
        combos.append({"A_NFACTOR": nf, "A_EPRIO": ep, "A_PIECES": pc})

    jobs = [(t, args.solver, c, itpath) for c in combos for t in tests]
    print(f"{len(combos)} combos x {len(tests)} tests = {len(jobs)} runs",
          file=sys.stderr)

    results: dict[str, dict[str, float]] = {}
    invalid: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for test, key, score, ok in ex.map(run_one, jobs):
            results.setdefault(key, {})[test] = score
            if not ok:
                invalid.setdefault(key, []).append(Path(test).name)

    rows = []
    for key, per in results.items():
        mean = sum(per.values()) / len(per)
        rows.append((mean, key, per))
    rows.sort(reverse=True)

    print(f"\n{'mean':>9}  {'zeros':>5}  config")
    for mean, key, per in rows:
        zeros = sum(1 for v in per.values() if v == 0.0)
        flag = "  INVALID:" + ",".join(invalid[key][:3]) if key in invalid else ""
        print(f"{mean:9.2f}  {zeros:5d}  {key}{flag}")

    best = rows[0]
    print(f"\nbest: {best[1]}  mean={best[0]:.2f}")
    print(f"\n{'test':<24} {'best':>9}")
    for t in tests:
        print(f"{Path(t).name:<24} {best[2][t]:9.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
