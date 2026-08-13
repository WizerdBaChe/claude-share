# Integrity sweep — the executable checks

Detail file for `40-maintenance.md` §5. The RULE (when to run, why it exists as
grep rather than a skill) stays in §5; this file holds the checks themselves and
the evidence that motivated them. Loaded on demand, never at session start.

## Why this gap exists (the measured case)

Neither audit skill covers it, and the gap is measured, not theoretical:
`config-self-audit` audits ONE artifact **named or just created** and refuses to
widen ("not the whole config tree"); `env-cleanup` sweeps the whole tree but is
**file-level only** ("no content edits", classification by presence and
orphanhood). So an artifact that is legitimately PRESENT and correctly
REFERENCED, but whose CONTENT is wrong, is invisible to both.

The 22 inherited `agents/*.md` definitions lived in exactly that gap for 37 days
(2026-07-06 → 2026-08-12) while instructing every dispatched subagent to call
tools that do not exist.

## The checks

Grep-only, seconds, no judgement — each line either returns nothing or returns a
defect. Extend the list when a new silent-failure class is found; record the
motivating case here beside the check.

```bash
# 1. subagent definitions that cannot reach any skill (L-014)
grep -L 'Skill' agents/*.md
# 2. phantom tooling in any instruction file — names no tool here provides
#    (40-maintenance and rule-registry quote the names as history; exclude them)
grep -rn "task_memo\|AI Team OS" --include=*.md agents/ skills/ ops/ *.md \
  | grep -v -E '40-maintenance|rule-registry|lessons\.md|integrity-sweep'
# 3. writes aimed at a retired destination (frozen files pass Test-Path)
grep -rn "Global_skill_update" --include=*.md agents/ skills/ ops/ *.md \
  | grep -v -E '40-maintenance|rule-registry|frozen|凍結|已凍結|RETIRED|historical|NOT |integrity-sweep'
# 4. agent colors outside the eight documented values
grep -h '^color:' agents/*.md | sort -u | grep -vE 'red|blue|green|yellow|purple|orange|pink|cyan'
# 5. lessons ledger: an entry with no hits: field is invisible to the
#    "2nd time" rule and to §4.4 — the two counts must be equal
grep -c '^## L-[0-9]' ops/lessons.md; grep -c '^## L-[0-9].*hits:' ops/lessons.md
# 6. reverse references: an agentType the routing table names but no file defines
grep -oE '`[a-z-]+`' ops/20-dispatch.md | tr -d '`' | sort -u > /tmp/named.txt
grep -h '^name:' agents/*.md | sed 's/name: //' | sort -u > /tmp/defined.txt
# compare by eye; built-ins (Explore/Plan/general-purpose) legitimately have no file
# 7. cap unit drift: the §3 table and the hook must measure the same way
grep -nE 'getsize|len\(text\)|len\(m\.group|count\("' hooks/ops_health_nudge.py
# 8. filenames that mint a label (LABEL-REGISTRY §4.3) — abbreviation happens
#    while naming a file, which is where no rule is looking
ls references/ skills/*/references/ 2>/dev/null \
  | grep -E "L[0-9]|R[0-9]|Tier[- ]?[0-9]|Mode[- ]?[A-Z]|AD[0-9]"
# 9. tier-3 inbound surface — ops_health_nudge checks 5 and 10 walk
#    ~/.claude/skills/ only, so plugin descriptions over the 800 cap and
#    plugin/local trigger collisions are invisible to it
#    (inbound-routing.md; count was 50 files / 15,664 desc chars on 2026-08-12)
find "$APPDATA/Claude/local-agent-mode-sessions" -name SKILL.md 2>/dev/null | wc -l
# 10. cap VALUE drift across mechanisms — check 7 catches the unit, not the
#     number, and a second mechanism holding its own copy is how a phantom
#     breach survived 12 days (see below). Every cap literal outside the
#     owning hook must be a declared fallback, never a live value.
grep -rnE '_CAP[A-Z_]* *= *[0-9]+ *\* *1024' tools/ hooks/ --include=*.py \
  | grep -v 'ops_health_nudge\|CAP_FALLBACKS'
# 11. unsettled values: every threshold still running on a guess. Non-empty is
#     NORMAL (a declared guess beats a silent one); the finding is an entry
#     whose evidence has not gained a line in months, or a guess in the tree
#     with NO registry entry at all (nowhere for the data to land).
grep -n "PROVISIONAL" ops/rule-registry.md
grep -rn "provisional\|not measured" ops/ --include=*.md | grep -v rule-registry
```

## Check 7's rationale (added 2026-08-12)

`40-maintenance.md` §3 said "~12K **chars**" while `hooks/ops_health_nudge.py`
measured `os.path.getsize()` = **bytes**. For CJK-dense files the two diverge by
up to 1.7×: `skill-trigger-dict.md` read as 98% of cap in bytes and 58% in
chars. The rule text says "change the two together"; nothing enforced it. Bytes
won on evidence (see `rule-registry.md`, key `cap measurement unit`) and the
table was corrected — but the drift was silent for as long as it existed, which
is what makes it a sweep item rather than a one-off fix.

## Check 10's rationale (added 2026-08-13)

Check 7 compares how the hook MEASURES against how §3 says to measure. It is
blind to a second mechanism holding its own copy of the VALUE, which is the
larger class: `tools/project-dashboard.py` carried three stale caps at once —
`ops/*.md` at 10K (two raises behind), `CLAUDE.md` at 12K (one raise behind,
so the dashboard printed "CLAUDE.md 15,084B (123% of 12K cap)", a breach that
did not exist, for 12 days), and a cap on `Global_skill_update.md` which was
retired from capping on 2026-08-11. Only `DICT_CAP` happened to still match.

The fix was not to correct the three numbers — that repeats in six weeks. The
dashboard now DERIVES the caps from the hook by parsing it (importing would
break its stdlib-single-file INV-4), keeps them only as declared fallbacks, and
announces a parse failure instead of silently reverting to them. This check
exists for the remaining hole in that arrangement: a fourth mechanism appearing
later with its own literal, or a constant rename that makes the parse fall back
forever. Third recurrence of the constant-binding class, and the first found in
a RENDERER rather than a rule file.
