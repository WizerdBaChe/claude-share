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

**Do not "improve" these into Grep-tool calls.** The harness's Bash tool
description advises against shell `grep`/`sed`/`find`, under an "unless
explicitly instructed" exemption — this file is that instruction. Grep-only is
the property that makes the sweep cheap enough to run without suspecting
anything is wrong, which is the entire point for a silent failure class.
Recorded 2026-08-14 in `rule-registry.md` → Harness defaults → low-severity
drift, so the exemption is not rediscovered as a violation.

```bash
# 1. subagent definitions that cannot reach any skill (L-014)
grep -L 'Skill' agents/*.md
# 2. phantom tooling in any instruction file — names no tool here provides
#    (40-maintenance and rule-registry quote the names as history; exclude them)
grep -rn "task_memo\|AI Team OS" --include=*.md agents/ skills/ ops/ *.md \
  | grep -v -E '40-maintenance|rule-registry|lessons\.md|integrity-sweep'
# 3. writes aimed at a retired destination (frozen files pass Test-Path, and a
#    RENAMED one does not even do that - the write just fails silently either
#    way, so the instruction reads as correct forever). The log was frozen
#    2026-08-11 and retired to audit-archive/ on 2026-08-15; any surviving
#    mention of the old NAME outside history is a write that will never land.
#    This check found four such files at the freeze and still missed a fifth
#    (skill-share-packaging said "Log the export in ~/.claude/Global_skill_
#    update.md") for four days - so read a hit as guilty until read.
grep -rn "Global_skill_update" --include=*.md agents/ skills/ ops/ *.md \
  | grep -v -E '40-maintenance|rule-registry|frozen|凍結|已凍結|RETIRED|historical|NOT |integrity-sweep'
# and the same question for the CURRENT destinations, which is the general form:
grep -rnE 'Log (the|this|it) .{0,20}in `?~?/?[A-Za-z0-9_./-]+\.md' --include=*.md skills/ agents/ ops/
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
# 12. review triggers: an entry whose value depends on a fact OUTSIDE this repo
#     (harness default, platform capability, vendor doc, unmeasured rate) must
#     carry review-when. Compare the two counts; the gap is the finding. Also
#     catches the pre-2026-08-14 spellings that were never enumerable.
#     ENUMERATE, do not compare two counts. The first version of this check
#     printed `grep -c '^### '` against `grep -c 'review-when:'` and read the
#     difference as the number of uncovered entries. It is not: grep counts
#     LINES, so an entry whose review-when wraps onto a second matching line
#     cancels out an entry that has none. Run 2026-08-15 it reported a gap of 6
#     where the true count was 9 - a proxy spoken in the voice of the thing it
#     stands for, which is L-012 inside the sweep that exists to catch L-012.
python -c "import io,re
t=io.open('ops/rule-registry.md',encoding='utf-8').read()
miss=[p.split('\n')[0][:60] for p in re.split(r'^### ',t,flags=re.M)[1:] if 'review-when:' not in p]
print(f'{len(miss)} entries without review-when:'); [print('  ',m) for m in miss]"
grep -rn 'Re-verify after\|re-verify after\|promote on a second' ops/rule-registry.md \
  | grep -v 'review-when:'
# 12b. unmarked degraded-mode deviations (20-dispatch §1a, L-011 P2)
grep -rn 'DEVIATION:' references/ ops/ --include=*.md
# 13. browser pane guard proof-of-life + the denials the user must adjudicate.
#     An allowlist that never denies and never logs is indistinguishable from a
#     dead hook: rule-registry asserted "every pane navigation is LOGGED" for two
#     days while the file did not exist (found 2026-08-14).
test -f telemetry/browser-nav.jsonl && echo "nav log: present" || echo "nav log: ABSENT - never navigated, or hook dead"
grep -c '"loud": true' telemetry/browser-nav.jsonl 2>/dev/null   # denials awaiting a user call
grep -c 'browser_pane_scope_guard' settings.json                 # still registered?
# 14. fieldwork shadow probe: proof-of-life AND its exit criterion. This one is
#     a ~100ms tax on every Read/Grep/Glob, so an idle probe is pure cost -
#     either it is producing rows to decide on, or it comes off.
test -f telemetry/fieldwork-shadow.jsonl && wc -l < telemetry/fieldwork-shadow.jsonl || echo "no trips recorded yet"
grep -c 'fieldwork_threshold_notice' settings.json
# 15. cap SATURATION, not just breach. ops_health_nudge fires at >cap, which is
#     one edit too late: 40-maintenance.md sat at 99.6% and three separate
#     attempts to add a single field name all breached (T-014). >=95% is the
#     state where the next edit of ANY size is the breach.
#     The cap is READ FROM THE HOOK, never restated here - a literal copy is
#     exactly the defect check 10 exists to catch, and this check would have
#     shipped one (2026-08-15).
#     EVERY capped file must be in this loop. skill-trigger-dict.md was NOT,
#     and sat at 99.5% unseen until an edit tipped it over (2026-08-15) - the
#     saturation check missing the file that saturates is the same blind spot
#     one level up. If ops_health_nudge gains a cap, add it here the same day.
python -c "import os,glob,re
src=open('hooks/ops_health_nudge.py',encoding='utf-8').read()
g=lambda n:int(re.search(n+r' *= *(\d+) *\* *1024',src).group(1))*1024
caps={'CLAUDE.md':'CLAUDE_MD_CAP','skill-trigger-dict.md':'DICT_CAP'}
for f in sorted(glob.glob('ops/*.md'))+list(caps):
    b=os.path.basename(f)
    if b in ('lessons.md','rule-registry.md'): continue
    p=os.path.getsize(f)/g(caps.get(b,'SIZE_CAP'))*100
    if p>=95: print(f'{p:5.1f}%  {f}')"
# 16. hook chain integrity. Every mechanism in this environment depends on one
#     hardcoded absolute interpreter path; if Python moves or is upgraded, all
#     of them fail SILENTLY and nothing else in the tree would notice.
python -c "import json,os,re,glob
d=json.load(open('settings.json',encoding='utf-8'))
paths=set(); interp=set()
for arr in d['hooks'].values():
    for e in arr:
        for h in e.get('hooks',[]):
            m=re.findall(r'\"([^\"]+)\"',h.get('command',''))
            if m: interp.add(m[0]); paths.update(m[1:])
for i in interp:
    if not os.path.exists(i): print('DEAD INTERPRETER:',i)
for p in paths:
    if not os.path.exists(p): print('DEAD HOOK TARGET:',p)
on={os.path.basename(f) for f in glob.glob('hooks/*.py')}
print('unregistered hook files:',sorted(on-{os.path.basename(p) for p in paths}) or 'none')"
# 17. corpus counts asserted in prose vs reality. A number written into a rule
#     file is a claim with no owner; `20-dispatch.md` said "9 定義" for two days
#     after management-tech-lead was archived, leaving 8 (found 2026-08-14).
#     Print both and compare by eye - the fix is usually to delete the number.
ls -1 agents/*.md | wc -l; grep -rnE '[0-9]+ 個定義|[0-9]+ (agent|skill|lesson) definitions' ops/ --include=*.md
ls -1 skills/*/SKILL.md | wc -l; grep -n '^## L-[0-9]' ops/lessons.md | wc -l
# 18. routing dictionary vs reality. skill-trigger-dict.md asserts, per skill,
#     which words route to it, and nothing ever checked the assertion. Measured
#     2026-08-15: the dict explained 0% of actual fires for every entry except
#     workflow-checkpoint (21%), while config-self-audit fired 28x on
#     vocabulary the dict does not list. Not a grep - it needs the transcripts.
python tools/skill-routing-audit.py --surface
# read the FIRING ANYWAY block first: an entry with fires and 0 coverage means
# the dict records words nobody says. A DEAD entry that never fired is only a
# skill whose occasion has not arisen, which is not a defect.
# --surface adds check 18b (added 2026-08-15): every zero is annotated with the
# trigger CLASS from ops/references/skill-trigger-classes.md, so an expected
# quiet skill stops printing like a bug, and each description's PROCEDURE share
# is measured. Procedure on a routing surface is charged in every session and
# buys no routing; three skills carried 27-34% of it before this check existed.
# Act on: any SATURATED row (>=95% of DESC_CAP, the check-15 failure one level
# down), any STALE fragment (the description moved and the classification did
# not), and any NOT CLASSIFIED skill. The proc% itself is a review prompt, not a
# threshold - do not trim prose to lower it (P-003); move it into the body,
# which loads on invoke anyway.
# 19. UNDO PATHS verified enabled, in advance. Every other recovery record in
#     this environment is about reverting a DELIBERATE change - rule-registry
#     `rollback:`, work-card Rollback, backups/<date>/, "git IS the backup".
#     None of them checks that the seconds-to-minutes undo paths are switched
#     ON, and all of them are worthless if enabled after the incident. This
#     environment has already been close: 40-maintenance.md records that
#     backups/ and memory-archive/ were once the SOLE surviving copies.
#     Derived from ai-coding-guardrails section 8, whose MVG is exactly "verify
#     TODAY" - the one of its nine sections not already covered by an always-on
#     rule (coverage table: references/claude-config-tickets.md T-017).
git reflog --date=iso | tail -1        # oldest entry = the REAL retention window
git config --get gc.reflogExpire || echo 'reflogExpire UNSET (default 90d)'
git config --get gc.reflogExpireUnreachable || echo 'unreachable UNSET (30d)'
ls -dt ~/.claude/backups/*/ 2>/dev/null | head -3   # -t: newest FIRST, and the
# trailing slash drops loose files. Sorting these by NAME was the first version
# of this check and it silently reported the alphabetically-last batch as the
# newest (2026-08-15).
# Act on: a reflog whose oldest entry is younger than the window you assumed;
# reflogExpire left at the default on a repo where a bad reset would be found
# later than that; a newest backup batch older than the last red-tier edit.
# Baseline 2026-08-15: reflog reaches the initial commit (2026-07-06, 40 days,
# nothing expired yet) and both expiry knobs are at defaults - so the 90-day
# horizon has simply not arrived. Re-read this check when the repo passes 90
# days (2026-10-04), which is when the defaults start actually deleting.
# For PROJECT repos the same questions belong to the audit skill, not here -
# security-deep-checklist Mode C section 6.
# 20. shadow probes still in shadow. THREE gates run in measure-only mode
#     (delivery_gate_shadow.py, fieldwork_threshold_notice.py,
#     context_runway_shadow.py). None can
#     ever announce that it is DUE for review: a probe that is working
#     correctly is silent, so "the review never happened" emits no event --
#     the same omission shape as check 19, and the reason this is a sweep item
#     rather than a note in a ticket. T-009 and T1 both stay open by design;
#     what must not happen is them going quiet and being read as finished.
python tools/e2-gate-test/check_shadow_log.py -n 40 --commands
python - <<'PY'
import json, io
p = "telemetry/fieldwork-shadow.jsonl"
rows = [json.loads(l) for l in io.open(p, encoding="utf-8") if l.strip()]
print(f"fieldwork rows: {len(rows)}  (classified in rule-registry -> dispatch)")
PY
python - <<'PY'
import json, io, os, collections
p = "telemetry/context-runway-shadow.jsonl"
rows = [json.loads(l) for l in io.open(p, encoding="utf-8") if l.strip()] if os.path.isfile(p) else []
b = collections.Counter(r.get("band") for r in rows)
print(f"context-runway rows: {len(rows)}  by band: {dict(b)}")
# Judge the WORDING, not the number: a row is a true positive only if a
# checkpoint was actually wanted at that moment. Read `wording` in the row.
PY
#     ROW COUNT IS NOT PROOF OF LIFE for this one, and that is the whole point
#     of the probe's own design: its conjunction suppresses it in exactly the
#     sessions that behaved well, so "0 rows" and "dead hook" look identical.
#     Checks 13 and 14 have the same weakness and got away with it because
#     their subjects produce rows routinely. Drive it instead: feed it a
#     transcript known to satisfy both conditions and require a row. The log is
#     redirected, so this never touches production telemetry - running the hook
#     bare once leaked a synthetic row into a real log (2026-08-15, P-005).
#     Scope of the assertion, stated because it is easy to over-read: driving
#     the hook end-to-end proves it RUNS and WRITES. It does not prove the
#     predicates are right - the input is chosen with those same predicates.
#     Whether a row landed at a moment a checkpoint was wanted is the reader's
#     job, above. A hand-rolled selector was tried first and picked a
#     transcript that failed both conditions, reporting DEAD for a working
#     probe (2026-08-15) - so the selector uses the shipped functions.
python - <<'PY'
import json, os, subprocess, sys, tempfile, glob
sys.path.insert(0, os.path.expanduser("~/.claude/hooks"))
import context_runway_shadow as m
from pathlib import Path
big = None
for p in sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))):
    if os.path.getsize(p) < 1_000_000:
        continue
    if m.context_total(Path(p)) >= min(m.BANDS) and not m.checkpoint_written(Path(p)):
        big = p; break
if not big:
    print("context-runway proof-of-life: SKIPPED (no qualifying transcript)"); sys.exit()
d = tempfile.mkdtemp()
env = dict(os.environ, CONTEXT_RUNWAY_LOG=os.path.join(d, "l.jsonl"), CLAUDE_CONFIG_DIR=d)
subprocess.run([sys.executable, os.path.expanduser("~/.claude/hooks/context_runway_shadow.py")],
               input=json.dumps({"session_id": "sweep-probe", "cwd": "x", "transcript_path": big}),
               text=True, env=env, capture_output=True)
n = sum(1 for _ in open(os.path.join(d, "l.jsonl"), encoding="utf-8")) if os.path.isfile(os.path.join(d, "l.jsonl")) else 0
print("context-runway proof-of-life:", "ALIVE" if n else "DEAD - it did not fire on a transcript that satisfies both conditions")
PY
# Reviewed baselines - compare, then APPEND a new line here after each review:
#   2026-08-15 delivery gate: 9 dispatches, 3 would-block, 8 organic / 2 FP / 0 TP
#   2026-08-15 fieldwork:     3 rows, 3 false positives, 2 were source defects
#   2026-08-15 context-runway: 0 rows, wired this day. Replay over 149 archived
#     sessions predicts 59% of sessions get >=1 notice at bands (150k, 300k) --
#     deliberately liberal because a shadow row costs nothing and the point of
#     the window is to find the band worth graduating, not to be right now.
#     (200k, 400k) would give 40%, (250k, 500k) 29%: pick from ROWS, not here.
# Act on: new dispatches since the last baseline. Both probes' errors so far
# were about WHAT COUNTS as the triggering event, never about a threshold, and
# both were found by reading rows -- so read the rows, do not re-reason about
# the numbers. Graduate only on an organic TRUE positive; if a probe accrues
# only false positives, the finding is that it cannot be a gate, and it comes
# OFF rather than being tuned until it agrees.
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
