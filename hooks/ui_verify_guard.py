r"""PreToolUse guard: browser-pane UI verification discipline (ops/lessons.md L-009, L-010).

Two failures kept recurring in browser-pane UI verification, and neither is
reliably prevented by a rules-layer reminder, because both fire at the moment
the agent is already mid-measurement and confident:

  L-010  getComputedStyle() called during a CSS transition returns the
         INTERPOLATED mid-flight value (CSSOM resolved value), not the target.
         The MCP round trip has non-deterministic latency, so the assertion
         comes back FLAKY rather than stably wrong - which sends the reader to
         debug correct code. Fix: finish animations first
         (el.getAnimations({subtree:true}).forEach(a => a.finish())) or inject
         a transition:none stylesheet, then measure.

  L-009  An occluded browser pane reports document.visibilityState === "hidden";
         compositing stops and every screenshot call TIMES OUT while DOM reads
         over CDP keep working. Historically misdiagnosed as a permission fault
         and "fixed" by opening more permissions. Fix: probe visibilityState
         before asking for pixels; take real pictures out-of-process.

Enforcement shape. Both branches DENY rather than warn: a warning arrives as
text the agent may skim, a denial forces the corrected call. Each denial costs
exactly one retry, and the corrected form is the one that should have been used
anyway.

The screenshot branch is stateful: a javascript_tool call mentioning
visibilityState writes a per-session marker, and a screenshot within
MARKER_TTL_S of that marker is allowed through. So the first screenshot of a
session is denied once, the probe satisfies it, and the rest of the session
runs unimpeded. The marker is per session_id, so it cannot leak between
sessions, and it expires so it cannot vouch for a stale observation.

Escape hatch. Measuring an IN-FLIGHT value is occasionally the actual goal -
verifying an easing curve, sampling a transition midpoint. The literal marker
`intentional-midflight` anywhere in the call (a comment is enough) says the
mid-transition read is the point, and the L-010 branch stands down. Same shape
as model_cap_guard.py's `[user-approved-top-tier]`.

Write scope: one marker file per session under
%TEMP%\claude-ui-verify-guard\. Deliberately outside ~/.claude - it is
ephemeral session state, and the config directory is a git repo that must not
accumulate untracked runtime droppings. Nothing else is written.

Scope: the in-app Browser pane (mcp__Claude_Browser__*) and Claude-in-Chrome
(mcp__claude-in-chrome__*). Known gap: a measurement performed inside
`read_page`/`get_page_text` output rather than an explicit getComputedStyle
call is not visible here - those tools do not report computed style, so the
gap is theoretical. Cost: one Python start (~100ms) per browser computer /
javascript_tool call; the matcher excludes read_page, find, get_page_text and
the network/console readers, which are the high-volume ones.

Fail-open by design: any parse error exits 0 so a guard bug never blocks work.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

MARKER_TTL_S = 300
MARKER_DIR = Path(os.environ.get("TEMP", "/tmp")) / "claude-ui-verify-guard"

# A read of rendered style that an in-flight transition can corrupt.
MEASURE_RE = re.compile(r"getComputedStyle|currentStyle|computedStyleMap", re.IGNORECASE)

# Any of these in the same call means the caller already settled the page.
SETTLED_RE = re.compile(
    r"getAnimations|transition\s*:\s*none|animation-duration\s*:\s*0"
    r"|__nomotion|prefers-reduced-motion",
    re.IGNORECASE,
)

VISIBILITY_RE = re.compile(r"visibilityState", re.IGNORECASE)

# Opt-out for the case where the mid-flight value IS the measurement.
MIDFLIGHT_MARKER = "intentional-midflight"


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def marker_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "", str(session_id))[:64] or "nosession"
    return MARKER_DIR / f"{safe}.probe"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    session_id = payload.get("session_id", "")

    if tool.endswith("javascript_tool"):
        text = str(tool_input.get("text", ""))

        if VISIBILITY_RE.search(text):
            try:
                MARKER_DIR.mkdir(parents=True, exist_ok=True)
                marker_path(session_id).write_text(str(time.time()), encoding="utf-8")
            except Exception:
                pass
            sys.exit(0)

        if (
            MEASURE_RE.search(text)
            and not SETTLED_RE.search(text)
            and MIDFLIGHT_MARKER not in text
        ):
            deny(
                "L-010: reading computed style without settling the page first. "
                "During a CSS transition getComputedStyle returns the interpolated "
                "mid-flight value, so this assertion will be FLAKY, not stably wrong. "
                "Re-issue with the animations finished in the same call, e.g.\n"
                "  el.getAnimations({subtree:true}).forEach(a => { try { a.finish() } catch {} });\n"
                "  void document.body.offsetHeight;\n"
                "  return getComputedStyle(el).backgroundColor;\n"
                "For infinite keyframes finish() cannot help - inject "
                "`*{transition:none!important;animation-duration:0s!important}` instead. "
                "Detail: ~/.claude/ops/lessons.md L-010."
            )
        sys.exit(0)

    if tool.endswith("computer") and str(tool_input.get("action", "")) == "screenshot":
        try:
            p = marker_path(session_id)
            if p.exists() and (time.time() - p.stat().st_mtime) < MARKER_TTL_S:
                sys.exit(0)
        except Exception:
            sys.exit(0)
        deny(
            "L-009: probe visibility before asking the pane for pixels. Run "
            "javascript_tool with `document.visibilityState` first. If it returns "
            '"hidden" the pane is occluded, compositing has stopped, and this '
            "screenshot will TIME OUT - that is a display-state fault, never a "
            "permission one, so do not open permissions to chase it; read_page / "
            "get_page_text / read_console_messages still work over CDP, and real "
            "pictures come from a separate browser process "
            "(`npx playwright screenshot <url> <out>.png`). "
            'If it returns "visible" the probe clears this guard for '
            f"{MARKER_TTL_S // 60} minutes and a timeout then means a different "
            "fault. Detail: ~/.claude/ops/lessons.md L-009."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
