# Maintenance Protocol — safely changing the rules layer itself

Governs changing the RULES, not doing the work the rules describe. This file
reuses the environment's existing mechanisms instead of inventing parallel
ones: audit trail = `~/.claude/Global_skill_update.md` (append-only), backups =
`~/.claude/backups/<YYYY-MM-DD>/`, config red-team = the `config-self-audit`
skill, file hygiene = global CLAUDE.md's rules (archive-not-delete,
new-file-not-overwrite), version history = the `~/.claude` git repo.

**After any 🔴/🟡 change is applied and audited**: `git add -A && git commit`
in `~/.claude` (conventional message, e.g. `docs(ops): ...` / `feat(skill): ...`)
— the git history is the diffable evolution record; the audit trail is the
narrative index into it. Guardrail changes (settings/hooks) follow the proposal
protocol in `70-evolution.md` first.

## §1 Tiering: who can change what

| Tier | Files | Rule |
|---|---|---|
| 🔴 Requester confirmation required | `~/.claude/CLAUDE.md`, any project `CLAUDE.md`, `settings.json`, hooks/, identity/persona files | show a diff, get a one-line confirmation, back up first, log in the audit trail |
| 🟡 Main session may change + audit | `ops/*` (including this file), `skills/*/SKILL.md`, `skill-trigger-dict.md`, `ops/rules-usage-dict.md` | back up first; run `config-self-audit` on the result; log one line in the audit trail |
| 🟢 Change freely | tickets, drafts, handoff notes, `ops/lessons.md` entries, memory entries | per each type's own convention (lessons: mark superseded, don't delete; memory: check for duplicates first) |
| ⛔ Subagents/workers | may NEVER write 🔴 or 🟡 files | worker output lands in drafts/scratch only; the main session reviews and performs the actual write |

✅ A worker drafts an improved dispatch template → main session reviews the
draft, makes the edit itself, backs up, logs it.
❌ A batch-cleanup worker "helpfully" rewrites `OPS.md` while it's in the
directory — a rule-tier write from a sandbox, unreviewed.

## §2 One lesson, one destination (this is the anti-bloat mechanism)

| Lesson type | Destination |
|---|---|
| One-off technical gotcha (command, API quirk, environment fact) | `ops/lessons.md` (bump hit-count if it recurs; mark superseded when replaced) |
| Dispatch/scheduling lesson | one line in the matching section of `20-dispatch.md` |
| Judgment lesson | a new ✅/❌ example under the matching R-rubric in `30-judgment.md` — NOT a new numbered rule (a genuinely new rule is a 🔴/🟡-tier change) |
| Requester preference / ruling | global CLAUDE.md (🔴 — via confirmation; end-of-project batches go through the `project-retrospective` skill) |

Never write the same lesson in full into two places — reference it from the
second place instead. A rule lives in exactly one file.

**Dict-sync corollary**: any 🟡 change that adds/renames/removes a skill, an
ops rule section, or a durable convention MUST update the affected index files
(`skill-trigger-dict.md` if the trigger surface changed; `ops/rules-usage-dict.md`
if a responsibility boundary changed; `OPS.md`'s routing table if a file's scope
changed) in the SAME commit — enumerate index files by grepping for references
to the changed file, not from memory (lessons.md L-004). The dicts are
indexes, and an index that lags its source is a ghost rule (§4.1). The
config-self-audit red-team of the change checks this sync explicitly, and
`hooks/ops_health_nudge.py` check 10 mechanically flags any local skill
missing from `skill-trigger-dict.md` at session start (change the two together).

✅ Discover a CLI needs a trust flag → one lesson card in `ops/lessons.md`,
and `20-dispatch.md` §3 already covers the class — bump nothing else.
❌ Paste the same pitfall paragraph into lessons.md, dispatch, AND CLAUDE.md —
three copies that will drift apart and contradict each other.

## §3 Trim discipline (keeping this from becoming an unread constitution)

- Triggers (defaults, mechanically nudged by `hooks/ops_health_nudge.py` —
  change the two together): any ops file past ~10K chars; the entry file
  (`OPS.md`) past ~60 lines; `ops/lessons.md` past ~30 unfolded entries;
  global `CLAUDE.md` past ~12K chars (it is ALWAYS loaded — trim/merge, don't
  append); any skill frontmatter description past ~800 chars; any SKILL.md
  past ~250 lines; `skill-trigger-dict.md` past ~20K chars;
  `Global_skill_update.md` past ~60K chars → rotate oldest entries to
  `archive/` with a pointer note (append-only still holds for what remains).
- **Birth budgets** (prevention beats trimming — a new artifact must be born
  within budget, not grow into a trim candidate): skill description ≤700
  chars stating purpose + trigger phrases + top 1–2 NOT-cases, detailed
  disambiguation goes to `skill-trigger-dict.md` with a pointer back;
  SKILL.md body ≤150 lines (soft), detail in `references/` loaded on demand;
  a new global CLAUDE.md rule must be conditional ("When X…"), single-bullet,
  and MERGE with any near-duplicate instead of appending beside it; a new ops
  rule goes in its ONE owning file (§2). The reviewer of any 🟡 change checks
  the budget before the content.
- Before deleting a clause, look for evidence it's alive: referenced in recent
  work, cited in the audit trail, appears in a relevant diff, or tied to an
  open ticket. No evidence → mark "trim candidate", and only demote/remove
  after a red-team pass or requester confirmation — absence of evidence is not
  proof of no effect.
- Then merge near-duplicates; extract long passages into a referenced sub-file.
- Per global CLAUDE.md file hygiene: retired content moves to an archive
  location with a note — never hard-deleted.

## §4 Degradation checks (run at retrospectives or when something feels stale)

1. **Ghost rules**: the routing table in `OPS.md` (and the pointer in global
   CLAUDE.md) is what keeps this layer alive — if a routing line breaks, the
   layer dies silently. Periodically check each ops file has appeared in real
   use recently. If a file is never read, ask "why does nobody use it" (bad
   routing? impractical rule?) — don't polish content nobody reads.
2. **Ghost mechanisms**: any document describing a mechanism ends with one
   proof-of-life command (check the scheduler entry / hook registration / an
   artifact's mtime). Run it before believing — or asserting — the mechanism
   exists. Documentation records intent; only evidence records reality.
3. **Ritualization**: if red-team/review passes come back clean repeatedly with
   zero findings, treat that as a stale review prompt, not as proof of quality.
   The fix is not more process — rewrite what the review is looking for.
4. **Recurring lesson**: when the same lessons.md entry's hit-count keeps
   climbing, harden it into a startup-time rule (a 🟡/🔴 change with the usual
   process) — that is the system remembering what sessions keep forgetting.

✅ Quarterly check finds `30-judgment.md` uncited for months → investigate the
routing table first; discover the trigger description is too vague to fire.
❌ "Our red-team has passed everything clean five times running — quality must
be excellent now."
