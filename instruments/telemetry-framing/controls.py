#!/usr/bin/env python3
"""Two-sided calibration for framing.py — run: python tools/telemetry-framing/controls.py

A counter that reports zero is indistinguishable from a counter that is not
looking, so the known-BAD side carries one specimen per way a row can fail to
parse, including the two shapes MEASURED in the live files (a tail fragment of an
overwritten record). The known-GOOD side is the larger risk here: a scanner that
called ordinary rows damaged would make the baseline meaningless, so CJK, escaped
backslashes, deep nesting and a trailing newline all have to come back clean.

EXTENDING (PH-11 / AP-61): a new damage shape gets a specimen in BAD_ROWS; a row
shape the corpus legitimately writes gets one in GOOD_ROWS. Coverage over
BASELINE is asserted at the bottom, and so is the closure of the class set
(AP-62): an entry the `*.jsonl` glob admits but no framing class fits must come
back on the third verdict — excluded from both totals, and still named (C-09..C-11).
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import framing  # noqa: E402

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if got == want else 'FAIL'} {name}")


# known-BAD: every one of these must be counted
BAD_ROWS = [
    ('b.meta.json"]}', "tail fragment of an overwritten record (live L58)"),
    (']}', "two-byte tail fragment (live L73)"),
    ('{"ts": 1, "session": "a"', "truncated mid-record, no closing brace"),
    ('{"ts": 1,, "x": 2}', "doubled comma"),
    ('not json at all', "plain text"),
    ('{"a": 1}{"b": 2}', "two records with no newline between them"),
]

# known-GOOD: none of these may be counted, or the baseline means nothing
GOOD_ROWS = [
    '{"ts": 1788800000, "hook": "x", "nonce": "ab12cd"}',
    '{"cwd": "D:\\\\work\\\\proj", "files": ["C:\\\\Users\\\\g\\\\a.md"]}',
    '{"note": "中文與 emoji 🚀 都要原樣通過"}',
    '{"deep": {"a": [1, 2, {"b": null, "c": true}]}}',
    '{"empty_list": [], "empty_obj": {}, "zero": 0, "neg": -1.5e3}',
    '{"quote": "he said \\"ok\\" and left"}',
]

tmp = Path(tempfile.mkdtemp(prefix="framing-controls-"))
try:
    (tmp / "good.jsonl").write_text(
        "\n".join(GOOD_ROWS) + "\n\n", encoding="utf-8")   # trailing blank line too
    (tmp / "mixed.jsonl").write_text(
        "\n".join(GOOD_ROWS + [r for r, _w in BAD_ROWS]) + "\n", encoding="utf-8")
    (tmp / "empty.jsonl").write_text("", encoding="utf-8")

    rows = {name: (r, b) for name, r, b, _s in framing.scan(tmp)}

    check("every file is visited", sorted(rows), ["empty.jsonl", "good.jsonl", "mixed.jsonl"])

    # known-TRUE: ordinary rows are not damage, and a blank line is not a row
    check("C-01 clean file counts zero damage", rows["good.jsonl"][1], 0)
    check("C-02 blank lines are not counted as rows",
          rows["good.jsonl"][0], len(GOOD_ROWS))
    check("C-03 an empty file is 0 rows, not an error", rows["empty.jsonl"], (0, 0))

    # known-BAD: every declared damage shape is counted
    check("C-04 every damaged row is counted", rows["mixed.jsonl"][1], len(BAD_ROWS))
    check("C-05 good rows in the same file still parse",
          rows["mixed.jsonl"][0] - rows["mixed.jsonl"][1], len(GOOD_ROWS))

    # per-specimen, so a failure names WHICH shape stopped being caught
    for row, why in BAD_ROWS:
        one = tmp / "one.jsonl"
        one.write_text(row + "\n", encoding="utf-8")
        got = {n: b for n, _r, b, _s in framing.scan(tmp)}["one.jsonl"]
        check(f"C-06 counted: {why}", got, 1)
    for row in GOOD_ROWS:
        one = tmp / "one.jsonl"
        one.write_text(row + "\n", encoding="utf-8")
        got = {n: b for n, _r, b, _s in framing.scan(tmp)}["one.jsonl"]
        check(f"C-07 NOT counted: {row[:44]}", got, 0)

    # the baseline is a value about the LIVE tree, so it must not be a guess
    check("C-08 baseline is a non-negative int", isinstance(framing.BASELINE, int)
          and framing.BASELINE >= 0, True)

    # --- AP-62: an entry the glob accepts but no framing class fits ------------
    # The vocabulary IS the glob (`*.jsonl`), so it admits things that are not
    # JSONL files at all. A directory with that name is the cheap, deterministic
    # specimen for the whole unreadable family (a locked or ACL-denied file
    # arrives on the same `except OSError` branch). It must come back as the
    # third-verdict sentinel (-1, -1) and NOT as (0, 0): a zero-row zero-damage
    # verdict is what a genuinely empty file earns, and folding "could not look"
    # into "looked, found nothing" is how a damage count stays plausible while
    # measuring less of the corpus than it claims.
    (tmp / "sealed.jsonl").mkdir()
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rows = {name: (r, b) for name, r, b, _s in framing.scan(tmp)}
    check("C-09 unreadable entry → undetermined sentinel + notice, not a clean empty file",
          (rows["sealed.jsonl"], rows["sealed.jsonl"] == rows["empty.jsonl"],
           "[UNREADABLE] sealed.jsonl" in err.getvalue()),
          ((-1, -1), False, True))

    # ...and the verdict layer must exclude it from both totals while still
    # naming it, so the published number reads as a floor rather than a total.
    framing.HOME = tmp                       # scan() defaults to HOME/"telemetry"
    (tmp / "telemetry").mkdir()
    (tmp / "telemetry" / "ok.jsonl").write_text(
        "\n".join(GOOD_ROWS) + "\n", encoding="utf-8")
    (tmp / "telemetry" / "sealed.jsonl").mkdir()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        framing.main()
    out = buf.getvalue()
    check("C-10 undetermined file excluded from the row and damage totals",
          f"2 file(s), {len(GOOD_ROWS)} row(s), 0 unparseable" in out, True)
    check("C-11 undetermined file still NAMED, count declared a floor",
          "UNDETERMINED: 1 file(s) could not be read: sealed.jsonl" in out
          and "floor, not a total" in out, True)

    # Suite-session allowlist (O-2, 2026-09-11), both sides. The skip is keyed
    # (session, FILE) for real ids and session-only for literals; a session-wide
    # skip on a real id is exactly the over-reach measured on 2026-09-11 (every
    # listed id also wrote genuine rows to a dozen other files), so C-13's
    # second half is the case that pins it.
    sdir = tmp / "suite"
    (sdir / "telemetry").mkdir(parents=True)
    suite_json = sdir / "suite-sessions.json"
    suite_json.write_text(json.dumps({
        "literals": ["synthtest-x"],
        "session_files": {"real-1111": ["secret-file-guard.jsonl"]},
    }), encoding="utf-8")
    real_in_listed = '{"ts": 1, "session_id": "real-1111", "kind": "deny"}'
    real_elsewhere = '{"ts": 1, "session": "real-1111", "kind": "deny"}'
    literal_row = '{"ts": 1, "session_id": "synthtest-x", "kind": "deny"}'
    stranger = '{"ts": 1, "session_id": "other-2222", "kind": "deny"}'
    (sdir / "telemetry" / "secret-file-guard.jsonl").write_text(
        "\n".join([real_in_listed, literal_row, stranger]) + "\n", encoding="utf-8")
    (sdir / "telemetry" / "rule-loads.jsonl").write_text(
        "\n".join([real_elsewhere, literal_row, stranger]) + "\n", encoding="utf-8")
    got = {n_: (r, b, s) for n_, r, b, s in framing.scan(sdir / "telemetry", suite_path=suite_json)}
    check("C-12 literal id skipped in EVERY file, stranger counted everywhere",
          (got["secret-file-guard.jsonl"][2] >= 1, got["rule-loads.jsonl"][2] >= 1,
           got["secret-file-guard.jsonl"][0] >= 1, got["rule-loads.jsonl"][0] >= 1),
          (True, True, True, True))
    check("C-13 real id skipped ONLY in its listed file (1 row + literal there; counted in rule-loads)",
          (got["secret-file-guard.jsonl"], got["rule-loads.jsonl"]),
          ((1, 0, 2), (2, 0, 1)))
    got_none = {n_: (r, b, s) for n_, r, b, s in framing.scan(sdir / "telemetry", suite_path=sdir / "missing.json")}
    check("C-14 missing allowlist skips NOTHING (fails toward counting more, never fewer)",
          (got_none["secret-file-guard.jsonl"], got_none["rule-loads.jsonl"]),
          ((3, 0, 0), (3, 0, 0)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

n = 5 + len(BAD_ROWS) + len(GOOD_ROWS) + 2 + 3 + 3
print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print(f"ALL PASS {n}/{n} ({len(BAD_ROWS)} damage shapes incl. both live ones, "
      f"{len(GOOD_ROWS)} known-good rows, blank/empty/baseline, "
      f"3 unclassifiable/undetermined)")
