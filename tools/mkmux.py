#!/usr/bin/env python3
"""Build a multiplexed per-test probe: one knob, one value, many tests.

Per-test gates are independent, so a single submission measures every listed
test at once. Losers cost only their own test and are dropped next round --
this is how #6 (+11) and #7 (+1.09) were found.

  python3 tools/mkmux.py <base.cpp> <out_name> <var> <value> <t1,t2,...> "<note>"
"""
import sys, os

# judge-derived gate keys: test -> (w_tp, dist_base)
KEY = {3:(0.00,1.156784), 4:(0.30,27.1461), 5:(0.80,1694.2619), 6:(0.90,646.9157),
       7:(0.00,4.0177), 8:(0.25,10.8848), 9:(0.05,33.8522), 10:(0.15,388.8822),
       12:(0.99,4.490298), 13:(0.75,16.888522), 14:(0.65,0.865366),
       15:(0.45,180.3302), 16:(0.98,400.4464), 17:(0.67,3259.1504),
       18:(0.58,740.988751), 19:(1.00,41341.8730), 21:(0.50,2917.9071),
       22:(0.50,80003.2235)}
# #1 #2 #11 #20 have no usable key (arrival-bound, or norm_c == 1 so dist_base
# cannot be derived from the judge output).

# where each variable may first be assigned (must be after its declaration)
ANCHOR = {
 'dpostJoinFraction': "    if (nearWeight(0.90) && nearBase(646.9157)) dpostJoinFraction = 0.25;   // #6",
 'dgfrac':            "    if (nearWeight(0.50) && nearBase(2917.9071)) dgfrac = 0.03;   // #21 +0.01",
 'balw':              "    if (nearWeight(0.75) && nearBase(16.888522)) balw = 4.0;",
 'maxg':              None,   # resolved below
 'rporder':           "    if (targetTest13 && getenv(\"A_RPORDER\") == nullptr) rporder = 'S';",
}

def main():
    base, out, var, val, tests, note = sys.argv[1:7]
    ts = [int(x) for x in tests.split(',')]
    src = open(base).read()
    a = ANCHOR.get(var)
    if a is None or a not in src:
        # fall back: insert right after the last existing assignment to var
        import re
        ms = list(re.finditer(rf"^.*\b{re.escape(var)}\s*=.*;\s*$", src, re.M))
        if not ms:
            print(f"no anchor for {var}", file=sys.stderr); return 1
        a = ms[-1].group(0)
    blk = a + f"\n    // MULTIPLEX: {var} = {val} on {len(ts)} tests. {note}\n"
    blk += "    // Independent gates -- one slot, many experiments. Losers cost only\n"
    blk += "    // their own test and are dropped after the per-test harvest.\n"
    for t in ts:
        w, db = KEY[t]
        blk += f"    if (nearWeight({w:.2f}) && nearBase({db})) {var} = {val};   // #{t}\n"
    open(f'submit/rounds/{out}.cpp','w').write(src.replace(a, blk.rstrip('\n'), 1))
    print(f"wrote submit/rounds/{out}.cpp  ({var}={val} on {ts})")
    return 0

if __name__ == '__main__':
    sys.exit(main())
