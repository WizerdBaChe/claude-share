"""Two-sided calibration for project_registry_gist.py — stdlib only, hermetic.

Run: python hooks/tests/test_project_registry_gist.py   (exit 0 = all pass)

WHY THIS EXISTS. The hook is a SessionStart injector: it prints or it does not,
and it fails open in silence. A parser that stopped matching would look exactly
like a quiet registry, and the prior-art rule that every session leans on would
be enforced by nothing. Nobody would see the difference from the outside.

The hook's own docstring carries `review-when: that column layout changes`.
L-1/L-2 below are that trigger made EXECUTABLE: L-1 parses the LIVE
references/PROJECTS.md and requires real rows, L-2 feeds the same file with its
columns removed and requires zero — so L-1 is known to be capable of failing.
A positive control that never fires is not a control.

EXTENDING (PH-11 / AP-61): a new registry ROW SHAPE the parser must accept gets
a case in GOOD; a line shape it must ignore gets one in IGNORED. A new CAP gets
a case beside C-1..C-3. No list outside this file changes.
"""
import importlib.util
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "project_registry_gist.py"
HOME = Path(__file__).resolve().parents[2]
LIVE = HOME / "references" / "PROJECTS.md"

spec = importlib.util.spec_from_file_location("project_registry_gist", HOOK)
gist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gist)

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    ok = got == want
    if not ok:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if ok else 'FAIL'} {name}")


def check_that(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        FAILS.append(f"{name}: {detail}" if detail else name)
    print(f"{'ok  ' if cond else 'FAIL'} {name}")


def rows(*lines: str) -> list[str]:
    return gist.gist_rows("\n".join(lines))


def run_main(text: str | None) -> str:
    """main() against a temp registry (None = the file does not exist)."""
    real = gist.REG
    tmp = Path(tempfile.mkdtemp(prefix="pr-gist-"))
    try:
        reg = tmp / "PROJECTS.md"
        if text is not None:
            reg.write_text(text, encoding="utf-8")
        gist.REG = reg
        buf = io.StringIO()
        with redirect_stdout(buf):
            gist.main()
        return buf.getvalue()
    finally:
        gist.REG = real


HEADER = "|project|status|path|last-checkpoint|next|predecessor|"
RULE = "|---|---|---|---|---|---|"

# ---------------------------------------------------------------- known-GOOD
print("-- rows the gist MUST carry")

r = rows(HEADER, RULE, "|Prism|active|D:\\<WORK_ROOT>\\Prism|2026-08-25 ok|build|")
check("G-1 one ordinary row parses to one gist line", len(r), 1)
check_that("G-1b name, path and checkpoint all survive",
           "Prism" in r[0] and "D:\\<WORK_ROOT>\\Prism" in r[0] and "2026-08-25" in r[0],
           r[0] if r else "no row")

r = rows(HEADER, RULE, "|X|active (L1 relaxation, ask-gate)|/p|2026-01-01|-|")
check("G-2 status is cut at the first paren", r[0].split("[")[1].split("]")[0], "active")

r = rows(HEADER, RULE, "|X|maintenance — dormant since June|/p|2026-01-01|-|")
check("G-3 status is cut at the em-dash", r[0].split("[")[1].split("]")[0], "maintenance")

r = rows(HEADER, RULE, "|X|active|/p|2026-01-01 phase 3 of 5, next is UAT|-|")
check_that("G-4 checkpoint keeps only its leading token",
           r[0].endswith("(ckpt 2026-01-01)"), r[0])

r = rows(HEADER, RULE, "|X|active|/p||-|")
check_that("G-5 an empty checkpoint becomes '-', not a crash",
           len(r) == 1 and r[0].endswith("(ckpt -)"), r)

# predecessor column (2026-09-19, L-039). The value it must change is the
# printed line, and it must survive a path long enough to hit LINE_MAX.
r = rows(HEADER, RULE, "|New|active|" + "D:\\<x>" * 60 + "|2026-01-01|-|Old|")
check_that("G-6 a named predecessor is printed, and survives LINE_MAX truncation",
           len(r) == 1 and "[active] (continues Old) D:" in r[0] and len(r[0]) <= gist.LINE_MAX, r)
r = rows(HEADER, RULE, "|New|active|/p|2026-01-01|-|-|")
check("G-6b predecessor '-' prints nothing extra", r, ["- New [active] /p  (ckpt 2026-01-01)"])
r = rows(HEADER, RULE, "|New|active|/p|2026-01-01|-|")
check("G-6c a row missing the predecessor cell still parses, with no lineage", r,
      ["- New [active] /p  (ckpt 2026-01-01)"])

# ---------------------------------------------------------------- known-BAD
print("\n-- lines the gist MUST NOT carry (a row for these is a false positive)")

check("B-1 the header row is not a project", rows(HEADER), [])
check("B-2 the separator row is not a project", rows(RULE), [])
check("B-3 prose outside the table is not a project",
      rows("Registry of record. Add a row per project."), [])
check("B-4 a short row (too few cells) is skipped",
      rows(HEADER, RULE, "|X|active|/p|"), [])
check("B-5 a row with no name is skipped",
      rows(HEADER, RULE, "||active|/p|2026-01-01|-|"), [])
check("B-6 an empty registry yields no rows, not an error", rows(""), [])

# ---------------------------------------------------------------- caps
print("\n-- caps (a runaway registry must not flood the session)")

r = rows(HEADER, RULE, "|X|" + "s" * 200 + "|/p|2026-01-01|-|")
check_that(f"C-1 status is capped at STATUS_MAX={gist.STATUS_MAX}",
           len(r[0].split("[")[1].split("]")[0]) <= gist.STATUS_MAX, r[0])
r = rows(HEADER, RULE, "|" + "N" * 300 + "|active|" + "/p" * 200 + "|2026-01-01|-|")
check_that(f"C-2 a row is capped at LINE_MAX={gist.LINE_MAX}",
           len(r[0]) <= gist.LINE_MAX, len(r[0]))
big = "\n".join([HEADER, RULE] + [f"|proj{i}|active|/path/{i}|2026-01-01|-|"
                                  for i in range(400)])
out = run_main(big)
check_that(f"C-3 the whole injection is capped at TOTAL_MAX={gist.TOTAL_MAX}",
           0 < len(out.rstrip("\n")) <= gist.TOTAL_MAX, len(out))

# C-4 (2026-09-27): overflow must drop row DETAIL, never a project NAME. The
# registry size is realistic (70 rows of ~100 chars, over TOTAL_MAX); C-4b is
# the proof that C-4 exercised the overflow path rather than a registry small
# enough to fit whole -- the value the old [:TOTAL_MAX] cut would have changed.
real_rows = [f"|project-name-{i:02d}|active|D:\\<WORK_ROOT>\\some-long-folder-name-{i:02d}\\sub|2026-09-{i % 28 + 1:02d}|-|"
             for i in range(70)]
out = run_main("\n".join([HEADER, RULE] + real_rows))
missing = [i for i in range(70) if f"project-name-{i:02d}" not in out]
check_that("C-4 every project name survives an over-budget registry", not missing, f"missing {missing}")
check_that("C-4b ...and C-4 really overflowed (names-only tail present, still within TOTAL_MAX)",
           "names only" in out and len(out.rstrip("\n")) <= gist.TOTAL_MAX, len(out))

# ---------------------------------------------------------------- fail-open
print("\n-- fail-open: a SessionStart hook may never break the session")

check("F-1 a missing registry prints nothing and does not raise", run_main(None), "")
check("F-2 a registry with no table prints nothing",
      run_main("# Projects\n\nNone yet.\n"), "")
out = run_main("\n".join([HEADER, RULE, "|X|active|/p|2026-01-01|-|"]))
check_that("F-3 a real registry prints the header line and the row",
           out.startswith("[project-registry]") and "- X [active] /p" in out, out[:120])

# ------------------------------------------------------- the review-when made live
print("\n-- L-1/L-2: the live registry, and the mutation that proves L-1 can fail")

if not LIVE.is_file():
    # Loud, and counted in no verdict: not finding the file determines nothing
    # about the parser (AP-62). A silent skip is how a control rots.
    print(f"SKIP L-1/L-2: {LIVE} is missing — this suite could not check the "
          f"live column layout, which is the only thing that tests the "
          f"docstring's review-when trigger")
else:
    live_text = LIVE.read_text(encoding="utf-8", errors="replace")
    live_rows = gist.gist_rows(live_text)
    check_that("L-1 the LIVE registry still parses (review-when: column layout)",
               len(live_rows) >= 5,
               f"{len(live_rows)} row(s) — if PROJECTS.md changed its columns, "
               f"fix gist_rows(), not this number")
    check_that("L-1b every live row carries a path",
               all(len(x.split("] ", 1)) == 2 and x.split("] ", 1)[1].strip()
                   for x in live_rows),
               [x for x in live_rows if len(x.split("] ", 1)) != 2][:2])
    # L-1c: a `|` inside a cell splits it and shifts every later column, yet the
    # row still carries a non-empty (wrong) path, so L-1b passes it. 2026-09-14:
    # `max|Δ|=1.4e-4` in a status cell injected `COMSOL_Test [...] Δ (ckpt
    # =1.4e-4...)` while this suite printed ALL TESTS PASSED. The value that
    # defect changes is the cell count, so that is what is asserted.
    def misaligned(text: str) -> list[str]:
        width, bad = None, []
        for ln in text.splitlines():
            if not ln.startswith("|"):
                continue
            cells = gist._cells(ln)
            if width is None:
                if gist._is_declared_header(cells):
                    width = len(cells)
                continue
            if len(cells) >= 7 and not gist._is_separator(cells) and len(cells) != width:
                bad.append(f"{cells[1]} ({len(cells)} cells, header {width})")
        return bad
    check("L-1c every live row has the declared header's cell count",
          misaligned(live_text), [])
    # Mutation for L-1c: one `|` planted after the name cell of the first data row.
    lines, seen_header, planted = live_text.splitlines(), False, False
    for i, ln in enumerate(lines):
        if not ln.startswith("|"):
            continue
        cells = gist._cells(ln)
        if gist._is_declared_header(cells):
            seen_header = True
        elif seen_header and len(cells) >= 7 and not gist._is_separator(cells):
            lines[i] = ln.replace(" | ", " | a|b ", 1)
            planted = True
            break
    baseline = len(misaligned(live_text))
    check_that("L-1c-mut a planted `|` inside a cell is caught",
               planted and len(misaligned("\n".join(lines))) == baseline + 1,
               f"planted={planted} baseline={baseline}")
    # Mutation: drop the trailing columns from every live row. The parser must
    # go to zero -- if it still reports rows, L-1 was passing on nothing.
    mutated = "\n".join(
        ("|".join(ln.split("|")[:4]) + "|") if ln.startswith("|") else ln
        for ln in live_text.splitlines())
    check("L-2 the same registry with its columns cut yields 0 rows",
          gist.gist_rows(mutated), [])

# --------------------------------------- AP-62: the input that matches no class
print("\n-- U-1/U-2: a row shape the parser cannot classify (AP-62)")

# The declared classes are `project row` and `ignored line`. A table whose
# COLUMNS WERE RENAMED belongs to neither: nothing in it is a project row, and
# until 2026-09-09 the parser had no third class to put it in. It folded — into
# `row`, emitting the foreign header and its data as plausible gist lines. That
# is the AP-62 shape exactly: silent, because the count stays plausible, and it
# is why the docstring's `review-when: that column layout changes` could sit
# there catching nothing. U-1/U-2 pinned it in that state; the fix landed and
# they were rewritten with it, which is the only reason it could not land
# quietly. They now pin the third class instead of the fold.
def note_of(text: str) -> str:
    """layout_note() through a shim, so a hook that LOST it fails the case that
    needs it instead of aborting the run with an AttributeError three cases
    early. Measured while calibrating this block against the pre-fix hook: the
    raw call took U-2 and U-2b down with it, and a control that stops the run is
    not a control."""
    fn = getattr(gist, "layout_note", None)
    return fn(text) if callable(fn) else ""


FOREIGN = "|name|owner|tier|updated|notes|"
renamed = "\n".join([FOREIGN, RULE, "|Prism|nathan|A|2026-08-25|x|"])
check("U-1 a renamed 5-column layout is UNDETERMINED, so it yields no rows: "
      "five cells in an unknown order are not project rows",
      gist.gist_rows(renamed), [])
check_that("U-1b ...and the drift is NAMED, not just absent — a silent "
           "non-injection reads the same as a quiet registry",
           note_of(renamed).startswith("name | owner | tier"),
           note_of(renamed) or "layout_note() is missing from the hook")

# The other half: withholding must reach the session. L-1 asks only for >= 5
# rows, which a renamed layout used to satisfy; L-2's mutation cuts COLUMNS (too
# few cells -> 0 rows) and never exercised renaming at all. So the case that
# matters is what main() actually prints.
many = "\n".join([FOREIGN, RULE] +
                 [f"|p{i}|nathan|A|2026-01-01|x|" for i in range(6)])
out = run_main(many)
check_that("U-2 main() withholds the gist and says why, naming both the header "
           "it found and the one it reads",
           "NOT injected" in out and "name | owner | tier" in out
           and "- p0 [nathan]" not in out, out[:160])
check_that("U-2b a row ABOVE the declared header is not carried either — "
           "anchoring is positional, and that is stated where it can be read",
           gist.gist_rows("\n".join(["|ghost|active|/p|2026-01-01|-|",
                                     HEADER, RULE,
                                     "|real|active|/p|2026-01-01|-|"]))
           == ["- real [active] /p  (ckpt 2026-01-01)"],
           gist.gist_rows("\n".join(["|ghost|active|/p|2026-01-01|-|", HEADER,
                                     RULE, "|real|active|/p|2026-01-01|-|"])))

OLD5 = "|project|status|path|last-checkpoint|next|"
old = "\n".join([OLD5, "|---|---|---|---|---|"] + [f"|p{i}|active|/p|2026-01-01|-|" for i in range(6)])
out = run_main(old)
check_that("U-3 the pre-2026-09-19 five-column header (no predecessor) is withheld "
           "and named — a registry that lost the column cannot carry lineage",
           "NOT injected" in out and "- p0 [active]" not in out, out[:160])

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
