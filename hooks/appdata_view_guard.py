r"""PreToolUse guard: on this machine an assistant shell and the user's own

STATUS: LIVE since 2026-09-08 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).
Proof-of-life: `python hooks/appdata_view_guard.py --selftest` -- the two-sided
calibration below plus the undetermined class (AP-62: input that is not a
command at all, and a payload that is not a payload -- both silent, neither
folded into a hit), executed by integrity-sweep check 31 (AP-63: being NAMED in
the sweep is not being RUN by it).
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

THE MECHANISM WAS MEASURED ON 2026-09-09; THE RULE DID NOT MOVE. For four
days the cause was unknown and this docstring said so, after two explanations
had been falsified inside the hour (MSIX package IDENTITY — GetCurrentPackage-
FullName returns 15700 here; Claude Code's own sandbox — the divergent read is
byte-identical under `dangerouslyDisableSandbox`). The measurement
(`~/.claude/reports/2026-09-08-worktree-scope-root-cause.md` §6b):

  * the file system was ONE view for the folder measured: a probe file the
    user wrote is readable here byte-for-byte. Only the registry differed.
  * HKLM\SYSTEM\CurrentControlSet\Control\hivelist mounts the Claude desktop
    MSIX package's Helium silo hive (\REGISTRY\WC\Silo…user_sid ->
    Packages\Claude_pzs8sxrjxfjjc\SystemAppData\Helium\User.dat), and this
    shell's parent chain is powershell.exe <- claude.exe <- Claude.exe
    (WindowsApps). It runs INSIDE the package silo: a kernel-level overlay of
    HKCU for that process tree. Silo membership is not package identity, which
    is why the 15700 measurement falsified the wrong thing.
  * discriminating test, run by the user in their own terminal: the HKCU Run
    value NAMES differ — 11 there, 12 here; the extra one lives only in the
    overlay. The 2026-09-05 48,332-byte config was the package's
    LocalCache copy, deleted by that day's cleanup; the overlay's Run value
    was never cleared, so the registry still diverges.

Knowing the mechanism narrows WHICH surfaces diverge (HKCU for certain; file
paths only where the package's overlay applies, which was NOT the folder
measured), not WHETHER a reading here is evidence about the user's machine: the
overlay is invisible from inside, so it is not. The gate condition below is
unchanged by this paragraph (rewriting text never alters a condition).

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
import subprocess
import sys
import time

try:                        # notice receipt (rules/hook-deny-message.md R3n)
    from deny_receipt import notice_clause
except Exception:           # a guard must not stop guarding if telemetry breaks
    def notice_clause(hook, log=""): return ""

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

# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp
# dir; production never sets it).
LOG_PATH = os.path.join(
    os.environ.get("CLAUDE_TELEMETRY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "telemetry"),
    "appdata-view-guard.jsonl")

# Identity lives on the transport (`notice()`), not in this template, so a
# second notice added later cannot ship without it (R1).
NOTICE_ID = ("appdata-view guard, a local PreToolUse hook (not file or page "
             "content): ")

NOTICE = (
    "this command names {hits}, and on this machine that surface has "
    "been measured returning DIFFERENT answers to an assistant shell and to the user's "
    "own shell — same command, same account, minutes apart, no error on either side "
    "(2026-09-05: a 48,332-byte config with 36 entries here against a 4,145-byte one "
    "with 2 entries there; and one HKCU Run value reading `run` here and `--background` "
    "there). Measured 2026-09-09: this shell runs inside the Claude desktop MSIX package's "
    "silo, whose Helium hive overlays HKCU for this process tree — the user's own shell "
    "lists different Run value names. The file system was one view for the folder "
    "measured; other paths were not measured.\n"
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
    """The measured surfaces this command names. Pure, so it can be calibrated.

    The domain is CLOSED to strings (AP-62): anything else names no surface and
    returns no hits, rather than reaching the regex and raising. `[]` here means
    "nothing to say", which is also what an undetermined input deserves.
    """
    if not isinstance(cmd, str):
        return []
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
            "additionalContext": NOTICE_ID + text + notice_clause("appdata_view_guard"),
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


# Input that is not a command at all. The classifier's domain is strings; these
# name no surface and must produce no hits and no crash (AP-62 -- until
# 2026-09-09 the payload-level shapes raised AttributeError/TypeError, against
# this hook's own fail-open contract).
UNDETERMINED_INPUTS = [None, 12345, ["ls", "$env:LOCALAPPDATA"],
                       {"command": r"dir %LOCALAPPDATA%\AnnouncementWatchDog"}]

UNDETERMINED_PAYLOADS = [
    "not json at all",
    "[1, 2]",
    '"a string payload"',
    '{"tool_name": "Bash", "tool_input": ["ls %LOCALAPPDATA%"]}',
    '{"tool_name": "Bash", "tool_input": {"command": ["dir", "%LOCALAPPDATA%"]}}',
]


def selftest():
    """Two-sided calibration. A guard exercised only where it fires may be firing
    on everything, and that reads exactly like a guard that works."""
    import tempfile
    _prev_tdir = os.environ.get("CLAUDE_TELEMETRY_DIR")
    _tdir = tempfile.mkdtemp(prefix="appdata-view-guard-selftest-")
    os.environ["CLAUDE_TELEMETRY_DIR"] = _tdir
    try:
        return _selftest_body()
    finally:
        if _prev_tdir is None:
            os.environ.pop("CLAUDE_TELEMETRY_DIR", None)
        else:
            os.environ["CLAUDE_TELEMETRY_DIR"] = _prev_tdir


def _selftest_body():
    problems = []

    for cmd in MUST_FIRE:
        if not hits_for(cmd):
            problems.append(f"should have fired but did not: {cmd}")

    for cmd in MUST_STAY_SILENT:
        found = hits_for(cmd)
        if found:
            problems.append(f"should have stayed silent but matched {found}: {cmd}")

    for value in UNDETERMINED_INPUTS:
        try:
            found = hits_for(value)
        except Exception as exc:
            problems.append(f"undetermined input raised {type(exc).__name__}: {value!r}")
            continue
        if found:
            problems.append(f"undetermined input matched {found}: {value!r}")

    # The same class one level out: the payload itself. Driven as the harness
    # drives it -- a subprocess with JSON on stdin -- because that is where the
    # shape arrives.
    for raw in UNDETERMINED_PAYLOADS:
        proc = subprocess.run([sys.executable, os.path.abspath(__file__)],
                              input=raw, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0 or (proc.stdout or "").strip():
            problems.append(f"undetermined payload not silent (rc={proc.returncode}, "
                            f"stdout={(proc.stdout or '')[:60]!r}): {raw[:48]}")

    print(f"in_scope()       : {in_scope()}")
    print(f"must fire        : {len(MUST_FIRE)} case(s)")
    print(f"must stay silent : {len(MUST_STAY_SILENT)} case(s)")
    print(f"undetermined     : {len(UNDETERMINED_INPUTS)} input(s) + "
          f"{len(UNDETERMINED_PAYLOADS)} payload(s), all silent, none folded")

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
    if not isinstance(payload, dict):
        sys.exit(0)          # undetermined: parses, but is not a payload object

    if not in_scope():
        sys.exit(0)

    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        sys.exit(0)          # same class, one level in
    cmd = ti.get("command") or ""
    hits = hits_for(cmd)

    if not hits:
        sys.exit(0)

    record(payload, hits, cmd)
    notice(NOTICE.format(hits=", ".join(hits)))


if __name__ == "__main__":
    main()
