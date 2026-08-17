#!/usr/bin/env python3
"""When can I submit again?

Codeforces exposes submission times without authentication:
    https://codeforces.com/api/user.status?handle=<HANDLE>&from=1&count=<N>
Each submission carries `creationTimeSeconds` (Unix epoch, UTC), which is the
exact accepted-at time the web UI does not show you.

Usage:
    python3 tools/cooldown.py <handle> [--cooldown 900] [--contest 2251] [--watch]
"""
import argparse, hashlib, json, os, random, string, sys, time, urllib.parse, urllib.request

BASE = "https://codeforces.com/api/"

def call(method, **params):
    """Codeforces API call. Signs the request when CF_KEY/CF_SECRET are set,
    which is required for gym contests and contest.status."""
    key, sec = os.environ.get("CF_KEY"), os.environ.get("CF_SECRET")
    params = {k: v for k, v in params.items() if v is not None}
    if key and sec:
        params["apiKey"] = key
        params["time"] = str(int(time.time()))
        rand = "".join(random.choice(string.digits) for _ in range(6))
        # apiSig = rand + sha512( rand/method?<params sorted by (key,value)>#secret )
        qs = "&".join(f"{k}={params[k]}" for k in sorted(params, key=lambda k: (k, params[k])))
        sig = hashlib.sha512(f"{rand}/{method}?{qs}#{sec}".encode()).hexdigest()
        params["apiSig"] = rand + sig
    url = BASE + method + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "cooldown-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        d = json.load(e)
    if d.get("status") != "OK":
        raise SystemExit(f"API error on {method}: {d.get('comment')}")
    return d["result"]

def fetch(handle, n=20, contest=None):
    if contest:
        return call("contest.status", contestId=contest, handle=handle, **{"from": 1, "count": n})
    return call("user.status", handle=handle, **{"from": 1, "count": n})

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
            left = report(a.handle, a.cooldown, a.contest, fetch(a.handle, 40, a.contest))
        except Exception as e:
            print(f"  fetch failed: {e}")
            left = 60
        if not a.watch or left is None or left <= 0:
            break
        time.sleep(min(30, max(5, left / 4)))
        print("  ---")
if __name__ == "__main__":
    main()
