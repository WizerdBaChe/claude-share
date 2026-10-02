"""hook proof-of-life — run what every registered hook says proves it still works.

Status: live 2026-09-08 | severity: FAIL when a declared suite fails, when a
declaration cannot be read, or when a registered hook declares NOTHING (promoted
from WARN on 2026-09-08, the day `uncovered` reached 0 — that was the promotion
trigger recorded in integrity-sweep check 31); WARN when a hook declares only a
sweep check, which is named-but-not-run (consumer = the human/LLM reading the
sweep) | controls: `controls.py` (two-sided, `ALL PASS n/n`) | wired:
`ops/references/integrity-sweep.md` check 31.

PH-11 / AP-63 (`ops/references/principle-design-guide.md`): a mechanism needs a
RECURRING proof-of-life, not only a birth one. Being NAMED in the sweep is not
being RUN by it. The measured case is `hooks/unattended_run.py`, which called
`_receipt()` without importing it: every scope deny and every stop block raised
NameError, a crashing hook fails open, and the offline run's two guards were
inert for a day before a manual audit found it. Its control suite existed and
passed the moment it was run -- nothing ran it.

So this tool executes the suites rather than listing them. The declaration lives
in each hook's OWN docstring (AP-61: the growth rule is in the artifact's text),
in the shape already used by four hooks before this tool existed:

    Proof-of-life: `python tools/<x>/controls.py`      <- executable
    Proof-of-life: `python hooks/<x>.py --selftest`    <- executable
    Proof-of-life: integrity-sweep check 21            <- manual, NOT proof

EXTENDING (AP-61): a hook gains coverage by adding that one line to its
docstring; no list in this file changes. A new DECLARATION SHAPE, however, is a
new object class and belongs in CLASSES below with a specimen in controls.py.

Classes are enumerated and CLOSED (AP-62). A hook is exactly one of:

    executable   a runnable command was declared -- this tool runs it
    manual       only a sweep check is named -- reported, never counted as proof
    uncovered    no Proof-of-life line at all
    undetermined the file could not be read or parsed

`undetermined` is never folded into `uncovered`: "nobody wrote it down" and "I
could not look" are different findings, and merging them is how a count stays
plausible while meaning nothing.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
SETTINGS = HOME / "settings.json"
# One temp dir for the whole run: many declared suites do not isolate their
# own telemetry writes, so this harness isolates them from the outside
# instead of trusting every one of ~25 suites to do it itself.
_POL_TELEMETRY_DIR = tempfile.mkdtemp(prefix="pol-telemetry-")
# Per suite. TWO measurements, and the difference between them is the reason
# this number is large:
#   under load  (2026-09-08, three sweeps at once): ops-health 106.6 s,
#               closeout-intake 36.7 s. 180 s was not enough and the timeout was
#               reported as a FAILING hook.
#   idle        (2026-09-08, re-measured alone after the fleet was completed):
#               ops-health 8.0 s, closeout-intake 5.3 s, the WHOLE sweep of 25
#               distinct suites 57 s.
# The first set was originally recorded here as "measured on an IDLE machine",
# which was wrong -- it was measured while the machine was doing the very thing
# that inflates it. Corrected rather than deleted, because the loaded figure is
# the one this timeout is sized for: a suite is starved by concurrency, not by
# being slow, and 420 s buys ~4x over the worst LOADED reading. Do not lower it
# to fit the idle numbers; that is how the false red came back.
TIMEOUT = 420

CLASSES = ("executable", "manual", "uncovered", "undetermined")
# A suite may report a third RESULT beside pass and fail: its scenario did not
# occur, so it determined nothing (a positive control that did not fire). That is
# not the hook failing, and it is not the hook proven either -- both foldings lie.
# `tools/session-board-test/test_session_board_register.py` H7/H8 is the case:
# the contention scenario needs a busy machine, and on a quiet one a correct hook
# was reported red. A TIMEOUT is the second source of the same result: the suite
# never reached a verdict, so neither did this tool (see run_suite).
EXIT_INCONCLUSIVE = 3

# The declaration marker, and how far after it a command may sit.
MARKER = re.compile(r"Proof-of-life[^:\n]{0,20}:", re.I)
WINDOW = 300
BACKTICKED = re.compile(r"`([^`]{3,200})`")
# A command we are willing to execute: python, on a path inside this repo.
RUNNABLE = re.compile(r"^python\s+\S+\.py\b")
# A manual declaration: it points at a sweep check instead of a command.
SWEEP_REF = re.compile(r"integrity-sweep(?:\.md)?\D{0,12}check\s*(\d+)", re.I)


def registered_hooks(settings_path=SETTINGS):
    """Hook basenames named in settings.json, in sorted order.

    utf-8-sig: a settings.json carrying a BOM crashed a sibling control suite
    for two days in 2026-09; the same read must not be re-invented here.
    """
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    names = set()
    for _event, groups in (data.get("hooks") or {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                m = re.search(r"hooks/([A-Za-z0-9_]+\.py)", hook.get("command", ""))
                if m:
                    names.add(m.group(1))
    return sorted(names)


def declaration(hook_path: Path):
    """-> (class, detail). Never guesses: an unrecognised shape is undetermined.

    EVERY `Proof-of-life:` marker in the docstring is read and the STRONGEST
    declaration wins (executable > manual > undetermined). Taking the first
    marker made the class depend on a POSITION in text that grows -- the same
    defect AP-45 names, found here the moment session_board_register.py turned
    out to carry two markers, the older one naming a sweep check and the newer
    one a runnable suite.
    """
    try:
        doc = ast.get_docstring(ast.parse(hook_path.read_text(encoding="utf-8"))) or ""
    except Exception as exc:
        return "undetermined", f"{type(exc).__name__}: {exc}"
    markers = list(MARKER.finditer(doc))
    if not markers:
        return "uncovered", "no `Proof-of-life:` line in the module docstring"
    best = None
    for m in markers:
        window = " ".join(doc[m.end(): m.end() + WINDOW].split())
        for cmd in BACKTICKED.findall(window):
            if RUNNABLE.match(cmd):
                return "executable", cmd
        sweep = SWEEP_REF.search(window)
        if sweep and best is None:
            best = ("manual", f"integrity-sweep check {sweep.group(1)} (not executable)")
        elif best is None:
            best = ("undetermined",
                    f"declared but no runnable command found: {window[:90]!r}")
    return best


def run_suite(cmd: str, root=None, env_extra=None):
    """-> (ok, summary). Runs from the repo root; the declared commands assume it.

    `env_extra` adds variables on top of the isolated env (class-closure's exercise.py
    passes its line probe this way, so both tools run a suite the SAME way)."""
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd.split(), cwd=str(root or HOME), capture_output=True,
                              text=True, timeout=TIMEOUT,
                              env=dict(os.environ, PYTHONIOENCODING="utf-8",
                                       CLAUDE_TELEMETRY_DIR=_POL_TELEMETRY_DIR,
                                       **(env_extra or {})))
    except subprocess.TimeoutExpired:
        # A timeout determines NOTHING about the hook: the suite may have been
        # starved by a busy machine. Measured 2026-09-08 -- three sweeps running
        # concurrently timed out ops-health at 180 s, and the report named the
        # hook as failing. Folding "I could not finish looking" into "it is
        # broken" is the count that stays plausible while meaning nothing.
        return "inconclusive", (f"timed out after {TIMEOUT}s ({time.monotonic()-start:.0f}s "
                                f"elapsed) -- re-run it alone before believing this")
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    tail = [ln for ln in (proc.stdout or proc.stderr or "").splitlines() if ln.strip()]
    summary = tail[-1][:150] if tail else f"exit {proc.returncode}"
    summary = f"{summary}  [{time.monotonic() - start:.0f}s]"
    if proc.returncode == EXIT_INCONCLUSIVE:
        # The suite ran and its SCENARIO did not occur (a positive control that
        # did not fire). That determines nothing about the hook, so it must not
        # be folded into either verdict -- downgrade-and-forward, never veto.
        return "inconclusive", summary
    return proc.returncode == 0, summary


def sweep(hooks_dir=None, settings_path=SETTINGS, quiet=False, root=None):
    hooks_dir = hooks_dir or (HOME / "hooks")
    rows, cache, start = [], {}, time.monotonic()
    for name in registered_hooks(settings_path):
        kind, detail = declaration(hooks_dir / name)
        ok = None
        if kind == "executable":
            if detail not in cache:
                cache[detail] = run_suite(detail, root=root)
            ok, detail = cache[detail][0], f"{detail} -> {cache[detail][1]}"
        rows.append((name, kind, ok, detail))
    if not quiet:
        _report(rows, len(cache), time.monotonic() - start)
    return rows


def _report(rows, suites, elapsed=None):
    counts = {c: 0 for c in CLASSES}
    for _n, kind, _ok, _d in rows:
        counts[kind] += 1
    failing = [(n, d) for n, k, ok, d in rows if k == "executable" and ok is False]
    unclear = [(n, d) for n, k, ok, d in rows if ok == "inconclusive"]
    # The wall time is printed because it is the thing that decides whether this
    # sweep keeps being RUN. A proof-of-life nobody can afford to wait for
    # decays back into a proof-of-life nobody runs (AP-63's whole failure mode).
    took = f" in {elapsed:.0f}s" if elapsed else ""
    print(f"proof-of-life: {len(rows)} registered hook(s), "
          f"{suites} distinct suite(s) run{took}")
    print("  " + "  ".join(f"{c} {counts[c]}" for c in CLASSES))
    for kind, label in (("undetermined", "UNDETERMINED"), ("uncovered", "uncovered"),
                        ("manual", "manual only")):
        named = [n for n, k, _o, _d in rows if k == kind]
        if named:
            print(f"  [{label}] {', '.join(named)}")
    for name, detail in unclear:
        # Reported loudly, counted nowhere: the run determined nothing.
        print(f"  [INCONCLUSIVE] {name}: {detail}")
    for name, detail in failing:
        # AP-64: the repair site, not just the symptom.
        print(f"  [FAIL] {name}: {detail}")
    if failing:
        print(f"proof-of-life: FAIL {len(failing)} suite(s) — re-run the command "
              f"printed above from {HOME}")
    elif counts["undetermined"]:
        print("proof-of-life: FAIL — a declaration could not be read; fix the "
              "docstring line named above")
    elif counts["uncovered"]:
        # PROMOTED 2026-09-08. This was WARN while a legacy backlog of hooks had
        # no suite at all; the promotion trigger recorded in integrity-sweep
        # check 31 was "uncovered reaching 0", and it reached 0 the same day the
        # last five suites landed. A WARN that everyone has already satisfied is
        # a WARN nobody reads -- and the next uncovered hook will be a NEW one,
        # which is exactly the case worth stopping for.
        print(f"proof-of-life: FAIL — {counts['uncovered']} registered hook(s) "
              f"carry no `Proof-of-life:` line, so nothing re-runs their "
              f"calibration and a hook that died would look like a quiet week. "
              f"Repair: add `Proof-of-life: \\`python <suite>\\`` to the "
              f"docstring named above, writing the suite first if there is "
              f"none. Baseline 2026-09-08 was 0 uncovered.")
    else:
        tail = (f" / {len(unclear)} INCONCLUSIVE (scenario did not occur; the "
                f"hook is not implicated)" if unclear else "")
        manual = (f" / WARN {counts['manual']} declaring only a sweep check "
                  f"(named is not run)" if counts["manual"] else "")
        # --list runs nothing, so it may not print the word this whole tool
        # exists to distinguish from "named". CLASSIFIED is not EXECUTED.
        verdict = (f"PASS ({counts['executable']} executed)" if suites
                   else f"CLASSIFIED ONLY ({counts['executable']} declare a "
                        f"runnable suite; NONE was run — drop --list to execute "
                        f"them)")
        print(f"proof-of-life: {verdict}{manual}{tail}")


def hmi_report(rows):
    """hmi-report/1 (tools/system-hmi/PROTOCOL.md): one point per registered hook.

    The four classes and the inconclusive outcome stay DISTINCT in the document:
    a suite that timed out determines nothing about the hook, so it is
    `state: null, quality: undetermined`, never a fail.
    """
    points = []
    for name, kind, ok, detail in rows:
        point = {"id": "hook-suite." + name[:-3] if name.endswith(".py")
                 else "hook-suite." + name,
                 "alias": name, "ran": kind == "executable", "skip_reason": None,
                 "state": None, "quality": "good",
                 "findings": [{"severity": kind, "label": kind, "text": str(detail)}]}
        if kind == "executable" and ok is True:
            point["state"] = "pass"
        elif kind == "executable" and ok is False:
            point["state"] = "fail"
        elif ok == "inconclusive":
            point["quality"] = "undetermined"
        elif kind in ("uncovered", "undetermined"):
            # the DECLARATION is broken or absent: determinable, and a defect
            point["state"] = "fail"
            point["skip_reason"] = "no-runnable-declaration"
        else:  # manual: named, never run
            point["quality"] = "undetermined"
            point["skip_reason"] = "manual-only"
        points.append(point)
    return {"protocol": "hmi-report/1", "source": "hook-proof-of-life",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "points": points}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true",
                    help="classify only; run no suites (fast, for the sweep's first pass)")
    ap.add_argument("--json", action="store_true",
                    help="run every suite and print an hmi-report/1 document "
                         "(one point per registered hook) instead of the text report")
    args = ap.parse_args()
    if args.json:
        rows = sweep(quiet=True)
        print(json.dumps(hmi_report(rows), ensure_ascii=False, indent=1))
        return 0
    if args.list:
        rows = [(n, *declaration((HOME / "hooks") / n), ) for n in registered_hooks()]
        rows = [(n, k, None, d) for n, k, d in rows]
        _report(rows, 0)
        return 0
    rows = sweep()
    # `is False`, not falsy: "inconclusive" must not be read as a failure, and
    # None (a non-executable row) must not either.
    bad = [r for r in rows if (r[1] == "executable" and r[2] is False)
           or r[1] in ("undetermined", "uncovered")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
