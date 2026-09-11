#!/usr/bin/env python3
"""triage.py — sort a source delta into the procedure each path needs.

    python tools/triage.py --source ~/.claude                  # since manifest `source_aligned`
    python tools/triage.py --source ~/.claude --since 27196ab
    python tools/triage.py --source ~/.claude --all            # every recheck/never row, not counts
    python tools/triage.py --source ~/.claude --json           # machine-readable

Why this exists
---------------
tools/COLLECTION-RULES.md: "sort the candidate list by which procedure it needs
*before* you copy anything, because a bulk sweep silently runs A over B's
files." Until 2026-09-12 that sort was done by hand, once per round, by whoever
ran the round — 516 changed source paths that day. The sort is mechanical: it
only asks what the manifest ALREADY declares about each path. So it is a
script. The verdicts are not mechanical, and this file reaches none of them —
it tells you which question to ask of each path, never the answer.

Buckets (first match wins, in this order)
-----------------------------------------
  refresh      a [[collected]] entry names it as its source -> procedure B.
               Flagged `dirty` (content uncommitted at the source — numstat,
               not the porcelain letter, so line endings alone do not count)
               or `untracked` (collected while committed nowhere).
  source-gone  a [[collected]] source that the source deleted -> report it;
               deleting the repo copy is main's decision (brief branch D4).
  never        on COLLECTION-RULES' never-collect list -> no entry, unless a
               shipped file cites it (the `cited` column).
  uncommitted  untracked at the source: committed nowhere, so not collectable.
  recheck      covered by a [[not_shipped]] entry, exact or directory ->
               re-verify the disposition per FILE (hard rule 5).
  deleted      gone at the source and never shipped or declared -> nothing.
  candidate    none of the above -> the seven-row decision table, procedure A.

A [[collected]] entry beats a [[not_shipped]] directory on purpose: the
archdiag library is collected from under the excluded `tools/` tree, and a
triage that called it "recheck" would send a refresh through the wrong
procedure — failure 4 of COLLECTION-RULES, produced by the sorting step.

`cited` counts tracked files here whose text contains the source path —
the input to decision-table row 2, and the number that turns a `never` or a
`candidate` into something that must reach a verdict. The manifest and the
changelog are excluded from the count: they name everything and route to
nothing. It is a substring count, so a generic root name reads high for the
wrong reason — on its first run the source's `.gitignore` showed 9, every one
a mention of THIS repo's own `.gitignore`. Treat `cited` as "look here", not
as "this is routed to".

Not a gate. Exit 0 whenever it could run, 2 when it could not. It rules on
nothing it cannot determine, and whether a path ships is never something it
can determine.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sharelib import REPO_ROOT, load_manifest  # noqa: E402

SRC_PREFIX = "~/.claude/"

# COLLECTION-RULES.md "Never collect", as data. Roots match at the start of the
# source path; segments match a DIRECTORY component anywhere (never a file
# name — `archived-notes.md` is not an archive).
NEVER_ROOTS = ("projects/", "memory/", "sessions/", "telemetry/", "backups/",
               "archive/", "audit-archive/", "drafts/", "plans/")
NEVER_SEGMENTS = ("archive", "audit-archive", "__pycache__")
NEVER_NAMES = (".credentials.json", "settings.local.json")

CITE_SUFFIXES = {".md", ".py", ".toml", ".json", ".txt", ".mjs", ".yml",
                 ".yaml", ".html"}
CITE_EXCLUDE = {"tools/share-manifest.toml", "CHANGELOG.md"}

PROCEDURE = {
    "refresh": "procedure B — recover the edits list first",
    "source-gone": "report; main decides (brief D4)",
    "never": "no entry unless cited",
    "uncommitted": "do not collect (Step 0)",
    "recheck": "re-verify the disposition per file (hard rule 5)",
    "deleted": "nothing to do",
    "candidate": "decision table, procedure A",
}
ORDER = list(PROCEDURE)


# --- pure classification (what test_triage.py exercises) ----------------------

def build_index(manifest):
    """source-relative path -> repo path, and the (path, disposition) list."""
    collected = {}
    for e in manifest.get("collected", []):
        src = e.get("source", "")
        if src.startswith(SRC_PREFIX):
            collected[src[len(SRC_PREFIX):]] = e.get("path")
    not_shipped = [(e["path"], e.get("disposition", ""))
                   for e in manifest.get("not_shipped", []) if e.get("path")]
    return collected, not_shipped


def ns_match(path, not_shipped):
    """Longest [[not_shipped]] entry covering `path`, on a segment boundary."""
    best = None
    for key, disp in not_shipped:
        k = key.rstrip("/")
        if path == k or path.startswith(k + "/"):
            if best is None or len(k) > len(best[0].rstrip("/")):
                best = (key, disp)
    return best


def is_never(path):
    parts = path.split("/")
    if path.startswith(NEVER_ROOTS) or parts[-1] in NEVER_NAMES:
        return True
    if len(parts) == 1 and parts[0].startswith("history"):
        return True
    if any(p in NEVER_SEGMENTS for p in parts[:-1]):
        return True
    # "anything under a `.claude/` subdirectory of a skill"
    return parts[0] == "skills" and ".claude" in parts[2:-1]


def classify(rec, collected, not_shipped, untracked, dirty):
    """rec = {path, status, old?}. Returns rec extended with bucket/flags."""
    path, status, old = rec["path"], rec["status"], rec.get("old")
    out = dict(rec, flags=[], repo=None, entry=None, disposition=None)
    if old:
        out["flags"].append(f"renamed-from:{old}")
        if old in collected or any(k.rstrip("/") == old for k, _ in not_shipped):
            out["flags"].append("entry-names-old-path")
    if path in collected:
        out["repo"] = collected[path]
        if status == "D":
            out["bucket"] = "source-gone"
            return out
        if path in untracked:
            out["flags"].append("untracked")
        if path in dirty:
            out["flags"].append("dirty")
        out["bucket"] = "refresh"
        return out
    if is_never(path):
        out["bucket"] = "never"
        return out
    if path in untracked:
        out["bucket"] = "uncommitted"
        return out
    m = ns_match(path, not_shipped)
    if m:
        out["entry"], out["disposition"] = m
        if status == "D":
            out["flags"].append("source-deleted")
        out["bucket"] = "recheck"
        return out
    out["bucket"] = "deleted" if status == "D" else "candidate"
    return out


def lane(path):
    p = path.split("/")
    if len(p) == 1:
        return "(root)"
    if p[0] in ("skills", "tools") and len(p) > 2:
        return "/".join(p[:2])
    return p[0]


# --- git plumbing ---------------------------------------------------------------

def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if p.returncode != 0:
        print(f"FATAL: git {' '.join(args)} failed in {root}:\n"
              f"{p.stderr.decode('utf-8', 'replace')}")
        sys.exit(2)
    return p.stdout.decode("utf-8", "replace")


def parse_name_status(z):
    """`git diff --name-status -M -z` -> [{path, status, old?}]."""
    tok, recs, i = z.split("\0"), [], 0
    while i < len(tok) and tok[i]:
        st = tok[i]
        if st[0] in "RC":
            recs.append({"status": st[0], "old": tok[i + 1], "path": tok[i + 2]})
            i += 3
        else:
            recs.append({"status": st[0], "path": tok[i + 1]})
            i += 2
    return recs


def parse_porcelain(z):
    """`git status --porcelain=v1 -uall -z` -> (untracked set, touched set)."""
    tok, untracked, touched, i = z.split("\0"), set(), set(), 0
    while i < len(tok) and tok[i]:
        xy, path = tok[i][:2], tok[i][3:]
        (untracked if xy == "??" else touched).add(path)
        i += 2 if xy[0] in "RC" else 1
    return untracked, touched


def parse_numstat(z):
    """`git diff HEAD --numstat -z` -> paths whose CONTENT differs."""
    tok, dirty, i = z.split("\0"), set(), 0
    while i < len(tok) and tok[i]:
        a, d, path = (tok[i].split("\t", 2) + ["", "", ""])[:3]
        if path == "":                       # rename: path follows as old\0new
            path, i = tok[i + 2], i + 3
        else:
            i += 1
        if a == "-" or (a.isdigit() and d.isdigit() and int(a) + int(d) > 0):
            dirty.add(path)
    return dirty


def cite_counts(paths):
    files = [p for p in git(REPO_ROOT, "ls-files").splitlines()
             if p and p not in CITE_EXCLUDE and Path(p).suffix in CITE_SUFFIXES]
    texts = []
    for rel in files:
        try:
            texts.append((REPO_ROOT / rel).read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
    return {p: sum(1 for t in texts if p in t) for p in paths}


# --- report -------------------------------------------------------------------

def render(rows, since, head, show_all):
    by = {b: [r for r in rows if r["bucket"] == b] for b in ORDER}
    out = [f"# triage — source {since}..{head}",
           "",
           f"{len(rows)} path(s): the committed delta plus uncommitted state at "
           f"the source. Buckets are a sort, not a verdict.",
           "",
           "| bucket | paths | next step |",
           "|---|---|---|"]
    out += [f"| {b} | {len(by[b])} | {PROCEDURE[b]} |" for b in ORDER if by[b]]

    def table(title, head_row, lines):
        if lines:
            cols = head_row.strip().strip("|").count("|") + 1
            out.extend(["", f"## {title}", "", head_row, "|" + "---|" * cols])
            out.extend(lines)

    table(f"refresh ({len(by['refresh'])})", "| source | repo | flags |",
          [f"| {r['path']} | {r['repo']} | {' '.join(r['flags'])} |"
           for r in sorted(by["refresh"], key=lambda r: r["path"])])
    table(f"source-gone ({len(by['source-gone'])})", "| source | repo | flags |",
          [f"| {r['path']} | {r['repo']} | {' '.join(r['flags'])} |"
           for r in by["source-gone"]])
    table(f"candidate ({len(by['candidate'])})", "| source | lane | status | cited | flags |",
          [f"| {r['path']} | {lane(r['path'])} | {r['status']} | {r['cited']} | "
           f"{' '.join(r['flags'])} |"
           for r in sorted(by["candidate"], key=lambda r: (lane(r["path"]), r["path"]))])

    rc = by["recheck"]
    if show_all:
        table(f"recheck ({len(rc)})", "| source | entry | disposition | cited | flags |",
              [f"| {r['path']} | {r['entry']} | {r['disposition']} | {r['cited']} | "
               f"{' '.join(r['flags'])} |" for r in sorted(rc, key=lambda r: r["path"])])
    else:
        groups = {}
        for r in rc:
            groups.setdefault((r["entry"], r["disposition"]), []).append(r)
        table(f"recheck ({len(rc)}, grouped by entry; --all for rows)",
              "| entry | disposition | files | cited (path: count) |",
              [f"| {e} | {d} | {len(g)} | "
               + ", ".join(f"{r['path']}: {r['cited']}" for r in g if r["cited"])
               + " |" for (e, d), g in sorted(groups.items())])

    for b in ("uncommitted", "never"):
        rs = by[b]
        if not rs:
            continue
        cited = [r for r in rs if r["cited"]]
        if show_all:
            table(f"{b} ({len(rs)})", "| source | cited |",
                  [f"| {r['path']} | {r['cited']} |" for r in sorted(rs, key=lambda r: r["path"])])
        else:
            counts = {}
            for r in rs:
                counts[lane(r["path"])] = counts.get(lane(r["path"]), 0) + 1
            table(f"{b} ({len(rs)}; per lane, --all for rows)", "| lane | paths |",
                  [f"| {k} | {v} |" for k, v in sorted(counts.items())])
            if cited:
                table(f"{b} — cited by a tracked file (must reach a verdict)",
                      "| source | cited |",
                      [f"| {r['path']} | {r['cited']} |" for r in cited])
    if by["deleted"]:
        out += ["", f"deleted, never shipped or declared: {len(by['deleted'])} path(s)."]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", metavar="PATH", default="~/.claude",
                    help="the source environment (a git checkout)")
    ap.add_argument("--since", metavar="SHA",
                    help="baseline commit (default: manifest `source_aligned`)")
    ap.add_argument("--all", action="store_true",
                    help="list every recheck/never/uncommitted row")
    ap.add_argument("--json", action="store_true", help="emit JSON rows")
    args = ap.parse_args()

    manifest = load_manifest()
    since = args.since or manifest.get("source_aligned")
    if not since:
        print("FATAL: no baseline — pass --since or set `source_aligned` in "
              "share-manifest.toml")
        return 2
    src = Path(args.source).expanduser()
    head = git(src, "rev-parse", "--short", "HEAD").strip()

    recs = {r["path"]: r for r in parse_name_status(
        git(src, "diff", "--name-status", "-M", "-z", since, "HEAD"))}
    untracked, touched = parse_porcelain(
        git(src, "status", "--porcelain=v1", "-uall", "-z"))
    dirty = parse_numstat(git(src, "diff", "HEAD", "--numstat", "-z"))
    for p in untracked | touched:
        recs.setdefault(p, {"path": p, "status": "?" if p in untracked else "M"})

    collected, not_shipped = build_index(manifest)
    rows = [classify(r, collected, not_shipped, untracked, dirty)
            for r in recs.values()]
    cites = cite_counts([r["path"] for r in rows if r["bucket"] != "refresh"])
    for r in rows:
        r["cited"] = cites.get(r["path"], 0)

    if args.json:
        print(json.dumps({"since": since, "head": head, "rows": rows}, indent=1))
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(render(rows, since, head, args.all), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
