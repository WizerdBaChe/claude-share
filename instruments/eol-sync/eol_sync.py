#!/usr/bin/env python
"""eol-sync -- bring the working copy of tracked files to the line ending .gitattributes pins.

Why this exists: the pin in `.gitattributes` is a property of the asset (user ruling
2026-10-01: CRLF for text a human opens, reads or copies and for Windows-native script
loaders; LF for everything machine-read). No agent write path honours it -- the Write tool
and every Python/heredoc writer emit LF -- and git normalises the index, so a file born with
the wrong ending stays wrong in the working tree forever while `git status` calls it clean.
ops-health check 21 DETECTS that drift at session start; this tool REMOVES it, and the
post-commit hook in `tools/git-hooks/` runs it on every commit, which is the event that turns
a new file into a tracked one.

Safety property: only a CLEAN file is rewritten (its content equals the index modulo line
endings), and the bytes written are the index blob with the pinned ending -- never the
working copy re-encoded -- so no content can be lost or invented. A dirty file, a file whose
index blob is not LF-normalised, and a binary file are skipped and reported.

Run:
  python -X utf8 tools/eol-sync/eol_sync.py              # files of HEAD (what the hook runs)
  python -X utf8 tools/eol-sync/eol_sync.py --all        # every tracked file (migration)
  python -X utf8 tools/eol-sync/eol_sync.py --all --check  # report only; exit 1 on drift
  python -X utf8 tools/eol-sync/eol_sync.py --wiring       # is the post-commit hook wired?
Exit: 0 = nothing off the pin after the run (or --check found none); 1 = --check found drift;
2 = git failed. The hook ignores the exit code: a post-commit hook cannot undo a commit.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

GIT_TIMEOUT_S = 60


def git(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    proc = subprocess.run(["git", "-C", str(repo), *args], input=data,
                          capture_output=True, timeout=GIT_TIMEOUT_S)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])} failed: "
                           f"{proc.stderr.decode('utf-8', 'replace').strip()[:300]}")
    return proc.stdout


def pinned_ending(attr: str) -> str | None:
    """The ending the attribute column pins: 'crlf', 'lf', or None (not pinned / not text)."""
    if "-text" in attr.split() or attr.endswith("/-text"):
        return None
    for token in attr.replace("attr/", "").split():
        if token == "eol=crlf":
            return "crlf"
        if token == "eol=lf":
            return "lf"
    return None


def eol_rows(repo: Path, paths: list[str] | None) -> list[dict]:
    """Parse `git ls-files --eol -z`: '<i/x> <w/y> <attr/...>\\t<path>' per record.

    Always lists the whole index and filters here: passing paths as arguments hit the
    Windows command-line limit (WinError 206) on the first --all migration, ~1500 paths."""
    if paths is not None and not paths:
        return []
    want = set(paths) if paths is not None else None
    rows = []
    for rec in git(repo, "ls-files", "--eol", "-z").split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        fields = meta.decode("ascii", "replace").split()
        if len(fields) < 3:
            continue
        p = path.decode("utf-8")
        if want is None or p in want:
            rows.append({"index": fields[0][2:], "work": fields[1][2:],
                         "attr": " ".join(fields[2:]), "path": p})
    return rows


def off_pin(row: dict) -> bool:
    want = pinned_ending(row["attr"])
    if want is None or row["work"] in ("", "none", "-text"):
        return False
    return row["work"] == "mixed" or row["work"] != want


def dirty_paths(repo: Path, paths: list[str]) -> set[str]:
    """Tracked paths with staged or unstaged edits (whole tree; no pathspec, see eol_rows)."""
    if not paths:
        return set()
    out = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=no")
    dirty = set()
    recs = out.split(b"\0")
    i = 0
    while i < len(recs):
        rec = recs[i]
        if len(rec) > 3:
            dirty.add(rec[3:].decode("utf-8"))
            if rec[:1] in (b"R", b"C"):  # rename/copy carries the source path next
                i += 1
        i += 1
    return dirty


def commit_paths(repo: Path, rev: str) -> list[str]:
    out = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "--root", rev)
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


def index_blobs(repo: Path, paths: list[str]) -> dict[str, bytes]:
    """Index content of many paths through ONE `git cat-file --batch` (one process, not one per file)."""
    if not paths:
        return {}
    req = b"".join(b":" + p.encode("utf-8") + b"\n" for p in paths)
    out = git(repo, "cat-file", "--batch", data=req)
    blobs, pos = {}, 0
    for p in paths:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].split()
        if len(header) < 3 or header[1] != b"blob":
            raise RuntimeError(f"cat-file --batch gave no blob for {p!r}: {out[pos:nl][:120]!r}")
        size = int(header[2])
        blobs[p] = out[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1  # content is followed by one LF
    return blobs


def realign(repo: Path, rows: list[dict], check: bool) -> dict:
    drift = [r for r in rows if off_pin(r)]
    dirty = dirty_paths(repo, [r["path"] for r in drift])
    result = {"drift": len(drift), "rewritten": [], "skipped": []}
    todo = []
    for row in drift:
        path = row["path"]
        if path in dirty:
            result["skipped"].append((path, "has uncommitted edits"))
            continue
        if row["index"] != "lf":
            result["skipped"].append((path, f"index blob is i/{row['index']}, not LF-normalised"))
            continue
        todo.append(row)
    if check:
        return result
    blobs = index_blobs(repo, [r["path"] for r in todo])
    for row in todo:
        path = row["path"]
        blob = blobs[path]
        if pinned_ending(row["attr"]) == "crlf":
            blob = blob.replace(b"\n", b"\r\n")
        (repo / path).write_bytes(blob)
        result["rewritten"].append(path)
    if result["rewritten"]:
        # Re-checkout the (now content-identical) paths so the index records their new stat.
        # Measured 2026-10-01: after an ending-only rewrite `git status` reports ` M` with an
        # empty diff, and neither `update-index --refresh` nor `--really-refresh` clears it;
        # `checkout -- <path>` does, and writes the same bytes this tool just wrote.
        git(repo, "--literal-pathspecs", "checkout", "--pathspec-from-file=-", "--pathspec-file-nul",
            data=b"\0".join(p.encode("utf-8") for p in result["rewritten"]))
    return result


HOOK_DIR = "tools/git-hooks"


def wiring(repo: Path) -> tuple[bool, str]:
    """Is the post-commit hook actually wired? core.hooksPath is repo-local config, so a
    fresh clone, a `git config --unset`, or a tool resetting hooks turns the remedy off
    silently -- check 21 would still see the drift, one session later."""
    try:
        val = git(repo, "config", "--get", "core.hooksPath").decode().strip()
    except RuntimeError:
        return False, f"core.hooksPath is unset (want {HOOK_DIR})"
    if val.replace("\\", "/").rstrip("/") != HOOK_DIR:
        return False, f"core.hooksPath = {val!r} (want {HOOK_DIR})"
    if not (repo / HOOK_DIR / "post-commit").is_file():
        return False, f"{HOOK_DIR}/post-commit is missing"
    return True, f"core.hooksPath = {HOOK_DIR}, post-commit present"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--wiring", action="store_true",
                    help="only check that the post-commit hook is wired; exit 1 if not")
    ap.add_argument("--repo", type=Path, default=None, help="repo root (default: the one holding cwd)")
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument("--commit", default=None, help="only the files this commit touched (default HEAD)")
    scope.add_argument("--all", action="store_true", help="every tracked file")
    ap.add_argument("--check", action="store_true", help="report only, write nothing; exit 1 on drift")
    ap.add_argument("--quiet", action="store_true", help="print nothing when nothing was off the pin")
    args = ap.parse_args(argv)

    try:
        repo = args.repo or Path(git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
        if args.wiring:
            ok, why = wiring(repo)
            print(f"[eol-sync] wiring {'ok' if ok else 'BROKEN'}: {why}")
            return 0 if ok else 1
        paths = None if args.all else commit_paths(repo, args.commit or "HEAD")
        rows = eol_rows(repo, paths)
        res = realign(repo, rows, args.check)
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f"[eol-sync] undetermined: {exc}", file=sys.stderr)
        return 2

    if res["drift"] or not args.quiet:
        verb = "would rewrite" if args.check else "rewrote"
        n = res["drift"] - len(res["skipped"]) if args.check else len(res["rewritten"])
        print(f"[eol-sync] {res['drift']} file(s) off the pinned line ending; {verb} {n}; "
              f"skipped {len(res['skipped'])}", file=sys.stderr)
        for path, why in res["skipped"]:
            print(f"[eol-sync]   skipped {path}: {why}", file=sys.stderr)
    if args.check:
        return 1 if res["drift"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
