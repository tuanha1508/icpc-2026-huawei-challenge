#!/usr/bin/env python3
"""When can I submit again?

Codeforces exposes submission times without authentication:
    https://codeforces.com/api/user.status?handle=<HANDLE>&from=1&count=<N>
Each submission carries `creationTimeSeconds` (Unix epoch, UTC), which is the
exact accepted-at time the web UI does not show you.

Usage:
    python3 tools/cooldown.py <handle> [--cooldown 900] [--contest 2251] [--watch]
"""
import argparse, json, sys, time, urllib.request

API = "https://codeforces.com/api/user.status?handle={h}&from=1&count={n}"

def fetch(handle, n=20):
    req = urllib.request.Request(API.format(h=handle, n=n),
                                 headers={"User-Agent": "cooldown-check/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.load(r)
    if d.get("status") != "OK":
        raise SystemExit(f"API error: {d.get('comment')}")
    return d["result"]

def fmt(sec):
    sec = int(sec)
    sign = "-" if sec < 0 else ""
    sec = abs(sec)
    return f"{sign}{sec//60}m{sec%60:02d}s"

def report(handle, cooldown, contest, subs):
    if contest:
        subs = [s for s in subs if s.get("contestId") == contest]
    if not subs:
        print(f"no submissions found for {handle}" + (f" in contest {contest}" if contest else ""))
        return None
    now = time.time()
    last = max(subs, key=lambda s: s["creationTimeSeconds"])
    age = now - last["creationTimeSeconds"]
    left = cooldown - age
    when = time.strftime("%H:%M:%S", time.localtime(last["creationTimeSeconds"]))
    prob = last.get("problem", {}).get("index", "?")
    print(f"  last submission : {when} local  (problem {prob}, {last.get('verdict')})")
    print(f"  age             : {fmt(age)}")
    if left > 0:
        ready = time.strftime("%H:%M:%S", time.localtime(last["creationTimeSeconds"] + cooldown))
        print(f"  COOLDOWN        : {fmt(left)} remaining -> ready at {ready} local")
    else:
        print(f"  READY NOW       : cooldown cleared {fmt(-left)} ago")
    # recent cadence, so you can see the real interval the judge enforced
    ts = sorted(s["creationTimeSeconds"] for s in subs)[-6:]
    if len(ts) > 1:
        gaps = [fmt(b - a) for a, b in zip(ts, ts[1:])]
        print(f"  recent gaps     : {' | '.join(gaps)}")
    return left

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handle")
    ap.add_argument("--cooldown", type=int, default=900, help="seconds (default 900)")
    ap.add_argument("--contest", type=int, default=None, help="filter to one contestId")
    ap.add_argument("--watch", action="store_true", help="poll until ready")
    a = ap.parse_args()
    while True:
        try:
            left = report(a.handle, a.cooldown, a.contest, fetch(a.handle))
        except Exception as e:
            print(f"  fetch failed: {e}")
            left = 60
        if not a.watch or left is None or left <= 0:
            break
        time.sleep(min(30, max(5, left / 4)))
        print("  ---")
if __name__ == "__main__":
    main()
