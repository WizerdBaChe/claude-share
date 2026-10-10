r"""PreToolUse guard: deterministic deny-list for destructive shell commands.

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
(80 cases as of 2026-09-22, printed by the suite: 38 must-deny / 33 must-pass /
3 undetermined + 3 determinable twins / fail-open / coverage / isolation). The
coverage case reads this file's own RULES list, so a shape added here without a
specimen there fails the suite rather than shipping unmeasured (PH-11 / AP-61).

OVER-MATCH, MEASURED 2026-09-08 (the machine-state half OBSERVED 4 times on
2026-09-22 and narrowed -- FALSE-POSITIVE LOG; the rm -rf half still 0): the patterns match inside
quoted strings, so a command that merely NAMES a shape is denied — measured on
`git commit -m "... rm -rf / ..."` and `echo 'the shutdown procedure ...'`. Both
are pinned in the suite's OVERMATCH block, which reports them and counts them in
no verdict. Nothing was narrowed: the loosening trigger for this guard is an
OBSERVED false-positive count (rules/hook-deny-message.md, FALSE-POSITIVE LOG),
and a synthetic hit is not one. When a real session hits one, the shape is
already named and those two cases are the regression floor for the narrowing.

FALSE-POSITIVE LOG:
- 2026-10-03 fold (feedback pool, user ruling 走建議), 2 observed:
  (a) 2026-09-27 ts 1790524668: `git push ... --tags && git branch -f ...` denied as
  a forced push — the push rule's `.*` crossed the `&&`. A matching DEFECT, not a
  loosening: the push rule now reads one statement. Regression: that chain is
  MUST-PASS; `git push origin main -f && echo ok` and `git push -f; git status`
  stay MUST-DENY. (b) 2026-10-02 ts 1790946837: `rm -rf` as prose inside a heredoc
  body piped to pb.py — the FIRST real hit of the pinned rm -rf OVERMATCH case.
  NOT narrowed (1 observed; this rule's trigger is 3); a deny is the safe side.
  (c) 2026-10-03, during this very fold: a Python heredoc holding the push-rule
  test strings was denied — the same quoted/heredoc-body class as (b), other rule.
  Class count 2 (b+c); at 3 the narrowing is heredoc-body exclusion for every rule.
- 2026-09-22, 4 observed, one session (receipt rows c52979, 858980, 8f6b91,
  87d0a1): the machine-state rule denied read-only work that NAMED the word — two
  grep patterns (`...\|shutdown\|...`), a report_fp.py `--why` text, and a Python
  heredoc calling `srv.shutdown()` on an HTTP server. The misfire report itself was
  denied by the same rule, so the exit could not record it. Loosened: that ONE rule
  now matches only in command position (see RULES); the other rules and the
  quoted-`rm -rf` OVERMATCH case are unchanged (not observed). Regression: the four
  shapes are MUST-PASS in the suite, and chained / launched / quoted-command spellings
  of every machine-state verb are MUST-DENY. Known gap, labelled: a verb reached
  through `ssh host shutdown` or an alias is not in command position and passes to
  the normal permission flow.
- 2026-09-11, 1 observed, another session (telemetry/hook-false-positives.jsonl
  ts 1789074447), surfaced by the feedback pool's review round 1 on 2026-09-22: a
  multi-statement PowerShell block whose destructive target was `$SB` under %TEMP%
  was denied because an absolute path on a non-system drive appeared in a LATER read-only
  statement (`Get-ChildItem`) of the same block — attribution is per command text,
  not per statement. Different rule from the 09-22 four (path-scope, not
  machine-state). NOT narrowed: 1 observed; the loosening trigger for this shape is
  3. If it recurs, the narrowing is per-statement attribution (split on `;`/newline
  before matching a path rule), with this block as the MUST-PASS regression.

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
    # One STATEMENT only (2026-10-03, FALSE-POSITIVE LOG): `.*` crossed `&&` and read
    # the `-f` of a later `git branch -f` as a forced push.
    ("any", re.compile(r"\bgit\s+push\b(?![^|;&\n]*--force-with-lease)[^|;&\n]*(--force\b|\s-f\b)", re.I),
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
    # COMMAND POSITION only (narrowed 2026-09-22, FALSE-POSITIVE LOG below): the verb must
    # start a line, follow an unescaped separator (; & | ( { $( backtick), or follow a
    # launcher (sudo/start/exec/xargs/call, -c, /c, /k, -Command), optionally opening a
    # quote. A grep pattern `\|shutdown`, a method call `srv.shutdown()` and prose naming
    # the word no longer match.
    ("any", re.compile(r"(?:^|(?<!\\)[;&|({`]|\$\(|\b(?:sudo|start|exec|xargs|call)\s+"
                       r"|(?:^|\s)(?:-c|/c|/k|-Command)\s+)\s*[\"']?"
                       r"(shutdown(\.exe)?|Restart-Computer|Stop-Computer|Format-Volume"
                       r"|Clear-Disk|diskpart(\.exe)?|mkfs(\.\w+)?)\b", re.I | re.M),
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
