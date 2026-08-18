#!/usr/bin/env python3
"""Submit a source file to Codeforces by driving an already-signed-in Chrome.

Connects to a running Chrome over the DevTools protocol, so it reuses the
session the user signed in with. No credentials are ever read, typed or stored
by this script.

  Start Chrome once (quit it first if it is already running):
    /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
        --remote-debugging-port=9333

  Dry run (fills the form, never sends):
    python3 tools/cf_submit.py --file submit/r119_strip.cpp --no-submit

  Real submission, waiting for the rate-limit window to open first:
    python3 tools/cf_submit.py --file submit/r119_strip.cpp --wait
"""
import argparse, os, sys, time, hashlib, random, string, json, urllib.request

API = "https://codeforces.com/api/"


def api(method, **params):
    """Signed read-only Codeforces API call (used only to read submission times)."""
    key, sec = os.environ.get("CF_KEY"), os.environ.get("CF_SECRET")
    if not (key and sec):
        return None
    params.update(apiKey=key, time=str(int(time.time())))
    rand = "".join(random.choice(string.digits) for _ in range(6))
    qs = "&".join(f"{k}={params[k]}" for k in sorted(params, key=lambda k: (k, params[k])))
    sig = hashlib.sha512(f"{rand}/{method}?{qs}#{sec}".encode()).hexdigest()
    url = API + method + "?" + qs + "&apiSig=" + rand + sig
    try:
        return json.load(urllib.request.urlopen(url, timeout=30))
    except Exception as e:
        print(f"  [api] {e}", file=sys.stderr)
        return None


def slot_free(handle, contest, quota=2, window=900):
    """Return (free, seconds_until_free). Mirrors tools/cooldown.py."""
    d = api("user.status", handle=handle, count="20", **{"from": "1"})
    if not d or d.get("status") != "OK":
        return True, 0.0                      # cannot tell -> do not block
    now = time.time()
    recent = sorted(
        s["creationTimeSeconds"] for s in d["result"]
        if s.get("contestId") == int(contest) and now - s["creationTimeSeconds"] < window
    )
    if len(recent) < quota:
        return True, 0.0
    return False, (recent[-quota] + window) - now


def submit(page, contest, problem, path, lang_match, do_submit):
    code = open(path, encoding="utf-8").read()
    print(f"  source : {path}  ({len(code)} bytes)")
    page.goto(f"https://codeforces.com/contest/{contest}/submit",
              wait_until="domcontentloaded", timeout=60000)

    if page.locator("input[name='handleOrEmail']").count():
        print("  ERROR: not signed in to Codeforces in this Chrome profile.", file=sys.stderr)
        return 2

    page.select_option("select[name='submittedProblemIndex']", problem)

    langs = page.locator("select[name='programTypeId'] option").all()
    chosen = None
    for o in langs:
        if lang_match.lower() in (o.text_content() or "").lower():
            chosen = (o.get_attribute("value"), o.text_content().strip())
            break
    if not chosen:
        print(f"  ERROR: no language matching {lang_match!r}. Available:", file=sys.stderr)
        for o in langs[:40]:
            print("    -", (o.text_content() or "").strip(), file=sys.stderr)
        return 3
    page.select_option("select[name='programTypeId'], select#programTypeId", chosen[0])
    print(f"  language: {chosen[1]}")

    # Codeforces renders a plain textarea; the ACE editor mirrors into it.
    page.evaluate(
        """([code]) => {
            const ta = document.querySelector('#sourceCodeTextarea')
                    || document.querySelector("textarea[name='source']");
            if (!ta) throw new Error('source textarea not found');
            ta.value = code;
            ta.dispatchEvent(new Event('input',  {bubbles: true}));
            ta.dispatchEvent(new Event('change', {bubbles: true}));
        }""", [code])
    got = page.evaluate(
        "() => (document.querySelector('#sourceCodeTextarea')"
        " || document.querySelector(\"textarea[name='source']\")).value.length")
    print(f"  form loaded with {got} bytes")
    if got != len(code):
        print(f"  ERROR: form holds {got} bytes, file has {len(code)}", file=sys.stderr)
        return 4

    if not do_submit:
        print("  DRY RUN -- form is filled, nothing sent.")
        return 0

    page.click("input.submit, input[value='Submit'], div.submit input[type='submit']")
    page.wait_for_load_state("domcontentloaded", timeout=60000)

    err = page.locator("span.error").first
    if err.count() and (err.text_content() or "").strip():
        print(f"  REJECTED: {err.text_content().strip()}", file=sys.stderr)
        return 5
    print(f"  SUBMITTED -> {page.url}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--contest", default="2251")
    p.add_argument("--problem", default="A")
    p.add_argument("--handle", default="tuanha")
    p.add_argument("--lang", default="G++23", help="substring match on the language name")
    p.add_argument("--cdp", default="http://localhost:9333")
    p.add_argument("--no-submit", action="store_true", help="fill the form but do not send")
    p.add_argument("--wait", action="store_true", help="block until a rate-limit slot frees up")
    p.add_argument("--max-wait", type=float, default=1800)
    a = p.parse_args()

    if not os.path.exists(a.file):
        print(f"no such file: {a.file}", file=sys.stderr); return 1

    if a.wait and not a.no_submit:
        deadline = time.time() + a.max_wait
        while True:
            free, wait = slot_free(a.handle, a.contest)
            if free:
                print("  slot is free"); break
            if time.time() + wait > deadline:
                print(f"  slot not free for {wait:.0f}s, past --max-wait", file=sys.stderr); return 6
            print(f"  blocked {wait:.0f}s -> sleeping", flush=True)
            time.sleep(min(wait, 60) + 2)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.connect_over_cdp(a.cdp, timeout=15000)
        except Exception as e:
            print(f"cannot reach Chrome at {a.cdp}: {e}\n"
                  f"Quit Chrome, then relaunch it with --remote-debugging-port=9333",
                  file=sys.stderr)
            return 7
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        # Reuse an existing tab. Opening a new one activates Chrome and steals
        # focus from whatever the user is doing; navigating a tab that already
        # exists does not. Never call page.bring_to_front() here.
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        opened = not ctx.pages or page not in ctx.pages
        try:
            return submit(page, a.contest, a.problem, a.file, a.lang, not a.no_submit)
        finally:
            if opened:
                page.close()


if __name__ == "__main__":
    sys.exit(main())
