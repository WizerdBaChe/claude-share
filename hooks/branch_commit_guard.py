r"""PreToolUse guard: a git commit targeting a checkout inside ~/.claude must
land on `main` — deny anything else unless the command carries explicit intent.

WHY A HOOK AND NOT THE RITUAL. The prose control already existed: L-023
(2026-08-17) prescribes `git branch --show-current` -> stage -> commit ->
`git show`. On 2026-08-27 it ran and did not gate — the check was a
non-gating spectator in a `&&` chain, so the commit proceeded on whatever
branch HEAD happened to be. Same argument as secret_file_guard /
ui_verify_guard (L-011): a rule that must be RECALLED at the moment of
committing fails exactly when a peer has just moved HEAD under you.
Enforce, don't recall.

RULE (asset property, not a path instruction): the shared tree ~/.claude has
one integrity property — work lands on `main` (user ruling 2026-08-25:
local-only repo, local merge to main on acceptance). Therefore: any `git
commit` whose TARGET CHECKOUT (cwd, `cd` chain, or `git -C`) resolves to a
checkout inside ~/.claude, with HEAD not on `main`, is denied unless:
  (a) the command string carries the literal marker [branch-ok] — the
      committer's contract: "I verified the target's current branch IN THIS
      TURN and it is the branch I intend". Unlike the user-approval markers
      (model_cap_guard, secret_file_guard), this one signals verified
      DELIBERATENESS, not user sign-off: feature-branch work here is
      legitimate; only ACCIDENTAL branch inheritance is the failure mode; or
  (b) the target is a LINKED WORKTREE whose checked-out branch matches a
      glob in `<gitdir>/branch-guard-allow` (one pattern per line, `#`
      comments; e.g. `claude/*`). Writing that file is the session's one-time
      opt-in for the branches it owns; it lives in the worktree's private
      gitdir, is never committed, and dies with the worktree.
The PRIMARY checkout (and any nested non-worktree repo under ~/.claude)
accepts NO standing opt-in — its HEAD is shared mutable state, which is the
exact incident vector. Marker only, per commit.

INCIDENT LOG (dated, running — append, never rewrite):
  #1 2026-08-27  commit c5468e6 landed on peer branch feat/lse-connector-layer
     (a local session, cross-index work). Recovered: cherry-pick e4681d9.
  #2 2026-08-27  commit f61b226 landed on peer branch
     feat/lse-connector-lifecycle, same day/session. Recovered: cherry-pick
     d769bbe + SendMessage coordination.
  Root cause, both: a peer switched the PRIMARY checkout's branch mid-turn;
  the committing session's `git branch --show-current` was a non-gating
  spectator in a `&&` chain. Prior control: L-023 ritual (prose, 2026-08-17)
  — present and insufficient. This hook is the compensating control; note
  `Bash(git commit *)` is on the permissions allowlist, so no permission
  prompt stands between a wrong-branch commit and the tree.
  #3 2026-08-27  the registration-side hazard (FAIL-OPEN section below)
     fired machine-wide: live settings.json referenced this file while the
     PRIMARY checkout sat on feat/lse-connector-lifecycle, a branch that
     does not carry it — python exited 2 and EVERY Bash/PowerShell call was
     blocked until the peer session restored the file from main into the
     working tree (byte-identical copy via the ticket session's worktree).
     Deployment property that follows: a hook file referenced by live
     settings.json must exist in the PRIMARY WORKING TREE on every branch
     the primary may sit on; restore it after any branch switch that drops
     it (the file is untracked on such branches — that is fine).
     Addendum (same day, from the lse session's post-mortem + first-hand
     probes): the outage began as a NON-ATOMIC fix — "delete the untracked
     copy, then merge" — and the merge then aborted on unrelated untracked
     collisions, leaving the window open. Convert untracked->tracked in
     place instead (`git checkout main -- hooks/branch_commit_guard.py`, no
     missing-file instant), or dry-run the dependent operation before
     removing anything it depends on. Also observed, twice, first-hand:
     hooks are read LIVE from settings.json — sessions started BEFORE
     registration execute this guard — so registration edits reach every
     running session immediately, outage and protection alike.

GATE AUTHORITY (global CLAUDE.md): deny is permitted only for what the gate
can DETERMINE. The target checkout's HEAD is determinable at decision time by
reading `.git`/`HEAD` files — no subprocess, no races with the allowlist.
Residual TOCTOU: a peer could still move HEAD between this check and the
command's execution; the window shrinks from authoring-time to approval-time
and cannot reach zero without wrapping git itself. Accepted.

KNOWN BOUNDARY (token-not-operation family, cf. secret_file_guard): this
matches the COMMAND TEXT. A command that merely mentions `git commit`
inside a string (e.g. `echo "how git commit works" > notes.md`) resolves to
cwd and can false-positive when cwd is a non-main checkout in scope; the
`cd`/`-C` scan is a best-effort segment walk that quoted separators can
confuse. The blunt direction is the safe one: every false positive has a
one-token escape ([branch-ok]) and is logged below. NOT covered, accepted
(threat model is ACCIDENT by well-behaved sessions, not bypass): commits
from script files, `gh`, python subprocesses, `--dry-run` nuance, or a
determined `-c core.hooksPath` style dodge.

OBSERVED FALSE POSITIVES (running count — this is the narrowing trigger's
evidence; append, do not reset). At ~3, narrow (e.g. command-position-only
match) and add every observed case to a must-pass suite in the same change:
  FP-1 2026-08-27  a local session: `git worktree add "$LOCALAPPDATA/…/wt"
     main && … && cd "$LOCALAPPDATA/…/wt" && … git commit` was denied
     against the PRIMARY checkout. Two compounding causes: the cd walk does
     not expand env vars, so the cd target resolved to a non-existent path
     UNDER the primary and find_checkout walked up to it; and the worktree
     is created by the same command, so no probe at authoring time could
     see it. Escaped with [branch-ok] after in-command branch gating.
     Narrowing candidates when the count reaches ~3: expand env vars
     (%VAR%/$VAR/${VAR}) in cd/-C arguments before resolving; and/or treat
     `git worktree add <path> main` earlier in the same command as
     retargeting later segments at <path>.
  FP-2 2026-08-27  a peer session (lse): a hook-verification command that
     ECHOED a JSON payload containing `cd ~/.claude && git
     commit -m …` was denied — the quote-blind segment split took the
     payload's `&&` as real separators and matched the embedded commit
     against the primary. The KNOWN-BOUNDARY class observed in the field;
     escaped by rewording, cost seconds. Count = 2: at the next observed
     FP, run the narrowing pass with FP-1 + FP-2 as the must-pass suite
     (env-var expansion in cd/-C args + quote-aware splitting are the
     named candidates).

NARROWING-PASS DESIGN NOTE (2026-08-27, analysis contributed by the lse
session; USER RULING 2026-08-27: HOLD — no early pass; run it when a named
trigger fires, FP #3 or the habituation threshold below. Recorded so the
pass starts from it, not from scratch): the deny itself is proportionate and should NOT be
loosened. The fragile part is [branch-ok] being SELF-CERTIFIED and
per-commit: on a feature branch it turns reflexive, and a reflexive marker
is a no-op against exactly the guarded incident (HEAD moved under you
mid-turn). Ownership is a fact; deliberateness is an assertion. Direction:
allow when THIS session created the branch (branch->session recorded at
creation) — but as an ADDITIONAL silent-allow path, not a replacement:
feature work in this tree legitimately spans sessions (feat/lse-* ran
across days), so ownership-only would strand every continuation session.
With the marker retained, the remaining per-commit tax lands only on
PRIMARY-checkout feature commits — the pattern the tree wants to
discourage anyway (worktrees + their opt-in stay tax-free). Habituation is
WATCHABLE in existing telemetry with no code change: roughly >=5
pass-marker lines from one session on the same non-main target is the
signal that the marker has gone reflexive — implement the ownership path
then, with FP-1 + FP-2 still the must-pass floor.

CALIBRATION (2026-08-27, pre-registration; runner + full matrix inlined in
outputs/branch-commit-guard-calibration-2026-08-27.md): 13/13, 5 deny /
8 allow, mixed verdicts — denied: the REAL primary checkout live off-main on
feat/lse-connector-lifecycle (the incident shape, not a simulation; also via
`-C` from outside and via PowerShell `Set-Location`), the real session
worktree pre-opt-in, and a planted feat/* worktree. Allowed: marker, opt-in,
main-branch checkout (scratch repo via BRANCH_GUARD_ROOT), out-of-scope
repo, two non-commit git commands, garbage stdin, missing tool_input. Every
case exited 0; telemetry appended exactly 5 deny + 2 pass lines.

EVIDENCE BEFORE THE VETO: every deny (and every marker/opt-in pass) is
appended to telemetry/branch-commit-guard.jsonl BEFORE the decision is
emitted — the commit message travels inside the command and must survive the
veto (global gate rule: persist what the gate may reject).

FAIL-OPEN: the whole run is wrapped — any crash, unreadable HEAD, or parse
failure exits 0 and the commit proceeds unguarded. A guard bug never blocks
work. Registration-side hazard, distinct from this: if settings.json points
at a MISSING hook file, python exits 2, which Claude Code treats as a
blocking error for every matched tool call — register only after this file
exists at the primary-checkout path.

TEST OVERRIDE: env BRANCH_GUARD_ROOT redefines the guarded root for
calibration only. Claude Code does not set it in production; if it ever
appears in settings/env, the guard has been silently retargeted — treat as
tampering.

review-when: (a) hook input schema or tool names change (tool_name strings,
cwd field); (b) the repo stops being local-main-canonical (moves to a
remote/PR flow) — the `main`-only premise dies with it; (c) Claude Code
moves worktrees off `<repo>/.claude/worktrees` or renames the `claude/*`
branch convention (suggested opt-in glob in the deny text goes stale);
(d) a nested repo under ~/.claude (e.g. tools/*) starts routine
feature-branch work — extend opt-in to non-linked gitdirs then, with these
cases as the must-pass suite; (e) a Claude Code update may change the hook
read timing observed 2026-08-27 (settings.json is re-read live — running
sessions affected immediately) — re-verify before relying on either timing.
"""
import fnmatch
import json
import os
import re
import sys
import time

MARKER = "[branch-ok]"
ALLOW_FILENAME = "branch-guard-allow"
LOG_PATH = os.path.join(os.path.expanduser("~"), ".claude", "telemetry",
                        "branch-commit-guard.jsonl")

# Segment separators for the cd/-C walk. Splitting inside quotes is a known
# blunt edge (see KNOWN BOUNDARY above).
SEG_SPLIT = re.compile(r"&&|\|\||;|\||\r?\n")

# A segment that changes directory (bash cd/pushd; PowerShell Set-Location
# and aliases; cmd-style `cd /d`).
CD_RE = re.compile(
    r"^\s*(?:cd|chdir|sl|pushd|set-location|push-location)(?:\.exe)?\s+"
    r"(?:/d\s+)?(?:-(?:path|literalpath)\s+)?"
    r"(?P<arg>\"[^\"]*\"|'[^']*'|\S+)",
    re.I,
)

# `git ... commit` with only global options between; lazy up to the first
# `commit` token (commit-tree and *recommit* excluded by the boundaries).
GIT_RE = re.compile(
    r"(?:^|[\s\"'(`^])git(?:\.exe)?[\"']?\s+(?P<mid>[^\r\n]*?)\bcommit(?![\w-])",
    re.I,
)

TOKEN_RE = re.compile(r"\"[^\"]*\"|'[^']*'|\S+")

# git global options that consume a following argument (-C handled inline).
ARG_OPTS = {"-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix",
            "--config-env", "-e"}


def ncase(p: str) -> str:
    return os.path.normcase(os.path.normpath(p))


def guarded_root() -> str:
    return (os.environ.get("BRANCH_GUARD_ROOT")
            or os.path.join(os.path.expanduser("~"), ".claude"))


def inside(path: str, root: str) -> bool:
    p, r = ncase(path), ncase(root)
    return p == r or p.startswith(r + os.sep)


def parse_commit_target(mid: str, base_dir: str):
    """If `mid` is a plausible run of git global options, return the effective
    directory after folding -C; else None (not a commit invocation)."""
    eff = base_dir
    toks = TOKEN_RE.findall(mid)
    i = 0
    while i < len(toks):
        t = toks[i].strip("\"'")
        if not t:
            i += 1
            continue
        if t == "-C":
            if i + 1 >= len(toks):
                return None
            c = toks[i + 1].strip("\"'")
            eff = os.path.normpath(os.path.join(eff, os.path.expanduser(c)))
            i += 2
            continue
        if t in ARG_OPTS:
            i += 2
            continue
        if t.startswith("--") or (t.startswith("-") and len(t) <= 3):
            i += 1
            continue
        return None  # a bare word between `git` and `commit` -> not a commit
    return eff


def scan(cmd: str, cwd: str):
    """Yield the effective target directory of each git-commit invocation."""
    cur = cwd
    for seg in SEG_SPLIT.split(cmd):
        m = CD_RE.match(seg)
        if m:
            arg = m.group("arg").strip("\"'")
            if arg and arg != "-":
                cur = os.path.normpath(os.path.join(cur, os.path.expanduser(arg)))
            continue
        for gm in GIT_RE.finditer(seg):
            eff = parse_commit_target(gm.group("mid"), cur)
            if eff is not None:
                yield eff


def find_checkout(start: str):
    """Walk up from `start` to the nearest checkout root; (root, gitpath)."""
    cur = os.path.abspath(start)
    while True:
        g = os.path.join(cur, ".git")
        if os.path.isdir(g) or os.path.isfile(g):
            return cur, g
        parent = os.path.dirname(cur)
        if ncase(parent) == ncase(cur):
            return None, None
        cur = parent


def head_info(gitpath: str):
    """Return (branch_or_detached, gitdir, is_linked_worktree)."""
    if os.path.isfile(gitpath):
        with open(gitpath, encoding="utf-8", errors="replace") as fh:
            m = re.search(r"gitdir:\s*(.+)", fh.read())
        if not m:
            return None, None, True
        gd = m.group(1).strip()
        if not os.path.isabs(gd):
            gd = os.path.normpath(os.path.join(os.path.dirname(gitpath), gd))
        linked = True
    else:
        gd, linked = gitpath, False
    with open(os.path.join(gd, "HEAD"), encoding="utf-8", errors="replace") as fh:
        ref = fh.read().strip()
    if ref.startswith("ref: refs/heads/"):
        return ref[len("ref: refs/heads/"):], gd, linked
    return "(detached: %s)" % ref[:12], gd, linked


def optin_patterns(gd: str):
    path = os.path.join(gd, ALLOW_FILENAME)
    try:
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as fh:
                return [ln.strip() for ln in fh.read().splitlines()
                        if ln.strip() and not ln.strip().startswith("#")]
    except Exception:
        pass
    return []


def record(payload, verdict, target, branch, cmd):
    """Persist before the veto. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "session": payload.get("session_id", ""),
                "cwd": payload.get("cwd", ""),
                "verdict": verdict,          # deny | pass-marker | pass-optin
                "target": target,
                "branch": branch,
                "command": cmd,              # recovery copy (message travels here)
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def deny(target, branch):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked by branch-commit guard: the target checkout {target} "
                f"is on branch '{branch}', not 'main'. Exactly this shape put "
                "commits c5468e6/f61b226 on peer sessions' branches "
                "(2026-08-27: a peer switched the primary checkout's branch "
                "mid-turn). The full command was saved to "
                "telemetry/branch-commit-guard.jsonl. If this branch IS the "
                "one you intend: (a) verify it in THIS turn (git branch "
                f"--show-current), then re-run with the literal marker {MARKER} "
                "in the command or message; or (b) in a worktree you own, opt "
                "in once for the branches you own: echo 'claude/*' > "
                "\"$(git rev-parse --git-dir)/branch-guard-allow\" (one glob "
                "per line; PowerShell: 'claude/*' | Set-Content ...). The "
                "PRIMARY checkout takes no opt-in — its branch is shared "
                "mutable state; marker only."
            ),
        }
    }))
    sys.exit(0)


def run(payload) -> None:
    tool = str(payload.get("tool_name", ""))
    if tool not in ("Bash", "PowerShell"):
        sys.exit(0)
    cmd = str((payload.get("tool_input") or {}).get("command", ""))
    low = cmd.lower()
    if not cmd or "git" not in low or "commit" not in low:
        sys.exit(0)
    cwd = str(payload.get("cwd", "") or os.getcwd())
    root = guarded_root()
    has_marker = MARKER.lower() in low
    seen = set()
    for target in scan(cmd, cwd):
        ck_root, gitpath = find_checkout(target)
        if not ck_root or not inside(ck_root, root):
            continue
        if ncase(ck_root) in seen:
            continue
        seen.add(ncase(ck_root))
        branch, gd, linked = head_info(gitpath)
        if branch is None or branch == "main":
            continue
        if has_marker:
            record(payload, "pass-marker", ck_root, branch, cmd)
            continue
        if linked and gd:
            pats = optin_patterns(gd)
            if any(fnmatch.fnmatchcase(branch, p) for p in pats):
                record(payload, "pass-optin", ck_root, branch, cmd)
                continue
        record(payload, "deny", ck_root, branch, cmd)
        deny(ck_root, branch)
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        run(payload)
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail-open: a guard bug never blocks work


if __name__ == "__main__":
    main()
