#!/usr/bin/env python3
"""Synthetic-payload tests for ops_health_nudge.py checks 11, 12, 14 + budget.

  check 12 -- interop freshness (added 2026-08-15)
  check 11 -- project ops-relaxation DECLARATION (precision fix 2026-08-15;
              it used to accept a prose mention, so it had never once fired
              correctly -- see CHECK11_CASES)
  check 14 -- stale uncommitted work in ~/.claude (added 2026-08-21). The
              fake home is made a real git repo on demand and dirty paths are
              back-dated with os.utime, so the known-TRUE case (a 5-day-old
              untracked path MUST fire) and the known-FALSE cases (a fresh
              path, a clean repo, no repo at all, a project cwd) are both
              exercised -- a one-sided fixture would pass for a check that
              fires on every dirty tree (global CLAUDE.md gate rule).
  check 13 -- advisory-output status lines (added 2026-09-09). The fixture had
              never created outputs/ at all, so this check had never once run
              in this suite. Its three classes are exercised two-sidedly: a
              spent keyword silences, a file with no status line at all is its
              own finding, and a status line the parse cannot rule on surfaces
              OPEN rather than being read as spent.
  BUDGET   -- the output budget itself (added 2026-08-27, BUDGET_CASES). The
              print used to be a bare `" | ".join(msgs[:4])`: everything past
              the fourth finding vanished with no indicator, so a reader could
              not tell "no dict warning" from "the dict warning was crowded
              out". It was the second: skill-trigger-dict.md was 2.6K over
              DICT_CAP and had been invisible for an unknown number of
              sessions. These cases pin the two properties that fix it --
              nothing is dropped unnamed, and severity decides what yields.

Same style the other guards were tested in: build the input the hook will
actually see, run the real script as a subprocess, assert on stdout + exit code.
Here the "payload" is two things -- the SessionStart JSON on stdin AND a
synthetic ~/.claude tree, reached by pointing USERPROFILE/HOME at a temp dir so
the hook's own os.path.expanduser resolves there.

The tree is built HEALTHY for every other check on purpose, so a noisy tree
cannot hide the thing under test. `noisy=` deliberately breaks that, and only
for the budget cases.

Run against the share-repo copy too -- it carries a declared specialization
(check 11 gated on the ops layer being present):
    python test_ops_health_nudge.py <path-to-hook>
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_cap_binding import hook_caps          # noqa: E402

# abspath: run() launches the hook with cwd set INSIDE the synthetic tree, so
# a relative path handed on the command line would resolve there and every
# case would fail with 0/36 rather than an error.
HOOK = os.path.abspath(
    sys.argv[1] if len(sys.argv) > 1 else
    os.path.join(os.path.expanduser("~/.claude"), "hooks",
                 "ops_health_nudge.py"))
# True when the hook under test is the share-repo copy, which carries a declared
# specialization: check 11 only runs if the ops layer is actually installed, so
# an adopter who never took ops/ is not nagged about a key they never met.
SHARE_EDITION = "CLAUDE_SHARE" in os.path.abspath(HOOK).upper()
ROUTED = [
    "OPS.md", "05-authority.md", "10-command-loop.md", "20-dispatch.md",
    "30-judgment.md", "40-maintenance.md", "50-coach.md", "60-bootstrap.md",
    "70-evolution.md", "environment.md", "rules-usage-dict.md", "lessons.md",
]
NOW = time.time()
# T0 < T1 < T2. Sources land at T0 and the built artifact at T1, so the healthy
# tree really is "artifact newer than its source". A stale case moves one source
# forward to T2. Every mtime is set explicitly -- letting one default to the
# write time is what made the first run of these two cases vacuous.
T0, T1, T2 = NOW - 9000, NOW - 6000, NOW - 3000

INTEROP_PY = '''\
from pathlib import Path
TARGETS = {
    "opencode": {"path": Path(r"%s"), "profile": "full"},
    "codex": {"path": Path(r"%s"), "profile": "full",
              "disabled": "user ruling — maintained from the codex side"},
}
'''
STAMP = "<!-- managed-by: claude-interop | profile: full | source: abc1234 -->\n"


STALE_AGE = NOW - 5 * 86400     # well past STALE_WORK_DAYS (3)


def _dead_pid():
    """A pid that is certainly not running — check 15's run-record fixture.

    Earned, not picked: a process is started and waited on, so the number is
    one the OS has really finished with. A hardcoded low pid would be a guess
    about the host, and the day it guessed wrong the known-TRUE cases would
    pass while the arm they claim to prove sat silent.
    """
    proc = subprocess.Popen([sys.executable, "-c", ""])
    proc.wait()
    return proc.pid


DEAD_PID = _dead_pid()

# Caps read from the HOOK UNDER TEST, never restated here -- a literal copy is
# the defect sweep check 7b exists to catch, and this file would have shipped
# one. Missing keys fall back high enough that a fixture can only ever be MORE
# over cap, never accidentally under it.
CAPS = hook_caps(open(HOOK, encoding="utf-8").read())
# Same reason for the exempt set: a copy here goes stale the next time a file
# is exempted, and the fixture would then seed one finding fewer than it
# asserts -- which is exactly what happened on 2026-09-08 with environment.md.
EXEMPT = set(re.findall(
    r'"([^"]+\.md)"',
    re.search(r"^SIZE_CAP_EXEMPT\s*=\s*\{([^}]*)\}",
              open(HOOK, encoding="utf-8").read(), re.M).group(1)))


def over(name, default):
    return CAPS.get(name, default) + 1024


def git(cc, *args):
    subprocess.run(["git", "-C", cc, "-c", "user.name=t", "-c", "user.email=t@t",
                    "-c", "commit.gpgsign=false", *args],
                   check=True, capture_output=True)


def build(tmp, *, target="fresh", curation="fresh", interop="ok",
          proj=None, ops_layer=True, stale_work=None, noisy=None):
    """Materialise a synthetic ~/.claude. Returns (fake home, cwd to run from).

    proj=None runs from the fake ~/.claude itself, which suppresses check 11
    (is_home) so a check-12 case cannot be polluted by it -- and is the ONLY
    cwd from which check 14 runs at all. Passing a string creates a project dir
    holding that string as its CLAUDE.md and runs from there, which is the only
    way check 11 is reachable at all.

    stale_work=None leaves the fake home as a plain directory (no .git), so
    check 14 sees `git status` fail and stays silent. Any other value makes it
    a real repo with one commit, then: "stale" adds an untracked path dated 5
    days ago; "fresh" adds one dated now; "mixed" both; "stale-modified"
    back-dates a modification to a TRACKED file; "clean" leaves it clean.
    """
    home = os.path.join(tmp, "home")
    cc = os.path.join(home, ".claude")
    os.makedirs(os.path.join(cc, "ops"))
    os.makedirs(os.path.join(cc, "skills"))
    os.makedirs(os.path.join(cc, "opencode"))
    # keep every other check silent
    for f in ROUTED:
        open(os.path.join(cc, "ops", f), "w").write("# stub\n")
    if not ops_layer:
        # An adopter who never took the ops layer. Check 4 (ghost-rule guard)
        # legitimately fires here -- that is not the assertion; check 11's
        # silence is.
        os.remove(os.path.join(cc, "ops", "05-authority.md"))
    open(os.path.join(cc, "ops", "rule-registry.md"), "w").write("# stub\n")
    open(os.path.join(cc, "CLAUDE.md"), "w").write("# stub\n")
    open(os.path.join(cc, "skill-trigger-dict.md"), "w").write("# stub\n")

    # Checks 15 and 16 landed 2026-08-26 and nothing added them to this
    # fixture, so "healthy -> silent" had been FAILING (two findings) ever
    # since -- a red baseline, which makes every later green meaningless.
    # Repaired 2026-08-27. PRE-EXISTING FIXTURE GAP, not a hook defect.
    os.makedirs(os.path.join(cc, "tools", "graph-snapshot", "out"))
    wd = os.path.join(cc, "tools", "graph-snapshot", "out",
                      "watchdog-status.json")
    with open(wd, "w") as f:
        json.dump({"finding": None, "ran_at": "2026-09-09T12:30:26"}, f)
    os.utime(wd, (NOW, NOW))
    # Check 15's second arm (2026-09-09). The healthy state is a run record
    # that CLOSED: a finished run is the case the arm must stay silent on, and
    # putting it in the shared fixture means every other case in this file is
    # asserting against it too, not against an absent file.
    with open(_run_record(cc), "w") as f:
        json.dump({"started_at": "2026-09-09T12:30:01", "state": "finished",
                   "pid": 4242, "carrier": "fixture",
                   "finished_at": "2026-09-09T12:30:26", "exit": 0,
                   "error": None}, f)
    with open(os.path.join(cc, "ops", "cc-reconciled.json"), "w") as f:
        # The binary lives under the FAKE home and does not exist, so check 16
        # reads moved=False and stays silent -- which is the healthy state.
        json.dump({"reconciled_version": "0.0.0",
                   "binary_size": 0, "binary_mtime": 0,
                   "feature_delta": "reports/cc-upgrade-delta/fixture.md"}, f)
    # 2026-09-27: the stamp must name an EXISTING feature-delta record.
    os.makedirs(os.path.join(cc, "reports", "cc-upgrade-delta"), exist_ok=True)
    open(os.path.join(cc, "reports", "cc-upgrade-delta", "fixture.md"), "w").write("x\n")

    tgt = os.path.join(cc, "opencode", "AGENTS.md")
    codex_tgt = os.path.join(cc, "opencode", "CODEX.md")   # never created
    idir = os.path.join(cc, "interop")

    if interop != "absent":
        os.makedirs(idir)
        body = INTEROP_PY % (tgt, codex_tgt)
        if interop == "exits":
            body = "import sys\nsys.exit('leak lib missing')\n" + body
        open(os.path.join(idir, "interop.py"), "w").write(body)
        open(os.path.join(idir, "portable-core.md"), "w").write("core\n")
        for f in ("interop.py", "portable-core.md"):
            os.utime(os.path.join(idir, f), (T0, T0))

    if target != "missing":
        open(tgt, "w").write(
            "# hand-written by somebody else\n" if target == "foreign" else STAMP)
        os.utime(tgt, (T1, T1))
        if target == "stale-core":
            os.utime(os.path.join(idir, "portable-core.md"), (T2, T2))
        elif target == "stale-script":
            os.utime(os.path.join(idir, "interop.py"), (T2, T2))

    if interop != "absent" and curation != "missing":
        s = os.path.join(idir, "curation.stamp")
        open(s, "w").write("abc1234\n")
        if curation == "drifted":
            os.utime(s, (T0, T0))
            os.utime(os.path.join(cc, "CLAUDE.md"), (T2, T2))
        else:
            os.utime(s, (T2, T2))
            os.utime(os.path.join(cc, "CLAUDE.md"), (T0, T0))

    if noisy:
        # A tree with MORE findings than the line can print, so the budget
        # itself is what is under test. Six on purpose: five SEV_BREACH (every
        # file cap) plus one SEV_QUEUE (the intake report, check 1), which is
        # the shape that must decide correctly -- the queue item is the one
        # that may yield. Sizes come from the hook's own constants, never a
        # copy. The queue finding is SEEDED by a stub intake.py in the fake
        # home (since 2026-09-07, when check 1 became a subprocess over
        # ops/lessons/): this suite tests the budget, not the intake tool,
        # which has its own two-sided harness (tools/closeout-intake/controls.py).
        open(os.path.join(cc, "skill-trigger-dict.md"), "w").write(
            "x" * over("DICT_CAP", 28 * 1024) + "\nfixture-skill\n")
        # 30-judgment.md, not environment.md: the latter joined SIZE_CAP_EXEMPT
        # on 2026-09-08 and this fixture would then seed FIVE findings while
        # asserting six. The suite caught that within the same minute, which is
        # also the evidence the exemption changed real behaviour rather than
        # silencing the check -- see the positive control in
        # the 2026-09-08 exemption proposal's step 6 (a private note). Pick a file
        # the hook still rules on, and read the exempt set from the hook.
        assert "30-judgment.md" not in EXEMPT, (
            "the fixture's over-cap ops file is now exempt; pick another")
        open(os.path.join(cc, "ops", "30-judgment.md"), "w").write(
            "z" * over("SIZE_CAP", 22 * 1024))
        sd = os.path.join(cc, "skills", "fixture-skill")
        os.makedirs(sd)
        open(os.path.join(sd, "SKILL.md"), "w").write(
            "---\nname: fixture-skill\ndescription: >\n"
            + "  d" * (CAPS.get("DESC_CAP", 800) + 100) + "\n---\n"
            + "\n" * (CAPS.get("BODY_CAP", 300) + 10))
        os.makedirs(os.path.join(cc, "tools", "closeout-intake"))
        open(os.path.join(cc, "tools", "closeout-intake", "intake.py"),
             "w").write(INTAKE_STUB)
        open(os.path.join(cc, "CLAUDE.md"), "w").write(
            "y" * over("CLAUDE_MD_CAP", 19968))
        # rewritten last, then re-dated: check 12 compares CLAUDE.md's mtime
        # against the curation stamp, and a fresh mtime would add an interop
        # finding this case did not ask for.
        os.utime(os.path.join(cc, "CLAUDE.md"), (T0, T0))
        if noisy == "alarm":
            # + one SEV_ALARM, to pin that it outranks all five breaches.
            os.remove(os.path.join(cc, "ops", "50-coach.md"))

    if stale_work is not None:
        # Make the fake home a real repo with EVERYTHING above committed, so
        # the only dirty paths are the ones each case plants. (The first draft
        # committed one file and left the stubs untracked -- 19 "fresher dirty
        # paths" in every case, a fixture artifact, not a hook defect.)
        git(cc, "init", "-q")
        git(cc, "add", "-A")
        git(cc, "commit", "-q", "-m", "fixture baseline")
        tracked = os.path.join(cc, "CLAUDE.md")
        if stale_work in ("stale", "mixed"):
            p = os.path.join(cc, "stale-note.md")
            open(p, "w").write("finished record nobody committed\n")
            os.utime(p, (STALE_AGE, STALE_AGE))
        if stale_work in ("fresh", "mixed"):
            p = os.path.join(cc, "fresh-note.md")
            open(p, "w").write("in-flight\n")
            os.utime(p, (NOW, NOW))
        if stale_work == "stale-modified":
            open(tracked, "a").write("edited long ago\n")
            os.utime(tracked, (STALE_AGE, STALE_AGE))
        # Check 18 fixtures: a FRESH untracked rule (so check 14 stays quiet
        # and cannot be what makes the case pass) that a committed CLAUDE.md
        # names ("dangling"), names after both are committed ("dangling-fixed"),
        # or that nothing names ("untracked-noref").
        if stale_work in ("dangling", "dangling-fixed", "untracked-noref"):
            os.makedirs(os.path.join(cc, "rules"), exist_ok=True)
            open(os.path.join(cc, "rules", "pointed.md"), "w").write("r\n")
            if stale_work != "untracked-noref":
                open(tracked, "a").write("\nrules index: `pointed`\n")
                git(cc, "add", "CLAUDE.md")
                git(cc, "commit", "-q", "-m", "pointer")
            if stale_work == "dangling-fixed":
                git(cc, "add", "rules/pointed.md")
                git(cc, "commit", "-q", "-m", "target")
    if proj is None:
        return home, cc
    pdir = os.path.join(tmp, "project")
    os.makedirs(pdir)
    with open(os.path.join(pdir, "CLAUDE.md"), "w", encoding="utf-8") as f:
        f.write(proj)
    return home, pdir


def _run_record(cc):
    """Path of the graph watchdog's run record inside a fixture tree."""
    return os.path.join(cc, "tools", "graph-snapshot", "out",
                        "watchdog-run.json")


def _healthy_marker(root):
    """A fresh OK mirror marker inside `root` — check 17's hermetic default.

    Every case runs with this unless it overrides OPS_NUDGE_MIRROR_MARKER:
    without it, the hook would read the REAL machine's marker, and a genuinely
    stale mirror would break every healthy-tree assertion in this file with an
    unrelated ALARM.
    """
    d = os.path.join(root, "_mirror-logs")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "last-run-status.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("OK  2026-09-01 13:00:00  robocopy exit=1 (fixture)\n")
    return p


def run(home, cwd, args=(), env_extra=None):
    env = dict(os.environ, USERPROFILE=home, HOME=home, HOMEPATH=home)
    env.pop("PYTHONPATH", None)
    env["OPS_NUDGE_MIRROR_MARKER"] = _healthy_marker(home)
    # Checks 19/20 would otherwise read the REAL backup disk and vault; point
    # them at paths that do not exist, which both checks treat as host-normal.
    env["OPS_NUDGE_BUNDLE_STATUS"] = os.path.join(home, "no-disk", "b", "s.json")
    env["OPS_NUDGE_VAULT_ROOT"] = os.path.join(home, "no-vault")
    if env_extra:
        env.update(env_extra)
    # `--all` must not read stdin (it is meant to be run by hand at a
    # terminal), so it is handed an empty one here -- if it ever blocks, this
    # call hangs, which is the failure the flag exists to avoid.
    p = subprocess.run([sys.executable, HOOK, *args],
                       input="" if args else json.dumps({"cwd": cwd}),
                       capture_output=True, text=True, env=env, cwd=cwd)
    return p.returncode, p.stdout.strip()


CASES = [
    # (name, build kwargs, expected substrings, forbidden substrings)
    ("healthy -> silent", {}, [], ["interop:", "ops-health"]),
    ("target never deployed (the 2026-08-15 defect)",
     {"target": "missing"}, ["interop:", "opencode not deployed"], []),
    ("target present but foreign",
     {"target": "foreign"}, ["opencode not interop-managed"], ["not deployed"]),
    ("target older than portable-core.md",
     {"target": "stale-core"}, ["opencode older than portable-core.md"], []),
    ("target older than interop.py",
     {"target": "stale-script"}, ["opencode older than interop.py"], []),
    ("no curation stamp",
     {"curation": "missing"}, ["no curation stamp"], ["not deployed"]),
    ("curation out of date",
     {"curation": "drifted"}, ["CLAUDE.md changed since last curation"], []),
    ("two problems joined in one message",
     {"target": "missing", "curation": "missing"},
     ["opencode not deployed", "no curation stamp"], []),
    ("disabled target with no file is not counted",
     {}, [], ["codex"]),
    ("remedy routes to status, never to build",
     {"target": "missing"}, ["interop.py status", "compares commits"], []),
    ("fail-open: interop.py sys.exit()s at import",
     {"interop": "exits"}, [], ["interop:"]),
    ("fail-open: interop/ absent entirely",
     {"interop": "absent"}, [], ["interop:"]),
]


# The literal sentence from the global CLAUDE.md that made the old substring
# test pass vacuously. Kept verbatim: paraphrasing it would test a different
# string than the one that actually broke.
MENTION = ("Otherwise offer to record `ops-relaxation:` in project CLAUDE.md "
           "so the ask happens once per project.\n")
NAG = "no ops-relaxation"

CHECK11_CASES = [
    ("11 real declaration -> silent",
     {"proj": "# Proj\n\nops-relaxation: L1\n"}, [], [NAG]),
    ("11 declaration as a bullet -> silent",
     {"proj": "# Proj\n\n- ops-relaxation: L2\n"}, [], [NAG]),
    ("11 declaration in bold -> silent",
     {"proj": "# Proj\n\n**ops-relaxation:** L0\n"}, [], [NAG]),
    ("11 PROSE MENTION ONLY -> must fire (the 2026-08-15 false negative)",
     {"proj": "# Proj\n\n" + MENTION}, [NAG], []),
    ("11 no mention at all -> fires",
     {"proj": "# Proj\n\nnothing here\n"}, [NAG], []),
    ("11 mention AND a real declaration -> silent",
     {"proj": "# Proj\n\n" + MENTION + "\nops-relaxation: L1\n"}, [], [NAG]),
    ("11 bogus level -> fires",
     {"proj": "# Proj\n\nops-relaxation: L9\n"}, [NAG], []),
    ("11 cwd is the config home -> suppressed",
     {}, [], [NAG]),
]

# Declared share-repo specialization. Canonical has no such gate: on this
# machine the ops layer is always present, and silencing the check when
# ops/05-authority.md goes missing would hide a real ghost-rule failure.
SHARE_CASES = [
    ("11 adopter without the ops layer -> silent (share edition only)",
     {"proj": "# Proj\n\nnothing here\n", "ops_layer": False},
     [] if SHARE_EDITION else [NAG],
     [NAG] if SHARE_EDITION else []),
]


STALE = "stale uncommitted work"

CHECK14_CASES = [
    ("14 back-dated untracked path -> fires",
     {"stale_work": "stale"},
     [STALE, "1 path(s) older than 3d", "stale-note.md"], ["company"]),
    ("14 fresh untracked path -> silent (the in-flight population)",
     {"stale_work": "fresh"}, [], [STALE]),
    ("14 stale beside fresh -> fires and counts the company, names only the stale",
     {"stale_work": "mixed"},
     [STALE, "stale-note.md", "1 fresher dirty path(s)"], ["fresh-note.md"]),
    ("14 clean repo -> silent",
     {"stale_work": "clean"}, [], [STALE]),
    ("14 back-dated TRACKED modification -> fires",
     {"stale_work": "stale-modified"}, [STALE, "CLAUDE.md"], []),
    ("14 not a git repo at all -> silent (fail-open, git exits 128)",
     {}, [], [STALE]),
    ("14 cwd is a project, not the config home -> skipped even when stale",
     {"stale_work": "stale", "proj": "# Proj\n\nops-relaxation: L1\n"},
     [], [STALE]),
]

DANGLING = "committed pointer(s) to uncommitted file(s)"

CHECK18_CASES = [
    ("18 committed CLAUDE.md names a fresh untracked rule -> fires (no age gate)",
     {"stale_work": "dangling"},
     [DANGLING, "CLAUDE.md → rules/pointed.md"], [STALE]),
    ("18 same pointer after the target is committed -> silent",
     {"stale_work": "dangling-fixed"}, [], [DANGLING]),
    ("18 untracked rule nothing names -> silent (check 14's domain, by age)",
     {"stale_work": "untracked-noref"}, [], [DANGLING]),
    ("18 not a git repo -> silent (undetermined, fail-open)",
     {}, [], [DANGLING]),
]


# --------------------------------------------------------------------------
# BUDGET / severity. These are the regression cases for the 2026-08-27 defect:
# the printed line truncated at four findings with NO indicator, so the fifth
# onward were indistinguishable from "healthy". Every case here runs a tree
# with SIX findings -- the "five or more checks fire" condition the acceptance
# for that fix demanded, seeded rather than reasoned about.
TAIL = "more, not shown in full"
# The dict's remedy sentence. It must NOT be printed in the truncated line --
# if it were, the case would be passing because the dict happened to fit, not
# because the tail named it.
DICT_REMEDY = "REVIEW TRIGGER, not a budget"
LESSONS_REMEDY = "route through ops/40-maintenance.md S2a"
# The SEV_QUEUE finding of the noisy fixture. Until 2026-09-07 it was the
# LESSON_CAP entry count (a hard-coded "lessons.md 32 entries" that went red
# on 2026-09-06 when the cap moved and the expectation did not -- the §3
# constant-binding defect). Check 1 is now `intake.py report --nudge`, a
# subprocess over ops/lessons/, so the fixture SEEDS the finding with a stub
# tool (INTAKE_STUB) and the expectation is the stub's own line: nothing here
# restates a value the mechanism owns.
LESSONS_COUNT = "intake: 1 card(s) with hits>=2 never folded"
INTAKE_STUB = (
    "import sys\n"
    "if sys.argv[1:3] == ['report', '--nudge']:\n"
    "    print('intake: 1 card(s) with hits>=2 never folded (L-001) - "
    "route through ops/40-maintenance.md S2a')\n")

# Collapsing is a BUDGET event since 2026-09-08, not a rank cutoff, so the cases
# that exercise the tail must squeeze the ceiling. TIGHT is small enough that
# only the top band survives in the noisy fixture; without it the six findings
# fit and nothing is hidden -- which is the new contract's own known-FALSE case
# (`nothing collapses when there is room`, below).
TIGHT = {"OPS_NUDGE_BYTE_CEILING": "400"}

BUDGET_CASES = [
    # The 2026-08-27 defect was "a breach is crowded out and the reader cannot
    # tell". Band semantics make it structurally impossible rather than merely
    # reported: budget pressure can only collapse a WHOLE band, and the most
    # severe band never collapses -- so the dict breach prints in full here even
    # under a 400-byte ceiling. That is what this case now pins.
    ("budget: squeezed, a breach is never crowded out (the 2026-08-27 defect, "
     "now structural)",
     {"noisy": True}, [TAIL, "skill-trigger-dict.md", DICT_REMEDY], [], TIGHT),
    ("budget: the hidden count is stated, not implied",
     {"noisy": True}, ["(+", TAIL], [], TIGHT),
    ("budget: the tail names the escape hatch",
     {"noisy": True}, ["ops_health_nudge.py --all"], [], TIGHT),
    # The rank cutoff's replacement must not become a severity FILTER: with room
    # to spare, the SEV_QUEUE finding prints in full alongside the breaches.
    # This is the case that caught the first cut of the change (check 11 alone
    # on the screen was being collapsed into its own tail).
    ("budget: with room to spare nothing is hidden, queue included",
     {"noisy": True}, [LESSONS_COUNT, LESSONS_REMEDY], [TAIL]),
    ("budget: squeezed, the queue band collapses whole and is named",
     {"noisy": True}, [TAIL, LESSONS_COUNT], [LESSONS_REMEDY], TIGHT),
    ("budget: a SEV_ALARM finding is printed first and in full",
     {"noisy": "alarm"},
     ["[ops-health] OPS.md routing targets missing: 50-coach.md"], []),
    # known-FALSE control for the tail itself: with nothing dropped there must
    # be no tail at all. A tail that always prints is not an indicator.
    ("budget: nothing dropped -> no tail (known-FALSE control)",
     {"target": "missing"}, ["interop:"], [TAIL, "--all"]),
]


def budget_extra_checks():
    """Assertions that need more than substring presence.

    Ordering is positional, and --all needs a different invocation -- neither
    fits the (want, avoid) table above.
    """
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp, noisy=True)

        # (a) with room to spare: every finding renders, no tail at all.
        rc, out = run(home, cwd)
        segs = out.split(" | ")
        errs = []
        if rc != 0:
            errs.append(f"exit {rc}")
        if len(segs) != 6:
            errs.append(f"expected all 6 findings, got {len(segs)} segments")
        if TAIL in out:
            errs.append("a tail was printed although everything fit")
        results.append(("budget: unsqueezed, all six findings render with no "
                        "tail", errs))

        # (b) squeezed: what disappears is a whole BAND, named in the tail --
        # never a finding chosen by its rank. The 2026-08-27 property (the
        # crowded-out dict breach must still be NAMED) is asserted here.
        rc, out = run(home, cwd, env_extra=TIGHT)
        segs = out.split(" | ")
        errs = []
        if rc != 0:
            errs.append(f"exit {rc}")
        if TAIL not in segs[-1]:
            errs.append("the tail is not the last segment")
        if any(LESSONS_REMEDY in s for s in segs[:-1]):
            errs.append("a SEV_QUEUE finding was printed in full while a "
                        "SEV_BREACH one was collapsed")
        if LESSONS_COUNT not in segs[-1]:
            errs.append("the collapsed queue band is not named in the tail")
        if not any(DICT_REMEDY in s for s in segs[:-1]):
            errs.append("the top band did not render; at least one band must "
                        "always survive the ceiling")
        results.append(("budget: squeezed, whole bands collapse and are named",
                        errs))

        rc, out = run(home, cwd, args=("--all",))
        errs = []
        if rc != 0:
            errs.append(f"exit {rc}")
        lines = out.splitlines()
        if len(lines) != 7:
            errs.append(f"--all printed {len(lines)} lines, want 1 header + 6")
        for token in ("[breach]", "[queue]", "skill-trigger-dict.md",
                      DICT_REMEDY, LESSONS_REMEDY):
            if token not in out:
                errs.append(f"--all is missing {token!r}")
        # len check, not truthiness: a hook without --all prints one truncated
        # line and lines[1] raised IndexError instead of reporting a failure.
        if len(lines) > 1 and "[queue]" in lines[1]:
            errs.append("--all is not severity-ordered")
        results.append(("budget: --all prints every finding with its band and "
                        "remedy", errs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


MIRROR = "session-transcript mirror"


def check15_remedy_cases():
    """Check 15's remedy branch — which sentence follows the finding.

    Untested until 2026-09-06, and it was keyed on substrings of a sentence
    the watchdog owns: the arm that recognised a links finding matched the
    literal "broken links", so the day gs_watchdog reworded it to
    "3 live-surface broken link(s)" the branch would have silently offered
    "regenerate the MOC" for a harvest. It now reads `remedy_kind` from the
    status payload; case 4 is that regression, run against the FALLBACK arm.

    2026-09-09: reading the kind is not enough if a kind has no branch. `build`
    had none and fell through to the harvest remedy, sending the reader to an
    integrity report the failed build never regenerated. Cases 5-6 pin every
    kind gs_watchdog.evaluate() can set to its own remedy, on both arms.
    """
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        wd = os.path.join(cwd, "tools", "graph-snapshot", "out",
                          "watchdog-status.json")

        def case(name, payload, want, avoid):
            with open(wd, "w") as f:
                json.dump(payload, f)
            os.utime(wd, (NOW, NOW))
            rc, out = run(home, cwd)
            errs = []
            if rc != 0:
                errs.append(f"exit {rc}, must always be 0")
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            results.append((name, errs))

        case("15 remedy_kind=regenerate -> emit-moc, not harvest",
             {"finding": "MOC lags the graph: 3 references/_moc file(s) would "
                         "change — run gsnap.py emit-moc",
              "remedy_kind": "regenerate"},
             ["emit-moc"], ["harvest due"])
        case("15 remedy_kind=harvest -> integrity report, not emit-moc",
             {"finding": "2 live-surface broken link(s)",
              "remedy_kind": "harvest"},
             ["harvest due", "integrity-report.md"], ["regenerate:"])
        case("15 old payload, MOC-only finding -> fallback picks regenerate",
             {"finding": "MOC lags the graph: 3 references/_moc file(s) would "
                         "change — run gsnap.py emit-moc"},
             ["emit-moc"], ["harvest due"])
        case("15 old payload, NEW links wording -> fallback still picks harvest",
             {"finding": "MOC lags the graph: 1 references/_moc file(s) would "
                         "change — run gsnap.py emit-moc; 3 live-surface "
                         "broken link(s)"},
             ["harvest due"], [])
        # Cases 5-6, 2026-09-09: `build` is a kind gs_watchdog.evaluate() can
        # set and check 15 had no branch for, so it took the else and offered
        # the integrity report — which a failed build did not regenerate. Both
        # fail against the pre-fix hook, which is what says they measure the
        # branch and not the wording.
        case("15 remedy_kind=build -> rebuild, not the stale integrity report",
             {"finding": "watchdog build FAILED (steps {'baseline': 0, "
                         "'build': 1, 'verify': 1}) — the graph, not the "
                         "corpus, needs attention first",
              "remedy_kind": "build"},
             ["rebuild first", "gsnap.py baseline", "zero-touch"],
             ["harvest due", "integrity-report.md", "emit-moc"])
        case("15 unknown kind -> says so, instead of a plausible wrong remedy",
             {"finding": "watchdog reported something new",
              "remedy_kind": "vacuum"},
             ["no remedy for remedy_kind", "'vacuum'",
              "watchdog reported something new"],
             ["harvest due", "emit-moc", "rebuild first"])
        case("15 old payload, build FAILED -> fallback picks rebuild too",
             {"finding": "watchdog build FAILED (steps {'baseline': 0, "
                         "'build': 1, 'verify': 1}) — the graph, not the "
                         "corpus, needs attention first"},
             ["rebuild first"], ["harvest due", "emit-moc"])
        case("15 no finding -> check 15 silent (known-FALSE)",
             {"finding": None}, [], ["graph rot watchdog:"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check15_graded_cases():
    """Graded watchdog status (user ruling 2026-09-23): the grade sets the HMI
    state. Severity was LOWERED for one shape (a MOC lag past its window: fail
    -> warn) and REMOVED for another (a lag inside it: no finding), so the
    regression half -- a defect still reads fail -- matters as much as the new
    half. Each case asserts the graph-watchdog point's STATE in `--json`, the
    value the change moves, and the remedy text on the text transport.
    """
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        wd = os.path.join(cwd, "tools", "graph-snapshot", "out",
                          "watchdog-status.json")
        overdue = {"text": "MOC lags the graph: 3 references/_moc file(s) "
                           "would change, oldest unregenerated commit 30h old",
                   "grade": "overdue", "remedy_kind": "regenerate"}
        links = {"text": "2 live-surface broken link(s)", "grade": "defect",
                 "remedy_kind": "harvest"}

        def case(name, graded, want_state, want, avoid, extra=None):
            payload = {"graded": graded,
                       "finding": "; ".join(g["text"] for g in graded) or None}
            payload.update(extra or {})
            with open(wd, "w") as f:
                json.dump(payload, f)
            os.utime(wd, (NOW, NOW))
            errs = []
            _rc, out = run(home, cwd)
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            _rc, js = run(home, cwd, args=("--json",))
            try:
                pts = {p["id"]: p for p in json.loads(js)["points"]}
                got = pts["ops-health.graph-watchdog"]["state"]
                if got != want_state:
                    errs.append(f"graph-watchdog state {got!r}, want {want_state!r}")
            except (ValueError, KeyError) as exc:
                errs.append(f"--json unreadable: {exc}")
            results.append((name, errs))

        case("15-graded overdue MOC lag -> breach, point warn (not fail)",
             [overdue], "warn", ["MOC lags the graph", "moc_regen.py --commit"],
             ["harvest due"])
        case("15-graded pending MOC lag -> no finding, point pass",
             [], "pass", [], ["graph rot watchdog:"],
             extra={"moc_state": "pending",
                    "moc_note": "MOC pending: 3 references/_moc file(s)"})
        # Regression half: a defect must still read fail, alone or beside an
        # overdue lag (the warn must not dilute it, the fail must not absorb it).
        case("15-graded defect (broken links) -> alarm, point fail (regression)",
             [links], "fail", ["harvest due"], [])
        case("15-graded defect + overdue -> fail, both named",
             [links, overdue], "fail", ["harvest due", "moc_regen.py --commit"], [])
        case("15-graded MOC absent -> defect, point fail",
             [{"text": "MOC absent: 8 references/_moc file(s) missing",
               "grade": "defect", "remedy_kind": "regenerate"}],
             "fail", ["MOC absent", "moc_regen.py --commit"], [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def _stamp(offset_s):
    """A run-record timestamp `offset_s` seconds ago, in the hook's format."""
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(NOW + offset_s))


def check15_run_cases():
    """Check 15's run-record arm — does the surface say a run did not finish?

    The defect it closes, measured 2026-09-09: watchdog-status.json is a COPY
    of "what the last run found", written after the work. The daily task was
    killed mid-run (0xC000013A); the copy kept the previous day's all-clear and
    check 15 reported nothing. Nothing on the machine could tell "ran and was
    fine" from "did not finish".

    The primary test is the record's pid, not its age: a dead pid under a
    `started` record is an unfinished run with no waiting period. DEAD_PID
    below is the fixture for that, and the live end-to-end proof that the
    record survives a real kill is tools/graph-snapshot/tests/
    live_run_record_control.py -- this file only proves the hook reads one.

    RUNG 1 (rules/verification-ladder.md): the domain is finite and these cases
    ARE the enumeration of it -- `state` x pid liveness x inside/outside the
    limit, every reachable cell, both verdicts:

        started + dead pid    + over limit   -> fires
        started + dead pid    + inside       -> fires   (liveness needs no wait)
        started + no pid      + over limit   -> fires   (the backstop)
        started + no pid      + inside       -> silent
        started + live pid    + inside       -> silent
        started + live pid    + over limit   -> silent  (we can see it running)
        crashed                              -> fires
        finished                             -> silent
        record absent (status clean / rot)   -> silent / old arm unchanged

    Calibrated in both directions, because a guard that has never fired is not
    known to be measuring and one that always fires measures nothing either.
    The last cell is the instrument check: it proves the new arm did not
    swallow the old one.
    """
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        rec = _run_record(cwd)
        wd = os.path.join(cwd, "tools", "graph-snapshot", "out",
                          "watchdog-status.json")
        healthy = {"finding": None, "ran_at": "2026-09-09T12:30:26"}

        def case(name, record, want, avoid, status=None):
            with open(wd, "w") as f:
                json.dump(status or healthy, f)
            os.utime(wd, (NOW, NOW))
            if record is None:
                if os.path.exists(rec):
                    os.remove(rec)
            else:
                with open(rec, "w") as f:
                    json.dump(record, f)
            rc, out = run(home, cwd)
            errs = []
            if rc != 0:
                errs.append(f"exit {rc}, must always be 0")
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            results.append((name, errs))

        killed = {"started_at": _stamp(-7200), "state": "started",
                  "pid": DEAD_PID,
                  "carrier": "graph-watchdog-task",
                  "finished_at": None, "exit": None, "error": None}

        # --- known-TRUE: the surface must say the run did not finish --------
        case("15-run killed 2 h ago -> 'did not finish' (known-TRUE)",
             killed,
             ["did not finish", "never came back", "EARLIER run",
              "LastTaskResult"], [])
        case("15-run killed 1 min ago, pid dead -> fires at once, no waiting "
             "period (known-TRUE)",
             {**killed, "started_at": _stamp(-60)},
             ["did not finish"], [])
        case("15-run no pid in the record -> the ExecutionTimeLimit backstop "
             "carries it (known-TRUE)",
             {k: v for k, v in killed.items() if k != "pid"},
             ["did not finish"], [])
        case("15-run crashed record -> names the exception (known-TRUE)",
             {**killed, "state": "crashed", "started_at": _stamp(-300),
              "finished_at": _stamp(-290), "exit": 1,
              "error": "TimeoutExpired: gsnap.py build"},
             ["did not finish", "crashed", "TimeoutExpired"], [])
        case("15-run unfinished OVER a reporting status -> one line, and it "
             "is the unfinished one (known-TRUE)",
             killed,
             ["did not finish"], ["harvest due"],
             status={"finding": "3 live-surface broken link(s)",
                     "remedy_kind": "harvest",
                     "ran_at": "2026-09-08T23:52:15"})

        # --- known-FALSE: a normal run, and an in-flight one, stay silent ---
        case("15-run finished record -> check 15 silent (known-FALSE)",
             {**killed, "state": "finished", "finished_at": _stamp(-7190),
              "exit": 0},
             [], ["graph rot watchdog"])
        case("15-run really in flight (this test's own live pid) -> silent "
             "(known-FALSE)",
             {**killed, "started_at": _stamp(-60), "pid": os.getpid()},
             [], ["graph rot watchdog"])
        case("15-run no pid but INSIDE the limit -> silent; the backstop is a "
             "deadline, not a default verdict (known-FALSE)",
             {k: v for k, v in killed.items() if k != "pid"} | {
                 "started_at": _stamp(-60)},
             [], ["graph rot watchdog"])
        case("15-run live pid PAST the 30 min limit -> still silent; the "
             "backstop must not overrule a process we can see (known-FALSE)",
             {**killed, "pid": os.getpid()},
             [], ["graph rot watchdog"])
        case("15-run record absent -> silent, an older carrier (known-FALSE)",
             None, [], ["graph rot watchdog"])
        case("15-run record absent, status REPORTING -> the original arm "
             "still fires (instrument check)",
             None, ["3 live-surface broken link(s)", "harvest due"],
             ["did not finish"],
             status={"finding": "3 live-surface broken link(s)",
                     "remedy_kind": "harvest",
                     "ran_at": "2026-09-08T23:52:15"})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check17_cases():
    """Check 17 (mirror heartbeat) — three known-TRUE, two known-FALSE.

    The marker path travels via OPS_NUDGE_MIRROR_MARKER (the hook's declared
    test seam), so no case touches the real archive. cwd == home throughout:
    the check is is_home-scoped like 14/15.
    """
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)

        def case(name, marker_path, want, avoid):
            rc, out = run(home, cwd,
                          env_extra={"OPS_NUDGE_MIRROR_MARKER": marker_path})
            errs = []
            if rc != 0:
                errs.append(f"exit {rc}, must always be 0")
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            results.append((name, errs))

        arch = os.path.join(tmp, "fake-archive", "_mirror-logs")
        os.makedirs(arch)
        marker = os.path.join(arch, "last-run-status.txt")

        # known-TRUE 1: FAIL marker fires regardless of age
        with open(marker, "w", encoding="utf-8") as f:
            f.write("FAIL  2026-09-01 13:00:00  robocopy exit=16\n")
        case("17 FAIL marker -> fires", marker,
             [MIRROR + " FAILED", "cleanupPeriodDays"], [])

        # known-TRUE 2: OK marker but stale mtime
        with open(marker, "w", encoding="utf-8") as f:
            f.write("OK  old run\n")
        old = time.time() - 5 * 86400
        os.utime(marker, (old, old))
        # SHARE EDITION: the source asserted the carrier's scheduled-task name
        # here. That name is a private literal (and the shipped hook words the
        # sentence without it), so the case asserts that the message names a
        # task at all; the staleness itself is asserted by the " silent" half.
        case("17 stale OK marker -> fires", marker,
             [MIRROR + " silent", "task"], [])

        # known-TRUE 3: archive root exists, marker missing (never ran)
        case("17 marker missing in an existing root -> fires",
             os.path.join(arch, "no-such-marker.txt"),
             [MIRROR + " marker missing"], [])

        # known-FALSE 1: fresh OK marker is silent
        with open(marker, "w", encoding="utf-8") as f:
            f.write("OK  fresh run\n")
        case("17 fresh OK marker -> silent (known-FALSE)", marker, [], [MIRROR])

        # known-FALSE 2: host without the archive root at all is silent
        case("17 archive root absent -> silent (host-normal, known-FALSE)",
             os.path.join(tmp, "no-such-drive", "_mirror-logs", "m.txt"),
             [], [MIRROR])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check5_desc_cases():
    """Check 5 measures the description AS DELIVERED (2026-09-19). Regression
    for both directions the raw-capture version got wrong: a one-line
    description measured 0 (audience-fit 1039 / ux-walkthrough 1106 never
    reported), and a folded block counted its own indentation (skill-co-upgrade
    813 raw vs 788 real, a false breach)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ohn", HOOK)
    ohn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ohn)
    cap = ohn.DESC_CAP
    words = ("word " * 400)
    one_line = "---\nname: a\ndescription: " + words[:cap + 50].strip() + "\n---\n"
    body = words[:cap - 10].strip()
    wrapped = "\n".join("  " + body[i:i + 70] for i in range(0, len(body), 70))
    folded_under = "---\nname: b\ndescription: >-\n" + wrapped + "\n---\n"
    body_over = words[:cap + 50].strip()
    folded_over = ("---\nname: c\ndescription: >-\n"
                   + "\n".join("  " + body_over[i:i + 70]
                               for i in range(0, len(body_over), 70)) + "\n---\n")
    quoted = '---\nname: d\ndescription: "' + "x" * (cap + 5) + '"\n---\n'
    out = []
    for name, text, over in (
            ("5 one-line description over cap -> fires (was measured 0)", one_line, True),
            ("5 folded block under cap -> silent (was a false breach)", folded_under, False),
            ("5 folded block over cap -> fires", folded_over, True),
            ("5 quoted one-line over cap -> fires", quoted, True)):
        n = len(ohn.description_value(text) or "")
        errs = [] if (n > cap) == over else [f"measured {n} chars vs cap {cap}"]
        out.append((name, errs))
    return out


BUNDLE = "off-disk bundle of ~/.claude"


def _case_runner(results, home, cwd):
    def case(name, env_extra, want, avoid):
        rc, out = run(home, cwd, env_extra=env_extra)
        errs = [] if rc == 0 else [f"exit {rc}, must always be 0"]
        errs += [f"missing {s!r}" for s in want if s not in out]
        errs += [f"unexpected {s!r}" for s in avoid if s in out]
        results.append((name, errs))
    return case


def check19_cases():
    """Check 19 (home-bundle heartbeat) — four known-TRUE, two known-FALSE."""
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        os.makedirs(os.path.join(cwd, "tools", "home-bundle"))
        dest = os.path.join(tmp, "disk", "_claude-home-bundles")
        os.makedirs(dest)
        status = os.path.join(dest, "last-run-status.json")
        case = _case_runner(results, home, cwd)
        env = {"OPS_NUDGE_BUNDLE_STATUS": status}

        def rec(**kw):
            with open(status, "w", encoding="utf-8") as f:
                json.dump(kw, f)

        case("19 record missing in an existing dest -> fires", env,
             [BUNDLE + " has never recorded"], [])
        rec(status="FAIL", error="git bundle create -> exit 128")
        case("19 FAIL record -> fires", env, [BUNDLE + " FAILED", "exit 128"], [])
        rec(status="OK", drill={"ok": False, "line": "DRILL FAIL: x"})
        case("19 failed drill -> fires", env, ["did not restore"], [])
        rec(status="OK", drill={"ok": True})
        old = time.time() - 5 * 86400
        os.utime(status, (old, old))
        # SHARE EDITION: as in case 17 -- the scheduled-task name is private.
        case("19 stale OK record -> fires", env,
             [BUNDLE + " silent", "task"], [])
        rec(status="OK", drill={"ok": True})
        case("19 fresh OK record -> silent (known-FALSE)", env, [], [BUNDLE])
        case("19 backup disk absent -> silent (host-normal, known-FALSE)",
             {"OPS_NUDGE_BUNDLE_STATUS":
              os.path.join(tmp, "no-drive", "b", "s.json")}, [], [BUNDLE])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check16_record_cases():
    """Check 16's feature-delta arm (2026-09-27): one known-FALSE (the shared
    fixture names an existing record) and two known-TRUE."""
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        cc = os.path.join(home, ".claude")
        case = _case_runner(results, home, cwd)
        case("16-record existing record -> silent (known-FALSE)", {}, [],
             ["feature-delta record"])
        os.remove(os.path.join(cc, "reports", "cc-upgrade-delta", "fixture.md"))
        case("16-record named record missing -> fires", {},
             ["names no existing feature-delta record"], [])
        with open(os.path.join(cc, "ops", "cc-reconciled.json"), "w") as f:
            json.dump({"reconciled_version": "0.0.0",
                       "binary_size": 0, "binary_mtime": 0}, f)
        case("16-record stamp without the field -> fires", {},
             ["names no existing feature-delta record"], [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check20_cases():
    """Check 20 (vault junctions) — three known-TRUE, one known-FALSE, built
    from a real junction to a real, then deleted, directory."""
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        vault = os.path.join(tmp, "vault")
        target = os.path.join(tmp, "wing-target")
        os.makedirs(vault)
        os.makedirs(target)
        with open(os.path.join(vault, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("| Area | Owner | Gate | How |\n|---|---|---|---|\n"
                    "| `wing/` | elsewhere | - | NTFS junction (wing) |\n"
                    "| `notes/` | here | - | native |\n")
        os.makedirs(os.path.join(vault, "notes"))
        link = os.path.join(vault, "wing")
        r = subprocess.run(["cmd", "/c", "mklink", "/J", link, target],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return [("20 fixture junction could not be created", [r.stderr])]
        case = _case_runner(results, home, cwd)
        env = {"OPS_NUDGE_VAULT_ROOT": vault}
        case("20 declared junction resolves -> silent (known-FALSE)", env, [],
             ["vault junction"])
        os.rmdir(target)
        case("20 junction to a deleted dir -> fires", env,
             ["vault junction", "wing/ junction target does not resolve"], [])
        os.makedirs(target)
        subprocess.run(["cmd", "/c", "mklink", "/J",
                        os.path.join(vault, "extra"), target],
                       capture_output=True)
        case("20 undeclared junction -> fires", env,
             ["extra/ is a junction the AGENTS.md area table does not declare"], [])
        os.rmdir(os.path.join(vault, "extra"))  # removes the link, not the target
        os.rmdir(link)
        case("20 declared junction missing -> fires", env,
             ["wing/ declared a junction but is missing"], [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check21_cases():
    """Check 21 (line endings vs .gitattributes) — one known-FALSE (every file
    holds the pinned ending), two known-TRUE (whole-file drift -> breach; mixed
    endings inside one file -> alarm), all on a real repo the fixture commits."""
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp, stale_work="clean")
        cc = cwd
        case = _case_runner(results, home, cwd)

        def pin(eol):
            # default text mode: the attributes file itself takes the platform ending,
            # which under eol=crlf on Windows is the pinned one
            with open(os.path.join(cc, ".gitattributes"), "w") as f:
                f.write(f"* text=auto eol={eol}\n")

        def commit(name, data):
            with open(os.path.join(cc, name), "wb") as f:
                f.write(data)
            git(cc, "-c", "core.autocrlf=false", "add", "-A")
            git(cc, "-c", "core.autocrlf=false", "commit", "-q", "-m", "eol fixture")

        # build() writes its stubs in text mode, so on Windows they are CRLF: pin crlf
        # and the whole fixture conforms (the known-FALSE must be a tree that really holds
        # the pinned ending everywhere, not one the check happens not to read).
        pin("crlf")
        commit("crlf.md", b"a\r\nb\r\n")
        case("21 every file holds the pinned ending -> silent (known-FALSE)", None, [],
             ["hold the other line ending", "mixed line endings"])
        commit("lf2.md", b"a\nb\n")
        case("21 whole-file drift from the pinned ending -> breach", None,
             ["hold the other line ending than .gitattributes pins", "eol_sync.py --all", "--wiring"],
             ["mixed line endings"])
        commit("mixed.md", b"a\r\nb\n")
        case("21 mixed endings inside one file -> alarm", None,
             ["mixed line endings inside 1 tracked file(s): mixed.md"], [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


OPEN_MSG = "advisory output(s) still OPEN"
UNSTAMPED_MSG = "advisory output(s) born without a status line"


def hmi_json_cases():
    """`--json` (hmi-report/1 emitter, tools/system-hmi/PROTOCOL.md) — two-sided.

    Known-TRUE: at home every home-only point RAN; a broken mirror marker lands
    as a finding under ITS point and nowhere else. Known-FALSE: away from home
    the home-only points must read ran:false / state:null (a skipped check may
    never read as a pass -- the whole reason the emitter exists), and the text
    transport must be unaffected by the emitter's presence.
    """
    results = []
    home_only = {"ops-health." + s for s in (
        "stale-uncommitted-work", "untracked-pointers", "graph-watchdog",
        "transcript-mirror", "copy-census", "home-bundle", "vault-junctions")}

    def doc(home, cwd, env_extra=None):
        rc, out = run(home, cwd, args=("--json",), env_extra=env_extra)
        try:
            return rc, json.loads(out), None
        except ValueError as exc:
            return rc, None, f"stdout is not one JSON document: {exc}"

    tmp = tempfile.mkdtemp()
    try:
        home, cc = build(tmp)
        rc, d, err = doc(home, cc)
        errs = [err] if err else []
        if d:
            pts = {p["id"]: p for p in d["points"]}
            if rc != 0:
                errs.append(f"exit {rc}, must be 0 whenever a document was produced")
            if d.get("protocol") != "hmi-report/1":
                errs.append(f"protocol {d.get('protocol')!r}")
            if len(pts) != 20:
                errs.append(f"{len(pts)} declared points, expected 20")
            errs += [f"{i} did not run at home" for i in sorted(home_only)
                     if i in pts and not pts[i]["ran"]]
            errs += [f"{i}: ran:false but state {p['state']!r}"
                     for i, p in pts.items() if not p["ran"] and p["state"] is not None]
            gate = pts.get("ops-health.relaxation-gate", {})
            if gate.get("ran") or gate.get("skip_reason") != "cwd-is-home":
                errs.append("relaxation-gate must be skipped (cwd-is-home) at home")
        results.append(("hmi-json at home: 20 points, home-only ones ran", errs))

        bad = {"OPS_NUDGE_MIRROR_MARKER": os.path.join(tmp, "no-such-marker.txt")}
        rc, d, err = doc(home, cc, env_extra=bad)
        errs = [err] if err else []
        if d:
            pts = {p["id"]: p for p in d["points"]}
            mirror = pts.get("ops-health.transcript-mirror", {})
            if mirror.get("state") != "fail" or not mirror.get("findings"):
                errs.append(f"missing marker must fail ITS point, got {mirror.get('state')!r}")
            strays = [i for i, p in pts.items() if i != "ops-health.transcript-mirror"
                      and any("mirror" in f["text"].lower() for f in p["findings"])]
            if strays:
                errs.append(f"mirror finding filed under {strays}")
            if any(p.get("undeclared") for p in d["points"]):
                errs.append("a finding reached the document with no declared owner")
        results.append(("hmi-json: a finding lands under its own point", errs))

        _rc, text_plain = run(home, cc, args=("--all",), env_extra=bad)
        errs = [] if "mirror" in text_plain.lower() else ["--all lost the mirror finding"]
        if text_plain.lstrip().startswith("{"):
            errs.append("--all printed JSON")
        results.append(("hmi-json: --all text transport unaffected", errs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tmp = tempfile.mkdtemp()
    try:
        home, pdir = build(tmp, proj="# project\nops-relaxation: L1\n")
        rc, d, err = doc(home, pdir)
        errs = [err] if err else []
        if d:
            pts = {p["id"]: p for p in d["points"]}
            for i in sorted(home_only):
                p = pts.get(i, {})
                if p.get("ran") or p.get("state") is not None \
                        or p.get("skip_reason") != "cwd-not-home":
                    errs.append(f"{i}: away from home must be ran:false/"
                                f"state:null/cwd-not-home, got {p.get('ran')}/"
                                f"{p.get('state')}/{p.get('skip_reason')}")
            if not pts.get("ops-health.relaxation-gate", {}).get("ran"):
                errs.append("relaxation-gate must RUN away from home")
        results.append(("hmi-json away from home: skipped is never pass", errs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def check13_cases():
    """Check 13's status parse — the class closure over an advisory status line.

    The hook rules only on what it can determine: a line carrying a spent
    keyword (SPENT / 已執行 / 否決 / 已裁) silences the file; a file with NO
    status line is its own `unstamped` finding; and a line that is present but
    carries none of the keywords is one the parse cannot rule on, so it
    surfaces as OPEN and routes the reader to that one file.

    Every case runs with exactly one artifact in outputs/, so a finding can
    only have come from the file the case planted.
    """
    results = []
    tmp = tempfile.mkdtemp()
    try:
        home, cwd = build(tmp)
        outdir = os.path.join(cwd, "outputs", "retrospectives")
        os.makedirs(outdir)

        def case(name, basename, body, want, avoid):
            for old in os.listdir(outdir):
                os.remove(os.path.join(outdir, old))
            with open(os.path.join(outdir, basename), "w",
                      encoding="utf-8") as f:
                f.write(body)
            rc, out = run(home, cwd)
            errs = []
            if rc != 0:
                errs.append(f"exit {rc}, must always be 0")
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            results.append((name, errs))

        # AP-62 specimen. "> status: pending" carries none of the spent
        # keywords, so the parse cannot rule on whether this artifact was acted
        # on. The declared handling is to surface it as OPEN with a remedy of
        # reading the one named file -- never to fold it into the silence that
        # a spent keyword buys.
        case("13 undetermined status (a line with no declared keyword) -> "
             "surfaces OPEN, never folded into silence",
             "global-rule-candidates-2026-09-01.md",
             "> status: pending, nobody has ruled on this yet\n\n# candidates\n",
             [OPEN_MSG, "global-rule-candidates-2026-09-01.md",
              "read its status line"],
             [UNSTAMPED_MSG])

        # The other half of the closure: an artifact with no status line at all
        # cannot be placed in either substantive class, and it gets its OWN
        # finding with its own remedy. Folding it into OPEN is the failure the
        # `avoid` here pins -- the count would stay plausible and the remedy
        # ("read its status line") would name a line that does not exist.
        case("13 no status line at all -> its own unstamped class, excluded "
             "from the OPEN list",
             "global-rule-candidates-2026-09-02.md",
             "# candidates\n\n- one offer nobody stamped\n",
             [UNSTAMPED_MSG, "global-rule-candidates-2026-09-02.md",
              "add `> status:"],
             [OPEN_MSG])

        case("13 a clearly spent status -> silent (known-FALSE)",
             "global-rule-candidates-2026-09-03.md",
             "> status: SPENT — folded into CLAUDE.md on 2026-09-04\n",
             [], [OPEN_MSG, UNSTAMPED_MSG])

        case("13 unstamped but born before the convention -> exempt, silent "
             "(known-FALSE; no backfill alarm)",
             "global-rule-candidates-2026-08-01.md",
             "# candidates\n\n- predates rules-usage-dict.md S7\n",
             [], [OPEN_MSG, UNSTAMPED_MSG])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return results



def check13_scope_cases():
    """Check 13's two scopes — who MAY be polled vs who OWES a stamp.

    Widened 2026-09-10 after a deferred-extraction record filed outside the two
    owed globs proved invisible. The asymmetry is the design: any self-stamped
    file under outputs/ may be polled (it opts in by carrying the line), while
    only the candidates and experiment-metrics classes are OBLIGED to carry one.
    Each case plants files at explicit relative paths, so a finding can only
    have come from what the case planted.
    """
    results = []

    def case(name, files, want, avoid):
        tmp = tempfile.mkdtemp()
        try:
            home, cwd = build(tmp)
            for rel, body in files.items():
                dst = os.path.join(cwd, *rel.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "w", encoding="utf-8") as f:
                    f.write(body)
            rc, out = run(home, cwd)
            errs = []
            if rc != 0:
                errs.append(f"exit {rc}, must always be 0")
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            results.append((name, errs))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # The motivating case: this file is nowhere near the two owed globs, and
    # before the widening nothing polled it.
    case("13-scope a self-stamped waiting file outside the owed globs -> "
         "polled (known-TRUE; the case the widening was built for)",
         {"outputs/numberref-extraction-deferred-2026-09-10.md":
          "> status: deferred-pending-second-customer — judged, not built\n"},
         [OPEN_MSG, "numberref-extraction-deferred-2026-09-10.md"],
         [UNSTAMPED_MSG])

    # The other half: opting in is what the stamp DOES. No stamp, no
    # obligation — outside the owed classes an unstamped file is not a finding.
    case("13-scope an UNstamped file outside the owed globs -> silent; only "
         "the owed classes owe a stamp (known-FALSE)",
         {"outputs/some-measurement-2026-09-10.md": "# just a record\n"},
         [], [OPEN_MSG, UNSTAMPED_MSG])

    case("13-scope skill-reviews keeps its own disposition convention -> never "
         "double-governed, even when stamped waiting (known-FALSE)",
         {"outputs/skill-reviews/audience-fit-gaps-2026-09-10.md":
          "> status: OPEN — disposition pending\n"},
         [], [OPEN_MSG, UNSTAMPED_MSG])

    # An archive of N identical residuals is ONE standing item. Listing it N
    # times is how a screen becomes the alarm nobody reads: the real corpus had
    # 23 such reports against 4 genuine offers.
    case("13-scope identical status text in one directory -> ONE row with a "
         "count, never N rows (known-TRUE)",
         {f"outputs/trigger-probe/report-2026-09-0{i}.md":
          "> status: OPEN — trigger-probe run; residual: unconsumed failures\n"
          for i in (1, 2, 3)},
         [OPEN_MSG, "outputs/trigger-probe/ x3"],
         ["report-2026-09-01.md", "report-2026-09-02.md"])

    # The class the parse CANNOT close must not vanish with the class it can:
    # before this was fixed the count rode inside the OPEN message, so a run
    # with only unruleable stamps reported nothing at all.
    case("13-scope only an unruleable stamp present -> still reported as a "
         "count, not silenced (known-TRUE; regression guard)",
         {"outputs/odd-2026-09-10.md": "> status: 量測紀錄 | consumer: user\n"},
         ["could not be ruled on", "rules-usage-dict.md S7"],
         [OPEN_MSG])

    return results


DEFERRED_MSG = "deliberately DEFERRED with a named trigger"


def check13_deferral_cases():
    """T-024 (2026-09-22): a trigger-named deferral reads queue/warn, not loss.

    Severity was LOWERED for one shape, so the regression half matters as much
    as the new half: an OPEN stamp, a lower-case "deferred" and a DEFERRED
    without a trigger must all still read loss -> HMI fail. Each case asserts
    on the point's STATE in `--json`, which is the value the change moves.
    """
    results = []

    def case(name, files, want_state, want, avoid, want_trigger=None):
        """want_trigger (2026-09-23, the hmi-report/1 `deferred` claim): a
        string = the point must carry `deferred` whose trigger is exactly
        that; False = it must carry none. The asserted value is the trigger
        text itself, which the defect (a claim on a mixed point, or a lost
        trigger) would change."""
        tmp = tempfile.mkdtemp()
        try:
            home, cwd = build(tmp)
            for rel, body in files.items():
                dst = os.path.join(cwd, *rel.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "w", encoding="utf-8") as f:
                    f.write(body)
            errs = []
            _rc, out = run(home, cwd)
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            _rc, js = run(home, cwd, args=("--json",))
            try:
                pts = {p["id"]: p for p in json.loads(js)["points"]}
                got = pts["ops-health.advisory-outputs"]["state"]
                if got != want_state:
                    errs.append(f"advisory-outputs state {got!r}, want {want_state!r}")
                if want_trigger is not None:
                    dfr = pts["ops-health.advisory-outputs"].get("deferred")
                    got_t = dfr["trigger"] if dfr else False
                    if got_t != want_trigger:
                        errs.append(f"deferred trigger {got_t!r}, want {want_trigger!r}")
            except (ValueError, KeyError) as exc:
                errs.append(f"--json unreadable: {exc}")
            results.append((name, errs))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    rel = "outputs/numberref-extraction-deferred-2026-09-10.md"
    case("13-defer DEFERRED + named trigger -> queue, point warn not fail "
         "(known-TRUE; the T-024 shape)",
         {rel: "> status: DEFERRED — trigger: a second project needs it\n"},
         "warn", [DEFERRED_MSG, "numberref-extraction-deferred-2026-09-10.md"],
         [OPEN_MSG], want_trigger="a second project needs it")
    case("13-defer the Chinese 狀態 spelling with a full-width colon -> same",
         {rel: "**狀態**：DEFERRED — trigger：第二個專案需要時\n"},
         "warn", [DEFERRED_MSG], [OPEN_MSG], want_trigger="第二個專案需要時")
    case("13-defer a deferral that quotes a ruling (已裁) stays visible, "
         "never silenced as spent; the trigger ends at the ';'",
         {rel: "> status: DEFERRED — trigger: second customer; 使用者已裁延後\n"},
         "warn", [DEFERRED_MSG], [OPEN_MSG], want_trigger="second customer")
    # Regression half: what the old SEV_LOSS level caught must still read fail.
    case("13-defer an OPEN stamp still reads loss -> fail (regression)",
         {rel: "> status: OPEN — offer awaiting a session\n"},
         "fail", [OPEN_MSG], [DEFERRED_MSG], want_trigger=False)
    case("13-defer DEFERRED with no trigger -> loss, fail (a deferral that "
         "names nothing is not deliberate), and no deferral claim",
         {rel: "> status: DEFERRED — later\n"},
         "fail", [OPEN_MSG], [DEFERRED_MSG], want_trigger=False)
    case("13-defer the old lower-case stamp -> loss, fail (regression)",
         {rel: "> status: deferred-pending-second-customer — judged, not built\n"},
         "fail", [OPEN_MSG], [DEFERRED_MSG])
    case("13-defer an empty trigger -> loss, fail",
         {rel: "> status: DEFERRED — trigger:  \n"},
         "fail", [OPEN_MSG], [DEFERRED_MSG])
    case("13-defer one OPEN beside one DEFERRED -> fail wins, both named, and "
         "the point carries NO deferral claim (a mixed point is not deferred)",
         {rel: "> status: DEFERRED — trigger: a second project needs it\n",
          "outputs/other-2026-09-20.md": "> status: OPEN — offer\n"},
         "fail", [OPEN_MSG, DEFERRED_MSG, "other-2026-09-20.md"], [],
         want_trigger=False)
    return results


def main():
    passed = failed = 0
    for case in (CASES + CHECK11_CASES + SHARE_CASES
                 + CHECK14_CASES + CHECK18_CASES + BUDGET_CASES):
        # 5th element (optional): env overrides for this case only.
        name, kw, want, avoid = case[:4]
        env_extra = case[4] if len(case) > 4 else None
        tmp = tempfile.mkdtemp()
        try:
            home, cwd = build(tmp, **kw)
            rc, out = run(home, cwd, env_extra=env_extra)
            errs = []
            if rc != 0:
                errs.append(f"exit {rc}, must always be 0")
            for s in want:
                if s not in out:
                    errs.append(f"missing {s!r}")
            for s in avoid:
                if s in out:
                    errs.append(f"unexpected {s!r}")
            if errs:
                failed += 1
                print(f"FAIL  {name}\n      {'; '.join(errs)}\n      out={out!r}")
            else:
                passed += 1
                print(f"pass  {name}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    for name, errs in (budget_extra_checks() + check13_cases()
                       + check13_scope_cases() + check13_deferral_cases()
                       + check15_remedy_cases() + check15_run_cases()
                       + check15_graded_cases()
                       + check17_cases() + check19_cases() + check5_desc_cases()
                       + check16_record_cases()
                       + check20_cases() + check21_cases() + hmi_json_cases()):
        if errs:
            failed += 1
            print(f"FAIL  {name}\n      {'; '.join(errs)}")
        else:
            passed += 1
            print(f"pass  {name}")
    print(f"\n{passed}/{passed + failed} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
