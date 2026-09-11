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
#    Scope widened 2026-09-01: references/ rules/ interop/ tools/ added — the
#    original scope excluded where such mentions actually live (same defect
#    class as LABEL-REGISTRY §5, found by the gate-integrity audit).
grep -rn "task_memo\|AI Team OS" --include=*.md agents/ skills/ ops/ references/ rules/ interop/ tools/ *.md \
  | grep -v -E '40-maintenance|rule-registry|lessons\.md|integrity-sweep|decisions\.md|phase-log|session-digest|graph-snapshot/out'
# 3. writes aimed at a retired destination (frozen files pass Test-Path, and a
#    RENAMED one does not even do that - the write just fails silently either
#    way, so the instruction reads as correct forever). The log was frozen
#    2026-08-11 and retired to audit-archive/ on 2026-08-15; any surviving
#    mention of the old NAME outside history is a write that will never land.
#    This check found four such files at the freeze and still missed a fifth
#    (skill-share-packaging said "Log the export in ~/.claude/Global_skill_
#    update.md") for four days - so read a hit as guilty until read.
grep -rn "Global_skill_update" --include=*.md agents/ skills/ ops/ references/ rules/ interop/ tools/ *.md \
  | grep -v -E '40-maintenance|rule-registry|frozen|凍結|已凍結|RETIRED|historical|NOT |integrity-sweep|decisions\.md|phase-log|session-digest|graph-snapshot/out'
# and the same question for the CURRENT destinations, which is the general form:
grep -rnE 'Log (the|this|it) .{0,20}in `?~?/?[A-Za-z0-9_./-]+\.md' --include=*.md skills/ agents/ ops/
# 4. agent colors outside the eight documented values
grep -h '^color:' agents/*.md | sort -u | grep -vE 'red|blue|green|yellow|purple|orange|pink|cyan'
# 5. (2026-09-07, closeout-capture cutover) the lessons ledger is ops/lessons/
#    — one intake record per file, born only through
#    tools/closeout-intake/intake.py — and ops/lessons.md is GENERATED from
#    it. One tool run replaces the four greps that used to live here: INV-1
#    every record still parses and validates; INV-2 no record body differs
#    from HEAD outside its ## Events tail and the status: projection line;
#    INV-4 hits/state in every card equal what its events derive; INV-5 the
#    index equals a fresh render (generated-from hash); INV-6 every record
#    carries a locator. Must print nothing and exit 0.
# SHARE EDITION: tools/closeout-intake/ does not ship in this repo -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (source-environment-only
# CLI and store). Both commands below always fail in this share; there is no
# adopter-side equivalent to run in their place.
python tools/closeout-intake/intake.py check --against HEAD --index
# ^ calibrated two-sided in controls.py: C-11 (a planted invalid file), C-21
#   (a hand-edited Pitfall), C-22 (status: contradicting the events), C-23 (an
#   Events line removed) and C-51 (a hand-edited index) each drive exit 4;
#   C-20 (a tool-driven event) stays silent.
# 5b. the guard's proof-of-life (INV-9): hooks/intake_guard.py DENIES direct
#     writes to those paths, and a guard that stopped firing is one nobody
#     notices. The harness's last line must read `ALL PASS n/n`; among its
#     cases C-90 (Write to ops/lessons/L-999.md) and C-92 (`>>` onto a record)
#     are denied, C-91 (a scratchpad Write) and C-93 (an intake.py command)
#     are the negative controls. A `PASS … (skipped …)` line means the hook
#     file is missing — read that as the guard being DOWN.
python tools/closeout-intake/controls.py | tail -1
# 5c. (2026-09-07) hooks/published_record_guard.py DENIES a Write/Edit into a tree
#     whose root carries its own collection rules when the payload contains a
#     private-value literal (drive-rooted path, POSIX home path, account name,
#     32+ hex run, UUID) — the half a dispatch brief cannot reach, and a guard
#     that stopped firing is one nobody notices. Last line must read `ALL PASS
#     n/n`: P-1..P-6 are the positives (one per class, plus a distant marker
#     ancestor), N-1..N-5 the negatives (same literals OUTSIDE such a tree, a
#     class-named edit entry, a non-file tool, short hex, a malformed payload).
#     DELIVERY is not provable by this run — it proves decide(), not that the
#     harness calls the hook. That was probed live 2026-09-07 (a main-session
#     Write denied, the class-named rewrite allowed, and a dispatched worker's
#     Write denied the same way); re-run that probe when the harness changes.
python hooks/published_record_guard.py --selftest | tail -1
# RETIRED 2026-09-07 (history only — the shapes they read no longer exist):
#   old 5  "hits: field on every card" — hits are derived from ## Events (INV-4);
#   old 5b "card ids == detail-section ids, enumerated both ways" — the detail
#          file ops/references/lessons-detail.md is FROZEN and every section
#          lives verbatim in its record's ## Narrative (`import --verify`
#          proved 54 ids both ways, bytes equal);
#   old 5c "no ## L-nnn heading below ## Archived" — the index has no Archived
#          region; lifecycle state is per record;
#   old 5d "Evidence: line on every card born after 2026-08-11" — D6: a record
#          cannot be born without a locator.
#   Their text and calibration notes: `git show fa08fa3:ops/references/integrity-sweep.md`.
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
# 13. browser pane guard: the denials the user must ADJUDICATE. Proof-of-life
#     moved to check 31 on 2026-09-08, which runs
#     hooks/tests/test_browser_pane_scope_guard.py -- counting rows here reads
#     what the hook DID and says nothing about a hook that has stopped deciding
#     (rule-registry asserted "every pane navigation is LOGGED" for two days
#     while the file did not exist, found 2026-08-14). What is left here is the
#     part no suite can do: a loud deny is a question addressed to the user.
test -f telemetry/browser-nav.jsonl && echo "nav log: present" || echo "nav log: ABSENT - never navigated, or hook dead"
grep -c '"loud": true' telemetry/browser-nav.jsonl 2>/dev/null   # denials awaiting a user call
grep -c 'browser_pane_scope_guard' settings.json                 # still registered?
# 14. fieldwork shadow probe: its EXIT CRITERION. This one is a ~100ms tax on
#     every Read/Grep/Glob, so an idle probe is pure cost - either it is
#     producing rows to decide on, or it comes off. Proof-of-life moved to
#     check 31 on 2026-09-08 (hooks/tests/test_fieldwork_threshold_notice.py):
#     an empty log means "nothing crossed the threshold" OR "the probe stopped
#     counting", and only the suite tells those apart.
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
# SHARE EDITION: tools/skill-routing-audit.py does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` ("serves records this
# share does not carry": it reads this machine's own session transcripts).
# `ops/references/skill-trigger-classes.md`, which this check's 18b extension
# reads, does ship; running the audit against your own transcripts is a build
# you would have to write yourself.
python tools/skill-routing-audit.py --surface
# read the FIRING ANYWAY block first: an entry with fires and 0 coverage means
# the dict records words nobody says. A DEAD entry that never fired is only a
# skill whose occasion has not arisen, which is not a defect.
# Since 2026-09-04 (T-023) three readings changed and the old ones were WRONG in
# the tool's favour, so do not read an older report by today's rules:
#   NO VOCABULARY is not DEAD -- the entry has no 關鍵詞 line, so the tool had
#     nothing to match and its silence says nothing about the dict (10 of 13
#     DEAD entries were this on 2026-09-04).
#   LATE beside a MISS means the words appeared and the entry's OWN skill fired
#     later in the same session, past the 6-event window. Coverage EXCLUDES it
#     by design, so `0% coverage` overstates the fiction unless LATE is quoted
#     with it (corpus-wide LATE was 71 the day the column was added).
#   ASCII tokens now treat CJK as a word boundary; every coverage number
#     measured before that date is understated (HIT 21 -> 28 on one corpus).
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
git config --get gc.reflogExpire || echo 'reflogExpire UNSET (default 90d) -- ACT'
git config --get gc.reflogExpireUnreachable || echo 'unreachable UNSET (30d) -- ACT'
# both must print `never`; a bare value that is not `never` is also ACT
ls -dt ~/.claude/backups/*/ 2>/dev/null | head -3   # -t: newest FIRST, and the
# trailing slash drops loose files. Sorting these by NAME was the first version
# of this check and it silently reported the alphabetically-last batch as the
# newest (2026-08-15).
# Act on: either knob NOT reading `never`; a newest backup batch older than the
# last red-tier edit. The predicate is the CONFIG, not a date, because a date
# baseline drifts out from under the check while still reading plausibly (PH-11
# / AP-62) - which is exactly what happened here.
# Baseline 2026-08-15 (WRONG, kept as the case): "reflog reaches the initial
# commit (2026-07-06, 40 days, nothing expired yet), both knobs at defaults, so
# the 90-day horizon has simply not arrived; re-read on 2026-10-04." It counted
# only gc.reflogExpire (90d) and forgot gc.reflogExpireUnreachable, whose
# default is 30d and had ALREADY been deleting. Measured 2026-09-08: the oldest
# entry was 2026-08-10 - 29 days, not 64 - so the real undo window on a repo
# with NO REMOTE was less than half the assumed one, silently.
# 2026-09-08: both knobs set to `never` on this checkout (repo-local .git/config,
# which is untracked - that is why this check must verify them rather than a
# committed file recording them). 990 entries in ~30 days is ~150 KB/month, so
# unbounded retention costs nothing here and buys back the whole history.
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
# SHARE EDITION: tools/e2-gate-test/ does not ship -- declared `[[not_shipped]]`
# under `tools/share-manifest.toml` (2026-08-16 user ruling: a test of this
# machine's own layout as much as of the hook it drives; deferral closed, not
# collected). `hooks/delivery_gate_shadow.py`, the hook it tests, does ship;
# there is no packaged suite to drive it with here.
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
# SHARE EDITION: tools/ps-errorpref-test/ and tools/ps-errorpref-backtest/ do
# not ship -- declared `[[not_shipped]]` under `tools/share-manifest.toml`
# (the general `tools/` exclusion; test/backtest harnesses this share does not
# carry). `hooks/ps_errorpref_guard.py` ships and is enforced; its regression
# and corpus evidence stay source-only.
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
# SHARE EDITION: tools/session-board-test/ and tools/session-board/ do not
# ship -- both declared `[[not_shipped]]` under `tools/share-manifest.toml`
# (the board and its writer are excluded as a pair: shipping the hook alone
# would mount a hook that appends to a file no adopter has). §7a of
# `20-dispatch.md` describes doing the three registration steps by hand in
# this share; there is no suite to run in their place.
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
# SHARE EDITION: tools/ps-pipeline-close-test/ and tools/ps-pipeline-close-
# backtest/ do not ship -- declared `[[not_shipped]]` under `tools/share-
# manifest.toml` (the general `tools/` exclusion). `hooks/ps_pipeline_close_
# guard.py` ships and is enforced; its regression and corpus evidence stay
# source-only.
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
# SHARE EDITION: this one file of tools/ops-health-test/ does not ship. Only
# `tools/ops-health-test/check_cap_binding.py` (checks 7b and 15 above) ships
# in this repo, mapped through `[source_map]`; `test_ops_health_nudge.py` is a
# separate file in the same source directory and stays declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (a test of this
# machine's own layout, per the 2026-08-16 ruling). `hooks/ops_health_nudge.py`
# ships and is enforced; its 28-case regression suite stays source-only.
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
# SHARE EDITION: tools/playwright-mcp/ does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (the general `tools/`
# exclusion; a durable local MCP install, not a rules asset). The `test -f`
# line and its README re-install pointer resolve only against your own
# install; `claude mcp get playwright-headless` on the next line is a Claude
# Code CLI command and needs nothing from this repo to run.
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
# SHARE EDITION: tools/graph-snapshot/ does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` via the `skills/
# graph-query` entry (the derived graph, its builder and its scheduled task
# are all environment-bound state; `skills/graph-query` is itself excluded for
# the same reason). The scheduled-task name below is source-only and names no
# task an adopter has; this whole check has nothing to run against in this
# share.
schtasks /Query /TN "ClaudeGraphSnapshotWatchdog-Daily" /FO LIST | findstr "Status Next"   # task exists, next run scheduled
python -X utf8 tools/graph-snapshot/gs_watchdog.py     # manual run: exit 0, or 3 = standing finding
python -X utf8 tools/graph-snapshot/tests/test_smoke.py   # 41 checks; 6 drive evaluate() two-sided
#     Act on: the task missing or its Last Result nonzero (re-register per
#     tools/graph-snapshot/watchdog-task.ps1 header); watchdog-status.json
#     mtime > 3 days while check 15 says nothing at session start (the hook
#     edit was lost — restore check 15); a FINDING standing for days with no
#     harvest (run the graph-query skill's J3 flow). Rule-registry key
#     `graph rot watchdog`.
# 27. archdiag receipt regression (born 2026-08-29 with the F3 close-out).
#     Frozen audit deliverables (dit-audit-f1 / prism-audit-f2 / mfp-audit-f3)
#     carry sha256 receipts; the library that emits them is shared, so ONE
#     edit under tools/archdiag/ can change every accepted artifact's bytes
#     with every test green — the motivating case is the eol hazard (commit
#     6fbe14c: a CRLF checkout would have corrupted all receipts silently).
#     Regeneration MUST be a byte-level no-op:
for b in outputs/diagram-authoring/*.build.mjs; do node "$b" >/dev/null || echo "BUILD FAILED: $b"; done
git status --porcelain outputs/diagram-authoring/*.html   # must print nothing
#     Act on: any diff = receipt drift — find the library edit that caused it;
#     an INTENDED change is a version bump per the post-acceptance protocol
#     (user ruling, D-043), never a silent regen. BUILD FAILED = a build
#     script rotted (API drift in the library). Full instrument ritual
#     (selfcheck calibration, LF pins, router acceptance):
#     tools/archdiag/MAINTENANCE.md.
# 28. (2026-09-06) files that are TRACKED although the ignore rules say they
#     should not be — i.e. every `git add -f` ever performed here. The force-add
#     is the only repo operation that leaves NO record: the file survives, the
#     reason does not, and the pattern that was wrong stays wrong for the next
#     file. Its signature is a SPLIT directory, which is worse than either
#     state, because the siblings nobody forced look exactly like deliberate
#     exclusions. Rule: 40-maintenance.md §vc-boundary.
git ls-files -ic --exclude-standard
#     ^ must print nothing. Act on a hit by fixing the RULE, never by removing
#     the file: anchor or narrow the pattern, or add a negation naming why (and
#     naming the tracked files that cite it, if that is the reason).
#     Calibrated two-sided 2026-09-06 — it was born RED, on five files with
#     three distinct causes: `plugins/` unanchored, therefore also eating
#     trigger-probe's roster fixture (pattern bug, fixed to `/plugins/`); an
#     archive/ subtree six tracked files cite by path, `interop/interop.py`
#     among them (negation, citers named); and nine archive NOTE/README files,
#     the one part of an archived subtree the blanket ignore was guaranteed to
#     drop while forced siblings survived. Positive control that survives the
#     fix (the tree is now silent, so the check needs one):
git ls-files -ic --exclude-standard -x 'projects/'
#     ^ re-adds the pre-2026-09-06 memory-store pattern as an extra rule and
#       must print the 79 memory files — proof the check can still see a
#       tracked-but-ignored file rather than having gone blind.
# 29. (2026-09-08) entry-schema conformance — artifacts that classify or route
#     (hooks, rules/*.md, trigger-class blocks, registry rows, the principle
#     guide's citations) missing a core field of ops/references/entry-schema.md
#     or an asset property of ops/references/principle-design-guide.md that has
#     a mechanical detection. An OMISSION fires no event (40-maintenance §2a
#     P2), so the absence is enumerated here. Legacy artifacts (first commit on
#     or before 2026-09-08) WARN with a count that must not rise; born-after FAIL.
# SHARE EDITION: tools/entry-schema-lint/ does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (the general `tools/`
# exclusion; new since this round, not individually adjudicated before now).
# `ops/references/entry-schema.md` and `ops/references/principle-design-
# guide.md`, the two files this lint enforces, both ship; the lint itself does
# not, so its ES-1..ES-8 checks stay a documented-only property in this share.
python -X utf8 tools/entry-schema-lint/controls.py | tail -1   # ALL PASS 41/41 — two-sided; read this line BEFORE trusting the next
python -X utf8 tools/entry-schema-lint/lint.py                  # exit 0; last line `entry-schema-lint: 0 FAIL / 0 WARN / anchors ok`
#     Born-RED baseline 2026-09-08 = 0 FAIL / 59 WARN; same day after R2 (user
#     ruling, STATUS backfilled from first-commit dates) and R3 (model3d ruling
#     rebound to the figure class) = 0 FAIL / 34 WARN; after the ES-2/ES-3
#     predicate rebuild the same evening = 0 FAIL / 16 WARN; and after the
#     control suites + the ES-5 why/evidence pass that night = **0 FAIL / 0
#     WARN, the whole born-RED baseline closed in one day**. THAT emptied the
#     WARN tier of its meaning, so ES-1..ES-5 were promoted to FAIL under a
#     second named trigger written into `SEVERITY_PROMOTED` (legacy count
#     reaches 0 → the next WARN could only be a regression printed quietly);
#     ES-7/ES-8 stay WARN because a heuristic may prompt a review and never
#     rule FAIL. Same pass: four findings that hardcoded `WARN` now call
#     `severity_for`, without which the promotion this file names would have
#     been INERT for ES-3/ES-4/ES-5 — controls C-05/C-05b/C-05c are the
#     two-sided proof that the lever moves. Baseline as measured at birth:
#     ES-1 0 (24 at birth: registered hooks
#     without a `STATUS:` line); ES-2 5 (17 at birth) — the predicate is no
#     longer "named in THIS file" (a POSITION in an artifact that grows, AP-45:
#     it flagged 11 hooks that check 31 already executes and none of the 5 that
#     declare nothing) but "carries a `Proof-of-life:` line in its own
#     docstring", which is what check 31 runs. A hook gains coverage by editing
#     the hook, never by being listed here; ES-3 0 (6 at birth) — rules/*.md
#     without a review-when; the detector now accepts the inline
#     `review-when: <event>` shape two rules already used, and a review DATE is
#     not a trigger; ES-5 0 (11 at birth: rule-registry entries lacking
#     why/evidence — closed 2026-09-08 by writing the reasons, one judgement
#     per entry; the shape that recurred was an entry documenting a HARNESS
#     conflict in `harness:`/`local narrowing:` and never naming its own
#     standing reason); ES-8 0 (1 at birth:
#     model3d-pipeline SKILL.md:49 "whenever this pipeline emits" — the ruling
#     L-059 was born from; rebound to "any schematic/illustrative figure this
#     repo produces" on 2026-09-08, R3; the lint's known-bad now lives only in
#     its controls).
#     Act on: any FAIL — a born-after artifact shipped without its core field:
#     fix the artifact, never move SCHEMA_BORN; exit 2 — an anchor moved (the
#     CLAUDE.md index line renamed, settings.json hook-command shape changed):
#     fix the anchor in lint.py, the alarm is the point; a WARN class above its
#     baseline for two consecutive sweeps, OR a WARN class that reaches 0 →
#     add it to SEVERITY_PROMOTED in lint.py (the two named promotion
#     triggers; heuristics are not eligible). Optional project pass:
#     `--project-root <repo>` adds ES-7 (page builders: data-page-class /
#     data-audience / own `<html` root — the T44 pattern; SSLD 2026-09-08 =
#     16 WARN, 6 independent shells). Rule-registry key `ENTRY_SCHEMA`.
# 30. (2026-09-08) worktree scope — hooks/worktree_scope_guard.py ANNOUNCES a
#     linked-worktree session (worktree, branch, canonical path, unmerged count,
#     ignored state present) and, in the canonical tree, the linked worktrees
#     that still exist; it DENIES a Write/Edit/NotebookEdit into a path git
#     ignores inside a linked worktree of ~/.claude, and a relative-path
#     gsnap.py/xi.py state build from such a worktree. Born from the user's
#     2026-09-08 repeat report (paths handed out that resolve only on an unmerged
#     worktree branch; a graph-snapshot out/ rebuilt in a worktree). Asset
#     properties: shared-tree-git.md §1a; rule-registry key `WORKTREE_SCOPE`.
python hooks/worktree_scope_guard.py --selftest | tail -1   # ALL PASS n/n — two-sided on real temp repos, telemetry redirected
git worktree list                                            # canonical tree only in steady state; any linked entry must be merged or in flight
#     Act on: a linked worktree whose branch has unmerged commits (announcement
#     shows +N) → merge from the canonical tree or hand the worktree path out;
#     an announcement missing from a worktree session → settings.json lost the
#     SessionStart entry; a deny on a tracked-class path → misfire, report_fp.py.
# 31. (2026-09-08) hook proof-of-life EXECUTED, not named. PH-11 / AP-63: every
#     other check on this page reads state; this one RUNS each registered hook's
#     declared control suite, because being named in a sweep is not being run by
#     one. The motivating case is hooks/unattended_run.py, which called
#     _receipt() without importing it: every scope deny and every stop block
#     raised NameError, a crashing hook fails open, and both offline guards were
#     inert for a day. Its suite existed and passed the moment someone ran it.
#     Declarations live in each hook's own docstring (`Proof-of-life: `python
#     ...``), so coverage grows by editing the hook, never a list here.
# SHARE EDITION: tools/hook-proof-of-life/ does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (the general `tools/`
# exclusion; new since this round, not individually adjudicated before now).
# Each hook's own `Proof-of-life:` docstring line, which this tool reads and
# runs, still ships with the hook; there is no runner here to execute it.
python tools/hook-proof-of-life/pol.py --list      # seconds: classify only, no suites run
python tools/hook-proof-of-life/pol.py             # MEASURED 57s over 25 suites (2026-09-08, idle)
python tools/hook-proof-of-life/controls.py | tail -1   # ALL PASS n/n — the instrument itself
#     RUN IT ALONE. Measured 2026-09-08: three sweeps running concurrently
#     starved two suites past their budget, and the report named innocent hooks.
#     A timeout is now reported [INCONCLUSIVE], not [FAIL] — but a machine busy
#     enough to starve a suite also makes every other verdict here noisier.
#     Act on: any [FAIL] line → re-run the command it prints; any UNDETERMINED
#     → the docstring declaration is unreadable, fix the line; any
#     [INCONCLUSIVE] → re-run that one suite alone before believing it.
#     `uncovered` is FAIL as of 2026-09-08. It was WARN while a legacy backlog
#     existed and the promotion trigger recorded here was "uncovered reaching
#     0"; it reached 0 the same day the last five suites landed
#     (browser_pane_scope_guard, fieldwork_threshold_notice,
#     extdispatch_entrypoint_guard, instructions_loaded_logger,
#     project_registry_gist). A WARN everyone has already satisfied is a WARN
#     nobody reads, and the next uncovered hook will be a NEW one — the case
#     worth stopping for. `manual` stays WARN: named-but-not-run is a weaker
#     finding than nothing at all.
#     BASELINE 2026-09-08: **29 executable / 0 manual / 0 uncovered /
#     0 undetermined, 0 FAIL, 25 distinct suites in 57s.** Any non-zero in the
#     last three columns is a regression against this line.
#     Cost trigger: this check is not on the fast path. Two readings, and the
#     gap between them is the point — 57s idle, but 508s was recorded on
#     2026-09-08 while three sweeps ran at once, and that reading is what the
#     420s per-suite timeout is sized for. If an IDLE run passes ~15 min, split
#     it (a --changed mode over the hooks git touched) rather than letting the
#     sweep quietly stop being run — a proof-of-life nobody can afford to wait
#     for decays back into one nobody runs.
# 32. (2026-09-08) telemetry rows no reader can parse. Every rate this
#     environment publishes — deny rates, delivery-gate would_block, the
#     model-effort audit — is computed from telemetry/*.jsonl, and a row that
#     vanished leaves nothing behind to notice. 16 rows across 2 of 22 files are
#     unparseable, and their SHAPE is a tail fragment of a record whose head is
#     gone (fieldwork-shadow L58 is `b.meta.json"]}`, L73 is `]}`). The
#     mechanism is NOT established and no writer was changed on that guess: a
#     12-writer concurrency harness failed to reproduce it in 6 trials, and an
#     earlier noisy run lost rows in EVERY write mode including two candidate
#     fixes — a positive control that does not fire is not a control. So this
#     counts instead, and a RISING count is the reproduction a fix would need.
# SHARE EDITION: tools/telemetry-framing/ does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (the general `tools/`
# exclusion; new since this round, not individually adjudicated before now).
# It reads `telemetry/*.jsonl`, which is itself excluded (runtime logs of real
# work), so there is nothing in this share for it to read even if it shipped.
python tools/telemetry-framing/framing.py               # WARN at baseline, FAIL above it
python tools/telemetry-framing/controls.py | tail -1    # ALL PASS n/n — the instrument itself
#     Act on: FAIL → new damage since the baseline; find it with `--verbose`,
#     read the damaged rows' neighbours, and explain the event BEFORE
#     re-recording BASELINE. WARN at exactly the baseline is the steady state.
# 33. (2026-09-09) control suites with no case they must call `undetermined`.
#     PH-11 / AP-62: an instrument's classes are CLOSED over its corpus, so an
#     input matching none is reported `undetermined`, never folded into the
#     nearest class (the fold is silent because the count stays plausible:
#     2026-09-08, `L-nnn.md` → broken-link 9/9 false, PNG → mixed-endings 31/31
#     false). The half a machine can decide is whether the suite EVER asserts
#     that verdict; the per-class specimen half stays an audit item in the guide.
#     Enumerates every tools/*/controls.py, hooks/tests/*.py and each registered
#     hook's declared Proof-of-life suite (through pol.py's grammar, so 31 and
#     33 never disagree on what a declaration is); a suite it cannot read is
#     itself `undetermined` and excluded from the counts.
# SHARE EDITION: tools/class-closure/ does not ship -- declared
# `[[not_shipped]]` under `tools/share-manifest.toml` (the general `tools/`
# exclusion; new since this round, not individually adjudicated before now).
# Same gap as check 31: nothing here to run it against, and the suites it
# would enumerate (`tools/*/controls.py`) are themselves mostly source-only.
python tools/class-closure/closure.py                   # FAIL on any lacking suite (promoted 2026-09-09)
python tools/class-closure/controls.py | tail -1        # ALL PASS n/n — the instrument itself
#     "Carries" is a WORD-LEVEL proxy (undetermined / unclassifiable / UNDET in
#     the suite text; `inconclusive` deliberately excluded) and the matching line
#     is printed — a comment can satisfy it, so a `carries` row is evidence the
#     class is NAMED, not that it is exercised. Act on: FAIL → that suite has
#     no unclassifiable specimen; add one (the line the tool prints says what).
#     There is no softer level and no exemption set: PROMOTED 2026-09-09, the
#     day it was born — the 28-name legacy backlog was drained the same day
#     (11 rule-tier suites by the main session, 17 across four dispatched
#     slices), so LEGACY_LACKING and the WARN branch are gone.
#     BASELINE 2026-09-09 (post-drain): **31 suites / 31 carry / 0 lack / 0
#     undetermined — PASS.** Any `lacks` row is the regression.
#     What the drain found, which is the argument for the severity: five hooks
#     folded unclassifiable input into a real verdict (browser_pane_scope_guard
#     recorded a non-string url as a navigation that happened;
#     fieldwork_threshold_notice counted one as a read file, walking a session
#     toward its own threshold), ten crashed on a payload that parses but is
#     not an object while their docstrings claimed fail-open, and several
#     instruments had a correct `undetermined` branch no case had ever reached.
#     None of that was visible from the counts.
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
