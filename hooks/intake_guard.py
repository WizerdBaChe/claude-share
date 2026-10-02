r"""PreToolUse DENY guard for the lesson intake store (`ops/lessons/`) and its
generated index (`ops/lessons.md`).

STATUS: LIVE since 2026-09-07 (claude-config Phase 23, closeout-capture R4 M2).
Implements design S-6 / INV-9 of
the closeout-capture R3 design note; the build contract is that round's
PSM, §3.2. The rule it enforces
is INV-2: an intake record is born once through `intake.py add` and is never
rewritten afterwards — later facts are appended as `## Events` lines by
`intake.py event`, and the index is re-rendered by `intake.py render`. Nothing
else may write those paths. A denial is the rule working: fix the call (use the
CLI), never the hook.

SEVERITY: DENY (a hard mechanism; the consumer is the tool call itself, not a
reader). Fail-OPEN on every internal error path (unparsable stdin, odd payload
shapes, any exception): exit 0 with empty stdout, and a best-effort telemetry
row `decision: error` so the failure is visible to the sweep — but a crashing
guard can never block an unrelated write.

Registration: settings.json PreToolUse, matcher `Write|Edit|Bash|PowerShell`
(TOOL_NAMES below is the second gate so a widened matcher cannot make it act
on other tools).

WHAT IS DENIED
  Write / Edit  — `file_path` (resolved against the payload `cwd` when
                  relative, `\` → `/`, case-insensitive on this NTFS tree) is
                  under `<home>/ops/lessons/` or equals `<home>/ops/lessons.md`.
  Bash / PowerShell — the command text names a lessons path
                  (`ops[\/]lessons(\.md|[\/])`) in a WRITE position:
                    * a redirect / tee / Out-File / Set-Content / Add-Content
                      whose TARGET is a lessons path
                    * `sed -i`, `rm`, `mv`, `Remove-Item`, `Move-Item`,
                      `Rename-Item`, `Copy-Item -Destination`, `cp ... <lessons>`
                      with a lessons path on the line
                    * `python - <<` (an inline script) with a lessons path on
                      the line AND a write verb in the text (write_text /
                      write_bytes / .write( / open(…,'w'|'a'|'x') / unlink /
                      os.remove|rename|replace / shutil / rmtree) — narrowed
                      2026-09-22, see FALSE-POSITIVE LOG
                  NEVER denied: a command containing `closeout-intake/intake.py`
                  (or `closeout-intake\intake.py`) — that is the tool itself.
  Everything else passes silently (reads, greps, `git show`, a redirect whose
  target is elsewhere).

KNOWN RESIDUALS (design G-2, accepted and labelled): a heredoc or a script that
composes the path from a variable (`p=ops/lessons; echo x >> $p/L-1.md`) is
not matched here; `intake.py check --against HEAD` (integrity sweep) is the
second line and reports any such edit as an INV-2 violation.

TELEMETRY: `telemetry/intake-guard.jsonl` (override: INTAKE_GUARD_LOG — the
controls harness points it at a temp file so a test run never touches the real
log). One row per DENY or ERROR only — allowed calls are not logged (every
Bash call in every session would otherwise land here):
  {ts, session, tool, path_or_cmd (first 200 chars), decision}

FALSE-POSITIVE LOG:
- 2026-09-09, 3 observed (telemetry/hook-false-positives.jsonl, two sessions): a read-only line-ending count in an inline script that OPENED the
  index in `rb`; and twice a write whose real target was another file
  (ops/rule-registry.md, ops/references/uat.md) while the command text merely
  QUOTED the index path in a payload. Not narrowed at the time (no log existed).
- 2026-09-22, 2 more observed (feedback pool review round 1):
  a probe whose printf payload contained the heredoc marker and the index path,
  and the `report_fp.py --why` call describing it — the misfire report was denied
  by the rule it reported, the same shape dangerous_command_guard logged on
  09-22. Loosened at 5 observed: the inline-script rule now also requires a
  write verb in the script text (WRITE_FORMS[2]); the redirect and destructive
  rules are unchanged. Regression: C-93c/C-93d (the observed shapes, MUST-PASS —
  both FAILED on the old rule when added first, so they discriminate) and
  C-92c/C-92d (inline scripts that write into the store, MUST-DENY). Known gap,
  labelled: a script that composes the write from names this list lacks
  (`io.FileIO`, `os.fdopen`, a subprocess) passes; `intake.py check --against
  HEAD` remains the second line (design G-2).

Proof-of-life: `python tools/closeout-intake/controls.py` cases C-90..C-93
(positive: Write to ops/lessons/L-999.md and `echo x >> ops/lessons/L-011.md`
are denied; negative: a scratchpad Write and an `intake.py add` command pass;
C-90c is the discriminator — a path of the SAME SHAPE under another root must
pass, or the two positives would look identical under a guard that matched the
suffix instead of the resolved store).

TELEMETRY CAVEAT, measured 2026-09-09. Until that date the controls did not pin
CLAUDE_CONFIG_DIR, so every run appended its four synthetic deny receipts to the
LIVE `telemetry/intake-guard.jsonl` — 724 bytes a run since 2026-09-07, and
about 100 of the file's 137 rows are those fixtures. They are recognisable by
target: `ops/lessons/L-999.md`, `echo x >> ops/lessons/L-011.md`, and
`Add-Content ops\lessons.md 'x'`. Anything reading this file as a DENY
denominator (`tools/hook-deny-lint/report_fp.py` computes a misfire rate against
it) must exclude them or it is dividing by mostly test data. The leak itself is
closed and C-90t now fails if it reopens; the rows already written are left in
place rather than edited out, because a telemetry file that gets hand-corrected
is worth less than one with a documented flaw.
review-when: the store moves (STORE / INDEX below and in intake.py must agree),
or a second record kind lands in another directory.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
STORE_DIR = CLAUDE_DIR / "ops" / "lessons"
INDEX_FILE = CLAUDE_DIR / "ops" / "lessons.md"
# Precedence: INTAKE_GUARD_LOG (per-hook override) > CLAUDE_TELEMETRY_DIR
# (suite redirect; production never sets it) > default.
LOG_PATH = Path(os.environ.get("INTAKE_GUARD_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "intake-guard.jsonl"))

TOOL_NAMES = ("Write", "Edit", "Bash", "PowerShell")
FILE_TOOLS = ("Write", "Edit")
SHELL_TOOLS = ("Bash", "PowerShell")

REASON = ("Write denied by intake_guard, a local PreToolUse hook (not file or "
          "page content). ops/lessons/ and ops/lessons.md are tool-owned: an "
          "intake record is born once and never rewritten, and the index is "
          "generated from the store. Use "
          "`python tools/closeout-intake/intake.py add --from <draft>` for a new "
          "lesson, `intake.py event L-nnn --kind recurrence|fold|supersede|retract` "
          "for a later fact, `intake.py render` for the index.")

# A lessons path token: the store dir (with either separator) or the index file.
_LESSONS = r"ops[\\/]lessons(?:\.md\b|[\\/])"
# One shell "word" that may carry the path (quotes allowed, no separators).
_WORD = r"[\"']?[^\s\"'|;&<>]*"
_TARGET = _WORD + _LESSONS

WRITE_FORMS = [
    # redirect / tee / PowerShell file-writing cmdlets whose TARGET is a lessons path
    re.compile(r"(?:>>?|\btee\b(?:\s+-a)?|\bOut-File\b(?:\s+-\w+)*|"
               r"\b(?:Set|Add)-Content\b(?:\s+-(?:Literal)?Path)?)\s*" + _TARGET, re.I),
    # in-place / destructive commands with a lessons path anywhere on the line
    re.compile(r"\b(?:sed\s+-i|rm|mv|Remove-Item|Move-Item|Rename-Item|Copy-Item|cp)\b.*" + _LESSONS, re.I | re.S),
    # inline python script fed by heredoc, naming a lessons path AND carrying a write verb
    # (2026-09-22 narrowing, FALSE-POSITIVE LOG: 5 observed read-only or merely-quoting commands)
    re.compile(r"\bpython\d?(?:\.exe)?\s+-\s*<<(?=.*(?:write_text|write_bytes|\.write\(|open\([^)]*['\"][wax]"
               r"|\bunlink\b|os\.(?:remove|rename|replace)|shutil\.|rmtree|\.rename\()).*" + _LESSONS, re.I | re.S),
]
ALLOW = re.compile(r"closeout-intake[\\/]intake\.py", re.I)


def _norm(p: str) -> str:
    return os.path.normcase(os.path.normpath(str(p))).replace("\\", "/")


def file_path_denied(file_path: str, cwd: str) -> bool:
    p = file_path
    if not os.path.isabs(p):
        p = os.path.join(cwd or os.getcwd(), p)
    n = _norm(p)
    store = _norm(STORE_DIR).rstrip("/") + "/"
    return n == _norm(INDEX_FILE) or n.startswith(store)


def command_denied(cmd: str) -> bool:
    if ALLOW.search(cmd):
        return False
    if not re.search(_LESSONS, cmd, re.I):
        return False
    return any(rx.search(cmd) for rx in WRITE_FORMS)


def log_row(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def decide(payload: dict) -> tuple:
    """-> (decision, subject) with decision in {allow, deny}. Pure; never raises on
    the documented payload shapes, and any other shape is `allow`."""
    tool = str(payload.get("tool_name", ""))
    ti = payload.get("tool_input")
    if tool not in TOOL_NAMES or not isinstance(ti, dict):
        return "allow", ""
    if tool in FILE_TOOLS:
        fp = ti.get("file_path")
        if not isinstance(fp, str) or not fp:
            return "allow", ""
        return ("deny" if file_path_denied(fp, str(payload.get("cwd") or "")) else "allow"), fp
    cmd = ti.get("command")
    if not isinstance(cmd, str) or not cmd:
        return "allow", ""
    return ("deny" if command_denied(cmd) else "allow"), cmd


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    session = str(payload.get("session_id") or "") if isinstance(payload, dict) else ""
    try:
        decision, subject = decide(payload if isinstance(payload, dict) else {})
        if decision == "deny":
            log_row({"ts": int(time.time()), "session": session,
                     "tool": str(payload.get("tool_name", "")),
                     "path_or_cmd": subject[:200], "decision": "deny"})
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON
                + _receipt("intake_guard", target=subject[:200])
                + _fp("intake_guard")}}))
    except SystemExit:
        raise
    except Exception as e:                      # fail-open, but visible
        log_row({"ts": int(time.time()), "session": session,
                 "tool": str(payload.get("tool_name", "")) if isinstance(payload, dict) else "",
                 "path_or_cmd": "", "decision": "error", "error": repr(e)[:200]})
    sys.exit(0)


if __name__ == "__main__":
    main()
