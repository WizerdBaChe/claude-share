r"""PreToolUse/PostToolUse guard: browser-pane UI verification discipline
(ops/lessons.md L-009 + 2026-08-16 amendment, L-010).

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
         compositing stops and every screenshot call TIMES OUT (5s, measured
         2026-08-16) while DOM reads over CDP keep working. Historically
         misdiagnosed as a permission fault. 2026-08-16 premise correction:
         "hidden" is this machine's STEADY STATE - the user's foreground is not
         commandeerable, so "make the pane visible and retry" was never an
         available remedy. Pixels route OUT-OF-PROCESS BY DEFAULT
         (ops/references/browser-pane-pixel-route.md, 1.4-1.5s measured).

Enforcement shape - the screenshot branch is a ROUTER, not just a gate. The
probe is still required first (its result is what routes), and the marker now
records the probe's RESULT, written by the PostToolUse event:

  no fresh marker            -> deny: run the visibilityState probe first
  marker state = "visible"   -> allow: pane screenshot is meaningful; a timeout
                                after a visible probe is a DIFFERENT fault and
                                must stay diagnosable (L-009 over-firing guard)
  marker state = "hidden"    -> deny WITH THE ROUTE: ready-to-run headless
                                command + SendUserFile delivery. Re-probing
                                (e.g. after the user says they are watching)
                                refreshes the state.
  marker state = "unknown"   -> allow (probe ran, result unparseable/legacy -
                                fail-open to the pre-router behaviour)

PostToolUse cannot block (docs) and is used here only to annotate the marker
with the observed state; every parse failure leaves state "unknown", so a
harness payload change degrades this hook to its 2026-08-08 behaviour, never
to a lockout.

Escape hatch (L-010 branch, unchanged): the literal marker
`intentional-midflight` anywhere in the call stands down the settled-read
denial, for the rare case where the mid-transition value IS the measurement.

Write scope: one marker file per session under %TEMP%\claude-ui-verify-guard\
(JSON: {"ts": <epoch>, "state": "unknown|visible|hidden"}; legacy plain-float
markers read as "unknown"). Deliberately outside ~/.claude. Nothing else is
written.

Scope: the in-app Browser pane (mcp__Claude_Browser__*) and Claude-in-Chrome
(mcp__claude-in-chrome__*). Cost: one Python start (~100ms) per browser
computer / javascript_tool call, now also on javascript_tool PostToolUse; the
matchers exclude read_page, find, get_page_text and the network/console
readers, which are the high-volume ones.

Fail-open by design: any parse error exits 0 so a guard bug never blocks work.
Tests: tools/ui-verify-test/test_ui_verify_guard.py.
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

# Probe RESULT, parsed from the PostToolUse tool_response (stringified, so
# escaped-JSON tolerant). Both patterns demand the QUOTED-JSON value shape and
# the parser takes the LAST match: a response that echoes the probe's own code
# (`visibilityState: document.visibilityState,` / `hidden: document.hidden`)
# must not be read as a result — the real result follows any echo.
STATE_RE = re.compile(r'visibilityState\\*"?\s*:\s*\\*"(hidden|visible)\\*"', re.IGNORECASE)
HIDDEN_BOOL_RE = re.compile(r'"hidden\\*"\s*:\s*(true|false)', re.IGNORECASE)

# Opt-out for the case where the mid-flight value IS the measurement.
MIDFLIGHT_MARKER = "intentional-midflight"

ROUTE_POINTER = "ops/references/browser-pane-pixel-route.md"


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


def write_marker(session_id: str, state: str) -> None:
    try:
        MARKER_DIR.mkdir(parents=True, exist_ok=True)
        marker_path(session_id).write_text(
            json.dumps({"ts": time.time(), "state": state}), encoding="utf-8")
    except Exception:
        pass


def read_marker(session_id: str):
    """Returns (fresh: bool, state: str). Legacy float markers -> "unknown"."""
    try:
        p = marker_path(session_id)
        if not p.exists():
            return False, ""
        raw = p.read_text(encoding="utf-8").strip()
        try:
            data = json.loads(raw)
            ts = float(data.get("ts", 0))
            state = str(data.get("state", "unknown"))
        except Exception:
            ts = float(raw)  # legacy format: bare epoch float
            state = "unknown"
        if (time.time() - ts) >= MARKER_TTL_S:
            return False, state
        return True, state
    except Exception:
        return False, ""


def parse_probe_state(tool_response) -> str:
    try:
        text = json.dumps(tool_response, ensure_ascii=False)
    except Exception:
        text = str(tool_response)
    hits = STATE_RE.findall(text)
    if hits:
        return hits[-1].lower()
    hits = HIDDEN_BOOL_RE.findall(text)
    if hits:
        return "hidden" if hits[-1].lower() == "true" else "visible"
    return "unknown"


def deny_probe_first() -> None:
    deny(
        "L-009: probe visibility before asking the pane for pixels. Run "
        "javascript_tool with `document.visibilityState` first. If it returns "
        '"visible", the pane screenshot unlocks for '
        f"{MARKER_TTL_S // 60} minutes and a timeout then means a DIFFERENT "
        'fault. If it returns "hidden" - the steady state on this machine - do '
        "NOT retry the pane: compositing is stopped and a screenshot can only "
        "time out (5s, measured); it is a display-state fault, never a "
        "permission one. Take the picture out-of-process instead:\n"
        "  npx playwright screenshot <url> <out>.png   (~1.5s)\n"
        f"  settled-state probe + PNG: {ROUTE_POINTER}\n"
        "  multi-step (click/hover/then shoot): mcp__playwright-headless__* "
        "(installed Chrome, no window; Playwright-launched, so not occludable)\n"
        "then deliver it with SendUserFile - never ask the user to front a "
        "window. Detail: ~/.claude/ops/lessons.md L-009."
    )


def deny_route_hidden() -> None:
    deny(
        'L-009 route: this session\'s last visibility probe returned "hidden" '
        "- the pane is not compositing, so this screenshot can only time out "
        "(5s, measured, zero pixels). Denied so you do not pay for nothing. "
        "Take the picture out-of-process:\n"
        "  npx playwright screenshot <url> <out>.png   (~1.5s, works from anywhere)\n"
        f"  settled-state probe + PNG (~1.4s): {ROUTE_POINTER}\n"
        "  multi-step (click/hover/then shoot): mcp__playwright-headless__* "
        "(installed Chrome, no window; Playwright-launched, so not occludable)\n"
        "Deliver it with SendUserFile - never ask the user to bring a window "
        'forward (standing premise, ops/environment.md "Browser pane"). DOM/'
        "state reads (read_page / get_page_text / javascript_tool) still work "
        "over CDP for content/structure/state/order claims. If the user has "
        "said they are watching and the pane should now be visible, re-run the "
        'visibilityState probe - a "visible" result refreshes this guard.'
    )


def handle_pre(payload) -> None:
    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    session_id = payload.get("session_id", "")

    if tool.endswith("javascript_tool"):
        text = str(tool_input.get("text", ""))

        if VISIBILITY_RE.search(text):
            write_marker(session_id, "unknown")
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
        fresh, state = read_marker(session_id)
        if not fresh:
            deny_probe_first()
        if state == "hidden":
            deny_route_hidden()
        sys.exit(0)

    sys.exit(0)


def handle_post(payload) -> None:
    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    session_id = payload.get("session_id", "")

    if tool.endswith("javascript_tool"):
        text = str(tool_input.get("text", ""))
        if VISIBILITY_RE.search(text):
            state = parse_probe_state(payload.get("tool_response"))
            write_marker(session_id, state)
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = str(payload.get("hook_event_name", "PreToolUse"))
    if event == "PostToolUse":
        handle_post(payload)
    else:
        handle_pre(payload)


if __name__ == "__main__":
    main()
