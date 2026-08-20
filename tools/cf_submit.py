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

    # Use the form's FILE INPUT rather than the textarea. Codeforces overlays
    # an ACE editor on #sourceCodeTextarea and copies the EDITOR's content into
    # the textarea when the form posts -- so filling the textarea leaves the
    # editor holding the PREVIOUS file, and that stale source is what gets
    # submitted. That is exactly how r179 arrived as a duplicate of r178.
    # set_input_files drives input[name='sourceFile'] through CDP: no OS file
    # dialog, no textarea, no editor involvement, and the file is uploaded
    # verbatim from disk.
    # Codeforces PERSISTS the last source per problem in localStorage and
    # repopulates the ACE editor from it on every page load. The editor then
    # copies itself into the textarea at submit time and wins over anything we
    # set -- which is why r179 kept arriving as a duplicate of r178 even with
    # the file input populated. Clear the stored source, turn the editor OFF via
    # its own toggle, and blank both surfaces BEFORE attaching the file.
    page.evaluate("""() => {
        try {
            const kill = [];
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                if (/source|editor|submit|ace/i.test(k)) kill.push(k);
            }
            kill.forEach(k => localStorage.removeItem(k));
            sessionStorage.clear();
        } catch (e) {}
    }""")
    try:
        cb = page.locator("#toggleEditorCheckbox")
        if cb.count() and cb.is_checked():
            cb.uncheck(); page.wait_for_timeout(400)
    except Exception as e:
        print(f"  [warn] editor toggle: {e}")
    page.evaluate("""() => {
        const ta = document.querySelector('#sourceCodeTextarea')
                || document.querySelector("textarea[name='source']");
        if (ta) { ta.value = ''; ta.dispatchEvent(new Event('input', {bubbles:true})); }
        if (window.ace) {
            const h = document.querySelector('#editor');
            if (h) { try { window.ace.edit(h).setValue('', -1); } catch (e) {} }
        }
    }""")

    fi = page.locator("input[name='sourceFile']")
    if not fi.count():
        print("  ERROR: no file input on the submit form", file=sys.stderr)
        return 4
    fi.set_input_files(os.path.abspath(path))
    page.wait_for_timeout(500)
    val = page.evaluate(
        "() => { const f = document.querySelector(\"input[name='sourceFile']\");"
        " return f && f.files && f.files.length ? f.files[0].name + ':' + f.files[0].size : ''; }")
    print(f"  file input holds: {val}")
    if not val.endswith(str(len(code))):
        print(f"  ERROR: file input reports {val}, expected size {len(code)}", file=sys.stderr)
        return 4
    # Re-assert emptiness AFTER upload: ACE can restore asynchronously.
    page.wait_for_timeout(600)
    leftover = page.evaluate("""() => {
        const ta = document.querySelector('#sourceCodeTextarea')
                || document.querySelector("textarea[name='source']");
        let n = ta ? ta.value.length : 0;
        if (window.ace) {
            const h = document.querySelector('#editor');
            if (h) { try {
                const e = window.ace.edit(h);
                if (e.getValue().length) { e.setValue('', -1); }
                n += e.getValue().length;
            } catch (e) {} }
        }
        if (ta && ta.value.length) { ta.value=''; ta.dispatchEvent(new Event('input',{bubbles:true})); }
        return n;
    }""")
    print(f"  stale source cleared (was {leftover} chars)")

    if not do_submit:
        print("  FORM READY -- problem, language and source are set.")
        print("  Click Submit in Chrome to send it. The Cloudflare Turnstile check")
        print("  on this form is bot-detection, so the submit click stays yours.")
        return 0

    # Intentionally NOT clicking submit. This form carries a Cloudflare
    # Turnstile token field (input[name=turnstileToken]); posting it from a
    # script means getting past bot-detection the site deliberately deployed.
    # An earlier version clicked here, reported "SUBMITTED", and nothing
    # actually landed -- the post was rejected and the false success was worse
    # than the failure. Fill the form; let the human click.
    print("  FORM READY -- click Submit in Chrome to send it.")
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
