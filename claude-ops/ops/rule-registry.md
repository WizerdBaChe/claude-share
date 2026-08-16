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
     - `references/<p>-decisions.md` D-nnn: a PROJECT's decisions
     - `audit-archive/`: historical event log, frozen 2026-08-11

     Entry fields: key / current / why / evidence / history / review-when /
     rollback. `review-when` is required ONLY for entries resting on a fact
     outside this repo (see REVIEW TRIGGERS below); an entry about this
     corpus's own numbers — the SKILL/CLAUDE.md caps, the trail cap, the
     standing rulings — correctly has none, so sweep check 12's count gap is
     expected to be roughly 7 and the finding is a NEW externally-dependent
     entry that arrived without one.
     `history` is the point of the file: it is the retrieval path that does
     NOT require git archaeology. Keep each entry ~6 lines; if the reasoning
     needs more, it belongs in a lessons entry and this cites it.

     PROVISIONAL VALUES (added 2026-08-13). A threshold shipped as a GUESS
     must still be registered, with `evidence:` starting with the literal
     token `PROVISIONAL` followed by (a) what observation would settle it and
     (b) the instruction that observations are appended to THIS entry. An
     unregistered guess has no home for the data that would correct it, so
     the data is never collected and the guess silently becomes permanent —
     which is indistinguishable from a measured value to every later reader.
     Registering it here buys three things a ticket cannot: `grep -n
     PROVISIONAL ops/rule-registry.md` enumerates every unsettled value
     (integrity-sweep check 11), the file has a liveness heartbeat
     (`ops_health_nudge.py` check 3, idle > 45 days), and it is
     project-independent — a ticket in one project's ledger is invisible to
     the sessions in OTHER projects that are the ones actually generating the
     observations. The point-of-use text must name this key as the write
     target; "revise later" with no destination is how a guess ossifies.

     REVIEW TRIGGERS (added 2026-08-14). An entry whose value depends on a fact
     OUTSIDE this repo — a harness default, a platform capability, a vendor
     doc, an unmeasured rate — carries a `review-when:` field naming the
     OBSERVABLE EVENT that invalidates it. Not a date: a date review fires
     when nobody has cause to look, and never fires when the fact actually
     moves. The field is greppable on purpose (`grep -n "review-when:"`,
     integrity-sweep check 12) because the practice already existed here in
     five different spellings across three different fields — "Re-verify after
     a CC upgrade" buried in `evidence:`, "promote on a second independent
     incident" inside `current:`, an ad-hoc `note:` on the references entry —
     which is a practice, not a mechanism: unenumerable, so unreviewable.
     Same three things PROVISIONAL buys, for the other failure class. -->

## Size and budget rules

### cap measurement unit — what every file cap below counts
- current: **BYTES** (`os.path.getsize`, so CRLF counts 2) for all FILE caps;
  chars for `DESC_CAP`; lines for `BODY_CAP`. (2026-08-12)
- why: bytes track TOKEN cost across mixed CJK/Latin — UTF-8 gives CJK 3
  bytes/char and tokenizers charge CJK ~3–4× Latin, so both scale together.
  Chars do not move with CJK and under-count the densest files.
- evidence: 7 rule files, 0–33% CJK — bytes/token 3.82–4.13 (±4%), chars/token
  2.26–3.99 (77%). `skill-trigger-dict.md` is 98% of cap in bytes, 58% in
  chars, and the corpus's most expensive file (~5,266 tok): the char reading
  calls the worst file the safest. Tokens estimated from CJK/ASCII composition,
  not tokenizer-measured — overturned by a `count_tokens` run reversing the
  spread.
- history: hook counted bytes from birth while `40-maintenance.md` §3 said
  "chars" — silent drift found 2026-08-12; resolved toward the hook, §3
  corrected, sweep check 7 added so it cannot recur silently.
- review-when: a `count_tokens` run reverses the bytes/chars spread (the
  refutation condition already stated in `evidence:`); or the corpus's CJK
  share moves far outside the 0–33% band the measurement covered.
- rollback: `backups/2026-08-12/`

### `CLAUDE_MD_CAP` — global CLAUDE.md always-loaded budget
- current: 17 * 1024 bytes (2026-08-16, closing T-015)
- why: CLAUDE.md is loaded IN FULL every session, so bytes here are the only
  instruction bytes that are unconditionally charged. Trim or merge, never
  append — and the cap's job is to force that question at a decision point,
  NOT to sit far enough away that nobody has to answer it.
- evidence: a real trim pass capped out at ~13.7K without cutting any distinct
  rule; raising beat deleting a rule that had no valid sink.
- T-015's argument for THIS raise, which it demanded be made on CLAUDE.md's own
  terms rather than inherited from the ops cap: a user-approved batch of 4 new
  rules + 2 amendments was checked against every sink first. None applied — the
  gate-authority rule fires on gate DESIGN in any language, the two PowerShell/
  Python rules fire on shell and script work rather than on a file pattern, and
  the invariant-authoring rule fires when writing rules, so no `paths:` glob
  under `~/.claude/rules/` can carry any of them and no skill owns them. That is
  exactly the condition under which this entry's own history says raising beat
  deleting. Two real merges were taken first (canonical-method + 2nd-report-of-
  the-same-symptom into one escalating rule; the relaxation gate compressed
  around its own standing ruling), saving ~550 B, so the raise is +2 KiB rather
  than +3. Cost: ~525 tokens per session, ~0.26% of a 200K context, prompt-
  cached after the first turn.
- headroom is DELIBERATELY thin: 17,327 B against 17,408 leaves ~80 B —
  amendment-only territory; no new rule fits without a sink, a merge, or an
  argued raise. That question being forced at the decision point is the cap's
  job. A cap with comfortable headroom is not a cap.
- history: 12K (birth) → 15K (2026-08-01, after the failed trim pass) → 17K
  (2026-08-16, T-015 closed; the 15K state had 276 B headroom, i.e. the next
  rule breached, which is what made it a ticket rather than a routine trim);
  17,004 → 17,327 B (2026-08-16 later, 3D-photo batch: 2 amendments +323 B —
  H-4 provider discriminator, H-2 representation rung — 0 new rules, per the
  amend-don't-append reading of the thin margin)
- review-when: any proposed global-CLAUDE.md change (headroom ~80 B fits no
  new rule — re-run find-a-sink / merge / argue-the-raise), or a rule in this
  file gains a valid `paths:` sink and can leave.
- rollback: `hooks/ops_health_nudge.py` `CLAUDE_MD_CAP`; `40-maintenance.md` §3

### `BODY_CAP` — SKILL.md body line cap
- current: 300 lines (2026-08-11)
- why: a SKILL.md body loads only when the skill fires, NEVER at session
  start, so this cap buys nothing at startup. The per-session skill cost is
  the frontmatter description, which has its own budget. 250 was shaping
  content instead of triggering extraction.
- evidence: commit 23ec0ba cut 37 lines from two SKILL.md bodies, added NO
  `references/` file, and left literature-search-extract at exactly 250 — the
  cap value. Corpus at the raise: 14 skills, median 153.5 lines, 62.9 B/line,
  one over 250 and none over 260 (so 260 bought a single nudge and no
  headroom). 300 lines ≈ 18.9K chars, paid once per invocation.
- history: 250 (birth) → 300 (2026-08-11)
- rollback: `backups/2026-08-11/ops_health_nudge.py.pre-bodycap-300`

### `DESC_CAP` — skill frontmatter description cap
- current: 800 chars hard / 700 birth budget (unchanged)
- why: THIS is the skill cost charged every session — descriptions are how the
  model picks a skill, so they are always loaded. Keep tight. Detailed
  disambiguation goes to `skill-trigger-dict.md` with a pointer back.
- evidence: commit 347412c ("slim 11 frontmatter descriptions to cut
  per-session tokens") targeted this deliberately, and correctly.
- history: 800/700 since birth
- rollback: `hooks/ops_health_nudge.py` `DESC_CAP`

### routing dict cap
- current: **24K bytes on `skill-trigger-dict.md`, ROLE = REVIEW TRIGGER**
  (2026-08-15, user ruling, raised from 20K). Firing means "run the routing
  audit and correct the entries it reports as fiction", NOT "extract detail".
- why: same class (b) argument as `ops file cap` — charged only on a routing
  miss — plus one this file has that the ops files do not. `tools/skill-routing
  -audit.py` measured, over 192 transcripts and 775 human turns, that the dict
  explains **0% of actual routing for every entry except workflow-checkpoint
  (21%)**. `config-self-audit` fired 28x and `product-design-thinking` 15x on
  vocabulary the dict does not list. So the file's defect is CONTENT VALIDITY,
  not volume, and the old "EXTRACT detail behind a pointer" remedy would have
  carefully reorganised fiction. Size is the wrong lever until the entries are
  true.
- **structural limit found while measuring (do not re-derive):** the dict models
  UTTERANCES only — which words the user says. `config-self-audit` is triggered
  by ARTIFACT CONTEXT (the thing under edit IS a config object); its fires were
  preceded by 「同意動手」 and 「權限L2，完成後走 config-audit 驗證」, none of
  which are registrable keywords. For a context-triggered skill the dict cannot
  be accurate by construction. Classifying entries by trigger shape before
  rewriting them is prerequisite work, not polish (L-011 shapes; user framing
  2026-08-15: 「skill 也需要先分類再路由」).
- evidence: **PROVISIONAL — 24K is a resize, not a measurement.** Chosen to
  clear the file's post-fix size (20,944 B) with headroom so the trigger fires
  on future growth. The file had sat at 20,376/20,480 = **99.5%** unseen because
  sweep check 15 walked `ops/*.md` and `CLAUDE.md` only; check 15 now derives
  every cap from the hook by name. What would settle it: the next three firings,
  one line each (`<date> <bytes>: audit found dead entries removed | audit found
  entries true, raised again`). Three "entries true" in a row means the dict
  finally describes real traffic and the cap can go back to being a size check.
- history: 20K since birth; the 2026-08-15 breach was the first time anything
  checked whether its contents corresponded to reality
- review-when: `tools/skill-routing-audit.py` reports coverage above ~50% for
  most entries — at that point the dict is load-bearing and its size argument
  changes. Also re-open if skill routing stops being description-driven.
- rollback: `backups/2026-08-15/ops_health_nudge.py.pre-dictcap-24k`

### skill trigger class registry
- current: **every skill carries a `class` + `source` + `on-fire` triple in
  `ops/references/skill-trigger-classes.md`**, read by
  `tools/skill-routing-audit.py --surface` (integrity-sweep check 18b). All 14
  local skills classified 2026-08-15.
- why: a firing rate is uninterpretable alone (user ruling 2026-08-15,
  「不能一竿子打死」). Before this, `motion-design` at 0 fires and
  `ai-coding-guardrails` at 0 fires printed identically; the first is a
  phase-gated skill with no UI phase in 43 days, the second is a real defect.
  The first reading of that table called **6 never-fired skills 6 defects; the
  classified count is 2** — an error of 3x, produced entirely by reading a
  number without its class.
- the second axis (user addition, same day): `on-fire` = `execute` |
  `ask-first`, orthogonal to class. Class decides WHEN to select; on-fire
  decides what selection COSTS. Test: does firing itself already spend
  something? `config-self-audit` executes (「叫到就驗，只會好不會壞」);
  `product-design-thinking` executes (its Phase 0 is a status question, so a
  wrong fire self-arrests — 15 fires, 0 false positives);
  `workflow-checkpoint` and `project-retrospective` ask first, both being
  heavyweight and file-writing.
- **the classification rule, which is the reusable part:** routing = text that
  changes WHETHER OR WHEN a skill is selected; procedure = text that only
  changes what happens after. Phrasing does not decide it. "never scan
  unprompted" reads as an instruction but moves the selection → routing.
  "ALWAYS asks per category" also reads as an instruction but only constrains
  execution → procedure. Applying it dropped `config-self-audit` from a
  first-pass 15.6% to 3.3% and `project-retrospective` from 49.1% to 34.3%
  before any edit — i.e. half of the original alarm was my own misclassification.
- evidence: measured, not resized. 14 descriptions, procedure share 0-34%;
  the three worst (`project-retrospective` 34.3%, `env-cleanup` 33.4%,
  `skill-share-packaging` 27.0%, the last also at 97.5% of DESC_CAP =
  saturated) were rewritten to 0% by MOVING text into bodies that already
  carried it — each verified present before removal, none compressed (P-003).
- why not frontmatter: the loader takes `name` and `description` only, and an
  extra key would be charged to every session for a fact only a periodic audit
  reads. Class (b) file instead.
- review-when: a skill is added or removed under `~/.claude/skills/`, or the
  audit prints STALE for any `proc:` fragment (the description moved and the
  classification did not follow).
- a sixth class was forced within hours of the first five: `second-order`, for a
  skill reached mainly through a HANDOFF edge. `ai-coding-guardrails` fired 0x
  while the two skills that hand off to it fired 0x and 1x — its zero was
  downstream of theirs, and nothing on its own routing surface could have
  changed it (T-017, resolved NOT A DEFECT). Expect more classes: five was a
  first cut, not a taxonomy.
- open against it: T-018 (`asset-vault` Mode B is omission-shaped, so no firing
  count can measure it).

### ops file cap
- current: **18K bytes per `ops/*.md`, and its ROLE is a REVIEW TRIGGER, not a
  budget** (2026-08-15). **Scope: `lessons.md` and `rule-registry.md` are exempt**
  (`SIZE_CAP_EXEMPT`) - their size tracks the CORPUS, not bloat, so an over-cap
  reading has no extract remedy and can only nag forever. Their real degradation
  checks are elsewhere: `LESSON_CAP` (entries, not bytes) and S4.1 ghost rules.
- why: the budget reading was never supported by a measurement, and Phase 2
  supplied one that refutes it. The entire always-loaded instruction surface we
  control is ~39.8 KB (~10,200 tokens) - about 5% of a 200K context, and
  prompt-cached; compaction occurs in 1.2% of 255 instrumented sessions; a
  SINGLE `general-purpose` dispatch costs ~49K tokens, five times the whole
  surface. Trimming an on-demand ops file therefore buys approximately nothing.
  What the number is still good for is noticing that a file grew enough to
  deserve a look - so **firing means "review this file", and raising the value
  after that review is the INTENDED outcome, not a failure of discipline.**
  The old procedure treated every raise as a defeat requiring a failed trim pass
  as evidence, which is why three raises carry the same apologetic sentence.
- **class boundary (do not generalise this):** ops files are class (b),
  charged only when something routes to them. `CLAUDE_MD_CAP` is class (a),
  charged unconditionally every session, and it is deliberately NOT raised with
  this change - the same 5% measurement applies, but class (a) is the only
  instruction spend that is unavoidable, so relaxing it needs its own argument
  rather than this one's momentum. CLAUDE.md sits at 98.2% and will breach on
  its next edit; that is a known open item, not an oversight.
- evidence: **PROVISIONAL - 18K is a resize, not a measurement.** It was chosen
  to clear the three files reviewed on 2026-08-15 (`40-maintenance.md` 15,294 B,
  `60-bootstrap.md` 15,042 B, `20-dispatch.md` 14,650 B) with real headroom, so
  the trigger fires on FUTURE growth rather than on the state we just examined
  and accepted. What would settle it: the next three firings, each recorded here
  as one line (`<date> <file> <bytes>: review found extractable concrete |
  review found nothing, raised again`). Three "found nothing" in a row means the
  trigger is measuring age rather than bloat and should be replaced by a
  growth-rate check instead of another raise.
- history: 10K (birth) -> 12K (2026-08-06, after a failed trim pass) -> 15K
  (2026-08-13, after another) -> 18K (2026-08-15, role changed to review
  trigger; the first raise justified by a measurement of what the bytes cost
  rather than by an inability to cut them)
- review-when: three consecutive firings resolve as "reviewed, nothing to
  extract, raised" (see evidence); OR a measurement shows the always-loaded
  surface is no longer cached or no longer a small share of context, which
  would restore the budget reading.
- rollback: `backups/2026-08-15/ops_health_nudge.py.pre-sizecap-18k`;
  `40-maintenance.md` S3 table row

### `TRAIL_SIZE_CAP` — audit trail rotation trigger
- current: 60 * 1024 chars, but **the rotation model is being retired** —
  see `audit-archive/` frozen header and this file's own premise.
- why: the trail grew as O(changes) while its value is O(rules), so rotation
  was permanent maintenance. This registry replaces the forward-going role.
- evidence: 2026-08-11 — rotating 17 entries took the file 76,207 → 49,108 B,
  and three entries written the same day put it back to 61,285 B. At that rate
  rotation recurs every few working days.
- history: 60K (birth) → retired for new rationale (2026-08-11)
- rollback: `backups/2026-08-11/Global_skill_update.md.pre-rotation`

### map STALE thresholds — when a project map stops being trusted
- current: DRIFT at 1–5 relevant changed files, STALE above 5 OR on any
  structural path (package manifest, directory added/removed). Relevance is
  scoped to the map's `covers` globs minus `excludes` (2026-08-13). Point of
  use: `ops/references/project-map.md` §6.
- why: scoping to `covers` is the cheap accuracy win — a docs-only commit must
  not invalidate a code map. The 5 and the structural list are NOT reasoned
  values; they are the smallest thing that could work, shipped as declared
  guesses rather than picked silently, because the same trap was already hit
  twice (the DocsGap uncovered-folder threshold, the ArchLens hotspot top-N).
- evidence: **PROVISIONAL — no measurement exists.** What settles it: two or
  three real cold-start projects each completing a FRESH → DRIFT → STALE
  cycle, recording the relevant-file count at which patching from the diff
  stopped being cheaper than regenerating. **Append each observation as one
  line to THIS entry** (`<date> <project>: <N> relevant files → patch|regen
  was cheaper`); replace `current` once three lines agree. Also open: how many
  of the six SHAPE diagrams a real map actually uses — SHAPE-4/5 are expected
  to be skipped often, which decides whether the catalogue is the right size.
- history: born provisional 2026-08-13 (no prior value)
- rollback: `ops/references/project-map.md` §6; tracked as T-010 in
  `references/claude-config-tickets.md` (that ledger is the SCHEDULE, this
  entry is the AUTHORITY and the write target — a ledger in one project is
  invisible to the sessions in other projects that generate the data)

## Standing rulings (user-origin — never auto-overturned)

### ops-relaxation level by main-loop model tier
- current: an Opus-tier main-loop model runs at **L1 (core relaxed)** in every
  project; a project CLAUDE.md may override with its own `ops-relaxation:`
  line. Others: ask, default L0. (2026-08-11)
- why: user ruling. L-numbers measure RELAXATION, not rigor — L0 is strictest.
- evidence: user directive, this session.
  Surfaced by `hooks/ops_health_nudge.py` check 11, which fires when a project
  CLAUDE.md declares no level. It requires the VALUE (`ops-relaxation: L1`),
  not the key: until 2026-08-15 it tested `"ops-relaxation:" not in text` and
  the global CLAUDE.md carries that token in prose, so every derived project
  file passed vacuously and the check had never once fired correctly
  (`lessons.md` L-016). The share edition gates it on `ops/05-authority.md`
  existing — an adopter taking the hooks lane without the ops lane cannot
  satisfy the key. 21/21: `tools/ops-health-test/test_ops_health_nudge.py`,
  which runs against either copy and asserts the opposite outcome per edition.
- history: always-ask (birth) → Opus⇒L1 standing (2026-08-11); check 11 made
  precise 2026-08-15
- rollback: `ops/05-authority.md` §2; global `CLAUDE.md` relaxation-gate
  bullet; check 11 → `backups/2026-08-15/`
  `ops_health_nudge.py.pre-check11-precision`

### subagent model cost cap
- current: dispatches capped at haiku/sonnet (× effort axis); opus/fable need
  per-instance user approval.
- why: cost control on fan-out; the main loop may be above the cap while
  dispatches are not.
- evidence: enforced mechanically by `hooks/model_cap_guard.py`, which reads
  the Agent tool's own `model` argument — NOT `settings.json`. Verified
  2026-08-11 when the session default moved haiku → sonnet: no interaction.
- history: unchanged since birth
- rollback: `ops/environment.md` "Subagent cost cap"

### `~/.claude/AGENTS.md` — keep on disk, out of version control
- current: kept, untracked. Do NOT delete and do NOT re-add to git. (2026-07-09)
- why: USER ruling. It is a codex env-copy leftover — not the interop source
  (`interop/portable-core.md` is) and not a deploy target.
- evidence: its pointers (`~/.Codex/ops/05-authority.md`) resolve to nothing
  since the codex ops tree moved to `ops/codex-ops/`, which makes it *look*
  like deletable rot. **This entry exists because that ruling had been evicted
  from the live audit trail by commit 23ec0ba and survived only in gitignored
  `backups/` and `memory-archive/` copies; it was recovered by luck during a
  2026-08-11 cleanup that would otherwise have deleted the file.**
- history: ruling 2026-07-09; rescued into this registry 2026-08-11
- rollback: n/a — a ruling, not a setting

### top-level `references/` — tracked
- current: TRACKED (2026-08-11), except the two generated dashboard views,
  which stay ignored by name because `tools/project-dashboard.py` rebuilds them.
- why: the 2026-07-19 ruling called them "semi-staging notes" and that was
  true then. It is not true now — the directory holds the project memory
  layer: phase logs (the resume anchor a fresh session reads FIRST), decision
  journals, glossaries, ticket ledgers, design/evaluation records. All of it
  passes the vc-boundary test. The semi-staging role the ruling protected is
  now covered by `drafts/` and `archive/`, both still ignored.
- evidence: 13 files inventoried 2026-08-11; only the 2 generated ones failed
  the test. Leak-scanned with `interop.py`'s patterns before tracking: 3 hits,
  all "account name in a path", which the repo already carried in 6 tracked
  files including `settings.json`, and there is no git remote — so tracking
  added no new exposure.
- history: gitignored 2026-07-19 → tracked 2026-08-11 (user ruling, on the
  condition that the staging role had a replacement — it does)
- rollback: `.gitignore`; re-add `/references/` and `git rm --cached -r`
- review-when: a git REMOTE is added. The no-remote premise is the only reason
  the three account-name hits were acceptable; re-run the `interop.py` leak
  scan before the first push. (Was an ad-hoc `note:` until 2026-08-14.)

## Harness defaults — where the local layer narrows within them

<!-- The harness injects instructions this side cannot edit or override, and
     whose source is not visible from here (verified 2026-08-14: none appear in
     `settings.json`, and there is no `output-styles/` directory). An entry
     records a harness default, the narrower local rule, and the mechanism that
     makes the narrowing fire.

     RULE OF CONSTRUCTION (user ruling 2026-08-14): NARROW WITHIN, NEVER
     CONTRADICT. Where the harness withholds an action pending user
     authorisation, the mechanism surfaces the decision to the user; it does
     not take the action. Where the harness states a default and lists
     alternatives, picking a listed alternative with a stated reason is
     narrowing — asserting the default is wrong is not. Full statement and
     failure mode: `lessons.md` L-011 harness-compatibility constraint.

     Every entry carries `review-when:`, because the injected text changes with
     the product, silently, and on someone else's release schedule. The whole
     class was invisible until 2026-08-14: `grep -rn "AgentTool|unless the
     user|user requested" ops/ CLAUDE.md rules/` returned ZERO — eight
     conflicts, none of them written down anywhere. -->

### dispatch — "Do not spawn agents unless the user asks"
- harness: session guidance, escalated by the Agent tool's own description —
  "A task with 'multiple angles,' 'thorough,' or several parts is not a request
  to spawn; handle it inline with your own tools." That is the exact task shape
  `OPS.md` hard rule 1 sends OUT, so the two are opposed, not merely silent.
- local narrowing: the gate does not dispatch and does not argue. It surfaces
  the threshold crossing so the USER can ask — which is what the harness wants.
- mechanism: `hooks/fieldwork_threshold_notice.py`, PreToolUse on
  `Read|Grep|Glob`, thresholds from `20-dispatch.md` §1. SHADOW first: the rate
  is unmeasured, and the 2026-08-14 session that found this would itself have
  tripped it repeatedly.
- why not a document: this is an OMISSION (L-011 P1). No document fires at the
  moment the model silently decides to read the files itself.
- evidence: **PROVISIONAL — the §1 numbers are a delegation heuristic and have
  never been measured AS A GATE TRIGGER.** First live run 2026-08-14 (headless
  `claude -p --model sonnet`, 2.1.226) proved REGISTRATION, not just logic: the
  probe fired inside a real session, and so did `InstructionsLoaded`. It also
  found a defect the synthetic tests could not — an unlimited `Read` was charged
  the 2000-line cap, so `lines~2000>200` tripped on the FIRST read of any
  session regardless of size; now counts the file's real length (bounded).
  2026-08-14 28757311: lines~2000 → false-positive (fixed at source).
  2026-08-14 d7f966a5: files=4>3 → **false-positive**. Classified 2026-08-15
  against that session's transcript, not from the filenames: the task was sync
  the remote, prune branches, align naming with the phase-log. The four files
  are four stages of ONE pipeline (`adapters/codexJsonl`, `denoise/denoiser`,
  `distill/distiller`, `text/preamble`) — orientation reading for a naming
  judgement the main session had to make itself. A subagent would have returned
  a summary and destroyed the detail the decision needed.
  2026-08-15 7c31fa3b: lines~201>200 → **false-positive, and a source defect**.
  The file was this session's OWN 201-line analysis report in its scratchpad.
  Delegation can never be the answer for one of those — the file exists BECAUSE
  the main session produced it. Fixed at source (`is_own_output`), so this class
  of trip stops rather than being counted as evidence about the thresholds.
  **Reading so far: 3 rows, 3 false positives, 2 of them source defects rather
  than threshold errors** — the same shape as the sibling precedent below. Both
  defects were found by reading the rows, never by reasoning about the numbers,
  which is the argument for leaving the probe in shadow rather than tuning it.
  Not enough to graduate OR to kill: an organic trip that is genuinely
  should-delegate has not yet appeared, and its absence is not yet evidence. What settles it: rows in
  `telemetry/fieldwork-shadow.jsonl` from real sessions, each classified by
  hand as "should have been delegated" or "correctly stayed in the main
  session". **Append each judgement as one line to THIS entry** (`<date>
  <session-prefix>: <reasons> → should-delegate|false-positive`). Graduate out
  of shadow only when the false-positive share is low enough that a notice is
  worth the interruption; if it is not, the finding is that §1's thresholds
  describe delegation ADVICE and cannot serve as a gate — which is itself the
  answer, and the probe comes off rather than being tuned until it agrees.
  Sibling precedent: `delivery_gate_shadow.py` returned 3/3 false positives on
  its first real run.
- cost: PreToolUse on `Read|Grep|Glob` is the high-volume matcher the browser
  hooks deliberately avoid — ~100ms Python start on every one. Acceptable for a
  bounded measurement window, NOT as a permanent tax. Sweep check 14 exists to
  make an idle probe visible.
- review-when: Agent-tool description or session guidance changes wording on a
  Claude Code upgrade; OR the shadow log has enough classified rows to decide;
  OR 30 days pass with the probe registered and no decision taken — at which
  point the latency is being paid for nothing.
- rollback: unregister from `settings.json`; the hook is inert without it.

### in-app Browser pane — "Already loaded. Default to this."
- harness: `<browser_surfaces>` names the pane the default surface; it also
  lists claude-in-chrome as an alternative, so choosing that IS narrowing.
- local narrowing: allowlist, not blocklist — see the Mechanisms entry
  `in-app Browser pane` below for the current state and its evidence.
- review-when: `<browser_surfaces>` wording changes; OR a third crash occurs;
  OR `telemetry/browser-nav.jsonl` shows a DENY the user had to override.

### workflows — "Do not use workflows unless the user requested it"
- harness: session guidance + the Workflow tool description, which additionally
  ships a COMPLETE rival dispatch doctrine (pipeline-vs-barrier, four quality
  patterns, a 15-agent size guideline) that overlaps `20-dispatch.md` §2/§4/§5
  and never references it.
- local narrowing: none needed for the prohibition — `enableWorkflows: true` is
  a capability, not a standing request, and the local layer agrees the user
  opens it. What IS unresolved: which doctrine governs once one is opened.
- current: DORMANT — no workflow has been run here. Recorded so it is not
  rediscovered as new; do NOT write reconciliation rules for a dead path.
- review-when: the first time a workflow is actually requested. That is the
  moment to reconcile the two doctrines, and not before.

### scratchpad — "Always use this scratchpad directory for ALL temporary files"
- harness: per-session scratchpad path, injected every session.
- local narrowing: `drafts/` is NOT a temp directory — `70-evolution.md` §2
  requires rule-change artifacts at `drafts/<date>-<name>/` with `APPLY.md`,
  and this registry's `references/` entry calls drafts a RECORD location.
  Scratchpad is session-scoped and discarded; a rule-change artifact written
  there loses the audit trail the §2 procedure exists to create.
- current: NOT MECHANISED (deferred by the user 2026-08-14 with the Artifact
  entry). Text rule only: temp → scratchpad, rule-change artifact → `drafts/`.
- review-when: a rule-change round is found to have left no `drafts/` artifact;
  that is the first real instance and it converts this into a P1 gate on Write.

### Artifact publishing — "not fully delivered while it lives only in a local file"
- harness: the Artifact tool description actively pushes finished deliverables
  to a claude.ai-hosted page as the completion step.
- local narrowing: none exists. Asymmetry recorded 2026-08-14 — the interop
  egress path is leak-scanned before any write (6/6 planted secret classes
  aborted the build; see the `interop` entry), and this egress path has NO
  gate while carrying an injected push toward routine use.
- current: NOT MECHANISED (deferred by the user 2026-08-14). Artifacts default
  to private, so this is a structural asymmetry, not a live leak.
- review-when: the first Artifact publish from this environment; or the
  default-private behaviour changes.

### External dispatch path — a second dispatch carrier with a one-way asymmetry
- what: `tools/extdispatch/` dispatches work to free external model tiers
  (opencode/Zen keyless, NVIDIA NIM keyed) over `opencode serve`. Path choice
  lives in `20-dispatch.md` §4a, redlines and disclosure in §4b, detail in
  `ops/references/external-dispatch.md`, environment facts in `environment.md`.
- mechanised: six gates in code (redline / allowlist / grant / daily cap /
  concurrency lock / full-content audit) plus
  `hooks/extdispatch_entrypoint_guard.py`, which denies direct `opencode` and
  hand-rolled POSTs to the local serve API so extdispatch is the only shell
  entry point. Marker escape: `[user-approved-direct-opencode]`.
- NOT mechanised, dispatcher-owned: "never dispatch a TASK about a project's
  own `.claude`-class internals". A worker's `grep` is not gated by its path
  argument, so no permission rule can carry this; the deny rules in
  `opencode.jsonc` are defence in depth and are labelled in-file as not a
  control. Also not mechanised: the disclosure duty (say which project is going
  out and why it is safe) and work-card sharding.
- honest limit: the hook sees shell commands, not a Python script that imports
  the HTTP helper (`ratecheck.py` is exactly that, and is a named exception).
- review-when: the Zen roster changes (`GET /config/providers` stops reporting
  7 active models); OR any rate refusal is observed on the Zen tier, since the
  current premise is only "not the bottleneck at single-digit RPM, serialised";
  OR opencode's permission model starts gating `grep` by path, which would let
  the `.claude` rule become mechanical; OR the `agentic` chain is re-argued,
  since its first version led with NIM on a `tool_call: null` catalogue field
  read as "cannot" when it means "unreported".

### low-severity drift (recorded so it is not rediscovered as new)
- Bash tool says avoid `grep/sed/find`; `integrity-sweep.md` is 11 bash greps
  BY DESIGN ("grep-only, seconds, no judgement"). The harness carries an
  "unless explicitly instructed" exemption, so the sweep is legal — a note now
  sits in that file so a later session does not helpfully rewrite it into Grep
  tool calls and destroy the property that makes it cheap.
- `Co-Authored-By: Claude Opus 5` commit trailer: **RESOLVED 2026-08-15, user
  ruling — KEEP IT.** The harness asks for it and `COMMIT-TEMPLATES.md` was
  silent, so one of the two was being ignored on every commit; the silence is
  now closed on the side of keeping. Consequence worth stating: the trailer
  names a MODEL, so `git log --author` stays a poor query for "what did the
  model write" while the trailer is the reliable one. Do not strip it from
  history — commits made before the ruling are mixed, and rewriting them would
  destroy the only record of when the practice started.
- Mid-session reminders push `TaskCreate`/`TaskUpdate`; the local progress
  system is the `references/` ticket ledger, which is durable. The harness task
  list is per-session. Keep the ledger; the reminder is advisory.
- review-when: any of the three stops being cosmetic — i.e. produces a wrong
  artifact rather than a stylistic difference.

### subagent instruction surface — what reaches a worker, and what it costs
- current: **`Explore` and `Plan` are the ONLY subagents that omit global
  CLAUDE.md** (and the parent's git status). Every other built-in AND every
  custom `agents/*.md` role loads the full CLAUDE.md hierarchy. There is no
  frontmatter field or per-agent setting that changes this. **Auto memory
  (`MEMORY.md` + its fact files) reaches NO subagent at all**, fork excepted;
  a worker that needs a memory fact must be given it in the dispatch prompt.
  Preamble cost of one `general-purpose` dispatch: **~49,200–49,700 tokens**
  with ZERO tool uses and a one-word answer.
- why it matters: (1) the cost is roughly FIVE TIMES the entire always-loaded
  surface of a main session (~10,200 tokens, cached, once), so `OPS.md` hard
  rule 1 buys MAIN-CONTEXT preservation, not total tokens — `20-dispatch.md`
  §8 now carries the number. (2) The auto-memory gap contradicts nothing in
  `70-evolution.md` §3, but it means knowledge routed to auto-memory is
  invisible to every worker; §2's "self-sufficient materials" contract is the
  only thing carrying it across, and that is now a load-bearing reason rather
  than a nicety. (3) Explore/Plan getting no rules is by design — the docs'
  own mitigation is that the MAIN conversation reads their results with full
  context, so a rule that must reach them goes in the delegation prompt.
- evidence: doc statement at `code.claude.com/docs/en/sub-agents` §what loads at
  startup (read 2026-08-15) CORROBORATED on both sides of its own falsifiable
  claim by probes the same day: `Explore` returned NO/NO/NONE/NO, and
  `general-purpose` returned YES/YES/YES listing all nine CLAUDE.md section
  headings verbatim. Cost: two probes, sonnet, identical minimal prompt —
  49,711 and 49,227 tokens (1% apart). The planned 4-role probe (~200K tokens)
  was CANCELLED as redundant once the doc made a categorical claim that the
  existing two probes already tested from both directions.
- history: the Explore exception sat unverified in `20-dispatch.md`'s roster
  table from birth; cost was never measured; the auto-memory gap was unknown
  until 2026-08-15
- review-when: a Claude Code upgrade changes the "what loads at startup" list —
  it is product behaviour, not contract, and the whole entry rests on one doc
  page plus two probes against build 2.1.226/2.1.229.
- rollback: n/a — a measurement, not a setting

## Mechanisms

### delivery gate (`hooks/delivery_gate_shadow.py`)
- current: SubagentStop, SHADOW ONLY — computes `would_block`, never blocks.
  Enforcement stays off until the false-positive rate is measured.
- why: a gate that fires wrongly is worse than no gate; and "a verification
  command appeared" is Goodhart-able.
- evidence: `SubagentStop` hands over the MAIN session's `transcript_path`, so
  the first real run returned 3/3 false `verified=True` until
  `resolve_transcript()` was added. Separately measured: `is_error` is exactly
  "shell exit != 0" (no exit code is persisted at all), so `cmd || true` and
  `cmd | head` report success while failing — phase 2 needs a stdout sniff.
- history: born shadow 2026-08-11; enforcement not yet enabled
- review-when: the shadow log has enough rows to compute a false-positive rate
  (that measurement IS the enable/disable decision); or `SubagentStop`'s payload
  shape changes on a Claude Code upgrade, which is what `resolve_transcript()`
  works around.
- rollback: unregister from `settings.json`; commits 4239d27 / 44fe7e4

### context runway (`hooks/context_runway_shadow.py`)
- current: UserPromptSubmit, SHADOW ONLY — logs the notice it would emit,
  stdout stays empty even though this is one of only three events whose stdout
  Claude would actually see (`SessionStart`, `UserPromptSubmit`,
  `UserPromptExpansion`; verified against the hooks reference 2026-08-15).
- fires on a CONJUNCTION: context >= a band AND no phase-log write has happened
  yet in this session. Context alone is not the trigger — it fires in 65% of
  sessions at 150k; adding the second condition is what makes it mean anything.
- threshold: **PROVISIONAL**, bands (150k, 300k). There is NO defensible
  fraction-of-window number available: main-loop context grows smoothly to 777k
  across 149 archived sessions with no pile-up at any limit, so the window
  cannot be recovered from transcripts and a percentage would be invented. The
  bands are anchored to the local distribution instead (median session maximum
  189k). Deliberately liberal: a shadow row costs nothing, and the window
  exists to find the band worth graduating.
- why not a wider skill description: measured cost asymmetry. A dismissed hook
  notice is ~60 tokens; routing `workflow-checkpoint` and being told "no" loads
  its whole 10,379-char SKILL.md, ~2,600 tokens — about 43x. Being liberal is
  cheap on the hook and expensive on the routing surface, so the liberalisation
  goes here and the description is left alone (user ruling 2026-08-15).
- evidence: checkpoint rate by session size PLATEAUS at ~63% instead of
  climbing (<100k 14%, 100-200k 46%, 200-300k 50%, 300-400k 65%, >400k 63%);
  29 of the 71 sessions past 200k never wrote one. Upper bound, not a defect
  rate — "no checkpoint" is not "should have had one". Time-ordered replay of
  the shipped rule over the same 149 sessions predicts 59% get >=1 notice.
- what it must never say: "this looks like a phase boundary". Phase 3 measured
  that boundaries are SPOKEN; context length is uncorrelated with them. The
  only sanctioned framing is "runway is short, checkpoint while it is cheap".
- history: born shadow 2026-08-15 (T-019). Two defects found by running it
  against real transcripts before wiring: a tail-only read returned 0 for a
  session whose last 256KB held no usage record, and a trailing all-zero
  `usage` block was taken at face value as 0 tokens for a 564k session.
- review-when: integrity-sweep check 20 finds rows to classify; or the notice's
  landing accuracy has been judged on real rows (that judgement IS the
  graduation decision, and it judges the WORDING at that moment, not the band).
- rollback: unregister `UserPromptSubmit` from `settings.json`.

### in-app Browser pane — what may be loaded into it
- current: **ALLOWLIST** (2026-08-14, user ruling). Loopback hosts (`localhost`,
  `127.0.0.1`, `::1`, `*.localhost`, `0.0.0.0`) are allowed by the hook itself;
  anything else needs an entry in `hooks/browser-pane-allowlist.json`, which
  only the user edits. Everything else is DENIED for `mcp__Claude_Browser__*`
  only — `mcp__claude-in-chrome__*` is a separate Chrome process and is never
  denied. Denials are logged with `"loud": true` and the denial text ORDERS the
  agent to report the host to the user and offer the allowlist edit, so a deny
  reaches the person who can adjudicate it instead of being absorbed silently.
  `browser-pane-blocklist.json` is retained: it no longer governs, but its
  recorded crash reasons make a denial message specific.
- why the inversion: a blocklist can only encode hosts that already cost us
  something, and the 2026-08-12 crash came from a host nobody had ever seen —
  so the blocklist was structurally incapable of preventing the event that
  motivated it. What IS knowable in advance is the safe set. Accepted cost: a
  first-time legitimate host is denied once.
- harness relation: `<browser_surfaces>` calls this pane the default surface and
  that instruction cannot be edited from here. The denial picks
  `claude-in-chrome` — an alternative the same block lists — and states why.
  Narrowing within the harness's menu, not overriding it (L-011).
- evidence: 7/7 hook cases pass (2026-08-14): loopback + `*.localhost` allow,
  third-party deny, claude-in-chrome untouched, known crasher carries its
  recorded reason, `back`/`forward` and `preview_start {name}` pass through.
  Log file confirmed created on first write — it had never existed before, so
  the previous "every navigation is LOGGED" claim was unproven for two days.
- history: L-013 scope rule in lessons only (2026-08-12) → logging + blocklist
  (2026-08-12) → allowlist + loud reporting (2026-08-14)
- review-when: `<browser_surfaces>` changes wording on a Claude Code upgrade;
  OR sweep check 13 shows `"loud": true` rows the user never adjudicated;
  OR a legitimate host is denied twice, which means the allowlist is too tight.
- why: the pane shares the desktop app's GPU child. A page can crash it,
  Electron does not relaunch it, and the in-flight turn of every session in the
  app dies with it — a blast radius none of L-009/L-010/L-011 anticipated,
  because those treat the pane as an instrument to read FROM, not a surface
  that executes hostile content.
- evidence: 2 crashes / ~180 pane opens in one log, both 3-4s after the same
  `preview_start` URL; the app's own `main.log` never records the URL, so
  without the new log the trigger is unattributable. Detail: L-013.
- history: born 2026-08-12 (log + blocklist); CLAUDE.md line deliberately
  deferred
- rollback: unregister `browser_pane_scope_guard.py` from `settings.json`;
  the blocklist is inert without it

### instruction carriers that reduce startup cost
- current: only three — delete/merge, a `paths:`-scoped file under
  `~/.claude/rules/`, or a skill.
- why: `@path` imports and unscoped `rules/*.md` load at launch and save
  nothing; sinking an INTENT-triggered rule into `ops/` makes it a ghost rule
  (L-011) because `ops/*` fires only via CLAUDE.md's project-operations clause.
- evidence: probed both directions on Claude Code 2.1.220, then confirmed in a
  fresh session (T-007): both sunk rules appeared with `load_reason:
  path_glob_match` and neither at `session_start`. MEASURED 2026-08-14 over
  `telemetry/rule-loads.jsonl` (332 events, 241 distinct sessions): CLAUDE.md
  loads at `session_start` in 100% of them; `rules/*.md` fired 8 times
  (`frontend-layering` 7, `shader-failure-modes` 1) — a 3.3% session rate that
  is ACCURACY, not failure, since both are meant to fire only on matching
  files. `ops/*` appears 0 times, but `InstructionsLoaded` does not cover files
  read with the Read tool, so the true statement is that the `ops/` firing rate
  is UNINSTRUMENTED — which is why `ops/` may hold authority and record but
  must not be the sole carrier for a silent-failure rule.
  **Scope correction 2026-08-14: those rates are MAIN SESSIONS ONLY.** A probe
  dispatch proved `InstructionsLoaded` does not fire in subagent context while
  the subagent demonstrably HAS the file — so the whole subagent load surface
  is uninstrumented too, and self-report was the only working instrument.
  **Counterexample 2026-08-16 (extension-glob blindness, H-5):** a low fire
  rate reads as ACCURACY only when the rule's language cannot be EMBEDDED in
  other file types. `shader-failure-modes` was extracted from the 3D Photo
  Synthesis Engine's own GLSL pitfalls, yet that repo has ZERO files matching
  `**/*.{glsl,frag,vert,vs,fs}` or `shaders/**` (verified 2026-08-16, tracked
  and untracked) — every line of GLSL lives in template strings inside
  `frontend/src/parallax.ts` / `ldi.ts`. Matching WORK existed (three rounds
  of GLSL debugging, one of them the exact silent-blank the rule describes);
  matching FILES did not. So 3.3% is accuracy for `frontend-layering` but
  blindness for `shader-failure-modes` on its own source project.
- history: established 2026-08-11; firing rates measured 2026-08-14;
  glob-blindness counterexample recorded 2026-08-16
- review-when: any Claude Code upgrade (the probe was against 2.1.220 and the
  loading mechanics are undocumented product behaviour); re-run the
  `rule-loads.jsonl` breakdown, which now has a baseline to compare against.
  Also: an extension-glob-dispatched rule's fire rate may be read as accuracy
  ONLY after checking the rule against its own source project — if the globs
  cannot see that project, the low rate is blindness, not accuracy.
- rollback: `ops/environment.md` "Instruction-loading mechanics"

### advisory-output surfacing — ops-health check 13
- current: the session screen lists OPEN/PARTIAL advisory outputs and flags
  post-2026-08-16 ones born without a status line. Scope: candidates files
  (`outputs/retrospectives/global-rule-candidates-*.md`) + experiment metrics
  (`outputs/experiments/*/metrics.md`); `outputs/skill-reviews/` excluded —
  its disposition convention (D-032) already carries status.
- why: handled-but-unannounced artifacts cost a full read to discover they
  are spent (user finding 2026-08-16). A maintained index file was rejected
  as a silently-rotting control; the surface is DERIVED from the files at
  each session start instead. Convention + entry command + cleanup semantics:
  `rules-usage-dict.md` §7 "advisory-output status line".
- evidence: two-sided fixture run 2026-08-16 — planted OPEN and missing-line
  fixtures both surfaced, an old-dated status-less fixture stayed silent
  (grandfathered), and the real corpus (3 artifacts, all spent) prints
  nothing.
- history: born 2026-08-16 (`drafts/2026-08-16-advisory-status-check/APPLY.md`;
  user commissioned inline, chip task_f9f07005 dismissed in its favour)
- review-when: a new advisory artifact class appears under `outputs/` (extend
  the globs in the same commit that adds the consumer — manifest standing
  rule), or `skill-reviews` drops its disposition convention.
- rollback: `backups/2026-08-16/ops_health_nudge.py.pre-check13`

### interop — what crosses to other agents
- current: **preference ports, method does not.** `portable-core.md` (the
  user's own standing rules) is transplanted; method depth is delegated to the
  target agent, which reads ITS OWN current docs. Every payload is leak-scanned
  before any write. **opencode is the only target in the registry** (user
  ruling 2026-08-15), at profile **`full`** (same day, was `light`).
- why: no documentation can produce the user's own preferences; method is the
  opposite — it needs platform machinery to fire, and copied prose has no
  trigger. `full` because opencode became a dispatch target, and because the
  birth-budget argument for `light` inverted once measured.
- evidence: leak gate — 6/6 planted secret classes aborted the build, nothing
  written. Profile — with nothing deployed opencode fell back to
  `~/.claude/CLAUDE.md` (~16.5 KB of Claude-only mechanism); `full` was
  11,129 B / 15 blocks at adoption (2026-08-16: 13,639 B / 16 blocks —
  `build` now prints blocks/bytes per target; re-derive, never copy the
  figure), so the heavier profile costs the worker less. `status` →
  `[fresh] opencode: profile=full, source=79e3517`, exit 0 (2026-08-15).
  Surfaced by `hooks/ops_health_nudge.py` check 12, a stat()-only session
  screen whose only remedy is "run `status`" — why it routes instead of
  judging, and why this layer needed a caller at all: `lessons.md` L-016.
- history: reference-compile retired, leak gate added, curation narrowed to
  CLAUDE.md, codex + antigravity sync-OFF (2026-08-11); opencode `light` →
  `full`, check 12 added, eval 8 replaced, codex + antigravity REMOVED from the
  registry (2026-08-15 — rows frozen at a 2026-07-10 verification under a
  heading calling those locations volatile; `lessons.md` L-005 hit 3)
- review-when: a second target goes live ("`full` costs less than the fallback"
  is measured against opencode's own fallback and does not transfer), or
  opencode changes the rules-precedence order that makes it the right baseline
- rollback: commits 7b3cbc1 / 2e16229 / 7aab241;
  `archive/interop-refs-2026-08-11/`; `backups/2026-08-15/`
  `ops_health_nudge.py.pre-interop-check12`; removed rows →
  `archive/2026-08-15-interop-targets-removed/` (last commit `596cfc0`)

### subagent definitions (`agents/*.md`) — what a definition may assert
- current: every definition carries an explicit `tools:` allowlist that always
  includes `Skill`; behaviour invariants come from CLAUDE.md and `ops/`, never
  from an imported persona; no skill name is hardcoded anywhere in a body
  (route off the runtime roster instead); read-only roles add
  `permissionMode: dontAsk`, implementer roles deliberately omit it; `effort:`
  is pinned per role, `color:` uses only the eight documented values. A
  definition that no routing rule references does not stay in `agents/`.
- why: capability must be enforced, not requested — an omitted `tools:` inherits
  `Edit`/`Write`, so "reports only, never edits" in prose enforces nothing.
  Hardcoded skill names rot the moment a skill is added or renamed, and the
  runtime roster is already dynamic, so naming one buys nothing and costs
  accuracy. `dontAsk` splits by role because it auto-denies anything outside
  the session allowlist, which would paralyse an implementer (`Edit` is not
  allowlisted) while being exactly right for a reviewer.
- evidence: all 22 inherited definitions instructed subagents to call
  `task_memo_read`/`task_memo_add` — tools that do not exist here — and to obey
  an "AI Team OS" framework and a Leader role that do not exist; nine carried
  identical character corruption. Separately, the first `tools:` draft
  (`Read, Glob, Grep`) would have silently disabled skill invocation entirely
  (`lessons.md` L-014). Capability facts verified against
  `code.claude.com/docs/en/sub-agents` on 2026-08-12.
- history: 22 third-party definitions inherited 2026-07-06 (commit 96c9525);
  13 archived and 8 rewritten 2026-08-12; `management-tech-lead` archived the
  same day because all three branches of its own disambiguation rule routed
  away from it
- review-when: `code.claude.com/docs/en/sub-agents` changes what a definition
  may assert (`tools:`, `permissionMode`, `effort:`, `color:` are all product
  behaviour verified on 2026-08-12, not contract); or a new agent definition is
  added, which is when the `tools:`-must-include-`Skill` invariant is at risk.
- rollback: commits fe8d69b / 79936c2 / 0548220 and this one;
  `archive/agents-2026-08-12/`
