#!/usr/bin/env python3
"""SessionStart hook: ops-layer health nudge.

Prints ONE short reminder line only when a maintenance threshold trips;
completely silent when everything is healthy. Never blocks, never denies,
stdlib only, pinned to ~/.claude. Designed to close the gap where
ops/40-maintenance.md defines trim/degradation checks but nothing ever
triggers them.

Checks (all cheap, no network, no subprocess):
  1. ops/lessons.md unfolded entries > 30       -> trim pass due
  2. any ops/*.md over 15K BYTES                -> extract pass due
     (excl. lessons.md and rule-registry.md -- see SIZE_CAP_EXEMPT)
  3. rule registry idle > 45 days               -> degradation check due
  4. OPS.md routing targets missing on disk     -> ghost-rule alarm
  5. skill description > 800 chars              -> preload-budget breach
  6. SKILL.md body > 300 lines                  -> move detail to references/
  7. CLAUDE.md > 15K BYTES                      -> always-loaded budget breach
  8. skill-trigger-dict.md > 24K BYTES          -> dict review due (audit 1st)
  9. (retired 2026-08-11 -- the trail is frozen, see below)
 10. skills/ dir vs skill-trigger-dict.md drift -> dict-sync breach (40-maintenance S2)
 11. project CLAUDE.md declares no ops-relaxation level -> gate never fired
     (a DECLARATION -- `ops-relaxation: L1` -- not a prose mention; see below)
 12. interop target undeployed/foreign/behind   -> run interop.py status
 13. advisory output OPEN / born unstamped      -> read the named file
     (rules-usage-dict.md S7 "advisory-output status line")
Thresholds mirror ops/40-maintenance.md S3 defaults; change them together --
INCLUDING the unit. File caps are BYTES (os.path.getsize, so CRLF counts 2);
DESC_CAP is chars; BODY_CAP is lines. Bytes because they track token cost:
bytes/token holds at 3.8-4.1 across this corpus while chars/token ranges
2.3-4.0. Drift between this file and the S3 table is sweep check 7.

Message wording is load-bearing: the nudge is what reaches session context,
while S3 is two routing hops away. So each message must carry the REMEDY, not
just the number -- a bare "trim" invites the compression S3 forbids.
"""
import json
import os
import re
import sys
import time

HOME = os.path.expanduser("~/.claude")
OPS = os.path.join(HOME, "ops")
SKILLS = os.path.join(HOME, "skills")
LESSON_CAP = 30
SIZE_CAP = 18 * 1024   # BYTES per ops/*.md (getsize). REVIEW TRIGGER, not a
                       # budget: ops files are charged only when something
                       # routes to them, and Phase 2 measured the whole
                       # always-loaded surface at ~5% of context and cached, so
                       # bytes here buy nothing worth a hard cap. Firing means
                       # "someone should look at this file", and RAISING IT
                       # AFTER A REVIEW IS THE INTENDED OUTCOME. Provisional.
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
CLAUDE_MD_CAP = 17 * 1024  # BYTES. why/history: ops/rule-registry.md
DICT_CAP = 24 * 1024   # BYTES. REVIEW TRIGGER, not a budget -- same class (b)
                       # reasoning as SIZE_CAP: the dict is charged only on a
                       # routing miss. Raised 20K->24K on 2026-08-15 after
                       # tools/skill-routing-audit.py showed the file's problem
                       # is CONTENT VALIDITY, not volume (0% of actual routing
                       # explained by its own registered vocabulary, except
                       # workflow-checkpoint at 21%). Extracting a file that
                       # measures as fiction would tidy the fiction. Firing
                       # means "review this dict against the audit output".
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
    msgs = []

    # 11. relaxation gate: a project CLAUDE.md without an ops-relaxation: line
    #     means the 05-authority.md §2 question was never asked or recorded.
    #     Model discipline alone proved unreliable at firing that gate (the
    #     trigger asks for a prediction, and the rule lives two conditional
    #     reads deep), so the nudge is moved into the harness. Silent when
    #     there is no project CLAUDE.md (likely not project work) or cwd is
    #     ~/.claude itself (that CLAUDE.md is the global prefs file — the
    #     level there is per-conversation, not a recorded key).
    try:
        raw = sys.stdin.read()
        cwd = json.loads(raw).get("cwd", "") if raw.strip() else ""
    except Exception:
        cwd = ""
    cwd = cwd or os.getcwd()
    try:
        proj_md = os.path.join(cwd, "CLAUDE.md")
        is_home = (os.path.normcase(os.path.abspath(cwd))
                   == os.path.normcase(os.path.abspath(HOME)))
        # SHARE-EDITION SPECIALIZATION (declared in tools/share-manifest.toml;
        # the source environment's copy does NOT have this gate). `ops-relaxation`
        # is a key defined by claude-ops/ops/05-authority.md. Adopting the hooks
        # without adopting the ops layer is a supported outcome of this repo --
        # the lanes are independent -- and an adopter in that position would
        # otherwise be nagged, every session, about a key that is defined nowhere
        # they can read and that no file they own can satisfy. A permanently-on
        # alarm is the one kind nobody reads, and it would train them to ignore
        # the other eleven checks too. Not back-flowed: on the source machine the
        # ops layer is always present, so the same gate would only be able to
        # mask a real ghost-rule failure (check 4's job).
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
                    msgs.append(
                        "project CLAUDE.md has no ops-relaxation: level — "
                        "before heavyweight work, state model identity and "
                        "ask the user to pick L0/L1/L2, then offer to record "
                        "it (ops/05-authority.md §2)"
                    )
    except OSError:
        pass

    # 1. unfolded lesson count
    try:
        with open(os.path.join(OPS, "lessons.md"), encoding="utf-8") as f:
            body = f.read().split("## Archived")[0]
        n = len(re.findall(r"^## L-\d+", body, re.M))
        if n > LESSON_CAP:
            msgs.append(
                f"ops/lessons.md has {n} unfolded entries (>{LESSON_CAP}): "
                "run the trim pass (ops/40-maintenance.md S3)"
            )
    except OSError:
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
            msgs.append(
                f"ops file(s) over {SIZE_CAP // 1024}K bytes: "
                + ", ".join(fat_ops)
                + " — EXTRACT the concrete (examples, command blocks, cases) "
                "to ops/references/ behind a pointer, keep rule+conditions+"
                "routing in place; never compress a rule to fit; if a lossless "
                "pass still misses, RAISE the cap with that pass as evidence "
                "(40-maintenance.md S3)"
            )
    except OSError:
        pass

    # 3. audit-trail staleness
    try:
        trail = os.path.join(OPS, "rule-registry.md")
        idle = (time.time() - os.path.getmtime(trail)) / 86400
        if idle > TRAIL_IDLE_DAYS:
            msgs.append(
                f"rule registry idle {int(idle)}d: run degradation checks "
                "(ops/40-maintenance.md S4)"
            )
    except OSError:
        pass

    # 4. ghost-rule guard: every routed file must exist
    missing = [f for f in ROUTED_FILES
               if not os.path.isfile(os.path.join(OPS, f))]
    if missing:
        msgs.append(
            "OPS.md routing targets missing: " + ", ".join(missing)
            + " — the rules layer is partially dead; fix routing first"
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
            msgs.append(
                "skill description(s) over "
                f"{DESC_CAP} chars: {', '.join(fat_desc)} — slim per "
                "ops/40-maintenance.md S3 budgets"
            )
        if fat_body:
            msgs.append(
                f"SKILL.md over {BODY_CAP} lines: {', '.join(fat_body)} — "
                "move detail to references/ (ops/40-maintenance.md S3)"
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
                msgs.append(
                    f"{fname} {n / 1024:.1f}K over {cap // 1024}K bytes: "
                    f"{hint} (ops/40-maintenance.md S3)"
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
            msgs.append(
                "skill(s) absent from skill-trigger-dict.md: "
                + ", ".join(undicted)
                + " — dict-sync breach (ops/40-maintenance.md S2)"
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
            msgs.append(
                "interop: " + "; ".join(problems)
                + " — run `python interop/interop.py status` for the "
                "authoritative report (it compares commits; this screen only "
                "compared mtimes), then build / curated as it directs"
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
            msgs.append(
                "advisory output(s) still OPEN: "
                + ", ".join(sorted(open_arts))
                + " — carries offers a session may need to act on; read its "
                "status line (rules-usage-dict.md S7)"
            )
        if unstamped:
            msgs.append(
                "advisory output(s) born without a status line: "
                + ", ".join(sorted(unstamped))
                + " — add `> status: ...` in the first 10 lines "
                "(rules-usage-dict.md S7)"
            )
    except OSError:
        pass

    if msgs:
        # stdout on SessionStart is injected as session context
        print("[ops-health] " + " | ".join(msgs[:4]))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # a health nudge must never break session start
