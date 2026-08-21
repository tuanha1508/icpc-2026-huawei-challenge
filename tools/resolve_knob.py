#!/usr/bin/env python3
"""Resolve the EFFECTIVE compiled value of a per-test knob for each judge test,
by replaying the gate assignments in source order (last write wins).

Motivated by r228: its 'dpost 0.60 on 15 tests' multiplex was silently reset to
0.25 for 9 of them by a later block, so the round's per-test readings on those
tests were artifacts, not measurements.
"""
import re, sys, glob, os

# dist_base key -> judge test number
KEY = {"1.156784":3,"27.1461":4,"1694.2619":5,"646.9157":6,"4.0177":7,"4.017728":7,
       "10.8848":8,"33.8522":9,"388.8822":10,"388.8819":10,"4.490298":12,
       "16.888522":13,"0.865366":14,"180.3302":15,"400.4464":16,"400.4455":16,
       "400.4447":16,"3259.1504":17,"740.988751":18,"41341.873":19,
       "2917.9071":21,"80003.2235":22,"80003.2264":22}

def resolve(path, knob):
    final = {}
    pat = re.compile(r'nearBase\(([\d.]+)\)[^;]*?\b%s = ([\d.eE+-]+)\s*;' % knob)
    for raw in open(path, errors='ignore'):
        line = raw.strip()
        if line.startswith('//') or knob not in line: continue
        if 'getenv' in line and '=' not in line.split('getenv')[0]: pass
        for m in pat.finditer(line):
            k = m.group(1)
            # match numerically, not as a string: the same dist_base is
            # written 41341.873 in one build and 41341.8730 in another, and a
            # string lookup silently DROPS that cell from the audit.
            t = KEY.get(k)
            if t is None:
                try:
                    kv = float(k)
                    for kk, tt in KEY.items():
                        if abs(float(kk) / kv - 1.0) < 1e-6: t = tt; break
                except ValueError: pass
            if t is not None:
                try: final[t] = float(m.group(2))
                except ValueError: pass
    return final

if __name__ == '__main__':
    knob = sys.argv[1] if len(sys.argv) > 1 else 'dpostJoinFraction'
    for f in sorted(sys.argv[2:]):
        r = resolve(f, knob)
        print(os.path.basename(f), '|', ' '.join(f"#{t}={r[t]:g}" for t in sorted(r)))
