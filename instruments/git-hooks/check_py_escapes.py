r"""pre-commit check: refuse staged Python that contains an invalid escape sequence.

Python 3.12 reports `"\S"`, `"dir\Sub"`, `"\|"` in a non-raw literal as a
SyntaxWarning on stderr and still compiles the file, so `python -m py_compile`
exits 0 and every "py_compile clean" acceptance passes it (calibrated
2026-10-03 on hooks/model_cap_guard.py before d16016a: plain py_compile exit 0,
`-W error::SyntaxWarning` exit 1). Python has announced these escapes will
eventually become a SyntaxError; for a hook that means an import failure, and a
deny-capable command hook that cannot start fails OPEN.

What it checks: the STAGED blob of every added/copied/modified/renamed `*.py`
(`git show :<path>`), not the working tree, so the verdict is about the bytes
being committed. What it rules on: invalid-escape SyntaxWarnings only -> exit 1.
What it does not rule on: a genuine SyntaxError (a fixture may be broken on
purpose) and any failure of its own -> printed as a notice, exit 0.

Fix for a hit: escape the backslash (`dir\\Sub`), or make the literal raw
(`r"..."`) when no other escape in it is meant -- either keeps the text the
literal produces; forward slashes change it.

Wired by: tools/git-hooks/pre-commit (core.hooksPath tools/git-hooks).
review-when: Python turns invalid escapes into a SyntaxError (then compile()
raises instead of warning and the SyntaxError branch must become the blocking
one); core.hooksPath changes.
"""
import subprocess
import sys
import warnings


def staged_py():
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z", "--", "*.py"],
        capture_output=True, check=True,
    ).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def check(path):
    blob = subprocess.run(["git", "show", f":{path}"], capture_output=True, check=True).stdout
    src = blob.decode("utf-8", errors="replace")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            compile(src, path, "exec")
        except SyntaxError as e:
            return [], f"{path}:{e.lineno}: SyntaxError ({e.msg}) -- not ruled on by this check"
    hits = [
        (w.lineno, str(w.message))
        for w in caught
        if issubclass(w.category, SyntaxWarning) and "escape sequence" in str(w.message)
    ]
    return hits, None


def main():
    try:
        paths = staged_py()
    except Exception as e:  # infrastructure failure: cannot determine -> do not veto
        print(f"pre-commit py-escape check skipped: {e}", file=sys.stderr)
        return 0
    failed = 0
    for path in paths:
        try:
            hits, note = check(path)
        except Exception as e:
            print(f"pre-commit py-escape check could not read {path}: {e}", file=sys.stderr)
            continue
        if note:
            print(note, file=sys.stderr)
        for lineno, msg in hits:
            print(f"{path}:{lineno}: {msg}", file=sys.stderr)
            failed += 1
    if failed:
        print(
            f"commit refused: {failed} invalid escape sequence(s) in staged Python. "
            "Escape the backslash (\\\\) or use a raw string, re-stage, commit again.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
