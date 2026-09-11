#!/usr/bin/env python3
"""SessionStart hook: ops-layer health nudge.

STATUS: LIVE since 2026-07-06 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

Prints ONE short reminder line only when a maintenance threshold trips;
completely silent when everything is healthy. Never blocks, never denies,
stdlib only, pinned to ~/.claude. Designed to close the gap where
ops/40-maintenance.md defines trim/degradation checks but nothing ever
triggers them.

Checks (all cheap, no network; ONE subprocess in the steady state -- check 14's
`git status`, scoped to cwd == ~/.claude and budgeted at 2 s. Check 16 adds a
SECOND one, but only after the claude binary's stat() fingerprint moves, which
is rare and measured at 86-102 ms. Every other check is stat() or a small
read):
  1. lesson intake report (`intake.py report --nudge`) -> route a hits>=2
     record through 40-maintenance S2a / a folded-but-recurring fix did not
     hold / a status projection drifted (replaced the LESSON_CAP entry count
     on 2026-09-07; ONE extra subprocess, 1.5 s budget, every cwd)
  2. any ops/*.md over SIZE_CAP                 -> extract pass due
     (excl. lessons.md, rule-registry.md, environment.md -- SIZE_CAP_EXEMPT)
  3. rule registry idle over TRAIL_IDLE_DAYS    -> degradation check due
  4. OPS.md routing targets missing on disk     -> ghost-rule alarm
  5. skill description over DESC_CAP            -> preload-budget breach
  6. SKILL.md body over BODY_CAP                -> move detail to references/
  7. CLAUDE.md over CLAUDE_MD_CAP               -> always-loaded budget breach
  8. skill-trigger-dict.md over DICT_CAP        -> dict review due (audit 1st)
  9. (retired 2026-08-11 -- the trail is frozen, see below)
 10. skills/ dir vs skill-trigger-dict.md drift -> dict-sync breach (40-maintenance S2)
 11. project CLAUDE.md declares no ops-relaxation level -> gate never fired
     (a DECLARATION -- `ops-relaxation: L1` -- not a prose mention; see below)
 12. interop target undeployed/foreign/behind   -> run interop.py status
 13. advisory output OPEN / born unstamped      -> read the named file
     (rules-usage-dict.md S7 "advisory-output status line"; two scopes --
     any self-stamped outputs/**.md may be polled, only the candidates and
     experiment-metrics classes OWE a stamp)
 14. stale uncommitted work in ~/.claude        -> commit it by what it touches
     (cwd == ~/.claude only; `git status --porcelain -uall`, paths whose
     mtime exceeds STALE_WORK_DAYS; report-only, never attributes)
 15. graph rot watchdog stale or reporting rot  -> run watchdog / harvest
     (cwd == ~/.claude only; reads tools/graph-snapshot/out/
     watchdog-status.json, one small JSON; report-only)
 16. installed Claude Code != the build ops/ was reconciled against
     -> run tools/cc-delta/cc_delta.py (every project, not just ~/.claude;
     stat()-gated, see the CC_STAMP block; a missing stamp is itself reported)
 17. session-transcript mirror marker FAIL, missing, or older than
     MIRROR_STALE_DAYS -> the backup task may be dead while cleanupPeriodDays
     deletion keeps running (reads MIRROR_MARKER, one small file)
NO THRESHOLD NUMBER APPEARS IN THIS DOCSTRING, and none may be added. Every
line above names the CONSTANT; the constant's assignment below is the single
site that carries the value. This is a property of the file, not a style
preference: from 2026-08-18 to 2026-08-27 these lines read "15K" for
CLAUDE_MD_CAP (really 19,968), "15K" for SIZE_CAP (really 22K) and "24K" for
DICT_CAP (really 28K) -- three silent lies inside the mechanism that is
supposed to BE the source of truth. A name cannot drift from the thing it
names; a copied number always can.

Thresholds mirror ops/40-maintenance.md S3 defaults; change them together --
INCLUDING the unit. File caps are BYTES (os.path.getsize, so CRLF counts 2);
DESC_CAP is chars; BODY_CAP is lines. Bytes because they track token cost:
bytes/token holds at 3.8-4.1 across this corpus while chars/token ranges
2.3-4.0. Two different drifts, two different checks: the UNIT is sweep check 7
(a grep), the VALUE is sweep check 7b
(`python tools/ops-health-test/check_cap_binding.py`, added 2026-08-27 after
check 7 was found to have never covered the value at all).

Message wording is load-bearing: the nudge is what reaches session context,
while S3 is two routing hops away. So each message must carry the REMEDY, not
just the number -- a bare "trim" invites the compression S3 forbids.

The printed line renders every finding that fits NUDGE_BYTE_CEILING, and when it
does not fit it collapses the lowest SEVERITY BAND whole -- a property of the
finding, never its position in a list. See the band comments below. Collapsing
is never silent: a tail names every hidden finding, and `--all` prints all of
them one per line. Before
2026-08-27 the print was a bare `msgs[:4]`; the named tail arrived then, and the
rank cutoff itself survived until 2026-09-08, by which time it had kept the same
three findings off the screen (two cap breaches and an 18-card queue) for long
enough that they were the repo's three oldest debts.

Proof-of-life: `python tools/ops-health-test/test_ops_health_nudge.py` (52/52).
"""
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~/.claude")
OPS = os.path.join(HOME, "ops")
SKILLS = os.path.join(HOME, "skills")
# RETIRED 2026-09-07: the unfolded-entry cap on ops/lessons.md (36 at retirement;
# history under rule-registry key `LESSON_CAP`). ops/lessons.md is now a
# GENERATED index of ops/lessons/ (tools/closeout-intake) and has no count cap
# (design S-7: the count was after-the-fact back-pressure that produced batch
# rewrites); the live signal is `intake.py report --nudge`, check 1 below.
INTAKE_REPORT_TIMEOUT = 1.5   # seconds; the report parses ~50 small files
SIZE_CAP = 26 * 1024   # BYTES per ops/*.md (getsize). REVIEW TRIGGER, not a
                       # budget: ops files are charged only when something
                       # routes to them, and Phase 2 measured the whole
                       # always-loaded surface at ~5% of context and cached, so
                       # bytes here buy nothing worth a hard cap. Firing means
                       # "someone should look at this file", and RAISING IT
                       # AFTER A REVIEW IS THE INTENDED OUTCOME. Provisional.
                       # 18K -> 22K on 2026-08-21 after the review it asked
                       # for: 20-dispatch.md 24.6K and environment.md 20.5K
                       # both yielded extractable concrete (3.7K and 3.9K to
                       # ops/references/), and what remained in 20-dispatch
                       # (20.9K) is rules and routing tables.
                       # 22K -> 26K on 2026-09-06, THIRD firing, user ruling.
                       # First firing whose review found real concrete AND
                       # left the file still over: environment.md 25,399 ->
                       # 24,156 lossless into its own sink, and 24,156 > cap.
                       # If environment.md fires AGAIN after a pass that moved
                       # real content, the honest answer is not a fourth raise
                       # but SIZE_CAP_EXEMPT -- see the registry entry.
                       # That is what happened: it fired 2026-09-08 after a
                       # second real extraction, and the file was EXEMPTED
                       # rather than the cap raised a fourth time. So 26K is
                       # still the trigger for every other ops file, and this
                       # comment is the record that the armed answer was taken.
                       # why/history: ops/rule-registry.md, key `ops file cap`;
                       # unit: key `cap measurement unit`. CLAUDE_MD_CAP below
                       # is deliberately NOT raised with it -- different class.
# Files whose size tracks the CORPUS, not bloat: an over-cap reading on these
# has no extract remedy, and a permanently-on alarm is one nobody reads. Their
# real degradation checks are elsewhere -- lessons.md is a generated index
# whose signal is `intake.py report` (check 1); rule-registry.md is bounded by
# the rule count and checked by 40-maintenance.md S4.1 (an entry for a rule
# nobody uses). why/history: ops/rule-registry.md, key `ops file cap`.
# environment.md joined 2026-09-08 on the condition ARMED on 2026-09-06 ("if it
# fires again after a pass that moved real content, the answer is not a fourth
# raise but SIZE_CAP_EXEMPT"), which fired the same week: two lossless passes
# moved -1,243 B and -5,572 B and left the file 3,514 B over, because what it
# holds is one fact table per SURFACE and the surface count is what grows. Its
# review trigger is not lost -- the file's own closing line re-verifies any
# block older than ~90 days, which is a property of the BLOCK where a byte
# count was a position (L-047). User authorization 2026-09-08 (named, as
# 70-evolution.md S1 invariant 1 requires); proposal + rollout + positive
# control: drafts/2026-09-08-environment-md-exempt/APPLY.md. Rollback: drop the
# name from this set (one token) -- the check then fires again, unchanged.
SIZE_CAP_EXEMPT = {"lessons.md", "rule-registry.md", "environment.md"}
TRAIL_IDLE_DAYS = 45
DESC_CAP = 800          # chars, skill frontmatter description — this is the
                        # one that costs EVERY session; keep it tight.
BODY_CAP = 300          # lines, whole SKILL.md. Charged only on invoke, not at
                        # session start. Over cap means EXTRACT to references/,
                        # never compress in place. why/history:
                        # ops/rule-registry.md
CLAUDE_MD_CAP = 23040      # BYTES (22.5 KB). why/history: ops/rule-registry.md
DICT_CAP = 49 * 1024   # BYTES. REVIEW TRIGGER, not a budget -- same class (b)
                       # reasoning as SIZE_CAP: the dict is charged only on a
                       # routing miss. Raised 20K->24K on 2026-08-15 after
                       # tools/skill-routing-audit.py showed the file's problem
                       # is CONTENT VALIDITY, not volume (0% of actual routing
                       # explained by its own registered vocabulary, except
                       # workflow-checkpoint at 21%). Extracting a file that
                       # measures as fiction would tidy the fiction. Firing
                       # means "review this dict against the audit output".
                       # Raised 24K->28K on 2026-08-17 after dict-review round
                       # 1 (trigger-probe M4 evidence pack): 3 user-ruled
                       # corrections landed (rewrite/de-generalize/remove),
                       # false matches 10->1 on the worst entry -- the review
                       # the trigger asked for happened; raising the cap after
                       # it is this rule's own stated intended outcome.
                       # Raised 28K->42K on 2026-09-04 after dict-review round
                       # 2 (outputs/dict-review-round2-2026-09-04.md): first
                       # round to move a coverage number (schedule and
                       # update-config 0% -> 100%), 3 phantom targets
                       # tombstoned, DEAD 13->8. It also checked the RULER:
                       # the audit reads only `關鍵詞：` lines and puts \b
                       # around ASCII tokens, so an entry with no keyword line
                       # -- and any ASCII token written flush against Chinese
                       # -- cannot match. Both biases understate the dict; the
                       # verdict survived both controls anyway. T-023 carries
                       # the tool fix. File 40,222 B = 93.5% of the new cap:
                       # headroom is ~2 skill sections ON PURPOSE, so the next
                       # expansion re-runs this decision.
                       # Raised 42K->49K on 2026-09-08 after dict-review round
                       # 3. This round found a defect in the VOCABULARY ITSELF,
                       # not in any one entry: 31 keyword tokens across 14
                       # entries were written as slash alternations
                       # (`把影片/圖片存下來`, `GLSL/shader`), which the matcher
                       # reads as ONE literal token, so they fired only on a
                       # turn that typed the slash too. Every MISS and coverage
                       # figure printed before this was therefore a FLOOR. The
                       # audit now DETECTS the shape (a property of the token,
                       # so a new entry written that way is caught the day it
                       # lands) and the 31 were spelled out: occurrences rose
                       # ~130, media-fetch-pipeline stopped being DEAD, and one
                       # naive expansion had to be walked back the same hour --
                       # a bare `STEP` token matched "multi-step" and added 107
                       # phantom occurrences, so the tokens are now `.step` /
                       # `STEP 檔`. Tombstones are also reported separately now:
                       # 4 of the 8 DEAD entries were deliberate, and making the
                       # reader re-adjudicate them every sweep is how a report
                       # stops being read.
                       # File 46,334 B = 92.3% of the new cap: headroom is ~2
                       # skill sections ON PURPOSE, so the next expansion
                       # re-runs this decision.
                       # AUTHORIZATION NOTE: that raise was applied BEFORE the
                       # named authorization 70-evolution.md S1 invariant 1
                       # requires for an edit to this file -- the model read
                       # "finish fixing these debts" as covering the remedy the
                       # rule itself prescribes, which it does not. Disclosed
                       # the same session and RATIFIED by the user 2026-09-08
                       # ("DICT_CAP 那筆也一併追認"), so the value stands. The
                       # sequence, not the value, was the defect: a guardrail
                       # edit is proposed in drafts/ and applied after the
                       # word, the way environment.md's exemption above was.
                       # Provisional. why/history: ops/rule-registry.md, key
                       # `routing dict cap`.
# RETIRED 2026-08-11: `Global_skill_update.md` is frozen as the historical
# event log and cannot grow, so a size cap on it can only nag. Standing rule
# rationale moved to `ops/rule-registry.md` -- which grows with the RULE count,
# not the change count, and so is SIZE_CAP_EXEMPT for that same reason
# (2026-08-13: it was in the loop until then, which is the bug that argument
# should have prevented at the time it was written).
ROUTED_FILES = [
    "OPS.md", "05-authority.md", "10-command-loop.md", "20-dispatch.md",
    "30-judgment.md", "40-maintenance.md", "50-coach.md", "60-bootstrap.md",
    "70-evolution.md", "environment.md", "rules-usage-dict.md", "lessons.md",
]
INTEROP = os.path.join(HOME, "interop")
# Files whose mtime, if NEWER than a deployed artifact, means that artifact was
# built from an older source. Mirrors the two paths interop.py's cmd_status
# passes to `git log` -- change the two together.
INTEROP_SOURCES = ("portable-core.md", "interop.py")
# Check 14. Days a dirty path in ~/.claude may sit before it is called stale.
# PROVISIONAL -- chosen from ONE day's data (2026-08-21: 17 uncommitted record
# artifacts aged 14-109 h; 72 h catches 7 of them with zero false positives on
# the same-hour in-flight peer work, 48 h catches 9, also zero FP). Age-gating
# is the load-bearing detail: without it the line fires on every legitimately
# in-flight tree and trains the reader to ignore it. Start at 3, tighten only on
# measured evidence. why/history/review-when: ops/rule-registry.md, key
# `stale uncommitted work`.
STALE_WORK_DAYS = 3
STALE_WORK_GIT_TIMEOUT = 2.0   # seconds; settings.json allows 3 s for the whole
                               # hook; measured 0.23 s on 663 tracked files.
# Check 15. Days the graph rot watchdog's status file may age before its
# carrier (the daily scheduled task) is presumed dead. PROVISIONAL, declared
# guess: the task is daily, so 3 tolerates two missed days (machine off)
# without a permanently-on alarm. why/history/review-when:
# ops/rule-registry.md, key `graph rot watchdog`.
WATCHDOG_STALE_DAYS = 3
WATCHDOG_STATUS = os.path.join(HOME, "tools", "graph-snapshot", "out",
                               "watchdog-status.json")
# Check 15, second arm (born 2026-09-09, from a measured miss). The status file
# above is a COPY of "what the last run found", written after the work; when a
# run dies the copy keeps its last plausible value and the two states "ran and
# was fine" and "did not finish" become indistinguishable. Measured: the daily
# task ran 14:49:58, was killed (0xC000013A) after gsnap.py baseline, wrote no
# log line, and this check reported the previous day's all-clear. gs_watchdog.py
# now writes watchdog-run.json BEFORE it measures; a record still reading
# `state: "started"` is a run that never came back.
# The PRIMARY test is not a threshold at all: the record carries the pid, so
# "is that process still running" is DETERMINABLE, and a dead pid under a
# `started` record is an unfinished run with no waiting period. That direction
# is the safe one -- a live process's pid cannot have been reused, so this can
# never accuse a run that is genuinely in flight; the failure it can have is
# staying quiet when a recycled pid makes a dead run look alive.
# The minutes below are the BACKSTOP for exactly that, and for any host where
# liveness cannot be read. Derived, not guessed: the task's own
# ExecutionTimeLimit is PT30M (verified on the registered task 2026-09-09, owed
# by D-27), so past 30 minutes the scheduler has already terminated it and no
# legitimate run can still be running. Under both tests the check stays silent,
# which is what keeps a run in progress (measured 25-41 s) quiet.
# review-when: your graph-watchdog task's ExecutionTimeLimit changes.
# why/history: ops/rule-registry.md, key `graph rot watchdog`.
WATCHDOG_RUN_LIMIT_MIN = 30
WATCHDOG_RUN = os.path.join(HOME, "tools", "graph-snapshot", "out",
                            "watchdog-run.json")

# Check 16. The build ops/ was last reconciled against, vs the one installed.
# The stamp also carries a stat() fingerprint of the binary, so the steady
# state costs nothing and `claude --version` (measured 86-102 ms) is spawned
# ONLY after the binary actually moved -- that keeps this file's one-subprocess
# budget intact. Never read the version from cache/changelog.md or
# .last-update-result.json: measured 2026-08-26, `claude update` refreshes
# neither, so both serve a stale number that reads as live.
# why/history/review-when: ops/rule-registry.md, key `cc version reconcile`.
CC_STAMP = os.path.join(HOME, "ops", "cc-reconciled.json")
CC_BIN = os.path.expanduser("~/.local/bin/claude.exe")

# Check 17. Days the session-transcript mirror's marker may age before its
# daily task (your session-transcript-mirror scheduled task, decisions D-033) is
# presumed dead. PROVISIONAL by the check-15 argument: daily carrier, 3
# tolerates two off days. The FAIL state fires regardless of age -- the
# mirror is the only thing between cleanupPeriodDays deletion and the
# transcripts. Run HISTORY lives beside the marker in run-ledger.tsv
# (append-only; the jsonl count may only grow under the COPY-ONLY contract).
# why/history/review-when: your own rule registry.
# The env var is the TEST SEAM (hermetic fixtures in tools/ops-health-test);
# the archive-root gate in the check makes a host without the archive silent
# by design (same absence-is-normal call as CC_BIN in check 16).
MIRROR_STALE_DAYS = 3
# SHARE EDITION: no default marker path ships here -- the source's default was
# an absolute path on a non-system drive (a private mirror root, the same
# leak class handled in transcript_read_guard.py CORPUS_ROOTS). Point
# OPS_NUDGE_MIRROR_MARKER at your own marker file; an unset/empty value's
# parent dir will not exist, so the check below stays silent by the same
# absence-is-normal rule as CC_BIN.
MIRROR_MARKER = os.environ.get("OPS_NUDGE_MIRROR_MARKER") or ""

# Check 18. copy-census (tools/copy-census, design references/copy-census-
# design.md). Its carrier is your copy-census scheduled task, so the same
# silent-when-dead argument as checks 15 and 17 applies -- and this one has a
# measured precedent: on 2026-09-09 the graph watchdog's task was killed
# mid-run, wrote no log line, and left a status file still reporting all-clear.
# 3 days tolerates two off days, by the check-15 argument. The env var is the
# TEST SEAM. why/history/review-when: ops/rule-registry.md, key `copy census`.
COPY_CENSUS_STALE_DAYS = 3
COPY_CENSUS_STATUS = (os.environ.get("OPS_NUDGE_COPY_CENSUS_STATUS")
                      or os.path.join(HOME, "tools", "copy-census", "out",
                                      "run-status.json"))


class _CopyCensusHandled(Exception):
    """Check 18 already reported this state; leave the block without falling
    through to the branches below. The outer fail-open handler absorbs it."""

# ---- output budget and severity ------------------------------------------
# The line is injected into EVERY session's context, so the number of findings
# printed is capped. The cap itself is fine; what was not is that it used to
# truncate SILENTLY (`print(" | ".join(msgs[:4]))`), so a reader could not tell
# "no dict warning" from "the dict warning was crowded out" -- and on
# 2026-08-27 skill-trigger-dict.md was measured 2.6K over DICT_CAP while four
# other checks filled the line, which is the second reading. Two properties fix
# it, and BOTH are tested (tools/ops-health-test/test_ops_health_nudge.py):
#   (1) anything dropped is COUNTED and the count is printed, with the command
#       that shows the rest;
#   (2) findings are ordered by SEVERITY first and insertion order second, so
#       what gets dropped is always the least consequential finding, never a
#       breach.
# Evidence that (1) alone is not enough: the acceptance for this change is that
# an over-cap file SURFACES when five or more checks fire, and a count cannot
# surface a message.
# What renders is a PROPERTY OF THE FINDING (its severity band), never its
# POSITION in the list. Until 2026-09-08 this was `found[:NUDGE_CAP]` with
# NUDGE_CAP = 4, and the defect is the one CLAUDE.md names as L-047: a predicate
# that is a position in an artifact that grows. Because the order is severity
# then arrival, the cutoff is DETERMINISTIC -- the same classes fall off every
# session, forever. Measured 2026-09-08 with 7 findings live: ranks 5-7 were
# `environment.md` 134% of cap, `skill-trigger-dict.md` 106% of cap, and 18
# unfolded intake cards -- which were also, independently, the three oldest
# debts in the repo. The count-and-name tail was working exactly as designed and
# still did not surface them, because a label in a tail is not a remedy.
#
# The replacement: every band renders, and collapsing is a BUDGET event, not a
# policy -- only when the rendered text exceeds NUDGE_BYTE_CEILING does the
# lowest band still shown collapse WHOLE into the named tail. So with room to
# spare nothing is hidden at all, and when there is not, what disappears is a
# CLASS the tail names rather than whoever happened to sit in fifth place. The
# printed set then shrinks as debt is paid instead of staying at four forever.
#
# Why a byte ceiling is not the same defect in another unit: it is a property of
# the rendered TEXT, and it never selects WHICH finding goes -- the band does,
# and a band is a property of the finding. Measured 2026-09-08: all seven live
# findings render in 2,073 bytes, so today the ceiling collapses nothing.
NUDGE_BYTE_CEILING = 2400
# Bands, most severe first. The axis is "if only ONE line survives, which one
# does the reader most need?" -- not the class-(a)/(b) budget distinction from
# 40-maintenance.md S3, which governs the REMEDY (already carried in each
# message's text) and not the cost of never seeing it. The check-16 comment
# below had already hand-rolled the top band with `insert(0)`; this replaces
# that with something the other 17 messages can also use.
SEV_ALARM = 0   # a mechanism is dead, or the rules being followed provably no
                # longer describe reality. Outranks everything.
SEV_LOSS = 1    # finished work is at risk or invisible: it exists, and nothing
                # else will surface it.
SEV_BREACH = 2  # a NAMED file is over a declared threshold. Bounded, one-off
                # remedy; it stops firing once done.
SEV_QUEUE = 3   # recurring counters and process reminders. They re-fire every
                # session until a work session happens, which is exactly what
                # makes them the right thing to drop when the line is full.
SEV_NAME = {SEV_ALARM: "alarm", SEV_LOSS: "loss",
            SEV_BREACH: "breach", SEV_QUEUE: "queue"}

def split_by_band(found, ceiling=None):
    """-> (shown, hidden). What collapses is a BAND, never a rank.

    `found` is `Nudges.ordered()`. Every band renders; collapsing happens only
    when the rendered text exceeds `ceiling` BYTES, and then the lowest band
    still shown collapses WHOLE and the test repeats. Two properties follow, and
    both are what the rank cutoff lacked:

      * a finding is never hidden for its POSITION -- only its class can be
        collapsed, and the tail names the class either way;
      * with room to spare NOTHING is hidden, so a lone queue finding still
        prints in full (the rank cutoff's replacement must not become a
        severity filter -- check 11 alone on the screen is the case that
        catches that).

    The most severe band never collapses: below one band there is nothing left
    to say.
    """
    if ceiling is None:
        # Control seam, same shape as OPS_NUDGE_MIRROR_MARKER: the collapse
        # branch is unreachable from a fixture otherwise, since the message
        # lengths belong to the checks and not to the test. Ignored unless it
        # parses as a positive int.
        try:
            ceiling = max(1, int(os.environ["OPS_NUDGE_BYTE_CEILING"]))
        except (KeyError, ValueError):
            ceiling = NUDGE_BYTE_CEILING
    bands = sorted({s for s, _, _ in found})
    while True:
        shown = [f for f in found if f[0] in bands]
        hidden = [f for f in found if f[0] not in bands]
        size = sum(len(t.encode("utf-8")) for _, t, _ in shown)
        if size <= ceiling or len(bands) <= 1:
            return shown, hidden
        bands = bands[:-1]


class Nudges(object):
    """Severity-ordered finding collector.

    `.add(text, sev, label)` replaces the bare list `.append()` this hook used
    until 2026-08-27, and the hand-rolled `.insert(0, ...)` that check 16
    needed to work around the truncation. Ordering is (severity, arrival) so it
    is STABLE: within a band the reading order is still the order the checks
    run, which is what the existing tests assert on.

    All three arguments are REQUIRED, on purpose. `label` is a 2-5 word name
    for the finding, and it is what an over-budget finding contributes to the
    hidden tail -- so a finding that cannot fit is still NAMED rather than
    reduced to a number. Making it optional would let the next check be added
    without one, and the finding it reports would be the one that silently
    becomes a "+1".
    """

    def __init__(self):
        self._items = []

    def add(self, text, sev, label):
        self._items.append((sev, len(self._items), text, label))

    def __len__(self):
        return len(self._items)

    def ordered(self):
        """[(sev, text, label)], most severe first, ties broken by arrival."""
        return [(s, t, n) for s, _, t, n in sorted(self._items)]


def _pid_alive(pid):
    """True / False / None (undeterminable) — check 15's run-record arm.

    No subprocess: this file's budget is 3 s for every check together, and a
    `Get-Process` would spend most of it. ctypes on Windows, signal 0
    elsewhere, and any surprise answers None so the caller falls back to the
    ExecutionTimeLimit backstop rather than inventing a verdict.

    OpenProcess alone is not enough: a handle can still be opened to a process
    that has exited, so the exit code is what actually answers the question
    (STILL_ACTIVE == 259).
    """
    if not isinstance(pid, int) or pid <= 0:
        return None
    try:
        if sys.platform != "win32":
            try:
                os.kill(pid, 0)
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                return True          # exists, owned by someone else
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = k32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFO
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return None
            return code.value == 259                   # STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    except Exception:
        return None


def interop_targets():
    """The live target registry, read from interop.py itself.

    Not re-declared here: a copy of TARGETS in this file would be a second
    source of truth for which targets are live, and 40-maintenance.md S2 is
    exactly the rule that forbids it. Import is cheap -- interop.py does no
    git, no I/O and no network at module level.

    BaseException, not Exception: an interop.py that sys.exit()s while being
    imported (the share-repo copy does, when its leak lib is absent) would
    otherwise take session start down with it. Returns {} on any failure --
    fail-open like every other check here.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_interop_registry", os.path.join(INTEROP, "interop.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return dict(mod.TARGETS)
    except BaseException:
        return {}


def main():
    msgs = Nudges()
    # `--all` is the escape hatch the truncation tail points at: same checks,
    # same cwd rules, no cap, one finding per line. It deliberately does NOT
    # read stdin -- a hook reading a terminal's stdin would hang, and a hint
    # nobody can run is not a hint.
    show_all = "--all" in sys.argv[1:]

    # 11. relaxation gate: a project CLAUDE.md without an ops-relaxation: line
    #     means the 05-authority.md §2 question was never asked or recorded.
    #     Model discipline alone proved unreliable at firing that gate (the
    #     trigger asks for a prediction, and the rule lives two conditional
    #     reads deep), so the nudge is moved into the harness. Silent when
    #     there is no project CLAUDE.md (likely not project work) or cwd is
    #     ~/.claude itself (that CLAUDE.md is the global prefs file — the
    #     level there is per-conversation, not a recorded key).
    try:
        raw = "" if show_all else sys.stdin.read()
        cwd = json.loads(raw).get("cwd", "") if raw.strip() else ""
    except Exception:
        cwd = ""
    cwd = cwd or os.getcwd()
    try:
        is_home = (os.path.normcase(os.path.abspath(cwd))
                   == os.path.normcase(os.path.abspath(HOME)))
    except Exception:
        is_home = False
    try:
        proj_md = os.path.join(cwd, "CLAUDE.md")
        # SHARE-EDITION SPECIALIZATION (declared in tools/share-manifest.toml;
        # the source environment's copy does NOT have this gate). `ops-relaxation`
        # is a key defined by claude-ops/ops/05-authority.md. Adopting the hooks
        # without adopting the ops layer is a supported outcome of this repo --
        # the lanes are independent -- and an adopter in that position would
        # otherwise be nagged, every session, about a key that is defined nowhere
        # they can read and that no file they own can satisfy. A permanently-on
        # alarm is the one kind nobody reads, and it would train them to ignore
        # the other checks too. Not back-flowed: on the source machine the ops
        # layer is always present, so the same gate would only be able to mask a
        # real ghost-rule failure (check 4's job).
        ops_layer_present = os.path.isfile(os.path.join(OPS, "05-authority.md"))
        if ops_layer_present and not is_home and os.path.isfile(proj_md):
            with open(proj_md, encoding="utf-8") as f:
                # A MENTION is not a DECLARATION. This was `"ops-relaxation:"
                # not in text` until 2026-08-15, and the global CLAUDE.md says
                # the words "offer to record `ops-relaxation:` in project
                # CLAUDE.md" -- so every project CLAUDE.md derived from it
                # passed vacuously. Measured that day: every occurrence of the
                # token anywhere in this environment was prose inside a
                # sentence; not one was a real declaration, so the check had
                # never once fired correctly. The discriminator is whether a
                # LEVEL follows (ops/05-authority.md S2 specifies
                # `ops-relaxation: L1`); the line-start prefix class allows a
                # bullet or bold wrapper but deliberately NOT a backtick, which
                # is how 05-authority.md's own quoted example begins.
                if not re.search(r"(?m)^[\s>*_-]*ops-relaxation:"
                                 r"\s*`?\**\s*L[0-2]\b", f.read()):
                    msgs.add(
                        "project CLAUDE.md has no ops-relaxation: level — "
                        "before heavyweight work, state model identity and "
                        "ask the user to pick L0/L1/L2, then offer to record "
                        "it (ops/05-authority.md §2)",
                        SEV_QUEUE, "ops-relaxation level unset"
                    )
    except OSError:
        pass

    # 1. lesson intake report. Replaced the LESSON_CAP unfolded-entry count and
    #    the misfiled-card check on 2026-09-07 (closeout-capture R4 M2): the
    #    ledger is now ops/lessons/ (one record per file, born only through
    #    intake.py add) and ops/lessons.md is GENERATED from it, so "count the
    #    headings" and "a heading below ## Archived" have no meaning any more
    #    (the position-based count also lied twice, L-047 hit 2). The report
    #    derives its lines from each record's ## Events: (a) hits >= 2 never
    #    folded -> route through 40-maintenance S2a; (b) folded but recurring
    #    -> the fix did not hold; (c) dormant; (d) status projection drifted.
    #    `--nudge` prints at most two lines, each carrying its remedy. Runs in
    #    every cwd (lessons are global). Fail-open: a timeout, a missing tool
    #    or a non-zero exit prints nothing -- sweep check 5 runs the full
    #    `intake.py check --against HEAD --index` two-sided.
    # SHARE EDITION: tools/closeout-intake/ does not ship in this repo -- its
    # store (ops/lessons/) and CLI are source-environment-only, the same
    # tools/ exclusion class as tools/session-board/ (see hooks/intake_guard.py's
    # not_shipped entry, same round). The subprocess below therefore always
    # raises FileNotFoundError, caught by the except clause -- exactly the "a
    # missing tool ... prints nothing" branch the check's own comment above
    # already names as a legitimate silent no-op, the same treatment check 16
    # gives a missing ops/cc-reconciled.json.
    try:
        r = subprocess.run(
            [sys.executable,
             os.path.join(HOME, "tools", "closeout-intake", "intake.py"),
             "report", "--nudge"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=INTAKE_REPORT_TIMEOUT)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                line = line.strip()
                if line:
                    # label = the finding without its remedy clause, so a
                    # truncated tail still names WHAT was dropped
                    label = re.split(r"\s[—-]\s", line, 1)[0][:70]
                    msgs.add(line, SEV_QUEUE, label)
    except Exception:
        pass

    # 14. stale uncommitted work in THIS tree -- cwd == ~/.claude only, so other
    #     projects pay nothing. Born 2026-08-21 from the stale-path attribution
    #     ticket: 17 complete, correct record artifacts from 5
    #     projects sat uncommitted here for up to 109 hours. Every session that
    #     wrote them followed the record-keeping discipline; none committed,
    #     because this repo has NO remote -- no push, no PR, no CI -- so
    #     `git status` is the only backpressure and nothing read it. The ONE
    #     subprocess in this hook, budgeted at STALE_WORK_GIT_TIMEOUT inside
    #     settings.json's 3 s. Report-only, like every check here. It does NOT
    #     attribute a dirty path to a session -- that is undecidable from
    #     outside (ops/references/shared-tree-git.md S4; the ticket got it wrong
    #     three times by cwd inference); the count of FRESHER dirty paths is
    #     printed as the "this tree has company" hint instead, which needs no
    #     platform API and no guess. A deleted path cannot be stat()ed and is
    #     skipped; a git failure or timeout prints nothing (fail-open), which is
    #     why sweep check 24 drives the two-sided suite rather than reading
    #     silence as health. why/threshold/review-when: ops/rule-registry.md
    #     key `stale uncommitted work`.
    if is_home:
        try:
            r = subprocess.run(
                ["git", "-C", HOME, "-c", "core.quotepath=off", "status",
                 "--porcelain", "--untracked-files=all"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=STALE_WORK_GIT_TIMEOUT)
            if r.returncode == 0:
                now = time.time()
                stale, fresh = [], 0
                for line in r.stdout.splitlines():
                    if len(line) < 4:
                        continue
                    path = line[3:]
                    if " -> " in path:            # rename: the new name exists
                        path = path.split(" -> ", 1)[1]
                    if len(path) > 1 and path[0] == path[-1] == '"':
                        path = path[1:-1]
                    try:
                        age = (now - os.path.getmtime(
                            os.path.join(HOME, path))) / 86400
                    except OSError:
                        continue                  # deleted: nothing to stat
                    if age > STALE_WORK_DAYS:
                        stale.append((age, path))
                    else:
                        fresh += 1
                if stale:
                    stale.sort(reverse=True)
                    msgs.add(
                        f"stale uncommitted work in ~/.claude: {len(stale)} "
                        f"path(s) older than {STALE_WORK_DAYS}d (oldest "
                        f"{stale[0][0]:.1f}d): "
                        + ", ".join(p for _, p in stale[:3])
                        + (f"; {fresh} fresher dirty path(s) alongside — the "
                           "tree has in-flight company" if fresh else "")
                        + " — finished records nobody committed (no remote, "
                        "so `git status` is the only backpressure): commit "
                        "them by what they touch, carrying a peer's "
                        "provenance if the path is shared, never `git add -A` "
                        "(ops/references/shared-tree-git.md)",
                        SEV_LOSS,
                        f"{len(stale)} stale uncommitted path(s)"
                    )
        except Exception:
            pass

    # 15. graph rot watchdog (tools/graph-snapshot/gs_watchdog.py). Reads the
    #     status file the daily task writes -- one small JSON, no build, no
    #     subprocess. Born 2026-08-26: live-surface broken links went 14 -> 38
    #     in the six days nobody ran the audit, then 38 -> 0 in one harvest
    #     round; rot is fast, and the integrity report only pays rent when
    #     something runs it. Fires on: watchdog silent too long (carrier
    #     presumed dead) / a nonzero live-surface count, with its growth named
    #     when it grew / MOC lag / a failed build (the finding text comes from
    #     gs_watchdog.evaluate, the tested single source of that judgment).
    #     NOT on the premise metric since 2026-09-06 (user ruling): its floor
    #     has no reachable path -- every one of its broken links is in a
    #     historical record where a dead link is correct -- so it alarmed
    #     forever and shared the message with live_broken, which does not.
    #     Still measured, still REFUTED in the report, `premise_under_floor`
    #     in the status file. is_home-scoped like check
    #     14: the remedy is ~/.claude maintenance and would be noise anywhere
    #     else. Fail-open. why/thresholds/review-when: ops/rule-registry.md,
    #     key `graph rot watchdog`.
    #     Second arm (2026-09-09): before trusting the status file at all, ask
    #     whether the run that should have written it came back. A run record
    #     left in `started` outranks everything below it -- not because an
    #     unfinished run is worse than rot, but because while it stands the
    #     status file describes an EARLIER run, so both its all-clear and its
    #     finding are answers to a question nobody asked today. A missing run
    #     record is silent by design: it means a carrier older than this arm,
    #     which the staleness arm already covers and the next run repairs.
    if is_home:
        unfinished = None
        try:
            with open(WATCHDOG_RUN, encoding="utf-8-sig") as f:
                _run = json.load(f)
            if _run.get("state") == "crashed":
                unfinished = _run
            elif _run.get("state") == "started":
                alive = _pid_alive(_run.get("pid"))
                if alive is False:
                    # Re-read before accusing. The one race this arm has is
                    # sampling the record microseconds before a healthy run
                    # closes it; a record that still says `started` after the
                    # process is gone is not that race.
                    with open(WATCHDOG_RUN, encoding="utf-8-sig") as f:
                        if json.load(f).get("state") == "started":
                            unfinished = _run
                elif alive is None:
                    # Liveness undeterminable (no pid in the record, or a host
                    # this cannot ask). Fall back to the time backstop. NOT
                    # applied when the pid is known alive: a manual run may
                    # legitimately outlast the scheduler's limit, and a run
                    # whose pid was recycled is caught by the staleness arm
                    # below once the status file stops being refreshed.
                    try:
                        began = time.mktime(time.strptime(_run["started_at"],
                                                          "%Y-%m-%dT%H:%M:%S"))
                    except (KeyError, ValueError, OverflowError):
                        began = os.path.getmtime(WATCHDOG_RUN)
                    if (time.time() - began) / 60 > WATCHDOG_RUN_LIMIT_MIN:
                        unfinished = _run
        except Exception:
            pass
        try:
            if unfinished is not None:
                why = (f"crashed ({unfinished.get('error')})"
                       if unfinished.get("state") == "crashed" else
                       "never came back — killed, or the machine went down")
                since = ""
                try:
                    with open(WATCHDOG_STATUS, encoding="utf-8-sig") as f:
                        since = " (last finished run: %s)" % json.load(f).get(
                            "ran_at", "unknown")
                except Exception:
                    pass
                msgs.add(
                    "graph rot watchdog: the run started "
                    f"{unfinished.get('started_at')} did not finish — {why}, "
                    "so watchdog-status.json is from an EARLIER run and says "
                    f"nothing about today{since}. Check "
                    "your graph-watchdog task's scheduler entry (LastTaskResult) and "
                    "run `python tools/graph-snapshot/gs_watchdog.py`",
                    SEV_ALARM, "graph watchdog run unfinished"
                )
            elif not os.path.isfile(WATCHDOG_STATUS):
                msgs.add(
                    "graph rot watchdog has never run — "
                    "`python tools/graph-snapshot/gs_watchdog.py`, and check "
                    "your graph-watchdog task's scheduler entry",
                    SEV_ALARM, "graph watchdog never ran"
                )
            else:
                age = (time.time() - os.path.getmtime(WATCHDOG_STATUS)) / 86400
                # utf-8-sig: a BOM-carrying writer would otherwise disable
                # this check silently through the fail-open except below.
                with open(WATCHDOG_STATUS, encoding="utf-8-sig") as f:
                    wd = json.load(f)
                if age > WATCHDOG_STALE_DAYS:
                    msgs.add(
                        f"graph rot watchdog silent {age:.1f}d "
                        f"(>{WATCHDOG_STALE_DAYS}d) — its daily task may be "
                        "dead: run `python tools/graph-snapshot/gs_watchdog.py`"
                        " and check your graph-watchdog task's scheduler entry",
                        SEV_ALARM, "graph watchdog silent"
                    )
                elif wd.get("finding"):
                    finding = str(wd["finding"])
                    # The remedy follows the finding (round 4, audit G-1): a
                    # lagging MOC is regenerated, not harvested. 2026-09-06:
                    # read the KIND the watchdog decided, instead of matching
                    # substrings of a sentence it may reword -- the old branch
                    # keyed on the literal "broken links", and the day that
                    # sentence became "3 live-surface broken link(s)" it would
                    # have silently picked the wrong remedy. The substring
                    # arm stays as the fallback for a status file written by
                    # an older watchdog.
                    # 2026-09-09: the `build` kind had no branch here, so a
                    # failed build -- the one finding that says nothing else
                    # in the file was measured today -- fell through to
                    # "harvest due: read the integrity report", a file the
                    # failed build did not regenerate. The measured line sent
                    # the reader to the LAST GOOD build's output while telling
                    # them the graph needed attention first. Every kind
                    # gs_watchdog.evaluate() can set now has a branch; the
                    # fallback maps the same three, so an old status file
                    # written before `remedy_kind` existed cannot reach the
                    # wrong one either. The three are a TABLE and the default is
                    # reserved for a kind this surface does not know (L-068):
                    # `harvest` used to be the else, which is how `build` was
                    # served a plausible wrong sentence instead of an error.
                    # The FALLBACK below keeps a default on purpose -- it maps
                    # free TEXT, an open set, where a default is the only
                    # terminating branch. A closed set of values is different:
                    # every member is named, and the unnamed case says so.
                    kind = wd.get("remedy_kind")
                    if kind is None:
                        if "FAILED" in finding:
                            kind = "build"
                        elif "MOC lags" in finding and not any(
                                k in finding for k in ("broken link", "premise")):
                            kind = "regenerate"
                        else:
                            kind = "harvest"
                    remedy = {
                        "build":
                            " — rebuild first: `python -X utf8 tools/"
                            "graph-snapshot/gsnap.py baseline` / `build` / "
                            "`verify`, and see which step exits nonzero — "
                            "every other number in this status file is the "
                            "LAST GOOD build's. A common cause is not a "
                            "graph defect: the corpus changed under the "
                            "build, which verify reports as an INV-2 "
                            "zero-touch violation — another session editing "
                            "~/.claude while it ran",
                        "regenerate":
                            " — regenerate: gsnap.py baseline / build / verify, "
                            "then `python -X utf8 tools/graph-snapshot/gsnap.py "
                            "emit-moc`, and commit references/_moc",
                        "harvest":
                            " — harvest due: read tools/graph-snapshot/out/"
                            "integrity-report.md (graph-query skill, J3)",
                    }.get(kind)
                    if remedy is None:
                        remedy = (f" — this surface has no remedy for remedy_kind"
                                  f" {kind!r}: gs_watchdog.evaluate() gained a "
                                  "kind check 15 was never extended for, so act "
                                  "on the finding above and add the branch "
                                  "(hooks/ops_health_nudge.py check 15)")
                    msgs.add("graph rot watchdog: " + finding + remedy,
                             SEV_ALARM, "graph rot reported")
        except Exception:
            pass

    # 16. Claude Code build vs the build ops/ was reconciled against. NOT
    #     is_home-scoped: a stale ops fact misleads in whatever project is
    #     open, not only while editing ~/.claude. Born 2026-08-26, after the
    #     CLI went 2.1.200 -> 2.1.246 with 8 recorded ops facts going stale
    #     unnoticed -- one of them pointing at a tool this environment cannot
    #     call. rule-registry.md had 6 `review-when: any Claude Code upgrade`
    #     entries and nothing on the machine ever fired them; this is the
    #     carrier they were missing. Cost: stat() only, until the binary moves.
    #     A missing stamp is REPORTED (the mechanism is uninstalled), a missing
    #     binary is not (that path is host-specific and its absence is normal).
    try:
        with open(CC_STAMP, encoding="utf-8-sig") as f:
            cc = json.load(f)
        want = cc.get("reconciled_version")
        try:
            b = os.stat(CC_BIN)
            moved = (b.st_size != cc.get("binary_size")
                     or int(b.st_mtime) != cc.get("binary_mtime"))
        except OSError:
            moved = False
        if moved and want:
            out = subprocess.run([CC_BIN, "--version"], capture_output=True,
                                 text=True, timeout=1.5)
            m = re.search(r"\d+\.\d+\.\d+", out.stdout or "")
            if m and m.group(0) != want:
                # SEV_ALARM, not the default band: this one is not a budget
                # reminder -- it says the rules being followed may no longer
                # describe the running build, which outranks a file being 0.2K
                # over its cap. It used to say `insert(0)` for the same reason,
                # back when ordering was something each check had to arrange
                # for itself. Same band for the stamp-missing branch below.
                msgs.add(
                    f"Claude Code is {m.group(0)} but ops/ was reconciled at "
                    f"{want} — ops facts are unverified against the running "
                    "build: `python tools/cc-delta/cc_delta.py`",
                    SEV_ALARM, "ops/ reconciled at an older build"
                )
    except FileNotFoundError:
        msgs.add(
            "ops/cc-reconciled.json missing — the Claude Code version-delta "
            "check is uninstalled, so `review-when: any Claude Code upgrade` "
            "entries in rule-registry.md have no carrier again",
            SEV_ALARM, "cc-reconciled.json missing"
        )
    except Exception:
        pass

    # 17. session-transcript mirror heartbeat (born 2026-09-01, D-052 item 5).
    #     The mirror (tools/claude-session-transcript-mirror.ps1, D-033) is
    #     the only thing between cleanupPeriodDays deletion and the
    #     transcripts, and it was silent-when-dead: it wrote a marker nobody
    #     read. This reads that one small marker; run HISTORY lives beside it
    #     in run-ledger.tsv (append-only; jsonl count may only grow under the
    #     COPY-ONLY contract — a drop between lines means archive loss).
    #     is_home-scoped like 15: the remedy is machine maintenance. Fail-open.
    if is_home:
        try:
            mirror_root = os.path.dirname(os.path.dirname(MIRROR_MARKER))
            if not os.path.isdir(mirror_root):
                pass   # host without the archive: absence is normal (CC_BIN)
            elif not os.path.isfile(MIRROR_MARKER):
                msgs.add(
                    "session-transcript mirror marker missing — the backup "
                    "may have never run: check your mirror task's scheduler "
                    "entry, then run "
                    "tools/claude-session-transcript-mirror.ps1",
                    SEV_ALARM, "session mirror marker missing"
                )
            else:
                age = (time.time() - os.path.getmtime(MIRROR_MARKER)) / 86400
                with open(MIRROR_MARKER, encoding="utf-8-sig") as f:
                    first = f.readline().strip()
                if first.startswith("FAIL"):
                    msgs.add(
                        "session-transcript mirror FAILED its last run ("
                        + first + ") — transcripts are unprotected against "
                        "cleanupPeriodDays deletion: see "
                        "your mirror log directory",
                        SEV_ALARM, "session mirror failed"
                    )
                elif age > MIRROR_STALE_DAYS:
                    msgs.add(
                        f"session-transcript mirror silent {age:.1f}d "
                        f"(>{MIRROR_STALE_DAYS}d) — its daily task may be "
                        "dead: check your mirror task's scheduler entry, "
                        "then run tools/claude-session-transcript-mirror.ps1",
                        SEV_ALARM, "session mirror silent"
                    )
        except Exception:
            pass

    # 18. unguarded copies (tools/copy-census, born 2026-09-09). Reads ONE
    #     small JSON its carrier writes; never scans anything itself -- the
    #     scan costs ~1 s over two roots and this hook has a 3 s budget for
    #     every check together. Three states, and the missing/stale ones matter
    #     as much as the findings: a copy guard nobody runs is worse than none,
    #     because the clean line it printed last week is still believed.
    #     is_home-scoped like 15 and 17: the remedy is machine maintenance.
    if is_home:
        try:
            # A host without the tool is silent by design -- the same
            # absence-is-normal call check 17 makes for the archive root. Only
            # an INSTALLED tool with no run record is an alarm.
            cc_root = os.path.dirname(os.path.dirname(COPY_CENSUS_STATUS))
            if not os.path.isdir(cc_root):
                pass
            elif not os.path.isfile(COPY_CENSUS_STATUS):
                msgs.add(
                    "copy-census has never recorded a run — the guard over "
                    "this machine's unguarded copies may not be running: "
                    "check your copy-census task's scheduler entry, then "
                    "run tools/copy-census/run-daily.ps1",
                    SEV_ALARM, "copy-census never ran"
                )
            else:
                age = (time.time()
                       - os.path.getmtime(COPY_CENSUS_STATUS)) / 86400
                try:
                    with open(COPY_CENSUS_STATUS, encoding="utf-8") as f:
                        status = json.load(f)
                except (ValueError, UnicodeDecodeError):
                    # An unreadable record is the WORST state, not a neutral
                    # one: it is recent enough to escape the staleness branch
                    # and unparseable enough to say nothing. Without this the
                    # outer except-pass turned a half-written file into
                    # silence -- which is exactly the failure this check
                    # exists to catch. Found by review 2026-09-09.
                    msgs.add(
                        "copy-census run record is unreadable — the last run "
                        "may have been killed mid-write: run "
                        "tools/copy-census/copies.py --check --record",
                        SEV_ALARM, "copy-census record unreadable"
                    )
                    raise _CopyCensusHandled
                findings = status.get("findings") or []
                if age > COPY_CENSUS_STALE_DAYS:
                    msgs.add(
                        f"copy-census silent {age:.1f}d "
                        f"(>{COPY_CENSUS_STALE_DAYS}d) — its daily task may "
                        "be dead: check your copy-census task's scheduler entry, then run "
                        "tools/copy-census/run-daily.ps1",
                        SEV_ALARM, "copy-census silent"
                    )
                elif findings:
                    worst = "FAIL" if any(
                        f.get("severity") == "FAIL" for f in findings) else "WARN"
                    msgs.add(
                        f"copy-census {worst}: "
                        + "; ".join(
                            "%s %s" % (f.get("kind"), f.get("row"))
                            for f in findings[:3])
                        + (f" (+{len(findings) - 3} more)"
                           if len(findings) > 3 else "")
                        + " — run tools/copy-census/copies.py --check for the "
                          "detail; a new pair needs a row in rows.toml",
                        SEV_ALARM if worst == "FAIL" else SEV_QUEUE,
                        "copy-census " + worst
                    )
        except Exception:
            pass

    # 2. oversized ops files -- ONE message for all of them: the remedy is
    #    shared, and this line is charged every session.
    try:
        fat_ops = []
        for name in sorted(os.listdir(OPS)):
            if name.endswith(".md") and name not in SIZE_CAP_EXEMPT:
                n = os.path.getsize(os.path.join(OPS, name))
                if n > SIZE_CAP:
                    fat_ops.append(f"{name} {n / 1024:.1f}K")
        if fat_ops:
            msgs.add(
                f"ops file(s) over {SIZE_CAP // 1024}K bytes: "
                + ", ".join(fat_ops)
                + " — EXTRACT the concrete (examples, command blocks, cases) "
                "to ops/references/ behind a pointer, keep rule+conditions+"
                "routing in place; never compress a rule to fit; if a lossless "
                "pass still misses, RAISE the cap with that pass as evidence "
                "(40-maintenance.md S3)",
                SEV_BREACH,
                "ops/*.md over cap: " + ", ".join(
                    f.split(" ")[0] for f in fat_ops)
            )
    except OSError:
        pass

    # 3. audit-trail staleness
    try:
        trail = os.path.join(OPS, "rule-registry.md")
        idle = (time.time() - os.path.getmtime(trail)) / 86400
        if idle > TRAIL_IDLE_DAYS:
            msgs.add(
                f"rule registry idle {int(idle)}d: run degradation checks "
                "(ops/40-maintenance.md S4)",
                SEV_QUEUE, f"rule registry idle {int(idle)}d"
            )
    except OSError:
        pass

    # 4. ghost-rule guard: every routed file must exist
    missing = [f for f in ROUTED_FILES
               if not os.path.isfile(os.path.join(OPS, f))]
    if missing:
        msgs.add(
            "OPS.md routing targets missing: " + ", ".join(missing)
            + " — the rules layer is partially dead; fix routing first",
            SEV_ALARM, "routed ops file(s) missing"
        )

    # 5+6. preload budgets: skill descriptions and SKILL.md body size
    try:
        fat_desc, fat_body = [], []
        for name in os.listdir(SKILLS):
            p = os.path.join(SKILLS, name, "SKILL.md")
            if not os.path.isfile(p):
                continue
            with open(p, encoding="utf-8") as f:
                text = f.read()
            m = re.search(
                r"^description:[^\n]*\n((?:[ \t]+[^\n]*\n|\n(?=[ \t]))*)",
                text, re.M,
            )
            if m and len(m.group(1)) > DESC_CAP:
                fat_desc.append(name)
            if text.count("\n") > BODY_CAP:
                fat_body.append(name)
        if fat_desc:
            msgs.add(
                "skill description(s) over "
                f"{DESC_CAP} chars: {', '.join(fat_desc)} — slim per "
                "ops/40-maintenance.md S3 budgets",
                SEV_BREACH,
                "skill desc over cap: " + ", ".join(fat_desc)
            )
        if fat_body:
            msgs.add(
                f"SKILL.md over {BODY_CAP} lines: {', '.join(fat_body)} — "
                "move detail to references/ (ops/40-maintenance.md S3)",
                SEV_BREACH,
                "SKILL.md over cap: " + ", ".join(fat_body)
            )
    except OSError:
        pass

    # 7-9. root-file budgets. The two are DIFFERENT rule classes (S3): CLAUDE.md
    #      is charged unconditionally every session, so the number IS the budget
    #      and the remedy is merge/relocate. The dict is charged only on a
    #      routing miss, so its cap is a REVIEW TRIGGER and the remedy is to
    #      check the entries against measured routing before touching size.
    for fname, cap, hint in (
        ("CLAUDE.md", CLAUDE_MD_CAP,
         "UNCONDITIONAL every-session budget — MERGE into an existing "
         "conditional bullet, or move the rule to a rules/ path-scoped file "
         "or a skill; never append, never compress a rule to fit"),
        ("skill-trigger-dict.md", DICT_CAP,
         "REVIEW TRIGGER, not a budget — run "
         "`python tools/skill-routing-audit.py` first and delete or correct "
         "the entries it reports as fiction; raising the cap after that "
         "review is the intended outcome, extraction is not"),
    ):
        try:
            n = os.path.getsize(os.path.join(HOME, fname))
            if n > cap:
                # `cap / 1024:g`, never `cap // 1024`: CLAUDE_MD_CAP is 19,968
                # and integer division printed it as "19K", so the line
                # misreported its own threshold by half a K -- the same
                # copied-number failure as the docstring, one layer down.
                msgs.add(
                    f"{fname} {n / 1024:.1f}K over {cap / 1024:g}K bytes: "
                    f"{hint} (ops/40-maintenance.md S3)",
                    SEV_BREACH,
                    f"{fname} {n / 1024:.1f}K over {cap / 1024:g}K"
                )
        except OSError:
            pass

    # 10. dict-sync drift: every local skill must appear in the trigger dict
    #     (ops/40-maintenance.md S2 dict-sync corollary; silent when in sync)
    try:
        with open(os.path.join(HOME, "skill-trigger-dict.md"),
                  encoding="utf-8") as f:
            dict_text = f.read()
        undicted = [
            name for name in os.listdir(SKILLS)
            if os.path.isfile(os.path.join(SKILLS, name, "SKILL.md"))
            and name not in dict_text
        ]
        if undicted:
            msgs.add(
                "skill(s) absent from skill-trigger-dict.md: "
                + ", ".join(undicted)
                + " — dict-sync breach (ops/40-maintenance.md S2)",
                SEV_ALARM,
                "skill(s) absent from the routing dict"
            )
    except OSError:
        pass

    # 12. interop freshness. `interop.py status` already computes all of this
    #     and exits 1 -- but nothing ran it, so the opencode target sat
    #     `[missing]` (never deployed at all) from 2026-08-11 until it was
    #     found by hand on 2026-08-15. A report nobody runs is not a check.
    #     This is the cheap screen that routes to it: stat() only, no git, no
    #     subprocess. Two of the three conditions it tests are exact -- the
    #     artifact is absent, or it is present but not ours. The third is not:
    #     "source mtime > artifact mtime" is NOT the commit comparison status
    #     makes, and it both over-fires (a checkout or a touch restamps mtime
    #     without changing content) and under-fires (a commit whose checkout
    #     predates the build). That is why the remedy below is always `status`
    #     and never `build`: the nudge points at the authority instead of
    #     impersonating it, so a false positive costs one cheap command.
    try:
        problems = []
        # No interop/ at all means the layer is not installed here, which is a
        # valid state -- not a finding. Without this guard the curation branch
        # below reports a missing stamp forever, on a machine where no command
        # can ever create one: a permanently-on alarm, which is the one kind
        # nobody reads. (Caught by the synthetic-tree test, not by reasoning.)
        if not os.path.isdir(INTEROP):
            raise OSError("interop layer not installed")
        for name, t in interop_targets().items():
            # A disabled target is a ruling, not a backlog item -- same
            # reasoning as cmd_status's `[off]` branch. Do not count it.
            if t.get("disabled"):
                continue
            path = str(t["path"])
            if not os.path.isfile(path):
                problems.append(f"{name} not deployed")
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                if "managed-by: claude-interop" not in f.read(300):
                    problems.append(f"{name} not interop-managed")
                    continue
            built = os.path.getmtime(path)
            behind = [s for s in INTEROP_SOURCES
                      if os.path.getmtime(os.path.join(INTEROP, s)) > built]
            if behind:
                problems.append(f"{name} older than {', '.join(behind)}")
        stamp = os.path.join(INTEROP, "curation.stamp")
        if not os.path.isfile(stamp):
            problems.append("no curation stamp")
        elif (os.path.getmtime(os.path.join(HOME, "CLAUDE.md"))
              > os.path.getmtime(stamp)):
            problems.append("CLAUDE.md changed since last curation")
        if problems:
            msgs.add(
                "interop: " + "; ".join(problems)
                + " — run `python interop/interop.py status` for the "
                "authoritative report (it compares commits; this screen only "
                "compared mtimes), then build / curated as it directs",
                SEV_ALARM, "interop: " + "; ".join(problems)
            )
    except OSError:
        pass

    # 13. advisory-output status lines (rules-usage-dict.md S7, 2026-08-16).
    #     Advisory artifacts under outputs/ declare handling status in a
    #     greppable line within their first 10 lines; this screen surfaces the
    #     ones still awaiting action and flags NEW ones born without the line.
    #     The two checks have DIFFERENT scopes, and that asymmetry is the
    #     design (widened 2026-09-10, after a deferred-extraction record filed
    #     under outputs/ proved invisible here):
    #       - OWES a stamp: candidates files and experiment metrics only. That
    #         list stays narrow because it says who is OBLIGED; widening it
    #         would nag every file under outputs/.
    #       - MAY be polled: any outputs/**/*.md that stamps ITSELF, minus
    #         outputs/skill-reviews/ (D-032 disposition convention, not
    #         double-governed). A file opts in by carrying the line.
    #     Measured before shipping, because the naive widening is the alarm
    #     nobody reads: 40 stamped files, of which "not SPENT" alone yields 35
    #     findings. So the ruler is the convention's own vocabulary
    #     (SPENT / OPEN / PARTIAL, plus deferred / pending / await / 待裁 /
    #     待決 / 尚未) and identical status text inside one directory collapses
    #     to ONE row with a count -- 23 trigger-probe reports are two standing
    #     residuals, not 23 offers. Result: 6 rows for 26 waiting files.
    #     A stamp matching NEITHER family cannot be ruled on (CLOSED, CONSUMED,
    #     LIVE, 量測紀錄 -- words the convention never defined): it is counted
    #     into the same message, never silenced and never expanded per file.
    #     A file with no date in its name, or dated on/before the convention's
    #     birth, is exempt from the missing-line flag (no backfill --
    #     evidence-block precedent).
    try:
        import glob as _glob
        spent_rx = re.compile(r"SPENT|已執行|否決|已裁")
        waiting_rx = re.compile(r"\bOPEN\b|\bPARTIAL\b|\bdeferred\b|\bpending\b"
                                r"|\bawait|待裁|待決|待確認|尚未", re.I)
        status_rx = re.compile(r"^(?:> status:|\*\*狀態)")
        date_rx = re.compile(r"(\d{4}-\d{2}-\d{2})")
        stamps = {}
        for p in _glob.glob(os.path.join(HOME, "outputs", "**", "*.md"),
                            recursive=True):
            rel = os.path.relpath(p, HOME).replace(os.sep, "/")
            if rel.startswith("outputs/skill-reviews/"):
                continue          # D-032 disposition convention; not double-governed
            with open(p, encoding="utf-8", errors="replace") as f:
                head = [next(f, "") for _ in range(10)]
            stamps[rel] = next((l for l in head if status_rx.match(l)), None)

        waiting, undetermined = {}, 0
        for rel, line in stamps.items():
            if line is None or spent_rx.search(line):
                continue
            body = re.sub(r"\s+", " ", status_rx.sub("", line).strip())
            if not waiting_rx.search(body):
                undetermined += 1     # a word the convention does not define
                continue
            waiting.setdefault((os.path.dirname(rel), body[:40]), []).append(rel)

        unstamped = []
        for pat in ("outputs/retrospectives/global-rule-candidates-*.md",
                    "outputs/experiments/*/metrics.md"):
            for p in _glob.glob(os.path.join(HOME, pat)):
                rel = os.path.relpath(p, HOME).replace(os.sep, "/")
                base = (os.path.basename(os.path.dirname(p))
                        if os.path.basename(p) == "metrics.md"
                        else os.path.basename(p))
                if stamps.get(rel, "sentinel") is None:
                    m = date_rx.search(base)
                    if m and m.group(1) > "2026-08-16":
                        unstamped.append(base)
        if waiting or undetermined:
            items = []
            for (d, _k), files in sorted(waiting.items()):
                items.append(os.path.basename(files[0]) if len(files) == 1
                             else f"{d}/ x{len(files)}")
            # The undetermined count rides in the same message but never
            # DEPENDS on it: a run with only unruleable stamps must still say
            # so, or the class the parse cannot close disappears from the
            # screen entirely.
            tail = ""
            if undetermined:
                tail = (f"{undetermined} stamped file(s) use a word the "
                        f"convention does not define (SPENT/OPEN/PARTIAL) and "
                        f"could not be ruled on")
            head = ("advisory output(s) still OPEN: " + ", ".join(items)
                    + " — carries offers a session may need to act on; read its "
                    "status line (rules-usage-dict.md S7)") if items else ""
            msgs.add(
                (head + (". " if head and tail else "") + tail)
                if head else
                (tail + " — advisory status lines, "
                 "rules-usage-dict.md S7 defines the three words"),
                SEV_LOSS,
                f"{len(items)} advisory output(s) OPEN"
                if items else f"{undetermined} advisory stamp(s) unruleable"
            )
        if unstamped:
            msgs.add(
                "advisory output(s) born without a status line: "
                + ", ".join(sorted(unstamped))
                + " — add `> status: ...` in the first 10 lines "
                "(rules-usage-dict.md S7)",
                SEV_LOSS,
                f"{len(unstamped)} advisory output(s) unstamped"
            )
    except OSError:
        pass

    found = msgs.ordered()
    if show_all:
        if found:
            shown_n = len(split_by_band(found)[0])
            print(f"[ops-health] {len(found)} finding(s), most severe first "
                  f"(a session start shows {shown_n}):")
            for sev, text, _label in found:
                print(f"  [{SEV_NAME[sev]}] {text}")
        else:
            print("[ops-health] no findings")
    elif found:
        shown_items, rest = split_by_band(found)
        shown = [t for _, t, _ in shown_items]
        if rest:
            # Defect 1's actual fix. A COUNT is not enough: it lets a reader
            # tell that something was dropped, but not WHAT -- and the finding
            # this was found by (skill-trigger-dict.md over DICT_CAP) would
            # still not have surfaced. So the tail carries each hidden
            # finding's label, which is short by construction; the full remedy
            # text is what --all is for. Since 2026-09-08 the tail holds whole
            # BANDS rather than whatever fell past rank 4, so a label appearing
            # here says "this class is collapsed", not "this one was unlucky".
            shown.append(
                f"(+{len(rest)} more, not shown in full: "
                + "; ".join(label for _, _, label in rest)
                + " — `python hooks/ops_health_nudge.py --all` for the "
                "remedies)"
            )
        # stdout on SessionStart is injected as session context
        print("[ops-health] " + " | ".join(shown))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # a health nudge must never break session start
