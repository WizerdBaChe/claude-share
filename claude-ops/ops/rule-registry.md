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
     needs more, it belongs in a lessons entry and this cites it. -->

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
- current: ~12K chars per `ops/*.md` (2026-08-06)
- why: same trim-vs-delete logic as CLAUDE.md, one tier down.
- evidence: a lossless trim pass capped out at ~11.2K without cutting distinct
  rules — the same pattern that justified the CLAUDE.md raise.
- history: 10K (birth) → 12K (2026-08-06, after the failed trim pass)
- rollback: `hooks/ops_health_nudge.py`; `40-maintenance.md` §3

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
- history: always-ask (birth) → Opus⇒L1 standing (2026-08-11)
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
  target agent, which reads ITS OWN current official docs. Every payload is
  leak-scanned before any write. codex sync OFF (maintained by hand from that
  side); antigravity OFF (unused); opencode is the only live target.
- why: no documentation can produce the user's own preferences, so those must
  be carried. Method is the opposite: it needs platform machinery to fire, and
  copied prose has no trigger.
- evidence: the retired reference-compile playbooks shipped ~20K whose own
  recorded degradation was "mechanical trigger → instructed read" — read
  either always or never. Leak gate verified adversarially: 6/6 planted secret
  classes aborted the build with nothing written.
- history: reference-compile retired, leak gate added, curation narrowed to
  CLAUDE.md (all 2026-08-11)
- rollback: `interop-layer/` git history predating the 2026-08-11 retirement
