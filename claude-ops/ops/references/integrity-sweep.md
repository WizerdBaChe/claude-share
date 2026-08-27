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
# 5b. (2026-08-21; id SETS, not counts, since 2026-08-27) the ledger is a CARD
#     file; the full record of every entry is ops/references/lessons-detail.md
#     under the same heading, written in the SAME COMMIT as the card. Folding
#     an entry (the ledger's Archived section) removes its card, never its
#     section — so a detail section may legitimately outlive its card, and
#     equal counts were never the invariant. They already lied once: after the
#     2026-08-27 trim both files counted 29 while six ids differed EACH WAY
#     (folded 002/003/004/013/026/029 detail-only; 030–035 born card-only with
#     no full record) and the count form of this check passed over it. Same
#     proxy defect check 12 records — ENUMERATE, do not compare two counts.
comm -23 <(grep -oE '^## L-[0-9]+' ops/lessons.md | tr -d '# ' | sort) \
         <(grep -oE '^## L-[0-9]+' ops/references/lessons-detail.md | tr -d '# ' | sort)
# ^ live cards whose full record was never written — must print nothing
for id in $(comm -13 <(grep -oE '^## L-[0-9]+' ops/lessons.md | tr -d '# ' | sort) \
                     <(grep -oE '^## L-[0-9]+' ops/references/lessons-detail.md | tr -d '# ' | sort)); do
  grep -qE "^- \*\*$id\b" ops/lessons.md || echo "$id: full record but no live card and no Archived bullet"
done
# ^ records whose id left the ledger entirely (a fold keeps a bullet) — must
#   print nothing. Calibrated two-sided 2026-08-27: pre-backfill tree fired
#   L-030..L-035 on the first arm; synthetic L-999 fires the second; the six
#   folded ids stay silent (their bullets exist).
grep -c '^## L-[0-9].*hits:' ops/references/lessons-detail.md   # must be 0 — hits: is
#     card-only; detail headings carry "(full record)" in its place, on purpose
# 6. reverse references: an agentType the routing table names but no file defines
grep -oE '`[a-z-]+`' ops/20-dispatch.md | tr -d '`' | sort -u > /tmp/named.txt
grep -h '^name:' agents/*.md | sed 's/name: //' | sort -u > /tmp/defined.txt
# compare by eye; built-ins (Explore/Plan/general-purpose) legitimately have no file
# 7. cap UNIT drift: the §3 table and the hook must measure the same way.
#    This check can only ever see the unit — it is a grep for the measuring
#    call. For nine months §3's "Constant binding" bullet named it as *the*
#    drift check for thresholds that live in both rule text and a mechanism,
#    which read as though the VALUE were covered too. It was not: on
#    2026-08-27 three constants were found drifted across four sites
#    (DICT_CAP 28K/24K/20K, CLAUDE_MD_CAP 19968/15K, SIZE_CAP 22K/15K), with
#    skill-trigger-dict.md sitting 2.6K over the enforced cap while every rule
#    file a reader might consult said it was fine. Hence 7b.
grep -nE 'getsize|len\(text\)|len\(m\.group|count\("' hooks/ops_health_nudge.py
# 7b. cap VALUE drift: every site that RESTATES a cap vs the mechanism that
#     enforces it. Reads the hook by AST (so `28 * 1024` and `19968` both
#     parse) and compares §3's tables and rule-registry's `current:` lines
#     against it. Exit 1 = a value drifted; exit 2 = a binding lost its anchor
#     (a site was retitled) — never silence, which is how the drift above
#     survived. `--selftest` runs the two-sided calibration: a known-TRUE input
#     that must come back clean AND four known-FALSE inputs that must each be
#     caught. Run --selftest after touching the script; it caught two real
#     defects in the checker itself on its first two runs.
python tools/ops-health-test/check_cap_binding.py
# Act on: DRIFT — the MECHANISM is the source of truth, so correct the rule
# text, never the hook, unless the value itself is being changed on purpose.
# ANCHOR LOST — a site moved; re-point the binding in BINDINGS, do not delete
# it. The stronger fix, where the site is inside a mechanism, is to DELETE the
# restatement: the hook's docstring names its constants instead of copying
# their values, which is why 7b asserts an absence there.
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
#     READ THE CAP BY AST, not by regex. The first version matched
#     `NAME = (\d+) * 1024` and CRASHED with AttributeError from 2026-08-18 -
#     the day CLAUDE_MD_CAP became a plain `19968` - until 2026-08-27, so for
#     nine days it covered neither CLAUDE.md nor skill-trigger-dict.md (they
#     are last in the loop, after the crash). A check whose failure mode is a
#     traceback in the middle of a sweep is a check nobody notices losing.
python -c "import os,glob,sys
sys.path.insert(0,'tools/ops-health-test')
from check_cap_binding import hook_caps
g=hook_caps(open('hooks/ops_health_nudge.py',encoding='utf-8').read())
caps={'CLAUDE.md':'CLAUDE_MD_CAP','skill-trigger-dict.md':'DICT_CAP'}
for f in sorted(glob.glob('ops/*.md'))+list(caps):
    b=os.path.basename(f)
    if b in ('lessons.md','rule-registry.md'): continue
    p=os.path.getsize(f)/g[caps.get(b,'SIZE_CAP')]*100
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
# 21. ps-errorpref guard proof-of-life (L-011 COST OF P1/P3, born with the hook
#     2026-08-21). This guard NEVER denies, so a dead one is completely silent:
#     no denial, no retry, no complaint -- exactly the shape it exists to fix,
#     one level up. And row count alone cannot tell "dead" from "nobody wrote a
#     hazardous .ps1 this month": the backtested rate is 0.375 fires/DAY, so a
#     quiet fortnight is normal. Hence the same treatment as check 20: DRIVE it.
grep -c 'ps_errorpref_guard' settings.json          # still registered?
test -f telemetry/ps-errorpref-guard.jsonl && wc -l < telemetry/ps-errorpref-guard.jsonl \
  || echo "eap log: ABSENT - no hazard written since 2026-08-21, or hook dead"
#     Every row is organic by construction: the log path is redirected for the
#     suite and for the drive below, and case E2 asserts production gained
#     nothing. That is why there is no "discount the first N rows" caveat here
#     and there is one on shell_transport_guard. Pre-redirect rows (112 of 113
#     synthetic) are parked in archive/2026-08-21-eap-guard/ with a note.
python - <<'PY'
import json, os, subprocess, sys, tempfile
d = tempfile.mkdtemp()
log = os.path.join(d, "l.jsonl")
hook = os.path.expanduser("~/.claude/hooks/ps_errorpref_guard.py")
payload = {"tool_name": "Write", "session_id": "sweep-probe", "cwd": "x",
           "tool_input": {"file_path": "C:/tmp/sweep.ps1",
                          "content": "$ErrorActionPreference = 'Stop'\ngit status\n"}}
r = subprocess.run([sys.executable, hook], input=json.dumps(payload), text=True,
                   capture_output=True, env=dict(os.environ, PS_ERRORPREF_LOG=log))
fired = "additionalContext" in (r.stdout or "")
rows = sum(1 for _ in open(log, encoding="utf-8")) if os.path.isfile(log) else 0
print("ps-errorpref proof-of-life:",
      "ALIVE" if (fired and rows) else "DEAD - it did not annotate EAP=Stop + git")
PY
#     Scope of that assertion, stated because it is easy to over-read: driving
#     the hook proves it RUNS, ANNOTATES and WRITES. It does not prove the
#     predicates are right -- the input is chosen with those same predicates.
#     For that, re-run the two-sided suite and the corpus backtest:
python tools/ps-errorpref-test/test_ps_errorpref_guard.py    # must be 45/45
python tools/ps-errorpref-backtest/backtest.py --sample 4
#     Act on: a registration count of 0; ALIVE but the suite failing (the
#     detector drifted from its calibration); a backtest fire rate far from the
#     recorded 0.60% of inspected payloads, which means the corpus changed shape
#     or a regex over-matched; or the Edit/Bash rows in the backtest table
#     accumulating fires while still unregistered -- that is the evidence that
#     was supposed to reopen the matcher decision (rule-registry review-when).

# 22. session-board registration proof-of-life (L-011 COST OF P1/P3, born with
#     the hook 2026-08-21). This hook is fail-open and SILENT BY DESIGN: it
#     prints nothing, never blocks a dispatch, and its whole job is to write a
#     row into a file nobody looks at until they need it. A dead one is
#     therefore invisible until the board reports UNBOUND for a ticket that was
#     dispatched an hour ago -- and UNBOUND reads as a tooling bug, not as a
#     missing entry, which is precisely why the prose rule it replaced rotted.
#     Rate is ~6 dispatches/day at the 2026-08-21 baseline, so a quiet day is
#     normal and row count alone cannot tell dead from idle. DRIVE it.
grep -c 'session_board_register' settings.json      # still registered? (want 1)
test -f telemetry/session-board-register.jsonl && wc -l < telemetry/session-board-register.jsonl \
  || echo "register log: ABSENT - no dispatch since 2026-08-21, or hook dead"
#     The three rows that mean something is wrong, all of them silent otherwise:
grep -c '"task_id_unread": true' telemetry/session-board-register.jsonl   # response shape changed
grep -c '"outcome": "lock-timeout"' telemetry/session-board-register.jsonl # contention beat the lock
grep -c '"outcome": "unparsable-registry"' telemetry/session-board-register.jsonl # tickets.json broke
python - <<'PY'
import json, os, subprocess, sys, tempfile
d = tempfile.mkdtemp()
reg = os.path.join(d, "tickets.json"); log = os.path.join(d, "l.jsonl")
open(reg, "w", encoding="utf-8").write("[]")
hook = os.path.expanduser("~/.claude/hooks/session_board_register.py")
env = dict(os.environ, SESSION_BOARD_TICKETS=reg, SESSION_BOARD_LOG=log)
def drive(payload):
    subprocess.run([sys.executable, hook], input=json.dumps(payload), text=True,
                   capture_output=True, env=env)
    return json.load(open(reg, encoding="utf-8"))
# known-TRUE: a dispatch MUST register.
# The id must be HEX. The hook's parser is deliberately tight (all 32 ids in the
# corpus are 8 hex chars) so it cannot lift a fabricated id out of surrounding
# prose. The first draft of this probe used `task_5weep0be` and correctly got
# DEAD -- the probe was wrong, not the hook.
rows = drive({"tool_name": "mcp__ccd_session__spawn_task", "session_id": "sweep",
              "cwd": "x", "tool_input": {"title": "sweep probe",
              "cwd": "X:/proj", "prompt": "Sweep probe opening line, distinctive."},
              "tool_response": "Noted (position 1, task_id: task_5eeeb0be)."})
ok_pos = len(rows) == 1 and rows[0]["deliverables"] is None
# known-FALSE: an unrelated call MUST NOT. A one-sided probe would pass for a
# hook that registered everything (global CLAUDE.md gate rule).
rows = drive({"tool_name": "Write", "session_id": "sweep", "cwd": "x",
              "tool_input": {"file_path": "x.md", "content": "task_5weep0be"},
              "tool_response": "ok"})
ok_neg = len(rows) == 1
print("session-board register proof-of-life:",
      "ALIVE" if (ok_pos and ok_neg) else
      ("DEAD - dispatch did not register" if not ok_pos else
       "BROKEN - it registered a non-dispatch"))
PY
#     Scope, stated so it is not over-read: driving it proves the hook RUNS,
#     PARSES the id, WRITES null deliverables and IGNORES other tools. It does
#     not prove it is mounted on the right EVENT -- only a real dispatch does
#     that, and the row it leaves in the production log is the evidence. For
#     the rest, re-run the two-sided suite and the board's own self-test:
python tools/session-board-test/test_session_board_register.py   # must be 65/65
powershell -NoProfile -File tools/session-board/session-board.ps1 -SelfTest
#     must be 29 passed / 0 failed, or 27 passed / 0 failed / 2 SKIPPED when no
#     claude session is live on the machine (the last two are live controls;
#     SKIP is their "premise absent" verdict, never a FAIL -- 2026-08-22)
#     Act on: a registration count of 0 (unregistered, and every dispatch since
#     is unrecorded); any task_id_unread row (the harness changed its response
#     and the hook is now writing nothing at all); any lock-timeout row (raise
#     LOCK_TIMEOUT or look for a wedged writer); any unparsable-registry row
#     (tickets.json is broken and has been rejecting writes silently since);
#     ALIVE but a suite failing (the hook drifted from its calibration); or a
#     tickets.json that has stopped gaining entries while spawn_task calls keep
#     appearing in `python tools/session-board/sweep-dispatch-surface.py`.

# 23. ps-pipeline-close guard proof-of-life (L-011 COST OF P1/P3, born with the
#     hook 2026-08-21). Same silence problem as check 21 and one worse: this
#     guard never denies AND its trap is invisible when it does happen -- a
#     killed upstream shows up as truncated output plus a failure exit code,
#     both of which read as the program's own fault (that is what cost L-027 two
#     diagnosis rounds). So a dead guard here is indistinguishable from a month
#     of correct pipelines. Backtested rate is 1.79 fires/day, which is high
#     enough that a WEEK of zero rows is itself the signal. DRIVE it.
grep -c 'ps_pipeline_close_guard' settings.json     # still registered? (want 1)
test -f telemetry/ps-pipeline-close.jsonl && wc -l < telemetry/ps-pipeline-close.jsonl \
  || echo "pipeline-close log: ABSENT - no hazardous pipeline since 2026-08-21, or hook dead"
python - <<'PY'
import json, os, subprocess, sys, tempfile
d = tempfile.mkdtemp(); log = os.path.join(d, "l.jsonl")
hook = os.path.expanduser("~/.claude/hooks/ps_pipeline_close_guard.py")
env = dict(os.environ, PS_PIPECLOSE_LOG=log)
def drive(cmd):
    r = subprocess.run([sys.executable, hook], text=True, capture_output=True, env=env,
                       input=json.dumps({"tool_name": "PowerShell", "session_id": "sweep-probe",
                                         "cwd": "x", "tool_input": {"command": cmd}}))
    return "additionalContext" in (r.stdout or "")
# known-TRUE: an interpreter killed by an early-closing consumer MUST annotate.
pos = drive("python tools/<script>.py | Select-Object -First 30")
# known-FALSE: a cmdlet upstream MUST NOT. A one-sided probe passes for a hook
# that annotates every pipeline (global CLAUDE.md gate rule).
neg = drive("Get-ChildItem -Recurse | Select-Object -First 30")
rows = sum(1 for _ in open(log, encoding="utf-8")) if os.path.isfile(log) else 0
print("ps-pipeline-close proof-of-life:",
      "ALIVE" if (pos and not neg and rows == 1) else
      ("DEAD - it did not annotate interpreter|Select-Object -First" if not pos else
       "BROKEN - it annotated a pure-cmdlet pipeline"))
PY
#     Every production row is organic by construction: the log path is redirected
#     for the suite, for this probe, and for the backtest, so there is no
#     "discount the first N rows" caveat to remember (contrast
#     shell_transport_guard, integrity-sweep check 20 / P-005).
#     Scope of the assertion, stated because it is easy to over-read: driving it
#     proves the hook RUNS, ANNOTATES, STAYS SILENT on a cmdlet and WRITES one
#     row. It does not prove the tier tables are right -- the inputs are chosen
#     with the same predicates. For that, re-run the two-sided suite and the
#     corpus backtest:
python tools/ps-pipeline-close-test/test_ps_pipeline_close_guard.py   # must be 49/49
python tools/ps-pipeline-close-backtest/backtest.py --sample 4
#     Act on: a registration count of 0; ALIVE but the suite failing (the
#     detector drifted from its calibration); a backtest fire rate far from the
#     recorded 2.93% of inspected payloads; Write/Edit/Bash rows appearing in the
#     backtest table while still unregistered (that is the evidence that reopens
#     the matcher decision); or -- the one specific to this guard -- a SUPPRESSED
#     upstream that can MUTATE something, which means a name is mis-tiered and
#     belongs in TIER_WORK.

# 24. stale-work nudge (ops_health_nudge.py check 14, born 2026-08-21). The ONE
#     check in that hook that runs a subprocess (git), and the one whose silence
#     is ambiguous: "no stale paths", "git failed" and "git timed out" all print
#     the same nothing, by design (fail-open). So do not read a quiet session
#     start as "nothing stale". DRIVE it: the two-sided suite builds a real repo
#     in a fake home and back-dates paths with os.utime (known-TRUE: a 5-day-old
#     untracked path and a 5-day-old tracked modification MUST fire; known-FALSE:
#     a fresh path, a clean repo, no repo at all, a project cwd MUST stay quiet).
python tools/ops-health-test/test_ops_health_nudge.py          # must be 28/28
#     Then look at the live tree the way the hook does, unscoped:
git -C ~/.claude status --porcelain --untracked-files=all | wc -l
#     Act on: a suite failure; the SAME stale paths reported at session start for
#     a week (the nudge is being read past -- L-011's "notice nobody reads"; the
#     remedy is to commit or hand them off, never to raise STALE_WORK_DAYS); a
#     firing rate near zero for months (retire the check, per its registry
#     entry -- do not tune it); or this repo gaining a remote (review-when: the
#     backpressure source changes and the threshold is re-judged). The threshold
#     is PROVISIONAL; each real firing is recorded as one line in
#     ops/rule-registry.md key `stale uncommitted work`.
# 25. Playwright MCP server proof-of-life (born 2026-08-23, TRIAL; narrowed to
#     one server 2026-08-25 — `playwright-chrome` removed, see rule-registry).
#     `playwright-headless` (installed Chrome, no window) points at a durable
#     install under tools/playwright-mcp/. If the install rots (node_modules
#     gone, Chrome channel missing, ~/.claude.json entry lost) the name simply
#     vanishes from the session's tool list - nothing announces it.
test -f tools/playwright-mcp/node_modules/@playwright/mcp/cli.js && echo "pw-mcp install: present" || echo "pw-mcp install: ABSENT - re-install per tools/playwright-mcp/README.md"
claude mcp get playwright-headless 2>&1 | grep -E "Status"     # expect: Connected
#     Act on: ABSENT / not Connected -> README re-install + re-register; the
#     user's ~10% per-turn cost ruling breached on a re-measure (baseline
#     method: tools/playwright-mcp/README.md) -> `claude mcp remove
#     playwright-headless -s user`. Rule-registry key `Playwright MCP`.

# 26. graph rot watchdog proof-of-life (born 2026-08-26 with ops-health check
#     15). The carrier is a daily scheduled task, and a dead task is silent in
#     exactly the way the watchdog exists to prevent; check 15's "silent too
#     long" line covers session-start, this item covers "is the machinery
#     itself still there".
schtasks /Query /TN "ClaudeGraphSnapshotWatchdog-Daily" /FO LIST | findstr "Status Next"   # task exists, next run scheduled
python -X utf8 tools/graph-snapshot/gs_watchdog.py     # manual run: exit 0, or 3 = standing finding
python -X utf8 tools/graph-snapshot/tests/test_smoke.py   # 41 checks; 6 drive evaluate() two-sided
#     Act on: the task missing or its Last Result nonzero (re-register per
#     tools/graph-snapshot/watchdog-task.ps1 header); watchdog-status.json
#     mtime > 3 days while check 15 says nothing at session start (the hook
#     edit was lost — restore check 15); a FINDING standing for days with no
#     harvest (run the graph-query skill's J3 flow). Rule-registry key
#     `graph rot watchdog`.
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
