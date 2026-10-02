"""Two-sided calibration for tools/shell-audit/invariants.py — run:

    python tools/shell-audit/controls.py

AP-62 (`ops/references/principle-design-guide.md` PH-11): an instrument's object
classes are enumerated and closed, and its controls carry ONE SPECIMEN PER CLASS
plus an input it must still catch. A checker that answers "clean" to everything
scores 100% on a one-sided calibration and reports zero defects forever — which
is exactly how the line-endings invariant stood at `31 MIXED` for weeks with 31
binaries and 0 text files in the count.

The cases run against a REAL temporary git repo, because `ls-files` is what
decides the population and a fixture that skipped git would not exercise it.

EXTENDING (AP-61): a class added to `invariants.content_class` needs a specimen
file here; a new invariant needs its own known-bad and known-good below. The
closure of that class set is itself a case: a tracked file whose bytes cannot be
read fits neither `text` nor `binary`, and the specimen block at the bottom
asserts it gets the THIRD verdict — named, and absent from both counts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LOCK_BYTES = 4096

sys.path.insert(0, str(Path(__file__).resolve().parent))

import invariants  # noqa: E402

FAILS: list[str] = []
RAN: list[str] = []


def check(name: str, got, want) -> None:
    # Case names stay ASCII even where the SPECIMEN is not: this prints to
    # whatever console the caller has, and a cp950 terminal would turn a passing
    # suite into a UnicodeEncodeError. The non-ASCII name lives in the fixture
    # and is asserted through a boolean.
    RAN.append(name)
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if got == want else 'FAIL'} {name}")


def _git(repo, *args):
    subprocess.run(["git", "-C", repo] + list(args),
                   capture_output=True, text=True, check=False)


def _fixture(root: str, files: dict[str, bytes]) -> str:
    os.makedirs(root, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "controls@local")
    _git(root, "config", "user.name", "controls")
    # core.autocrlf must not rewrite what we are measuring
    _git(root, "config", "core.autocrlf", "false")
    for name, data in files.items():
        p = os.path.join(root, name)
        os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
        with open(p, "wb") as fh:
            fh.write(data)
    _git(root, "add", "-A")
    return root


def _make_unreadable(path):
    """Make `path` genuinely unopenable and return the undo. NOT a stub: the
    caller asserts the file really cannot be read before trusting the verdict,
    because a setup that quietly failed would turn the AP-62 case below into a
    control that passes without exercising anything."""
    if os.name == "nt":
        import msvcrt
        fh = open(path, "r+b")
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, LOCK_BYTES)   # region lock blocks other handles

        def undo():
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, LOCK_BYTES)
            fh.close()
        return undo
    mode = os.stat(path).st_mode
    os.chmod(path, 0)
    return lambda: os.chmod(path, mode)


CLEAN_LF = b"alpha\nbeta\ngamma\n"
CLEAN_CRLF = b"alpha\r\nbeta\r\ngamma\r\n"
MIXED_TEXT = b"alpha\r\nbeta\ngamma\r\n"          # the real defect (L-024)
# A binary whose bytes contain BOTH endings — the specimen that used to be
# folded into `text` and produced the 31/31 false positives.
BINARY_MIXED = b"\x89PNG\r\n\x1a\n\x00\x00\x00IHDR\r\npayload\nmore\r\n\x00\xff"

tmp = tempfile.mkdtemp(prefix="shell-audit-controls-")
try:
    # --- class specimens ---------------------------------------------------
    check("content_class: LF text", invariants.content_class(CLEAN_LF), "text")
    check("content_class: CRLF text", invariants.content_class(CLEAN_CRLF), "text")
    check("content_class: mixed text", invariants.content_class(MIXED_TEXT), "text")
    check("content_class: binary with both endings",
          invariants.content_class(BINARY_MIXED), "binary")

    # --- known-GOOD: a clean repo holds --------------------------------------
    good = _fixture(os.path.join(tmp, "good"), {
        "a.md": CLEAN_LF, "b.md": CLEAN_CRLF, "img.png": BINARY_MIXED,
    })
    ok, detail, _ = invariants.check_line_endings(good)
    check("known-GOOD: clean repo holds", ok, True)
    check("known-GOOD: binary counted, not judged", "1 binary excluded" in detail, True)

    # --- known-BAD: one mixed TEXT file must still be caught -----------------
    bad = _fixture(os.path.join(tmp, "bad"), {
        "a.md": CLEAN_LF, "broken.md": MIXED_TEXT, "img.png": BINARY_MIXED,
    })
    ok, detail, hint = invariants.check_line_endings(bad)
    check("known-BAD: mixed text file caught", ok, False)
    check("known-BAD: names the repair site", "broken.md" in detail, True)
    check("known-BAD: binary not in the count", "1 MIXED" in detail, True)
    check("known-BAD: hint reaches the full list", "--list-mixed" in hint, True)
    check("known-BAD: --list-mixed lists it",
          invariants._mixed_text_files(bad), ["broken.md"])

    # --- the regression this widening could have caused ----------------------
    # A binary-only repo must report CLEAN, and a repo whose ONLY defect is a
    # text file must NOT be silenced by the binary class existing.
    binonly = _fixture(os.path.join(tmp, "binonly"), {"img.png": BINARY_MIXED})
    check("binary-only repo is clean", invariants.check_line_endings(binonly)[0], True)

    # --- the population, not the verdict: a path git C-QUOTES -----------------
    # `ls-files` quotes any path with a byte outside ASCII, and the scan then
    # looks for a file at the literal quoted name. It is not there, so the file
    # left the denominator entirely -- neither counted, nor named, nor ruled on.
    # This is the earlier fold one layer up: the class set was closed, but the
    # POPULATION it classified was silently short. Live instance when this was
    # written: 1 of 1442 tracked files in ~/.claude.
    quoted = _fixture(os.path.join(tmp, "quoted"), {
        "a.md": CLEAN_LF, "驗收報告.md": MIXED_TEXT,
    })
    ok, detail, _ = invariants.check_line_endings(quoted)
    check("quoted path: a mixed TEXT file with a non-ASCII name is caught",
          ok, False)
    check("quoted path: it is named in the detail, in a form that can be opened",
          "驗收報告.md" in detail, True)
    check("quoted path: the population is whole -- 2 text, nothing dropped",
          invariants._scan_line_endings(quoted)[2], {"text": 2, "binary": 0})

    # --- tracked, and there is nothing at that path to read -------------------
    ghost = _fixture(os.path.join(tmp, "ghost"),
                     {"a.md": CLEAN_LF, "gone.md": MIXED_TEXT})
    os.remove(os.path.join(ghost, "gone.md"))
    g_mixed, g_third, g_counts = invariants._scan_line_endings(ghost)
    check("absent path: named as undetermined rather than skipped",
          g_third, ["gone.md (tracked, absent from the worktree)"])
    check("absent path: in NEITHER class count", g_counts, {"text": 1, "binary": 0})
    check("absent path: not ruled a defect -- bytes nobody read are not rot",
          (invariants.check_line_endings(ghost)[0], g_mixed), (True, []))
    # Inverted 2026-09-09, and the result is worth stating because it is not the
    # obvious one. The three quoted-path cases survive removing EITHER defence
    # (`-z` suppresses C-quoting on its own, and so does core.quotePath=false);
    # all three fail only with both gone, i.e. against the code as it actually
    # shipped. The absent-path cases: the first falls to a bare `continue`, the
    # second to folding the file into `text`, and the third holds under every
    # inversion tried -- it is kept as the statement of what must not happen, and
    # is NOT a discriminator. A control whose failure mode nobody has seen is a
    # sentence, not a measurement, and saying which is which here costs one line.

    # --- AP-62: the tracked file that fits NEITHER declared class -------------
    # `content_class` is closed over {text, binary}, but classifying needs the
    # bytes, and a tracked file that cannot be opened has none. That input gets
    # the third verdict: `_scan_line_endings` names it, keeps it out of both
    # class counts, and `check_line_endings` refuses to rule on it. The
    # specimen's bytes are MIXED_TEXT, so folding it into `text` would have
    # produced a `1 MIXED` verdict on a file nobody read — the same 0%-precision
    # shape the PNG fold produced. A clean verdict here is the proof it was
    # excluded rather than quietly counted.
    sealed_repo = _fixture(os.path.join(tmp, "sealed"), {
        "a.md": CLEAN_LF, "img.png": BINARY_MIXED, "sealed.md": MIXED_TEXT,
    })
    undo = _make_unreadable(os.path.join(sealed_repo, "sealed.md"))
    try:
        try:
            open(os.path.join(sealed_repo, "sealed.md"), "rb").read()
            really_sealed = False
        except OSError:
            really_sealed = True
        check("specimen setup: the file really cannot be opened", really_sealed, True)
        mixed, third, counts = invariants._scan_line_endings(sealed_repo)
        check("undetermined: named, with the reason",
              third, ["sealed.md (PermissionError)"])
        check("undetermined: in NEITHER class count (not folded into text/binary)",
              counts, {"text": 1, "binary": 1})
        ok, detail, _ = invariants.check_line_endings(sealed_repo)
        check("undetermined: excluded from the verdict — mixed bytes nobody read "
              "are not a defect", (ok, mixed), (True, []))
        check("undetermined: reported in the detail, so the count reads as a floor",
              "1 undetermined: sealed.md" in detail, True)
    finally:
        undo()
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print(f"ALL PASS {len(RAN)}/{len(RAN)} (class specimens, known-good, known-bad, "
      "regression, quoted path, absent path, no-class-fits)")
