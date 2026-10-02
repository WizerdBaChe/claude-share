#!/usr/bin/env python3
"""tracking refs — does a COMMITTED instruction surface point at a file git does not hold?

Status: live 2026-09-18 | severity: FAIL for every `dangling` pointer (exit 1);
`pending` / `ignored` are REPORT lines; `undetermined` is counted apart and never
folded into a verdict | controls: `controls.py` (two-sided, `ALL PASS n/n`) |
wired: `ops/references/integrity-sweep.md` check 34 + `hooks/ops_health_nudge.py`
check 18 | why: `ops/rule-registry.md` key `tracking refs` | record:
`reports/2026-09-18-git-tracking-sweep.md`.

THE CLASS IT CLOSES
-------------------
2026-09-18: `skills/comsol-agent-pipeline/` (5 files) had never been added, and
the committed `CLAUDE.md` indexed `rules/layout-convergence.md`, which was also
untracked. Ops-health check 14 only reports dirty paths older than a threshold
by AGE; it cannot see that a path is load-bearing because something already in
history names it. A rollback to any commit in that window restores the pointer
without its target. This tool reads the pointers instead of the ages.

CLASSES (closed over the corpus; every extracted reference lands in exactly one)
------------------------------------------------------------------------------
  dangling      source TRACKED, target exists and is UNTRACKED (not ignored) -> FAIL
  pending       source untracked, target untracked: both halves in flight;
                check 14 owns their age                                -> REPORT
  ignored       target exists but .gitignore excludes it: a deliberate
                exclusion this tool cannot overrule                    -> REPORT
  undetermined  target found nowhere (prose that looks like a path, a path
                relative to ANOTHER repo such as the COMSOL rig)        -> counted apart
  (resolved)    target tracked                                         -> silent
A whole run is `undetermined` (exit 2) when the root is not a git work tree:
no verdict is printed, rather than "0 dangling" from an empty tracked set.

WHAT IT CANNOT DETERMINE
------------------------
Whether an `undetermined` string was meant as a path at all, and whether an
ignored target SHOULD be ignored. Both are reported with their sources so a
reader can rule; neither moves the exit code.

Two reference forms: a PATH (`tools/x/y.py`, `~/.claude/...`, `C:\\...\\.claude\\...`)
and a NAME (a backticked rule name -> `rules/<name>.md`; a `### <name>` heading in
skill-trigger-dict.md -> `skills/<name>`); a name counts only when its file exists.
Reference resolution: a path match is tried at the repo root first, then under every
ancestor of the source file (so `tools/sync_rules.py` written inside
`skills/x/SKILL.md` resolves to `skills/x/tools/sync_rules.py`). Backslashes and
doubled separators are folded to `/` before resolution.

Usage:
    python tools/tracking-refs/refs.py              # summary + dangling rows; exit 0/1/2
    python tools/tracking-refs/refs.py --verbose    # + pending / ignored / undetermined rows
    python tools/tracking-refs/refs.py --json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import PurePosixPath

DEFAULT_ROOT = os.path.expanduser("~/.claude")

# Instruction surfaces: files a session READS and acts on. Records under
# outputs/ drafts/ reports/ are history, where a dead pointer can be correct.
SURFACE = re.compile(
    r"^(CLAUDE\.md|settings\.json|skill-trigger-dict\.md"
    r"|skills/.+\.(md|py|json)"
    r"|hooks/.+\.(py|json|md)"
    r"|rules/.+\.md|ops/.+\.md|agents/.+\.md|commands/.+\.md"
    r"|references/[^/]+\.md"
    r"|tools/[^/]+/README\.md)$")
EXCLUDE = re.compile(r"(^|/)(archive|__pycache__|node_modules|\.venv)/")
REF = re.compile(
    r"(?<![\w.-])(?:~/\.claude[\\/]|\.claude[\\/]|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]+\.claude[\\/]+)?"
    r"((?:tools|skills|hooks|rules|agents|commands)(?:[\\/]+[\w.\-]+)+)")
CAPABILITY_DIRS = ("skills/", "tools/", "hooks/", "rules/", "agents/", "commands/")
# Name-form references: the house indexes name rules and skills WITHOUT a path
# (CLAUDE.md's path-scoped rules line: `layout-convergence`; the trigger dict's
# `### comsol-agent-pipeline` headings). Path-only extraction missed exactly the
# 2026-09-18 CLAUDE.md -> rules/layout-convergence.md case on replay. A name
# counts only when the file it names EXISTS, so an ordinary backticked word is
# not a reference and never becomes `undetermined`.
NAME_TOKEN = re.compile(r"`([a-z0-9][a-z0-9-]*[a-z0-9])`")
DICT_HEADING = re.compile(r"^###\s+([a-z0-9][a-z0-9-]*[a-z0-9])", re.M)


def _git(root: str, *args: str, timeout: float) -> str | None:
    try:
        r = subprocess.run(["git", "-C", root, "-c", "core.quotepath=off", *args],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def git_sets(root: str, timeout: float = 5.0):
    """(tracked, untracked) as sets of repo-relative posix paths, or None."""
    t = _git(root, "ls-files", timeout=timeout)
    u = _git(root, "ls-files", "--others", "--exclude-standard", timeout=timeout)
    if t is None or u is None:
        return None
    return set(t.splitlines()), set(u.splitlines())


def _clean(raw: str) -> str | None:
    r = re.sub(r"[\\/]+", "/", raw).strip().rstrip(".,;:)`'\"/")
    if not r or any(c in r for c in "*<>{}|") or "..." in r:
        return None
    if len(r.split("/")) < 2:
        return None
    return r


def classify(root: str, tracked: set[str], untracked: set[str]) -> dict:
    """Return {class: {target: sorted sources}} over every surface file."""
    tracked_dirs = set()
    for p in tracked:
        parts = p.split("/")
        for i in range(1, len(parts)):
            tracked_dirs.add("/".join(parts[:i]))
    untracked_dirs = set()
    for p in untracked:
        parts = p.split("/")
        for i in range(1, len(parts)):
            untracked_dirs.add("/".join(parts[:i]))

    def state(path: str) -> str | None:
        if path in tracked or path in tracked_dirs:
            return "tracked"
        if path in untracked or path in untracked_dirs:
            return "untracked"
        if os.path.exists(os.path.join(root, path)):
            return "ignored"
        return None

    out: dict[str, dict[str, set[str]]] = {
        "dangling": {}, "pending": {}, "ignored": {}, "undetermined": {}}
    sources = sorted(p for p in (tracked | untracked)
                     if SURFACE.match(p) and not EXCLUDE.search(p))
    for src in sources:
        try:
            with open(os.path.join(root, src), encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        src_tracked = src in tracked
        ancestors = [str(a) for a in PurePosixPath(src).parents if str(a) != "."]
        seen = set()
        for m in REF.finditer(text):
            ref = _clean(m.group(1))
            if ref is None or ref in seen:
                continue
            seen.add(ref)
            resolved, st = ref, None
            for cand in [ref] + [f"{a}/{ref}" for a in ancestors]:
                st = state(cand)
                if st is not None:
                    resolved = cand
                    break
            if st == "tracked":
                continue
            if st is None:
                cls = "undetermined"
            elif st == "ignored":
                cls = "ignored"
            else:
                cls = "dangling" if src_tracked else "pending"
            out[cls].setdefault(resolved, set()).add(src)
        names = [f"rules/{n}.md" for n in NAME_TOKEN.findall(text)]
        if src == "skill-trigger-dict.md":
            names += [f"skills/{n}" for n in DICT_HEADING.findall(text)]
        for cand in names:
            if cand in seen:
                continue
            seen.add(cand)
            st = state(cand)
            if st in (None, "tracked"):
                continue          # a name that names nothing is not a reference
            cls = "ignored" if st == "ignored" else ("dangling" if src_tracked else "pending")
            out[cls].setdefault(cand, set()).add(src)
    return {k: {t: sorted(s) for t, s in sorted(v.items())} for k, v in out.items()}


def scan(root: str = DEFAULT_ROOT, timeout: float = 5.0) -> dict | None:
    sets = git_sets(root, timeout)
    if sets is None:
        return None
    return classify(root, *sets)


def summary(res: dict) -> str:
    return (f"tracking-refs: {len(res['dangling'])} dangling (FAIL) / "
            f"{len(res['pending'])} pending / {len(res['ignored'])} ignored / "
            f"{len(res['undetermined'])} undetermined")


def main(argv: list[str]) -> int:
    root = DEFAULT_ROOT
    if "--root" in argv:
        root = argv[argv.index("--root") + 1]
    res = scan(root)
    if res is None:
        print(f"tracking-refs: undetermined — {root} is not a readable git work tree")
        return 2
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 1 if res["dangling"] else 0
    classes = ["dangling"] + (["pending", "ignored", "undetermined"] if "--verbose" in argv else [])
    for cls in classes:
        for tgt, srcs in res[cls].items():
            more = f" (+{len(srcs) - 3})" if len(srcs) > 3 else ""
            print(f"{cls:12} {tgt}  <-  {', '.join(srcs[:3])}{more}")
    if res["dangling"]:
        print("act: commit each target by path (`git add -- <target>`), or fix the pointer "
              "if the target is not meant to exist; never widen .gitignore to silence it")
    print(summary(res))
    return 1 if res["dangling"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
