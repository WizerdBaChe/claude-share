"""token_key_gate.py - a focused definition token must not swallow the page's shortcuts.

Property (rules/deliverable-doc-refs.md, layer 2 "registry-driven hover cards"):
a REFS/SYMS token (`.ref`, `.sym`, `.num`) is focusable (tabIndex=0), so a mouse click
leaves focus on it. While it holds focus, only its OWN activation keys (Enter / Space)
may be intercepted; every other key - Backspace-return, G glossary, M TOC, arrows -
must still reach the page handler. Defect found 2026-10-05 (SSLD textbook shell,
AssetVault briefing-deck-shell): the keydown handler returned for EVERY key on a
focused token, so Backspace and G were dead right after the click that jumped.

  run <built.html ...>     DYNAMIC (authoritative): headless Chromium clicks a token that
                           jumps, keeps focus on it, presses Backspace (scroll must come
                           back) and G (#gloss must open). PASS / FAIL / UNDET per file.
  static <path ...>        STATIC (cheap, for shells and builders that are not runnable
                           pages): flags the swallow signature line. Heuristic - it knows
                           the two shapes measured in 2026-10-05; `run` decides.
  selftest                 two-sided controls for both modes on generated fixtures.

Exit: 0 all PASS (UNDET allowed), 1 any FAIL, 2 instrument unavailable (playwright).
A file the gate cannot exercise (no token that jumps, no #gloss) is UNDET, never PASS.
"""
from __future__ import annotations

import re
import sys
import tempfile
import time
from pathlib import Path

VIEWPORT = {"width": 1707, "height": 830}   # measured delivery viewport (deliverable-doc-refs.md)
TOKENS = ".ref,.sym,.num"
MAX_TRIES = 40

# The swallow shape: the token test is the WHOLE condition, followed by `return` either
# directly (deck shell) or after an inner Enter/Space block (textbook shell). The fixed
# form adds `&& (e.key==='Enter'||e.key===' ')` to the condition and does not match.
SIGNATURE = re.compile(
    r"closest\(\s*'\.ref,\.sym[^']*'\s*\)\s*\)\s*"
    r"(?:\{\s*if\s*\(\s*e\.key\s*===?\s*'Enter'[^}]*\}\s*)?return\b")
STATIC_SUFFIXES = {".html", ".htm", ".tpl", ".py", ".js"}


# ---------------------------------------------------------------- static
def static_hits(text: str) -> list[int]:
    return [i for i, ln in enumerate(text.splitlines(), 1) if SIGNATURE.search(ln)]


def iter_files(paths: list[str]):
    me = Path(__file__).resolve()                 # this file carries the bad shapes as fixtures
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if (f.suffix.lower() in STATIC_SUFFIXES and f.resolve() != me
                        and not {".git", "node_modules"} & set(f.parts)):
                    yield f
        elif p.exists() and p.resolve() != me:
            yield p


def cmd_static(paths: list[str]) -> int:
    bad = 0
    for f in iter_files(paths):
        try:
            hits = static_hits(f.read_text(encoding="utf-8", errors="replace"))
        except OSError as e:
            print(f"UNDET  {f}  unreadable: {e}")
            continue
        if hits:
            bad += 1
            print(f"FAIL   {f}  swallow signature at line(s) {hits}")
    print(f"static: {bad} file(s) carry the swallow signature")
    return 1 if bad else 0


# ---------------------------------------------------------------- dynamic
SETTLE_JS = "() => [window.scrollX, window.scrollY]"


def settle(page, timeout=3.0):
    last, stable, t0 = None, 0, time.time()
    while time.time() - t0 < timeout:
        cur = page.evaluate(SETTLE_JS)
        stable = stable + 1 if cur == last else 0
        if stable >= 3:
            return cur[1]
        last = cur
        page.wait_for_timeout(100)
    return page.evaluate(SETTLE_JS)[1]


def check_page(page, url: str) -> tuple[str, str]:
    page.goto(url)
    page.wait_for_load_state("load")
    page.wait_for_timeout(400)
    toks = page.locator(TOKENS)
    n = toks.count()
    if n == 0:
        return "UNDET", "no .ref/.sym/.num token on the page"
    for i in range(min(n, MAX_TRIES)):
        tok = toks.nth(i)
        if not tok.is_visible():
            continue
        tok.scroll_into_view_if_needed()
        y0 = settle(page)
        tok.click()
        y1 = settle(page)
        if abs(y1 - y0) < 40:
            continue                              # this token has no jump target
        # the defect's precondition, made deterministic: focus stays on the token
        tok.evaluate("e => e.focus({preventScroll: true})")
        if not page.evaluate(f"() => !!(document.activeElement && document.activeElement.closest('{TOKENS}'))"):
            return "UNDET", "token cannot hold focus - precondition absent"
        page.keyboard.press("Backspace")
        y2 = settle(page)
        back_ok = abs(y2 - y0) < abs(y1 - y0) / 2
        msg = f"token #{i} ({tok.inner_text()[:16]!r}): y {y0:.0f} -> jump {y1:.0f} -> Backspace {y2:.0f}"
        if page.locator("#gloss").count() == 0:
            gl = "glossary UNDET (no #gloss)"
            gl_ok = True
        else:
            tok.evaluate("e => e.focus({preventScroll: true})")
            page.keyboard.press("g")
            page.wait_for_timeout(200)
            opened = page.evaluate("() => document.getElementById('gloss').classList.contains('open')")
            rows = page.locator("#gloss .gl-row").count()
            gl_ok = bool(opened)
            gl = f"G with token focused: glossary {'opened' if opened else 'DID NOT open'} ({rows} rows)"
            page.keyboard.press("Escape")
        verdict = "PASS" if (back_ok and gl_ok) else "FAIL"
        return verdict, f"{msg} ({'returned' if back_ok else 'DID NOT return'}); {gl}"
    return "UNDET", f"none of the first {min(n, MAX_TRIES)} visible tokens jumps"


def cmd_run(files: list[str]) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("UNDET  playwright not installed in this interpreter - the token-key property "
              "was NOT checked (pip install playwright; the browser is usually already under "
              "%LOCALAPPDATA%\\ms-playwright)")
        return 2
    worst = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=VIEWPORT, reduced_motion="reduce")
        page = ctx.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for f in files:
            path = Path(f).resolve()
            if not path.exists():
                print(f"UNDET  {f}  missing")
                continue
            errors.clear()
            v, msg = check_page(page, path.as_uri())
            if errors:
                msg += f"; page errors: {errors[:2]}"
            print(f"{v:<6} {path.name}  {msg}")
            if v == "FAIL":
                worst = 1
        b.close()
    return worst


# ---------------------------------------------------------------- selftest
FIXTURE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>fixture</title>
<style>section{min-height:1400px} #gloss{display:none} #gloss.open{display:block}</style></head><body>
<section id="s1"><p>see <span class="ref" tabindex="0" data-key="X1">X1</span> for the definition</p></section>
<section id="s2"><p>filler</p></section>
<section id="s3"><h2>X1 defined here</h2></section>
<div id="gloss"><div id="glosslist"><div class="gl-row">X1</div></div></div>
<script>
var REFS = {X1: {s: 's3'}}, back = [], gloss = document.getElementById('gloss');
function entryFor(k){ return REFS[k]; }
function jumpTo(id){ back.push(window.scrollY); document.getElementById(id).scrollIntoView(); }
function goBack(){ if (back.length) window.scrollTo(0, back.pop()); }
document.addEventListener('click', function(e){ var sp = e.target.closest('.ref');
  if (sp){ var en = entryFor(sp.dataset.key); if (en && en.s) jumpTo(en.s); } });
document.addEventListener('keydown', function(e){
  %s
  if (e.key === 'g'){ gloss.classList.toggle('open'); }
  if (e.key === 'Escape'){ gloss.classList.remove('open'); }
  if (e.key === 'Backspace'){ e.preventDefault(); goBack(); }
});
</script></body></html>
"""
BAD_TEXTBOOK = ("if (e.target && e.target.closest && e.target.closest('.ref,.sym')){ if (e.key==='Enter'||e.key===' ')"
                "{ e.preventDefault(); var en = entryFor(e.target.dataset.key); if (en && en.s) jumpTo(en.s); } return; }")
BAD_DECK = "if (e.target && e.target.closest && e.target.closest('.ref,.sym')) return;"
GOOD = ("if (e.target && e.target.closest && e.target.closest('.ref,.sym') && (e.key==='Enter'||e.key===' '))"
        "{ e.preventDefault(); var en = entryFor(e.target.dataset.key); if (en && en.s) jumpTo(en.s); return; }")


def cmd_selftest() -> int:
    ok = True
    # static: both measured bad shapes must hit, the fixed shape must not
    for name, line, want in (("bad-textbook", BAD_TEXTBOOK, True), ("bad-deck", BAD_DECK, True),
                             ("good", GOOD, False)):
        got = bool(static_hits(line))
        print(f"static {name:<13} hit={got} expected={want}  {'ok' if got == want else 'MISMATCH'}")
        ok &= got == want
    # dynamic: known-false must FAIL, known-true must PASS (a reject-all gate fails the latter)
    with tempfile.TemporaryDirectory() as d:
        files = {}
        for name, line in (("bad-textbook", BAD_TEXTBOOK), ("bad-deck", BAD_DECK), ("good", GOOD)):
            f = Path(d) / f"{name}.html"
            f.write_text(FIXTURE % line, encoding="utf-8")
            files[name] = f
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("dynamic selftest NOT RUN: playwright missing")
            return 2
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_context(viewport=VIEWPORT, reduced_motion="reduce").new_page()
            for name, f in files.items():
                want = "PASS" if name == "good" else "FAIL"
                v, msg = check_page(page, f.as_uri())
                print(f"dynamic {name:<12} {v} expected={want}  {'ok' if v == want else 'MISMATCH'}  ({msg})")
                ok &= v == want
            b.close()
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in ("run", "static", "selftest"):
        print(__doc__)
        return 2
    if argv[1] == "selftest":
        return cmd_selftest()
    if len(argv) < 3:
        print("give at least one path")
        return 2
    return cmd_run(argv[2:]) if argv[1] == "run" else cmd_static(argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
