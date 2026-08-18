#!/usr/bin/env python3
"""Scrape per-test judge output for a submission, via the signed-in Chrome.

The API exposes only the total score. The submission page carries the full
per-test breakdown (tp / mean_tdr / mean_tpot / dist / norm_tp / norm_c), which
is what attribution actually needs. Reading it costs no submission slot.

  python3 tools/cf_fetch_tests.py 387613068 --out data/judgefeedback/run_r104.txt
"""
import argparse, re, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("submission")
    p.add_argument("--contest", default="2251")
    p.add_argument("--cdp", default="http://localhost:9333")
    p.add_argument("--out")
    a = p.parse_args()

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.connect_over_cdp(a.cdp, timeout=15000)
        ctx = b.contexts[0] if b.contexts else b.new_context()
        page = ctx.pages[0] if ctx.pages else ctx.new_page()   # reuse: no focus steal
        page.goto(f"https://codeforces.com/contest/{a.contest}/submission/{a.submission}",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)
        txt = page.inner_text("body")

    rows = re.findall(r"points\s+([0-9.]+)\s+tp=([0-9.eE+-]+)\s+mean_tdr=([0-9.eE+-]+)"
                      r"\s+mean_tpot=([0-9.eE+-]+)\s+dist=([0-9.eE+-]+)"
                      r"\s+norm_tp=([0-9.eE+-]+)\s+norm_c=([0-9.eE+-]+)", txt)
    if not rows:
        print("no per-test rows found (is the submission page fully rendered?)", file=sys.stderr)
        print(txt[:600], file=sys.stderr)
        return 1
    out = []
    for i, r in enumerate(rows, 1):
        out.append(f"#{i} {r[0]} tp={r[1]} mean_tdr={r[2]} mean_tpot={r[3]} "
                   f"dist={r[4]} norm_tp={r[5]} norm_c={r[6]}")
    total = sum(float(r[0]) for r in rows)
    body = "\n".join(out) + f"\n# total {total:.3f} over {len(rows)} tests\n"
    if a.out:
        open(a.out, "w").write(body); print(f"wrote {a.out}")
    print(f"{len(rows)} tests, total {total:.3f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
