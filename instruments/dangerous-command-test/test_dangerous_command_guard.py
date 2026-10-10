#!/usr/bin/env python3
r"""Two-sided calibration for hooks/dangerous_command_guard.py.

Run:  python tools/dangerous-command-test/test_dangerous_command_guard.py

This guard is the compensating control for a WIDENED permission allowlist
(owner ruling 2026-07-29): low-risk shell commands stopped prompting, so the
irreversible shapes need a gate that does not depend on the allowlist. That
makes both directions load-bearing:

  MUST-DENY  (positive control) — one specimen per shape the docstring names.
             If any passes, the compensation for the widened allowlist is gone
             and nothing prompts either.
  MUST-PASS  (negative control) — the near-misses: relative deletes, scratchpad
             cleanup, `--force-with-lease`, `git clean -n`, reads of the same
             registry hive. If any is denied, the guard is a tax on ordinary
             work and the next session learns to route around it.

VOCABULARY COVERAGE (L-044, `ops/lessons.md`): the third block asserts that
every entry in the hook's own RULES list, plus both delete matchers, is fired by
at least one MUST-DENY case. A rule added to the hook with no specimen here
fails this suite — that is the extension clause (PH-11 / AP-61), and it is why
the coverage check reads the hook's live RULES rather than a copy of the list.

UNDETERMINED is a third result class, ASSERTED and counted in no verdict
(AP-62). dangerous_delete_target() enumerates the target classes it rules on:
a flag, a temp root (exempt), `..` traversal, a bare `.` / `*` / `~` / `/`, a
home-relative path, a drive-letter or POSIX absolute path — and everything else
is "relative in-project target", the class it treats as safe. An UNEXPANDED
SHELL VARIABLE (`$PROJECT_ROOT`, `%APPDATA%\...`, `$ProjectRoot`) belongs to
none of them: its value does not exist at decision time, so the guard cannot
know whether it names `./build` or `/`. It is currently folded into the safe
class and the command falls through.

That fold is DECLARED, which is why these are specimens and not a defect report:
the hook's own words are "Everything it does not match falls through to the
normal permission flow (exit 0 = no opinion, NOT approval)" — downgrade-and-
forward, the permission prompt still stands behind it. So the assertion here is
NOT "these are safe". It is that the guard returns NO OPINION on them: rc 0 with
an empty stdout, which is a different event from an allow decision. Each ships
with its DETERMINABLE TWIN — the same command with the variable written out as
the path it most plausibly names — which must deny. The twin is what keeps the
pair honest: it proves the shape is one the guard rules on when it CAN, so the
no-opinion came from the undeterminable value and not from a hole in the matcher.

Not the same class as OVERMATCH below: overmatch is the guard RULING on a string
it should arguably ignore; undetermined is the guard unable to rule at all.
This shape is not hypothetical — the sibling branch_commit_guard logged it in
the field as FP-1 (2026-08-27), where an unexpanded `$LOCALAPPDATA` in a `cd`
argument resolved to a path that did not exist.

OVERMATCH is a fourth result class, REPORTED and counted in no verdict (AP-62).
These are commands that merely NAME a dangerous shape inside a quoted string.
Measured 2026-09-08, synthetic — zero observed in production, so nothing was
narrowed: the hook's loosening trigger is an OBSERVED false-positive count
(`rules/hook-deny-message.md`, FALSE-POSITIVE LOG convention), and a synthetic
hit is not one. They are pinned here so that the day a real session hits one,
the shape is already named and the fix is a narrowing with these as regression
cases — not a rediscovery.

Isolation: CLAUDE_CONFIG_DIR points the deny receipt at a temp dir, so a suite
that runs on every sweep never inflates the live deny denominator (D-01 checks
it). No case ever executes a command; the hook only ever sees the string.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
HOOK = HOME / "hooks" / "dangerous_command_guard.py"
REAL_RECEIPTS = HOME / "telemetry" / "dangerous-command-guard.jsonl"
TEMP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\x\AppData\Local"),
                        "Temp", "claude", "probe")

MUST_DENY = [
    # recursive+force deletion, high blast radius
    ("Bash", r"rm -rf C:\Users\x\work", "absolute path"),
    ("Bash", "rm -rf /etc/nginx", "absolute posix path"),
    ("Bash", "rm -rf ~/.cache", "home"),
    ("Bash", "rm -rf ../sibling", "parent traversal"),
    ("Bash", "rm -rf .", "bare cwd"),
    ("Bash", "rm -rf *", "bare glob"),
    ("Bash", "rm --recursive --force /var/log", "long-flag spelling"),
    ("PowerShell", r"Remove-Item -Recurse -Force C:\Users\x\work",
     "PowerShell recursive delete"),
    ("PowerShell", r"rmdir /s /q C:\temp", "cmd-style /s"),
    # history-destroying git
    ("Bash", "git push --force origin main", "force push"),
    ("Bash", "git push -f", "force push, short flag"),
    ("Bash", "git push origin main -f && echo ok", "force flag before a separator"),
    ("Bash", "git status; git push -f", "force push after a separator"),
    ("Bash", "git reset --hard HEAD~1", "reset --hard"),
    ("Bash", "git clean -fd", "clean -f"),
    ("Bash", "git checkout -- .", "whole-tree discard"),
    ("Bash", "git restore .", "whole-tree restore"),
    # registry
    ("Bash", r"reg add HKCU\Software\X /v Y /d 1", "reg add"),
    ("Bash", r"reg delete HKLM\Software\X /f", "reg delete"),
    ("PowerShell", r"Set-ItemProperty HKCU:\Software\X -Name Y -Value 1",
     "*-ItemProperty on a hive"),
    ("PowerShell", r"New-ItemProperty HKLM:\SOFTWARE\Y -Name Z -Value 1",
     "*-ItemProperty on a hive"),
    # machine state
    ("Bash", "shutdown /r /t 0", "shutdown"),
    ("PowerShell", "Restart-Computer -Force", "Restart-Computer"),
    ("PowerShell", "Stop-Computer", "Stop-Computer"),
    ("PowerShell", "Format-Volume -DriveLetter D", "Format-Volume"),
    ("PowerShell", "Clear-Disk -Number 1 -RemoveData", "Clear-Disk"),
    ("Bash", "diskpart", "diskpart"),
    ("Bash", "mkfs.ext4 /dev/sdb1", "mkfs"),
    # machine state in every command position the 2026-09-22 narrowing keeps
    ("Bash", "git status; shutdown -h now", "after a separator"),
    ("Bash", "make && shutdown /s /t 0", "after &&"),
    ("Bash", "sudo shutdown now", "after sudo"),
    ("Bash", "cmd /c shutdown /r", "cmd /c launcher"),
    ("Bash", "bash -c 'shutdown -r now'", "quoted -c command"),
    ("Bash", "echo ok\nshutdown.exe /s", "at a line start"),
    ("Bash", "x=$(shutdown -k now)", "inside $( )"),
    ("PowerShell", 'powershell -Command "Stop-Computer -Force"', "-Command launcher"),
    ("PowerShell", "Get-Disk 1 | Clear-Disk -RemoveData", "after a pipe"),
    ("PowerShell", "if ($x) { Restart-Computer }", "inside a script block"),
    ("PowerShell", "& diskpart", "call operator"),
    ("PowerShell", "Set-ExecutionPolicy RemoteSigned", "execution policy"),
]

MUST_PASS = [
    # deletes that stay inside the project or the scratchpad
    ("Bash", "rm -rf node_modules", "relative in-project target"),
    ("Bash", "rm -rf ./build", "relative in-project target"),
    ("Bash", "rm -rf dist/assets", "relative in-project target"),
    ("Bash", f"rm -rf {TEMP_DIR}/scratch", "scratchpad cleanup is routine"),
    ("Bash", "rm -rf /tmp/foo", "posix temp root"),
    ("PowerShell", r"Remove-Item -Recurse -Force .\node_modules",
     "relative in-project target"),
    ("PowerShell", r"Remove-Item -Recurse -Force $env:TEMP\build", "temp root"),
    ("PowerShell", "Remove-Item ./one-file.txt", "no -Recurse, no -Force"),
    ("PowerShell", "Get-ChildItem -Recurse -Force .", "reads, does not delete"),
    # git shapes that are safe by construction
    ("Bash", "git push --force-with-lease origin main", "the approved spelling"),
    ("Bash", "git push origin main", "ordinary push"),
    ("Bash", "git push origin v1.2 --tags && git branch -f release v1.2",
     "observed 2026-09-27: a later local `branch -f` is not a forced push"),
    ("Bash", "git reset --soft HEAD~1", "reset --soft keeps the worktree"),
    ("Bash", "git reset HEAD~1", "mixed reset keeps the worktree"),
    ("Bash", "git clean -n", "dry run is the recommended first step"),
    ("Bash", "git checkout -- src/app.ts", "a named path, not the whole tree"),
    ("Bash", "git restore --staged src/app.ts", "a named path"),
    ("Bash", "git stash", "the recommended alternative to reset --hard"),
    ("Bash", "git status --short && git log --oneline -5", "ordinary traffic"),
    # registry / machine words in a READ or a different verb
    ("Bash", r"reg query HKCU\Software", "reads the hive"),
    ("PowerShell", r"Get-ItemProperty HKLM:\SOFTWARE\Microsoft", "reads the hive"),
    ("PowerShell", "Get-ExecutionPolicy", "reads the policy"),
    ("Bash", "cargo clean -f", "not git clean"),
    # the four OBSERVED 2026-09-22 misfires (hook FALSE-POSITIVE LOG) + the old synthetic one
    ("Bash", r'grep -n "Machine-state\|shutdown\|FALSE-POSITIVE" hooks/x.py',
     "observed: grep alternation naming the verb"),
    ("Bash", "python report_fp.py --why \"the word 'shutdown' (read-only search) was classed\"",
     "observed: prose inside a --why argument"),
    ("Bash", "python - <<'EOF'\n    print('stopping')\n    srv.shutdown()\nEOF",
     "observed: a method call in a heredoc"),
    ("Bash", "echo 'the shutdown procedure is documented'",
     "synthetic 2026-09-08 OVERMATCH, now narrowed"),
    # ordinary work
    ("Bash", "npm run build", "ordinary work"),
    ("Bash", "python tools/graph-snapshot/gsnap.py freshness", "ordinary work"),
    ("Read", r"rm -rf C:\Users\x", "not a shell tool -- out of scope"),
    ("Edit", "git reset --hard", "not a shell tool -- out of scope"),
    # the declared per-instance escape
    ("Bash", "rm -rf /home/u/proj [user-approved-destructive]", "approval marker"),
    ("PowerShell", "Set-ExecutionPolicy Bypass [user-approved-destructive]",
     "approval marker"),
    # fail-open contract
    ("Bash", "", "empty command"),
]

# Asserted, counted in no verdict: a recursive delete whose TARGET is an
# unexpanded shell variable. (tool, cmd, twin_cmd, escapes) — twin_cmd is the
# same command with the variable written out, and must deny.
UNDETERMINED = [
    ("Bash", 'rm -rf "$PROJECT_ROOT"', 'rm -rf "/srv/project"',
     "a POSIX variable: not a flag, not a temp root, no `..`, not a bare "
     "./*/~//, not absolute -- so dangerous_delete_target falls through its "
     "whole class list and returns None, the `relative in-project` verdict"),
    ("Bash", r"rm -rf %APPDATA%\Claude\cache",
     r"rm -rf C:\Users\x\AppData\Roaming\Claude\cache",
     "a cmd-style variable: `%APPDATA%` is not the `Local\\Temp` root the "
     "exemption names, and the guard never expands it to find out"),
    ("PowerShell", "Remove-Item -Recurse -Force $ProjectRoot",
     r"Remove-Item -Recurse -Force C:\srv\project",
     "a PowerShell variable: the -Recurse -Force flags match, so the guard "
     "reaches the target test and then cannot classify the target"),
]

# Reported, never counted: the guard matches inside quoted strings, so a message
# that NAMES a shape is denied. Synthetic (2026-09-08), zero observed.
OVERMATCH = [
    ("Bash", 'git commit -m "note: never rm -rf / on this box"',
     "a commit message naming the shape"),
    ("Bash", "python pb.py save <<'EOF'\nnever run rm -rf / here\nEOF",
     "observed 1x 2026-10-02: prose in a heredoc body (not narrowed, trigger 3)"),
    # the machine-state specimen moved to MUST_PASS on 2026-09-22 (observed 4x, narrowed)
]


def load_hook_module():
    """Import the hook for its RULES list -- the coverage check must read the
    LIVE vocabulary, or a rule added without a specimen would go unnoticed."""
    sys.path.insert(0, str(HOME / "hooks"))
    spec = importlib.util.spec_from_file_location("dcg_under_test", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def denied(tool: str, cmd: str, env: dict) -> tuple[bool, int]:
    ti = {"command": cmd} if tool in ("Bash", "PowerShell") else {"file_path": cmd}
    proc = subprocess.run([sys.executable, str(HOOK)],
                          input=json.dumps({"tool_name": tool, "tool_input": ti}),
                          capture_output=True, text=True, env=env, timeout=20)
    out = (proc.stdout or "").strip()
    if not out:
        return False, proc.returncode
    try:
        decision = json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return False, proc.returncode
    return decision == "deny", proc.returncode


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="dcg-test-")
    env = dict(os.environ, CLAUDE_CONFIG_DIR=tmp, PYTHONIOENCODING="utf-8")
    real_before = REAL_RECEIPTS.stat().st_size if REAL_RECEIPTS.exists() else -1
    failures: list[str] = []
    try:
        print(f"{'side':10} {'verdict':8} case")
        print("-" * 100)
        for tool, cmd, note in MUST_DENY:
            hit, rc = denied(tool, cmd, env)
            print(f"{'MUST-DENY':10} {'deny' if hit else 'PASS!!':8} "
                  f"{tool}: {cmd[:46]:46}  {note}")
            if not hit or rc != 0:
                failures.append(f"MUST-DENY leaked: {tool}: {cmd}  ({note}, rc {rc})")
        for tool, cmd, note in MUST_PASS:
            hit, rc = denied(tool, cmd, env)
            print(f"{'MUST-PASS':10} {'pass' if not hit else 'DENY!!':8} "
                  f"{tool}: {cmd[:46]:46}  {note}")
            if hit or rc != 0:
                failures.append(f"MUST-PASS blocked: {tool}: {cmd}  ({note}, rc {rc})")

        # --- fail-open on unparseable input ---------------------------------
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json {{{",
                              capture_output=True, text=True, env=env, timeout=20)
        ok = proc.returncode == 0 and not proc.stdout.strip()
        print(f"{'FAIL-OPEN':10} {'ok' if ok else 'BROKEN':8} garbage stdin "
              f"-> rc {proc.returncode}, silent")
        if not ok:
            failures.append("garbage stdin did not fail open (a guard bug must "
                            "never block work)")

        # --- vocabulary coverage over the hook's OWN rule list ---------------
        mod = load_hook_module()
        print("-" * 100)
        uncovered = []
        for scope, pattern, reason in mod.RULES:
            fired = any(
                (scope == "any" or scope == ("bash" if t == "Bash" else "ps"))
                and pattern.search(c)
                for t, c, _n in MUST_DENY if t in ("Bash", "PowerShell"))
            if not fired:
                uncovered.append(reason[:60])
        for label, matcher in (("RECURSIVE_RM", mod.RECURSIVE_RM),
                               ("PS_RECURSIVE_RM", mod.PS_RECURSIVE_RM)):
            if not any(matcher.search(c) for _t, c, _n in MUST_DENY):
                uncovered.append(label)
        ok = not uncovered
        print(f"{'ok  ' if ok else 'FAIL'} D-COV every live rule has a "
              f"MUST-DENY specimen: {len(mod.RULES) + 2} rules, "
              f"{len(uncovered)} uncovered")
        for u in uncovered:
            failures.append(f"D-COV: no MUST-DENY case fires the rule -- {u}")

        # --- undetermined: asserted, counted in no verdict (AP-62) -----------
        print("-" * 100)
        for tool, cmd, twin, escapes in UNDETERMINED:
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps({"tool_name": tool, "tool_input": {"command": cmd}}),
                capture_output=True, text=True, env=env, timeout=20)
            ruled = (proc.stdout or "").strip()
            ok = proc.returncode == 0 and not ruled
            print(f"{'UNDET':10} {'undet' if ok else 'RULED!':8} "
                  f"{tool}: {cmd[:46]:46}  no opinion -> the permission prompt")
            print(f"{'':10} {'':8}   escapes: {escapes}")
            if not ok:
                failures.append(
                    f"UNDETERMINED ruled on: {tool}: {cmd} -- the guard emitted a "
                    f"decision (rc {proc.returncode}) on a delete target whose "
                    f"value does not exist at decision time. AP-62: an input "
                    f"matching no declared target class is undetermined and is "
                    f"forwarded, never folded into a verdict. If the guard "
                    f"learned to expand variables, move this case to MUST_DENY "
                    f"and keep its twin as the regression.")
            twin_hit, twin_rc = denied(tool, twin, env)
            if not twin_hit or twin_rc != 0:
                failures.append(
                    f"UNDETERMINED twin leaked: {tool}: {twin} (rc {twin_rc}) -- "
                    f"the twin of '{cmd}' must deny, or that case proves nothing: "
                    f"a no-opinion on a shape the guard never rules on is not an "
                    f"undetermined verdict, it is a gap in the matcher.")

        # --- overmatch: printed, counted in no verdict -----------------------
        for tool, cmd, note in OVERMATCH:
            hit, _rc = denied(tool, cmd, env)
            print(f"{'OVERMATCH':10} {'deny' if hit else 'pass':8} "
                  f"{tool}: {cmd[:46]:46}  {note}"
                  f"{'' if hit else '  <- narrowed since 2026-09-08; log it'}")

        real_after = REAL_RECEIPTS.stat().st_size if REAL_RECEIPTS.exists() else -1
        ok = real_before == real_after
        print(f"{'ok  ' if ok else 'FAIL'} D-01 the live receipt file was not "
              f"touched: {real_before} -> {real_after} bytes")
        if not ok:
            failures.append(
                "D-01: this run wrote to the LIVE telemetry/dangerous-command-"
                "guard.jsonl -- CLAUDE_CONFIG_DIR isolation broke and every "
                "sweep would inflate the deny denominator. Fix the env in "
                "main(), not this assertion.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("-" * 100)
    print(f"must-deny: {len(MUST_DENY)}   must-pass: {len(MUST_PASS)}   "
          f"undetermined + twins (not counted): {len(UNDETERMINED)}   "
          f"overmatch (not counted): {len(OVERMATCH)}   failures: {len(failures)}")
    if failures:
        for f in failures:
            print("  FAIL " + f)
        return 1
    total = len(MUST_DENY) + len(MUST_PASS) + 2 * len(UNDETERMINED) + 3
    print(f"ALL PASS {total}/{total} ({len(MUST_DENY)} must-deny, "
          f"{len(MUST_PASS)} must-pass, {len(UNDETERMINED)} undetermined + "
          f"{len(UNDETERMINED)} determinable twins, fail-open, coverage, "
          f"isolation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
