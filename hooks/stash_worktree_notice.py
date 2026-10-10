r"""PreToolUse notice: a `git stash` that writes the stash, in a repository that has linked worktrees.

STATUS: LIVE since 2026-10-06. Carries `ops/rule-registry.md` key
`stash_worktree_notice` — the asset property `ops/references/shared-tree-git.md`
§0 states for `refs/stash` (L-130, folded 2026-10-06).

WHAT IT GATES. `refs/stash` is ONE ref for the canonical tree and every linked
worktree (HEAD and the index are per-worktree; the stash is not). Probe W3 in
L-130: a stash pushed in a worktree is popped by a peer's `git stash pop` in the
canonical tree, which exits 0 and writes the worktree's edit into the canonical
working tree. Nothing errors.

WHY A NOTICE AND NEVER A DENY (user ruling 2026-10-06 「走建議用提醒的」). The
hook can determine that the repository has worktrees, not that a peer is active
in one; a stash in a repository whose worktrees are idle loses nothing. No loss
incident is on record. Same ladder as dispatch_commit_notice (L-061): promotion
to DENY on a first incident where a stash entry crossed trees.

DECISION (all must hold):
  - the command runs `git [-C <dir>] [-c k=v]… stash` with no subcommand (= push)
    or one of push|save|pop|apply|drop|clear|branch — `list`/`show` only read;
  - the target repository (`-C <dir>` when given, else the payload cwd) lists
    more than one entry in `git worktree list --porcelain`.

Fail-open: any parse or git problem exits 0 with no output.

Proof-of-life: `python hooks/tests/test_stash_worktree_notice.py`
"""
import json
import os
import re
import subprocess
import sys
import time

try:
    from deny_receipt import notice_clause
except Exception:           # a notice must not break the call if telemetry breaks
    def notice_clause(hook, log=""): return ""

HOOK = "stash_worktree_notice"
LOG_PATH = os.path.join(
    os.environ.get("CLAUDE_TELEMETRY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "telemetry"),
    "stash-worktree-notice.jsonl")
NOTICE_ID = "stash_worktree_notice, a local PreToolUse hook (not file or page content): "

# git, then global options (-C <dir>, -c k=v, --no-pager …), then `stash`, then an optional subcommand.
STASH_RE = re.compile(
    r"""\bgit((?:\s+(?:-C\s+(?:"[^"]*"|'[^']*'|\S+)|-c\s+\S+|--[a-z-]+))*)\s+stash\b(?:\s+([a-z]+))?""")
WRITING = {None, "push", "save", "pop", "apply", "drop", "clear", "branch"}
DIR_RE = re.compile(r"""-C\s+("[^"]*"|'[^']*'|\S+)""")


def stash_target(command: str, cwd: str):
    """(subcommand, target dir) of the first stash-writing git call, or None."""
    for m in STASH_RE.finditer(command):
        sub = m.group(2)
        if sub not in WRITING and not (sub or "").startswith("-"):
            continue
        d = DIR_RE.findall(m.group(1) or "")
        target = d[-1].strip("\"'") if d else cwd
        if target and not os.path.isabs(target) and cwd:
            target = os.path.join(cwd, target)
        return (sub or "push"), target
    return None


def worktree_count(target: str) -> int:
    p = subprocess.run(["git", "-C", target, "worktree", "list", "--porcelain"],
                       capture_output=True, text=True, encoding="utf-8", timeout=10)
    if p.returncode != 0:
        return 0
    return sum(1 for line in p.stdout.splitlines() if line.startswith("worktree "))


def record(payload, sub, target, n):
    """Persist before emitting. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "kind": "notice",
                "hook": HOOK,
                "session": sid[:64] if isinstance(sid := payload.get("session_id"), str) else None,
                "subcommand": sub,
                "target": target,
                "worktrees": n,
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    ti = payload.get("tool_input")
    command = ti.get("command") if isinstance(ti, dict) else None
    cwd = payload.get("cwd")
    if not isinstance(command, str) or not isinstance(cwd, str):
        sys.exit(0)
    try:
        hit = stash_target(command, cwd)
        if not hit:
            sys.exit(0)
        sub, target = hit
        n = worktree_count(target)
    except Exception:
        sys.exit(0)
    if n < 2:
        sys.exit(0)

    record(payload, sub, target, n)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": NOTICE_ID + (
                f"`git stash {sub}` in a repository with {n} worktrees (canonical + linked). "
                "refs/stash is ONE ref shared by all of them: an entry pushed here can be popped "
                "by a session in another tree, and a pop here can take another tree's entry — "
                "exit 0 either way. If the goal is "
                "to run something against the pre-change version of a file, read it out instead: "
                "`git show <rev>:<path> > <scratchpad>/<name>`. If you checked `git stash list` and "
                "every entry is yours, nothing needs doing."
            ) + notice_clause(HOOK),
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
