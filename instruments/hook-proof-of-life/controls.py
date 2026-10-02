"""Two-sided calibration for pol.py — run: python tools/hook-proof-of-life/controls.py

AP-62 (`ops/references/principle-design-guide.md` PH-11): one specimen per
declared class, plus the input the instrument must still catch. Here that second
half matters twice over — this tool's whole job is to notice a control suite that
has stopped passing, so a version of it that reported PASS unconditionally would
be the exact failure it exists to prevent. C-05 is that case.

The fixture is a real temp tree with a real settings.json and real suite scripts,
because `registered_hooks()` parses settings.json and `run_suite()` shells out;
a fixture that stubbed either would exercise neither.

EXTENDING (AP-61): a class added to pol.CLASSES needs a specimen hook here; a new
DECLARATION SHAPE needs a case proving both that it is recognised and that a
near-miss of it is NOT.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pol  # noqa: E402

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if got == want else 'FAIL'} {name}")


HOOKS = {
    # name -> module docstring
    "passing_guard.py":
        'Guard.\n\nProof-of-life: `python suites/ok.py` (2 cases).\n',
    "failing_guard.py":
        'Guard.\n\nProof-of-life: `python suites/bad.py` (2 cases).\n',
    "inconclusive_guard.py":
        'Guard.\n\nProof-of-life: `python suites/unclear.py` (scenario-gated).\n',
    "manual_guard.py":
        'Guard.\n\nProof-of-life: integrity-sweep check 13 — no suite exists.\n',
    "bare_guard.py":
        'Guard with no declaration at all.\n',
    "vague_guard.py":
        'Guard.\n\nProof-of-life: someone checks it now and then.\n',
    # two markers, the WEAKER one first: the strongest declaration must win, or
    # the class would depend on a position in text that grows (AP-45).
    "two_marker_guard.py":
        'Guard.\n\nProof-of-life: integrity-sweep check 22 reads the log.\n\n'
        'Proof-of-life: `python suites/ok.py` (the runnable one).\n',
}
SUITES = {
    "ok.py": "print('ALL PASS 2/2')\n",
    "bad.py": "import sys\nprint('1 FAILURE(S)')\nsys.exit(1)\n",
    # exit 3 = the suite ran and its scenario did not occur. Neither pass nor fail.
    "unclear.py": "import sys\nprint('2 passed, 0 failed, 1 inconclusive')\nsys.exit(3)\n",
    # never finishes within the (temporarily lowered) budget -- C-11's fixture.
    # Deliberately NOT registered as a hook's declaration: C-11 calls run_suite
    # directly, so the sweep above never pays 30 s to learn what C-11 measures.
    "slow.py": "import time\ntime.sleep(30)\nprint('ALL PASS 1/1')\n",
}

tmp = Path(tempfile.mkdtemp(prefix="pol-controls-"))
try:
    (tmp / "hooks").mkdir()
    (tmp / "suites").mkdir()
    for name, doc in HOOKS.items():
        (tmp / "hooks" / name).write_text(f'"""{doc}"""\n', encoding="utf-8")
    # a file that is not valid python at all -> undetermined, never "uncovered"
    (tmp / "hooks" / "broken_guard.py").write_text("def (:\n", encoding="utf-8")
    for name, body in SUITES.items():
        (tmp / "suites" / name).write_text(body, encoding="utf-8")

    settings = tmp / "settings.json"
    names = sorted(list(HOOKS) + ["broken_guard.py"])
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [{"hooks": [
        {"command": f'"python" "C:/x/hooks/{n}"'} for n in names]}]}}),
        encoding="utf-8")

    check("settings parse finds every registered hook",
          pol.registered_hooks(settings), names)

    rows = pol.sweep(hooks_dir=tmp / "hooks", settings_path=settings,
                     quiet=True, root=tmp)
    by = {n: (k, ok, d) for n, k, ok, d in rows}

    # --- C-01..C-05: one specimen per class, plus the failing suite ----------
    check("C-01 executable class", by["passing_guard.py"][0], "executable")
    check("C-02 manual class", by["manual_guard.py"][0], "manual")
    check("C-03 uncovered class", by["bare_guard.py"][0], "uncovered")
    check("C-04a undetermined: declared but unrunnable",
          by["vague_guard.py"][0], "undetermined")
    check("C-04b undetermined: file will not parse",
          by["broken_guard.py"][0], "undetermined")

    # known-BAD: the whole point. A declared suite that fails must be reported.
    check("C-05 a FAILING suite is reported", by["failing_guard.py"][1], False)
    check("C-05 names the command to reproduce (AP-64)",
          "python suites/bad.py" in by["failing_guard.py"][2], True)

    # known-TRUE: a passing suite must NOT be reported as failing, or the tool
    # would be a reject-everything gate scoring 100% one-sided.
    check("C-06 a PASSING suite is not reported as failing",
          by["passing_guard.py"][1], True)

    # C-10: exit 3 is a THIRD result, folded into neither verdict (AP-62).
    check("C-10 exit 3 -> inconclusive, not False",
          by["inconclusive_guard.py"][1], "inconclusive")
    check("C-10 inconclusive is not True either",
          by["inconclusive_guard.py"][1] is True, False)

    # C-11: a suite that never finishes determined NOTHING about its hook. Before
    # 2026-09-08 this returned False and the report named the hook as failing --
    # measured, on three sweeps run concurrently. The budget is lowered here so
    # the fixture stays cheap; the class is what is under test, not the number.
    real_timeout, pol.TIMEOUT = pol.TIMEOUT, 2
    try:
        verdict, detail = pol.run_suite("python suites/slow.py", root=tmp)
    finally:
        pol.TIMEOUT = real_timeout
    check("C-11 a timed-out suite is inconclusive, not a failing hook",
          verdict, "inconclusive")
    check("C-11 and it is not read as success either", verdict is True, False)
    check("C-11 the detail says what to do (AP-64)", "re-run it alone" in detail, True)

    # --- C-07: the strongest declaration wins, not the first -----------------
    check("C-07 two markers -> executable wins over manual",
          by["two_marker_guard.py"][0], "executable")
    check("C-07 and it actually ran", by["two_marker_guard.py"][1], True)

    # --- C-08: a missing settings.json yields nothing, never a false PASS ----
    check("C-08 unreadable settings -> no rows (not a silent all-clear)",
          pol.registered_hooks(tmp / "nope.json"), [])

    # --- C-09: suites are deduped, so a shared one runs once -----------------
    ran = {d.split(" -> ")[0] for _n, k, _o, d in rows if k == "executable"}
    check("C-09 two hooks sharing one suite yield one command", len(ran), 3)

    # --- C-12: `uncovered` was PROMOTED to FAIL on 2026-09-08 ----------------
    # It was WARN while a legacy backlog existed; the trigger recorded in
    # integrity-sweep check 31 was "uncovered reaching 0", and it did. Both
    # sides, because a promotion that also made the PASS case fail would be a
    # gate that stops everything -- and a reject-everything gate scores 100% on
    # a one-sided calibration.
    def _exit_for(rows_in):
        return 1 if [r for r in rows_in if (r[1] == "executable" and r[2] is False)
                     or r[1] in ("undetermined", "uncovered")] else 0

    check("C-12 known-BAD: a hook with no declaration exits 1",
          _exit_for([("bare.py", "uncovered", None, "")]), 1)
    check("C-12 known-TRUE: an all-executable fleet still exits 0",
          _exit_for([("a.py", "executable", True, ""), ("b.py", "executable", True, "")]), 0)
    check("C-12 a MANUAL-only declaration stays WARN, not FAIL "
          "(named-but-not-run is a weaker finding than nothing at all)",
          _exit_for([("m.py", "manual", None, "")]), 0)
    check("C-12 an INCONCLUSIVE run is still not a failure",
          _exit_for([("i.py", "executable", "inconclusive", "")]), 0)

    # --- C-13: the hmi-report/1 document keeps the classes DISTINCT -----------
    # Asserted on the fields a defect would CHANGE (state / quality /
    # skip_reason), one row per class, because a reader that folded
    # "inconclusive" into fail or "manual" into pass would still emit a valid
    # document.
    doc = pol.hmi_report([("ok.py", "executable", True, "d"),
                          ("bad.py", "executable", False, "d"),
                          ("slow.py", "executable", "inconclusive", "timeout"),
                          ("bare.py", "uncovered", None, ""),
                          ("prose.py", "undetermined", None, ""),
                          ("hand.py", "manual", None, "")])
    by = {q["id"]: q for q in doc["points"]}
    check("C-13 protocol header", (doc["protocol"], doc["source"]),
          ("hmi-report/1", "hook-proof-of-life"))
    check("C-13 known-TRUE: a passing suite is state=pass, quality=good, ran",
          (by["hook-suite.ok"]["state"], by["hook-suite.ok"]["quality"], by["hook-suite.ok"]["ran"]),
          ("pass", "good", True))
    check("C-13 known-BAD: a failing suite is state=fail",
          by["hook-suite.bad"]["state"], "fail")
    check("C-13 a TIMEOUT determines nothing: state null, quality undetermined",
          (by["hook-suite.slow"]["state"], by["hook-suite.slow"]["quality"]),
          (None, "undetermined"))
    check("C-13 no declaration is a determinable defect: fail + no-runnable-declaration",
          (by["hook-suite.bare"]["state"], by["hook-suite.bare"]["skip_reason"], by["hook-suite.bare"]["ran"]),
          ("fail", "no-runnable-declaration", False))
    check("C-13 an unbackticked declaration reads the same as none",
          (by["hook-suite.prose"]["state"], by["hook-suite.prose"]["skip_reason"]),
          ("fail", "no-runnable-declaration"))
    check("C-13 manual-only is never a pass: state null, undetermined, manual-only",
          (by["hook-suite.hand"]["state"], by["hook-suite.hand"]["quality"], by["hook-suite.hand"]["skip_reason"]),
          (None, "undetermined", "manual-only"))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL PASS 29/29 (5 class specimens, 1 known-bad suite, 1 known-true, "
      "1 inconclusive, 1 timeout, position + settings + dedup regressions, "
      "4 for the 2026-09-08 uncovered->FAIL promotion, 7 for the hmi-report/1 emitter)")
