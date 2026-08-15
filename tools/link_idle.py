#!/usr/bin/env python3
"""Attribute every idle interval on a link to the event that should have filled it.

Test 12's makespan is set by the serial UP link, which runs at 90.7% on the
faithful reproduction. The missing 9.3% is worth about 110 points, and it is not
admission, capping, or E ordering -- all three are excluded by measurement. So
read the answer out of the transcript instead of guessing again.

A transfer's duration is latency + size*8/(bw*1e6) ms, and the stream reports
its COMPLETION time, so each transfer's occupancy is [done - dur, done]. Sorting
those gives the busy intervals; the gaps between them are the idle ones. For
each gap we report what completed at its start and what started it -- i.e. what
the link was waiting on.

Usage: python3 tools/link_idle.py <test> <solver> [UP|DOWN]
"""
from __future__ import annotations
import subprocess, sys, os

def main() -> int:
    test, solver = sys.argv[1], sys.argv[2]
    which = sys.argv[3] if len(sys.argv) > 3 else "UP"
    dump = "/tmp/_linkidle.stream"
    subprocess.run([sys.executable, "tools/interactor.py", "--test", test,
                    "--solver", solver, "--dump-stream", dump],
                   capture_output=True, text=True)
    head = open(test).read().split("\n")
    K, S, lat, bw, bpt, layers = head[0].split()
    lat, bw = float(lat), float(bw)

    lines = open(dump).read().split("\n")
    # skip the echoed header: config, scoring, n, then n task-table rows.
    # Without this the table's leading integers parse as timestamps.
    nrows = int(lines[2].strip())
    lines = lines[3 + nrows:]
    # Frame structure: <timestamp> <count> then exactly <count> event lines.
    # Parsing "any bare number is a timestamp" fails because the COUNT is also a
    # bare number and overwrites it.
    xfers = []          # (start, done, kind, rid)
    tasks = []          # (done, text)
    i = 0
    while i < len(lines):
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i + 1 >= len(lines):
            break
        try:
            t = float(lines[i].strip()); n = int(lines[i + 1].strip())
        except ValueError:
            i += 1
            continue
        i += 2
        for _ in range(n):
            if i >= len(lines):
                break
            ln = lines[i].strip(); i += 1
            if ln.startswith("XDN"):
                p2 = ln.split()
                d, size = p2[1], float(p2[3])
                dur = lat + size * 8.0 / (bw * 1e6)
                if d == which:
                    xfers.append((t - dur, t, p2[4], p2[6] if len(p2) > 6 else "?"))
            elif ln.startswith("TDN"):
                tasks.append((t, ln))

    xfers.sort()
    span = max(x[1] for x in xfers) if xfers else 0.0
    busy = sum(b - a for a, b, _, _ in xfers)
    print(f"{which}: {len(xfers)} transfers, busy {busy:,.0f} ms over a "
          f"{span:,.0f} ms span -> util {busy/span:.3f}")

    # merge overlapping (a serial link should not overlap, but be safe)
    merged = []
    for a, b, k, r in xfers:
        if merged and a <= merged[-1][1] + 1e-9:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    gaps = []
    prev = 0.0
    for a, b in merged:
        if a - prev > 1e-6:
            gaps.append((prev, a, a - prev))
        prev = max(prev, b)
    gaps.sort(key=lambda g: -g[2])
    tot = sum(g[2] for g in gaps)
    print(f"idle: {len(gaps)} intervals totalling {tot:,.0f} ms "
          f"({100*tot/span:.1f}% of the span)\n")
    print(f"{'start':>14} {'end':>14} {'length':>12}   what the link was waiting on")
    for a, b, L in gaps[:12]:
        before = [x for x in tasks if abs(x[0] - a) < 1e-6]
        after = [x for x in tasks if a < x[0] <= b + 1e-6]
        note = ""
        if after:
            note = "next task done in gap: " + after[0][1][:52]
        elif before:
            note = "gap opens as: " + before[0][1][:52]
        print(f"{a:14,.1f} {b:14,.1f} {L:12,.1f}   {note}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
