#!/usr/bin/env python3
"""CLI auth emitter: is the `claude` CLI logged in? (hmi-report/1, class=reconcile)

STATUS: LIVE since 2026-10-02 (user ruling: "CLI 也重新登入了，這點幫我掛監控，有時候會自己跳掉").

Point:
  platform.cli-auth   `claude auth status --json` -> loggedIn true = pass; false = FAIL (every
                      `claude -p` route, plugin test harness and headless probe then fails with
                      "OAuth session expired" while the Desktop app keeps working, so nothing
                      else surfaces it); CLI missing / timeout / unparseable = not ran (skip),
                      never a verdict.

Severity: FAIL, not warn — the consumer is a hard downstream tool (any headless `claude`
call), not a reader deciding whether to look (gate-severity-by-consumer). The remedy is the
user's own action (`claude login`); this emitter never attempts it and never reads a credential
file (connector-secret boundary) — it asks the CLI, which reports a boolean.

Read-only. Proof-of-life: `python tools/system-hmi/emitters/cli_auth.py --selftest`
(parses a planted logged-in and a planted logged-out status; the live call is a smoke).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time

POINT = "platform.cli-auth"
ALIAS = "CLI 登入狀態"
TIMEOUT_S = 25


def _point(state, findings, ran=True, skip=None, remedy=None):
    return {"id": POINT, "alias": ALIAS, "class": "reconcile", "ran": ran, "skip_reason": skip,
            "state": state, "quality": "good", "findings": findings, "remedy": remedy}


def parse_status(text: str):
    """-> (loggedIn: bool, detail: dict) or None when the text is not a status document."""
    try:
        start = text.index("{")
        doc = json.loads(text[start:])
    except Exception:
        return None
    if not isinstance(doc, dict) or "loggedIn" not in doc:
        return None
    return bool(doc.get("loggedIn")), {k: doc.get(k) for k in ("authMethod", "apiProvider", "email") if k in doc}


def read_status():
    """-> ('ok', loggedIn, detail) | ('skip', reason, None)."""
    exe = shutil.which("claude")
    if not exe:
        return "skip", "claude-cli-not-on-path", None
    try:
        r = subprocess.run([exe, "auth", "status"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return "skip", f"claude-auth-status-timeout-{TIMEOUT_S}s", None
    except OSError as e:
        return "skip", f"claude-auth-status-oserror:{e.__class__.__name__}", None
    parsed = parse_status(r.stdout or "") or parse_status(r.stderr or "")
    if parsed is None:
        return "skip", "claude-auth-status-unparseable", None
    return "ok", parsed[0], parsed[1]


def build(config=None):
    kind, a, detail = read_status()
    if kind == "skip":
        points = [_point(None, [], ran=False, skip=a)]
    elif a:
        points = [_point("pass", [{"severity": "info", "label": "logged in",
                                   "text": ", ".join(f"{k}={v}" for k, v in (detail or {}).items() if k != "email") or "claude.ai"}])]
    else:
        points = [_point("fail", [{"severity": "fail", "label": "claude CLI logged out",
                                   "text": "every headless `claude` call (claude -p, claude plugin test, probes) fails with 'OAuth session expired'"}],
                         remedy="claude login   (the user runs it in a terminal; never automated)")]
    return {"protocol": "hmi-report/1", "source": "cli-auth",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "points": points}


def selftest() -> int:
    ok = True
    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("PASS " if cond else "FAIL ") + name)
    check("planted logged-in parses true", parse_status('{"loggedIn": true, "authMethod": "claude.ai"}') == (True, {"authMethod": "claude.ai"}))
    check("planted logged-out parses false", parse_status('note\n{"loggedIn": false}')[0] is False)
    check("garbage is None, never a verdict", parse_status("Failed to authenticate") is None)
    check("a document without loggedIn is None", parse_status('{"version": 1}') is None)
    doc = build()
    p = doc["points"][0]
    check("live smoke: one point, state in {pass, fail, None}", p["id"] == POINT and p["state"] in ("pass", "fail", None))
    print(f"live: state={p['state']} ran={p['ran']} skip={p['skip_reason']}")
    print("ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(build(), ensure_ascii=False))
