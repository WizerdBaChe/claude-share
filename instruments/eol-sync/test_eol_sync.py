#!/usr/bin/env python
"""Controls for eol_sync.py and the post-commit hook -- both directions, asserted on bytes.

Each case asserts on the VALUE the defect would change (the bytes on disk, the skipped
list), never on an exit label alone. Every repo is a throwaway under tempfile.

Run:  python -X utf8 tools/eol-sync/test_eol_sync.py
Exit: 0 = every control behaved as declared; 1 = the instrument is broken.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eol_sync  # noqa: E402

HOOK = HERE.parent / "git-hooks" / "post-commit"
ATTRS = "* text=auto eol=lf\n*.md text eol=crlf\n*.bat text eol=crlf\n"


def sh(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def new_repo(tmp: Path, name: str, hook: bool = False) -> Path:
    repo = tmp / name
    repo.mkdir()
    sh(repo, "init", "-q")
    sh(repo, "config", "user.name", "t")
    sh(repo, "config", "user.email", "t@example.invalid")
    sh(repo, "config", "core.autocrlf", "false")
    (repo / ".gitattributes").write_bytes(ATTRS.encode())
    if hook:
        (repo / "tools" / "git-hooks").mkdir(parents=True)
        (repo / "tools" / "eol-sync").mkdir(parents=True)
        shutil.copy2(HOOK, repo / "tools" / "git-hooks" / "post-commit")
        shutil.copy2(HERE / "eol_sync.py", repo / "tools" / "eol-sync" / "eol_sync.py")
        sh(repo, "config", "core.hooksPath", "tools/git-hooks")
    return repo


def commit(repo: Path, *paths: str) -> None:
    sh(repo, "add", "--", *paths)
    sh(repo, "commit", "-q", "-m", "c")


def report(ok: bool, name: str, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  -- ' + detail) if detail and not ok else ''}")
    return ok


def run() -> int:
    res: list[bool] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # E0 negative: every file already holds its pinned ending -> nothing to do
        repo = new_repo(tmp, "clean")
        (repo / "a.py").write_bytes(b"x = 1\ny = 2\n")
        (repo / "doc.md").write_bytes(b"# t\r\nbody\r\n")
        commit(repo, ".gitattributes", "a.py", "doc.md")
        rc = eol_sync.main(["--repo", str(repo), "--all", "--check"])
        res.append(report(rc == 0, "E0 pinned endings everywhere -> --check exit 0"))

        # E1 positive: an LF file under a CRLF pin (the Write-tool birth) is rewritten to CRLF
        (repo / "new.md").write_bytes(b"# new\nline\n")
        commit(repo, "new.md")
        rc_check = eol_sync.main(["--repo", str(repo), "--all", "--check"])
        before = (repo / "new.md").read_bytes()
        eol_sync.main(["--repo", str(repo), "--commit", "HEAD"])
        after = (repo / "new.md").read_bytes()
        res.append(report(rc_check == 1 and before == b"# new\nline\n"
                          and after == b"# new\r\nline\r\n",
                          "E1 LF file under eol=crlf -> --check 1, then bytes become CRLF",
                          f"rc={rc_check} after={after!r}"))
        res.append(report(sh(repo, "status", "--porcelain") == "",
                          "E2 rewritten file is clean in git status"))

        # E3 positive, other direction: a CRLF file under an LF pin is rewritten to LF
        (repo / "b.py").write_bytes(b"a = 1\r\nb = 2\r\n")
        commit(repo, "b.py")
        eol_sync.main(["--repo", str(repo), "--commit", "HEAD"])
        res.append(report((repo / "b.py").read_bytes() == b"a = 1\nb = 2\n",
                          "E3 CRLF file under eol=lf -> bytes become LF"))

        # E4 safety: a dirty file is never rewritten, and is named as skipped
        (repo / "dirty.md").write_bytes(b"one\n")
        commit(repo, "dirty.md")
        (repo / "dirty.md").write_bytes(b"one\ntwo, uncommitted\n")
        rows = eol_sync.eol_rows(repo, ["dirty.md"])
        out = eol_sync.realign(repo, rows, check=False)
        res.append(report((repo / "dirty.md").read_bytes() == b"one\ntwo, uncommitted\n"
                          and [p for p, _ in out["skipped"]] == ["dirty.md"],
                          "E4 dirty file untouched and reported skipped", str(out)))
        sh(repo, "checkout", "--", "dirty.md")

        # E5 scope: --commit HEAD touches only that commit's files
        (repo / "old.md").write_bytes(b"old\n")
        commit(repo, "old.md")
        (repo / "other.md").write_bytes(b"other\n")
        commit(repo, "other.md")
        eol_sync.main(["--repo", str(repo), "--commit", "HEAD"])
        res.append(report((repo / "other.md").read_bytes() == b"other\r\n"
                          and (repo / "old.md").read_bytes() == b"old\n",
                          "E5 --commit HEAD rewrites the commit's file only"))

        # E6 binary content is never touched
        (repo / "blob.bin").write_bytes(b"\x00\x01\n\x02")
        commit(repo, "blob.bin")
        eol_sync.main(["--repo", str(repo), "--all"])
        res.append(report((repo / "blob.bin").read_bytes() == b"\x00\x01\n\x02",
                          "E6 binary file untouched"))

        # E9 scale: a migration-sized commit (first live --all hit WinError 206 at ~1500 paths)
        big = new_repo(tmp, "big")
        names = [f"docs/a-rather-long-folder-name/note-number-{i:05d}.md" for i in range(1600)]
        (big / "docs" / "a-rather-long-folder-name").mkdir(parents=True)
        for n in names:
            (big / n).write_bytes(b"x\n")
        (big / "[odd] name.md").write_bytes(b"glob chars\n")   # E10: pathspec magic must be literal
        sh(big, "add", "-A")
        sh(big, "commit", "-q", "-m", "c")
        rc = eol_sync.main(["--repo", str(big), "--all"])
        ok_all = all((big / n).read_bytes() == b"x\r\n" for n in names)
        res.append(report(rc == 0 and ok_all and sh(big, "status", "--porcelain") == "",
                          "E9 1600-path migration -> every file CRLF, tree clean (no WinError 206)",
                          f"rc={rc} ok_all={ok_all}"))
        res.append(report((big / "[odd] name.md").read_bytes() == b"glob chars\r\n",
                          "E10 a path with glob characters is realigned literally"))

        # E7 end-to-end: the hook itself fires on commit (positive) ...
        hrepo = new_repo(tmp, "hooked", hook=True)
        (hrepo / "note.md").write_bytes(b"# note\nhuman text\n")
        (hrepo / "run.bat").write_bytes(b"@echo off\necho hi\n")
        (hrepo / "tool.py").write_bytes(b"print(1)\n")
        commit(hrepo, ".gitattributes", "note.md", "run.bat", "tool.py")
        res.append(report((hrepo / "note.md").read_bytes() == b"# note\r\nhuman text\r\n"
                          and (hrepo / "run.bat").read_bytes() == b"@echo off\r\necho hi\r\n"
                          and (hrepo / "tool.py").read_bytes() == b"print(1)\n",
                          "E7 post-commit hook realigns md/bat to CRLF, leaves LF py alone",
                          repr((hrepo / "note.md").read_bytes())))
        res.append(report(eol_sync.main(["--repo", str(hrepo), "--wiring"]) == 0,
                          "W1 wired repo -> --wiring exit 0"))
        # ... and is absent without core.hooksPath (negative: the wiring is what makes it fire)
        sh(hrepo, "config", "--unset", "core.hooksPath")
        res.append(report(eol_sync.main(["--repo", str(hrepo), "--wiring"]) == 1,
                          "W2 hooksPath unset -> --wiring exit 1"))
        (hrepo / "note2.md").write_bytes(b"plain\n")
        commit(hrepo, "note2.md")
        res.append(report((hrepo / "note2.md").read_bytes() == b"plain\n",
                          "E8 without core.hooksPath nothing realigns (wiring is load-bearing)"))

    total, good = len(res), sum(res)
    print(f"\ncontrols: {good}/{total}")
    return 0 if good == total else 1


if __name__ == "__main__":
    raise SystemExit(run())
