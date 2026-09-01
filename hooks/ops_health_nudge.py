#!/usr/bin/env python3
"""SessionStart hook: ops-layer health nudge.

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
  1. ops/lessons.md unfolded entries over LESSON_CAP    -> trim pass due
  2. any ops/*.md over SIZE_CAP                 -> extract pass due
     (excl. lessons.md and rule-registry.md -- see SIZE_CAP_EXEMPT)
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
     (rules-usage-dict.md S7 "advisory-output status line")
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

The printed line is CAPPED at NUDGE_CAP findings and ordered by SEVERITY --
see the band comments below. Truncation is never silent: a hidden-count tail is
appended whenever anything is dropped, and `--all` prints every finding, one
per line. Before 2026-08-27 the print was a bare `msgs[:4]` and the dict cap
breach had been crowded out for an unknown number of sessions.
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
LESSON_CAP = 30
SIZE_CAP = 22 * 1024   # BYTES per ops/*.md (getsize). REVIEW TRIGGER, not a
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
                       # why/history: ops/rule-registry.md, key `ops file cap`;
                       # unit: key `cap measurement unit`. CLAUDE_MD_CAP below
                       # is deliberately NOT raised with it -- different class.
# Files whose size tracks the CORPUS, not bloat: an over-cap reading on these
# has no extract remedy, and a permanently-on alarm is one nobody reads. Their
# real degradation checks are elsewhere -- lessons.md has LESSON_CAP (entries,
# not bytes); rule-registry.md is bounded by the rule count and checked by
# 40-maintenance.md S4.1 (an entry for a rule nobody uses). why/history:
# ops/rule-registry.md, key `ops file cap`.
SIZE_CAP_EXEMPT = {"lessons.md", "rule-registry.md"}
TRAIL_IDLE_DAYS = 45
DESC_CAP = 800          # chars, skill frontmatter description — this is the
                        # one that costs EVERY session; keep it tight.
BODY_CAP = 300          # lines, whole SKILL.md. Charged only on invoke, not at
                        # session start. Over cap means EXTRACT to references/,
                        # never compress in place. why/history:
                        # ops/rule-registry.md
CLAUDE_MD_CAP = 19968      # BYTES (19.5 KB). why/history: ops/rule-registry.md
DICT_CAP = 28 * 1024   # BYTES. REVIEW TRIGGER, not a budget -- same class (b)
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
# daily task (decisions D-033) is
# presumed dead. PROVISIONAL by the check-15 argument: daily carrier, 3
# tolerates two off days. The FAIL state fires regardless of age -- the
# mirror is the only thing between cleanupPeriodDays deletion and the
# transcripts. Run HISTORY lives beside the marker in run-ledger.tsv
# (append-only; the jsonl count may only grow under the COPY-ONLY contract).
# why/history/review-when: your own rule registry.
# The env var is the TEST SEAM (hermetic fixtures in tools/ops-health-test);
# the archive-root gate in the check makes a host without the archive silent
# by design (same absence-is-normal call as CC_BIN in check 16).
# SHARE EDITION: no default marker path ships here -- the source's default was
# an absolute path on a non-system drive (a private mirror root, the same
# leak class handled in transcript_read_guard.py CORPUS_ROOTS). Point
# OPS_NUDGE_MIRROR_MARKER at your own marker file; an unset/empty value's
# parent dir will not exist, so the check below stays silent by the same
# absence-is-normal rule as CC_BIN.
MIRROR_STALE_DAYS = 3
MIRROR_MARKER = os.environ.get("OPS_NUDGE_MIRROR_MARKER") or ""

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
NUDGE_CAP = 4
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

    # 1. unfolded lesson count
    try:
        with open(os.path.join(OPS, "lessons.md"), encoding="utf-8") as f:
            body = f.read().split("## Archived")[0]
        n = len(re.findall(r"^## L-\d+", body, re.M))
        if n > LESSON_CAP:
            msgs.add(
                f"ops/lessons.md has {n} unfolded entries (>{LESSON_CAP}): "
                "run the trim pass (ops/40-maintenance.md S3)",
                SEV_QUEUE, f"lessons.md {n} entries"
            )
    except OSError:
        pass

    # 14. stale uncommitted work in THIS tree -- cwd == ~/.claude only, so other
    #     projects pay nothing. Born 2026-08-21 from the stale-path attribution
    #     ticket (task_406a32d8): 17 complete, correct record artifacts from 5
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
    #     presumed dead) / links grew since last run / premise metric under
    #     its floor (the finding text comes from gs_watchdog.evaluate, the
    #     tested single source of that judgment). is_home-scoped like check
    #     14: the remedy is ~/.claude maintenance and would be noise anywhere
    #     else. Fail-open. why/thresholds/review-when: ops/rule-registry.md,
    #     key `graph rot watchdog`.
    if is_home:
        try:
            if not os.path.isfile(WATCHDOG_STATUS):
                msgs.add(
                    "graph rot watchdog has never run — "
                    "`python tools/graph-snapshot/gs_watchdog.py`, and check "
                    "the ClaudeGraphSnapshotWatchdog-Daily scheduled task",
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
                        " and check ClaudeGraphSnapshotWatchdog-Daily",
                        SEV_ALARM, "graph watchdog silent"
                    )
                elif wd.get("finding"):
                    msgs.add(
                        "graph rot watchdog: " + str(wd["finding"])
                        + " — harvest due: read tools/graph-snapshot/out/"
                        "integrity-report.md (graph-query skill, J3)",
                        SEV_ALARM, "graph rot reported"
                    )
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
                        "cleanupPeriodDays deletion: see your mirror log "
                        "directory",
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
    #     Scope is deliberately narrow -- candidates files and experiment
    #     metrics only; outputs/skill-reviews/ keeps its own disposition
    #     convention (D-032) and is not double-governed. A file with no date
    #     in its name, or dated on/before the convention's birth, is exempt
    #     from the missing-line flag (no backfill -- evidence-block precedent;
    #     a permanently-on alarm about old files is the alarm nobody reads).
    #     The status parse rules only on what it can determine: clearly-spent
    #     keywords silence, anything else present surfaces and routes to
    #     reading ONE named file.
    try:
        import glob as _glob
        spent_rx = re.compile(r"SPENT|已執行|否決|已裁")
        status_rx = re.compile(r"^(?:> status:|\*\*狀態)")
        date_rx = re.compile(r"(\d{4}-\d{2}-\d{2})")
        open_arts, unstamped = [], []
        for pat in ("outputs/retrospectives/global-rule-candidates-*.md",
                    "outputs/experiments/*/metrics.md"):
            for p in _glob.glob(os.path.join(HOME, pat)):
                with open(p, encoding="utf-8", errors="replace") as f:
                    head = [next(f, "") for _ in range(10)]
                line = next((l for l in head if status_rx.match(l)), None)
                base = (os.path.basename(os.path.dirname(p))
                        if os.path.basename(p) == "metrics.md"
                        else os.path.basename(p))
                if line is None:
                    m = date_rx.search(base)
                    if m and m.group(1) > "2026-08-16":
                        unstamped.append(base)
                elif not spent_rx.search(line):
                    open_arts.append(base)
        if open_arts:
            msgs.add(
                "advisory output(s) still OPEN: "
                + ", ".join(sorted(open_arts))
                + " — carries offers a session may need to act on; read its "
                "status line (rules-usage-dict.md S7)",
                SEV_LOSS,
                f"{len(open_arts)} advisory output(s) OPEN"
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
            print(f"[ops-health] {len(found)} finding(s), most severe first "
                  f"(a session start shows the first {NUDGE_CAP}):")
            for sev, text, _label in found:
                print(f"  [{SEV_NAME[sev]}] {text}")
        else:
            print("[ops-health] no findings")
    elif found:
        shown = [t for _, t, _ in found[:NUDGE_CAP]]
        rest = found[NUDGE_CAP:]
        if rest:
            # Defect 1's actual fix. A COUNT is not enough: it lets a reader
            # tell that something was dropped, but not WHAT -- and the finding
            # this was found by (skill-trigger-dict.md over DICT_CAP) would
            # still not have surfaced. So the tail carries each hidden
            # finding's label, which is short by construction; the full remedy
            # text is what --all is for. The cap stays a FINDING cap, not a
            # character one, so this tail is the only thing that grows.
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
