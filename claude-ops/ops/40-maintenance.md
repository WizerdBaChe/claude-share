# Maintenance Protocol — safely changing the rules layer itself

Governs changing the RULES, not doing the work the rules describe. This file
reuses the environment's existing mechanisms instead of inventing parallel
ones: rule rationale = `ops/rule-registry.md`, change events = git commit
messages, backups = `~/.claude/backups/<YYYY-MM-DD>/`, config red-team = the
`config-self-audit` skill, file hygiene = global CLAUDE.md's rules
(archive-not-delete, new-file-not-overwrite), version history = the
`~/.claude` git repo. (`audit-archive/` is the frozen pre-2026-08-11
event log — historical reading only.)

**After any 🔴/🟡 change is applied and audited**: `git add -A && git commit`
in `~/.claude` (conventional message, e.g. `docs(ops): ...` / `feat(skill): ...`)
— the commit message IS the change record (fields below), and
`ops/rule-registry.md` carries the standing reason. Guardrail changes (settings/hooks) follow the proposal
protocol in `70-evolution.md` first.

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
`audit-archive/` is frozen as the pre-2026-08-11 historical log for
exactly this reason; see its header for the ruling it lost.

### Version-control boundary (anchor: vc-boundary)

The test is **"will someone need to FIND this later?"** — not the file type,
not its age.

- **In git**: rules, the reasons rules hold their values, decision registries,
  code, and rotated rationale (`audit-archive/`). If a future session could
  ask "why is this like this", it must be greppable in the working tree.
- **Not in git**: machine-local state (`telemetry/`, caches), raw session
  transcripts (`memory-archive/`), scratch (`drafts/`), dead material
  (`archive/`), and **backups** — git IS the backup.
- **The failure mode this rule exists to stop**: a gitignored directory
  quietly becoming the only home of a live ruling. It has happened —
  `backups/` and `memory-archive/` were the sole surviving copies of the
  2026-07-09 `AGENTS.md` ruling after it was rotated out. If you are about to
  move rationale into `archive/` or `backups/`, you are about to lose it;
  move it somewhere tracked instead.
- **Known open tension**: top-level `references/` is gitignored by a
  2026-07-19 user ruling, but now holds phase logs and decision journals,
  which are durable rationale by this test. Flagged 2026-08-11, unruled.

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
  change the two together; sweep check 7 catches drift). **WHY each value is
  what it is lives in `ops/rule-registry.md` — do not restate it here** (§2).
  **Two classes, and they are not the same kind of rule:**

  **(a) Unconditional — charged every session whether used or not. The number
  IS the budget; a hard cap is correct here.**
  | trigger | value | unit as measured |
  |---|---|---|
  | global `CLAUDE.md` (trim/merge, never append) | ~15K | **bytes** (`getsize`) |
  | skill frontmatter description (× every skill, plugins included) | ~800 | **chars** (`len`) |

  **(b) On demand — charged only when something routes to it. The cap is a
  PROXY for "reading this got expensive", not a budget. One read that routes
  correctly beats a smaller file that costs two more reads; optimise clarity
  per read first, and treat the number as the signal to look, not the goal.**
  | trigger | value | unit as measured |
  |---|---|---|
  | any `ops/*.md` — except `lessons.md` and `rule-registry.md` | ~18K | **bytes** (`getsize`) |
  | `skill-trigger-dict.md` | ~20K | **bytes** (`getsize`) |
  | any `SKILL.md` body | ~300 | lines |
  | entry file `OPS.md` | ~60 | lines (not hook-enforced) |
  | `ops/lessons.md` | ~30 | unfolded entries |

  Bytes, not chars, because bytes track TOKEN cost: measured across this corpus
  bytes/token holds at 3.8–4.1 (±4%) while chars/token ranges 2.3–4.0 (77%
  spread) — UTF-8 gives CJK 3 bytes and tokenizers charge CJK ~3–4× Latin, so
  the two scale together. Rotation of the frozen `audit-archive/` is
  retired — rationale goes to the registry, which grows with the rule count.
- **A size trigger means EXTRACT, not DELETE.** Over cap, the legitimate moves
  are: move detail behind a pointer — `skills/<name>/references/` for skills,
  **`ops/references/` for ops files** (pointer from the owning §; no `OPS.md`
  routing row — these load on demand from their owner, never at session start),
  `archive/` for logs — merge genuine duplicates, and cut text that says
  nothing. **What moves is the concrete: examples, command blocks, motivating
  cases, evidence. What stays is the rule, its conditions, and the routing.**
  Compressing a rule until it fits — dropping the example, the why, the
  boundary case — makes the file shorter and the rule weaker, and it is
  invisible in a line count. If a pass cannot get under cap without cutting a
  distinct rule, that IS the signal to raise the cap (with the failed pass
  recorded as the evidence), the same way CLAUDE.md went 12K→15K and ops files
  10K→12K→15K. Never trade completeness for the number.
- **Birth budgets** (prevention beats trimming — a new artifact must be born
  within budget, not grow into a trim candidate): skill description ≤700
  chars stating purpose + trigger phrases + top 1–2 NOT-cases, detailed
  disambiguation goes to `skill-trigger-dict.md` with a pointer back;
  SKILL.md body ≤150 lines (soft), detail in `references/` loaded on demand;
  a new global CLAUDE.md rule must be conditional ("When X…"), single-bullet,
  and MERGE with any near-duplicate instead of appending beside it; a new ops
  rule goes in its ONE owning file (§2). The reviewer of any 🟡 change checks
  the budget before the content.
  **Label birth** (moved here from the Scale-label bullet 2026-08-12 — that
  bullet fires only over cap, but a label is minted while authoring): before
  introducing any enumerable label citable WITHOUT its owner's filename
  (`Mode X`, `L2`, `Tier-3`, `AD1`, a new checklist's numbering), run the grep
  in `~/.claude/LABEL-REGISTRY.md` §4. Hit → reuse that family's meaning, pick
  another family, or register a new owner in the SAME commit; never a second
  meaning for a live family. Project lists (rounds, UAT items) also need a
  generation prefix (§3 there), registered in `60-bootstrap.md` §E.
- **Constant binding** (a different failure from naming — same name, drifting
  value): any threshold existing BOTH as rule text and in a mechanism states
  its unit at both sites and carries a drift check. Rule text is not a source
  of truth; the mechanism is. Case and check: `rule-registry.md` key `cap
  measurement unit`, sweep check 7.
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
  higher = stricter). The never-reuse-a-family corollary moved to Birth
  budgets 2026-08-12 — it fires when a label is MINTED, not when a file is
  over cap. Table of every family in use: `~/.claude/LABEL-REGISTRY.md`.
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

## §5 Integrity sweep (the gap between the two audit skills)

An artifact that is legitimately PRESENT and correctly REFERENCED, but whose
CONTENT is wrong, is invisible to BOTH audit skills — `config-self-audit` refuses
to widen past the artifact just named, `env-cleanup` is file-level only. That gap
is measured, not theoretical (22 `agents/*.md` definitions sat in it for 37 days).

**Run** at retrospectives, after importing anything from outside, and whenever §4
runs. **The checks + their motivating cases**: `ops/references/integrity-sweep.md`.

Why grep and not a skill: the failure class is *silent*, so it needs a check that
runs without anyone suspecting anything is wrong. A skill fires when someone
already suspects — which is precisely what did not happen for 37 days.
