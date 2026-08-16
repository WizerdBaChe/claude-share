#!/usr/bin/env python3
"""score_redteam - mechanically check a red-team report's evidence anchors.

This is the peer's acceptance layers 2-4 written as code instead of carried as a
reading habit:

  layer 2 (structure)  -- the report must parse and every required key must be
                          present. A report that does not parse is not a weak
                          report, it is not a report.
  layer 3 (anchor)     -- every finding carries a verbatim line quote plus
                          file:line, or the literal SOURCE-NOT-FOUND. Checking a
                          quote costs one file read; producing a fake one that
                          survives the check costs the model the whole fabrication.
  layer 4 (spot check) -- a FABRICATED anchor downgrades the WHOLE REPORT rather
                          than just that finding, because a model that invented
                          one quote has told you what its other claims are worth.
                          A CITATION error -- a verbatim quote filed under the
                          wrong line number -- does not, and the difference was
                          learned the expensive way; see check_anchor().

Why this exists: on 2026-08-15 an external free-tier model returned a single
finding, beautifully formatted, claiming a missing `await` on a line that reads
`await page.addStyleTag(...)`. Nothing in the output betrayed it -- the reasoning
trace did, and a trace is not always there. The quote check catches that finding
without reading the trace and without reading the file first.

Usage:
  python score_redteam.py --repo <project-root> --report x.json [--json]

--report accepts either an extdispatch result JSON (the "answer" field is read)
or a raw text/markdown file containing the ```json block.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsonspan import first_parsable  # noqa: E402

REQUIRED_KEYS = {"file", "line", "quote", "defect", "failure", "severity"}
NOT_FOUND = "SOURCE-NOT-FOUND"


def extract_findings(raw: str) -> tuple[list[dict[str, Any]] | None, str]:
    """Return (findings, note). findings is None when the report does not parse."""
    # A UTF-8 BOM is not whitespace, so .strip() leaves it and every subsequent
    # test fails in a way that names the wrong culprit: the report was reported
    # as STRUCTURE-FAIL when the model's JSON was perfect and PowerShell's
    # `Out-File -Encoding utf8` had prepended EF BB BF. Measured 2026-08-16.
    # The general shape -- a mechanical gate rejecting good content over a
    # transport detail nobody specified -- is an open norm question; this share
    # carries it in README.md under 已知邊界與失效模式.
    text = raw.lstrip("﻿").strip()
    # extdispatch result JSON: the model's report lives in "answer".
    if text.startswith("{"):
        try:
            outer = json.loads(text)
            if isinstance(outer, dict) and "answer" in outer:
                text = str(outer["answer"]).strip()
        except json.JSONDecodeError:
            pass
    # Was `text.find("[")` .. `text.rfind("]")` when the fence was absent — the
    # greedy slice L-019 is about, still live in the structure layer after the
    # same bug had been fixed twice elsewhere. Found by the retrospective's
    # sibling scan 2026-08-16, not by any test: the test that covered this
    # algorithm imported a DUPLICATE of it.
    data = first_parsable(text, want=lambda value: isinstance(value, list))
    if data is None:
        return None, ("no parseable JSON array found in the report "
                      "(fenced block, then balanced spans, last-first)")
    return data, "parsed"


def commit_files(repo: Path, commit: str) -> set[str] | None:
    """Files a commit touched, repo-relative with forward slashes."""
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(repo), "show", "--pretty=format:", "--name-only", commit],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def file_sha(repo: Path, finding: dict[str, Any]) -> str | None:
    """Short content hash of the file this finding points at, or None."""
    import hashlib

    path = repo / str(finding.get("file", "")).replace("\\", "/")
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def check_anchor(repo: Path, finding: dict[str, Any]) -> tuple[str, str, int | None]:
    """Return (verdict, detail, repaired_line).

    Verdicts: OK / MISALIGNED / MISALIGNED-AMBIGUOUS / NOT-FOUND-DECLARED /
              FABRICATED / BAD-PATH / MALFORMED

    REVISED 2026-08-16 after this layer destroyed two true findings. The old
    version collapsed every anchor failure into one MISMATCH verdict, and layer 4
    rejected the whole report on any of them. Measured cost of that: an external
    reviewer returned two findings on a fresh repository, one of them a real
    directory-traversal hole; the other cited line 79 while quoting the text of
    line 80. Both claims were true. The report was REJECTED.

    The fix is to separate two questions this layer had fused:

        did the model READ the file?   <- what an anchor can actually prove
        is the claim TRUE?            <- layer 5's job, not this one's

    A verbatim line that occurs in the named file is proof of reading, and it is
    proof no matter which line number was written next to it: you cannot copy a
    line out of a file you never opened. An off-by-one is a CITATION error. A
    quote that appears nowhere in the file is a different animal entirely -- that
    is the fabrication this layer was built to catch, and it still rejects the
    report.

    Downgraded, not forgiven: a MISALIGNED finding is repaired to the line where
    its quote actually lives and passed on to layer 5, which tests the claim
    itself. Nothing is accepted here on trust; it is only spared execution by the
    wrong court.
    """
    missing = REQUIRED_KEYS - set(finding)
    if missing:
        return "MALFORMED", f"missing keys: {sorted(missing)}", None
    quote = str(finding["quote"])
    if quote.strip() == NOT_FOUND:
        return "NOT-FOUND-DECLARED", "model declared it could not anchor this claim", None
    path = repo / str(finding["file"]).replace("\\", "/")
    if not path.is_file():
        return "BAD-PATH", f"{finding['file']} does not exist in the repo", None

    lines = path.read_text("utf-8", "replace").splitlines()
    try:
        line_no: int | None = int(finding["line"])
    except (TypeError, ValueError):
        line_no = None

    if line_no is not None and 1 <= line_no <= len(lines):
        actual = lines[line_no - 1]
        if actual == quote:
            return "OK", "exact", line_no
        if actual.strip() == quote.strip():
            return "OK", "matches ignoring leading/trailing whitespace", line_no

    # The quote did not match where it was cited. Does it exist in the file at
    # all? That single question separates a citation slip from an invention.
    elsewhere = [i + 1 for i, text in enumerate(lines) if text.strip() == quote.strip()]
    cited = "not an integer" if line_no is None else (
        f"line {line_no}" + ("" if 1 <= line_no <= len(lines)
                             else f" (outside 1..{len(lines)})"))
    if len(elsewhere) == 1:
        return "MISALIGNED", (
            f"quote is verbatim from this file at line {elsewhere[0]}, cited as {cited}"
            " -- citation error, repaired; the model demonstrably read the file"
        ), elsewhere[0]
    if elsewhere:
        return "MISALIGNED-AMBIGUOUS", (
            f"quote occurs at lines {elsewhere}, cited as {cited} -- the model read the "
            "file, but which occurrence it meant cannot be recovered; layer 5 decides"
        ), None
    actual_text = (lines[line_no - 1].strip()[:90]
                   if line_no is not None and 1 <= line_no <= len(lines) else "")
    return "FABRICATED", (
        f"quote appears NOWHERE in {finding['file']}"
        + (f"; {cited} actually reads: {actual_text!r}" if actual_text else "")
    ), None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--label", default=None)
    parser.add_argument("--commit", default=None,
                        help="commit the review was scoped to; findings outside it are OUT-OF-SCOPE")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repair", type=Path, default=None,
                        help="write a line-corrected copy of the report for layer 5")
    args = parser.parse_args(argv)

    label = args.label or args.report.stem
    findings, note = extract_findings(args.report.read_text("utf-8", "replace"))
    if findings is None:
        print(f"{label}: STRUCTURE-FAIL ({note})")
        return 2

    # SCOPE, checked separately from the anchor and for a measured reason. On
    # 2026-08-16 an arm returned one finding whose quote matched its file and
    # line character for character -- and whose file is not in the reviewed
    # commit, is not in any commit, and is not tracked by git at all. A perfect
    # anchor on the wrong target is still a wrong report, so the anchor layer
    # alone does not close the gap: it verifies the QUOTE, not the SUBJECT.
    scope = commit_files(args.repo, args.commit) if args.commit else None
    if args.commit and scope is None:
        print(f"{label}: WARNING - could not resolve commit {args.commit}; scope not checked")

    # Scope applies to any finding whose quote is real, not only to the exact
    # ones: an out-of-scope finding is out of scope whether or not its line
    # number was right.
    read_the_file = ("OK", "MISALIGNED", "MISALIGNED-AMBIGUOUS")
    rows = []
    repaired_findings = []
    for index, finding in enumerate(findings, 1):
        verdict, detail, repaired = check_anchor(args.repo, finding)
        if verdict in read_the_file and scope is not None:
            named = str(finding.get("file", "")).replace("\\", "/")
            if named not in scope:
                verdict, detail, repaired = "OUT-OF-SCOPE", (
                    f"{named} is not among the {len(scope)} files touched by {args.commit}"
                ), None
        # An anchor is a claim about a file AT A MOMENT. Scoring the same report
        # twice can legitimately give different line numbers, because the file
        # moved between the two runs -- which happened here on 2026-08-16: a
        # concurrent session fixed the very defect under review and every anchor
        # shifted 50-odd lines. Without this fingerprint the second scoring looks
        # like a scorer bug rather than a different file.
        rows.append({"n": index, "verdict": verdict, "detail": detail,
                     "file": finding.get("file"), "line": finding.get("line"),
                     "repaired_line": repaired, "file_sha": file_sha(args.repo, finding),
                     "defect": str(finding.get("defect", ""))[:160]})
        if verdict in read_the_file:
            fixed = dict(finding)
            if repaired is not None and repaired != finding.get("line"):
                fixed["line"] = repaired
                fixed["_line_repaired_from"] = finding.get("line")
            repaired_findings.append(fixed)

    # FATAL means the report cannot be trusted as a whole: an invented quote, a
    # file that is not there, a malformed object, a finding outside the review's
    # scope. A citation error is not in this list -- see check_anchor().
    fatal = [r for r in rows if r["verdict"] in
             ("FABRICATED", "BAD-PATH", "MALFORMED", "OUT-OF-SCOPE")]
    repairs = [r for r in rows if r["verdict"].startswith("MISALIGNED")]
    anchored = [r for r in rows if r["verdict"] == "OK"]
    declared = [r for r in rows if r["verdict"] == "NOT-FOUND-DECLARED"]
    if fatal:
        report_verdict = "REJECTED"
    elif not findings:
        report_verdict = "EMPTY-ACCEPTED"
    elif repairs:
        report_verdict = "ACCEPTED-WITH-REPAIRS"
    else:
        report_verdict = "ACCEPTED"

    if args.repair:
        args.repair.write_text(
            "```json\n" + json.dumps(repaired_findings, ensure_ascii=False, indent=2)
            + "\n```", encoding="utf-8")

    if args.json:
        print(json.dumps({"label": label, "verdict": report_verdict, "n": len(rows),
                          "anchored": len(anchored), "declared_not_found": len(declared),
                          "repairs": len(repairs), "fatal": len(fatal), "rows": rows},
                         ensure_ascii=False, indent=2))
        return 1 if fatal else 0

    print(f"=== {label} ===")
    print(f"findings: {len(rows)}   exact: {len(anchored)}   repaired: {len(repairs)}   "
          f"declared-not-found: {len(declared)}   FATAL: {len(fatal)}")
    for row in rows:
        line = row["line"]
        if row["repaired_line"] is not None and row["repaired_line"] != line:
            line = f"{line}->{row['repaired_line']}"
        print(f"  [{row['verdict']:<22}] {row['file']}:{line}  {row['defect']}")
        if row["verdict"] != "OK":
            print(f"       -> {row['detail']}")
    print(f"REPORT VERDICT: {report_verdict}")
    if fatal:
        print("  layer 4: an invented quote, a missing file or an out-of-scope finding "
              "voids the whole report.")
    elif repairs:
        print("  Citation errors were repaired, not punished. The quotes are verbatim "
              "from the named files,\n  which is what an anchor can prove; whether the "
              "claims are TRUE is layer 5's question.")
        if args.repair:
            print(f"  repaired report written to {args.repair} -- feed THIS to "
                  "redteam_verify.py")
        else:
            print("  re-run with --repair <file> to emit a line-corrected report for "
                  "layer 5.")
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
