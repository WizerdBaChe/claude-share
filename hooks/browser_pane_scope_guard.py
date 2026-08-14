r"""PreToolUse guard: in-app Browser pane navigation scope (ops/lessons.md L-013).

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

Two jobs, in order of how often they matter:

  1. RECORD (always, never blocks). The desktop app's main.log logs a preview's
     serverId and tabId but NEVER the URL, so after a crash there is no app-side
     record of what was loaded. The 2026-08-12 diagnosis only worked because the
     CLI transcript happened to still be readable. Every navigation is appended
     to telemetry/browser-nav.jsonl so the next investigation starts with the
     answer instead of hunting for it.

  2. DENY a known-crasher host, in-app pane only. After the first crash the
     agent re-issued the identical `preview_start` on the same URL once the app
     came back, turning one crash into two. That is the part that was inside our
     control, and it is a named tool call with an inspectable argument - so per
     the L-011 layering rule it belongs in a hook, not in a line of prose the
     agent reads past while already confident.

Escape hatch by design, not by marker: the deny branch fires ONLY for
`mcp__Claude_Browser__*` (the in-app pane, whose GPU child is shared with the
whole app). `mcp__claude-in-chrome__*` drives a separate Chrome process and is
never denied - it is one of the out-of-process alternatives the denial names.
To un-block a host permanently, edit the blocklist file; that is a deliberate,
reviewable, version-controlled act.

Files:
  hooks/browser-pane-blocklist.json   curated, tracked in git, hand-edited
  telemetry/browser-nav.jsonl         append-only runtime log, gitignored

Scope: `navigate` and `preview_start` on both browser MCP servers. `navigate`
also accepts the literal "back"/"forward" - those carry no host and are logged
without a blocklist check. `preview_start {name: ...}` starts a dev server from
launch.json and has no URL to judge.

Cost: one Python start (~100ms) per pane navigation - a low-volume call. The
matcher deliberately excludes read_page / get_page_text / javascript_tool, which
are the high-volume ones.

Fail-open by design: any parse, IO or lookup error exits 0, so a guard bug can
never block browsing.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
BLOCKLIST_PATH = CLAUDE_DIR / "hooks" / "browser-pane-blocklist.json"
LOG_PATH = CLAUDE_DIR / "telemetry" / "browser-nav.jsonl"

# The in-app pane shares its GPU child with the whole desktop app; Chrome does not.
IN_APP_PREFIX = "mcp__Claude_Browser__"

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


def load_blocklist() -> list:
    try:
        data = json.loads(BLOCKLIST_PATH.read_text(encoding="utf-8"))
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


def record(session_id: str, tool: str, url: str, host: str, decision: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "session": str(session_id)[:64],
            "tool": tool,
            "url": url[:MAX_URL_CHARS],
            "host": host,
            "decision": decision,
        }, ensure_ascii=False)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    session_id = payload.get("session_id", "")

    url = str(tool_input.get("url") or "")
    if not url:
        # preview_start {name: ...} starts a dev server - nothing to judge.
        sys.exit(0)

    host = host_of(url)
    entry = matched_entry(host, load_blocklist()) if (host and tool.startswith(IN_APP_PREFIX)) else None

    record(session_id, tool, url, host, "deny" if entry else "allow")

    if entry:
        reason = (
            f"L-013: `{host}` is on the in-app Browser pane blocklist "
            f"({BLOCKLIST_PATH.name}) because loading it previously crashed the "
            "Electron GPU process. Electron does not relaunch that child: the window "
            "stops compositing, the main process goes silent, and the in-flight turn "
            "of every session in the app is lost. Do NOT retry this URL in the pane - "
            "re-issuing the identical call after a restart is exactly what turned one "
            "crash into two on 2026-08-12.\n"
            "Use an out-of-process route instead, in this order:\n"
            "  1. WebFetch (no browser at all) if you only need the text;\n"
            "  2. `mcp__claude-in-chrome__*` - a separate Chrome process, never denied here;\n"
            "  3. headless Playwright (a one-off "
            "`chromium.launch({headless:true})` script) when you need scripted DOM access.\n"
            f"Recorded reason: {entry.get('reason', 'unrecorded')}. "
            "Detail: ~/.claude/ops/lessons.md L-013. To un-block, the user edits the "
            "blocklist file - do not work around this by switching tools to reach the "
            "same pane."
        )
        deny(reason)

    sys.exit(0)


if __name__ == "__main__":
    main()
