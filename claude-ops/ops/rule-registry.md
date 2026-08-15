# Rule Registry — why each rule holds its current value

<!-- Keyed by the RULE, not by the date. One entry per rule or standing
     ruling; changing a rule REPLACES its entry in place and compresses the
     old value into `history:`. The file therefore grows with the number of
     rules (bounded) rather than the number of changes (unbounded), so it
     never needs rotation.

     Schema and write-triggers: `40-maintenance.md` §3. Registered in
     `rules-usage-dict.md` §7. English — read by the model on resume.

     WHAT GOES HERE vs ELSEWHERE
     - here:                 the standing reason a rule holds its value, its
                             value history, and how to undo it
     - commit message:       the event — which files changed on which day
     - `lessons.md` L-nnn:   a pitfall that was actually hit
     - a project's own decision log: a PROJECT's decisions, not a rule's
     - `Global_skill_update.md`: historical event log, frozen 2026-08-11

     Entry fields: key / current / why / evidence / history / rollback.
     `history` is the point of the file: it is the retrieval path that does
     NOT require git archaeology. Keep each entry ~6 lines; if the reasoning
     needs more, it belongs in a lessons entry and this cites it.

     PROVISIONAL VALUES (added 2026-08-13). A threshold shipped as a GUESS
     must still be registered, with `evidence:` starting with the literal
     token `PROVISIONAL` followed by (a) what observation would settle it and
     (b) the instruction that observations are appended to THIS entry. An
     unregistered guess has no home for the data that would correct it, so the
     data is never collected and the guess silently becomes permanent — which
     is indistinguishable from a measured value to every later reader.
     Registering it here buys three things a ticket cannot: `grep -n
     PROVISIONAL ops/rule-registry.md` enumerates every unsettled value
     (integrity-sweep check 11), this file has a liveness check of its own
     (idle > 45 days), and it is project-independent — a ticket in ONE
     project's ledger is invisible to the sessions in OTHER projects, which
     are the ones actually generating the observations. The point-of-use text
     must name this key as the write target; "revise later" with no
     destination is how a guess ossifies. -->

## Size and budget rules

### `CLAUDE_MD_CAP` — global CLAUDE.md always-loaded budget
- current: 15 * 1024 chars (2026-08-01)
- why: CLAUDE.md is loaded IN FULL every session, so bytes here are the only
  instruction bytes that are unconditionally charged. Trim or merge, never
  append.
- evidence: a real trim pass capped out at ~13.7K without cutting any distinct
  rule; raising beat deleting a rule that had no valid sink.
- history: 12K (birth) → 15K (2026-08-01, after the failed trim pass)
- rollback: `hooks/ops_health_nudge.py` `CLAUDE_MD_CAP`; `40-maintenance.md` §3

### `BODY_CAP` — SKILL.md body line cap
- current: 300 lines (2026-08-11)
- why: a SKILL.md body loads only when the skill fires, NEVER at session
  start, so this cap buys nothing at startup. The per-session skill cost is
  the frontmatter description, which has its own budget. 250 was shaping
  content instead of triggering extraction.
- evidence: a prior trim pass cut lines from two SKILL.md bodies, added NO
  references file, and left one skill at exactly 250 lines — the cap value.
  Corpus at the raise: 14 skills, median 153.5 lines, 62.9 B/line, one over
  250 and none over 260 (so 260 bought a single nudge and no headroom). 300
  lines ≈ 18.9K chars, paid once per invocation.
- history: 250 (birth) → 300 (2026-08-11)
- rollback: pre-change backup of `ops_health_nudge.py`

### `DESC_CAP` — skill frontmatter description cap
- current: 800 chars hard / 700 birth budget (unchanged)
- why: THIS is the skill cost charged every session — descriptions are how the
  model picks a skill, so they are always loaded. Keep tight. Detailed
  disambiguation goes to `skill-trigger-dict.md` with a pointer back.
- evidence: a dedicated slimming pass targeted this deliberately, and
  correctly.
- history: 800/700 since birth
- rollback: `hooks/ops_health_nudge.py` `DESC_CAP`

### ops file cap
- current: ~15K **bytes** per `ops/*.md` (2026-08-13). **Scope: `lessons.md`
  and `rule-registry.md` are exempt** — their size tracks the CORPUS, not
  bloat, so an over-cap reading has no extract remedy and can only nag
  forever. Their real degradation checks are elsewhere: the lessons
  entry-count cap, and §4.1 ghost rules (a registry entry for a rule nobody
  uses).
- why: same trim-vs-delete logic as CLAUDE.md, one tier down — but a DIFFERENT
  rule class: ops files are charged only when something routes to them, so the
  cap is a proxy for "reading this got expensive", not a hard budget
  (`40-maintenance.md` §3). The 12K value had reached the state a proxy must
  not reach: six files over it at once, nudging every session, with no pass
  able to clear them — a permanently-on alarm is one nobody reads.
- evidence: 12K→15K (2026-08-13) — `60-bootstrap.md` sat at 12,011 B BEFORE
  the §H read-time-map rules were added, i.e. already at cap with its whole
  extractable surface already extracted into `60-record-templates.md`. Adding
  7 distinct rules put it at 14,163 B; the only concrete left to move was two
  templates totalling ~1,180 B, landing at ~12,983 B — still over. The pass
  provably could not reach cap without cutting a distinct rule, which §3
  forbids. The prior raise (10K→12K) used the same test.
- history: 10K (birth) → 12K (2026-08-06, after a failed trim pass) → 15K
  (2026-08-13, after the failed pass above)
- rollback: the nudge hook's size constant; `40-maintenance.md` §3

### map STALE thresholds — when a project map stops being trusted
- current: DRIFT at 1–5 relevant changed files, STALE above 5 OR on any
  structural path (package manifest, directory added/removed). Relevance is
  scoped to the map's `covers` globs minus `excludes` (2026-08-13). Point of
  use: `ops/references/project-map.md` §6.
- why: scoping to `covers` is the cheap accuracy win — a docs-only commit must
  not invalidate a code map. The 5 and the structural list are NOT reasoned
  values; they are the smallest thing that could work, shipped as declared
  guesses rather than picked silently, because the source environment had
  already hit that trap twice with other thresholds.
- evidence: **PROVISIONAL — no measurement exists.** What settles it: two or
  three real cold-start projects each completing a FRESH → DRIFT → STALE
  cycle, recording the relevant-file count at which patching from the diff
  stopped being cheaper than regenerating. **Append each observation as one
  line to THIS entry** (`<date> <project>: <N> relevant files → patch|regen
  was cheaper`); replace `current` once three lines agree. Also open: how many
  of the six SHAPE diagrams a real map actually uses — SHAPE-4/5 are expected
  to be skipped often, which decides whether the catalogue is the right size.
- history: born provisional 2026-08-13 (no prior value)
- rollback: `ops/references/project-map.md` §6. Track the measurement as a
  ticket in whichever project ledger schedules it — but THIS entry is the
  authority and the write target, because a ledger in one project is invisible
  to the sessions in others that generate the data.

### Audit-trail rotation model — retired
- current: the chronological event-log-with-rotation model is retired. A
  rotation-triggered log grows as O(changes) while its value is O(rules), so
  rotation is permanent maintenance, and it evicts the OLDEST rationale, which
  is the most settled and therefore the most load-bearing. This registry
  replaces the forward-going role.
- why: measured across several rotation cycles, the growth kept recurring at
  a rate that made rotation a standing maintenance cost rather than an
  occasional cleanup.
- evidence: one rotation pass took the log from well over its cap back down
  by roughly a third, and normal same-day writes put it most of the way back
  within one session.
- history: chronological log + periodic rotation (birth) → retired for this
  registry (2026-08-11)
- rollback: n/a — a structural change, not a tunable value

## Standing rulings (user-origin — never auto-overturned)

### ops-relaxation level by main-loop model tier
- current: an Opus-tier main-loop model runs at **L1 (core relaxed)** in every
  project; a project CLAUDE.md may override with its own `ops-relaxation:`
  line. Others: ask, default L0. (2026-08-11)
- why: user ruling. L-numbers measure RELAXATION, not rigor — L0 is strictest.
- evidence: user directive, recorded this session.
  Surfaced by `hooks/ops_health_nudge.py` check 11, which fires when a project
  CLAUDE.md declares no level. It requires the VALUE (`ops-relaxation: L1`),
  not the key: until 2026-08-15 it tested `"ops-relaxation:" not in text` and
  the global CLAUDE.md carries that token in prose, so every derived project
  file passed vacuously and the check had never once fired correctly
  (`lessons.md` L-016). This repo's copy additionally runs it only when
  `ops/05-authority.md` is present — taking the hooks lane without the ops
  lane is supported here, and the key would otherwise be unsatisfiable.
- history: always-ask (birth) → Opus⇒L1 standing (2026-08-11); check 11
  made precise 2026-08-15
- rollback: `ops/05-authority.md` §2; global `CLAUDE.md` relaxation-gate bullet

### subagent model cost cap
- current: dispatches capped at haiku/sonnet (× effort axis); opus/fable need
  per-instance user approval.
- why: cost control on fan-out; the main loop may be above the cap while
  dispatches are not.
- evidence: enforced mechanically by `hooks/model_cap_guard.py`, which reads
  the Agent tool's own `model` argument — NOT `settings.json`. Verified stable
  across a session-default model change: no interaction between the two.
- history: unchanged since birth
- rollback: `ops/environment.md` "Subagent cost cap"

## Mechanisms

### instruction carriers that reduce startup cost
- current: only three — delete/merge, a `paths:`-scoped file under
  `~/.claude/rules/`, or a skill.
- why: `@path` imports and unscoped `rules/*.md` load at launch and save
  nothing; sinking an INTENT-triggered rule into `ops/` makes it a ghost rule
  (`lessons.md` L-011) because `ops/*` fires only via CLAUDE.md's project-
  operations clause.
- evidence: probed both directions on the current Claude Code release, then
  confirmed in a fresh session: both sunk rules appeared with `load_reason:
  path_glob_match` and neither at `session_start`. Re-verify after a CC
  upgrade.
- history: established 2026-08-11
- rollback: `ops/environment.md` "Instruction-loading mechanics"

### interop — what crosses to other agents
- current: **preference ports, method does not.** `portable-core.md` (the
  user's own standing rules) is transplanted; method depth is delegated to the
  target agent, which reads ITS OWN current docs. Every payload is leak-scanned
  before any write. **One target in the registry**, at profile **`full`**
  (rulings 2026-08-15; it was `light`, alongside two sync-off targets).
- why: no documentation can produce the user's own preferences; method is the
  opposite — it needs platform machinery to fire, and copied prose has no
  trigger. `full` because the target's role changed to dispatch target, and
  because the birth-budget argument for `light` inverted once measured.
- evidence: leak gate — 6/6 planted secret classes aborted the build, nothing
  written. Profile — with nothing deployed the target fell back to reading the
  source environment's `CLAUDE.md` (~16.5 KB of Claude-only mechanism); `full`
  is ~11 KB / 15 blocks, so the heavier profile cost the worker less. Port the
  SHAPE, not the number: whether `full` is cheaper depends on what YOUR target
  falls back to when nothing is deployed. Measure that before deciding.
  Surfaced by `hooks/ops_health_nudge.py` check 12, a stat()-only session
  screen whose only remedy is "run `status`" — why it routes instead of
  judging, and why the layer needed a caller at all: `lessons.md` L-016.
- history: reference-compile retired, leak gate added, curation narrowed to
  CLAUDE.md, two targets sync-OFF (2026-08-11); profile `light` → `full`,
  check 12 added, eval 8 replaced, and the two sync-off targets REMOVED from
  the registry outright (2026-08-15 — their rows had been frozen at a
  2026-07-10 verification under a heading calling those locations volatile, and
  one of the two applications had since been uninstalled; `lessons.md` L-005
  hit 3). Removing beats annotating: a registry row reads as a fact sheet.
- review-when: a second target goes live ("`full` costs less than the fallback"
  is measured against one target's own fallback and does not transfer), or that
  target changes the rules-precedence order that makes it the right baseline
- rollback: `interop-layer/` git history predating the 2026-08-11 retirement
