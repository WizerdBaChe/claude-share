"""Synthetic test suite for hooks/ui_verify_guard.py, ROUTER edition (v2).

Run: python test_ui_verify_guard.py [path-to-hook]
Default hook path: ~/.claude/hooks/ui_verify_guard.py — pass the draft's path
to test it before applying. On apply this file REPLACES
tools/ui-verify-test/test_ui_verify_guard.py (v1, 10 cases, gate-only).

Covers the v1 ten (probe gate, L-010 settle, escape hatch, cross-session
isolation, fail-open) plus the router semantics: PostToolUse annotates the
marker with the probe RESULT; screenshot is allowed on "visible"/"unknown",
denied-with-route on "hidden"; legacy float markers and unparseable responses
degrade to "unknown" (= pre-router behaviour); a response that merely echoes
the probe's code must not be misread as a result.

Scope note: browser_pane_scope_guard's deny branch is deliberately NOT
exercised here — a synthetic deny would append a `"loud": true` row to
telemetry/browser-nav.jsonl, which integrity-sweep check 13 surfaces for USER
adjudication. Its 7/7 record: rule-registry.md "in-app Browser pane".
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path.home() / ".claude" / "hooks" / "ui_verify_guard.py")
PY = sys.executable
SESSION = "synthtest-A"
MARKER = Path(os.environ["TEMP"]) / "claude-ui-verify-guard" / f"{SESSION}.probe"
# CLAUDE_TELEMETRY_DIR (ruling 2026-09-11): nothing here isolated the deny
# receipt's writer, so its rows landed in production
# telemetry/ui-verify-guard.jsonl (160 rows, 7 sessions per the 2026-09-10
# inventory). One temp dir for the whole run fixes that at the source.
_ENV = dict(os.environ, CLAUDE_TELEMETRY_DIR=tempfile.mkdtemp(prefix="ui-verify-test-"))

def run(payload, raw=None):
    p = subprocess.run([PY, str(HOOK)],
                       input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, timeout=15, env=_ENV)
    denied = False
    reason = ""
    if p.stdout.strip():
        try:
            out = json.loads(p.stdout)
            hso = out.get("hookSpecificOutput", {})
            denied = hso.get("permissionDecision") == "deny"
            reason = hso.get("permissionDecisionReason", "")
        except Exception:
            pass
    return p.returncode, denied, reason

def case(name, payload, expect_deny, expect_in_reason=None):
    rc, denied, reason = run(payload)
    ok = (denied == expect_deny) and rc == 0
    if ok and expect_in_reason:
        ok = all(s in reason for s in expect_in_reason)
    print(f"{'PASS' if ok else 'FAIL'}  {name}  (deny={denied})")
    return ok

def marker_state():
    try:
        return json.loads(MARKER.read_text(encoding="utf-8")).get("state")
    except Exception:
        return None

def check(name, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    return cond

def pre(tool, tool_input, session=SESSION):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": tool_input, "session_id": session}

def post(tool, tool_input, tool_response, session=SESSION):
    return {"hook_event_name": "PostToolUse", "tool_name": tool,
            "tool_input": tool_input, "tool_response": tool_response,
            "session_id": session}

PROBE_TEXT = "(async () => ({ visibilityState: document.visibilityState, hidden: document.hidden }))()"
JS = "mcp__Claude_Browser__javascript_tool"
CAM = "mcp__Claude_Browser__computer"
SHOT = {"action": "screenshot"}

def main():
    if MARKER.exists():
        MARKER.unlink()
    r = []

    r.append(case("01 screenshot w/o probe -> deny, teaches probe + route",
                  pre(CAM, SHOT), True,
                  ["visibilityState", "playwright screenshot", "ui-probe.mjs",
                   # deny-message contract (rules/hook-deny-message.md): the
                   # route used to be a pointer at the route DOC; it is now the
                   # runnable command, and the message must name its own actor
                   # and offer a misfire exit.
                   "ui_verify_guard", "report_fp.py"]))
    r.append(case("02 visibility probe (Pre) -> allow, marker born", pre(JS, {"text": PROBE_TEXT}), False))
    r.append(check("03 marker state is 'unknown' before any result", marker_state() == "unknown"))
    r.append(case("04 screenshot on 'unknown' -> allow (pre-router compat)", pre(CAM, SHOT), False))

    rc, _, _ = run(post(JS, {"text": PROBE_TEXT},
                        {"content": [{"type": "text",
                                      "text": "{\n  \"visibilityState\": \"hidden\",\n  \"hidden\": true\n}"}]}))
    r.append(check("05 PostToolUse hidden result -> marker 'hidden'",
                   rc == 0 and marker_state() == "hidden"))
    r.append(case("06 screenshot on 'hidden' -> deny WITH route",
                  pre(CAM, SHOT), True,
                  ["playwright screenshot", "SendUserFile", "re-run",
                   "ui-probe.mjs", "ui_verify_guard", "report_fp.py"]))
    r.append(case("07 cross-session isolation -> deny (probe-first)",
                  pre(CAM, SHOT, session="synthtest-B"), True))

    rc, _, _ = run(post(JS, {"text": PROBE_TEXT},
                        {"content": [{"type": "text",
                                      "text": "{ \"visibilityState\": \"visible\", \"hidden\": false }"}]}))
    r.append(check("08 PostToolUse visible result -> marker 'visible'",
                   rc == 0 and marker_state() == "visible"))
    r.append(case("09 screenshot on 'visible' -> allow (discriminator lives)",
                  pre(CAM, SHOT), False))

    echo = ("Executed: (async () => ({ visibilityState: document.visibilityState,\n"
            "  hidden: document.hidden }))()\nResult: { \"visibilityState\": \"visible\", \"hidden\": false }")
    rc, _, _ = run(post(JS, {"text": PROBE_TEXT}, echo))
    r.append(check("10 code echo in response not misread (last quoted value wins)",
                   rc == 0 and marker_state() == "visible"))

    rc, _, _ = run(post(JS, {"text": PROBE_TEXT}, {"content": "no state words here"}))
    r.append(check("11 unparseable response -> marker 'unknown'",
                   rc == 0 and marker_state() == "unknown"))
    r.append(case("12 screenshot on 'unknown' after bad parse -> allow", pre(CAM, SHOT), False))

    MARKER.write_text(str(time.time()), encoding="utf-8")
    r.append(case("13 legacy float marker -> allow (compat)", pre(CAM, SHOT), False))
    MARKER.write_text(json.dumps({"ts": time.time() - 9999, "state": "visible"}),
                      encoding="utf-8")
    r.append(case("14 expired marker -> deny (probe-first)", pre(CAM, SHOT), True))

    r.append(case("15 getComputedStyle unsettled -> deny (L-010)",
                  pre(JS, {"text": "return getComputedStyle(document.body).color"}), True))
    r.append(case("16 settle token -> allow",
                  pre(JS, {"text": "document.body.getAnimations({subtree:true}).forEach(a=>a.finish()); return getComputedStyle(document.body).color"}), False))
    r.append(case("17 intentional-midflight escape hatch -> allow",
                  pre(JS, {"text": "/* intentional-midflight */ return getComputedStyle(document.body).color"}), False))
    r.append(case("18 non-screenshot computer action -> allow",
                  pre(CAM, {"action": "left_click", "coordinate": [1, 1]}), False))

    rc, denied, _ = run(None, raw="not json{")
    r.append(check("19 malformed stdin -> fail-open", rc == 0 and not denied))

    # Class closure over the probe result (AP-62). The guard enumerates exactly
    # two states in STATE_RE -- `hidden|visible` -- and routes on them. A probe
    # that comes back with a third value matches neither, and both folds are
    # plausible-looking and wrong: fold to "visible" and a dead pane silently
    # unlocks the screenshot, fold to "hidden" and a live pane is routed
    # out-of-process forever. The declared degradation is the docstring's
    # "every parse failure leaves state 'unknown'" -> pre-router behaviour. The
    # marker is set to "visible" first so the assertion cannot pass by inertia:
    # cases 11-14 left an unrelated state behind.
    run(post(JS, {"text": PROBE_TEXT},
             {"content": [{"type": "text", "text": "{ \"visibilityState\": \"visible\" }"}]}))
    rc, _, _ = run(post(JS, {"text": PROBE_TEXT},
                        {"content": [{"type": "text",
                                      "text": "{ \"visibilityState\": \"prerender\" }"}]}))
    r.append(check("20 undetermined probe result (a third visibilityState value) -> "
                   "marker 'unknown', never folded to visible/hidden",
                   rc == 0 and marker_state() == "unknown"))

    # Unclassifiable SHAPE (AP-62): stdin that parses but is not a payload
    # object. Case 19 never reaches main()'s `not isinstance(payload, dict)`
    # guard -- its stdin fails json.load first. These parse, so without the
    # guard `payload.get` raises (rc 1, traceback). Docstring: "Fail-open by
    # design". Asserted: rc 0, nothing on stdout, no receipt row written.
    receipts = Path(_ENV["CLAUDE_TELEMETRY_DIR"]) / "ui-verify-guard.jsonl"
    for raw in ("[]", "null", json.dumps("mcp__Claude_Browser__computer")):
        before = receipts.stat().st_size if receipts.exists() else -1
        p = subprocess.run([PY, str(HOOK)], input=raw, capture_output=True,
                           text=True, timeout=15, env=_ENV)
        after = receipts.stat().st_size if receipts.exists() else -1
        r.append(check(f"21 unclassifiable payload {raw!r} -> fail-open "
                       f"(rc {p.returncode}, receipts {before} -> {after})",
                       p.returncode == 0 and not p.stdout.strip()
                       and before == after))

    # Unclassifiable tool_input (AP-62, one level in): a dict payload whose
    # tool_input is a truthy non-object. `or {}` does not catch it, so without
    # main()'s tool_input guard both handlers call `tool_input.get` on a list
    # or str and raise (rc 1, AttributeError) -- measured 2026-09-23 on all
    # three payloads below. Same assertions as case 21.
    for payload in (
            {"tool_name": CAM, "tool_input": ["screenshot"], "session_id": "zz"},
            {"tool_name": JS, "tool_input": "getComputedStyle", "session_id": "zz"},
            {"hook_event_name": "PostToolUse", "tool_name": JS,
             "tool_input": ["x"], "session_id": "zz"}):
        before = receipts.stat().st_size if receipts.exists() else -1
        p = subprocess.run([PY, str(HOOK)], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=15, env=_ENV)
        after = receipts.stat().st_size if receipts.exists() else -1
        r.append(check(f"22 unclassifiable tool_input {payload['tool_input']!r} "
                       f"({payload.get('hook_event_name', 'PreToolUse')}) -> fail-open "
                       f"(rc {p.returncode}, receipts {before} -> {after})",
                       p.returncode == 0 and not p.stdout.strip()
                       and before == after))

    for s in (SESSION, "synthtest-B"):
        p = MARKER.parent / f"{s}.probe"
        if p.exists():
            p.unlink()
    n = sum(1 for x in r if x)
    print(f"\n{n}/{len(r)} passed")
    sys.exit(0 if all(r) else 1)

if __name__ == "__main__":
    main()
