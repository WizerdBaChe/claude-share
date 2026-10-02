#!/usr/bin/env python3
"""class closure — does every control suite carry a case it must call `undetermined`?

Status: live 2026-09-09 | severity: FAIL for any suite that lacks the case,
`undetermined` for a suite this tool cannot read (excluded from every count,
never folded) | controls: `controls.py` (two-sided, `ALL PASS n/n`) | wired:
`ops/references/integrity-sweep.md` check 33; at SAVE time through
`hooks/golive_check.py` (`closure_gap()` imports `suites()` + `classify()` from
here); HMI point `health-checks.class-closure` (gate known-good) | principle:
PH-11 / AP-62 (`ops/references/principle-design-guide.md`).

REGROWTH 2026-09-23. Fourteen days after the drain below, 10 suites lacked the
case again (2 tools/, 4 hooks/tests/, 4 hook --selftest): every runner was a
manual sweep, and the HMI watched only `controls.py`, never this verdict. A
FAIL nobody runs is inert, so the verdict now runs where a suite is written
(golive_check) and in the monitor. Backfilling the 10 found real folds again:
five hooks str()-ed a non-string session_id / agent_type into a record as if
it were one, moc_closeout_notice logged an unmeasured lag as `commits=0`,
past_work_recall_inject lost its whole row on a malformed leg, feedback-pool
folded an unknown target prefix into a target, recall crashed on a non-list leg.

PROMOTED 2026-09-09, the day it was born. The tool shipped with a WARN branch and
a 28-name `LEGACY_LACKING` set, and one recorded promotion trigger: the set
reaching empty. All 28 were backfilled the same day -- 11 rule-tier suites by the
main session, 17 across four dispatched slices -- so the set and the WARN branch
are gone and every `lacks` is now FAIL. What the drain found is the argument for
the severity: five hooks were folding unclassifiable input into a real verdict
(a non-string url recorded as a navigation that happened; a non-string file_path
counted as a read file, walking a session toward its fieldwork threshold), and
several instruments had a correct `undetermined` branch that no case had ever
reached. None of it was visible from the counts.

WHAT IT DETERMINES, AND WHAT IT LEAVES TO AUDIT
-----------------------------------------------
AP-62 says an instrument's object classes are enumerated and CLOSED over its own
corpus: an input matching no declared class is reported `undetermined` and
excluded from every verdict count, never folded into the nearest class. Folding
is silent because the count stays plausible (2026-09-08: `L-nnn.md` folded into
broken-link, 9/9 false; PNG folded into mixed-line-endings, 31/31 false).

The half of AP-62 a machine can decide is whether the instrument's control suite
EVER asserts that verdict: a suite that never names `undetermined` has no
specimen for it, so the class is either absent from the instrument or never
exercised — either way the closure was never proved. That is what this counts.
The other half — one specimen PER declared class — needs the class list, which
lives in each instrument's own vocabulary; it stays `detect: audit` in the guide.

THE PROXY, STATED PLAINLY
-------------------------
"Carries the case" is decided by a WORD-LEVEL match (MARKER below) over the
suite's CODE tokens -- string literals and identifiers; since 2026-09-23 a
comment, a trailing comment or a docstring no longer counts (measured that
day: 1 of 51 suites carried the word only in a comment). A code token still
cannot tell a case that runs from a string that is never asserted, so a suite
can satisfy it without exercising anything. That is the remaining
false-positive shape; the matching line is printed so the reader can see
which it was. The false-negative shape is a real case whose name never uses
the word; golive_check's save-time notice asks for the word in the case name.
Both shapes are facts about EXECUTION, which this static tool cannot see:
`exercise.py` (same folder, since 2026-09-23) runs every suite this module
enumerates under a line probe and reports `named-only` (the word, no case ran)
and `unnamed-exercise` (a branch ran, the word is missing). It imports
`suites()` / `classify()` / `MARKER` from here -- one enumeration, one marker.
This module stays the save-time and FAIL-severity half because it is cheap;
`inconclusive` is deliberately NOT in the marker: it is a
third verdict for "the scenario did not occur" (pol.py, timeouts), not the
unclassifiable-input class AP-62 names.

ENUMERATION (PH-11 / AP-61: the vocabulary is the corpus, never a list here)
------------------------------------------------------------------------------
  * every `tools/*/controls.py`;
  * every `hooks/tests/*.py`;
  * the suite each registered hook DECLARES in its `Proof-of-life:` line, read
    through pol.py's own grammar so the two checks never disagree on what a
    declaration is. A hook that declares nothing is check 31's finding, not
    this one's, and is not counted.
A suite reached by more than one route is counted once, by repo-relative path.
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOME / "tools" / "hook-proof-of-life"))
import pol  # noqa: E402  (registered_hooks, declaration — the shared grammar)

MARKER = re.compile(r"\b(?:undetermined|unclassifiable|unclassified|UNDET)\b", re.I)
CLASSES = ("carries", "lacks", "undetermined")

LEGACY_DATE = "2026-09-09"   # the day the born-lacking set was measured AND drained


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def suites(root: Path | None = None, settings: Path | None = None) -> dict[str, str]:
    """-> {repo-relative suite path: how it was reached}. Enumerates, never judges."""
    root = root or HOME
    settings = settings or (root / "settings.json")
    found: dict[str, str] = {}
    for p in sorted(root.glob("tools/*/controls.py")):
        found.setdefault(_rel(p, root), "tools/*/controls.py")
    for p in sorted(root.glob("hooks/tests/*.py")):
        found.setdefault(_rel(p, root), "hooks/tests/*.py")
    for name in pol.registered_hooks(settings):
        kind, detail = pol.declaration(root / "hooks" / name)
        if kind != "executable":
            continue  # check 31's finding (uncovered / manual / undetermined), not ours
        parts = detail.split()
        if len(parts) < 2:
            continue
        found.setdefault(_rel(root / parts[1], root), f"declared by hooks/{name}")
    return found


def _docstring_lines(tree: ast.AST) -> set[int]:
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    return lines


def _code_hit(text: str) -> tuple[int, str] | None:
    """First (line number, line) where MARKER occurs in a CODE token of Python source --
    a string literal or an identifier -- never in a comment or a docstring.
    Raises SyntaxError / tokenize.TokenError when the text is not Python."""
    doc = _docstring_lines(ast.parse(text))
    src = text.splitlines()
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE):
            continue
        if tok.type == tokenize.STRING and tok.start[0] in doc:
            continue
        if MARKER.search(tok.string):
            no = tok.start[0]
            return no, src[no - 1] if no <= len(src) else tok.string
    return None


def classify(path: Path) -> tuple[str, str]:
    """-> (class, detail). An unreadable suite is `undetermined`, never a guess.

    For a .py suite only CODE tokens count (2026-09-23): a comment or docstring naming
    the class is not a case. Python that does not parse is `undetermined`, not `lacks`.
    """
    try:
        text = path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return "undetermined", "declared suite does not exist"
    except UnicodeDecodeError as exc:
        return "undetermined", f"not UTF-8 text ({exc.reason} at byte {exc.start})"
    except OSError as exc:
        return "undetermined", f"{type(exc).__name__}: {exc}"
    if path.suffix == ".py":
        try:
            hit = _code_hit(text)
        except (SyntaxError, ValueError, tokenize.TokenError) as exc:
            return "undetermined", f"not parseable as Python ({type(exc).__name__}: {exc})"[:160]
        if hit:
            return "carries", f"L{hit[0]}: {hit[1].strip()[:110]}"
        return "lacks", "no code line (comments and docstrings excluded) names an unclassifiable/undetermined case"
    for no, line in enumerate(text.splitlines(), 1):
        if MARKER.search(line):
            return "carries", f"L{no}: {line.strip()[:110]}"
    return "lacks", "no line names an unclassifiable/undetermined case"


def scan(root: Path | None = None, settings: Path | None = None) -> list[dict]:
    root = root or HOME
    rows = []
    for rel, via in suites(root, settings).items():
        kind, detail = classify(root / rel)
        rows.append({"suite": rel, "via": via, "class": kind, "detail": detail})
    return rows


def verdict(rows: list[dict]) -> tuple[str, str]:
    """-> (level, line). FAIL / PASS from the rows; undetermined never counts.

    There is no downgrade path: since the promotion (docstring), a lacking suite
    is FAIL wherever it came from. WARN is unreachable, which `controls.py`
    asserts as a regression case so it cannot come back unnoticed.
    """
    lacking = [r["suite"] for r in rows if r["class"] == "lacks"]
    undet = [r["suite"] for r in rows if r["class"] == "undetermined"]
    note = ""
    if undet:
        note += f"; {len(undet)} undetermined (excluded from every count above)"
    if lacking:
        return "FAIL", (f"FAIL: {len(lacking)} suite(s) lack an unclassifiable case: "
                        f"{', '.join(lacking)}{note}")
    return "PASS", f"PASS: every readable suite carries an unclassifiable case{note}"


def report(rows: list[dict], verbose: bool = False) -> int:
    counts = {c: sum(1 for r in rows if r["class"] == c) for c in CLASSES}
    print(f"class-closure: {len(rows)} control suite(s) — {counts['carries']} carry an "
          f"unclassifiable case, {counts['lacks']} lack one, {counts['undetermined']} undetermined")
    for r in rows:
        if r["class"] == "lacks":
            print(f"  lacks  {r['suite']}  -> add one deliberately unclassifiable input "
                  f"asserting `undetermined` (AP-62)")
        elif r["class"] == "undetermined":
            print(f"  undetermined  {r['suite']}  -> {r['detail']}  (via {r['via']})")
        elif verbose:
            print(f"  carries       {r['suite']}  {r['detail']}")
    level, line = verdict(rows)
    print(line)
    return 1 if level == "FAIL" else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=None, help="repo root (controls only)")
    ap.add_argument("--json", action="store_true", help="rows as JSON, no verdict line")
    ap.add_argument("--verbose", action="store_true", help="also print the carrying suites")
    a = ap.parse_args(argv)
    rows = scan(a.root)
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    return report(rows, a.verbose)


if __name__ == "__main__":
    sys.exit(main())
