# Maintenance Protocol — safely changing the rules layer itself

Governs changing the RULES, not doing the work the rules describe. This file
reuses the environment's existing mechanisms instead of inventing parallel
ones: rule rationale = `ops/rule-registry.md`, change events = git commit
messages, backups = `~/.claude/backups/<YYYY-MM-DD>/`, config red-team = the
`config-self-audit` skill, file hygiene = global CLAUDE.md's rules
(archive-not-delete, new-file-not-overwrite), version history = the
`~/.claude` git repo. (`Global_skill_update.md` is the frozen pre-2026-08-11
event log — historical reading only.)

**After any 🔴/🟡 change is applied and audited**: `git add -A && git commit`
in `~/.claude` (conventional message, e.g. `docs(ops): ...` / `feat(skill): ...`)
— the commit message IS the change record (fields below), and
`ops/rule-registry.md` carries the standing reason. Guardrail changes
(settings/hooks) follow the proposal protocol in `70-evolution.md` first.

### Where a rule change gets recorded (anchor: audit-entry-schema)

Restructured 2026-08-11. A change produces TWO records with different
lifetimes, and they go to different places:

1. **The event** — which files changed, on what day, and how to revert →
   **the git commit message**. Fields, in order: trigger (the failure, review
   finding, or user directive that forced it — "because it was better" is not
   a trigger) / change (before → after; for rule text quote the operative line
   both ways, a §-reference does not satisfy this) / result (evidence it
   holds: command output, size delta, one real run per `30-judgment.md` R2) /
   rollback (backup path or commit). This is the record that decays: it is
   worth most on the day it is written, and `git log`/`git log -S` already
   index it perfectly.
2. **The standing reason** — why the rule holds its CURRENT value →
   **`ops/rule-registry.md`**, keyed by the rule, not the date. Changing a rule
   REPLACES its entry and compresses the old value into `history:`. Fields:
   key / current / why / evidence / history / rollback.

Why not one chronological log: it grows as O(changes) while its value is
O(rules), so it needs rotation forever — and rotation evicts the OLDEST
rationale, which is the most settled and therefore the most load-bearing.
`Global_skill_update.md` is frozen as the pre-2026-08-11 historical log for
exactly this reason; see its header for the ruling it lost.

### Version-control boundary (anchor: vc-boundary)

The test is **"will someone need to FIND this later?"** — not the file type,
not its age.

- **In git**: rules, the reasons rules hold their values, decision registries,
  code, and rotated rationale (an archive, tracked). If a future session could
  ask "why is this like this", it must be greppable in the working tree.
- **Not in git**: machine-local state (telemetry, caches), raw session
  transcripts, scratch/draft material, dead material, and **backups** — git
  IS the backup.
- **The failure mode this rule exists to stop**: a gitignored directory
  quietly becoming the only home of a live ruling. It has happened — a
  gitignored backup directory was briefly the sole surviving copy of a
  standing user ruling after it was rotated out of the old chronological log.
  If you are about to move rationale into a gitignored archive or a backups
  folder, you are about to lose it; move it somewhere tracked instead.

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
  change the two together). **WHY each value is what it is, and what it was
  before, lives in `ops/rule-registry.md` — do not restate it here** (§2: one
  thing, one place):
  | trigger | value |
  |---|---|
  | any `ops/*.md` — except `lessons.md` and `rule-registry.md` | ~15K **bytes** |
  | entry file `OPS.md` | ~60 lines |
  | `ops/lessons.md` | ~30 unfolded entries |
  | global `CLAUDE.md` (ALWAYS loaded — trim/merge, never append) | ~15K **bytes** |
  | skill frontmatter description (charged every session) | ~800 chars |
  | any `SKILL.md` body (charged only on invoke) | ~300 lines |
  | `skill-trigger-dict.md` | ~20K **bytes** |
  File caps count BYTES (`getsize`, so CRLF counts 2), not chars: bytes track
  TOKEN cost across mixed CJK/Latin, chars under-count the densest files.
  Two files are exempt from the ops cap — their size tracks the CORPUS, not
  bloat, so an over-cap reading has no extract remedy and can only nag forever;
  their real checks are the lessons entry-count and §4.1 ghost rules.
  Rotation of a frozen chronological event log is retired — rationale now
  goes to the registry, which grows with the rule count, not the change count.
- **A size trigger means EXTRACT, not DELETE.** Over cap, the legitimate moves
  are: move detail to a references file (or an archive for logs) behind a
  pointer, merge genuine duplicates, and cut text that says nothing.
  Compressing a rule until it fits — dropping the example, the why, the
  boundary case — makes the file shorter and the rule weaker, and it is
  invisible in a line count. If a pass cannot get under cap without cutting a
  distinct rule, that IS the signal to raise the cap (with the failed pass
  recorded as the evidence), the same way CLAUDE.md went 12K→15K and ops files
  10K→12K. Never trade completeness for the number.
- **Birth budgets** (prevention beats trimming — a new artifact must be born
  within budget, not grow into a trim candidate): skill description ≤700
  chars stating purpose + trigger phrases + top 1–2 NOT-cases, detailed
  disambiguation goes to `skill-trigger-dict.md` with a pointer back;
  SKILL.md body ≤150 lines (soft), detail in `references/` loaded on demand;
  a new global CLAUDE.md rule must be conditional ("When X…"), single-bullet,
  and MERGE with any near-duplicate instead of appending beside it; a new ops
  rule goes in its ONE owning file (§2). The reviewer of any 🟡 change checks
  the budget before the content.
- **Birth schema** (record types): a NEW record-document type must declare at
  birth its minimum field set — at least an id-or-date anchor, a status/verdict,
  a why, and an evidence-or-link field — plus its owning file, and register in
  `ops/rules-usage-dict.md` §7 in the SAME commit. Schema fields are
  invariant-class: no relaxation level omits them; only narrative style and
  procedure relax. An unregistered record format is a ghost rule (§4.1).
- **Scale-label qualifier rule**: an enumerable label whose meaning or
  direction is not derivable from the word itself (L0–L2, Tier-2, Mode A/B,
  layer numbers) carries a compact qualifier at every point of USE outside its
  defining file — e.g. "L2 (fully relaxed, loosest)". Labels travel farther
  than their definitions, and a bare label invites the reader's default
  convention, which for L-scales is usually the INVERTED one (ASVS-style
  higher = stricter). Corollary: never reuse an existing label family for a
  new scale in the same rule tree (the 70-evolution "(L2)" build-check /
  relaxation-level collision, fixed 2026-07-31, lessons.md L-008).
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
