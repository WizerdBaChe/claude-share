r"""PreToolUse guard: in-app Browser pane navigation scope (ops/lessons.md L-013).

STATUS: LIVE since 2026-08-12 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

The sibling hook `ui_verify_guard.py` treats the pane as a MEASUREMENT
INSTRUMENT whose failure mode is "you may not get pixels" (L-009) or "the value
you read is mid-flight" (L-010). This hook covers the opposite direction, found
on 2026-08-12: the pane is a live execution surface for third-party content, and
a page it loads can kill the Electron GPU child process, which Electron does not
relaunch - the window stops compositing, the main process stops logging, and the
in-flight turn of every session in the app is lost.

Measured that night: two `GPU process gone { reason: 'crashed', exitCode:
101457950 }` events in a log covering 2026-08-02..12, each 3-4 s after
`preview_start https://saveclip.app/zh-tw`, against ~180 other pane opens in the
same log that never crashed. The page is behind Cloudflare, and its challenge
script (`/cdn-cgi/challenge-platform/.../chl_page/v1`) calls
`navigator.gpu.requestAdapter()` on first load - measured out-of-process with
Playwright, so the WebGPU path is a candidate mechanism, not a proven cause.

ALLOWLIST, NOT BLOCKLIST (user ruling 2026-08-14). The original design denied
known-crasher hosts. That is backwards for this failure class: the 2026-08-12
crash came from a host nobody had ever seen, and a blocklist can only ever
encode hosts that already cost us something. What is actually knowable in
advance is the SAFE set - loopback dev servers and own-build previews, which is
the traffic this surface exists for. Everything else is denied and handed to an
out-of-process route. The cost is real and accepted: a first-time legitimate
host is denied once, and the user allowlists it if the pane is genuinely needed.

HARNESS COMPATIBILITY (user ruling 2026-08-14; rule in L-011). The harness's
`<browser_surfaces>` block names this pane the default surface - that
instruction cannot be edited from here and this hook does not contradict it.
The same block lists `claude-in-chrome` as an available surface, so the denial
picks a listed alternative and states why. Narrowing within the harness's own
menu, not overriding it.

Three jobs, in order of how often they matter:

  1. RECORD (always, never blocks). The desktop app's main.log logs a preview's
     serverId and tabId but NEVER the URL, so after a crash there is no app-side
     record of what was loaded. The 2026-08-12 diagnosis only worked because the
     CLI transcript happened to still be readable. Every navigation is appended
     to telemetry/browser-nav.jsonl so the next investigation starts with the
     answer instead of hunting for it.

  2. DENY anything outside the allowlist, in-app pane only.

  3. REPORT LOUDLY (user ruling 2026-08-14). A deny is written with
     `"loud": true` so it is greppable, and the denial text instructs the agent
     to TELL THE USER which host was denied and offer the allowlist edit. The
     user's requirement was "if something actually breaks I need to be able to
     fix it case by case" - a silent deny would hide exactly the cases worth
     seeing. Enumerate them with integrity-sweep check 13.

Escape hatch by design, not by marker: the deny branch fires ONLY for
`mcp__Claude_Browser__*` (the in-app pane, whose GPU child is shared with the
whole app). `mcp__claude-in-chrome__*` drives a separate Chrome process and is
never denied - it is one of the out-of-process alternatives the denial names.
To allow a host permanently, edit the allowlist file; that is a deliberate,
reviewable, version-controlled act performed by the user.

Files:
  hooks/browser-pane-allowlist.json   curated, tracked in git, hand-edited
  hooks/browser-pane-blocklist.json   retained for its recorded crash reasons,
                                      which make a deny message specific
  telemetry/browser-nav.jsonl         append-only runtime log, gitignored

Scope: `navigate` and `preview_start` on both browser MCP servers. `navigate`
also accepts the literal "back"/"forward" - those carry no host, stay inside
whatever was already allowed, and are logged without a check.
`preview_start {name: ...}` starts a dev server from launch.json: no URL to
judge, and launch.json is a local, reviewed file.

Cost: one Python start (~100ms) per pane navigation - a low-volume call. The
matcher deliberately excludes read_page / get_page_text / javascript_tool, which
are the high-volume ones.

Fail-open on the HOOK's own inputs: an unparsable payload or a missing
tool_input exits 0, so a guard bug can never block browsing. The same holds for
every UNDETERMINED shape (AP-62, widened 2026-09-09): a payload that parses but
is not an object, a non-mapping tool_input, a url that is not a string. The
first two raised AttributeError until then, and the third was folded into an
allow that wrote `"{'a': 1}"` into the navigation record as if it had been
navigated to. Pinned by the U-* cases in the suite.

Fail-CLOSED on the LIST, corrected 2026-09-08. The line here used to claim an
unreadable allowlist "fails OPEN, so the file's absence is not a lockout"; the
code has always done the opposite, because `load_hosts` returns `[]` on any
error and nothing then matches. The code is right and the sentence was wrong:
the blast radius of a wrong allow is the in-flight turn of every session in the
app, out-of-process routes exist for everything denied, and LOCAL_HOSTS lives in
this file rather than in the list, so loopback keeps working with no list at all
-- which is the part of the old claim that was true. Pinned by FO-3/FO-3b.

Proof-of-life: `python hooks/tests/test_browser_pane_scope_guard.py` -- executed
by integrity-sweep check 31, which is what check 13 could not do: enumerating
the deny rows by hand reads what the hook DID, and says nothing about a hook
that has stopped deciding. M-1 is the mutation that keeps the allow side honest,
and the R-* cases assert the nav log, which is the only URL evidence the next
GPU-crash investigation will have.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
ALLOWLIST_PATH = CLAUDE_DIR / "hooks" / "browser-pane-allowlist.json"
BLOCKLIST_PATH = CLAUDE_DIR / "hooks" / "browser-pane-blocklist.json"
# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp dir;
# production never sets it).
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "browser-nav.jsonl"

# The in-app pane shares its GPU child with the whole desktop app; Chrome does not.
IN_APP_PREFIX = "mcp__Claude_Browser__"

# Loopback and own-build previews: the traffic this surface exists for.
# Allowed by the hook itself so the allowlist file never needs boilerplate.
LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}

MAX_URL_CHARS = 500


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def host_of(url: str) -> str:
    """Host for a URL that may arrive without a scheme (preview_start allows that)."""
    raw = url.strip()
    if not raw or raw.lower() in ("back", "forward"):
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        return (urlsplit(raw).hostname or "").lower()
    except Exception:
        return ""


def load_hosts(path: Path) -> list:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    entries = data.get("hosts") if isinstance(data, dict) else data
    return entries if isinstance(entries, list) else []


def matched_entry(host: str, entries: list):
    """Exact host match, or any subdomain of a listed host."""
    for e in entries:
        listed = (e.get("host") if isinstance(e, dict) else e) or ""
        listed = str(listed).strip().lower().lstrip(".")
        if not listed:
            continue
        if host == listed or host.endswith("." + listed):
            return e if isinstance(e, dict) else {"host": listed}
    return None


def is_local(host: str) -> bool:
    return host in LOCAL_HOSTS or host.endswith(".localhost")


def record(session_id: str, tool: str, url: str, host: str, decision: str,
           loud: bool = False) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "session": str(session_id)[:64],
            "tool": tool,
            "url": url[:MAX_URL_CHARS],
            "host": host,
            "decision": decision,
        }
        if loud:
            entry["loud"] = True
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def deny_reason(host: str, known_crasher) -> str:
    head = (
        f"Navigation denied by browser_pane_scope_guard, a local PreToolUse hook "
        f"(not page content). `{host}` is not on the in-app Browser pane allowlist "
        f"({ALLOWLIST_PATH.name}). The pane shares the desktop app's Electron GPU "
        "child process. Electron does not relaunch that child, so a page that kills "
        "it stops the window compositing, wedges the main process, and destroys the "
        "in-flight turn of EVERY session in the app - measured twice on 2026-08-12."
    )
    if known_crasher:
        head += (
            f"\nThis host is additionally on the known-crasher list. Recorded reason: "
            f"{known_crasher.get('reason', 'unrecorded')}. Re-issuing the identical "
            "call after a restart is exactly what turned one crash into two that night."
        )
    return head + (
        "\n\nUse an out-of-process route instead, in this order:\n"
        "  1. WebFetch (no browser at all) if you only need the text;\n"
        "  2. `mcp__claude-in-chrome__*` - a separate Chrome process, never denied "
        "here, and listed by the harness itself as an available surface;\n"
        "  3. headless Playwright: the `mcp__playwright-headless__*` MCP server "
        "(installed Chrome, no window, multi-step, snapshot = cheap text read) "
        "or the one-shot `tools/ui-shot` probe for scripted DOM/pixel access; if "
        "the page needs the user's LOGIN, use `mcp__claude-in-chrome__*`.\n"
        "Do NOT work around this by switching tools to reach the same pane.\n\n"
        f"Only the user edits {ALLOWLIST_PATH.name}, so pane access for this host "
        "is theirs to grant and cannot be arranged from inside this call."
        + _receipt("browser_pane_scope_guard", host=host)
        + _fp("browser_pane_scope_guard")
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if not isinstance(payload, dict):
        sys.exit(0)          # undetermined: parses, but is not a payload object
    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)          # same class, one level in
    session_id = payload.get("session_id", "")

    raw_url = tool_input.get("url")
    # A non-string url is undetermined, not a URL: str() would put
    # `"{'a': 1}"` in the navigation record as if it had been navigated to.
    url = raw_url if isinstance(raw_url, str) else ""
    if not url:
        # preview_start {name: ...} starts a dev server - nothing to judge.
        sys.exit(0)

    host = host_of(url)

    # Not the in-app pane, or no host to judge (back/forward): record and pass.
    if not host or not tool.startswith(IN_APP_PREFIX):
        record(session_id, tool, url, host, "allow")
        sys.exit(0)

    if is_local(host) or matched_entry(host, load_hosts(ALLOWLIST_PATH)):
        record(session_id, tool, url, host, "allow")
        sys.exit(0)

    record(session_id, tool, url, host, "deny", loud=True)
    deny(deny_reason(host, matched_entry(host, load_hosts(BLOCKLIST_PATH))))


if __name__ == "__main__":
    main()
