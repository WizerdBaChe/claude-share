#!/usr/bin/env python3
"""Regression cover for the anchor layer, written when it was loosened.

Loosening a gate is only defensible if you can show it still catches what it was
built for. On 2026-08-16 layer 4 rejected a report containing a real
directory-traversal finding because a second finding cited line 79 while quoting
line 80. The fix separates a CITATION error from a FABRICATION. The risk the fix
introduces is obvious and must be measured, not asserted:

    does an invented quote still void the report?   <- case 4, the one that matters

Every case below states the verdict it expects and why. Case 4 is a replica of
the 2026-08-15 fabrication shape: a quote that reads plausibly and appears
nowhere in the file.

Run:  python test_score_anchor.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import score_redteam as sr  # noqa: E402

SOURCE = """\
def load(path):
    handle = open(path)
    data = handle.read()
    return data


def save(path, data):
    handle = open(path)
    handle.write(data)
    return True
"""
# `    handle = open(path)` deliberately occurs twice (lines 2 and 8) so the
# ambiguous case is real rather than contrived.


def finding(**over):
    base = {"file": "mod.py", "line": 2, "quote": "    handle = open(path)",
            "defect": "file handle is never closed",
            "failure": "repeated calls exhaust the descriptor table",
            "severity": "medium"}
    base.update(over)
    return base


CASES = [
    ("exact anchor", [finding(line=3, quote="    data = handle.read()")],
     ["OK"], "ACCEPTED", None,
     "quote matches the cited line -- nothing to do"),

    ("exact anchor on a line whose text repeats",
     [finding(line=2, quote="    handle = open(path)")],
     ["OK"], "ACCEPTED", None,
     "the same text also sits at line 8; an exact hit at the CITED line must "
     "short-circuit before ambiguity is even considered"),

    ("off-by-one, unique elsewhere",
     [finding(line=4, quote="    data = handle.read()")],
     ["MISALIGNED"], "ACCEPTED-WITH-REPAIRS", 3,
     "THE 2026-08-16 CASE: verbatim quote, wrong line number. Must survive and be "
     "repaired to line 3"),

    ("invented quote",
     [finding(line=2, quote="    handle.close()  # always closed")],
     ["FABRICATED"], "REJECTED", None,
     "THE REGRESSION GUARD: plausible text that is nowhere in the file. Must still "
     "void the report"),

    ("quote occurs twice",
     [finding(line=5, quote="    handle = open(path)")],
     ["MISALIGNED-AMBIGUOUS"], "ACCEPTED-WITH-REPAIRS", None,
     "the model read the file; which occurrence it meant is unrecoverable, so no "
     "repair is invented"),

    ("declared unanchorable", [finding(quote="SOURCE-NOT-FOUND")],
     ["NOT-FOUND-DECLARED"], "ACCEPTED", None,
     "an honest answer, accepted since v1"),

    ("missing file", [finding(file="nope.py")],
     ["BAD-PATH"], "REJECTED", None, "still fatal"),

    ("missing key", [{"file": "mod.py", "line": 2, "quote": "x"}],
     ["MALFORMED"], "REJECTED", None, "still fatal"),

    ("one repairable + one invented",
     [finding(line=4, quote="    data = handle.read()"),
      finding(line=2, quote="    handle.close()  # always closed")],
     ["MISALIGNED", "FABRICATED"], "REJECTED", 3,
     "a fabrication anywhere still voids the report, repairs elsewhere notwithstanding"),

    ("line number is not an integer",
     [finding(line="around 3", quote="    data = handle.read()")],
     ["MISALIGNED"], "ACCEPTED-WITH-REPAIRS", 3,
     "a junk line number with a real quote is still only a citation error"),
]


def main() -> int:
    repo = Path(tempfile.mkdtemp())
    (repo / "mod.py").write_text(SOURCE, encoding="utf-8")
    report = repo / "report.json"

    print("=== anchor layer: citation error vs fabrication ===\n")
    failures = 0
    for name, findings, want_verdicts, want_report, want_repair, why in CASES:
        report.write_text("```json\n" + json.dumps(findings) + "\n```", encoding="utf-8")
        out = repo / "repaired.json"
        code = sr.main(["--repo", str(repo), "--report", str(report), "--json",
                        "--label", name, "--repair", str(out)])
        # main() prints the JSON; re-derive the same values for assertions.
        parsed, _ = sr.extract_findings(report.read_text("utf-8"))
        got_verdicts, got_repair = [], None
        for item in parsed:
            verdict, _detail, repaired = sr.check_anchor(repo, item)
            got_verdicts.append(verdict)
            if repaired is not None and repaired != item.get("line"):
                got_repair = repaired

        fatal = any(v in ("FABRICATED", "BAD-PATH", "MALFORMED", "OUT-OF-SCOPE")
                    for v in got_verdicts)
        repairs = any(v.startswith("MISALIGNED") for v in got_verdicts)
        got_report = ("REJECTED" if fatal else
                      "ACCEPTED-WITH-REPAIRS" if repairs else "ACCEPTED")

        ok = (got_verdicts == want_verdicts and got_report == want_report
              and got_repair == want_repair and (code == 1) == fatal)
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        print(f"         verdicts {got_verdicts} -> {got_report}"
              + (f", repaired line {got_repair}" if got_repair else ""))
        if not ok:
            print(f"         EXPECTED {want_verdicts} -> {want_report}"
                  + (f", repair {want_repair}" if want_repair else ""))
        print(f"         {why}")

    print(f"\n{len(CASES) - failures}/{len(CASES)} cases behave as specified.")
    if failures:
        return 1
    print("An invented quote still voids the report (case 'invented quote' and "
          "'one repairable + one invented').\nThe loosening is confined to citation "
          "errors, which is what it was for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
