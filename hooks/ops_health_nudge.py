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
  8. skill-trigger-dict.md > 20K BYTES          -> dict extract due
  9. (retired 2026-08-11 -- the trail is frozen, see below)
 10. skills/ dir vs skill-trigger-dict.md drift -> dict-sync breach (40-maintenance S2)
 11. project CLAUDE.md lacks ops-relaxation:    -> relaxation gate never fired
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
SIZE_CAP = 15 * 1024   # BYTES per ops/*.md (getsize). why/history:
                       # ops/rule-registry.md, key `cap measurement unit`
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
CLAUDE_MD_CAP = 15 * 1024  # BYTES. why/history: ops/rule-registry.md
DICT_CAP = 20 * 1024       # BYTES.
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
        if not is_home and os.path.isfile(proj_md):
            with open(proj_md, encoding="utf-8") as f:
                if "ops-relaxation:" not in f.read():
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
    #      routing miss, so the cap is a proxy and the remedy is extraction.
    for fname, cap, hint in (
        ("CLAUDE.md", CLAUDE_MD_CAP,
         "UNCONDITIONAL every-session budget — MERGE into an existing "
         "conditional bullet, or move the rule to a rules/ path-scoped file "
         "or a skill; never append, never compress a rule to fit"),
        ("skill-trigger-dict.md", DICT_CAP,
         "charged on routing miss only — EXTRACT detail behind a pointer; "
         "clarity per read outranks the number"),
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

    if msgs:
        # stdout on SessionStart is injected as session context
        print("[ops-health] " + " | ".join(msgs[:4]))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # a health nudge must never break session start
