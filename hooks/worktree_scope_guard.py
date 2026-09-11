r"""SessionStart announcement + PreToolUse DENY guard for linked git worktrees.

STATUS: LIVE since 2026-09-08 (claude-config). Enforces `ops/rule-registry.md`
key `WORKTREE_SCOPE` — the properties `ops/references/shared-tree-git.md` §1a
states for the asset class "a linked worktree of ~/.claude" (user ruling
2026-09-08: handle it at the source). Born from the repeat report that sessions hand out
`~/.claude/...` paths that do not resolve: the Desktop app places every parallel
session on a git repo in a pooled worktree before the first prompt, and from
inside a worktree the copy is indistinguishable from the canonical tree. Three
things silently differ, and each half of this hook covers them:

  SessionStart (matcher "", every session):
    - cwd inside a LINKED worktree (any repo): prints the worktree, its branch,
      the canonical checkout, the branch's unmerged-commit count and the ignored
      state dirs present, plus the merge-to-finish fact. For the governed repo
      (~/.claude) it adds the runtime-loads-from-canonical fact.
    - cwd inside a PRIMARY checkout with linked worktrees: one line per
      worktree with +unmerged / dirty / ignored-state, so a stranded branch is
      visible before anyone hands out a path.
    - cwd inside a PRIMARY checkout whose worktree POOL holds a directory git
      does not name: that directory is announced as RESIDUE, whether or not any
      linked worktree still exists. Added 2026-09-09: `git worktree remove` on
      Windows empties the tree and drops its own admin directory, then fails to
      unlink the last one when another session holds it as cwd -- and reports
      `Permission denied`, a hard error after the work is done (L-063). What is
      left is worktree-SHAPED and, until this line existed, completely silent:
      `git worktree list` names nothing, so the announce returned "". A reader
      running `ls` then had two available readings, both wrong -- "live
      worktrees the guard missed" and "the guard is broken". An empty orphan
      needs nothing from anyone; a `(NOT empty)` one holds files no branch
      carries and is read before it is removed.
      Silent only when there are neither worktrees nor residue.
  PreToolUse (matcher "Write|Edit|NotebookEdit|Bash|PowerShell"):
    - Write/Edit/NotebookEdit whose target lies inside a linked worktree of the
      governed repo AND is a path git ignores there → DENY (ignored paths never
      merge; the write is stranded by construction). Names the canonical target.
    - Bash/PowerShell whose cwd is such a worktree and whose command runs a
      state-building tool (`gsnap.py build|verify|emit-moc|bench`, `xi.py
      emit|register|union`) by RELATIVE path → DENY (the tool resolves its root
      from its own file, so its out/ lands in the worktree). Absolute canonical
      path, a `cd <canonical>` earlier in the command, or the literal marker
      [worktree-ok] passes.
    - Everything else, every other repo's worktree, and the canonical tree
      itself pass silently. Tracked-path writes in a worktree are the
      worktree's purpose and are never gated.

SEVERITY: DENY for the two determinable classes above (gate-severity-by-consumer:
a stranded write is silent and costs a later session a search that finds
nothing). ANNOUNCE for everything the hook can only describe. Fail-OPEN on every
internal error path (unparsable stdin, git missing or slow, any exception): exit
0, empty stdout, best-effort telemetry row `decision: error`.

ESCAPES (each leaves a trace): opt-in file `<worktree gitdir>/worktree-scope-allow`
(same shape as branch_commit_guard's opt-in; lives in the worktree's private
gitdir, dies with the worktree) lifts the write deny for that worktree; the
marker [worktree-ok] in a shell command lifts the builder deny for that call.
Both are self-certified, as branch_commit_guard's are, and are logged as
`pass-optin` / `pass-marker` so habituation is watchable.

TEST OVERRIDES (calibration only; Claude Code never sets them): env WSG_HOME
redefines the governed canonical root, WSG_LOG the announce/verdict log. If either
appears in settings/env the guard has been retargeted — treat as tampering.

TELEMETRY: `telemetry/worktree-scope-guard.jsonl` — one row per announce, deny,
pass-optin, pass-marker or error; deny rows carry the receipt nonce quoted in the
message (deny_receipt). Allowed writes are not logged.

KNOWN BOUNDARIES (accepted, labelled): a shell redirect or a python one-liner
that writes into an ignored worktree path is not matched (Write/Edit/NotebookEdit
only, the measured failure shape); `cd` targets with env vars are not expanded
(branch_commit_guard FP-1 shape); a builder invoked through a wrapper script is
not seen; a worktree whose gitdir lacks `commondir` and lives outside
`<repo>/.git/worktrees/` resolves its canonical root by the gitdir's parent
layout only.

FALSE-POSITIVE LOG: none observed as of 2026-09-08 (born today). At 3 observed
misfires narrow the condition (drop the tool that misfired, or require the
target to be under a STATE_DIRS prefix as well as ignored) rather than widening
the escape. A hook with no log has never been measured, which is not the same
as never having misfired.

Proof-of-life: `python hooks/worktree_scope_guard.py --selftest` (two-sided, real
temp repos, last line `ALL PASS n/n`; 37 cases as of 2026-09-09). R-1..R-7 pin
the residue half two-sided: a pooled directory git DOES name never appears in
the residue clause (R-1), an empty orphan does (R-2/R-3), a non-empty one is
labelled (R-4), the zero-worktrees-plus-residue shape the mechanism exists for
is NOT silent (R-5), a repo with no pool gets no clause (R-6), and removing the
pool returns the plain worktree line (R-7). Inverted at `POOL_DIRS = ()` and
observed failing R-1..R-5 before it shipped. U-1/U-1b/U-2 pin the AP-62 half: with
`git()` returning its (None, "") "cannot answer", the write that P-1 denies is
ALLOWED and the announcement prints `?` for the counts git was the only source
for -- an unknown ahead-count folded into "0 commit(s) ahead" would read as a
branch safe to discard. Registered in
`ops/references/integrity-sweep.md` check 30.
review-when: (a) the Desktop app moves worktrees off `<repo>/.claude/worktrees`
or ships a per-repo off switch (the announcement stays right, the ruling in
shared-tree-git §1a may relax); (b) hook input schema or tool names change
(`tool_name`, `cwd`, `file_path`/`notebook_path`); (c) a new state-building
tool with a gitignored out/ appears under tools/ — add it to BUILDER; (d) git
changes the linked-worktree layout (`.git` file + `gitdir:` + `commondir`);
(e) a second worktree pool location appears (another host app, or the user
placing one by hand) — add it to POOL_DIRS, which is the single edit point;
(f) `git worktree remove` stops leaving the directory behind on Windows (a git
release note, or the failure stops reproducing) — R-5's shape would then be
unreachable in practice and the clause could be reconsidered, but do not delete
it on the strength of one clean run.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

HOOK = "worktree_scope_guard"
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
MARKER = "[worktree-ok]"
ALLOW_FILENAME = "worktree-scope-allow"
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
# Ignored state classes a worktree can hold; checked by existence (cheap) for
# the announcement. The DENY uses `git check-ignore`, not this list.
STATE_DIRS = ("cache", "drafts", "backups", "telemetry", "tools/graph-snapshot/out",
              "tools/cross-index/out", "projects")
# State-building tools whose out/ is gitignored and whose root is __file__-relative.
BUILDER = re.compile(
    r"(?P<pre>[^\s\"'=]*?)(?P<tool>gsnap\.py|xi\.py)[\"']?\s+"
    r"(?P<sub>build|verify|emit-moc|bench|emit|register|union)\b")
SEG_SPLIT = re.compile(r"&&|\|\||;|\r?\n")
CD_SEG = re.compile(r"^\s*(?:cd|pushd|Set-Location|sl)\s+(?:/d\s+)?[\"']?([^\"';&|]+?)[\"']?\s*$",
                    re.IGNORECASE)
GIT_TIMEOUT = 4
ANNOUNCE_MAX = 1400

# Where the Desktop app pools its per-session worktrees, relative to a repo root.
# Scanned for RESIDUE: a directory here that `git worktree list` does not name.
# See `residue()` for why an empty directory is worth a line.
POOL_DIRS = (os.path.join(".claude", "worktrees"),)


def home_root() -> str:
    return os.path.abspath(os.environ.get("WSG_HOME") or str(CLAUDE_DIR))


def log_path() -> Path:
    # Precedence: WSG_LOG (per-hook override) > CLAUDE_TELEMETRY_DIR (suite
    # redirect; production never sets it) > default.
    return Path(os.environ.get("WSG_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "worktree-scope-guard.jsonl"))


def ncase(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def git(args, cwd, timeout=GIT_TIMEOUT):
    """(returncode, stdout) — (None, "") on any failure, never raises."""
    try:
        r = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True,
                           text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout
    except Exception:
        return None, ""


def find_checkout(start: str):
    """Walk up from `start` to the nearest `.git` (dir or file); (root, gitpath)."""
    cur = os.path.abspath(start)
    while True:
        g = os.path.join(cur, ".git")
        if os.path.isdir(g) or os.path.isfile(g):
            return cur, g
        parent = os.path.dirname(cur)
        if ncase(parent) == ncase(cur):
            return None, None
        cur = parent


def checkout_info(start: str):
    """-> {root, gitdir, linked, canonical, branch} or None."""
    root, g = find_checkout(start)
    if not root:
        return None
    linked, gd, canonical = False, g, root
    if os.path.isfile(g):
        try:
            with open(g, encoding="utf-8", errors="replace") as fh:
                m = re.search(r"gitdir:\s*(.+)", fh.read())
        except OSError:
            return None
        if not m:
            return None
        gd = m.group(1).strip()
        if not os.path.isabs(gd):
            gd = os.path.normpath(os.path.join(root, gd))
        linked = True
        common = os.path.dirname(os.path.dirname(gd))       # <repo>/.git/worktrees/<n> -> <repo>/.git
        try:
            with open(os.path.join(gd, "commondir"), encoding="utf-8") as fh:
                cd = fh.read().strip()
            if cd:
                common = cd if os.path.isabs(cd) else os.path.normpath(os.path.join(gd, cd))
        except OSError:
            pass
        canonical = os.path.dirname(common) if os.path.basename(common) == ".git" else common
    branch = None
    try:
        with open(os.path.join(gd, "HEAD"), encoding="utf-8", errors="replace") as fh:
            ref = fh.read().strip()
        branch = ref[len("ref: refs/heads/"):] if ref.startswith("ref: refs/heads/") \
            else "(detached %s)" % ref[:10]
    except OSError:
        pass
    return {"root": root, "gitdir": gd, "linked": linked, "canonical": canonical, "branch": branch}


def governed(info) -> bool:
    return bool(info) and info["linked"] and ncase(info["canonical"]) == ncase(home_root())


def is_ignored(wt_root: str, target: str) -> bool:
    rc, _ = git(["check-ignore", "-q", "--", target], cwd=wt_root)
    return rc == 0


def opted_in(gitdir: str) -> bool:
    try:
        return os.path.isfile(os.path.join(gitdir, ALLOW_FILENAME))
    except Exception:
        return False


def default_branch(root: str) -> str:
    rc, out = git(["symbolic-ref", "--short", "HEAD"], cwd=root)
    return out.strip() if rc == 0 and out.strip() else "main"


def ahead_count(root: str, base: str, tip: str):
    rc, out = git(["rev-list", "--count", f"{base}..{tip}"], cwd=root)
    return int(out.strip()) if rc == 0 and out.strip().isdigit() else "?"


def dirty_count(wt: str):
    rc, out = git(["status", "--porcelain"], cwd=wt)
    return len([ln for ln in out.splitlines() if ln.strip()]) if rc == 0 else "?"


def state_present(wt: str):
    return [d + "/" for d in STATE_DIRS if os.path.isdir(os.path.join(wt, d))]


def cd_to_canonical(cmd: str, before: int) -> bool:
    """True if a segment BEFORE offset `before` changes directory to the governed root."""
    head = cmd[:before]
    for seg in SEG_SPLIT.split(head):
        m = CD_SEG.match(seg)
        if m:
            try:
                if ncase(os.path.expanduser(m.group(1).strip())) == ncase(home_root()):
                    return True
            except Exception:
                pass
    return False


# ---------------------------------------------------------------- verdict (pure)

def decide(payload: dict) -> tuple:
    """-> (verdict, facts). verdicts: allow | pass-optin | pass-marker | deny-write | deny-shell.
    Pure apart from read-only git calls; never writes telemetry."""
    tool = str(payload.get("tool_name", ""))
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return "allow", {}
    cwd = str(payload.get("cwd") or "") or os.getcwd()
    if tool in WRITE_TOOLS:
        fp = ti.get("file_path") or ti.get("notebook_path")
        if not isinstance(fp, str) or not fp:
            return "allow", {}
        target = fp if os.path.isabs(fp) else os.path.join(cwd, fp)
        info = checkout_info(os.path.dirname(target))
        if not governed(info):
            return "allow", {}
        facts = {"tool": tool, "target": target, "wt": info["root"], "branch": info["branch"],
                 "canonical": info["canonical"], "gitdir": info["gitdir"]}
        if opted_in(info["gitdir"]):
            return "pass-optin", facts
        if is_ignored(info["root"], target):
            rel = os.path.relpath(target, info["root"])
            facts["canonical_target"] = os.path.join(info["canonical"], rel)
            return "deny-write", facts
        return "allow", {}
    if tool in SHELL_TOOLS:
        cmd = ti.get("command")
        if not isinstance(cmd, str) or not cmd:
            return "allow", {}
        m = BUILDER.search(cmd)
        if not m:
            return "allow", {}
        if re.match(r"^(?:[A-Za-z]:[/\\]|/|~)", m.group("pre")):
            return "allow", {}                       # absolute invocation
        if cd_to_canonical(cmd, m.start()):
            return "allow", {}
        info = checkout_info(cwd)
        if not governed(info):
            return "allow", {}
        facts = {"tool": tool, "invocation": m.group("pre") + m.group("tool") + " " + m.group("sub"),
                 "builder": m.group("tool"), "sub": m.group("sub"), "wt": info["root"],
                 "branch": info["branch"], "canonical": info["canonical"], "gitdir": info["gitdir"],
                 "command": cmd[:300]}
        if MARKER in cmd:
            return "pass-marker", facts
        return "deny-shell", facts
    return "allow", {}


# ---------------------------------------------------------------- announcement

def residue(root: str, known: list[str]) -> list[str]:
    """Directories in a worktree pool that `git worktree list` does not name.

    They are what `git worktree remove` leaves behind on Windows when another
    session still holds the path as its cwd: git empties the tree and drops its
    own admin directory, then fails to unlink the last one and reports
    `Permission denied` — a hard error AFTER the work is done (L-063).

    Why an EMPTY directory earns a line: without one, the canonical-tree
    announce is silent (git names no linked worktree) while four
    worktree-shaped directories sit under the pool. Both readings a person can
    make of that are wrong — "these are live worktrees the guard missed" and
    "the guard is broken" — and the residue is indistinguishable from a live
    worktree by `ls` alone. Naming it is the difference between state that is
    gone and state that merely looks present.
    """
    seen = {os.path.normcase(os.path.abspath(p)) for p in known}
    out = []
    for pool in POOL_DIRS:
        base = os.path.join(root, pool)
        try:
            entries = sorted(os.scandir(base), key=lambda e: e.name)
        except OSError:
            continue
        for e in entries:
            try:
                if not e.is_dir():
                    continue
            except OSError:
                continue
            if os.path.normcase(os.path.abspath(e.path)) in seen:
                continue
            try:
                empty = not any(os.scandir(e.path))
            except OSError:
                empty = False
            rel = f"{pool}/{e.name}".replace("\\", "/")
            out.append(rel + ("" if empty else " (NOT empty)"))
    return out


def announce(cwd: str) -> str:
    info = checkout_info(cwd)
    if not info:
        return ""
    if info["linked"]:
        canon, wt, b = info["canonical"], info["root"], info["branch"] or "?"
        main = default_branch(canon)
        ahead = ahead_count(canon, main, b) if not b.startswith("(") else "?"
        dirty = dirty_count(wt)
        present = state_present(wt)
        text = (
            f"[worktree-scope] worktree_scope_guard (a local SessionStart hook): this session's cwd "
            f"is the LINKED WORKTREE {wt} on branch {b}; the canonical checkout is {canon} ({main}); "
            f"{b} is {ahead} commit(s) ahead of {main}, worktree dirty count {dirty}. Tracked files "
            f"written or committed here reach {canon} only after {b} is merged — until then only the "
            f"worktree path resolves, and a close-out here ends with the ff-merge onto {main} from "
            f"{canon}, not with the commit. Gitignored paths here never merge (present now: "
            f"{', '.join(present) if present else 'none'}); that class is written under {canon}."
        )
        if governed(info):
            text += (
                f" Hooks, skills and rules load from {canon}, never from this copy; live-environment "
                f"verification does not run here. This hook's PreToolUse half denies Write/Edit into an "
                f"ignored path here and denies gsnap.py/xi.py state builds by relative path (an absolute "
                f"canonical path, or the marker {MARKER} in the command, passes)."
            )
        text += f" ExitWorktree moves this session to {canon}."
        return text[:ANNOUNCE_MAX]
    # primary checkout: list its linked worktrees
    rc, out = git(["worktree", "list", "--porcelain"], cwd=info["root"])
    if rc != 0:
        return ""
    entries, cur = [], {}
    for ln in out.splitlines() + [""]:
        if not ln.strip():
            if cur:
                entries.append(cur)
            cur = {}
            continue
        k, _, v = ln.partition(" ")
        cur[k] = v
    linked = [e for e in entries[1:] if e.get("worktree")]
    orphans = residue(info["root"], [e["worktree"] for e in entries if e.get("worktree")])
    if not linked and not orphans:
        return ""
    if not linked:
        return (f"[worktree-scope] no linked worktree of {info['root']} exists, but its pool still "
                f"holds {len(orphans)} director{'y' if len(orphans) == 1 else 'ies'} git does not "
                f"know about: {'; '.join(orphans)} — "
                f"residue, not a worktree. An EMPTY one is a `git worktree remove` whose last unlink "
                f"failed because another session holds it as cwd; it disappears when that session "
                f"closes and needs nothing from you. A `(NOT empty)` one holds files no branch "
                f"carries: read it before removing it."[:ANNOUNCE_MAX])
    main = default_branch(info["root"])
    parts = []
    for e in linked[:12]:
        path = e["worktree"]
        b = e.get("branch", "").replace("refs/heads/", "") or ("detached" if "detached" in e else "?")
        tip = e.get("HEAD", "")
        ahead = ahead_count(info["root"], main, tip) if tip else "?"
        dirty = dirty_count(path) if os.path.isdir(path) else "missing"
        present = state_present(path) if os.path.isdir(path) else []
        parts.append(f"{os.path.basename(path)} (branch {b}, +{ahead} unmerged, dirty {dirty}, "
                     f"ignored state: {', '.join(present) if present else 'none'})")
    text = (f"[worktree-scope] {len(linked)} linked worktree(s) of {info['root']} still exist: "
            + "; ".join(parts) + f" — a branch with unmerged commits holds files no path under "
            f"{info['root']} resolves; a worktree with ignored state holds builds {info['root']} "
            f"does not have.")
    if orphans:
        text += (f" Also in the pool, git does not know about: {'; '.join(orphans)} — residue, "
                 f"not worktrees (an empty one is a removal whose last unlink lost a race with "
                 f"another session's cwd).")
    return text[:ANNOUNCE_MAX]


# ---------------------------------------------------------------- output + log

def log_row(row: dict) -> None:
    try:
        p = log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def deny_message(verdict: str, f: dict) -> str:
    if verdict == "deny-write":
        allow_path = os.path.join(f["gitdir"], ALLOW_FILENAME)
        return (
            f"{f['tool']} denied by worktree_scope_guard, a local PreToolUse hook (not file or page "
            f"content): the target {f['target']} matched git's ignore rules inside the linked worktree "
            f"{f['wt']} (branch {f['branch']}) of {f['canonical']}. An ignored path never merges, so "
            f"whatever lands there stays in the worktree and cannot be found from {f['canonical']}. "
            f"To proceed: write the same file under the canonical tree — {f['canonical_target']} — "
            f"or, when this worktree's ignored state is deliberately kept local, opt in once with "
            f"echo ok > \"{allow_path}\" (PowerShell: 'ok' | Set-Content \"{allow_path}\") and re-run "
            f"the write."
            + _receipt(HOOK, target=f["target"], worktree=f["wt"], canonical=f["canonical"])
            + _fp(HOOK)
        )
    canon_tool = os.path.join(f["canonical"], "tools",
                              "graph-snapshot" if f["builder"] == "gsnap.py" else "cross-index",
                              f["builder"])
    return (
        f"{f['tool']} denied by worktree_scope_guard, a local PreToolUse hook (not file or page "
        f"content): this command runs {f['invocation']} by a relative path while the shell's cwd "
        f"{f['wt']} (branch {f['branch']}) is a linked worktree of {f['canonical']}. That tool resolves "
        f"its root from its own file, so its out/ would be built inside the worktree and never reach "
        f"{f['canonical']}. To proceed: run the canonical copy by absolute path — python "
        f"{canon_tool} {f['sub']} — or re-run with the literal marker {MARKER} in the command when "
        f"the worktree's own out/ is what you want."
        + _receipt(HOOK, invocation=f["invocation"], worktree=f["wt"], canonical=f["canonical"])
        + _fp(HOOK)
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)
    session = str(payload.get("session_id") or "")
    event = str(payload.get("hook_event_name") or ("PreToolUse" if "tool_name" in payload else "SessionStart"))
    try:
        if event == "SessionStart":
            text = announce(str(payload.get("cwd") or "") or os.getcwd())
            if text:
                log_row({"ts": int(time.time()), "session": session, "decision": "announce",
                         "cwd": str(payload.get("cwd") or "")[:200], "chars": len(text)})
                try:
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
                print(text)
        elif event == "PreToolUse":
            verdict, facts = decide(payload)
            if verdict in ("pass-optin", "pass-marker"):
                log_row({"ts": int(time.time()), "session": session, "decision": verdict,
                         "tool": facts.get("tool", ""),
                         "target": str(facts.get("target") or facts.get("invocation") or "")[:200]})
            elif verdict.startswith("deny"):
                log_row({"ts": int(time.time()), "session": session, "decision": verdict,
                         "tool": facts.get("tool", ""),
                         "target": str(facts.get("target") or facts.get("invocation") or "")[:200],
                         "worktree": facts.get("wt", "")[:200]})
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": deny_message(verdict, facts)}}))
    except SystemExit:
        raise
    except Exception as e:
        log_row({"ts": int(time.time()), "session": session, "decision": "error",
                 "error": repr(e)[:200]})
    sys.exit(0)


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    """Two-sided controls on REAL temp repos (git required). Positive cases must deny or
    announce; every one has a negative twin that must pass silently. Telemetry and the
    governed root are redirected into the temp dir (WSG_HOME / WSG_LOG / CLAUDE_CONFIG_DIR)
    so no row leaks into production (integrity-sweep check 20's lesson)."""
    import shutil
    import tempfile
    results = []

    def check(cid, cond, detail=""):
        results.append((cid, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'} {cid} {detail[:110]}")

    def sh(args, cwd):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
                              + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")

    def mkrepo(path):
        os.makedirs(os.path.join(path, "references"))
        os.makedirs(os.path.join(path, "tools", "graph-snapshot"))
        with open(os.path.join(path, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("cache/\ndrafts/\ntools/graph-snapshot/out/\ntelemetry/\n")
        with open(os.path.join(path, "references", "a.md"), "w", encoding="utf-8") as fh:
            fh.write("a\n")
        with open(os.path.join(path, "tools", "graph-snapshot", "gsnap.py"), "w", encoding="utf-8") as fh:
            fh.write("# stub\n")
        sh(["init", "-q", "-b", "main"], path)
        sh(["add", "-A"], path)
        sh(["commit", "-q", "-m", "init"], path)

    tmp = tempfile.mkdtemp(prefix="wsg-ctl-")
    old_env = {k: os.environ.get(k) for k in ("WSG_HOME", "WSG_LOG", "CLAUDE_CONFIG_DIR")}
    try:
        canon = os.path.join(tmp, "canon")
        other = os.path.join(tmp, "other")
        cfg = os.path.join(tmp, "cfg")
        os.makedirs(cfg)
        mkrepo(canon)
        mkrepo(other)
        os.environ["WSG_HOME"] = canon
        os.environ["WSG_LOG"] = os.path.join(cfg, "wsg.jsonl")

        # N-12 first: canonical with no linked worktree announces nothing.
        check("N-12", announce(canon) == "", "primary checkout without worktrees: silent")
        check("N-11", announce(tmp) == "", "no repo at all: silent")

        wt = os.path.join(tmp, "wt")
        r = sh(["worktree", "add", "-q", "-b", "claude/test", wt, "main"], canon)
        check("setup", r.returncode == 0, "git worktree add: " + (r.stderr.strip()[:80] or "ok"))
        owt = os.path.join(tmp, "owt")
        sh(["worktree", "add", "-q", "-b", "claude/other", owt, "main"], other)
        os.makedirs(os.path.join(wt, "cache"), exist_ok=True)

        def call(tool, inp, cwd):
            return decide({"tool_name": tool, "tool_input": inp, "cwd": cwd})[0]

        # POSITIVE — deny
        check("P-1", call("Write", {"file_path": os.path.join(wt, "cache", "x.json"), "content": "1"}, wt) == "deny-write",
              "Write into an ignored path of the governed worktree")
        check("P-2", call("Edit", {"file_path": os.path.join(wt, "drafts", "d.md"), "old_string": "a", "new_string": "b"}, wt) == "deny-write",
              "Edit into an ignored path that does not exist yet")
        check("P-3", call("NotebookEdit", {"notebook_path": os.path.join(wt, "cache", "n.ipynb")}, wt) == "deny-write",
              "NotebookEdit path field")
        check("P-4", call("Bash", {"command": "python tools/graph-snapshot/gsnap.py build"}, wt) == "deny-shell",
              "relative gsnap build from the worktree")
        check("P-5", call("PowerShell", {"command": "python -X utf8 tools\\cross-index\\xi.py emit"}, wt) == "deny-shell",
              "relative xi emit from the worktree (backslashes)")
        check("P-6", call("Write", {"file_path": "cache/rel.json", "content": "1"}, wt) == "deny-write",
              "relative file_path resolved against the worktree cwd")
        a = announce(wt)
        check("P-7", "LINKED WORKTREE" in a and canon in a and "claude/test" in a and "+" not in a.split("ahead")[0][-3:],
              "worktree announcement names worktree, branch, canonical")
        check("P-8", "0 commit(s) ahead" in a and "cache/" in a, "announcement: ahead count + ignored state present")
        with open(os.path.join(wt, "references", "b.md"), "w", encoding="utf-8") as fh:
            fh.write("b\n")
        sh(["add", "-A"], wt)
        sh(["commit", "-q", "-m", "wt commit"], wt)
        b = announce(canon)
        check("P-9", b.startswith("[worktree-scope] 1 linked worktree") and "+1 unmerged" in b and "claude/test" in b,
              "primary announcement lists the worktree with +1 unmerged")

        # RESIDUE (R-*) — a pool directory git does not name. Two-sided: the
        # negative control puts a LIVE worktree in the same pool, so "the pool
        # is scanned at all" and "residue is reported" are distinguishable; a
        # scan that reported every pool entry would fail R-1.
        pool = os.path.join(canon, ".claude", "worktrees")
        live = os.path.join(pool, "live-one")
        os.makedirs(pool, exist_ok=True)
        sh(["worktree", "add", "-q", "-b", "claude/pooled", live, "main"], canon)
        empty_orphan = os.path.join(pool, "gone-empty")
        os.makedirs(empty_orphan, exist_ok=True)
        r1 = announce(canon)
        r1_res = r1.split("git does not know about:")[1] if "git does not know about:" in r1 else ""
        check("R-1", bool(r1_res) and "live-one" not in r1_res,
              "a pooled directory git DOES name is absent from the residue clause")
        check("R-2", "gone-empty" in r1_res and "residue" in r1,
              "an empty pool directory git does not name is reported as residue")
        # Read the label that FOLLOWS the name, without assuming the name is
        # there: on an inverted build the suite must FAIL, never raise — a
        # control that stops the run takes every later case down with it.
        after = r1_res.split("gone-empty", 1)[1][:20] if "gone-empty" in r1_res else "(NOT empty)"
        check("R-3", "(NOT empty)" not in after,
              "the empty one is not labelled NOT empty")
        left_orphan = os.path.join(pool, "gone-full")
        os.makedirs(left_orphan, exist_ok=True)
        with open(os.path.join(left_orphan, "leftover.txt"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        r2 = announce(canon)
        check("R-4", "gone-full (NOT empty)" in r2,
              "a non-empty orphan is flagged NOT empty — it holds files no branch carries")
        # The shape this whole mechanism exists for: git names NOTHING, residue remains.
        sh(["worktree", "remove", "--force", live], canon)
        sh(["worktree", "remove", "--force", wt], canon)
        r3 = announce(canon)
        check("R-5", r3.startswith("[worktree-scope] no linked worktree") and "gone-empty" in r3,
              "with zero linked worktrees the announce is NOT silent while residue remains")
        check("R-6", "residue" not in announce(other),
              "a repo with a worktree but NO pool directory gets no residue clause")
        sh(["worktree", "add", "-q", "--force", wt, "claude/test"], canon)
        sh(["branch", "-D", "claude/pooled"], canon)
        import shutil as _shutil
        _shutil.rmtree(pool, ignore_errors=True)
        check("R-7", announce(canon).startswith("[worktree-scope] 1 linked worktree"),
              "with the pool gone the announce returns to the plain worktree line")

        # NEGATIVE — allow
        check("N-1", call("Write", {"file_path": os.path.join(wt, "references", "c.md"), "content": "c"}, wt) == "allow",
              "tracked-class path in the worktree passes (the worktree's purpose)")
        check("N-2", call("Write", {"file_path": os.path.join(canon, "cache", "x.json"), "content": "1"}, canon) == "allow",
              "ignored path in the CANONICAL tree passes")
        check("N-3", call("Bash", {"command": "git status --porcelain"}, wt) == "allow", "ordinary shell in the worktree")
        check("N-4", call("Bash", {"command": "python tools/graph-snapshot/gsnap.py build " + MARKER}, wt) == "pass-marker",
              "marker lifts the builder deny (logged)")
        check("N-5", call("Bash", {"command": "python tools/graph-snapshot/gsnap.py build"}, canon) == "allow",
              "builder from the canonical cwd")
        check("N-6", call("Bash", {"command": f"python {canon}/tools/graph-snapshot/gsnap.py build"}, wt) == "allow",
              "absolute canonical invocation from the worktree")
        check("N-7", call("Bash", {"command": f"cd {canon} && python tools/graph-snapshot/gsnap.py build"}, wt) == "allow",
              "cd to canonical earlier in the command")
        check("N-8", call("Write", {"file_path": os.path.join(owt, "cache", "x.json"), "content": "1"}, owt) == "allow",
              "another repo's worktree is announce-only, never denied")
        check("N-9", decide({"tool_name": "Write"})[0] == "allow", "malformed payload passes (fail-open)")
        check("N-10", call("Bash", {"command": "python tools/graph-snapshot/gsnap.py query x"}, wt) == "allow",
              "read-only subcommand is not a builder")
        info = checkout_info(wt)
        with open(os.path.join(info["gitdir"], ALLOW_FILENAME), "w", encoding="utf-8") as fh:
            fh.write("ok\n")
        check("N-13", call("Write", {"file_path": os.path.join(wt, "cache", "x.json"), "content": "1"}, wt) == "pass-optin",
              "opt-in file lifts the write deny (logged)")
        os.remove(os.path.join(info["gitdir"], ALLOW_FILENAME))

        # UNDETERMINED (AP-62). `git()` returns (None, "") when it cannot answer
        # — git missing, slow, or broken. That is this guard's unclassifiable
        # input: with no answer, whether the target is a linked worktree of the
        # governed repo is UNKNOWN, and an unknown must not be folded into
        # "yes, deny". U-1 feeds the exact payload P-1 denies, with git silenced;
        # U-2 is its twin, proving the case is capable of failing (without it,
        # U-1 would also pass on a guard that had simply stopped denying).
        undet_payload = {"file_path": os.path.join(wt, "cache", "x.json"), "content": "1"}
        real_git = globals()["git"]
        globals()["git"] = lambda *a, **k: (None, "")
        try:
            check("U-1", call("Write", undet_payload, wt) == "allow",
                  "git cannot answer -> undetermined -> allow, never deny")
            # The announcement still fires — that the cwd is a linked worktree
            # is decidable from the gitdir alone. What git was the only source
            # for is printed as `?`, NOT as 0: an unknown ahead-count folded
            # into "0 commit(s) ahead" would read as a branch safe to discard.
            a_undet = announce(wt)
            check("U-1b", "? commit(s) ahead" in a_undet and "dirty count ?" in a_undet,
                  f"counts git could not supply print as ?, never as 0: "
                  f"{a_undet[a_undet.find('is ?') - 12:][:60]!r}")
        finally:
            globals()["git"] = real_git
        check("U-2", call("Write", undet_payload, wt) == "deny-write",
              "the same call denies again once git answers (U-1's positive twin)")

        # SUBPROCESS — the whole invocation path, telemetry redirected.
        # CLAUDE_CONFIG_DIR=cfg is this block's own isolation for the deny
        # receipt (S-1 asserts it lands under cfg/telemetry); an inherited
        # CLAUDE_TELEMETRY_DIR now outranks that in deny_receipt.py and would
        # steer the receipt elsewhere, so drop it here.
        env = dict(os.environ, WSG_HOME=canon, WSG_LOG=os.path.join(cfg, "wsg.jsonl"), CLAUDE_CONFIG_DIR=cfg)
        env.pop("CLAUDE_TELEMETRY_DIR", None)
        me = os.path.abspath(__file__)
        p = subprocess.run([sys.executable, me], input=json.dumps({
            "hook_event_name": "PreToolUse", "session_id": "selftest", "tool_name": "Write", "cwd": wt,
            "tool_input": {"file_path": os.path.join(wt, "cache", "sub.json"), "content": "1"}}),
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        out = p.stdout
        receipt_ok = os.path.isfile(os.path.join(cfg, "telemetry", "worktree-scope-guard.jsonl"))
        check("S-1", '"permissionDecision": "deny"' in out and "worktree_scope_guard" in out and receipt_ok,
              "subprocess deny JSON + receipt row in the redirected telemetry dir")
        p2 = subprocess.run([sys.executable, me], input=json.dumps({
            "hook_event_name": "SessionStart", "session_id": "selftest", "cwd": wt, "source": "startup"}),
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        check("S-2", p2.stdout.startswith("[worktree-scope]") and canon in p2.stdout,
              "subprocess SessionStart announcement")
        p3 = subprocess.run([sys.executable, me], input=json.dumps({
            "hook_event_name": "PreToolUse", "session_id": "selftest", "tool_name": "Write", "cwd": canon,
            "tool_input": {"file_path": os.path.join(canon, "cache", "sub.json"), "content": "1"}}),
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        check("S-3", p3.stdout.strip() == "" and p3.returncode == 0, "subprocess: canonical write passes silently")
        p4 = subprocess.run([sys.executable, me], input="not json", capture_output=True, text=True,
                            encoding="utf-8", env=env, timeout=30)
        check("S-4", p4.stdout.strip() == "" and p4.returncode == 0, "subprocess: garbage stdin exits 0 silently")
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for repo, w in ((canon, os.path.join(tmp, "wt")), (other, os.path.join(tmp, "owt"))):
            try:
                sh(["worktree", "remove", "--force", w], repo)
            except Exception:
                pass
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [c for c, ok in results if not ok]
    if bad:
        print(f"FAILED {len(bad)}/{len(results)}: {', '.join(bad)}")
        return 1
    print(f"ALL PASS {len(results)}/{len(results)}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
