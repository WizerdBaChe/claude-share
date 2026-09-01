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

## Execution surface

### surface routing — which surface runs which work (CLI headless vs Desktop)
- current: unattended / batch / long / subagent fan-out → CLI headless; visual
  review / parallel sidebar / Dispatch / computer use → Desktop; GUI on a
  RUNNING CLI session → Remote Control; full disclosure → the session JSONL.
  Block: `environment.md` "Execution surface". User ruling 2026-08-22.
- why: same engine, different host. The measured 1.722× Desktop premium is
  about HALF permission mode and half host (E3 cell C2B, n=4: Desktop × bypass
  vs CLI × bypass still 1.139× fresh / 1.265× cost, descriptive, not separated
  at n=4; the permission-mode half is 1.172× / 1.361×), so the routing rests on
  four things: CLI-only flags (`-p`, `--max-budget-usd`, `--output-format json`,
  `--settings`), unattended semantics, the T0 prefix (+38%), and a residual
  ≈1.14×/1.27× Desktop premium at aligned permission mode. Desktop stays the
  right surface for visual review — with Bypass (not Auto) for autonomous
  coding turns (worth roughly half the premium). No third-party GUI changes
  that (the "CLI-mirrored GUI" idea was swept and shot down the same day: red
  ocean + ToS-volatile — `references/cc-mirror-gui-concept-sweep.md`).
- evidence: `_bench-claude-arms/ANALYSIS_CHANNEL_MECHANISM_2026-08-22.md`
  §2/§6; `ANALYSIS_CHANNEL_CONFOUNDS_2026-08-22.md` §6.2 (C2B n=4, $35.31;
  §6.1 is the superseded n=1 reading); PAPER §7.2.1; E2 probes 2026-08-22
  (`disableWorkflows` −7,897 T0 on CLI, −7,900 on Desktop; $1.49).
- history: first entry 2026-08-22 (cost-based rationale); same day, after E3
  n=1, narrowed to flags + unattended semantics + T0 with a "Bypass for
  autonomous Desktop work" clause; same day again, after C2B n=4 (review-when
  fired: C2B-06 = 145,876 > 134,642), the cost rationale was PARTLY restored —
  "about half the premium is permission mode", residual ≈1.14×/1.27× descriptive.
- review-when: a further C2B replicate (n=4) separates C2B from C1 completely
  → the residual premium becomes a test result, re-weigh the cost rationale; a
  same-day Desktop × auto control on the current Desktop build lands in the C2B
  band → the permission-mode half is version drift, not mode; the
  Desktop-bundled claude.exe changes minor version; Anthropic ships a
  cross-surface session view or a Desktop `--settings` equivalent.
- rollback: `backups/2026-08-22/` (environment.md, OPS.md, rule-registry.md).

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
  corrected, sweep check 7 added so it cannot recur silently. **That last
  clause was true of the UNIT and read as though it covered the VALUE**: check
  7 is a grep for `getsize`/`len(...)` and cannot see a number at all. Found
  2026-08-27 with three constants drifted across four sites (`DICT_CAP` 28K vs
  24K vs 20K; `CLAUDE_MD_CAP` 19,968 vs 15K vs 15K; `SIZE_CAP` 22K vs 15K in
  the hook's own docstring). Two fixes, in this order: the hook's docstring now
  names constants instead of copying values (the restatement is deleted, not
  checked), and sweep check 7b
  (`tools/ops-health-test/check_cap_binding.py`) compares what remains.
- **`DESC_CAP` counts the RAW folded block, not the description string**
  (recorded 2026-08-27). `ops_health_nudge.py` measures
  `len(m.group(1))` of `^description:[^\n]*\n((?:[ \t]+[^\n]*\n|\n(?=[ \t]))*)`
  — every continuation line INCLUDING its newline and leading indentation. So
  the same description measures three different numbers depending on how it is
  read: raw block 977, YAML-parsed string 953, whitespace-collapsed 979 for the
  pre-2026-08-27 `scientific-research-guide` description. Only the first is the
  gate. Consequence for anyone trimming a description: measure it the hook's
  way or the headroom is imaginary — that trim landed at **789 of 800, an
  11-char margin**, while a collapsed-string reading reported 771 and implied
  29. Re-indenting a compliant description can push it over without a word
  changing, because indentation counts.
- review-when: `DESC_CAP`'s measuring expression in `ops_health_nudge.py`
  changes, or a skill adopts a non-folded (`|`, quoted, single-line)
  description form, for which that regex's group(1) means something different.
- review-when: a `count_tokens` run reverses the bytes/chars spread (the
  refutation condition already stated in `evidence:`); or the corpus's CJK
  share moves far outside the 0–33% band the measurement covered.
- rollback: `backups/2026-08-12/`

### `CLAUDE_MD_CAP` — global CLAUDE.md always-loaded budget
- current: **19,968 bytes (19.5 KiB)** — user ruling 2026-08-18
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
- 2026-08-18's argument for the raise to 19.5K, made on the same terms T-015
  demanded. Two new rules (shell TOOL ROUTING; the three silent Bash-tool
  limits) plus three amendments (line endings, PS `EAP='Stop'`, the Python
  raw-string cause). Sinks checked and none applies: a `paths:` glob under
  `~/.claude/rules/` loads only when a MATCHING FILE IS READ, but both new
  rules must fire at the moment a TOOL IS CHOSEN — before any file is touched
  — so the carrier is structurally wrong, not merely inconvenient; no skill
  owns tool selection. Two compression passes were taken first, moving every
  number and mechanism into `lessons.md` L-024 and shrinking the line-ending
  bullet once `.gitattributes` took over its enforcement: +2,855 B → +1,848 B.
  The residual 19,249 B against 19,968 leaves ~719 B. The hook planned for
  R-1/R-4 (see `shell tool routing`) is expected to let bullet 2 shrink to a
  pointer, which would return most of the raise; if it does, re-judge this cap
  DOWNWARD rather than absorbing the slack.
- headroom is DELIBERATELY thin (the 17K era ran at ~80 B and that was the
  point): a cap with comfortable headroom is not a cap. Amendment-only
  territory; no new rule fits without a sink, a merge, or an argued raise.
- 2026-08-31 trim-pass verdict (value UNCHANGED — recorded so the next
  addition doesn't repeat the analysis): a user-directed pass compressed
  22,338 → 19,957 B without cutting any distinct rule, but it CONSUMED THE
  WORDING RESERVE — everything with a sink is now behind a pointer (shell
  numbers → L-024, ui-verify denial enumeration → the hook docstring,
  rule-file globs → their own frontmatter), and the pass's red-team measured
  the marginal quality cost: 2 should-fix regressions from compression (a
  lost vault-index split; an altitude drift in the gate rule's Chinese half
  vs `30-judgment.md` R2) had to be restored. Pre-armed conclusion for the
  NEXT sink-empty addition: route straight to an argued raise (suggested
  +2,560 B → 22,528, following the +2–2.5K pattern) rather than another
  compression pass — the reserve is spent and further compression has
  measured negative marginal value. A raise NOW was evaluated (user prompt
  2026-08-31) and declined: the raise trigger never fired (no distinct rule
  was cut) and this entry's own doctrine says thin headroom IS the decision
  point, not a defect.
- history: 12K (birth) → 15K (2026-08-01, after the failed trim pass) → 17K
  (2026-08-16, T-015 closed; the 15K state had 276 B headroom, i.e. the next
  rule breached, which is what made it a ticket rather than a routine trim);
  17,004 → 17,327 B (2026-08-16 later, 3D-photo batch: 2 amendments +323 B —
  H-4 provider discriminator, H-2 representation rung — 0 new rules, per the
  amend-don't-append reading of the thin margin) → **19,968 B (2026-08-18,
  user ruling; 2 new rules + 3 amendments from the shell-error sweep, after
  two compression passes and a sink check that came back empty)**
- review-when: any proposed global-CLAUDE.md change (headroom ~11 B as of
  2026-08-31, reserve spent — re-run find-a-sink / merge, then argue the raise
  per the 2026-08-31 verdict above), or a rule in this file gains a valid
  `paths:` sink and can leave. Also: once the shell-guard hook ships, re-judge
  whether bullet 2 can shrink and the cap come back down.
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
- rollback: `git show 0c435ab^:hooks/ops_health_nudge.py` (pre-bodycap-300; dated backup pruned)

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
- current: **28K bytes on `skill-trigger-dict.md`, ROLE = REVIEW TRIGGER**
  (2026-08-17, after dict-review round 1). Firing means "run the routing
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
- evidence: **PROVISIONAL — every value so far is a resize, not a measurement.**
  20K→24K cleared the file's post-fix size (20,944 B) with headroom; 24K→28K
  cleared it again after round 1 landed 3 user-ruled corrections (false matches
  10→1 on the worst entry), on this rule's own stated terms that raising after
  the review it asked for IS the intended outcome. The file had sat at
  20,376/20,480 = **99.5%** unseen because sweep check 15 walked `ops/*.md` and
  `CLAUDE.md` only; check 15 now derives every cap from the hook by name. What
  would settle it: the next three firings, one line each (`<date> <bytes>: audit
  found dead entries removed | audit found entries true, raised again`). Three
  "entries true" in a row means the dict finally describes real traffic and the
  cap can go back to being a size check.
- firing log (the three-firing test above):
  - `2026-08-15 20,376 B`: audit found the dict explained 0% of real routing →
    corrections, then raised 20K→24K
  - `2026-08-17 ~24K`: round 1, 3 user-ruled corrections → raised 24K→28K
  - `2026-08-27 31,287 B`: **breach open, not yet acted on.** The re-run audit
    still reports 0% coverage on 20 of 23 live entries and 14 DEAD entries, 3 of
    which fire anyway — so the review this trigger asks for has NOT happened and
    a third raise is not earned. Recorded here rather than acted on because the
    session that found it was fixing the nudge, not the dict.
- history: 20K (birth) → **24K (2026-08-15**, user ruling, after the first
  routing audit) → **28K (2026-08-17**, after dict-review round 1). The
  2026-08-15 breach was the first time anything checked whether its contents
  corresponded to reality. **The 2026-08-17 raise was never recorded here** and
  this entry read "24K" until 2026-08-27, while `40-maintenance.md` §3 read
  "20K" and the hook enforced 28K — three live values for one constant. Fixed
  by adding sweep check 7b, which compares every restating site to the hook.
- review-when: `tools/skill-routing-audit.py` reports coverage above ~50% for
  most entries — at that point the dict is load-bearing and its size argument
  changes. Also re-open if skill routing stops being description-driven.
- rollback: `git show 7ff7d0c^:hooks/ops_health_nudge.py` (pre-dictcap-28k).
  Earlier step: `git show aa5e7d1^:hooks/ops_health_nudge.py` (pre-dictcap-24k;
  dated backup pruned)

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
- current: **22K bytes per `ops/*.md`, and its ROLE is a REVIEW TRIGGER, not a
  budget** (2026-08-15; 22K since 2026-08-21). **Scope: `lessons.md` and `rule-registry.md` are exempt**
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
  2026-08-21 20-dispatch.md 24,625 B: review found extractable concrete —
  the shared-tree git narrative (§7a) → `references/shared-tree-git.md`, the
  T1–T5 templates (§6) → `references/dispatch-templates.md`, measurement
  sentences compressed → 20.9K; what remained is rules and routing tables, so
  the cap was raised 18K → 22K with this pass as the evidence.
  2026-08-21 environment.md 20,516 B: review found extractable concrete —
  instruction-loading probes, Bash-result shape, auto-mode evidence, reviewer
  correction → `references/harness-measurements.md`; hook mechanics →
  `references/browser-pane-pixel-route.md` "Enforcement" → 16.6K.
- history: 10K (birth) -> 12K (2026-08-06, after a failed trim pass) -> 15K
  (2026-08-13, after another) -> 18K (2026-08-15, role changed to review
  trigger; the first raise justified by a measurement of what the bytes cost
  rather than by an inability to cut them) -> 22K (2026-08-21, after a review
  that found and extracted concrete from both firing files and still left
  20-dispatch.md at 20.9K of rules)
- review-when: three consecutive firings resolve as "reviewed, nothing to
  extract, raised" (see evidence); OR a measurement shows the always-loaded
  surface is no longer cached or no longer a small share of context, which
  would restore the budget reading.
- rollback: `git show 425a7e5^:hooks/ops_health_nudge.py` (pre-check14, 18K value);
  `git show fe2dc3f^:hooks/ops_health_nudge.py` (pre-sizecap-18k); dated backups pruned;
  `40-maintenance.md` S3 table row

### lessons ledger shape — one card per entry, full record in `references/lessons-detail.md`
- current: `ops/lessons.md` holds one CARD per entry (header line with the
  only `hits:` field / Context / Pitfall / Fix / Detection / Recurrences /
  Evidence / Detail pointer); `ops/references/lessons-detail.md` holds the FULL
  RECORD under the same `## L-nnn` heading, verbatim and append-only, with
  `(full record)` where `hits:` would be. Bumping a hit edits the card and
  appends to the detail section; the card never contradicts the detail.
- why: at 116,051 B / 1,637 lines / 27 entries the ledger had become a narrative
  archive — the pre-task grep it exists for had become a full read, and the
  mechanism of an entry was buried under its recurrence blocks (L-011 185
  lines, L-025 186, L-023 148). `40-maintenance.md` §3's extract rule applied to
  the one ops file it exempts from the byte cap; the exemption was about the
  cap, not about extraction. Splitting rather than compressing keeps every
  cross-reference ("L-011 hit 3", "L-025 (B4)", 333 occurrences in 89 files)
  resolvable, and keeps retractions and provenance notes in the record.
- evidence: 116,051 B → 52,821 B ledger (-54%) + 115,675 B detail; 27 cards =
  27 `hits:` = 27 detail sections (sweep checks 5 / 5b); ids, dates, tags and
  hit counts unchanged; the pre-split file is
  `git show 9ad18b4:ops/lessons.md` (dated backup pruned).
- history: born 2026-08-21 (user-mandated ops cleanup at L2).
- review-when: a card's `hits:` bumps without a matching append in the detail
  file (check 5b counts headings, not bumps — add a bump check if it happens
  twice); or readers start opening the detail file FIRST, which would mean the
  cards are not carrying the mechanism.
- rollback: restore `git show 9ad18b4:ops/lessons.md` over
  `ops/lessons.md` and delete the detail file (sweep 5b then reports 0 vs 27,
  which is the intended signal that the split was undone).

### `UAT_A_CAP` — manual-acceptance checklist: rank axis and `A` item budget
- current: a manual-acceptance checklist is two consequence-ranked sections —
  `A. 必驗` (≤ **7** items; 資料與不可逆狀態 → 運作與使用 → 失敗看得見 → 換環境
  存活) then `B. 體驗` (看得懂 → 順手 → 觀感) — both descending, continuously
  numbered, and never grouped by module, technology, or surface. Admission is
  gated twice: machine-checkable → not an item at all (paste the test output);
  then blocks shipping → A, merely annoys the user → B, neither → not written.
  Owner: `ops/references/uat.md`. Binding short form: global CLAUDE.md `[BC]`
  line. Eleven carriers, enumerated in that file's §8.
- why: user ruling 2026-09-01 —「檢驗項目太容易膨脹，開一堆的檢驗項目等於沒驗」.
  Count is not coverage, and a list long enough to be skipped is worse than no
  list, because the delivery still reads as verified. Rank is what makes
  stopping early SAFE — the reader's actual behaviour — and the cap moves the
  "what matters least" decision from the reader (who resolves it by not
  running anything) to the author.
- evidence: PROVISIONAL — 7 is a first value, not a measurement. What settles
  it: at each round where the user reports back, record how many A items were
  actually run before they stopped. A routinely-unrun tail lowers the cap; a
  genuine need for more than 7 blockers is a SCOPING finding (split the
  acceptance pass per milestone) rather than a cap problem. Observations
  append to this entry.
- history: born 2026-09-01, replacing the 2026-08 form (items ordered by
  SURFACE — UI / API / build — with stress-path parity enforced BY COUNT).
  That quota was itself an inflation driver: parity can only be satisfied
  upward. Its teeth survive as a rank tie-breaker (中斷／重入／極端輸入
  outranks the happy path on the same surface) plus a required one-line "this
  change has no such path" claim, so silence is no longer a passing answer.
  Regression case for the loosening: `ops/references/uat.md` §6.
- review-when: (a) a delivery needs an A section over 7 and does NOT split the
  pass — twice means the cap is wrong rather than the deliveries; (b) the user
  reports running the list to the end every time, which would mean rank is
  doing no work and only the cap is active.
- rollback: revert the carriers listed in `ops/references/uat.md` §8 and delete
  that file; the pre-ruling wording is the parent of the commit that adds it.

### `TRAIL_SIZE_CAP` — audit trail rotation trigger
- current: 60 * 1024 chars, but **the rotation model is being retired** —
  see `audit-archive/` frozen header and this file's own premise.
- why: the trail grew as O(changes) while its value is O(rules), so rotation
  was permanent maintenance. This registry replaces the forward-going role.
- evidence: 2026-08-11 — rotating 17 entries took the file 76,207 → 49,108 B,
  and three entries written the same day put it back to 61,285 B. At that rate
  rotation recurs every few working days.
- history: 60K (birth) → retired for new rationale (2026-08-11)
- rollback: `git show 3fe7099^:Global_skill_update.md` (pre-rotation; dated backup pruned)

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

### compact recovery (`hooks/compact_bookmark.py` + `compact_pointer.py` + `transcript_read_guard.py`)
- current: PreCompact("") writes `cache/compact-recovery/<sid>.json` (transcript
  path, newline count, trigger, ts — no jsonl parsing per the standing
  format-unstable ruling) then runs memory-pipeline `preserve.py` (<=45s) so the
  LIVE session's digest exists at recall time; SessionStart("compact") injects a
  ~220-token pointer card (digest-first ladder + the two recall triggers, plus
  the [intake re-arm] block since 2026-08-31: intake gates are NOT satisfied by
  the compact summary — a prior-art verdict survives compaction only as a
  NAMED consulted-list; deliverable-series inputs = deliverables 1..N-1 +
  review records; a single-source ruling covers only its named axis — L-039);
  PreToolUse(Read) denies reads of SESSION-RECORD-shaped files (`*.jsonl`, or
  `*.md` under a `digests/` dir) under `projects/` + `memory-archive/` +
  any configured mirror root when size > 128KB AND (no `limit` or
  limit > 120 lines). Grep untouched. Non-record tenants of those roots
  (WebFetch caches / tool-result overflow under `**/tool-results/`,
  model-cache, indexes) Read freely — identity is by asset shape since
  2026-08-29; regression matrix at `hooks/tests/test_transcript_read_guard.py`.
  (2026-08-16; identity narrowed 2026-08-29)
- why: post-compact recall must stay ON-DEMAND — compaction saves resident
  tokens, recall spends one-off tokens, and the only move that re-inflates
  context is a wholesale re-read, removed structurally at its pressure moment
  (same argument as ui_verify_guard: enforced, not recalled). User rulings
  2026-08-16: D1 build, D2 hard guard, D3 digest refresh at compact.
- evidence: PROVISIONAL — the 128KB gate and 120-line window are guesses; a
  denial that blocked a LEGITIMATE whole-file need is the settling observation,
  append such cases HERE. Appended 2026-08-29: a different false-positive
  class — the original path-only identity ("under corpus root AND >128KB")
  denied WebFetch-cached PDFs under `projects/**/tool-results/` (2 subagent
  events; 36 non-record files >128KB under projects/ at audit, plus
  memory-archive model-cache/index files). The subagents classified the deny
  text (identity assertion + "Policy:" + read-elsewhere imperative) as prompt
  injection — correct calibration on their side. Fixed by shape-based
  identity + constraint-form deny message; thresholds unchanged, the gate was
  NOT loosened for real records. Boundary probe same day: shape-on-raw-path
  was itself bypassable via 8.3 short names (extension truncates to `.JSO`) —
  fixed by canonicalizing before all checks (also covers `\\?\` prefix and
  junctions). Allow/deny DECISION TABLE + BOUNDARIES AND UNKNOWNS ledger
  (3 tested accepted bypasses: UNC admin share, NTFS hardlink, renamed copy)
  live in the hook docstring; all of it pinned by the regression matrix
  (22/22 green 2026-08-29, incl. bypass pins + real-file positive controls). Measured: digest = 1.1% of raw (50,849B/4,448,760B,
  one real session); 19/19 real-data acceptance runs 2026-08-16 including
  live-session digest refresh proof (mtime_age 0s). Guard REAL-fired the same
  day: live PreToolUse deny on a 4.2MB corpus read in the authoring session —
  hooks apply mid-session, no restart. FULL-CHAIN REAL FIRE 2026-08-16 21:59
  (manual /compact, authoring a local session): bookmark written (manual,
  160 lines/0.87MB) -> card injected post-compact naming the exact region
  (lines 1-160, values matching the bookmark) -> digest fresh at card time ->
  recall ladder walked for real (digest hit for one fact; a truncation-cut
  fact escalated per policy to a transcript-region Grep, line 158) -> guard
  deny re-confirmed POST-compact (guard survives compaction). One observation:
  digest mtime 22:02 postdates the 45s-capped chained preserve run, so a
  second preserve invocation also fired during the compact turnover; the D3
  guarantee held either way (chained-run sufficiency was separately proven
  pre-compact, mtime_age 0s). Still unobserved: the auto-compact trigger case
  (card should read trigger=auto).
- history: born 2026-08-16. Compact on-disk geometry evidence (boundary
  appended in-place, session id retained) recorded the same day in
  a local memory note, correcting its first draft. 2026-08-31:
  card gained the [intake re-arm] block (~90 tokens; summary-handoff gate
  disarm, SSLD Phase 5 incident — `ops/lessons.md` L-039; proposal
  `drafts/2026-08-31-compact-rearm/APPLY.md`; positive control: synthetic
  SessionStart payload prints both blocks, degraded mode included).
- review-when: a CC update changes compact geometry (recheck: compact_boundary
  line numbers in `projects/*/*.jsonl` — mid-file = unchanged) or
  PreCompact/SessionStart stdin fields; the mirror root moves with
  the scheduled copy job that feeds it; a recurring Bash `cat`/`Get-Content`
  bypass on corpus files is the event that extends guard coverage to the shell
  path; a new corpus-root tenant that IS .jsonl-shaped but not a session
  record (shape identity over-matches), or records written in a non-.jsonl
  format (it under-matches).
- rollback: unregister the three hooks from `settings.json` (single merge
  commit on `feat/compact-recovery`).

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
  **Re-verified 2026-08-18 under Claude Code 2.1.233** (the review trigger below
  had fired 13 builds earlier and nobody noticed — the exact silent-rot failure
  this file exists to prevent). Re-run over `telemetry/rule-loads.jsonl`, now
  1,590 events / 1,094 sessions: CLAUDE.md still loads at `session_start` in
  **100.0%** of sessions (1,486 `session_start` + 53 `compact` + 2
  `nested_traversal`); `rules/*.md` still fire ONLY via `path_glob_match` (49
  events). The conclusion is unchanged; the RATES are not, because the
  denominator grew 4.5x while absolute fires did not: `frontend-layering` 7 →
  8 sessions (3.3% → 0.7%), `shader-failure-modes` 1 → 1 session (0.4% → 0.1%).
  `ops/*` remains 0, still uninstrumented rather than unloaded.
  **`shader-failure-modes.md` has now fired exactly once in 1,094 sessions**;
  with the 2026-08-16 glob-blindness counterexample above, that rule is a
  candidate for retirement or re-globbing, not a healthy low-fire rule.
  **Re-globbed 2026-08-19 (user ruling: try the glob before retiring).**
  Measured over 1,361 first-party source files under the work root, of which
  exactly 2 contain GLSL: the original globs matched 8 files and hit 0 (recall
  0%); adding the filename signals that sound right (`*shader*`, `*glsl*`,
  `*webgl*`) still hit 0; only naming the two techniques (`parallax*`, `ldi*`)
  reached 100% recall, at 10 matches of which 8 are `.fs` Tcl font files in a
  vendored toolchain nobody reads — so precision on files actually OPENED is
  2/2. The load-bearing detail, recorded in the rule file itself: those two
  patterns carry the entire recall, i.e. the fix works by hard-coding the known
  answer. A glob cannot see inside a template string, so this buys the existing
  project and nothing else.
- history: established 2026-08-11; firing rates measured 2026-08-14;
  glob-blindness counterexample recorded 2026-08-16; re-verified under 2.1.233
  and rates restated on the larger denominator 2026-08-18
- review-when: any Claude Code upgrade (the probe was against 2.1.220, the
  re-verification against 2.1.233, and the loading mechanics are undocumented
  product behaviour); re-run the `rule-loads.jsonl` breakdown, which now has
  two baselines to compare against.
  Re-run with `python tools/context-budget/rule_loads.py` — it carries both
  recorded runs inline, so the comparison needs no archaeology.
  **Also: re-check `shader-failure-modes` fire rate after ~2026-10.** The
  re-glob is a hypothesis with a falsifier — if it is still ~1 session per
  thousand, naming files did not help and the rule should be retired rather
  than patched a third time; if GLSL work happens in a file that did NOT load
  it, that is the same silent miss recurring and the conclusion is that path
  globs are the wrong carrier for content-embedded code, not that the list
  needs another entry. Reachability half:
  `python tools/glob-fitness.py --rule ~/.claude/rules/shader-failure-modes.md
  --root <WORK_ROOT> --content "gl_FragColor|gl_Position|uniform sampler2D"`
  (2026-08-19: recall 94.1%, precision on files actually opened 100%; the one
  unreached file is a third-party ComfyUI Python extension).
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
- rollback: `git show f2e8bc2^:hooks/ops_health_nudge.py` (pre-check13; dated backup pruned)

### stale uncommitted work — ops-health check 14
- current: at session start with cwd == `~/.claude` ONLY, `git status
  --porcelain -uall`; any dirty path whose mtime exceeds **3 days**
  (`STALE_WORK_DAYS`) is reported — count, oldest age, the 3 oldest names, plus
  the count of FRESHER dirty paths as the "this tree has company" hint.
  Report-only; never attributes a path to a session; git failure/timeout (2 s
  budget) prints nothing.
- why: 2026-08-21, 17 complete record artifacts from 5 projects sat uncommitted
  in this tree for 14–109 h. Every writer had followed the record-keeping
  discipline; nobody committed, because this repo has no remote — no push, PR
  or CI — so `git status` is the only backpressure and nothing read it; and
  the 2026-08-11/16 tracking rulings (`references/`, `outputs/`) changed what
  "done" means without changing any procedure that produces "done". SessionStart
  is the only moment a reader can act (at SessionEnd nobody is left); an
  integrity-sweep item was rejected because the sweep is loaded on demand — it
  runs when someone already suspects, which is exactly the state nobody was in
  for five days. Attribution was dropped, not deferred: a dirty working-tree
  path touches no object, so it is undecidable from outside (the proposing
  ticket misattributed three times by cwd), and `list_sessions` is an MCP tool a
  SessionStart hook cannot reach; the fresher-path count carries the intent of
  the proposal's condition (B) with no API and no guess. Proposal as received:
  `drafts/2026-08-21-stale-work-nudge/APPLY.md`.
- evidence: **PROVISIONAL — 3 days is the most conservative zero-false-positive
  point on ONE day's data**: 72 h catches 7 of the 17 paths, 48 h catches 9,
  both with zero false positives against the same-hour in-flight peer work
  (hours old). Two-sided suite 2026-08-21: back-dated untracked path and
  back-dated tracked modification fire; fresh path, clean repo, no repo, project
  cwd stay quiet (`tools/ops-health-test/`, 28/28). Live tree at birth: clean
  (correct negative). **Baseline stamp 2026-08-22** — the generative fix landed
  (T-021: `workflow-checkpoint` §A 6b commit-or-hand-off, commit `6fa2641`; its
  first live run `0e29451`): 0 firings recorded since birth, and that session's
  tree was clean at start. Count firings AFTER this date against it; the
  comparison is the nudge's rate before vs after 6b, not an absolute number.
  What settles it: append one line per real firing here —
  `<date> <n stale> <oldest> <acted-on: y/n>`. A firing rate near zero for
  months means RETIRE, not tune (shell_transport_guard's 2.7% notice-rate watch
  is the precedent); the same paths reported for a week means the notice is
  being read past, and the remedy is to commit them, never to raise the
  threshold.
- history: proposed 2026-08-21 by the stale-path attribution ticket
  (task_406a32d8) as a hand-off to a rules-layer session; built the same day
  in-session, with the user's L2 mandate for the ops cleanup as the named
  authorization (`70-evolution.md` §1.1).
- review-when: this repo gains a remote (the backpressure source changes; the
  threshold and the check's reason to exist are both re-judged); or the
  session-board / `list_sessions` layer gains a way to attribute a dirty path
  (then the company hint can become attribution); or `settings.json` lowers the
  SessionStart timeout below 3 s (the git call must shrink with it).
- rollback: `git show 425a7e5^:hooks/ops_health_nudge.py` (pre-check14; dated backup
  pruned. The companion test file was untracked and its backup pruned — no
  recoverable pre-state)

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

### browser-pane pixel route — out-of-process by default
- current: pixels for UI verification come from headless Playwright
  out-of-process BY DEFAULT (durable runner: `tools/ui-shot/`, doctor-checked);
  the pane serves DOM/state reads; the screenshot guard ROUTES on a `hidden`
  probe result (deny + handed command) and permits on `visible`, so
  visible+timeout stays a distinct diagnosable fault; pictures reach the user
  via `SendUserFile`/links, never a fronted window; pixels are for APPEARANCE
  claims only. (2026-08-16)
- why: user premise — the foreground is not commandeerable, so `hidden` is the
  steady state and probe-then-retry was a ritual with a foregone answer.
  Brief + dispositions: `outputs/browser-pane-visibility-brief-2026-08-16.md`,
  `outputs/browser-pane-visibility-outcome-2026-08-16.md`.
- evidence: headless 1.4–1.5s WITH pixels vs pane 5s timeout with none; fresh
  pane born hidden/0×0/rAF-stalled; archive-wide 80 pane-screenshot calls vs
  853 DOM/state reads; hook suite 19/19 (`tools/ui-verify-test/`); live
  router check in-session (marker annotated `hidden`, route denial fired).
- history: detect-first CLAUDE.md line (2026-08-05) → PreToolUse gate
  (2026-08-08) → result-aware router + default inversion + durable runner
  (2026-08-16)
- review-when: `<browser_surfaces>` or the screenshot tool's error wording
  changes on an upgrade; the suite or `tools/ui-shot/doctor.mjs` fails; a
  probe marker stays `unknown` in live use (`tool_response` unpopulated). A
  user "I'm watching" is a temporary premise flip, not an edit trigger.
- rollback: `git show 4ba4528^:hooks/ui_verify_guard.py` (pre-router; dated backup pruned);
  `drafts/2026-08-16-pane-pixel-route/`

### Playwright MCP — one user-scope server (2026-08-23, narrowed 2026-08-25)
- current: `playwright-headless` (`--browser chrome --headless --isolated`:
  the installed Chrome 151, new-headless, no window, nothing persists), run via
  `node tools/playwright-mcp/node_modules/@playwright/mcp/cli.js` — a durable
  exact-pinned install (0.0.79), never npx. Registered in `~/.claude.json`
  `mcpServers` (user scope = every project). Neither hook (`ui_verify_guard`,
  `browser_pane_scope_guard`) is wired to it — user upheld 2026-08-23; the pane
  hooks' denial/route texts name it (and `claude-in-chrome` for logged-in
  tasks) instead, so the surface is discovered at the moment the pane is
  refused. `playwright-chrome` (`--extension`, real logged-in Chrome tabs) ran
  alongside it 2026-08-23–2026-08-25 and was removed — see "removal:" below.
- why: the pane and claude-in-chrome leave two gaps — (a) a logged-in real
  browser that an agent can drive with a full tool set (verify/snapshot/
  network/trace) for mfp's IG adapter and signed-in backends; (b) multi-step
  UI verification (click → settle → shoot) without a window and without the
  pane's `hidden` steady state. `--browser chrome` sidesteps a browser download
  (bundled playwright-core 1.63-alpha wants chromium r1237, not installed).
- evidence: per-turn context measured with `claude -p` (haiku, 2 runs each):
  CLI baseline 37,889 → one server 38,131 (+242) → both 38,511 tokens
  (**+622, +1.64%**; tool search on, names only — full schema ≈ 4.9K/server if
  ever loaded upfront). User ruling: remove above ~10%. End-to-end: navigate →
  snapshot → screenshot → close through `claude -p`, 6 turns, 13.5 s. User
  acceptance 2026-08-23: 1 tab picker ✓, 2 logged-in snapshot ✓, 3 occluded-tab
  `browser_take_screenshot` **TIMEOUT 5000 ms** (L-009 class — the user's own
  Chrome lacks Playwright's `--disable-backgrounding-occluded-windows`, which
  `playwright-headless` has; grep'd), 4 headless localhost shot with no window
  ✓, 5 `claude mcp list` Connected ✓. Rule from item 3: on `playwright-chrome`
  read with `browser_snapshot`/`browser_evaluate`; pixels only while the user
  says they are watching that tab. Records: `ops/environment.md` "Browser
  pane" (Playwright MCP paragraph), `tools/playwright-mcp/README.md`,
  `ops/references/browser-pane-pixel-route.md`. Proof-of-life: sweep check 25.
- history: evaluated 2026-08-23 (Playwright already the default pixel route
  since 08-16 via `tools/ui-shot`) → installed same day at user scope → token
  set, acceptance 4/5 → hooks' route texts updated to name the servers →
  2026-08-25 `playwright-chrome` real-use failure (`browser_tabs list`
  returned empty, no error) → removal (see below).
- removal (`playwright-chrome`, 2026-08-25): read
  `playwright-core/lib/coreBundle.js`'s `_openConnectPageInBrowser` — the
  earlier "token rotates" hypothesis was wrong and retracted.
  `PLAYWRIGHT_MCP_EXTENSION_TOKEN` is a user-chosen pre-shared secret sent as
  `?token=` on the extension's `connect.html`; if absent/mismatched the server
  does not error, it opens the connect page and `await`s
  `_extensionConnectionPromise`, which only resolves on a manual "allow" click
  inside the extension's own UI — no MCP tool can drive that click. Even with
  a correct token, the env var is read once at stdio server spawn and cached
  for the process lifetime, so a corrected value needs a session restart that
  no in-session tool can trigger. Both gaps are structural, not
  misconfiguration — unfit for the automated-agent use case it was installed
  for. User decision 2026-08-25: `claude mcp remove playwright-chrome -s user`
  (executed, verified via `claude mcp list`); keep `playwright-headless`
  (unaffected — no token, no extension, no manual-approval gate); route
  logged-in-browser tasks through `mcp__claude-in-chrome__*`. Docs updated in
  the same change: `tools/playwright-mcp/README.md`, `ops/environment.md`
  "Browser pane", `ops/references/browser-pane-pixel-route.md`,
  `ops/references/integrity-sweep.md` check 25,
  `hooks/browser_pane_scope_guard.py` route text.
- review-when: `@playwright/mcp` bump (re-check bundled browser revision and
  the `chrome` channel assumption); Claude Code changes the tool-search
  default (re-measure per-turn cost).
- rollback: `claude mcp remove playwright-headless -s user`;
  `tools/playwright-mcp/` can stay (inert) or be archived.

### shell tool routing — pick the tool before writing the command
- current: file CONTENT goes through Write (create/replace) or Edit
  (modify/append), search through Grep/Glob; the shell keeps git, running
  programs and POSIX pipelines. Global CLAUDE.md Environment bullet 1.
  (2026-08-18)
- why: the Bash tool's three defects (backslash `ceil(n/2)` collapse, ~7.7 KB
  truncation, Windows-path forms) exist only inside the shell, and the first
  two fail SILENTLY — the command reports success with corrupt output. A rule
  saying "avoid `\\`" needs recall at the moment of writing; a routing rule is
  decidable from the task shape before a character is typed. Auto mode is not
  in conflict: it routes to Bash "wherever it can accomplish the job".
- evidence: 6,544 deduplicated calls / 10 days. Write 0.1% failure (1/1,226)
  vs Bash-writing-a-file 5.2% (15/291) and inline `python - <<'PY'` 6.1%
  (36/586); Grep 0.9% vs PowerShell-searching 17.4% (38/218). Write and
  PowerShell probed against all three limits and have none.
  Report `outputs/shell-command-error-audit-2026-08-18.md`; `lessons.md` L-024.
- history: no routing rule existed before this entry (grep of CLAUDE.md,
  AGENTS.md, ops/*, skill-trigger-dict.md returned nothing) → born 2026-08-18
- review-when: Claude Code updates — run `tools/shell-audit/PROBES.md` P1/P2/P4
  (hand-run; they test the TOOL boundary and cannot be scripted) then
  `python tools/shell-audit/sweep.py --since <10d ago>`. If either Bash defect
  disappears, the routing argument weakens to a preference and this entry should
  be re-judged. Once the live transcripts age out (cleanupPeriodDays, ~30d), add
  `--root <MIRROR_ROOT>`.
- rollback: remove CLAUDE.md Environment bullets 1–2; `lessons.md` L-024 keeps
  the measurement so the decision can be re-made without a re-sweep.

### `shell_transport_guard` — asymmetric by design: deny size, annotate backslashes
- current: PreToolUse on the Bash tool. **DENY** at >= 7,700 B (`SIZE_LIMIT`).
  **NOTICE, never deny**, on any run of >= 2 backslashes — stating how many
  will actually be delivered, and more emphatically when the command reaches a
  content sink. **NOTICE (rule 3, 2026-08-23, L-029)** when a known
  Windows-native exe sits at command position followed by a `/letter` token
  (`cmd /c`, `taskkill /PID`, `reg … /v`, `findstr /i`, `sc`, `net`,
  `schtasks`, `wmic`…): MSYS rewrites it (`/c` → `C:/`, `/PID` →
  `C:/Program Files/Git/PID`) before the exe runs; skipped when the command
  carries `MSYS_NO_PATHCONV`; `//c` never matches. PowerShell/Write fall
  straight through. Escape hatch `[transport-checked]`. Fail-open.
  (2026-08-18; rule 3 added 2026-08-23)
- why: the two defects differ in what the gate can DETERMINE, and the global
  gate-authority rule makes that the deciding question, not severity.
  Size is fully determinable. The backslash collapse is not: the FIRST version
  of this hook denied a halving that reached a sink, and backtesting it against
  5,122 real Bash calls flagged 112 of which **89 had SUCCEEDED**. Sampling
  those showed a large share were the author already COMPENSATING for the
  collapse (four backslashes to land two; `\\|` in a markdown table to land
  `\|`; `[\\/]` in a JS regex). Compensation and naive escaping are
  byte-identical in the command string — no pattern separates them — so a veto
  would have been right 23 times and wrong 89, and a control wrong three times
  in four gets routed around rather than obeyed.
- evidence: backtest over 5,122 deduplicated Bash calls (10-day window).
  Final rates: **DENY 7 calls = 0.14%, and all 7 had already failed — zero
  false positives by construction**; NOTICE 138 = 2.7% (13.8/day, no blocking);
  untouched 97.2%. Suite `tools/shell-transport-test/` 31/31 (2026-08-23; was
  23/23), two-sided (2 deny cases against 29 allow/notice — rule 3 adds M1–M8:
  `cmd /c`, `taskkill /PID`, `&& taskkill /F`, `reg … /v` → notice; a POSIX
  path to a POSIX tool, `cmd //c`, `MSYS_NO_PATHCONV=1 …`, `dotnet … /p:` →
  allow), including a boundary pair at 7,699/7,700 B,
  the compensation shape asserted NOT vetoed, fail-open on malformed stdin, and
  E1 proving the rejected command is persisted in full BEFORE the veto
  (`telemetry/shell-transport-guard.jsonl`) — a denied heredoc body exists
  nowhere else. Probes and mechanism:
  `outputs/shell-command-error-audit-2026-08-18.md`; `lessons.md` L-024.
- history: born 2026-08-18. Design corrected in the same session, BY the
  backtest, from "deny both" to "deny size / annotate backslashes" — the
  correction is the entry's main content and should not be re-derived.
  2026-08-23: rule 3 (MSYS `/flag` rewrite, L-029) added as ANNOTATE after a
  `cmd /c` probe hung 300 s and `taskkill /PID` errored in one session; deny
  deferred until a corpus backtest like the original one.
- review-when: any Claude Code upgrade — `tools/shell-audit/PROBES.md` P1 and
  P3; if the collapse disappears the notice branch becomes noise, and if the
  ceiling moves `SIZE_LIMIT` is stale in the UNSAFE direction. Drift check:
  `python tools/shell-audit/invariants.py` prints the guard's deny/notice counts
  against the backtested 0.14% / 2.7%; a notice rate far above 2.7% of the Bash
  total (from `sweep.py`) means the sink patterns drifted. Discount the first
  ~90 telemetry rows — the test suite writes real entries.
- rollback: unregister from `settings.json` (the `Bash|PowerShell` PreToolUse
  block); the file is inert without it. CLAUDE.md Environment bullets 1-2 keep
  working as text.

### `ps_errorpref_guard` — annotate `$ErrorActionPreference='Stop'` over a native exe
- current: PreToolUse on `Write|PowerShell`. **NOTICE, never deny**, when
  PowerShell text sets the preference to 'Stop' and a native-executable
  invocation is then governed by it. The annotation names which of the two
  directions is live: (A) the call's stderr is redirected, so a warning aborts
  the script at exit 0; (B) no `$LASTEXITCODE` is read, so a non-zero exit
  passes unnoticed. Escape hatch `[eap-checked]`. Fail-open. (2026-08-21)
- why: this is the third trap in `lessons.md` L-024 and the only one that was
  carried by prose alone. Within ONE ledger entry, one project, one week, one
  author: the two hooked traps were reached for twice and intercepted twice,
  zero loss; this one was hit once, was NOT prevented, and voided experiment run
  C3-02 (L-011 hit 3). Annotate rather than deny because 'Stop' is CORRECT for a
  pure-cmdlet script and whether the author means the exe to be governed is not
  decidable from the text — the same gate-authority asymmetry as the transport
  guard's backslash branch. Separate file from `shell_transport_guard` because
  that one guards the Bash tool's TRANSPORT and its "Bash tool only" scope claim
  is load-bearing; this guards PowerShell LANGUAGE semantics and has to sit on
  Write.
- evidence: backtest over 722 transcript files / 56 days (live + the daily
  mirror), 25,606 deduplicated calls on the four candidate surfaces.
  **As registered: 21 fires / 3,488 inspected payloads = 0.60%, 0.375/day, and
  reading all 22 corpus hits found ZERO false positives** — every one is a real
  native invocation under a live 'Stop'. The positive control is organic: the
  guard fires on the Write that created `run_arm.ps1` as first drafted, on the
  line `... | & claude @claudeArgs 2>&1 | Out-String`, which is the line that
  voided C3-02. Recall was measured too, because a fire rate alone is one-sided:
  of 50 in-scope payloads containing the string `EAP='Stop'`, 23 fired and 27
  stayed quiet — 22 because no native call exists (pure-cmdlet probe scripts,
  and `Start-Process -FilePath $exe`, which is a CMDLET and cannot raise
  NativeCommandError) and 5 because the only occurrence was inside a comment
  EXPLAINING the trap. Every silence has a reason; none is a false negative.
  Suite `tools/ps-errorpref-test/` 45/45, two-sided (17 must-fire / 26
  must-stay-quiet), and it caught three real detector defects before ship.
  Instrument: `tools/ps-errorpref-backtest/backtest.py` (imports the hook, never
  reimplements it — the first version diverged within the day). The rates above
  are the corpus as it stood BEFORE this hook existed; a re-run shows one extra
  Write fire, the hook's own live proof-of-life (`liveprobe.ps1`, 2026-08-21),
  which is a real annotated Write and is deliberately not filtered out.
- MATCHER CHOSEN BY MEASURED YIELD, not by guesswork. 105 ms/invocation, all of
  it Python start-up. Write 62.6 calls/day → 20 fires; PowerShell 60.8 → 1;
  Edit 134.8 → **0**; Bash 199.1 → 1. Edit and Bash are 73% of the cost for one
  fire in 56 days, so they are detected-but-unregistered: the code paths exist
  and are tested, `settings.json` does not wire them. Registered tax: 123
  invocations/day = 13.0 s/day. Edit cannot fire on a fragment without reading
  the target file inside the hook — considered and declined, named here so it is
  not re-derived as a fresh idea.
- history: proposed in L-011 hit 3 (2026-08-21) as "decidable enough to
  ANNOTATE, not yet built"; built the same day. The ticket asked for the
  PowerShell tool alone; the backtest found only 2 EAP='Stop' commands in 3,405
  PowerShell calls, both of them the 2026-08-18 audit's own probes, and moved
  the scope to Write. That correction is the entry's main content.
- review-when: (a) any Claude Code upgrade, or a move off Windows PowerShell
  5.1 — PowerShell 7.3+ ships `PSNativeCommandUseErrorActionPreference`, which
  makes direction (B) *stop being true*; if the shell changes, re-verify with
  `tools/shell-audit/PROBES.md` before trusting this annotation, because half of
  it would then be wrong in the confident direction. (b) `integrity-sweep.md`
  check 21 each sweep. (c) if the backtest's Edit or Bash rows accumulate fires
  while unregistered, the matcher decision reopens — that is the evidence it was
  deferred for, and it is measured whether or not anyone remembers to ask.
- rollback: unregister the `Write|PowerShell` PreToolUse block in
  `settings.json`; the file is inert without it. Global CLAUDE.md Environment,
  the "calling a native executable from PowerShell" bullet, keeps carrying the
  rule as text exactly as it did before — and that is what the measurement says
  is worth 0/1.

### `ps_pipeline_close_guard` — annotate an early-closing consumer downstream of a live process
- current: PreToolUse on `PowerShell`. **NOTICE, never deny**, when a pipeline
  puts an interpreter/builder/exe upstream of `Select-Object -First N` (or its
  `select` alias, or `| more`), because closing the pipeline TERMINATES the
  upstream process. Two tiers: `work` (interpreter, builder, or anything that
  can mutate) annotates; `report` (`git`, `gh`, `rg`, `findstr`, `tree`,
  `tasklist`…, things that only print) is detected, counted, and SILENT. Escape
  hatch `[pipeline-checked]`. Fail-open. (2026-08-21)
- why: `ops/lessons.md` L-027, hits: 2 — the same call shape cost two full
  diagnosis rounds days apart, and hit 1 left no artifact behind so hit 2 paid
  the price again. Both halves of the damage point AWAY from the cause: output
  truncates (the program looks like it stopped early on its own) and the call
  returns exit 255 (the program looks broken), so the consumer the author just
  added to shorten the screen is the last suspect. The entry sat in
  `ops/lessons.md`, the layer L-011 describes as firing "only when something
  greps it, i.e. essentially never" — and by L-011's own routing table this
  trigger is a named tool call with inspectable input, i.e. a PreToolUse hook.
  Raised as ruling #8 of `_bench-claude-arms/
  REVIEW_RETRO_ADVERSARIAL_2026-08-21.md`: the carrier layer had been chosen by
  where the retrospective happened to be writing, not by the rule, and the
  cheaper, less decidable trap next door had already been given a hook. Annotate
  rather than deny because whether the upstream still had work to do is not
  decidable from the text — the same gate-authority asymmetry as its two
  neighbours.
- evidence: backtest over 726 transcript files / 56 days (live + the daily
  mirror), 26,046 deduplicated calls on the four candidate surfaces.
  **As registered: 100 fires / 3,412 inspected payloads = 2.93%, 1.79/day.**
  Reading the first 28 distinct work-tier statements found ZERO false positives,
  and several are the L-027 damage at full size: `dotnet publish -c Release …
  | Select-Object -First 40`, `npx playwright test … | Select-Object -First 60`,
  `.venv\Scripts\python.exe -m pytest … | Select-Object -First 16` — a publish
  and two test runs, killed to shorten a screen. Suite
  `tools/ps-pipeline-close-test/` 49/49, two-sided (19 must-fire / 30
  must-stay-quiet), and the negatives include the FIX L-027 prescribes
  (`$out = & python x.py; $out | Select-Object -First 30`) — a guard that fired
  on its own fix would be worse than none. The suite was itself positive-
  controlled before its 49/49 was believed: `FIRE_TIERS = ()` takes the fire
  half to 0/19, and widening the tiers takes the silent half to 16/30, so
  neither half is passing by construction. Instrument:
  `tools/ps-pipeline-close-backtest/backtest.py` (imports the hook, never
  reimplements it — the sibling backtest diverged from its hook within a day).
  LIVING PROOF, not just a passing suite: the first organic fire is telemetry
  row 1, `python --version | Select-Object -First 1` run as a real PowerShell
  tool call in a local session on 2026-08-21, annotation rendered in-session.
  Recorded because the same batch widened `30-judgment.md` R2.2 to demand
  exactly this — shipping its enforcement on a green suite alone would have been
  the next entry in that ledger. Expect that one extra fire on every re-run of
  the backtest; it is named rather than filtered, because a filter is a place
  for a real hit to hide.
- MATCHER CHOSEN BY MEASURED YIELD, and it came out OPPOSITE to the sibling's.
  PowerShell 3,411 payloads → 160 hazards; Write 85 → **0**; Edit 142 → **0**;
  Bash 226 → **0**, over 56 days. This trap is an INTERACTIVE idiom — typed at a
  prompt to shorten output, never written into a script — where
  `$ErrorActionPreference='Stop'` was the reverse (47 of 53 payloads arrived
  through Write). Registering Write/Edit/Bash would cost 42.4 s/day of
  PreToolUse tax for zero recorded fires, so those branches are
  detected-but-unregistered: the code paths exist and are tested,
  `settings.json` does not wire them. Registered tax: 61 invocations/day =
  6.4 s/day at 105 ms.
- TIER DECISION, also from rows: of the 160 hazards, 60 were `report`-tier and
  ALL 60 were `git diff|show|log` or `gh` — an author asking for the first N
  lines of something that only prints. Annotating those is 1.07 notices/day over
  correct code, which is how an annotate-only guard teaches its reader to skim
  it (`40-maintenance.md` §4.3, ritualization). They stay measured and silent.
  The suppressed rows are REPRINTED by every backtest run for exactly that
  reason — a class that is suppressed and no longer counted is a class nobody
  can reopen.
- history: L-027 written 2026-08-21 into `ops/lessons.md` during the
  bench-claude-arms retrospective; the adversarial review of that retrospective
  (§4.7 row 5, ruling #8) pointed out that the ledger's own layering rule had
  not been applied to it, and that the trap next door — less decidable, one
  round cheaper — had got the hook. Built the same day. Nothing about the
  original diagnosis changed; only the layer did.
- review-when: (a) a move off Windows PowerShell 5.1 — the early-close semantics
  hold in 7.x too, but the alias table (`curl`, `wget`, `ls`, `sort` resolve to
  CMDLETS in 5.1 and to real exes on other platforms/newer shells) does not, and
  a wrong entry there turns a silence into a miss. Re-verify with
  `tools/shell-audit/PROBES.md`. (b) `integrity-sweep.md` check 23 each sweep.
  (c) if the backtest's Write/Edit/Bash rows accumulate fires while
  unregistered, the matcher decision reopens. (d) if a SUPPRESSED upstream
  appears that can MUTATE something (a cloud CLI, `reg`, `schtasks`, a signing
  or publish tool), the name is mis-tiered and moves to `TIER_WORK` — the
  membership rule is stated in the hook beside the tables.
- rollback: unregister the `PowerShell` PreToolUse block in `settings.json`; the
  file is inert without it. `ops/lessons.md` L-027 keeps carrying the rule as
  text exactly as it did before — and what the measurement says that is worth is
  2 hits and 2 diagnosis rounds.

### line endings — pinned by `.gitattributes`, not by `core.autocrlf`
- current: `~/.claude/.gitattributes` declares `* text=auto eol=crlf`, with
  `eol=lf` for `*.sh` and `provider-episodic/cli/*` (shebang scripts) and a
  `binary` list as a forward safety net. (2026-08-18)
- why: no write path available to an agent emits CRLF — only Edit preserves an
  existing ending. CRLF in the working tree was coming solely from
  `core.autocrlf=true` in `C:/Program Files/Git/etc/gitconfig`: per-MACHINE,
  invisible to the repo, and a heuristic. Moving it into a committed file makes
  the ending a property of the asset, which is the standing rule for controls.
- evidence: 6 write paths probed (Edit preserves; Write/heredoc/WriteAllText
  emit LF; Out-File/Set-Content/`>` emit LF body + CRLF tail, and Out-File/`>`
  add a UTF-8 BOM). Damage found: 2 mixed-ending files under
  `skills/scientific-research-guide/domains/` built by `cat >>`, and 11 git
  `LF will be replaced by CRLF` warnings in one 10-day window. After the fix:
  0 mixed files; 54 files aligned to the declaration with content fingerprints
  verified unchanged; only 8 files carry a real content diff.
  Report §5.2; `lessons.md` L-024.
- history: implicit `core.autocrlf=true` (machine default) → declared
  `.gitattributes` (2026-08-18)
- review-when: a remote is added to this repo, or a POSIX clone appears — then
  `eol=crlf` would impose Windows endings on that checkout and the default line
  must drop to plain `* text=auto`. Verified 2026-08-18: no remote exists.
  Standing check after any bulk write or `.gitattributes` edit:
  `python tools/shell-audit/invariants.py` (mixed-ending count must stay 0).
- rollback: delete `.gitattributes`; `core.autocrlf=true` resumes governing.
  Working-tree endings revert on the next checkout.

### graph rot watchdog — ops-health check 15 + daily task
- current: `tools/graph-snapshot/gs_watchdog.py` rebuilds the graph, compares
  live-surface broken-link count and premise metric against the previous run,
  and writes `out/watchdog-status.json` (+ a history jsonl). Carrier:
  scheduled task `ClaudeGraphSnapshotWatchdog-Daily` (12:30, same convention
  as the transcript mirror). Surfacing: `ops_health_nudge.py` check 15 reads
  the status file at session start (cwd == `~/.claude` only, report-only,
  fail-open) and fires on: status older than **3 days** (`WATCHDOG_STALE_DAYS`,
  provisional — daily task, so 3 tolerates two missed days), live count grown,
  or premise under **90%** (`gs_watchdog.PREMISE_FLOOR`, the design's
  pre-registered line).

### session mirror heartbeat — ops-health check 17 + the mirror's run ledger
- current: the daily transcript mirror (`tools/claude-session-transcript-mirror.ps1`,
  the scheduled copy job that feeds it, 13:00, D-033) writes a last-run
  marker + an append-only `run-ledger.tsv` (status, exit, jsonl count, MB —
  the count may only grow under the COPY-ONLY contract; a drop between lines
  means archive loss). Surfacing: `ops_health_nudge.py` check 17 reads the
  marker at session start (cwd == `~/.claude`, report-only, fail-open): FAIL
  marker fires regardless of age; marker older than **3 days**
  (`MIRROR_STALE_DAYS`, provisional — same two-missed-days argument as check
  15) fires; marker missing inside an existing archive root fires; a host
  without the archive root is silent by design. Test seam:
  `OPS_NUDGE_MIRROR_MARKER` env var (5 hermetic cases in ops-health-test,
  3 known-TRUE / 2 known-FALSE).
- why: D-052 item 5 (user ruling 2026-09-01) — the mirror was silent-when-dead:
  it wrote a marker nobody read, and the discovery moment for a dead backup is
  the data-loss moment.
- review-when: the archive moves off any configured mirror root (constant
  `MIRROR_MARKER` + the ps1's `$Dest` change together), or cleanupPeriodDays
  semantics change in Claude Code (re-derive the staleness tolerance).
- why: measured 2026-08-26 — live-surface broken links went 14 → 38 in the six
  days nobody ran the audit, then 38 → 0 in one harvest round. The integrity
  report only pays rent when something runs it, and SessionStart is the only
  moment a reader can act (same reasoning as check 14). The comparison lives
  in `gs_watchdog.evaluate()`, a pure function with injected inputs
  (lessons.md L-031), driven two-sided by 6 smoke-test cases.
- evidence: `references/graph-snapshot-phase-log.md` Phase 2 checkpoint;
  three-sided control run 2026-08-26 (growth fires / stale fires / healthy
  silent); first task run exit 0, log line in `out/watchdog-task.log`.
- history: born 2026-08-26 (Phase 2 gap-fill round, user-approved 🔴 change).
- review-when: the daily task is removed or the machine's scheduling story
  changes; graph-snapshot's covers change enough that "live surface" means
  something else; the premise floor is re-ruled.
- rollback: `backups/2026-08-26/ops_health_nudge.py.pre-check15`;
  `schtasks /Delete /TN "ClaudeGraphSnapshotWatchdog-Daily" /F`; delete
  `tools/graph-snapshot/gs_watchdog.py` + `watchdog-task.ps1`.

### cc version reconcile — ops-health check 16 + tools/cc-delta
- current: `ops/cc-reconciled.json` stamps which Claude Code build the ops
  layer has been reconciled against (plus a `stat()` fingerprint of
  `~/.local/bin/claude.exe`). `ops_health_nudge.py` check 16 compares the
  fingerprint at session start — free — and spawns `claude --version` ONLY
  after the binary moves; on a version mismatch it `insert(0)`s a line, because
  `msgs[:4]` is routinely full of budget nudges and this one says the rules
  being followed may not describe the running build. `tools/cc-delta/cc_delta.py`
  produces the actual delta: changelog entries in `(stamped, running]`, filtered
  to eight categories that mirror what `ops/` records. NOT `is_home`-scoped — a
  stale ops fact misleads in whatever project is open.
- why: measured 2026-08-26 — the CLI went 2.1.200 → 2.1.246 while `ops/` sat at
  `as-of 2026-08-12`, and 8 recorded facts had gone stale, one of them listing
  the Workflow tool as an available dispatch mechanism in an environment whose
  `settings.json` disables it. This registry already carried 6
  `review-when: any Claude Code upgrade` entries and **no carrier ever fired
  them**; a control that rots silently is worse than none.
- evidence: three-sided control 2026-08-26 — stamp==running silent and the
  other 15 checks unaffected (294 ms); stamp=2.1.200 + stale fingerprint fires
  FIRST (587 ms, both inside the 3 s hook budget); stamp deleted reports the
  mechanism uninstalled. Tool calibrated two-sided: in-sync says so, the real
  2.1.200→2.1.238 backlog keeps 442/859 bullets (**51.5% selectivity** — a
  filter near 0% or 100% is broken, not clean). Detail:
  `reports/2026-08-26-cc-version-reconcile-2.1.200-2.1.246.md`.
- instrument note (load-bearing): `claude update` refreshes NEITHER
  `cache/changelog.md` NOR `.last-update-result.json` — measured across the
  2.1.239→2.1.246 upgrade, both kept serving the old number. Any future version
  check built on those reads stale data that looks live. `claude --version` is
  the only source. The env var `AI_AGENT` would be a free exact one but on
  2026-08-26 it agreed with `claude --version` while both read 2.1.246 — a
  one-sided calibration that cannot discriminate; the test to validate it is
  recorded in the stamp file.
- history: born 2026-08-26, same round as the 2.1.200→2.1.246 reconciliation.
- review-when: the stamp is bumped WITHOUT a pass having been done (that turns
  the whole mechanism into a silent no-op — the exact failure it exists to
  prevent); `cache/changelog.md` stops being the changelog cache path; the CLI
  install moves off `~/.local/bin/claude.exe`; `AI_AGENT` gets validated and
  replaces the subprocess.
- rollback: `backups/2026-08-26/ops_health_nudge.py.pre-check16`; delete
  `ops/cc-reconciled.json` + `tools/cc-delta/`.
