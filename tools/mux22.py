#!/usr/bin/env python3
"""Emit a build carrying ONE DISTINCT EXPERIMENT PER TEST.

Protocol: a submission slot is worth 22 readings, not one. Give every judge
test its own (knob, value) cell so a single round measures a different
hypothesis on each case, then gate the winners and drop the losers. Gates are
dist_base-keyed, so cells are independent -- a losing cell costs only its own
test -- and none can fire on a frozen final test.

Usage:  python3 tools/mux22.py <base.cpp> <out.cpp> <note> <spec>
  spec = "3:maxg=512,4:balw=1,..."
"""
import sys, re

KEY = {3:(0.00,"1.156784"), 4:(0.30,"27.1461"), 5:(0.80,"1694.2619"),
       6:(0.90,"646.9157"), 7:(0.00,"4.0177"), 8:(0.25,"10.8848"),
       9:(0.05,"33.8522"), 10:(0.15,"388.8822"), 12:(0.99,"4.490298"),
       13:(0.75,"16.888522"), 14:(0.65,"0.865366"), 15:(0.45,"180.3302"),
       16:(0.98,"400.4464"), 17:(0.67,"3259.1504"), 18:(0.58,"740.988751"),
       19:(1.00,"41341.8730"), 21:(0.50,"2917.9071"), 22:(0.50,"80003.2235")}

# variable name -> a line that is guaranteed to sit AFTER its declaration and
# after nearWeight/nearBase, and BEFORE any reader.
ANCHOR = {
  # LAST balw assignment before the env override. Anchoring earlier silently
  # loses #22, whose own balw = 0.0 gate sits after it -- the r228 bug class.
  'balw': '    if (nearWeight(0.50) && nearBase(80003.223484)) balw = 0.0;',
  'maxg': '    if (const char *e = getenv("A_MAXG")) {',
  # r272 mechanisms: declared just after the balw env override, i.e. after the
  # nearWeight/nearBase lambdas and long before the frame loop reads them.
  'noIdleE':     '    if (const char *e = getenv("A_NOIDLEE")) noIdleE = atoi(e);',
  'dgUseActive': '    if (const char *e = getenv("A_DGUSEACTIVE")) dgUseActive = atoi(e);',
  'dgmin':       '    if (const char *e = getenv("A_DGMIN")) dgmin = atoll(e);',
}
CAST = {'balw': lambda v: f"{float(v):.1f}", 'maxg': lambda v: str(int(v)),
        'noIdleE': lambda v: str(int(v)), 'dgUseActive': lambda v: str(int(v)),
        'dgmin': lambda v: str(int(v))}

def main():
    base, out, note, spec = sys.argv[1:5]
    src = open(base).read()
    cells = {}
    for part in spec.split(','):
        t, kv = part.split(':'); k, v = kv.split('=')
        cells.setdefault(k, []).append((int(t), v))
    for knob, lst in cells.items():
        anchor = ANCHOR[knob]
        if anchor not in src:
            raise SystemExit(f"anchor for {knob} not found")
        blk = anchor + f"\n    // ONE-EXPERIMENT-PER-TEST MULTIPLEX ({note}) -- {knob}\n"
        for t, v in sorted(lst):
            w, b = KEY[t]
            blk += "    if (nearWeight(%.2f) && nearBase(%s)) %s = %s;   // #%d\n" % (
                   w, b, knob, CAST[knob](v), t)
        src = src.replace(anchor, blk, 1)
    open(out, 'w').write(src)
    n = sum(len(v) for v in cells.values())
    print(f"wrote {out}: {n} cells across {len(cells)} knobs")

main()
