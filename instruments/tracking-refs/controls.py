#!/usr/bin/env python3
"""Two-sided calibration for refs.py — run: python tools/tracking-refs/controls.py

Builds throwaway git repos and asserts every class the tool can emit. Known-BAD
side: a committed surface pointing at an untracked file is `dangling` and exits 1,
from the root form, the relative-to-skill form, the absolute Windows form and the
backslash form. Known-GOOD side: the same pointer after the target is committed is
silent and exits 0; an ignored target is `ignored`, an uncommitted source is
`pending`, a non-surface or archived source is not read at all — none of them
FAIL. Unclassifiable side (AP-62): a target found nowhere is `undetermined` and
excluded from the verdict, and a root that is not a git work tree makes the whole
run `undetermined` (exit 2), never "0 dangling".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import refs  # noqa: E402

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    ok = got == want
    if not ok:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if ok else 'FAIL'} {name}")


def git(root: str, *args: str) -> None:
    subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t",
                    "-c", "core.autocrlf=false", *args],
                   check=True, capture_output=True)


def write(root: str, rel: str, text: str) -> None:
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def repo(files: dict[str, str], commit: list[str], extra: dict[str, str] | None = None) -> str:
    root = tempfile.mkdtemp(prefix="tracking-refs-")
    git(root, "init", "-q")
    for rel, text in files.items():
        write(root, rel, text)
    if commit:
        git(root, "add", "--", *commit)
        git(root, "commit", "-q", "-m", "fixture")
    for rel, text in (extra or {}).items():
        write(root, rel, text)
    return root


def run_cli(root: str) -> int:
    return subprocess.run([sys.executable, str(HERE / "refs.py"), "--root", root],
                          capture_output=True, text=True).returncode


def main() -> int:
    roots: list[str] = []
    try:
        # 1 known-BAD: the 2026-09-18 shape — committed CLAUDE.md indexes an untracked rule
        r = repo({"CLAUDE.md": "see `rules/layout.md`\n", "rules/layout.md": "x\n"}, ["CLAUDE.md"])
        roots.append(r)
        res = refs.scan(r)
        check("1 committed pointer -> untracked target is dangling", list(res["dangling"]), ["rules/layout.md"])
        check("1 its source is named", res["dangling"].get("rules/layout.md"), ["CLAUDE.md"])
        check("1 CLI exits 1 (the positive control fires)", run_cli(r), 1)

        # 2 known-GOOD: same pointer, target committed
        git(r, "add", "--", "rules/layout.md")
        git(r, "commit", "-q", "-m", "target")
        res = refs.scan(r)
        check("2 target committed -> no dangling", res["dangling"], {})
        check("2 CLI exits 0", run_cli(r), 0)

        # 3 relative-to-skill form (the comsol skill's `tools/sync_rules.py`)
        r = repo({"skills/s/SKILL.md": "run `python tools/sync.py`\n", "skills/s/tools/sync.py": "\n"},
                 ["skills/s/SKILL.md"])
        roots.append(r)
        check("3 relative ref resolves under the skill and is dangling",
              list(refs.scan(r)["dangling"]), ["skills/s/tools/sync.py"])

        # 4 absolute Windows + backslash forms fold to the same repo path
        r = repo({"skill-trigger-dict.md": r"C:\Users\someone\.claude\skills\new-skill\ and hooks\\g.py" + "\n",
                  "skills/new-skill/SKILL.md": "x\n", "hooks/g.py": "\n"}, ["skill-trigger-dict.md"])
        roots.append(r)
        check("4 absolute and backslash forms are dangling",
              sorted(refs.scan(r)["dangling"]), ["hooks/g.py", "skills/new-skill"])

        # 5 ignored target -> REPORT, not FAIL
        r = repo({".gitignore": "tools/t/out/\n", "ops/a.md": "read `tools/t/out/status.json`\n",
                  "tools/t/out/status.json": "{}\n"}, [".gitignore", "ops/a.md"])
        roots.append(r)
        res = refs.scan(r)
        check("5 ignored target is `ignored`", list(res["ignored"]), ["tools/t/out/status.json"])
        check("5 ignored target is not dangling", res["dangling"], {})
        check("5 CLI exits 0", run_cli(r), 0)

        # 6 both halves uncommitted -> pending
        r = repo({"README.md": "x\n"}, ["README.md"],
                 {"rules/new.md": "see `tools/new/x.py`\n", "tools/new/x.py": "\n"})
        roots.append(r)
        res = refs.scan(r)
        check("6 untracked source -> pending", list(res["pending"]), ["tools/new/x.py"])
        check("6 pending is not dangling", res["dangling"], {})

        # 7 non-surface and archived sources are not read
        r = repo({"outputs/rec.md": "old `rules/gone.md`\n", "archive/ops/b.md": "`rules/gone.md`\n",
                  "rules/gone.md": "x\n"}, ["outputs/rec.md", "archive/ops/b.md"])
        roots.append(r)
        check("7 record/archive sources never produce a finding",
              refs.scan(r), {"dangling": {}, "pending": {}, "ignored": {}, "undetermined": {}})

        # 8 AP-62 specimen: a target found nowhere is `undetermined`, excluded from the verdict
        r = repo({"ops/c.md": "the rig runs `tools/deposit_gate.py`\n"}, ["ops/c.md"])
        roots.append(r)
        res = refs.scan(r)
        check("8 missing target is undetermined", list(res["undetermined"]), ["tools/deposit_gate.py"])
        check("8 undetermined does not move the exit code", run_cli(r), 0)

        # 9 AP-62 whole-run specimen: not a git work tree -> undetermined, exit 2
        r = tempfile.mkdtemp(prefix="tracking-refs-nogit-")
        roots.append(r)
        write(r, "CLAUDE.md", "`rules/x.md`\n")
        write(r, "rules/x.md", "x\n")
        check("9 non-repo root -> scan returns None", refs.scan(r), None)
        check("9 CLI exits 2 (undetermined), not 0", run_cli(r), 2)

        # 10 a tracked DIRECTORY target is resolved (no false dangling on `tools/x`)
        r = repo({"CLAUDE.md": "`tools/x` and `tools/x/y.py`\n", "tools/x/y.py": "\n"},
                 ["CLAUDE.md", "tools/x/y.py"])
        roots.append(r)
        check("10 tracked dir + file -> silent", refs.scan(r)["dangling"], {})

        # 11 name form: CLAUDE.md indexes a rule by bare name (the replay miss of 2026-09-18)
        r = repo({"CLAUDE.md": "rules index: `layout-convergence` · `plain-word`\n",
                  "rules/layout-convergence.md": "x\n"}, ["CLAUDE.md"])
        roots.append(r)
        res = refs.scan(r)
        check("11 bare rule name -> dangling rules/<name>.md",
              list(res["dangling"]), ["rules/layout-convergence.md"])
        check("11 a backticked word naming no file is not even undetermined",
              res["undetermined"], {})

        # 12 name form: trigger-dict heading names an untracked skill dir
        r = repo({"skill-trigger-dict.md": "### new-skill（x）\n- keywords\n",
                  "skills/new-skill/SKILL.md": "x\n"}, ["skill-trigger-dict.md"])
        roots.append(r)
        check("12 dict heading -> dangling skills/<name>",
              list(refs.scan(r)["dangling"]), ["skills/new-skill"])
    finally:
        for r in roots:
            shutil.rmtree(r, ignore_errors=True)

    total = sum(1 for _ in open(__file__, encoding="utf-8") if _.lstrip().startswith("check("))
    if FAILS:
        print(f"FAILED {len(FAILS)}: " + " | ".join(FAILS))
        return 1
    print(f"ALL PASS {total}/{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
