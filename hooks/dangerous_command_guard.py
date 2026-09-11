"""PreToolUse guard: deterministic deny-list for destructive shell commands.

STATUS: LIVE since 2026-07-29 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

Policy (owner: user, 2026-07-29): the permission allowlist was widened for
low-risk commands; this hook is the compensating control. It unconditionally
blocks command shapes whose damage is hard or impossible to reverse, regardless
of allowlist state. Everything it does not match falls through to the normal
permission flow (exit 0 = no opinion, NOT approval).

Scope: Bash and PowerShell tool calls. Checked shapes:
- recursive+force deletion (rm -rf / Remove-Item -Recurse -Force / rmdir /s)
  targeting absolute paths, home (~), parent traversal (..), bare . or *
  — relative in-project targets (e.g. node_modules) pass through to the
  normal prompt instead;
- history-destroying git: push --force (--force-with-lease passes),
  reset --hard, clean -f, whole-tree discard (checkout -- . / restore .);
- registry writes (reg add/delete, *-ItemProperty on HK*: hives);
- machine state: shutdown / Restart-Computer / Stop-Computer / Format-Volume /
  Clear-Disk / diskpart / mkfs / Set-ExecutionPolicy.

Per-instance escape hatch: the literal marker [user-approved-destructive]
inside the command string (e.g. appended as a comment). The orchestrator may
only add it after the user approved that specific command in conversation —
same contract as model_cap_guard's approval marker.

Temp roots (scratchpad/TEMP) are exempt from the deletion rules: recursive
deletes inside them are routine cleanup.

Proof-of-life: `python tools/dangerous-command-test/test_dangerous_command_guard.py`
(65 cases as of 2026-09-09, printed by the suite: 27 must-deny / 29 must-pass /
3 undetermined + 3 determinable twins / fail-open / coverage / isolation). The
coverage case reads this file's own RULES list, so a shape added here without a
specimen there fails the suite rather than shipping unmeasured (PH-11 / AP-61).

OVER-MATCH, MEASURED 2026-09-08, OBSERVED 0 TIMES: the patterns match inside
quoted strings, so a command that merely NAMES a shape is denied — measured on
`git commit -m "... rm -rf / ..."` and `echo 'the shutdown procedure ...'`. Both
are pinned in the suite's OVERMATCH block, which reports them and counts them in
no verdict. Nothing was narrowed: the loosening trigger for this guard is an
OBSERVED false-positive count (rules/hook-deny-message.md, FALSE-POSITIVE LOG),
and a synthetic hit is not one. When a real session hits one, the shape is
already named and those two cases are the regression floor for the narrowing.

review-when: RULES is an enumeration of command SHAPES, and an enumeration loses
to the first member nobody wrote down — none of the facts below is visible from
inside this repo. (a) A CLI whose destructive verb this list does not name enters
routine use here (`wsl --unregister`, `docker volume rm` / `system prune -af`,
`gh repo delete`, a cloud `... delete --yes`), or git adds/renames a whole-tree
discard spelling — the compensating control is only as wide as the allowlist it
compensates for. (b) The permission allowlist is NARROWED back — this hook exists
because it was widened on 2026-07-29; if the normal flow prompts on these
commands again, the unconditional deny changes from compensation to a second
gate, which is a rent question, not a correctness one. (c) The shell or platform
changes — the tool-scope column and half the patterns are shaped by cmd /
PowerShell / Git Bash on Windows (`Remove-Item -Recurse -Force`, `rmdir /s`, the
`HK*:` PSDrive prefixes); on another OS the same damage has different spellings.
(d) The session scratchpad or TEMP root moves off the shapes in
TEMP_ROOT_PATTERNS (`Users/<u>/AppData/Local/Temp`, `/tmp`, `$env:TEMP`) — the
exemption silently stops applying and routine cleanup starts being denied. (e) A
real session hits either pinned OVERMATCH case: the observed false-positive count
is this guard's loosening trigger, and those two cases are the regression floor.

Fail-open by design: any parse error exits 0 so a guard bug never blocks work.
"""
import json
import os
import re
import sys

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

APPROVAL_MARKER = "[user-approved-destructive]"

TEMP_ROOT_PATTERNS = [
    re.compile(r"^([A-Za-z]:)?[/\\]?Users[/\\][^/\\]+[/\\]AppData[/\\]Local[/\\]Temp\b", re.I),
    re.compile(r"^/tmp\b"),
    re.compile(r"^\$env:TE?MP\b", re.I),
]

# (tool-scope, compiled pattern, reason) — tool-scope: 'any', 'bash', 'ps'
RULES = [
    ("any", re.compile(r"\bgit\s+push\b(?!.*--force-with-lease).*(--force\b|\s-f\b)", re.I),
     "git push --force rewrites remote history; use --force-with-lease after user approval, or ask the user."),
    ("any", re.compile(r"\bgit\s+reset\s+--hard\b", re.I),
     "git reset --hard discards uncommitted work irrecoverably; prefer git stash, or get explicit user approval."),
    ("any", re.compile(r"\bgit\s+clean\s+-[a-z]*f", re.I),
     "git clean -f permanently deletes untracked files; list them first (git clean -n) and ask the user."),
    ("any", re.compile(r"\bgit\s+(checkout|restore)\s+(--\s+)?\.(\s|$)", re.I),
     "Whole-tree discard (checkout/restore .) erases all uncommitted changes; restore specific paths instead or ask the user."),
    ("any", re.compile(r"\breg\s+(add|delete)\b", re.I),
     "Direct registry modification is blocked; ask the user to run it themselves."),
    ("ps", re.compile(r"\b(Set|New|Remove)-ItemProperty\b[^|]*\bHK(LM|CU|CR|U|CC):", re.I),
     "Registry writes via *-ItemProperty are blocked; ask the user to run it themselves."),
    ("any", re.compile(r"\b(shutdown|Restart-Computer|Stop-Computer|Format-Volume|Clear-Disk|diskpart|mkfs(\.\w+)?)\b", re.I),
     "Machine-state / disk-formatting commands are blocked; ask the user."),
    ("ps", re.compile(r"\bSet-ExecutionPolicy\b", re.I),
     "Changing PowerShell execution policy is a system security setting; ask the user."),
]

RECURSIVE_RM = re.compile(
    r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*"
    r"|--recursive\s+--force|--force\s+--recursive)\b(?P<rest>[^|;&]*)", re.I)
PS_RECURSIVE_RM = re.compile(r"\b(Remove-Item|rmdir|rd|del)\b(?P<rest>[^|;&]*)", re.I)
PS_RECURSIVE_FLAGS = re.compile(r"(-Recurse\b|(^|\s)/s\b)", re.I)


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason + (
                f" Per-instance override: re-run with the marker {APPROVAL_MARKER} "
                "in the command ONLY after the user approved this exact command."
            ) + _receipt("dangerous_command_guard") + _fp("dangerous_command_guard"),
        }
    }))
    sys.exit(0)


def is_temp_path(tok: str) -> bool:
    t = tok.strip("'\"")
    return any(p.search(t) for p in TEMP_ROOT_PATTERNS)


def dangerous_delete_target(rest: str) -> str | None:
    """Return the offending token if a delete target is high-blast-radius."""
    for tok in rest.split():
        if tok.startswith("-") or tok.startswith("/") and len(tok) == 2:
            continue  # flags (incl. cmd-style /s /q)
        t = tok.strip("'\"")
        if not t:
            continue
        if is_temp_path(t):
            continue
        if ".." in t:
            return tok
        if t in (".", "./", "*", "./*", "~", "/"):
            return tok
        if t.startswith("~"):
            return tok
        if re.match(r"^[A-Za-z]:[/\\]", t) or t.startswith("/") or t.startswith("\\"):
            return tok
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)      # undetermined: parses, but is not a payload object (AP-62)

    tool = payload.get("tool_name", "")
    if tool not in ("Bash", "PowerShell"):
        sys.exit(0)
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        sys.exit(0)      # same class, one level in
    cmd = str(ti.get("command", ""))
    if not cmd or APPROVAL_MARKER in cmd:
        sys.exit(0)

    scope = "bash" if tool == "Bash" else "ps"
    for rule_scope, pat, reason in RULES:
        if rule_scope in ("any", scope) and pat.search(cmd):
            deny(f"Blocked by dangerous_command_guard, a local PreToolUse hook "
                 f"(not file or page content): {reason}")

    targets = []
    m = RECURSIVE_RM.search(cmd)
    if m:
        targets.append(m.group("rest"))
    m = PS_RECURSIVE_RM.search(cmd)
    if m and PS_RECURSIVE_FLAGS.search(m.group("rest")):
        targets.append(m.group("rest"))
    for rest in targets:
        bad = dangerous_delete_target(rest)
        if bad:
                deny(
                    "Blocked by dangerous_command_guard, a local PreToolUse hook "
                    "(not file or page content): recursive/forced delete "
                    f"targeting '{bad}' (absolute path, home, parent traversal, or "
                    "whole-directory glob). Deletes outside the scratchpad need "
                    "explicit user approval; consider moving to archive/ instead."
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
