#!/usr/bin/env python3
"""Champion-style per-fingerprint knob sweep.

For a given proxy + solver, sweep each A_* knob across candidate values,
run the interactor, and report physical metric deltas (tp/tdr/tpot/dist)
plus local score. Physical deltas are the trustworthy signal when a proxy's
score window differs from the judge (see OPEN_TESTS.md trust rules).

Usage:
  python3 tools/knob_sweep.py --test data/judgecal/cal_t14_u.txt \
      --solver reference/build/v74 [--objective tp|tpot|tdr|score] [--only A_DGFRAC,A_PFVAL]
"""
import argparse, os, re, subprocess, sys

METRIC_RE = re.compile(
    r"score=([0-9.eE+-]+).*?\btp=([0-9.eE+-]+).*?\btdr=([0-9.eE+-]+)"
    r".*?\btpot=([0-9.eE+-]+).*?\bdist=([0-9.eE+-]+)", re.S)

# knob -> candidate values (strings passed via env)
KNOBS = {
    "A_DGFRAC":   ["0.0", "0.05", "0.10", "0.25", "0.35", "0.50", "0.75", "0.95"],
    "A_DPOSTFRAC":["0.0", "0.10", "0.25", "0.50", "0.75", "1.0"],
    "A_DPROCFRAC":["0.0", "0.25", "0.50", "0.75"],
    "A_BALW":     ["-1", "0", "1", "2", "4", "8"],
    "A_PFAIR":    ["0", "1", "2", "4", "8"],
    "A_PFVAL":    ["4", "8", "12", "14", "20"],
    "A_MAXG":     ["1", "2", "4", "8", "16", "32", "64"],
    "A_PIECES":   ["0", "1", "2", "3", "4"],
    "A_ORDER":    ["F", "S", "H"],
    "A_EPRIO":    ["CDBA", "DCBA", "CDAB", "ACDB", "DCAB"],
    "A_RPRIO":    ["D", "P"],
    "A_RPORDER":  ["F", "S", "C", "N", "I", "L"],
    "A_RUSE":     ["1", "2", "3", "4"],
    "A_RADAPT":   ["0", "1"],
    "A_MARGINAL": ["0", "1"],
    "A_WAVEREMOTES":["1", "2", "4"],
    "A_STRICTPREFILL":["0", "1"],
    "A_PFBARRIER":["0.0", "0.5", "1.0"],
    "A_NFACTOR":  ["0.5", "1.0", "2.0"],
    "A_CHUNK":    ["0.25", "0.5", "1.0", "2.0"],
    "A_BALCURVE": ["0", "1"],
    "A_FUTUREBALW":["0", "1"],
}


def run(test, solver, env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    out = subprocess.run(
        [sys.executable, "tools/interactor.py", "--test", test, "--solver", solver],
        capture_output=True, text=True, env=env, timeout=120).stdout
    m = METRIC_RE.search(out)
    if not m:
        return None
    return dict(zip(("score", "tp", "tdr", "tpot", "dist"),
                    (float(x) for x in m.groups())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--objective", default="tp",
                    choices=["tp", "tpot", "tdr", "score"])
    ap.add_argument("--only", default="", help="comma list of knobs to sweep")
    ap.add_argument("--min-rel", type=float, default=0.5,
                    help="min %% change in objective to report")
    args = ap.parse_args()

    base = run(args.test, args.solver, {})
    if base is None:
        print("FAILED to get baseline", file=sys.stderr); sys.exit(1)
    print(f"baseline: score={base['score']:.3f} tp={base['tp']:.6f} "
          f"tdr={base['tdr']:.3f} tpot={base['tpot']:.3f} dist={base['dist']:.4f}")
    # objective direction: tp higher is better; tpot/tdr/dist lower better; score higher
    better_up = args.objective in ("tp", "score")

    only = set(x for x in args.only.split(",") if x)
    hits = []
    for knob, vals in KNOBS.items():
        if only and knob not in only:
            continue
        for v in vals:
            r = run(args.test, args.solver, {knob: v})
            if r is None:
                continue
            o0, o1 = base[args.objective], r[args.objective]
            if abs(o0) < 1e-12:
                continue
            rel = (o1 - o0) / abs(o0) * 100.0
            improved = rel > 0 if better_up else rel < 0
            tag = ""
            if abs(rel) >= args.min_rel:
                tag = "  <== IMPROVE" if improved else "  (worse)"
            if abs(rel) >= args.min_rel:
                print(f"{knob}={v:<6} {args.objective} {o1:.6f} "
                      f"({rel:+.2f}%)  tp={r['tp']:.6f} tdr={r['tdr']:.1f} "
                      f"tpot={r['tpot']:.3f} dist={r['dist']:.4f} score={r['score']:.3f}{tag}")
            if tag.strip().startswith("<") :
                hits.append((rel if better_up else -rel, knob, v, r))
    print("\n=== top improvements ===")
    for rel, knob, v, r in sorted(hits, reverse=True)[:12]:
        print(f"  {knob}={v}  {args.objective}{'+' if better_up else '-'}{abs(rel):.2f}%  "
              f"tp={r['tp']:.6f} tdr={r['tdr']:.1f} tpot={r['tpot']:.3f} dist={r['dist']:.4f}")


if __name__ == "__main__":
    main()
