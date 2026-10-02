#!/usr/bin/env python3
"""Reconcile emitter: does the disk agree with the RECORD? (hmi-report/1, class=reconcile)

STATUS: LIVE since 2026-09-19 (user ruling 2026-09-19: every subsystem is judged on two
classes -- R reconcile and I integrity; design 06 in the source environment's design record, not shipped).

The record here is git. One `git status --porcelain` per repo, apportioned by PATH:
  * the home repo (~/.claude): one point per HMI subsystem, `reconcile.git.home.<subsystem>`,
    plus `reconcile.git.home.unowned` for dirty paths no registered component owns;
  * every external repo listed in registry/reconcile.json: `reconcile.git.<slug>`.
A repo also reports its branches: not merged into the default branch, and merged-but-undeleted.

Verdict (user rulings 2026-09-19, Q1/Q3):
  clean                                   -> pass
  dirty, every dirty path younger than G  -> warn  (work in flight)
  any dirty path older than G             -> fail  (never closed out)
  unmerged branch, tip younger than G     -> warn ; older -> fail
  merged-but-undeleted branch             -> warn, never fail
Two asset classes are judged on what they ARE, not on mtime (user rulings 2026-09-23):
  * a path with the git attribute `tool-appended` (.gitattributes: a tracked record a tool
    appends to on every routine use -- its mtime is always fresh and it is always dirty) is
    judged by the age of its LAST COMMIT: younger than G -> no finding; older -> warn.
  * a merged branch still checked out in a linked worktree (a Desktop pool session never
    diverges, so it reads "merged" the moment main moves) is judged by that worktree's HEAD
    reflog age: younger than G -> in use, no finding; older or unreadable -> merged warn.
G is NOT restated here (INV-4): it is STALE_WORK_DAYS, read out of hooks/ops_health_nudge.py.
If that constant cannot be read the age is undeterminable, so every dirty repo is
`quality: undetermined` -- never a guess.

Known limits (E-6): "the record was confirmed" is not machine-observable, so a path's mtime
stands in for it. A path that is a directory uses the newest mtime beneath it (bounded walk).
A repo that is missing or not a git repo is ran:false, never pass. No fetch is ever made:
ahead/behind a remote is out of scope (offline by design).

Read-only: runs `git status`, `git branch`, `git log -1`, `git check-attr`, `git worktree list`;
writes nothing.
Proof-of-life: `python tools/system-hmi/controls.py`
"""
import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
HOME = TOOL_DIR.parents[1]
sys.path.insert(0, str(TOOL_DIR))

GIT_TIMEOUT_S = 20
WALK_CAP = 400  # entries examined under one dirty directory before giving up on "newest"


def grace_days(hook_path):
    """STALE_WORK_DAYS from the ops-health hook, by AST (importing a hook would run it)."""
    try:
        tree = ast.parse(Path(hook_path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "STALE_WORK_DAYS" for t in node.targets):
            try:
                return float(ast.literal_eval(node.value))
            except (ValueError, SyntaxError):
                return None
    return None


def _git(repo, *args):
    try:
        p = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=false", *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    if p.returncode != 0:
        return None, (p.stderr or "").strip()[:200]
    return p.stdout, None


def _age_days(path, now):
    """Age of the NEWEST thing at path (file, or bounded walk of a directory); None if gone."""
    try:
        if path.is_dir():
            newest, seen = path.stat().st_mtime, 0
            for root, _dirs, files in os.walk(path):
                for f in files:
                    seen += 1
                    if seen > WALK_CAP:
                        return (now - newest) / 86400.0
                    try:
                        newest = max(newest, (Path(root) / f).stat().st_mtime)
                    except OSError:
                        pass
            return (now - newest) / 86400.0
        return (now - path.stat().st_mtime) / 86400.0
    except OSError:
        return None  # deleted path: the deletion itself has no mtime to read


APPEND_ATTR = "tool-appended"  # .gitattributes: the asset declares its own class


def _appended_paths(repo, rels):
    """Subset of rels whose `tool-appended` attribute is set (one git call; none on error)."""
    if not rels:
        return set()
    out, _ = _git(repo, "check-attr", APPEND_ATTR, "--", *rels)
    hit = set()
    for line in (out or "").splitlines():
        path, _sep, rest = line.rpartition(f": {APPEND_ATTR}: ")
        if path and rest.strip() == "set":
            hit.add(path)
    return hit


def _commit_age(repo, rel, now):
    ts, _ = _git(repo, "log", "-1", "--format=%ct", "--", rel)
    return (now - float(ts.strip())) / 86400.0 if ts and ts.strip().isdigit() else None


def _worktree_activity(repo, now):
    """-> {branch: age_days|None} for branches checked out in a LINKED worktree.
    Age = mtime of that worktree's HEAD reflog (moves on commit, checkout, merge, rebase)."""
    out, _ = _git(repo, "worktree", "list", "--porcelain")
    blocks = [b for b in (out or "").replace("\r", "").split("\n\n") if b.strip()]
    act = {}
    for block in blocks[1:]:  # the first block is the main worktree
        fields = dict(l.split(" ", 1) for l in block.splitlines() if " " in l)
        br = fields.get("branch", "")
        if not br.startswith("refs/heads/"):
            continue
        age = None
        gd, _ = _git(fields.get("worktree", ""), "rev-parse", "--absolute-git-dir")
        if gd and gd.strip():
            for f in ("logs/HEAD", "HEAD"):
                age = _age_days(Path(gd.strip()) / f, now)
                if age is not None:
                    break
        act[br[len("refs/heads/"):]] = age
    return act


def repo_facts(repo, now):
    """-> (facts, error). facts = {dirty:[(relpath, age|None)], appended:[(relpath, commit_age)],
    unmerged:[(name, age)], merged:[name], parked:[(name, worktree_age|None)]}"""
    repo = Path(repo)
    if not repo.exists():
        return None, "path-missing"
    out, err = _git(repo, "rev-parse", "--is-inside-work-tree")
    if out is None or out.strip() != "true":
        return None, "not-a-git-repo"
    status, err = _git(repo, "status", "--porcelain")
    if status is None:
        return None, "git-status-failed: " + (err or "")
    rels = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        rels.append(line[3:].split(" -> ")[-1].strip().strip('"').rstrip("/"))
    marked = _appended_paths(repo, rels)
    dirty, appended = [], []
    for rel in rels:
        age = _commit_age(repo, rel, now) if rel in marked and (repo / rel).is_file() else None
        if age is not None:
            appended.append((rel, age))
        else:  # unmarked, deleted, or never committed: an ordinary dirty path
            dirty.append((rel, _age_days(repo / rel, now)))
    head, _ = _git(repo, "symbolic-ref", "--short", "HEAD")
    head = (head or "").strip()
    unmerged, merged, parked = [], [], []
    if head:
        um, _ = _git(repo, "branch", "--no-merged", head, "--format=%(refname:short)")
        for name in (um or "").split():
            ts, _ = _git(repo, "log", "-1", "--format=%ct", name)
            age = (now - float(ts.strip())) / 86400.0 if ts and ts.strip().isdigit() else None
            unmerged.append((name, age))
        mg, _ = _git(repo, "branch", "--merged", head, "--format=%(refname:short)")
        act = _worktree_activity(repo, now)
        for n in (mg or "").split():
            if n == head:
                continue
            if n in act:
                parked.append((n, act[n]))
            else:
                merged.append(n)
    return {"dirty": dirty, "appended": appended, "unmerged": unmerged, "merged": merged,
            "parked": parked, "head": head}, None


def judge(dirty, unmerged, merged, grace, appended=(), parked=()):
    """-> (state, quality, findings). Pure; the controls exercise every branch.
    appended: [(path, days since its last commit)]; parked: [(branch, worktree reflog age|None)]."""
    findings = []
    if not dirty and not unmerged and not merged and not appended and not parked:
        return "pass", "good", findings
    if grace is None and (dirty or unmerged or appended or parked):
        return None, "undetermined", [{"severity": "undetermined", "label": "grace unreadable",
                                       "text": "STALE_WORK_DAYS could not be read from hooks/ops_health_nudge.py"}]
    stale_app = [(p, a) for p, a in appended if a > grace]
    idle = [(n, a) for n, a in parked if a is None or a > grace]
    if not dirty and not unmerged and not merged and not stale_app and not idle:
        return "pass", "good", findings  # records committed within G; worktrees in use
    worst = "warn"
    if stale_app:
        findings.append({"severity": "warn", "label": f"{len(stale_app)} tool-appended record(s) not committed",
                         "text": ", ".join(f"{p} (last commit {a:.1f}d ago)" for p, a in stale_app[:6])})
    if idle:
        findings.append({"severity": "warn", "label": "merged worktree idle",
                         "text": ", ".join(f"{n} (worktree idle {a:.1f}d)" if a is not None
                                           else f"{n} (worktree activity unreadable)" for n, a in idle[:6])})
    old = [(p, a) for p, a in dirty if a is not None and a > grace]
    if dirty:
        if old:
            worst = "fail"
        oldest = max((a for _p, a in dirty if a is not None), default=None)
        sev = "fail" if old else "warn"
        shown = ", ".join(p for p, _a in (old or dirty)[:6])
        more = len(old or dirty) - 6
        findings.append({"severity": sev, "label": f"{len(dirty)} uncommitted path(s)",
                         "text": (f"{len(old)} older than {grace:g}d (oldest {oldest:.1f}d): " if old
                                  else f"all younger than {grace:g}d (work in flight): ")
                                 + shown + (f" (+{more} more)" if more > 0 else "")})
    for name, age in unmerged:
        sev = "fail" if (age is not None and age > grace) else "warn"
        if sev == "fail":
            worst = "fail"
        findings.append({"severity": sev, "label": "branch not merged",
                         "text": f"{name} (tip {age:.1f}d old)" if age is not None else name})
    if merged:
        findings.append({"severity": "warn", "label": "merged branch not deleted",
                         "text": ", ".join(merged[:6])})
    return worst, "good", findings


def _point(pid, alias, state, quality, findings, ran=True, skip=None, remedy=None):
    return {"id": pid, "alias": alias, "class": "reconcile", "ran": ran, "skip_reason": skip,
            "state": state, "quality": quality, "findings": findings, "remedy": remedy}


def build(home, registry, config, now=None):
    from hmi import scan as scan_mod
    now = now or time.time()
    grace = grace_days(Path(home) / "hooks" / "ops_health_nudge.py")
    points = []

    # --- home repo, apportioned by the component that owns each dirty path ----
    facts, err = repo_facts(home, now)
    sub_ids = [s["id"] for s in registry["subsystems"]]
    if facts is None:
        for sid in sub_ids + ["unowned"]:
            points.append(_point(f"reconcile.git.home.{sid}", f"git 對帳／{sid}", None, "good", [],
                                 ran=False, skip=err))
    else:
        comp_idx = scan_mod.component_index(scan_mod.scan(str(home), registry))
        owners = sorted(comp_idx, key=len, reverse=True)
        by_sub = {sid: ([], []) for sid in sub_ids + ["unowned"]}
        for kind, rows in ((0, facts["dirty"]), (1, facts["appended"])):
            for rel, age in rows:
                owner = next((c for c in owners if rel == c or rel.startswith(c.rstrip("/") + "/")), None)
                sid = comp_idx[owner].get("subsystem") if owner else None
                by_sub[sid if sid in by_sub else "unowned"][kind].append((rel, age))
        for sid in sub_ids:
            st, q, f = judge(by_sub[sid][0], [], [], grace, appended=by_sub[sid][1])
            points.append(_point(f"reconcile.git.home.{sid}", f"git 對帳／{sid}", st, q, f,
                                 remedy="git -C ~/.claude status -- <paths>; commit or archive"))
        # branches belong to the repo as a whole, so they ride on the unowned point
        st, q, f = judge(by_sub["unowned"][0], facts["unmerged"], facts["merged"], grace,
                         appended=by_sub["unowned"][1], parked=facts["parked"])
        points.append(_point("reconcile.git.home.unowned", "git 對帳／無主路徑與分支", st, q, f,
                             remedy="git -C ~/.claude status; git branch --no-merged; "
                                    "idle merged worktree: git worktree remove <path>; git branch -d <branch>"))

    # --- external repos --------------------------------------------------------
    for r in config.get("repos", []):
        pid = f"reconcile.git.{r['slug']}"
        facts, err = repo_facts(r["path"], now)
        if facts is None:
            points.append(_point(pid, f"git 對帳／{r['slug']}", None, "good", [], ran=False, skip=err))
            continue
        st, q, f = judge(facts["dirty"], facts["unmerged"], facts["merged"], grace,
                         appended=facts["appended"], parked=facts["parked"])
        points.append(_point(pid, f"git 對帳／{r['slug']}", st, q, f,
                             remedy=f"git -C {r['path']} status; commit, merge or delete the branch"))
    return {"protocol": "hmi-report/1", "source": "reconcile",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "points": points}


def main():
    from hmi import registry as registry_mod
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    reg = registry_mod.load_registry(str(TOOL_DIR / "registry"))
    cfg_path = TOOL_DIR / "registry" / "reconcile.json"
    config = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    print(json.dumps(build(HOME, reg, config), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
