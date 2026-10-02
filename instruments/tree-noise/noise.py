r"""tree-noise — classify a git working tree's uncommitted paths into NOISE vs REAL work.

STATUS: LIVE since 2026-09-23. Rule carried: `ops/rule-registry.md` key `TREE_NOISE`.
Severity: none — it reports, it never blocks, never stages, never commits (AP-28).

WHY. The harness shows every session a `git status` snapshot of its cwd repo. Paths an
app or a tool rewrote with no content change behind them (Obsidian re-serialising a
`.base` and dropping quotes; a census tool regenerating its status note; a file moved
without an edit) arrive looking exactly like unfinished work, and the session spends
reasoning on "is this mine / pre-existing / safe?" (obsidian_Nathan 2026-09-23: four
dirty paths, none of them work). This tool settles that question with git alone —
no model call — so the SessionStart hook `hooks/tree_noise_gist.py` can say it in one
line before the session reads the snapshot.

CLASSES (closed, AP-62). A path is NOISE only with a PROOF; the default is `real`:
  generated     the path carries the git attribute `tool-appended` (the same vocabulary
                system-hmi's reconcile emitter reads): a tool rewrites it on routine use
  eol-only      `git diff HEAD --ignore-cr-at-eol` is empty for it (line endings only)
  format-only   a .base/.yaml/.yml/.json whose HEAD and working copies PARSE to equal
                data (quoting, key order, flow-vs-block style). Never `.md`: a note's
                front-matter re-serialised by Obsidian's Properties panel is a SEMANTIC
                change for the cross-index card grammar (vault AGENTS.md §2)
  rename-only   a deleted tracked path whose HEAD blob equals the (filtered) hash of an
                untracked or added path — moved, not edited; reported as `old -> new`
  real          any other content change, incl. a deletion with no identical twin and a
                parseable file that no longer parses (no null proof exists)
  untracked     a new path that is not the target of a rename-only pair
  undetermined  a state this tool does not model: unmerged (conflict), typechange,
                git failure, or past MAX_ENTRIES. Excluded from every noise count.

RULER (AP-31). Sees: content equality after EOL normalisation, parse equality for the
four suffixes, blob identity for renames, one attribute. Does NOT see: whitespace
beyond CR, semantic equality of Markdown/HTML/code, partial renames (edited AND moved
= real + untracked), who wrote a path. Known-excluded calibration case: a `.md` whose
front-matter lost its quotes stays `real` (controls C2).

EXTENSION: a new noise class carries (1) a proof predicate that can only return True
for a content-neutral change, (2) a positive AND a negative case in controls.py, and
(3) a line in CLASSES above. A new parseable suffix is one entry in PARSERS plus a
negative case (a value change of that suffix must stay `real`).

Proof-of-life: `python tools/tree-noise/controls.py`
review-when: git changes `status --porcelain=v1 -z` framing; the vault stops using
`.base` files; a tool starts committing its own writes (its path then leaves the
`tool-appended` class).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ATTR = "tool-appended"
NOISE = ("generated", "eol-only", "format-only", "rename-only")
CLASSES = NOISE + ("real", "untracked", "undetermined")
MAX_ENTRIES = 400          # past this, the rest is `undetermined` — a hook budget, not a verdict
MAX_PARSE = 60             # parse-equality probes per run (each is one `git show`)


def _yaml(text: str):
    import yaml             # PyYAML; absent -> ImportError -> the path stays `real`
    return yaml.safe_load(text)


PARSERS = {".base": _yaml, ".yaml": _yaml, ".yml": _yaml, ".json": json.loads}


def git(repo: Path, *args: str, stdin: bytes | None = None) -> tuple[int, bytes]:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], input=stdin,
                           capture_output=True, timeout=20)
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, b""


def _z(out: bytes) -> list[str]:
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def parse_status(out: bytes) -> list[tuple[str, str, str]]:
    """porcelain v1 -z -> [(XY, path, orig_path_or_'')]."""
    toks, rows, i = out.split(b"\0"), [], 0
    while i < len(toks):
        t = toks[i]
        i += 1
        if len(t) < 4:
            continue
        xy, path = t[:2].decode(), t[3:].decode("utf-8", "surrogateescape")
        orig = ""
        if "R" in xy or "C" in xy:
            orig = toks[i].decode("utf-8", "surrogateescape") if i < len(toks) else ""
            i += 1
        rows.append((xy, path, orig))
    return rows


def classify(repo: Path | str) -> dict | None:
    """-> {"repo", "entries": [{"path", "cls", "why"}], "counts"} or None (not a git repo)."""
    repo = Path(repo)
    rc, top = git(repo, "rev-parse", "--show-toplevel")
    if rc != 0:
        return None
    root = Path(top.decode("utf-8", "replace").strip())
    rc, out = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries: list[dict] = []

    def add(path, cls, why):
        entries.append({"path": path, "cls": cls, "why": why})

    if rc != 0:
        add(".", "undetermined", "git status failed")
        return _finish(root, entries)
    rows = parse_status(out)
    if len(rows) > MAX_ENTRIES:
        for xy, p, _ in rows[MAX_ENTRIES:]:
            add(p, "undetermined", f"past MAX_ENTRIES={MAX_ENTRIES}")
        rows = rows[:MAX_ENTRIES]

    modified, deleted, newish = [], [], []        # newish: untracked or staged-added
    for xy, p, orig in rows:
        if "U" in xy or xy in ("AA", "DD"):
            add(p, "undetermined", "unmerged (conflict)")
        elif "T" in xy:
            add(p, "undetermined", "typechange")
        elif xy == "??":
            newish.append((p, "untracked"))
        elif "R" in xy or "C" in xy:
            deleted.append(orig)
            newish.append((p, "added"))
        elif "D" in xy:
            deleted.append(p)
        elif xy[0] == "A":
            newish.append((p, "added"))
        else:
            modified.append(p)

    # 1. generated: one batched attribute read
    if modified:
        rc, out = git(root, "check-attr", "-z", "--stdin", ATTR, stdin="\0".join(modified).encode() + b"\0")
        toks = _z(out) if rc == 0 else []
        gen = {toks[k] for k in range(0, len(toks) - 2, 3) if toks[k + 2] == "set"}
        for p in [p for p in modified if p in gen]:
            add(p, "generated", f"`{ATTR}` attribute")
        modified = [p for p in modified if p not in gen]

    # 2. eol-only: one batched diff; whatever still differs is NOT eol-only
    if modified:
        rc, out = git(root, "diff", "HEAD", "--ignore-cr-at-eol", "--name-only", "-z", "--", *modified)
        if rc == 0:
            differ = set(_z(out))
            for p in [p for p in modified if p not in differ]:
                add(p, "eol-only", "no difference once CR at EOL is ignored")
            modified = [p for p in modified if p in differ]

    # 3. format-only: parse both sides
    probes = 0
    for p in modified:
        parser = PARSERS.get(Path(p).suffix.lower())
        if parser is None or probes >= MAX_PARSE:
            add(p, "real", "content differs")
            continue
        probes += 1
        rc, old = git(root, "show", f"HEAD:{p}")
        try:
            same = rc == 0 and parser(old.decode("utf-8")) == parser((root / p).read_text(encoding="utf-8"))
        except Exception:
            add(p, "real", "does not parse on one side — no null proof")
            continue
        if same:
            add(p, "format-only", f"{Path(p).suffix} parses to equal data (re-serialised)")
        else:
            add(p, "real", "parsed data differs")

    # 4. rename-only: HEAD blob of a deleted path == filtered hash of a new path
    head_blob = {}
    if deleted:
        rc, out = git(root, "ls-tree", "-z", "HEAD", "--", *deleted)
        for line in _z(out):
            meta, _, path = line.partition("\t")
            head_blob[path] = meta.split()[-1]
    new_hash = {}
    files = [p for p, _ in newish if (root / p).is_file()]
    if files and head_blob:
        rc, out = git(root, "hash-object", "--stdin-paths", stdin="\n".join(files).encode() + b"\n")
        hashes = out.decode().split() if rc == 0 else []
        if len(hashes) == len(files):
            new_hash = dict(zip(files, hashes))
    by_blob: dict[str, list[str]] = {}
    for p, h in new_hash.items():
        by_blob.setdefault(h, []).append(p)
    paired = set()
    for d in deleted:
        twins = [p for p in by_blob.get(head_blob.get(d, ""), []) if p not in paired]
        if twins:
            paired.add(twins[0])
            add(f"{d} -> {twins[0]}", "rename-only", "moved; blob identical")
        else:
            add(d, "real", "deleted")
    for p, kind in newish:
        if p not in paired:
            add(p, "untracked" if kind == "untracked" else "real", "new path" if kind == "untracked" else "added")
    return _finish(root, entries)


def _finish(root: Path, entries: list[dict]) -> dict:
    counts = {c: 0 for c in CLASSES}
    for e in entries:
        counts[e["cls"]] += 1
    return {"repo": str(root), "entries": entries, "counts": counts}


def noise_count(res: dict) -> int:
    return sum(res["counts"][c] for c in NOISE)


def summary(res: dict, max_paths: int = 6) -> str:
    """One line: counts by class + the noise paths (capped). "" when there is no noise."""
    n = noise_count(res)
    if not res or n == 0:
        return ""
    c = res["counts"]
    parts = [f"{c[k]} {k}" for k in CLASSES if c[k]]
    noise = [e for e in res["entries"] if e["cls"] in NOISE]
    shown = "; ".join(f"{e['path']} ({e['cls']})" for e in noise[:max_paths])
    more = f"; +{len(noise) - max_paths} more" if len(noise) > max_paths else ""
    return f"{sum(c.values())} uncommitted path(s) in {res['repo']} = {', '.join(parts)}. Noise: {shown}{more}."


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Classify uncommitted paths as noise vs real.")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = classify(Path(a.repo))
    if res is None:
        print(f"tree-noise: {a.repo} is not a git repository")
        return 2
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    for e in res["entries"]:
        print(f"{e['cls']:<13} {e['path']}  — {e['why']}")
    c = res["counts"]
    print(f"\ntree-noise: {noise_count(res)} noise / {c['real']} real / {c['untracked']} untracked / "
          f"{c['undetermined']} undetermined under {res['repo']}")
    print("ruler: CR-at-EOL, parse-equality for .base/.yaml/.yml/.json, blob-identical renames, "
          f"`{ATTR}` attribute. Not covered: other whitespace, Markdown/code semantics, edited renames.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
