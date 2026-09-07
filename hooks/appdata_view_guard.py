r"""PreToolUse guard: on this machine an assistant shell and the user's own
shell can return DIFFERENT answers for the same %LOCALAPPDATA% path and the
same HKCU value, with no error on either side.

Copy this file into ~/.claude/hooks/ and mount it in settings.json (see this
repo's hooks/README.md) — no separate installer script ships with it.

WHAT WAS MEASURED (2026-09-05, AnnouncementWatchDog, D-057). Same command,
minutes apart, one machine, one account:

    assistant shell   config.json 48,332 B / 36 targets / log 653,870 B
                      HKCU …\Run\AnnouncementWatchDog = "…\watchdog.exe" run
    user's shell      config.json  4,145 B /  2 targets / log  62,654 B
                      HKCU …\Run\AnnouncementWatchDog = "…\watchdog.exe" --background

The mtimes were not consistent with one file changing (48,332 B was stamped
09-05 14:46; 4,145 B was stamped 09-04 13:47 — a file does not go backwards),
so these are two different objects reached by one path. Nothing in either
output said which one it was. A cleanup plan written from the first reading
deleted what it took to be a duplicate; it was the only copy of 36 configured
boards.

THE CAUSE IS UNKNOWN, AND THIS GUARD DELIBERATELY DOES NOT NAME ONE. Two
explanations were proposed and both were falsified by measurement inside the
hour:

  * MSIX per-package virtualization — GetCurrentPackageFullName returns 15700
    (APPMODEL_ERROR_NO_PACKAGE): the assistant shell has no package identity.
  * Claude Code's own sandbox — the divergent HKCU read is byte-identical with
    `dangerouslyDisableSandbox`, same account, same SID (…-1001).

Guessing a third time is what the rule below exists to stop. The observation is
reproducible and is enough on its own: a reading taken here is not evidence
about the user's machine.

WHY A HOOK AND NOT A CLAUDE.md LINE (L-011). The project this happened in
already carried the rule — D-055 and invariant SI-16 are about path resolution
differing by who asks, in the same repository, written by the same assistant a
few hours earlier — and the readings were still believed and still acted on.
A rule that fires on recall is not a mechanism when the wrong answer looks
completely ordinary. Whether a command NAMES one of these two surfaces is
decidable from the command string, at the moment it is issued, with no
judgment.

GATE AUTHORITY (global CLAUDE.md).

  DETERMINABLE — does this command name a surface on which divergence was
  measured? A property of the command string.

  NOT DETERMINABLE — whether this particular call is on the diverging side,
  and why. So this ANNOTATES and never denies: a deny would block the many
  legitimate uses (the scratchpad, node/NuGet caches, this hook's own
  telemetry), and the annotation already does the work — it says, in the same
  turn, that the number about to be read cannot be reported as the machine's
  state.

CALIBRATION (`--selftest`). Both sides, because a guard exercised only where it
fires may be firing on everything: six commands that must annotate, and six
that must stay silent — including AppData\Roaming, AppData\Local\Temp (the
scratchpad, which would otherwise fire on nearly every call), an explicit
AppData\Local\Packages path, and the override marker.
"""

import json
import os
import re
import sys
import time

MARKER = "[view-checked]"

# The two surfaces divergence was measured on, in the spellings the shells on
# this machine use. AppData\Roaming is deliberately absent: it may well be
# redirected too, but nothing has been measured there, and a guard that fires
# on everything is indistinguishable from noise. Two paths under AppData\Local
# are excluded for the same reason: \Packages is naming the container on
# purpose, and \Temp is where the session scratchpad lives.
SURFACES = (
    (re.compile(r"%LOCALAPPDATA%", re.I), "%LOCALAPPDATA%"),
    (re.compile(r"\$env:LOCALAPPDATA", re.I), "$env:LOCALAPPDATA"),
    (re.compile(r"\$\{?LOCALAPPDATA\}?", re.I), "$LOCALAPPDATA"),
    (re.compile(r"AppData[\\/]+Local(?![\\/]+(?:Packages|Temp))", re.I), r"AppData\Local"),
    (re.compile(r"HKCU:", re.I), "HKCU:"),
    (re.compile(r"HKEY_CURRENT_USER", re.I), "HKEY_CURRENT_USER"),
)

LOG_PATH = os.path.join(os.path.expanduser("~"), ".claude", "telemetry",
                        "appdata-view-guard.jsonl")

NOTICE = (
    "appdata-view guard: this command names {hits}, and on this machine that surface has "
    "been measured returning DIFFERENT answers to an assistant shell and to the user's "
    "own shell — same command, same account, minutes apart, no error on either side "
    "(2026-09-05: a 48,332-byte config with 36 entries here against a 4,145-byte one "
    "with 2 entries there; and one HKCU Run value reading `run` here and `--background` "
    "there). The cause is not known: MSIX package identity and the Claude Code sandbox "
    "were both proposed and both falsified by measurement.\n"
    "So whatever comes back is evidence about THIS view only. Do not report it as the "
    "state of the user's machine, and above all do not write a cleanup, deletion, "
    "migration or repair plan on it — have the user run the command in their own "
    "terminal and paste the output. A copy that looks like a stale duplicate from here "
    "may be the only copy there is: that mistake cost 36 configured boards (D-057).\n"
    "If you have already established which side you are reading, re-run with " + MARKER + "."
)


def in_scope():
    """Windows only. There is deliberately no cleverer test than this.

    The first version asked GetCurrentPackageFullName and stayed silent when the
    process came back unpackaged — and that probe answered "not packaged" while
    the divergence it exists to warn about was demonstrably present. An
    instrument that disagrees with the phenomenon must not be the thing that
    decides whether to speak.
    """
    return os.name == "nt"


def hits_for(cmd):
    """The measured surfaces this command names. Pure, so it can be calibrated."""
    if not cmd or MARKER in cmd:
        return []
    return [label for pattern, label in SURFACES if pattern.search(cmd)]


def record(payload, hits, cmd):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "session": payload.get("session_id", ""),
                "cwd": payload.get("cwd", ""),
                "verdict": "notice",
                "hits": hits,
                "command": cmd,
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def notice(text):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": text,
        }
    }))
    sys.exit(0)


MUST_FIRE = [
    r'Get-ChildItem "$env:LOCALAPPDATA\AnnouncementWatchDog"',
    r"dir %LOCALAPPDATA%\AnnouncementWatchDog",
    r'ls "C:\Users\<user>\AppData\Local\AnnouncementWatchDog"',
    r"Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'",
    r"reg query HKEY_CURRENT_USER\Software",
    r'cat "$LOCALAPPDATA/app/config.json"',
]

MUST_STAY_SILENT = [
    "git status --short",
    "grep -rn TODO src/",
    r'ls "$env:APPDATA\Microsoft"',
    r'ls "C:\Users\<user>\AppData\Roaming\npm"',
    r'ls "C:\Users\<user>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc"',
    r'cat "C:\Users\<user>\AppData\Local\Temp\claude\scratchpad\notes.txt"',
    r'ls "$env:LOCALAPPDATA\app" [view-checked]',
]


def selftest():
    """Two-sided calibration. A guard exercised only where it fires may be firing
    on everything, and that reads exactly like a guard that works."""
    problems = []

    for cmd in MUST_FIRE:
        if not hits_for(cmd):
            problems.append(f"should have fired but did not: {cmd}")

    for cmd in MUST_STAY_SILENT:
        found = hits_for(cmd)
        if found:
            problems.append(f"should have stayed silent but matched {found}: {cmd}")

    print(f"in_scope()       : {in_scope()}")
    print(f"must fire        : {len(MUST_FIRE)} case(s)")
    print(f"must stay silent : {len(MUST_STAY_SILENT)} case(s)")

    if problems:
        for p in problems:
            print("FAIL " + p)
        return 1

    print("PASS both sides")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())

    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if not in_scope():
        sys.exit(0)

    cmd = (payload.get("tool_input") or {}).get("command") or ""
    hits = hits_for(cmd)

    if not hits:
        sys.exit(0)

    record(payload, hits, cmd)
    notice(NOTICE.format(hits=", ".join(hits)))


if __name__ == "__main__":
    main()
