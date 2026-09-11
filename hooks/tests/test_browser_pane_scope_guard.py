"""Two-sided calibration for browser_pane_scope_guard.py — stdlib only, hermetic.

Run: python hooks/tests/test_browser_pane_scope_guard.py   (exit 0 = all pass)

WHY BOTH SIDES, AND WHY THE ALLOW SIDE IS THE RISKY ONE. This is an ALLOWLIST
guard: a version that denied everything would still look correct from the deny
side, and the traffic the pane exists for — loopback dev servers and own-build
previews — is exactly what it would break. LOCAL_HOSTS lives in the hook rather
than in the list file precisely so that path never depends on a file; A-* pins
it. M-1 is the mutation that keeps the allow side honest: with an EMPTY
allowlist the host A-05 allows must be denied, or A-05 was passing on nothing.

RECORD IS A JOB, NOT A SIDE EFFECT. The desktop app logs a preview's serverId
and tabId but never the URL, so after a GPU crash there is no app-side record of
what was loaded — that is the whole reason telemetry/browser-nav.jsonl exists.
A hook that quietly stopped writing it would cost nothing until the next crash,
when the answer would be missing again. The R-* cases assert the rows.

EXTENDING (PH-11 / AP-61): a new denied shape gets a D-* case, a new allowed one
an A-* case; both go through `run()`, so a case is one call.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "browser_pane_scope_guard.py"
HOME = Path(__file__).resolve().parents[2]
LIVE_ALLOW = HOME / "hooks" / "browser-pane-allowlist.json"
LIVE_LOG = HOME / "telemetry" / "browser-nav.jsonl"

spec = importlib.util.spec_from_file_location("browser_pane_scope_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

PANE = "mcp__Claude_Browser__navigate"
PANE_PREVIEW = "mcp__Claude_Browser__preview_start"
CHROME = "mcp__claude-in-chrome__navigate"

FAILS: list[str] = []


def check_that(name: str, cond: bool, detail="") -> None:
    if not cond:
        FAILS.append(f"{name}: {detail}" if detail else name)
    print(f"{'ok  ' if cond else 'FAIL'} {name}")


class Box:
    """One isolated CLAUDE_CONFIG_DIR: its own allowlist, blocklist and nav log."""

    def __init__(self, allow=None, block=None):
        self.dir = Path(tempfile.mkdtemp(prefix="pane-guard-"))
        (self.dir / "hooks").mkdir(parents=True, exist_ok=True)
        if allow is not None:
            (self.dir / "hooks" / "browser-pane-allowlist.json").write_text(
                json.dumps({"hosts": allow}), encoding="utf-8")
        if block is not None:
            (self.dir / "hooks" / "browser-pane-blocklist.json").write_text(
                json.dumps({"hosts": block}), encoding="utf-8")
        self.env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.dir),
                        PYTHONIOENCODING="utf-8")
        # This box's whole point is CLAUDE_CONFIG_DIR isolation; an inherited
        # CLAUDE_TELEMETRY_DIR (e.g. from a harness running this suite) now
        # outranks it in the hook's own LOG_PATH resolution and would steer
        # rows away from self.log, so it must not leak in here.
        self.env.pop("CLAUDE_TELEMETRY_DIR", None)
        self.log = self.dir / "telemetry" / "browser-nav.jsonl"

    def run(self, tool: str, ti: dict):
        """-> (denied, reason, returncode)."""
        payload = json.dumps({"tool_name": tool, "tool_input": ti,
                              "session_id": "test-session"})
        p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=payload,
                           capture_output=True, text=True, env=self.env, timeout=60)
        out = (p.stdout or "").strip()
        if not out:
            return False, "", p.returncode
        try:
            spec_out = json.loads(out)["hookSpecificOutput"]
        except Exception:
            return False, out, p.returncode
        return (spec_out.get("permissionDecision") == "deny",
                spec_out.get("permissionDecisionReason", ""), p.returncode)

    def rows(self):
        if not self.log.is_file():
            return []
        return [json.loads(ln) for ln in self.log.read_text(encoding="utf-8").splitlines()
                if ln.strip()]


ALLOWED_HOST = "preview.mybuild.example"
CRASHER = "saveclip.app"
BLOCK = [{"host": CRASHER, "reason": "GPU child crashed twice on 2026-08-12"}]

# ------------------------------------------------------------------ deny side
print("-- D: in-app pane navigations that MUST be denied")

box = Box(allow=[{"host": ALLOWED_HOST}], block=BLOCK)
for cid, tool, ti, why in [
    ("D-01", PANE, {"url": f"https://{CRASHER}/zh-tw"}, "the host measured to crash the GPU child"),
    ("D-02", PANE, {"url": "https://example.com/page"}, "an ordinary third-party host"),
    ("D-03", PANE_PREVIEW, {"url": "https://example.com"}, "preview_start takes a URL too"),
    ("D-04", PANE, {"url": "example.com/page"}, "no scheme: preview_start allows that spelling"),
    ("D-05", PANE, {"url": "https://cdn.example.com"}, "a subdomain of a host nobody listed"),
    ("D-06", PANE, {"url": "HTTPS://EXAMPLE.COM"}, "the host compare is case-folded"),
    ("D-07", PANE, {"url": "http://localhost.evil.example"},
     "a host that merely STARTS with localhost is not loopback"),
    ("D-08", PANE, {"url": f"https://{ALLOWED_HOST}.evil.example"},
     "an allowlisted host as a PREFIX of someone else's domain"),
]:
    denied, reason, rc = box.run(tool, ti)
    check_that(f"{cid} deny: {why}", denied and rc == 0,
               f"rc={rc}, denied={denied}, reason={reason[:90]!r}")

denied, reason, _rc = box.run(PANE, {"url": f"https://{CRASHER}/x"})
check_that("D-01b the deny message quotes the recorded crash reason",
           "2026-08-12" in reason and "crashed twice" in reason, reason[:200])
check_that("D-01c and names the host, the allowlist file and an out-of-process route",
           CRASHER in reason and "allowlist" in reason and "claude-in-chrome" in reason,
           reason[:200])

# ------------------------------------------------------------------ allow side
print("\n-- A: the traffic this surface exists for, which must NEVER be denied")

for cid, tool, ti, why in [
    ("A-01", PANE, {"url": "http://localhost:3000"}, "the loopback dev server"),
    ("A-02", PANE, {"url": "http://127.0.0.1:8080/x"}, "loopback by IP"),
    ("A-03", PANE, {"url": "http://app.localhost:3000"}, "a *.localhost dev host"),
    ("A-04", PANE, {"url": "http://[::1]:5173"}, "IPv6 loopback"),
    ("A-05", PANE, {"url": f"https://{ALLOWED_HOST}/index.html"}, "a host on the allowlist"),
    ("A-06", PANE, {"url": f"https://sub.{ALLOWED_HOST}/x"}, "a subdomain of a listed host"),
    ("A-07", CHROME, {"url": "https://example.com"},
     "a separate Chrome process: never denied, and the denial names it"),
    ("A-08", PANE, {"url": "back"}, "history navigation carries no host"),
    ("A-09", PANE_PREVIEW, {"name": "dev"}, "a launch.json server: no URL to judge"),
]:
    denied, reason, rc = box.run(tool, ti)
    check_that(f"{cid} allow: {why}", not denied and rc == 0,
               f"rc={rc}, reason={reason[:120]!r}")

# ------------------------------------------------ the mutation that tests A-05
print("\n-- M-1: with an EMPTY allowlist the same host must be denied")

empty = Box(allow=[], block=BLOCK)
denied, _r, _rc = empty.run(PANE, {"url": f"https://{ALLOWED_HOST}/index.html"})
check_that("M-1 A-05's host is denied when nothing lists it "
           "(so A-05 was reading the allowlist, not passing on nothing)", denied)
denied, _r, _rc = empty.run(PANE, {"url": "http://localhost:3000"})
check_that("M-1b but loopback still works with an empty allowlist "
           "(LOCAL_HOSTS lives in the hook, not in the file)", not denied)

# ------------------------------------------------------------------ recording
print("\n-- R: the record job — after a crash this log is the only URL evidence")

box = Box(allow=[{"host": ALLOWED_HOST}], block=BLOCK)
box.run(PANE, {"url": "http://localhost:3000"})
box.run(CHROME, {"url": "https://example.com"})
box.run(PANE, {"url": "back"})
box.run(PANE, {"url": "https://example.com/denied-here"})
rows = box.rows()
check_that("R-1 every navigation is recorded, allows included", len(rows) == 4, rows)
check_that("R-2 the deny row is marked loud so it is greppable",
           [r for r in rows if r["decision"] == "deny"]
           and all(r.get("loud") for r in rows if r["decision"] == "deny"),
           rows[-1:])
check_that("R-2b and the allow rows are not marked loud",
           not any(r.get("loud") for r in rows if r["decision"] == "allow"), rows[:3])
check_that("R-3 the out-of-app navigation is recorded as an allow",
           any(r["tool"] == CHROME and r["decision"] == "allow" for r in rows), rows)
check_that("R-4 back/forward is recorded with an empty host, not dropped",
           any(r["url"] == "back" and r["host"] == "" for r in rows), rows)
check_that("R-5 every row carries ts/session/tool/url/host/decision",
           all({"ts", "session", "tool", "url", "host", "decision"} <= set(r)
               for r in rows), rows[:1])

long_url = "https://example.com/" + "a" * 4000
box.run(PANE, {"url": long_url})
check_that(f"R-6 a pathological URL is truncated to MAX_URL_CHARS={guard.MAX_URL_CHARS}",
           len(box.rows()[-1]["url"]) <= guard.MAX_URL_CHARS, len(box.rows()[-1]["url"]))

# ------------------------------------------------------------------ fail-open
print("\n-- FO: what happens when the hook's own inputs are broken")

for cid, raw, why in (
    ("FO-1", "not json at all", "unparsable stdin"),
    ("FO-2", '{"tool_name": "mcp__Claude_Browser__navigate"}', "no tool_input"),
):
    p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=raw,
                       capture_output=True, text=True, env=box.env, timeout=60)
    check_that(f"{cid} {why}: exits 0 silently",
               p.returncode == 0 and not (p.stdout or "").strip(),
               f"rc={p.returncode} stdout={(p.stdout or '')[:80]!r}")

# ---------------------------------- U: input that belongs to no declared class
print("\n-- U: undetermined input — silent, recorded nowhere (AP-62)")

ubox = Box(block=BLOCK)
for cid, raw, why in (
    ("U-1", "[1, 2]", "a payload that parses but is not an object"),
    ("U-1b", '"a string payload"', "a JSON scalar payload"),
    ("U-2", '{"tool_name": "mcp__Claude_Browser__navigate", "tool_input": ["url"]}',
     "a non-mapping tool_input"),
    ("U-3", '{"tool_name": "mcp__Claude_Browser__navigate", '
            '"tool_input": {"url": {"unexpected": "shape"}}}',
     "a url that is not a string"),
):
    p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=raw,
                       capture_output=True, text=True, env=ubox.env, timeout=60)
    check_that(f"{cid} {why}: exits 0 silently",
               p.returncode == 0 and not (p.stdout or "").strip(),
               f"rc={p.returncode} stdout={(p.stdout or '')[:80]!r}")
# The second half of AP-62: excluded from the count, not folded into one. U-1..
# U-3 must leave NO row behind — a `str()` of the url would have written
# "{'unexpected': 'shape'}" into the record as a navigation that happened.
check_that("U-4 and none of them was recorded as a navigation",
           not (ubox.dir / "telemetry" / "browser-nav.jsonl").exists(),
           (ubox.dir / "telemetry" / "browser-nav.jsonl").read_text(encoding="utf-8")[:200]
           if (ubox.dir / "telemetry" / "browser-nav.jsonl").exists() else "")

corrupt = Box(block=BLOCK)
(corrupt.dir / "hooks" / "browser-pane-allowlist.json").write_text(
    "{ not json", encoding="utf-8")
denied, _r, rc = corrupt.run(PANE, {"url": f"https://{ALLOWED_HOST}/x"})
check_that("FO-3 an UNREADABLE allowlist denies non-local hosts — fail-CLOSED on this "
           "path, on purpose: the blast radius of a wrong allow is every session in "
           "the app, and out-of-process routes exist", denied and rc == 0,
           f"denied={denied} rc={rc}")
denied, _r, _rc = corrupt.run(PANE, {"url": "http://localhost:3000"})
check_that("FO-3b and loopback still works, so a broken list is not a lockout",
           not denied)

# ------------------------------------------------- the live list, and isolation
print("\n-- the live allowlist, and isolation from the live nav log")

check_that("L-1 the LIVE allowlist parses to a list of entries",
           isinstance(guard.load_hosts(LIVE_ALLOW), list),
           f"{LIVE_ALLOW} did not parse — the hook would then deny every non-local "
           f"host, which is safe but is NOT what the file says")
live_hosts = guard.load_hosts(LIVE_ALLOW)
bad = [e for e in live_hosts
       if not str((e.get("host") if isinstance(e, dict) else e) or "").strip()]
check_that("L-1b every live entry carries a non-empty host", not bad, bad)
print(f"note [uncounted] the live allowlist holds {len(live_hosts)} host(s); an empty "
      f"list is the documented steady state — loopback is allowed by the hook itself, "
      f"and a third-party host is meant to be a deliberate user edit")

copied = Box(block=BLOCK)
shutil.copyfile(LIVE_ALLOW, copied.dir / "hooks" / "browser-pane-allowlist.json")
for e in live_hosts:
    h = str((e.get("host") if isinstance(e, dict) else e)).strip().lstrip(".")
    denied, _r, _rc = copied.run(PANE, {"url": f"https://{h}/"})
    check_that(f"L-2 the live list's own host is allowed by it: {h}", not denied)

before = LIVE_LOG.stat().st_size if LIVE_LOG.exists() else -1
Box(allow=[]).run(PANE, {"url": "https://example.com"})
after = LIVE_LOG.stat().st_size if LIVE_LOG.exists() else -1
check_that("I-1 the LIVE browser-nav.jsonl was not written to by this suite",
           after == before,
           f"{before} -> {after} bytes; CLAUDE_CONFIG_DIR isolation broke and the log "
           f"the next crash investigation reads would carry test rows")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
