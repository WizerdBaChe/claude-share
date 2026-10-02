#!/usr/bin/env python3
"""Two-sided calibration for hooks/branch_commit_guard.py.

Run:  python tools/branch-guard-test/test_branch_commit_guard.py

  MUST-DENY  (positive control) — a git commit whose target checkout resolves
             inside the guarded root with HEAD off `main`. If any of these
             passes, the guard is not holding the line that the 2026-08-27
             incident (c5468e6, f61b226 onto peer sessions' branches) crossed.
  MUST-PASS  (negative control) — ordinary commits and near-miss shapes. If any
             is denied, the guard taxes every session; a deny-everything guard
             scores 100% on a one-sided test.

PRIOR ART: the 2026-08-27 calibration record (13/13, 5
deny / 8 allow; a private note, not shipped). Its cases are reproduced here (B-01..B-13 map to C1..C11) —
this file is not a re-derivation. What CHANGED is that the 2026-08-27 runner was
a one-shot: it asserted against the live repo's then-current off-main HEAD,
planted a worktree in the real tree, and left an opt-in file behind. None of
that can run on every sweep. So the fixture is a REAL git tree built in a temp
directory and pointed at by HOME/USERPROFILE, which relocates both the guarded
root (`guarded_root()` -> `~/.claude`) and the telemetry path in one move.

  B-20 is the control on that isolation: this suite runs the guard ~20 times
  per sweep, and each deny appends a row. If the seam ever breaks, the suite
  would be manufacturing the very deny-rate the hook's docstring says to watch
  (">=5 pass-marker lines from one session" is its reflexive-marker signal).
  A proof-of-life that corrupts the evidence it proves is worse than none.

EXTENDING (PH-11 / AP-61, `ops/references/principle-design-guide.md`): a new
ESCAPE (a third way past the deny) needs one MUST-PASS case proving it works and
one MUST-DENY proving its near-miss still denies — B-05 is that pair's model,
pinning that the primary checkout accepts no opt-in. A new RESOLUTION shape (a
new way a command names its target checkout, beside cwd / `cd` / `git -C` /
`Set-Location`) needs a case in both lists.

Classes are enumerated and CLOSED (AP-62). A case whose fixture could not be
built is reported as UNBUILT and the suite exits non-zero rather than silently
shrinking its matrix. Every case is exactly one of MUST_DENY / MUST_PASS, plus a
third class that is asserted and counted in NEITHER:

  UNDETERMINED — a target checkout INSIDE the guarded root whose branch the
  guard cannot resolve. The guard's checkout classes are enumerated by
  head_info(): a `.git` directory (primary), a `.git` file carrying a `gitdir:`
  pointer (linked worktree), and either of those on a detached HEAD. B-U1 is the
  fourth shape — a `.git` FILE with no `gitdir:` line, the residue of a vendored
  or half-copied tree — which matches none of them. head_info returns branch
  None, run() skips the target, and NOTHING is recorded: no deny, no
  pass-marker, no pass-optin. That is the AP-62 property this case pins, and it
  is asserted as a telemetry DELTA of zero, not merely as "was not denied" —
  "excluded from every verdict count" is the half that a silent fold breaks.

  The fold is DECLARED, which is why it is a specimen and not a defect report:
  the hook's FAIL-OPEN section says any crash, unreadable HEAD, or parse failure
  exits 0 and the commit proceeds unguarded. B-U1 is a parse failure by
  construction. Its DETERMINABLE TWIN (B-U2) runs the identical command from the
  identical cwd with the broken `.git` file removed, so the walk reaches the
  off-main primary and denies. The twin is what stops B-U1 passing for the wrong
  reason: without it, a fixture accidentally built OUTSIDE the guarded root
  would also record nothing and would also look green.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
HOOK = HOME / "hooks" / "branch_commit_guard.py"
REAL_TELEMETRY = HOME / "telemetry" / "branch-commit-guard.jsonl"

OFF_MAIN = "feat/lse-connector-lifecycle"   # the incident branch, kept by name
WT_BRANCH = "claude/dazzling-dijkstra-9c5682"
GIT_ID = ["-c", "user.email=calib@local", "-c", "user.name=calib",
          "-c", "commit.gpgsign=false"]

UNBUILT: list[str] = []


def git(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def build(tmp: Path) -> dict:
    """A real git tree: a primary checkout, a linked worktree, a nested repo on
    main, a detached checkout, an out-of-scope repo, and a scratch root."""
    paths = {
        "primary": tmp / ".claude",
        "worktree": tmp / ".claude" / ".claude" / "worktrees" / "wt",
        "nested": tmp / ".claude" / "nested" / "lib",
        "detached": tmp / ".claude" / "detached",
        "outside": tmp / "outside" / "repo",
        "scratch_root": tmp / "scratchroot",
        "scratch_repo": tmp / "scratchroot" / "repoM",
    }

    def init(path: Path, branch: str) -> None:
        path.mkdir(parents=True, exist_ok=True)
        git("-c", "init.defaultBranch=main", "init", str(path))
        git(*GIT_ID, "commit", "--allow-empty", "-m", "init", cwd=str(path))
        if branch != "main":
            git("checkout", "-q", "-b", branch, cwd=str(path))

    init(paths["primary"], OFF_MAIN)
    init(paths["nested"], "main")
    init(paths["outside"], "feat/unrelated")
    init(paths["scratch_repo"], "main")
    init(paths["detached"], "main")
    head = git("rev-parse", "HEAD", cwd=str(paths["detached"])).stdout.strip()
    git("checkout", "-q", "--detach", head, cwd=str(paths["detached"]))

    # B-U1's fixture: a directory under the (off-main) primary whose `.git` is a
    # FILE with no `gitdir:` pointer -- a checkout shape head_info cannot parse.
    paths["undet"] = paths["primary"] / "vendored"
    paths["undet"].mkdir(parents=True, exist_ok=True)
    (paths["undet"] / ".git").write_text(
        "this is not a gitdir pointer\n", encoding="utf-8")

    paths["worktree"].parent.mkdir(parents=True, exist_ok=True)
    res = git("worktree", "add", "-b", WT_BRANCH, str(paths["worktree"]),
              cwd=str(paths["primary"]))
    if res.returncode != 0:
        UNBUILT.append(f"linked worktree: {res.stderr.strip()[:120]}")
    paths["wt_gitdir"] = paths["primary"] / ".git" / "worktrees" / "wt"
    paths["telemetry"] = paths["primary"] / "telemetry" / "branch-commit-guard.jsonl"
    return paths


def call(tmp: Path, tool, cwd, cmd, env_extra=None, raw=None):
    """-> (denied, returncode). HOME/USERPROFILE relocate the guarded root AND
    the telemetry path; CLAUDE_CONFIG_DIR relocates the deny receipt."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("BRANCH_GUARD_ROOT", "CLAUDE_TELEMETRY_DIR")}
    # branch_commit_guard.py's own LOG_PATH now checks CLAUDE_TELEMETRY_DIR
    # before falling back to expanduser("~"); an inherited one (e.g. from a
    # harness running this suite) would outrank the HOME/USERPROFILE
    # relocation above and steer rows away from tmp, so it is dropped, not
    # inherited.
    env.update(HOME=str(tmp), USERPROFILE=str(tmp), HOMEDRIVE="",
               HOMEPATH=str(tmp), CLAUDE_CONFIG_DIR=str(tmp / ".claude"),
               PYTHONIOENCODING="utf-8")
    if env_extra:
        env.update(env_extra)
    if raw is None:
        payload = {"session_id": "branch-guard-test", "hook_event_name": "PreToolUse",
                   "tool_name": tool}
        if cwd is not None:
            payload["cwd"] = str(cwd)
        if cmd is not None:
            payload["tool_input"] = {"command": cmd}
        raw = json.dumps(payload)
    proc = subprocess.run([sys.executable, str(HOOK)], input=raw, env=env,
                          capture_output=True, text=True, timeout=30)
    denied = False
    if proc.stdout.strip():
        try:
            denied = (json.loads(proc.stdout)["hookSpecificOutput"]
                      ["permissionDecision"] == "deny")
        except Exception:
            denied = False
    return denied, proc.returncode


def cases(p: dict) -> list[tuple]:
    """(id, expect_deny, tool, cwd, cmd, env_extra, note). Order matters only
    for B-03/B-05, which write their opt-in file just before running."""
    primary, wt = p["primary"], p["worktree"]
    return [
        # --- MUST-DENY -------------------------------------------------------
        ("B-01", True, "Bash", primary, 'git commit -m "docs: update"', None,
         "primary checkout off-main (the incident shape)"),
        ("B-02", True, "Bash", wt, 'git commit -m "feat: x"', None,
         "linked worktree on claude/*, no opt-in yet"),
        ("B-05", True, "Bash", primary, 'git commit -m "docs: y"', None,
         "opt-in file PLANTED in the primary gitdir -- must not be honoured"),
        ("B-10", True, "Bash", p["outside"],
         f'git -C "{primary}" commit -m "x"', None,
         "-C resolves into the guarded root from an out-of-scope cwd"),
        ("B-11", True, "PowerShell", p["outside"],
         f'Set-Location "{primary}"; git commit -m "wip"', None,
         "PowerShell tool + Set-Location tracking"),
        ("B-14", True, "Bash", p["detached"], 'git commit -m "x"', None,
         "detached HEAD is not `main` either"),
        ("B-18", True, "Bash", p["outside"],
         f'git commit -m "a" && cd "{primary}" && git commit -m "b"', None,
         "second invocation in a cd-chain lands inside the root"),
        # --- MUST-PASS -------------------------------------------------------
        ("B-03", False, "Bash", wt, 'git commit -m "feat: x"', None,
         "same worktree AFTER opt-in glob claude/*"),
        ("B-04", False, "Bash", wt, 'git commit -m "feat: x [branch-ok]"', None,
         "marker escape, verified-this-turn contract"),
        ("B-06", False, "Bash", p["nested"], 'git commit -m "chore: y"', None,
         "nested repo inside the root, but on main"),
        ("B-07", False, "Bash", p["outside"], 'git commit -m "z"', None,
         "checkout outside the guarded root, off-main"),
        ("B-08", False, "Bash", primary, "git status && git log --oneline -3",
         None, "no commit token -- fast path"),
        ("B-09", False, "Bash", primary, "git log --format=%H -1 && echo commit",
         None, "git and commit both present, no commit invocation"),
        ("B-12", False, None, None, None, None, "garbage stdin -- fail-open"),
        ("B-13", False, "Bash", None, None, None, "tool_input missing"),
        ("B-15", False, "Bash", p["scratch_repo"], 'git commit -m "q"',
         {"BRANCH_GUARD_ROOT": str(p["scratch_root"])},
         "BRANCH_GUARD_ROOT override, repo on main -- the seam still resolves"),
        ("B-16", False, "Bash", primary, "git commit-tree HEAD^{tree} -m x",
         None, "`commit-tree` is a different verb, excluded by the boundary"),
        ("B-17", False, "Read", primary, None, None,
         "not a shell tool -- out of scope"),
        ("B-19", False, "Bash", p["outside"],
         f'cd "{p["nested"]}" && git commit -m "x"', None,
         "cd-chain into a main-branch nested repo"),
    ]


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="branch-guard-test-"))
    real_before = REAL_TELEMETRY.stat().st_size if REAL_TELEMETRY.exists() else -1
    failures: list[str] = []
    try:
        p = build(tmp)
        allow_wt = p["wt_gitdir"] / "branch-guard-allow"
        allow_primary = p["primary"] / ".git" / "branch-guard-allow"

        print(f"{'id':6} {'expect':7} {'got':7} {'rc':>2}  note")
        print("-" * 92)
        n_deny = n_allow = 0
        for cid, expect, tool, cwd, cmd, env_extra, note in cases(p):
            n_deny, n_allow = n_deny + bool(expect), n_allow + (not expect)
            if cid == "B-03" and allow_wt.parent.is_dir():
                allow_wt.write_text("claude/*\n", encoding="utf-8")
            if cid == "B-05":
                # the escape the primary checkout must NOT have
                allow_primary.write_text(f"{OFF_MAIN}\n*\n", encoding="utf-8")
            if cid == "B-12":
                denied, rc = call(tmp, None, None, None, raw="not json {{{")
            else:
                denied, rc = call(tmp, tool, cwd, cmd, env_extra)
            ok = (rc == 0) and (denied == expect)
            print(f"{cid:6} {'DENY' if expect else 'allow':7} "
                  f"{'DENY' if denied else 'allow':7} {rc:>2}  "
                  f"{'' if ok else '** FAIL ** '}{note}")
            if not ok:
                failures.append(
                    f"{cid}: expected {'deny' if expect else 'allow'}, got "
                    f"{'deny' if denied else 'allow'} (rc {rc}) -- {note}")

        # --- UNDETERMINED: asserted, counted in no verdict (AP-62) -----------
        # Runs BEFORE the telemetry block so B-U2's deny is inside its tally.
        def tele_rows() -> int:
            if not p["telemetry"].exists():
                return 0
            return sum(1 for ln in p["telemetry"].read_text(encoding="utf-8")
                       .splitlines() if ln.strip())

        print("-" * 92)
        undet_cwd = p["undet"]
        before = tele_rows()
        denied, rc = call(tmp, "Bash", undet_cwd, 'git commit -m "docs: z"')
        after = tele_rows()
        ok = (not denied) and rc == 0 and after == before
        print(f"{'B-U1':6} {'UNDET':7} {'undet' if ok else 'RULED!':7} {rc:>2}  "
              f"a `.git` FILE with no `gitdir:` line -- matches none of "
              f"head_info's checkout classes; recorded {after - before} verdict "
              f"row(s), want 0")
        if not ok:
            failures.append(
                f"B-U1: an unresolvable checkout inside the guarded root was "
                f"{'DENIED' if denied else 'allowed'} (rc {rc}) and appended "
                f"{after - before} telemetry row(s), want 0. AP-62: an input "
                f"matching no declared class is undetermined and excluded from "
                f"every verdict count -- folding it into deny, pass-marker or "
                f"pass-optin makes those counts plausible and wrong.")

        # B-U2, the determinable twin: identical cwd and command, `.git` removed,
        # so the walk reaches the off-main primary. Without this, a fixture built
        # outside the guarded root would make B-U1 green for the wrong reason.
        (undet_cwd / ".git").unlink()
        denied, rc = call(tmp, "Bash", undet_cwd, 'git commit -m "docs: z"')
        ok = denied and rc == 0
        print(f"{'B-U2':6} {'DENY':7} {'DENY' if denied else 'allow':7} {rc:>2}  "
              f"{'' if ok else '** FAIL ** '}the same cwd once the checkout IS "
              f"resolvable -- proves B-U1 sat in scope and off-main")
        if not ok:
            failures.append(
                f"B-U2: the twin of B-U1 was allowed (rc {rc}). B-U1's fixture "
                f"is not where this suite thinks it is -- it resolved to no "
                f"in-scope off-main checkout even with a readable `.git`, so "
                f"B-U1 proved nothing about unresolvable input.")

        # --- the persist-before-veto contract --------------------------------
        rows = []
        if p["telemetry"].exists():
            for line in p["telemetry"].read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        failures.append("telemetry line is not JSON")
        verdicts = [r.get("verdict") for r in rows if "verdict" in r]
        print("-" * 92)
        for label, want, got in (
            ("B-T1 every deny persisted its command before the veto", 8,
             verdicts.count("deny")),   # 7 MUST-DENY cases + B-U2, the twin
            ("B-T2 the marker escape is recorded, not silent", 1,
             verdicts.count("pass-marker")),
            ("B-T3 the opt-in escape is recorded, not silent", 1,
             verdicts.count("pass-optin")),
        ):
            ok = want == got
            print(f"{'ok  ' if ok else 'FAIL'} {label}: {got} (want {want})")
            if not ok:
                failures.append(f"{label}: got {got}, want {want}")

        real_after = REAL_TELEMETRY.stat().st_size if REAL_TELEMETRY.exists() else -1
        ok = real_before == real_after
        print(f"{'ok  ' if ok else 'FAIL'} B-20 the live telemetry file was not "
              f"touched: {real_before} -> {real_after} bytes")
        if not ok:
            failures.append(
                "B-20: this run wrote to the LIVE telemetry/branch-commit-guard"
                ".jsonl -- the HOME/USERPROFILE seam in call() broke, and every "
                "sweep would inflate the deny denominator. Fix call(), not this "
                "assertion.")
    finally:
        # a linked worktree holds no lock once the parent repo is gone
        shutil.rmtree(tmp, ignore_errors=True)

    if UNBUILT:
        failures.extend(f"fixture not built: {u}" for u in UNBUILT)
    print()
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print("  " + f)
        return 1
    # Counted, not typed: this line was the literal string "ALL PASS 25/25" until
    # 2026-09-09, so it printed the same total whatever ran -- and the number it
    # printed had already outlived the docstring that quoted it.
    total = n_deny + n_allow + 2 + 3 + 1
    print(f"ALL PASS {total}/{total} ({n_deny} must-deny, {n_allow} must-pass, "
          "1 undetermined + its determinable twin, 3 telemetry, 1 isolation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
