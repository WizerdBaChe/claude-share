#!/usr/bin/env python3
"""Two-sided calibration for closure.py — run: python tools/class-closure/controls.py

Builds a throwaway repo root and asserts every class the tool can emit, from
every enumeration route, plus the verdict ladder. Known-BAD side: a suite that
lacks the case is called `lacks`, and every one of them is FAIL — since the
2026-09-09 promotion there is no softer level, which the two no-downgrade cases
pin. Known-GOOD side: a suite carrying the word is `carries` (through all three
routes), a suite that only says `inconclusive` is NOT `carries` (the proxy
boundary the docstring states), and an unreadable or missing suite is
`undetermined` — reported, excluded from the counts, never folded into `lacks`.

The last case is this instrument's own AP-62 specimen: an input matching no
declared class asserting `undetermined`.

The second half (2026-09-23) calibrates `exercise.py` by really running fixture
suites under the line probe: known-TRUE rows must read `exercised` through each
route (import, a python child, a hook's own --selftest) and each branch shape
(a named guarded statement, a marker-test body, a `not isinstance` shape guard);
known-FALSE rows must read `named-only` (a case in an uncalled function; a
--selftest hook whose word sits only in production code, which closure.py
itself reads as `carries`). The asserted case/branch VALUES of both sides are
printed as `value` lines so the calibration record carries them.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import closure  # noqa: E402

FAILS: list[str] = []
RAN: list[str] = []


def check(name: str, got, want) -> None:
    RAN.append(name)
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if got == want else 'FAIL'} {name}")


HOOK_TEMPLATE = '''"""{name} — a fixture hook.

Proof-of-life: `python {suite}` -- fixture.
"""
'''


def build_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="class-closure-"))
    (root / "tools" / "carrying").mkdir(parents=True)
    (root / "tools" / "lacking").mkdir(parents=True)
    (root / "tools" / "binary").mkdir(parents=True)
    (root / "tools" / "inconclusive-only").mkdir(parents=True)
    (root / "hooks" / "tests").mkdir(parents=True)
    (root / "tools/carrying/controls.py").write_text(
        'check("garbage input", classify("x"), "undetermined")\n', encoding="utf-8")
    (root / "tools/lacking/controls.py").write_text(
        'check("good", classify("a"), "good")\ncheck("bad", classify("b"), "bad")\n',
        encoding="utf-8")
    (root / "tools/binary/controls.py").write_bytes(b"\xff\xfe\x00 not text \x80\x81")
    (root / "tools/inconclusive-only/controls.py").write_text(
        'check("timeout", run("slow"), "inconclusive")\n', encoding="utf-8")
    # hooks/tests route: one carrying (via the UNDET spelling), one lacking
    (root / "hooks/tests/test_alpha.py").write_text(
        'assert lint(weird) == "UNDET"\n', encoding="utf-8")
    (root / "hooks/tests/test_beta.py").write_text(
        'assert lint(ok) == "PASS"\n', encoding="utf-8")
    # declared route: hook gamma declares a suite that exists only through the
    # declaration; hook delta declares a suite that does not exist
    (root / "hooks/gamma.py").write_text(
        HOOK_TEMPLATE.format(name="gamma", suite="tools/gamma-suite/selftest.py"),
        encoding="utf-8")
    (root / "tools/gamma-suite").mkdir()
    (root / "tools/gamma-suite/selftest.py").write_text(
        'want("unclassifiable", "undetermined")\n', encoding="utf-8")
    (root / "hooks/delta.py").write_text(
        HOOK_TEMPLATE.format(name="delta", suite="hooks/tests/test_missing.py"),
        encoding="utf-8")
    # hook epsilon declares nothing: check 31's finding, must not appear here
    (root / "hooks/epsilon.py").write_text('"""epsilon — no declaration."""\n',
                                          encoding="utf-8")
    hooks = {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": f"python {root.as_posix()}/hooks/{n}.py"}
        for n in ("gamma", "delta", "epsilon")]}]}
    (root / "settings.json").write_text(json.dumps({"hooks": hooks}), encoding="utf-8")
    return root


root = build_root()
try:
    rows = closure.scan(root)
    by = {r["suite"]: r for r in rows}

    # enumeration: every route reaches its suite, once, and the undeclared hook adds nothing
    check("enumerates 8 suites, each once", sorted(by), sorted([
        "tools/carrying/controls.py", "tools/lacking/controls.py",
        "tools/binary/controls.py", "tools/inconclusive-only/controls.py",
        "hooks/tests/test_alpha.py", "hooks/tests/test_beta.py",
        "tools/gamma-suite/selftest.py", "hooks/tests/test_missing.py"]))
    check("declared-only suite reached via the hook's declaration",
          by["tools/gamma-suite/selftest.py"]["via"], "declared by hooks/gamma.py")

    # known-GOOD: carrying, through each route and each spelling
    check("controls.py asserting undetermined -> carries", by["tools/carrying/controls.py"]["class"], "carries")
    check("hooks/tests asserting UNDET -> carries", by["hooks/tests/test_alpha.py"]["class"], "carries")
    check("declared suite asserting unclassifiable -> carries", by["tools/gamma-suite/selftest.py"]["class"], "carries")
    check("carrying detail names the line", by["tools/carrying/controls.py"]["detail"].startswith("L1:"), True)

    # known-BAD: lacking
    check("controls.py with only good/bad -> lacks", by["tools/lacking/controls.py"]["class"], "lacks")
    check("hooks/tests with only PASS -> lacks", by["hooks/tests/test_beta.py"]["class"], "lacks")
    check("inconclusive alone is NOT the class (proxy boundary)",
          by["tools/inconclusive-only/controls.py"]["class"], "lacks")

    # the instrument's own AP-62 specimen: unreadable / missing -> undetermined, not lacks
    check("non-UTF-8 suite -> undetermined", by["tools/binary/controls.py"]["class"], "undetermined")
    check("declared-but-missing suite -> undetermined", by["hooks/tests/test_missing.py"]["class"], "undetermined")
    check("undetermined detail says why", "does not exist" in by["hooks/tests/test_missing.py"]["detail"], True)

    # verdict ladder — FAIL / PASS. WARN was deleted at the 2026-09-09 promotion.
    level, line = closure.verdict(rows)
    check("a lacking suite -> FAIL", level, "FAIL")
    check("FAIL line names the lacking suites",
          "tools/lacking/controls.py" in line and "test_beta" in line, True)
    check("undetermined excluded from the FAIL count", "3 suite(s)" in line, True)

    # REGRESSION for the promotion. The deleted WARN branch softened exactly this
    # input: a corpus where every lacking suite was named in advance. If a
    # legacy-style exemption ever returns, these two are what catch it.
    only_lacking = [r for r in rows if r["class"] == "lacks"]
    check("a corpus where EVERY suite lacks the case is still FAIL, never softened",
          closure.verdict(only_lacking)[0], "FAIL")
    check("no input produces a third level",
          sorted({closure.verdict(x)[0] for x in
                  ([], only_lacking, rows, [r for r in rows if r["class"] != "lacks"])}),
          ["FAIL", "PASS"])

    only_good = [r for r in rows if r["class"] != "lacks"]
    level4, line4 = closure.verdict(only_good)
    check("no lacking suite -> PASS even with undetermined present", level4, "PASS")
    check("PASS line still reports the undetermined ones", "2 undetermined" in line4, True)

    # CODE-TOKEN proxy (2026-09-23): a comment or docstring naming the class is not a case.
    # Known-BAD side is the shape measured live that day (dispatch_commit_notice: real
    # cases, word only in a comment); known-GOOD side keeps every code-token spelling.
    tok = Path(tempfile.mkdtemp(prefix="class-closure-tok-"))
    try:
        specimens = {
            "comment_only.py": ('# case: an undetermined input\ncheck("bad", f(x), "bad")\n', "lacks"),
            "trailing_comment.py": ('check("bad", f(x), "bad")  # unclassifiable\n', "lacks"),
            "docstring_only.py": ('"""Suite. Covers undetermined input."""\n'
                                  'def t():\n    """and an UNDET case"""\n    assert f(1) == 1\n', "lacks"),
            "string_in_check.py": ('check("unclassifiable payload", f([]), "error")\n', "carries"),
            "fstring.py": ('cid = "U"\ncheck(f"{cid} undetermined payload", f([]), "error")\n', "carries"),
            "not_python.py": ('check("undetermined" (\n', "undetermined"),
            "not_python.ps1": ('# undetermined\n', "carries"),   # non-.py keeps the line proxy
        }
        for name, (body, want) in specimens.items():
            (tok / name).write_text(body, encoding="utf-8")
            check(f"code-token proxy: {name} -> {want}", closure.classify(tok / name)[0], want)
        check("unparseable .py says why (undetermined, never lacks)",
              "not parseable" in closure.classify(tok / "not_python.py")[1], True)
    finally:
        shutil.rmtree(tok, ignore_errors=True)

    # the live tree: the tool must run on itself
    live = closure.scan()
    live_names = {r["suite"] for r in live}
    check("this tool's own suite is enumerated in the live tree",
          "tools/class-closure/controls.py" in live_names, True)
finally:
    shutil.rmtree(root, ignore_errors=True)


# ============================================================================ exercise.py
# Two-sided calibration of the RUN-TIME evidence (2026-09-23). Every fixture suite is
# really executed under the probe. Known-TRUE side: a case that runs AND reaches a
# guarded instrument branch -> `exercised`, through all three routes (in-process import,
# a python CHILD process, a hook's own --selftest) and both branch shapes (a guarded
# marker statement, the body of a marker-test `if`). Known-FALSE side: the word present
# but never run (a case inside an uncalled function; a --selftest hook whose word sits
# only in production code) -> `named-only`, and the WARN it drives. Neither-side rows
# pin the rest of the ladder: case-only, unnamed-exercise, absent, undetermined.
import exercise  # noqa: E402

INST = '''UNDET = "undetermined"


def classify(x):
    if not isinstance(x, str):
        return UNDET
    return "good" if x == "a" else "bad"


def classify_quiet(x):
    if not isinstance(x, str):
        return None
    return "good"


def label(k):
    if k == UNDET:
        return None
    return k
'''
QUIET = '''def classify_quiet(x):
    try:
        return "good" if x.lower() else "bad"
    except AttributeError:
        return None
'''
# the wordless unclassifiable branch hooks use: a `not isinstance` guard, no marker anywhere
SHAPED = '''def decide(payload):
    if not isinstance(payload, dict):
        return None
    return "allow"
'''
IMPORT = 'import sys\nsys.path.insert(0, "tools/inst")\nimport inst\n'
EX_SUITES = {
    # known-TRUE: the case runs and the instrument's guarded branch runs
    "tools/ex-true/controls.py": IMPORT + 'assert inst.classify(5) == "undetermined"\nassert inst.classify("a") == "good"\n',
    # known-TRUE via a marker-TEST body: `return None` under `if k == UNDET`
    "tools/ex-testbody/controls.py": IMPORT + 'assert inst.label(inst.UNDET) is None\n',
    # known-FALSE: the case exists only inside a function nobody calls
    "tools/ex-named/controls.py": IMPORT + 'def never():\n    assert inst.classify(5) == "undetermined"\n\n\nassert inst.classify("a") == "good"\n',
    # SHAPE route, known-TRUE: the named case drives a wordless `not isinstance` branch
    "tools/ex-shape/controls.py": ('import sys\nsys.path.insert(0, "tools/inst")\nimport shaped\n'
                                   'assert shaped.decide([]) is None, "unclassifiable payload"\n'),
    # SHAPE route, the historical false negative (dispatch_commit_notice before c0b30ee):
    # a real case, no word, wordless instrument -> unnamed-exercise, no longer `absent`
    "tools/ex-shape-unnamed/controls.py": ('import sys\nsys.path.insert(0, "tools/inst")\nimport shaped\n'
                                           'assert shaped.decide([]) is None\n'),
    # SHAPE route, known-FALSE: the suite never sends a non-dict, so the guard body never runs
    "tools/ex-shape-valid/controls.py": ('import sys\nsys.path.insert(0, "tools/inst")\nimport shaped\n'
                                         'assert shaped.decide({}) == "allow", "undetermined not taken"\n'),
    # case runs, and the only instrument it touches has no named branch -> case-only
    "tools/ex-caseonly/controls.py": ('import sys\nsys.path.insert(0, "tools/inst")\nimport quiet\n'
                                      'assert quiet.classify_quiet(5) is None, "unclassifiable input"\n'),
    # the marker-test HEADER runs but its body does not, and inst.py's named branches
    # (lines 6, 18) never run although inst.py did -> branch-unreached
    "tools/ex-header/controls.py": IMPORT + 'assert inst.label("x") == "x", "undetermined not taken"\n',
    # exercised without the word -> unnamed-exercise
    "tools/ex-unnamed/controls.py": IMPORT + 'assert inst.classify(5) != "good"\n',
    # neither named nor exercised -> absent
    "tools/ex-absent/controls.py": IMPORT + 'assert inst.classify("a") == "good"\n',
    # a failing suite observed nothing -> undetermined, never named-only
    "tools/ex-failing/controls.py": IMPORT + 'assert inst.classify(5) == "undetermined"\nraise SystemExit(1)\n',
    # CHILD route: the branch runs in a python subprocess the suite spawns
    "hooks/tests/test_hk.py": ('import subprocess, sys\n'
                               'p = subprocess.run([sys.executable, "hooks/hk.py"], input="[]", '
                               'capture_output=True, text=True)\n'
                               'assert p.stdout.strip() == "undetermined", p.stdout\n'),
    "hooks/hk.py": ('"""hk -- fixture hook, no declaration."""\nimport json\nimport sys\n\n\n'
                    'def main():\n    data = json.loads(sys.stdin.read())\n'
                    '    if not isinstance(data, dict):\n        print("undetermined")\n        return 0\n'
                    '    print("ok")\n    return 0\n\n\nsys.exit(main())\n'),
}
SELFTEST_HOOK = '''"""{name} -- fixture hook.

Proof-of-life: `python hooks/{name}.py --selftest` -- fixture.
"""
import sys


def decide(x):
    if not isinstance(x, dict):
        return "undetermined"
    return "allow"


def selftest():
{body}    return 0


if "--selftest" in sys.argv:
    sys.exit(selftest())
'''
EX_SUITES["hooks/sfgood.py"] = SELFTEST_HOOK.format(
    name="sfgood", body='    assert decide([]) == "undetermined"\n    assert decide({}) == "allow"\n')
# known-FALSE, the second shape: the word is in PRODUCTION code, the selftest never takes it.
# closure.py reads this suite as `carries` -- the false positive this block exists for.
EX_SUITES["hooks/sfbad.py"] = SELFTEST_HOOK.format(name="sfbad", body='    assert decide({}) == "allow"\n')

xroot = Path(tempfile.mkdtemp(prefix="class-exercise-ctl-"))
try:
    (xroot / "tools/inst").mkdir(parents=True)
    (xroot / "tools/inst/inst.py").write_text(INST, encoding="utf-8")
    (xroot / "tools/inst/quiet.py").write_text(QUIET, encoding="utf-8")
    (xroot / "tools/inst/shaped.py").write_text(SHAPED, encoding="utf-8")
    for rel, body in EX_SUITES.items():
        (xroot / rel).parent.mkdir(parents=True, exist_ok=True)
        (xroot / rel).write_text(body, encoding="utf-8")
    xhooks = {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": f"python {xroot.as_posix()}/hooks/{n}.py"}
        for n in ("sfgood", "sfbad", "hk")]}]}
    (xroot / "settings.json").write_text(json.dumps({"hooks": xhooks}), encoding="utf-8")

    # the site grammar itself, on the instrument
    isites = {s["lo"]: s["branch"] for s in exercise.file_sites(INST)}
    check("site: module-level `UNDET = ...` is a site but not a branch", isites.get(1), False)
    check("site: guarded `return UNDET` is a branch", isites.get(6), True)
    check("site: marker-test `if k == UNDET` header is not a branch", isites.get(17), False)
    check("site: the body under a marker test is a branch", isites.get(18), True)
    check("site: a comment naming the class is no site",
          exercise.file_sites("def f(x):\n    if x:\n        return 1  # undetermined\n"), [])
    ssites = exercise.file_sites(SHAPED)
    check("site: a `not isinstance` guard body is a shape branch",
          [(s["lo"], s["branch"], s["shape"]) for s in ssites], [(3, True, True)])
    check("site: `x is not None and not isinstance(x, str)` is a shape guard too",
          [s["shape"] for s in exercise.file_sites(
              "def f(x):\n    if x is not None and not isinstance(x, str):\n        return None\n")], [True])
    check("site: a positive isinstance dispatch is not a shape guard",
          exercise.file_sites("def f(x):\n    if isinstance(x, str):\n        return x\n"), [])
    check("site: a named branch under a shape guard stays named (the word wins)",
          [(s["lo"], s["shape"]) for s in exercise.file_sites(INST) if s["lo"] == 6], [(6, False)])

    xrows = {r["suite"]: r for r in exercise.scan(xroot, jobs=4)}
    got = {k: v["class"] for k, v in xrows.items()}
    want = {
        "tools/ex-true/controls.py": "exercised",
        "tools/ex-testbody/controls.py": "exercised",
        "hooks/tests/test_hk.py": "exercised",
        "hooks/sfgood.py": "exercised",
        "tools/ex-named/controls.py": "named-only",
        "hooks/sfbad.py": "named-only",
        "tools/ex-caseonly/controls.py": "case-only",
        "tools/ex-shape/controls.py": "exercised",
        "tools/ex-shape-unnamed/controls.py": "unnamed-exercise",
        "tools/ex-shape-valid/controls.py": "case-only",
        "tools/ex-header/controls.py": "branch-unreached",
        "tools/ex-unnamed/controls.py": "unnamed-exercise",
        "tools/ex-absent/controls.py": "absent",
        "tools/ex-failing/controls.py": "undetermined",
    }
    for suite, w in want.items():
        check(f"exercise: {suite} -> {w}", got.get(suite), w)
    # the asserted VALUES behind the two sides, printed so the calibration record has them
    for suite in ("tools/ex-true/controls.py", "hooks/tests/test_hk.py", "hooks/sfgood.py",
                  "tools/ex-named/controls.py", "hooks/sfbad.py"):
        r = xrows.get(suite, {})
        print(f"     value {suite}: static={r.get('static')} case={r.get('case')} branch={r.get('branch')}")
    check("known-FALSE sfbad reads `carries` to closure.py (the proxy's false positive)",
          xrows["hooks/sfbad.py"]["static"], "carries")
    check("child route: the probe loaded in the spawned hook too (2 processes)",
          xrows["hooks/tests/test_hk.py"]["procs"], 2)
    check("child route: the branch that ran is the child's", xrows["hooks/tests/test_hk.py"]["branch"],
          ["hk.py:9"])
    check("undetermined says why", "did not pass" in xrows["tools/ex-failing/controls.py"]["detail"], True)
    check("branch-unreached names the named branches that did not run",
          xrows["tools/ex-header/controls.py"]["unreached"], ["inst.py:18", "inst.py:6"])
    check("exercised suite: the named branch it did not take is still listed, not hidden",
          xrows["tools/ex-true/controls.py"]["unreached"], ["inst.py:18"])

    level, line = exercise.verdict(list(xrows.values()))
    check("a named-only suite -> WARN (born severity)", level, "WARN")
    check("WARN line names both named-only suites",
          "ex-named" in line and "sfbad" in line and "1 undetermined" in line, True)
    clean = [r for r in xrows.values() if r["class"] != "named-only"]
    check("no named-only -> PASS, undetermined still reported",
          exercise.verdict(clean), ("PASS", "PASS: no suite names the class without running a case for "
                                            "it; 1 undetermined (excluded from every count)"))
    check("exit code: WARN -> 1, PASS -> 0",
          (exercise.report(list(xrows.values())), exercise.report(clean)), (1, 0))
    check("no probe env -> the probe is inert (nothing written, nothing raised)",
          __import__("subprocess").run(
              [sys.executable, "-c", "import sitecustomize"], cwd=str(exercise.PROBE_DIR),
              capture_output=True, text=True,
              env={k: v for k, v in __import__("os").environ.items()
                   if k not in ("CC_PROBE_MAP", "CC_PROBE_OUT")}).returncode, 0)
finally:
    shutil.rmtree(xroot, ignore_errors=True)

n = len(RAN)   # derived; a hand count here read 22 while the suite grew
if FAILS:
    print(f"FAILED {len(FAILS)}/{n}:")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print(f"ALL PASS {n}/{n} (3 routes x carries/lacks, 2 undetermined shapes, "
      f"FAIL/PASS ladder + the no-downgrade regression, proxy boundary, code-token proxy, live tree; "
      f"exercise: 3 routes x 3 branch shapes, named-only both shapes, WARN ladder)")
