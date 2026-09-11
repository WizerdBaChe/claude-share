"""Two-sided calibration for fieldwork_threshold_notice.py — stdlib only, hermetic.

Run: python hooks/tests/test_fieldwork_threshold_notice.py   (exit 0 = all pass)

WHY THIS EXISTS. This is a SHADOW probe on the highest-volume matcher in the
config (PreToolUse on Read|Grep|Glob). It never blocks and never prints, so
every way it can break is invisible from the outside: stop counting and the log
stays empty, which is indistinguishable from a quiet week; start over-counting
and the rows say the delegation threshold is crossed constantly, which is a
finding about §1 that would in fact be a bug in here. Only running it tells
those apart (AP-63).

BOTH SIDES. TRIP-* are inputs that MUST be counted; QUIET-* are inputs that must
NOT be. The QUIET side carries the three false positives this hook actually
shipped and fixed — the 2000-line charge for an unlimited Read (2026-08-14), the
2000-line charge for an unreadable path (2026-08-15), and a session reading back
its own scratchpad output (2026-08-15). Loosening a gate ships with the case it
used to catch, so each one is pinned here rather than remembered.

T-0 pins the thresholds against the LITERAL text of ops/20-dispatch.md §1. The
docstring's claim is that they are deliberately untuned; that claim is only
worth anything if something checks it.

EXTENDING (PH-11 / AP-61): a new counted shape gets a TRIP row, a new exclusion
a QUIET row. Both are lists of payloads, so a case is one line.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "fieldwork_threshold_notice.py"
HOME = Path(__file__).resolve().parents[2]
DISPATCH_RULE = HOME / "ops" / "20-dispatch.md"
LIVE_LOG = HOME / "telemetry" / "fieldwork-shadow.jsonl"

FAILS: list[str] = []
SESSION = "aaaabbbb-1111-2222-3333-444444444444"


def check(name: str, got, want) -> None:
    ok = got == want
    if not ok:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if ok else 'FAIL'} {name}")


def check_that(name: str, cond: bool, detail="") -> None:
    if not cond:
        FAILS.append(f"{name}: {detail}" if detail else name)
    print(f"{'ok  ' if cond else 'FAIL'} {name}")


class Box:
    """One isolated CLAUDE_CONFIG_DIR: its own state dir and its own log."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="fieldwork-"))
        self.env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.dir),
                        PYTHONIOENCODING="utf-8")
        # This box's whole point is CLAUDE_CONFIG_DIR isolation; an inherited
        # CLAUDE_TELEMETRY_DIR (e.g. from a harness running this suite) now
        # outranks it in the hook's own LOG_PATH resolution and would steer
        # rows away from self.log, so it must not leak in here.
        self.env.pop("CLAUDE_TELEMETRY_DIR", None)
        self.log = self.dir / "telemetry" / "fieldwork-shadow.jsonl"

    def call(self, tool: str, ti: dict, session: str = SESSION):
        payload = json.dumps({"tool_name": tool, "tool_input": ti,
                              "session_id": session, "cwd": str(self.dir)})
        p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=payload,
                           capture_output=True, text=True, env=self.env, timeout=60)
        if p.returncode != 0 or (p.stdout or "").strip():
            FAILS.append(f"SHADOW CONTRACT broken by {tool}({ti}): rc={p.returncode}, "
                         f"stdout={(p.stdout or '')[:120]!r} — this probe must never "
                         f"block or annotate real work")
        return p

    def rows(self):
        if not self.log.is_file():
            return []
        return [json.loads(ln) for ln in self.log.read_text(encoding="utf-8").splitlines()
                if ln.strip()]

    def state(self, session: str = SESSION) -> dict:
        f = self.dir / "cache" / "fieldwork-shadow" / f"{session}.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def make_file(box: Box, name: str, lines: int) -> str:
    p = box.dir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x\n" * lines, encoding="utf-8")
    return str(p)


# --------------------------------------------------- T-0: the thresholds are §1's
print("-- T-0: the constants are 20-dispatch.md §1's literal defaults, not tuned here")

import importlib.util  # noqa: E402  (after the helpers, before the cases that need it)

spec = importlib.util.spec_from_file_location("fieldwork_threshold_notice", HOOK)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

check("T-0a FILE_THRESHOLD", probe.FILE_THRESHOLD, 3)
check("T-0b LINE_THRESHOLD", probe.LINE_THRESHOLD, 200)
check("T-0c BROAD_SEARCH_THRESHOLD", probe.BROAD_SEARCH_THRESHOLD, 1)
if DISPATCH_RULE.is_file():
    rule = DISPATCH_RULE.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"touches\s*>(\d+)\s*files\s*or\s*>(\d+)\s*\n?\s*lines", rule)
    check_that("T-0d the rule text still says >3 files / >200 lines",
               bool(m) and (int(m.group(1)), int(m.group(2)))
               == (probe.FILE_THRESHOLD, probe.LINE_THRESHOLD),
               f"rule says {m.groups() if m else 'NOT FOUND'}, hook says "
               f"({probe.FILE_THRESHOLD}, {probe.LINE_THRESHOLD}) — if §1 moved, "
               f"move the hook WITH it and say so; do not quietly pick friendlier "
               f"numbers here")
else:
    print(f"SKIP T-0d: {DISPATCH_RULE} is missing — the thresholds could not be "
          f"compared with the rule they claim to copy (counted in no verdict)")

# --------------------------------------------------- TRIP: must be counted
print("\n-- TRIP: crossings the probe MUST record")

box = Box()
for i in range(4):
    box.call("Read", {"file_path": make_file(box, f"f{i}.txt", 2)})
check_that("TRIP-1 a fourth distinct file crosses files>3",
           any("files=4>3" in r["reasons"] for r in box.rows()), box.rows())

box = Box()
box.call("Read", {"file_path": make_file(box, "big.txt", 5), "limit": 201})
check_that("TRIP-2 an explicit limit above 200 crosses lines",
           any(any(x.startswith("lines~201") for x in r["reasons"]) for r in box.rows()),
           box.rows())

box = Box()
box.call("Read", {"file_path": make_file(box, "long.txt", 400)})
check_that("TRIP-2b an unlimited Read of a 400-line file counts its REAL length",
           any(any(x.startswith("lines~401") for x in r["reasons"]) for r in box.rows()),
           box.state())

box = Box()
box.call("Grep", {"pattern": "TODO"})
check_that("TRIP-3 an unscoped Grep is a broad search",
           any("broad_search=1" in r["reasons"] for r in box.rows()), box.rows())

box = Box()
box.call("Glob", {"pattern": "**/*.py", "path": "."})
check_that("TRIP-3b a Glob aimed at the whole tree is a broad search",
           any("broad_search=1" in r["reasons"] for r in box.rows()), box.rows())

box = Box()
for _ in range(3):
    box.call("Grep", {"pattern": "TODO"})
check("TRIP-4 only the FIRST crossing is logged (the counters carry the rest)",
      len(box.rows()), 1)
check_that("TRIP-4b but the counters keep counting after the trip",
           box.state().get("broad") == 3, box.state())

# --------------------------------------------------- QUIET: must NOT be counted
print("\n-- QUIET: the three false positives this probe shipped, pinned as cases")

box = Box()
box.call("Read", {"file_path": make_file(box, "tiny.txt", 2)})
check_that("QUIET-1 an unlimited Read of a 2-line file is ~2 lines, NOT the 2000 cap "
           "(regression: 2026-08-14)",
           box.state().get("lines", 0) <= 5 and not box.rows(),
           f"lines={box.state().get('lines')}, rows={box.rows()}")

box = Box()
box.call("Read", {"file_path": str(box.dir / "does-not-exist.md")})
check_that("QUIET-2 an unreadable path charges 0, not the cap (regression: 2026-08-15)",
           box.state().get("lines", -1) == 0 and not box.rows(),
           f"lines={box.state().get('lines')}, rows={box.rows()}")

box = Box()
own = make_file(box, f"scratchpad/{SESSION[:8]}/report.md", 400)
box.call("Read", {"file_path": own})
check_that("QUIET-3 a session reading back its OWN scratchpad output is not fieldwork "
           "(regression: 2026-08-15)",
           box.state().get("lines", 0) == 0 and not box.rows(),
           f"state={box.state()}")

box = Box()
other = make_file(box, "scratchpad/99999999/report.md", 400)
box.call("Read", {"file_path": other})
check_that("QUIET-3b but ANOTHER session's scratchpad still counts — the exclusion is "
           "'my own output', not 'anything called scratchpad'",
           box.state().get("lines", 0) > 200, box.state())

box = Box()
for _ in range(6):
    box.call("Read", {"file_path": make_file(box, "same.txt", 2)})
check_that("QUIET-4 re-reading ONE file six times is one file, not six",
           box.state().get("files") and len(box.state()["files"]) == 1
           and not box.rows(), box.state())

box = Box()
box.call("Grep", {"pattern": "TODO", "path": "tools/graph-snapshot", "glob": "*.py"})
check_that("QUIET-5 a Grep scoped to a directory with a glob filter is not broad",
           box.state().get("broad", 0) == 0 and not box.rows(), box.state())

box = Box()
box.call("Bash", {"command": "ls"})
box.call("Write", {"file_path": "x.md"})
check("QUIET-6 tools outside Read|Grep|Glob are not this probe's business",
      box.state(), {})

# --------------------------------------------------- UNDETERMINED: not charged
print("\n-- U: input the probe cannot classify is charged nothing (AP-62)")

# The counted classes are `a file this Read consumes` and `a broad search`. A
# `file_path` that is not a string belongs to neither — and until 2026-09-09 it
# was folded into the file list as `"{'a': 1}"`, so four malformed payloads
# could trip files>3 and log fieldwork that never happened. In a probe whose
# only product is a measurement, that fold IS the defect.
box = Box()
box.call("Read", {"file_path": {"unexpected": "shape"}})
box.call("Read", {"file_path": ["a", "b"]})
box.call("Read", {"file_path": 12345})
box.call("Read", {"file_path": None})
st = box.state()
check_that("U-1 four unclassifiable file_paths charge 0 files and 0 lines",
           st.get("files") == [] and st.get("lines") == 0, st)
check("U-1b and nothing was logged as a crossing", box.rows(), [])

box = Box()
box.call("Read", ["file_path"])          # call() itself fails the suite on rc!=0
box.call("Grep", "not even a mapping")
check_that("U-2 a non-mapping tool_input exits 0 silently and leaves no state "
           "(it crashed with AttributeError until 2026-09-09)",
           box.state() == {}, box.state())

box = Box()
for raw in ("[1, 2]", '"a string payload"', "null"):
    p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=raw,
                       capture_output=True, text=True, env=box.env, timeout=60)
    check_that(f"U-2b a payload that parses but is not an object ({raw}) exits 0 "
               f"silently — the same crash class, one level out",
               p.returncode == 0 and not (p.stdout or "").strip(),
               f"rc={p.returncode} stdout={(p.stdout or '')[:80]!r}")

# Negative control: without this, U-1 would also pass on a probe that counts
# nothing at all.
box = Box()
box.call("Read", {"file_path": make_file(box, "real.txt", 5)})
check_that("U-3 a well-formed Read of a real file IS still counted",
           len(box.state().get("files", [])) == 1, box.state())

# --------------------------------------------------- fail-open + isolation
print("\n-- fail-open, and isolation from the live telemetry")

box = Box()
for raw in ("not json", '{"tool_name": "Read"}', "{}"):
    p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=raw,
                       capture_output=True, text=True, env=box.env, timeout=60)
    check_that(f"FO {raw[:24]!r} exits 0 silently",
               p.returncode == 0 and not (p.stdout or "").strip(),
               f"rc={p.returncode} stdout={(p.stdout or '')[:80]!r}")

before = LIVE_LOG.stat().st_size if LIVE_LOG.exists() else -1
box = Box()
box.call("Grep", {"pattern": "TODO"})
after = LIVE_LOG.stat().st_size if LIVE_LOG.exists() else -1
check_that("I-1 the LIVE fieldwork-shadow.jsonl was not written to by this suite",
           after == before,
           f"{before} -> {after} bytes; CLAUDE_CONFIG_DIR isolation broke and every "
           f"reading taken from that file would be inflated by test rows")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
