"""Suite for hooks/stash_worktree_notice.py.

Run: python hooks/tests/test_stash_worktree_notice.py [path-to-hook]

Two-sided on real temp repositories: the same stash command must notice in a repo
WITH a linked worktree and stay silent in one WITHOUT, or the worktree count is
not what decides (an inverted build that ignores it fails F1).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path(__file__).resolve().parents[1] / "stash_worktree_notice.py")
PY = sys.executable
TMP = Path(tempfile.mkdtemp(prefix="stash-notice-test-"))
_ENV = dict(os.environ, CLAUDE_TELEMETRY_DIR=str(TMP / "telemetry"))
RESULTS = []


def git(*a, cwd):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)


def make_repo(name, with_worktree):
    r = TMP / name
    r.mkdir()
    git("init", "-q", cwd=r)
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init", cwd=r)
    if with_worktree:
        git("worktree", "add", "-q", str(TMP / f"{name}-wt"), "-b", "wt", cwd=r)
    return r


SHARED = make_repo("shared", True)
SOLO = make_repo("solo", False)


def run(command=None, cwd=SHARED, tool="Bash", raw=None):
    if raw is None:
        raw = json.dumps({"tool_name": tool, "tool_input": {"command": command},
                          "session_id": "synthtest-stash", "cwd": str(cwd)})
    p = subprocess.run([PY, str(HOOK)], input=raw, capture_output=True, text=True, encoding="utf-8", env=_ENV)
    out = (p.stdout or "").strip()
    text = ""
    if out:
        try:
            text = json.loads(out).get("hookSpecificOutput", {}).get("additionalContext", "")
        except Exception:
            text = "(unparseable stdout)"
    return p.returncode, text


def check(name, want_notice, **kw):
    rc, text = run(**kw)
    RESULTS.append((rc == 0 and bool(text) == want_notice, name,
                    "notice" if want_notice else "silent", "notice" if text else "silent"))
    return text


# ------------------------------------------------------------ known TRUE
t = check("T1 bare `git stash` in a repo with a linked worktree -> notice", True, command="git stash")
check("T2 `git stash pop` -> notice", True, command="git stash pop")
check("T3 `git stash push -- file` after cd && -> notice", True, command="git add x && git stash push -q -- moc.py")
check("T4 -C <repo> from an unrelated cwd -> notice", True, command=f'git -C "{SHARED}" stash apply', cwd=TMP)
check("T5 inside the linked worktree itself -> notice", True, command="git stash", cwd=TMP / "shared-wt")
check("T6 PowerShell tool -> notice", True, tool="PowerShell", command="git stash; git status")
RESULTS.append(("git stash push" in t and "2 worktrees" in t and "git show <rev>:<path>" in t
                and t.startswith("stash_worktree_notice, a local PreToolUse hook"),
                "T7 notice names itself first, the subcommand, the count and the read-out route",
                "pinned", "pinned" if "2 worktrees" in t else "unpinned"))

# ----------------------------------------------------------- known FALSE
check("F1 the same `git stash` in a repo WITHOUT worktrees -> silent", False, command="git stash", cwd=SOLO)
check("F2 `git stash list` (read-only) -> silent", False, command="git stash list")
check("F3 `git stash show -p` (read-only) -> silent", False, command="git stash show -p")
check("F4 no stash in the command -> silent", False, command="git status && git log -1")
check("F5 the word stash outside git -> silent", False, command="echo stash this")
check("F6 not a repository -> silent (fail-open)", False, command="git stash", cwd=TMP / "telemetry-missing")
check("F7 other tool -> silent", False, tool="Read", command="git stash")
check("F8 unclassifiable: malformed stdin -> undetermined, silent, fails open", False, raw="not json")
check("F9 unclassifiable: payload is a list -> undetermined, silent", False, raw="[1, 2]")
check("F10 unclassifiable: command is not a string -> undetermined, silent", False,
      raw=json.dumps({"tool_name": "Bash", "tool_input": {"command": ["git", "stash"]}, "cwd": str(SHARED)}))

ok = sum(1 for r in RESULTS if r[0])
for passed, name, want, got in RESULTS:
    print(f"  {'PASS' if passed else 'FAIL'}  {name}" + ("" if passed else f"  (want {want}, got {got})"))
print(f"{ok}/{len(RESULTS)}")
sys.exit(0 if ok == len(RESULTS) else 1)
