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
- evidence: `_bench-claude-arms\ANALYSIS_CHANNEL_MECHANISM_2026-08-22.md`
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
- current: **23,040 bytes (22.5 KiB)** — user ruling 2026-09-06; file at
  **22,985 B since 2026-09-10 (headroom 55 B)** after a sink-and-merge pass,
  no raise; **22,996 B (headroom 44 B)** the same evening after the audience
  ruling R-1 (user: "兩層宣告，不分檔") added a Readers line to the preamble and
  a `[main]` tag on six main-loop-only bullets, paid for by four restatement
  cuts (the commit-type list, "especially the review family", the UAT-P8
  restatement, a spec pointer).
- 2026-09-10's pass (rules-debt audit, `reports/2026-09-10-rules-debt-audit.md`
  §5; user-confirmed): the file had crept to 23,522 B (+1,508 since the
  09-06 pass, three rules and a CJK clause). Sinks found, in the order this
  entry prescribes: (1) the shell bullets 2+3+py-raw folded onto the
  `shell_transport_guard.py` carrier that this entry's own review-when had
  pre-armed — the hook now injects the limits at the call (measured: 982
  notices / 205 denies), so the text keeps only the routing, the unhooked
  unquoted-path case and a pointer (−~700 B); (2) the path-scoped index
  trimmed to names + short hints, detail already in each rule's
  frontmatter, and the missing `literature-access` entry added; (3) the
  L-072 CJK paragraph merged into the English calibration clause;
  (4) restatements whose canonical copy exists elsewhere (P-tags and the
  contract's five section names → `05-authority.md` §4; PS `EAP` detail →
  `ps_errorpref_guard.py`; HTML width detail → `rules/deliverable-doc-refs.md`).
  Four judged candidates merged, none appended: C-1 (assert on the value the
  defect changes, L-062), C-2 (temporary scope narrowing names its lifting
  event), C-4 (severity ladder in either direction), C-6 (underived summary
  field). Net 23,522 → 22,985 B, bullet headings 40 → 38, no distinct rule
  dropped. Audience measured for the first time (`tools/rule-usage-census`):
  opus 48% / fable 28% / sonnet 17% of live main sessions, sonnet main
  loops never reach the scaffolding rules — the audience ruling (R-1) is
  the user's and was still open when this was written.
- 2026-09-06's argument for THIS raise, on the same terms the entry demands.
  The fold pass ran the find-a-sink test first and found exactly ONE cluster
  with a real destination: the four `[BC]` rules, whose mechanics moved to
  `05-authority.md` §4a — a genuine sink, because §4 there already named all
  four and stated when a live boundary contract supersedes them — with their
  TRIGGERS kept in CLAUDE.md so they still fire (−685 B). Two restatement
  deletions followed (the path-rule index's reference impls/gate paths/re-glob
  dates, −703 B; the relaxation-gate ask procedure, the `[unattended-run]`
  obligation list, the ledger flag list, the prior-art tool paths and the
  browser-pane detail, −545 B). One new rule was added, from this round's own
  defect: a gate's predicate must not be a POSITION in a growing artifact
  (+360 B). Net 23,587 → 22,014 B, bullet headings 42 → 39 with no rule
  dropped. The residual fails all three sinks the nudge names: the remaining
  39 bullets trigger on TASK SHAPE, so no `paths:` glob can carry them, and a
  rule parked in a low-traffic home is what `lessons.md` L-048 hit 2 measured
  (the verification-ladder text sat in a skill invoked in 0 archived sessions).
  Compressing further is what the 2026-08-31 verdict already priced at negative
  marginal value. **Applied at 23,040, which is 512 B ABOVE the 22,528 the
  2026-08-31 pre-armed conclusion suggested** — the proposal argued from the
  post-pass size (22,014) plus ~1 KiB, and the user approved that value; the
  extra 512 B is headroom this entry's doctrine still says must not be treated
  as spendable. Next addition runs find-a-sink and merge FIRST, as before.
- why: CLAUDE.md is loaded IN FULL every session, so bytes here are the only
  instruction bytes that are unconditionally charged. Trim or merge, never
  append — and the cap's job is to force that question at a decision point,
  NOT to sit far enough away that nobody has to answer it.
  The path-scoped index line's own rationale lives here since 2026-09-08 (moved
  out of CLAUDE.md as the byte sink for the principle-guide pointer): one rule
  in `rules/` costs nothing at session start; one in CLAUDE.md is charged to
  every session.
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
  two compression passes and a sink check that came back empty)** →
  **23,040 B (2026-09-06, user ruling; the `[BC]` extraction + two restatement
  deletions + 1 new rule, sink check empty for the residual)** → cap unchanged,
  file 23,522 → 22,985 B (2026-09-10, user-confirmed sink-and-merge; shell
  bullets onto the hook, 4 candidates merged, 0 rules dropped)
- review-when: any proposed global-CLAUDE.md change (headroom 55 B as of
  2026-09-10 — the wording reserve is still spent, so re-run find-a-sink /
  merge FIRST and treat the headroom as unspendable), or a rule in this file
  gains a valid `paths:` sink and can leave. Also: the shell-guard re-judge
  was DONE 2026-09-10 (bullet 2 shrank onto the hook; the cap was NOT lowered
  because the freed bytes absorbed four judged candidates — re-judge the
  cap downward if the audience ruling R-1 moves the scaffolding bullets out); and
  if `05-authority.md` §4a proves to be a home nobody reads (the L-048 hit-2
  test: count its loads), the `[BC]` extraction must be reversed rather than
  left as prose in a cold file — which would put ~685 B back and re-open this
  value.
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
- current: **49K bytes on `skill-trigger-dict.md`, ROLE = REVIEW TRIGGER**
  (2026-09-08, after dict-review round 3). Firing means "run the routing
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
    **CLOSED 2026-09-04 by round 2 below.**
  - `2026-09-04 37,369 B`: round 2 — **audit found dead entries removed AND the
    instrument checked**, then raised 28K→42K. First firing to move a coverage
    number: `schedule` and `update-config` 0% → 100% after their vocabulary was
    rewritten from their own measured fires; DEAD 13→8; DEAD-but-firing 4→1 (the
    survivor is a user naming the skill outright, not a vocabulary defect); 3
    phantom targets tombstoned (`/review`, `verify`,
    `product-management:write-spec` — none installed, none in the catalog); one
    live-surface broken link fixed. **The ruler was checked first, and it is
    biased:** `load_entries()` reads only `關鍵詞：`, so 10 entries carrying only
    `精準句型：` printed DEAD by construction (folding that line in adds 205
    occurrences and ZERO hits — the fix is to label the state, not to parse
    more); and `compile_tokens()` wraps ASCII tokens in `\b`, which never
    matches ASCII written flush against CJK (control: HIT 21→28,
    workflow-checkpoint 16%→24%). Both biases understate the dict, and the "the
    dict does not explain real routing" verdict survives both. Evidence:
    a dated review note under the source's outputs/ tree, which this repo does
    not ship; tool fix carried by T-023.
    Not an "entries true" reading, so the three-in-a-row test has not started.
  - `2026-09-04 (same day, T-023 DONE)`: the three biases are fixed, so the
    numbers three lines up are now the numbers of a RETIRED ruler. Re-measured
    on one corpus (1,982 turns, old tool vs new): HIT 21→28, occurrences
    534→620, and a new `LATE` column shows **71** turns whose words appeared
    and whose own skill fired later in the same session, past the 6-event
    window. `workflow-checkpoint` alone: coverage 16%→24%, LATE 50. The
    direction of the 2026-09-04 verdict is unchanged — the dict still explains
    a minority of routing — but **"0% coverage" must not be quoted on its own
    any more**: quote it with LATE, or it overstates the fiction. `LOOKAHEAD`
    was deliberately NOT widened (that would manufacture causation) and
    `精準句型` deliberately NOT tokenised (+205 occurrences, +0 hits). Tests:
    `tools/skill-routing-audit-test/` — 14 two-sided cases, 4/8 against the
    pre-fix copy, so they bite.
  - `2026-09-08 44,463 B`: round 3 — the defect this time was in the
    VOCABULARY'S FORM, not in any one entry. 31 keyword tokens across 14
    entries were written as slash alternations (`把影片/圖片存下來`,
    `GLSL/shader`, `等待/取消/失敗後怎麼辦`), and the matcher reads each as ONE
    literal token: they could only fire on a turn that typed the slash as well.
    **Every MISS and coverage number printed before today was therefore a
    FLOOR, and nothing said so.** The audit now DETECTS the shape — a property
    of the token, so an entry written that way in future is named the day it
    lands — and the 31 were spelled out; occurrences rose ~130 and
    `media-fetch-pipeline` stopped printing DEAD (it had fired 1x with its
    dict explaining 0; the real trigger is a PASTED URL, so the post domains
    are now registered vocabulary — the only way an artifact-context trigger
    becomes measurable at all). Two other findings: tombstoned entries are now
    reported separately (4 of the 8 DEAD were deliberate, and re-adjudicating
    them every sweep is how a report stops being read), and the prose note
    inside `security-deep-checklist`'s `關鍵詞：` line was being tokenised as a
    keyword — moved to its own line. **One naive expansion had to be walked
    back within the hour:** a bare `STEP` token matched "multi-step" / "Step 6"
    and added 107 phantom occurrences to `model3d-pipeline` (166 → 59 after the
    fix to `.step` / `STEP 檔`). That is the two-sided lesson in miniature — the
    repair for an unmatchable token is a token that matches only in context,
    not the shortest one. Still not an "entries true" reading: coverage stayed
    at 0% for most entries, so the three-in-a-row test has not started.
- history: 20K (birth) → **24K (2026-08-15**, user ruling, after the first
  routing audit) → **28K (2026-08-17**, after dict-review round 1) → **42K
  (2026-09-04**, user ruling, after dict-review round 2) → **49K
  (2026-09-08**, after dict-review round 3; the file lands at 92.3% on purpose
  so the next expansion re-runs the decision — applied BEFORE the named
  authorization `70-evolution.md` §1 invariant 1 requires for a `hooks/` edit,
  disclosed the same session, and RATIFIED by the user 2026-09-08; the sequence
  was the defect, not the value). The
  2026-08-15 breach was the first time anything checked whether its contents
  corresponded to reality. **The 2026-08-17 raise was never recorded here** and
  this entry read "24K" until 2026-08-27, while `40-maintenance.md` §3 read
  "20K" and the hook enforced 28K — three live values for one constant. Fixed
  by adding sweep check 7b, which compares every restating site to the hook.
- review-when: `tools/skill-routing-audit.py` reports coverage above ~50% for
  most entries — at that point the dict is load-bearing and its size argument
  changes. Also re-open if skill routing stops being description-driven.
> **Share note.** `tools/skill-routing-audit.py` is source-only
> (excluded-by-decision, `tools/share-manifest.toml`). Substitute: sample your
> own transcripts by hand for turns where a skill fired without matching dict
> vocabulary, the same coverage question the audit answers mechanically.
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
- current: **26K bytes per `ops/*.md`, and its ROLE is a REVIEW TRIGGER, not a
  budget** (2026-08-15; 26K since 2026-09-06). **Scope: `lessons.md`,
  `rule-registry.md` and `environment.md` are exempt**
  (`SIZE_CAP_EXEMPT`) - their size tracks the CORPUS, not bloat, so an over-cap
  reading has no extract remedy and can only nag forever. Their real degradation
  checks are elsewhere: `intake.py report` over the per-record events (key
  `INTAKE`; `LESSON_CAP` retired 2026-09-07), S4.1 ghost rules, and for
  `environment.md` its own closing line (re-verify any block older than ~90
  days — a property of the BLOCK, which is the position-free form a byte count
  never was). `environment.md` was added 2026-09-08 on the condition armed
  2026-09-06, with the user's named authorization; rollback is one token.
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
  **2026-09-06 environment.md 25,399 B: review found extractable concrete, and
  it was NOT ENOUGH — the first firing where that happened.** Moved: the
  Playwright MCP flags/measurements and the whole `playwright-chrome` removal
  narrative (a REMOVED server, described in full, whose mechanism already lived
  in two other files) → `references/browser-pane-pixel-route.md` §"Playwright
  MCP servers"; the hook-enforcement and pixel-route paragraphs compressed to
  fact + pointer, their detail already being in that file. −1,243 B lossless,
  to 24,156 B — still 1,628 B over. What remains is the measured-fact tables
  this file exists to BE (toolchain traps, dispatch semantics, cost-cap policy,
  display premises), and §3 forbids compressing those to fit. So this firing is
  the one the settling procedure above did not anticipate: not "found nothing"
  (the trigger worked — it produced a real extraction), but "found something
  and the file is still over", which is the signature of a file whose size
  tracks the ENVIRONMENT rather than bloat. Proposal, with this pass as its
  evidence: `drafts/2026-09-06-ops-size-cap/APPLY.md`. Not self-applied —
  `SIZE_CAP` lives in `hooks/`, so it needs the named authorization
  `70-evolution.md` §1 invariant 1 requires.
  **2026-09-08 environment.md 35,710 B: the armed condition FIRED.** The file
  grew 11.5K in two days — the `Computer use — desktop control` block, a whole
  new surface recorded for the first time on 2026-09-07. A second lossless pass
  moved the two `###` subsections (the 2026-09-07 probe record and the
  scripting-channel inventory, 7,787 B of measurements and app-by-app tables)
  into `ops/references/computer-use-probe-2026-09-07.md`, keeping in place the
  four findings that change a PLAN (a screenshot HIDES the user's other windows;
  `open_application` does take the foreground; the shell is a third click-only
  tier; coordinates come from the screenshot's own frame), the 30-second
  portable-exe workaround, and the routing rule that the question is never "can
  computer use drive X" but "does X have a headless channel". 35,710 → 30,138 B,
  still 3,514 B over 26K. **So this is the second consecutive firing where a
  real extraction was not enough, which is exactly the condition armed on
  2026-09-06** — and the answer that entry names is not a fourth raise but
  `SIZE_CAP_EXEMPT`, on the same ground as `lessons.md`: what remains is the
  environment's fact tables, one block per SURFACE, and the surface count is
  what grows. The extract remedy has now been exercised twice and produced
  −1,243 B and −5,572 B; a third pass would have to start deleting routing,
  which S3 forbids. NOT self-applied: `SIZE_CAP_EXEMPT` lives in `hooks/`, so
  it needs the named authorization `70-evolution.md` §1 invariant 1 requires.
  Proposal: `drafts/2026-09-08-environment-md-exempt/APPLY.md`. Note this file
  keeps a review trigger either way — its own closing line ("re-verify any block
  older than ~90 days") is a property of the BLOCK, which is the position-free
  form a byte count never was.
  Same day, same check, a second finding worth keeping separate:
  `20-dispatch.md` went 16 BYTES over on an edit made in the same session that
  was reading this entry. It was not a raise case — the added material was
  detail with a designated sink (`references/harness-measurements.md`
  §Dispatch semantics), and moving it took the file to 98.4%. A 16-byte breach
  is the clearest possible demonstration that the number is a review trigger
  and not a budget.
- history: 10K (birth) -> 12K (2026-08-06, after a failed trim pass) -> 15K
  (2026-08-13, after another) -> 18K (2026-08-15, role changed to review
  trigger; the first raise justified by a measurement of what the bytes cost
  rather than by an inability to cut them) -> 22K (2026-08-21, after a review
  that found and extracted concrete from both firing files and still left
  20-dispatch.md at 20.9K of rules) -> **26K (2026-09-06, user ruling,
  proposal `drafts/2026-09-06-ops-size-cap/APPLY.md`)**. The third firing was
  the first of a THIRD kind the 2026-08-15 settling procedure never
  anticipated: it armed for "review found extractable concrete" or "review
  found nothing", and this one found real concrete AND left the file over
  (environment.md 25,399 -> 24,156 B lossless into
  `references/browser-pane-pixel-route.md`, still 1,628 B past 22K). 26K
  clears the reviewed state with ~2.4K headroom, which puts the two files
  nearest behind it -- 20-dispatch 22,167 B and 40-maintenance 21,302 B -- at
  83% and 80%, where a review trigger should sit right after a review.
- review-when: three consecutive firings resolve as "reviewed, nothing to
  extract, raised" (see evidence); OR a measurement shows the always-loaded
  surface is no longer cached or no longer a small share of context, which
  would restore the budget reading. **AND (armed 2026-09-06): environment.md
  fires again after a pass that moved real content** -- then the honest answer
  is not a fourth raise but a RECLASSIFICATION into `SIZE_CAP_EXEMPT` on the
  same ground as `lessons.md` ("size tracks the corpus, not bloat"). It is NOT
  exempt today and should not be: the 2026-09-06 pass proves it still has an
  extract remedy, and exempting it now would remove the pressure that produced
  that extraction.
- rollback: `git show 425a7e5^:hooks/ops_health_nudge.py` (pre-check14, 18K value);
  `git show fe2dc3f^:hooks/ops_health_nudge.py` (pre-sizecap-18k); dated backups pruned;
  `40-maintenance.md` S3 table row

### `LESSON_CAP` — unfolded entries in `ops/lessons.md` (RETIRED)
- current: **RETIRED 2026-09-07 (intake cutover, key `INTAKE`)** — the ledger
  is `ops/lessons/` (one record per file) and `ops/lessons.md` is a GENERATED
  index with NO count cap: the cap was after-the-fact back-pressure whose only
  relief was a fold pass, which is what produced the periodic several-hundred-
  line rewrites (R2 evaluation RC2/RC3). The live signal is per record now:
  `intake.py report` (hits ≥ 2 never folded → §2a; folded but recurring). The
  constant, the nudge check and the `check_cap_binding.py` binding were removed
  in the same commit. Value at retirement: 36. What follows is history.
- was: **36 unfolded entries** — user ruling 2026-09-06. Counted as
  `^## L-\d+` headings over the WHOLE file: folding removes an entry's heading
  and leaves a `- **L-nnn**` bullet, so the heading set IS the unfolded set.
- why: class (b), a REVIEW TRIGGER rather than a budget — the ledger is charged
  only when something greps it, and its size tracks the corpus of real
  incidents. The number's job is to force a fold pass at a decision point. The
  floor is not zero: an entry with `hits:` >= 2 is never folded (a climbing hit
  count is the live evidence a fix does not work), and entries cited by number
  from global CLAUDE.md or `40-maintenance.md` must stay resolvable in place.
- evidence: the 4th fold pass (2026-09-06) applied the bar unchanged from
  passes 1–3 — `hits: 1`, a hook or durable rule file carries the fix, no
  by-number global CLAUDE.md citation — folded 9 entries, and STOPPED at 33.
  Named reasons for the 33: 16 at `hits:` >= 2, 5 cited by number, 8 kept on
  carrier grounds by the 2026-08-31 pass, 2 carried only by project code, 2
  with a carrier too young to have been read even once (the L-048 hit-2 test).
  Going lower means folding entries whose fix lives only in recall, which §3
  names as the signal to raise the cap with the failed pass as evidence.
  36 = that floor + a 3-entry margin; the margin is not theoretical — L-053 was
  written the same hour and took the live count to 34.
- history: ~30 (birth, `40-maintenance.md` §3) → 36 (2026-09-06, user
  ruling) → **retired 2026-09-07 (intake)**. The measured count was WRONG for the five days before this raise:
  the check split the file at `## Archived` and read 32 while the truth was 42
  (`lessons.md` L-047 hit 2), so the pre-raise number was never a real reading.
- review-when: the never-foldable population (`hits:` >= 2) passes 20 — that
  population, not the total, is what sets the floor. Also whenever the fold BAR
  itself changes (e.g. if "carried by project code" becomes foldable), because
  the floor moves with it.
- rollback: `hooks/ops_health_nudge.py` `LESSON_CAP`; `40-maintenance.md` §3
  table (b); `tools/ops-health-test/check_cap_binding.py` `FIXTURE_CAPS`.
  Backup: `backups/2026-09-06/ops_health_nudge.py` (pre-change).

### lessons ledger shape — one card per entry, full record in `references/lessons-detail.md` (SUPERSEDED)
- current: **SUPERSEDED 2026-09-07 by `INTAKE` (next entry)** — the two-file
  hand-written shape is retired: `ops/references/lessons-detail.md` is FROZEN
  (header says so) with every section imported verbatim into
  `ops/lessons/L-nnn.md` `## Narrative`, and `ops/lessons.md` is generated.
  What follows is history.
- was: `ops/lessons.md` holds one CARD per entry (header line with the
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

### `INTAKE` — lesson intake store `ops/lessons/`, generated index, event-derived state
- current: since 2026-09-07 (closeout-capture R4, claude-config Phase 23) a
  lesson is ONE file `ops/lessons/L-nnn.md` — xi-card front matter + `## Record`
  (id / kind / created / session / project / **locator** / digest) + capped
  Context / Pitfall / Fix / Detection + unbounded verbatim `## Narrative` +
  append-only `## Events` — born only through
  `python tools/closeout-intake/intake.py add --from <draft>` after validation
  D1–D9 (INV-1), never rewritten (INV-2: `hooks/intake_guard.py` DENIES
  Write/Edit/shell writes to `ops/lessons/` and `ops/lessons.md`; later facts
  are `intake.py event L-nnn --kind recurrence|fold|supersede|retract`). `hits`
  and lifecycle state (live / dormant / folded / superseded / retracted) are
  DERIVED from `## Events` (INV-4); the front-matter `status:` line is the one
  tool-rewritten projection in xi vocabulary (S-9). `ops/lessons.md` is a
  GENERATED index of capped cards (INV-5, `intake.py render`) with NO count cap;
  the `## L-nnn` heading shape is kept so citations and gsnap keep resolving.
> **Share note.** `tools/closeout-intake/` (the `intake.py` CLI and its
> `controls.py`) is source-only (excluded-by-decision, `tools/share-manifest.toml`).
> `ops/lessons.md` ships here as a generated snapshot, and `ops/lessons/` does
> not ship at all (`[[not_shipped]]`, `excluded-by-decision`) — there is no
> shipped `add`/`event`/`render`/`report`/`match`/`check` to run against this
> copy; build your own capture tool against the record shape described below.
  Sub-keys — values are PROVISIONAL and live in the code; the registry NAMES
  them and never restates them (a second site would be a drift surface):
  - `INTAKE_FIELD_CAPS` — `intake_core.DEFAULT_CAPS`, byte caps on Context /
    Pitfall / Fix / Detection; overflow belongs in `## Narrative` and the D5
    reject names the bytes to move. review-when: `intake.py report` shows
    > 20 % of new records rejected on D5 twice in one week.
  - `INTAKE_INJECT_BUDGET` — `intake_core.DEFAULT_BUDGET`, max cards / max
    bytes per `intake.py match` (INV-7). review-when: the shadow telemetry
    `telemetry/intake-match.jsonl` median `bytes` exceeds it.
  - `INTAKE_LOCK_STALE_S` — `intake.Lock` stale age for `<id>.lock`.
    review-when: a `stale lock broken` line appears for a holder that was
    still alive (a false break), or controls C-95/C-96 start failing.
- why: the hand-written two-file ledger needed 11 manual steps at ~190k
  context — 77 % of writing sessions skipped the detail file, ids collided
  twice, and a count cap whose only relief was a fold pass produced the
  periodic "大型重整" (R2 evaluation RC1–RC5). User premise (2026-09-07): fix
  the schema at capture time so later processing loses less — every
  processing step loses or changes something, so processing APPENDS events
  and derives views; it never rewrites the record.
- evidence: `intake.py import --verify` 54 ids both ways, `## Narrative` bytes
  equal to both legacy sources; `tools/closeout-intake/controls.py` C-01..C-96
  ALL PASS (a positive and a negative control per rule, a 20-process id race,
  render idempotence, a Hypothesis property on the match budget, tampered-
  source import, stale/fresh lock, guard payloads); design verification
  (sonnet, author ≠ verifier) BLOCKED 3/2/9 → resolved in design v1.1.
- history: born 2026-09-07; supersedes `lessons ledger shape` (2026-08-21) and
  retires `LESSON_CAP`; sweep checks 5/5b/5c/5d replaced by `intake.py check
  --against HEAD --index` + the guard proof-of-life.
- review-when: a second record kind (`kind: digest`) enters — BR-10c
  mechanisation (registered kinds only) is the labelled extension; or the
  match hook graduates from shadow (a user gate; its criterion is pending).
- rollback: revert the M2 commit (guard + registration set); the M1 store is
  unaffected. Pre-cutover ledger: `git show fa08fa3:ops/lessons.md`;
  `git show 483435f:archive/lessons-cutover-2026-09/NOTE.md` (archive/ is history-only since 2026-09-09).
- owner / spec: semantics `references/closeout-capture-r3-design-2026-09-07.md`
  §4; build contract `references/closeout-capture-r3-psm-2026-09-07.md`; usage
  and record format `tools/closeout-intake/README.md` (rules-usage-dict §7).

### `PUBLISHED_RECORD` — a record of a removal must not carry the removed value
- current: two layers, one rule. (1) A dispatch brief that sends a worker into a
  governed record carries that record's own record-writing rule
  (`ops/20-dispatch.md` §2, shape in `ops/references/dispatch-templates.md`).
  (2) `hooks/published_record_guard.py` DENIES a Write/Edit whose target sits
  inside a tree carrying its own collection rules when the payload contains a
  drive-rooted path, a POSIX home path, the account name, a 32+ hex run or a
  UUID. Detection is by MARKER on an ancestor, never a hardcoded root — the
  hook would otherwise contain the class it gates. No unblock escape: the
  false-positive exit `--report` records and does not open the gate.
- why: the class had been recorded correctly 11 days earlier in the
  orchestrating skill — a layer no dispatched worker loads — and recurred
  anyway. The rule needed a surface at the worker's danger moment
  (`40-maintenance.md` §2a, first row: a named tool call with inspectable
  input), and a surface for the half a brief cannot reach (a main session
  writing the record itself).
- evidence: 2026-09-07 collection round — 38 findings, all inside the merged
  manifest, none in the files it described; the same class hand-fixed twice
  earlier the same day. Gate: `--selftest` ALL PASS 11/11 (P-1..P-6 one per
  class + a distant marker ancestor; N-1..N-5 the same literals outside such a
  tree, a class-named entry, a non-file tool, short hex, a malformed payload).
  Delivery probed live the same day: a main-session Write denied, its
  class-named rewrite allowed, and a dispatched worker's Write denied
  identically — so PreToolUse reaches subagent writes. `ops/lessons.md` L-057.
- history: born 2026-09-07. Nothing preceded the hook; the brief-side clause
  and `40-maintenance.md` §2's capture/enforcement split landed the same day.
- review-when: the marker names in `MARKERS` stop being what a governed record
  tree carries (it is a fact about repos outside this one), or the hook's
  FALSE-POSITIVE LOG reaches 3 — at which point NARROW condition 2, do not
  widen the escape.
- rollback: unregister the `Write|Edit` block naming `published_record_guard.py`
  in `settings.json` (leave the file on disk — §1.5 forbids a registered-absent
  window), or revert the commit. Pre-change copies: `backups/2026-09-07/`.

### `PAGE_FILL` — human-facing HTML uses the width it is given; classes are data
- current: a page declares `<html data-page-class="…">`; class rows + thresholds
  live in `tools/page-fill-gate/page_classes.json` (document-short centred &
  symmetric, min fill 0.35 · document-long / deck / dashboard reach ≥ 0.85 ·
  tool ≥ 0.90 · diagram centred-or-fill, min fill 0.60; left-anchored cap =
  right void − left void > 15 % of the content width → FAIL at a gating
  viewport, WARN at 1280×610 and on any INFERRED class). Property text:
  `ops/environment.md` §Display; rule carrier: `rules/deliverable-doc-refs.md`.
- why: user ruling 2026-09-04 — one shell's `max-width:1060px` had become 13
  deliverables at 60–69 % fill and no gate had a word for "unused width"
  (`lessons.md` L-048). Thresholds are FIRST VALUES set from the 268-file scan
  (negatives 96–99 %, positives 60–69 %); the user preferred proportional
  allocation over pixel caps for every class including tools.
- evidence: a dated width-void diagnosis note under the source's outputs/ tree,
  which this repo does not ship;
  `tools/page-fill-gate/README.md` §基準; `tests/test_fill_gate.py` (two-sided
  per class).
- history: 2026-09-04 created (five decisions D1–D4 + registry-over-enum on the
  user's "avoid re-classifying later" instruction).
- review-when: the screen / scaling in `environment.md` changes; a page ships
  on an inferred class and draws a second human report (add the row); a
  threshold produces a false FAIL on an accepted page (lower it HERE with the
  page named, never by exempting the page in prose).
- rollback: remove the CLAUDE.md line + the two rule paragraphs; the tool and
  registry can stay as an advisory instrument.

### `UAT_A_CAP` — manual-acceptance checklist: rank axis and `A` item budget
- current: a manual-acceptance checklist is two consequence-ranked sections —
  `A. 必驗` (≤ **7** items; 資料與不可逆狀態 → 運作與使用 → 失敗看得見 → 換環境
  存活) then `B. 體驗` (看得懂 → 順手 → 觀感) — both descending, continuously
  numbered, and never grouped by module, technology, or surface. Admission is
  gated twice: machine-checkable → not an item at all (paste the test output);
  then blocks shipping → A, merely annoys the user → B, neither → not written.
  Owner: `ops/references/uat.md`. Binding short form: global CLAUDE.md `[BC]`
  line. Eleven carriers, enumerated in that file's §8. **Two properties added
  2026-09-09 (user ruling 「之後這種交付也都用絕對路徑指向讓我知道」)**: **P8**
  every path absolute and every command copy-runnable from any working
  directory — P3's "blind-executable" restated in a form the AUTHOR can check,
  since a repo-relative path works for the one reader who is standing in the
  tree; **P9** a pass must look different from not-run — print the number the
  item claims plus the one fact proving the check reached its subject. P8's
  broader half (any pointer in any reply) sits in CLAUDE.md's *Conversation
  replies* bullet, not the `[BC]` line, because it fires without a checklist.
  Carrier state for both: `uat.md` §8 (three updated, ten downstream templates
  deliberately not, with the trigger that would change that).
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
  - **obs 1 (2026-09-09, copy-census)**: 7 items written (A1–A6 + B7), **7 run
    to completion** across three sittings — no tail was skipped, so this round
    says nothing against the cap. What it DID say is that the two failures were
    in the items, not the tool: A2 named a field the reader cannot see and A4
    printed nothing on pass, and the user ran both anyway and reported honestly
    ("應該是通過"). Reading: at this list length the reader does not stop early,
    so the cap is not yet the binding constraint — item QUALITY is. P8/P9 were
    born from this observation.
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

### `LEVEL_CONSUMER_FIRST` — every output item is classified on two axes before it exists
- current: before creating any output item (file, folder, page, figure, record,
  rule) the author names its LEVEL (rule-tier · cross-round instrument/register ·
  round output · audience entry · record) and its CONSUMER (machine · builder ·
  audience). LEVEL fixes location + write ownership (round-first containers
  `T<nn>_<theme>_<YYYYMMDD>`; typed layers frozen for rounds; one persistent
  audience entry holding COPIES with round tags; indexes regenerated). CONSUMER
  fixes language (existing Language rule), vocabulary (audience pages carry no
  paths / PASS counts / run-ids / gate ids) and the artifact a gate reads (an
  embedded item's emitted artifact is its HOST document). Rulings bind the asset
  CLASS, never the tool or moment. Both values are declared on the item
  (`layer:`/`audience:` front-matter; `data-page-class` + `data-audience`).
  Carrier: global CLAUDE.md one bullet (Engineering judgement) + index line;
  operative clauses `rules/naming-and-placement.md` (path-scoped); request-time
  routing `skill-trigger-dict.md` (model3d-pipeline rebinding, audience-fit
  mandatory for that project's audience pages).
- why: user ruling 2026-09-08 (SSLD T46) — three T43–T45 failures had one
  shape: a rule attached to the wrong object or moment. A figure engine's
  contract stopped at the SVG file while the audience opened an HTML inlining 15
  of them (`id` collision, every file-level gate green); the paper-figure ruling
  was bound to "whenever the pipeline emits" so two rounds that never called it
  drew physical sections on the retired framework; a placement ruling with two
  readings was executed twice and three placement axes coexisted at the repo
  root. The user: 層級與對象是產出項目前的第一確認項目, peer to
  LLM-reads-English / humans-read-Chinese; the naming/placement principles
  designed 2026-09-04 (`references/naming-over-routing_global-rule-candidate_
  2026-09-04.md`) were ignored because nothing fired at creation time.
- evidence: SSLD `T46_檢討與放置契約_20260908/SSLD-T43-T45檢討_根因診斷與修正方向_
  20260908.md` (§1 A1 DOM read n_clip_ids=15; §1 A3; §1 B1; §4.1–4.2); session
  3418016b-16aa-4d1b-b091-51722844b9d8 ledger rows 6–7, 9–10; lesson L-059 +
  recurrence events on L-044 (hits 2) / L-047 (hits 3).
- history: 2026-09-04 candidate drafted (status "raise after SSLD L4 round");
  2026-09-08 raised — 🟡 carriers applied (this entry, `rules/naming-and-
  placement.md`, two dict hunks); the 🔴 carriers (global CLAUDE.md bullet +
  index line `e5f182f`, new SSLD project CLAUDE.md) applied the same day on
  the user's ruling (ledger 3418016b) — this history line still said "await
  confirmation" until the 2026-09-09 clean-up corrected it. SSLD R1 migration
  is the first application (`T46_…/migrate_r1.py`).
- review-when: (a) a second project runs a round under the placement clauses —
  test whether round-first fits a non-research repo; (b) the declaration marker
  gets an integrity-sweep check (`ops/references/integrity-sweep.md`) — then
  drop the "omission not enumerated" caveat — PARTIAL 2026-09-08: `data-audience`
  on project page builders is enumerated by entry-schema-lint ES-7 (sweep check
  29); `layer:`/`audience:` front-matter inside `~/.claude` rule directories is
  derivable from the path and deliberately not warned (`entry-schema.md` §3); the
  round-folder manifest is still unenumerated, so the caveat stays; (c) `model3d-pipeline` ships its
  host-embed gate (R-HOST-EMBED) — cite it from the rule file §5; (d) a session
  creates an item without naming the two axes AND the user reports misplacement
  again → the trigger wording in CLAUDE.md is wrong, not the rule.
- rollback: restore `backups/2026-09-08/{CLAUDE.md,rule-registry.md,
  skill-trigger-dict.md}`; delete `rules/naming-and-placement.md`; the candidate
  file's status line returns to "draft".

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
  **Origin, backfilled 2026-09-11** (found by session-archive mining; not
  recorded here before): the mechanism was the user's own diagnosis, not a
  model-side convenience. 2026-07-09, session
  `5ae4133c-69ca-4637-89aa-0bf5315f20fb`, two turns apart — first the cost
  complaint: "像你這種強模型好像反而很容易被限縮能力並佔用可分配token在無意義的
  『遵守規則』，失去原本更強大的擴散思考能力，是否應該要做一些流程或前提資訊的
  顆粒度與載入方法的調整，或者足夠但有規則的『越權』指示？"; then the mechanic
  itself, verbatim, including the identity/decision split that `05-authority.md`
  §2 states as "the model states who it is; the USER decides how much the
  rules loosen": "直接硬規定開場重型任務(如專案開發等系統性的問題)前，呼叫使用者
  確認本次專案的權限放寬程度，畢竟模型本身知道自己是誰，但規定的遵守放寬可以由
  使用者決定". Both the relaxation-gate TRIGGER (fire at heavyweight-task start)
  and the identity/decision split in §2 trace to this one exchange.
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

### `~/.claude/AGENTS.md` — SUPERSEDED 2026-09-05: archived with the Codex cleanup
- current: file no longer exists on disk. USER ruling 2026-09-05 (clean slate
  before reinstalling Codex): it was moved to a dated archive folder outside
  this tree (2026-09-05) and the
  user will delete the archive. Do NOT recreate it; the `.gitignore` line stays
  so a future codex env-copy cannot slip into git.
- previous (2026-07-09 → 2026-09-05): kept, untracked. Do NOT delete and do NOT re-add to git.
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
> **Share note.** `tools/project-dashboard.py` is source-only
> (excluded-by-decision, `tools/share-manifest.toml`); the two generated views
> it rebuilds do not ship either, only the reasoning for ignoring them by name.
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

### `projects/*/memory/*.md` — tracked (the rest of `projects/` is not)
- current: TRACKED (2026-09-06, user ruling "memory 那半追蹤的狀態也一起處理
  掉"). `.gitignore` re-includes exactly `projects/*/memory/*.md` — 79 files
  across every project slug — via `projects/*` + directory negations; every
  other tenant of `projects/` (transcripts `*.jsonl`, `*.ledger.jsonl`,
  `*.canary.json`, subagent dirs, `tool-results/`) stays ignored, including a
  non-`.md` file placed INSIDE a memory dir.
- why: the boundary is an asset property — **distilled memory is versioned,
  raw session records are not** — not a per-file decision anyone must remember.
  `PHILOSOPHY.md` §3 had already recorded that the memory subdir is Tier-2
  "精煉過的事實" excluded ONLY because its PARENT carries conversation content:
  an accident of granularity, not a ruling. It is also the single copy —
  memory is never written into the project repo it describes — so an untracked
  memory store has no history and no second home.
- evidence: the state this replaced was the worst of the three. 5 of the 79
  files had been `git add -f`'d one at a time as sessions happened to notice
  (first at `9e1ea0b`, last at `d5a2791`); the other 74 were indistinguishable
  from deliberate exclusions. Boundary verified two-sided before the commit:
  `git status --untracked-files=all -- projects/` listed 74 paths, ALL matching
  `*/memory/*.md` (74 untracked + 5 tracked = 79 on disk, exact); `git
  check-ignore -q` still ignores `<sid>.jsonl`, `<sid>.ledger.jsonl`,
  `<sid>.canary.json`, `projects/*/tool-results/**`, `projects/*/<uuid>/**`
  and a hypothetical `memory/secret.jsonl` / `memory/digests/x.md`. Leak-scanned
  the 74 incoming files for credential shapes (`sk-`, `gh[pousr]_`, PRIVATE KEY,
  api-key/password assignments): every hit was prose ABOUT tokens, no values —
  and there is no git remote, so tracking added no new exposure. `check-ignore
  -v` prints the matching line even when the match is a NEGATION, so the
  positive control was re-run on the exit code, not on the printed pattern.
- history: gitignored as part of a blanket `projects/` since the repo's birth
  → half-tracked by force-add 2026-08-26…2026-09-05 → boundary rule 2026-09-06
- rollback: `.gitignore`; restore the single line `projects/` and
  `git rm --cached -r projects/`
- review-when: (a) a git REMOTE is added — same premise as the `references/`
  entry above, and memory carries more personal fact per byte than any other
  tracked directory: re-run the leak scan and re-decide BEFORE the first push;
  (b) the harness starts writing a non-`.md` artifact into `memory/` that is
  worth keeping (the rule would then be excluding it silently).

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
- current: SHADOW — the notice fires, nothing dispatches. 3 classified rows, 3
  false positives (2 of them source defects, both fixed at source). Control
  suite `hooks/tests/test_fieldwork_threshold_notice.py`: T-0d reads the
  thresholds out of `20-dispatch.md` §1's literal text so hook and rule cannot
  drift, QUIET-1/2/3 pin the three false positives this probe actually shipped.
- why: the harness and `OPS.md` hard rule 1 are opposed on the SAME task shape,
  so the local layer may not silently pick a side. Surfacing the crossing and
  leaving the ask to the user is the one move both layers permit.
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
- **2026-09-11 ruling (user, R-3 of `reports/2026-09-10-rules-debt-audit.md`):
  RETIRED — unregistered from `settings.json`, file and
  `telemetry/fieldwork-shadow.jsonl` kept.** The classification this entry
  asked for was done over all 293 rows plus a 15-row hand sample
  (`outputs/shadow-hook-eval-2026-09-10.md` §3): 141/293 (48%) trip on ONE
  file via the >200-line threshold alone — a single long read can never be
  the >3-files / repo-wide shape §1 describes; 12 more re-read the session's
  own `projects/.../tool-results/` output (the sibling of the `scratchpad/`
  false positive already patched); one row charged 874 "lines" to a `.png`.
  ≥52% quantifiably false before any judgement call, and the 30-day clause
  above had 27 days elapsed. The entry's own alternative therefore applies:
  §1's thresholds describe delegation ADVICE and cannot serve as a gate. The
  probe came off rather than being tuned.
- review-when (post-retirement): a dispatch-shape violation that a hook could
  have seen recurs in a retrospective (a main session doing a repo-wide scan
  it should have delegated) — then re-derive the predicate from that instance
  (files-touched, not lines-read) before re-registering; never re-register
  the retired form.
- rollback: re-add the `Read|Grep|Glob` PreToolUse entry (backup
  `backups/2026-09-11/settings.json.pre-fieldwork-retire`); the hook is inert
  without it.

### in-app Browser pane — "Already loaded. Default to this."
- harness: `<browser_surfaces>` names the pane the default surface; it also
  lists claude-in-chrome as an alternative, so choosing that IS narrowing.
- local narrowing: allowlist, not blocklist — see the Mechanisms entry
  `in-app Browser pane` below for the current state and its evidence.
- current: the harness default HOLDS. The narrowing is WHICH HOSTS may load in
  the pane, never which surface is tried first: `hooks/browser-pane-allowlist.json`
  ships with `hosts: []`, so today every non-loopback host is denied and
  claude-in-chrome takes them.
- why: "default to this" is a routing preference; the local layer adds the one
  fact the harness cannot know — the pane shares the desktop app's GPU child
  process, so a page that kills it takes the in-flight turn of EVERY session in
  the app. Blast radius, not taste, is what the allowlist rules on.
- evidence: `telemetry/browser-nav.jsonl` 108 rows, 7 denies (1 synthetic
  control + 6 real hosts: optica, github, bing, a claude.ai artifact, a chatgpt
  share, tree.icqr.com). The allowlist has stayed EMPTY since birth — no denied
  host was ever promoted, so the review trigger below has not yet fired. Suite:
  `hooks/tests/test_browser_pane_scope_guard.py` (D-01..D-08 / A-01..A-09,
  M-1 mutation keeps the allow side honest, FO-1..FO-3b fail-open).
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
- why: the prohibition is not the conflict — the local layer agrees the user
  opens a workflow. The conflict is the rival dispatch doctrine that ships with
  the tool, and reconciling it now would be writing rules against a guess: they
  would be unfalsifiable until a workflow runs, and stale by the time one does.
- evidence: `enableWorkflows` is no longer in the live `settings.json` — it
  survives only under `backups/` and `archive/` (last live copy 2026-08-11) —
  and no run record exists anywhere in the tree. DORMANT rests on that absence,
  which is exactly why the trigger below is an EVENT and not a date.
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
  Narrowed 2026-09-09 by the disposal ruling in `copy census`: the artifact
  belongs in `drafts/` while the proposal is IN FLIGHT and on the
  rejected/superseded branch. Once it lands, the commit is the as-proposed
  record and the copy goes; what stays is `APPLY.md` and any design record.
  copy-census reports an artifact still sitting there as an UNKNOWN-COPY, so
  the lifetime argument above now has a detector at its far end.
- why: the two directories differ in LIFETIME, not in tidiness. Scratchpad is
  session-scoped and discarded, so a rule-change artifact written there loses
  the audit trail `70-evolution.md` §2 exists to create. "Temporary" is a
  property of who reads the file next, not of the moment it was written.
- evidence: 12 rule-change rounds have left an artifact under `drafts/` since
  2026-07-12 (`ls drafts/`), including the two still open on 2026-09-08. No
  round has yet been found to have written one to the scratchpad instead — the
  review trigger below is what would catch the first, and it has not fired.
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
- why: the two egress carriers are not symmetric in GATING, and the ungated one
  is the one the harness pushes toward routine use. A leak scan is a property of
  a CARRIER, not of this environment, for exactly as long as a second carrier
  can reach the same content without it.
- evidence: the interop egress path aborts the build on 6/6 planted secret
  classes (see the `interop` entry); the Artifact path has no equivalent, and no
  publish has been recorded from this environment. Structural, so there is
  nothing to measure yet — which is why the trigger is the FIRST publish.
- review-when: the first Artifact publish from this environment; or the
  default-private behaviour changes.

### External dispatch path — a second dispatch carrier with a one-way asymmetry
- current: LIVE. extdispatch is the only shell entry point to the external
  tiers; `hooks/extdispatch_entrypoint_guard.py` denies direct `opencode` and
  hand-rolled POSTs to the local serve API. Marker escape:
  `[user-approved-direct-opencode]`.
- why: this carrier crosses the trust boundary ONE WAY — work leaves under this
  machine's authority and nothing enforceable comes back. A control can only sit
  where the work is still a PATH, i.e. at the entry point; once the prompt is on
  the wire there is no place left to put one.
- evidence: `hooks/tests/test_extdispatch_entrypoint_guard.py` ALL PASS 41/41
  (16 MUST_DENY / 19 MUST_PASS / 3 fail-open / 2 coverage asserted over the
  hook's LIVE `ALLOWED_SUBCOMMANDS` and `POST_INDICATORS` / 1 isolation), plus 2
  KNOWN_GAPS counted in NEITHER total: `npx opencode run`, and a Python script
  that imports the HTTP helper — the honest limit below, kept as a named hole
  rather than folded into the pass count.
- what: `tools/extdispatch/` dispatches work to free external model tiers
  (opencode/Zen keyless, NVIDIA NIM keyed) over `opencode serve`. Path choice
  lives in `20-dispatch.md` §4a, redlines and disclosure in §4b, detail in
  `ops/references/external-dispatch.md`, environment facts in `environment.md`.
> **Share note.** `tools/extdispatch/` ships `partial` (`tools/share-manifest.toml`):
> only the `red-team/` acceptance scripts ship. The dispatcher itself
> (`extdispatch.py`, the allowlist/grants/breaker state, all telemetry) stays
> source-only — there is no shipped entry point to run; the six gates and the
> guard hook are described here as design, not as something this copy executes.
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
- current: three items — one RESOLVED by user ruling (the commit trailer), two
  standing and still cosmetic (the sweep's greps, the harness task-list nudge).
- why: an unrecorded cosmetic conflict is rediscovered as NEW by the next
  session, which spends a round re-deciding it — and one of the three
  (helpfully rewriting the sweep into Grep tool calls) would destroy the
  property that makes the sweep cheap. Three lines here, or a round each time.
- evidence: each item names its own source (Bash-tool text vs the sweep file;
  the harness trailer request vs `COMMIT-TEMPLATES.md`'s silence; mid-session
  reminders vs the ticket ledger). The trailer item closed on a user ruling
  2026-08-15; the other two have produced no wrong artifact since being written
  down, which is the condition for staying in this entry rather than becoming
  a rule of their own.
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
- why: (1) the cost is roughly FIVE TIMES the entire always-loaded
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
- re-read 2026-09-06 against build 2.1.257 (cc-delta reconcile; the carrier
  fired for the second time). The four load-bearing claims all STILL HOLD
  verbatim in the doc: Explore and Plan are the only subagents that omit
  CLAUDE.md and git status, and there is no per-agent setting to change that;
  the full CLAUDE.md hierarchy reaches every other subagent; auto memory never
  reaches a non-fork subagent; the main conversation reading Explore/Plan
  results with full context is the doc's own stated mitigation. No probe was
  spent — the entry rests on this doc page making a categorical claim, and the
  claim is unchanged, so two ~50K-token probes would re-test a constant.
  What DID change is that the list GREW, by four items this layer had never
  written down: (a) **preloaded skills** — an agent's `skills:` field puts the
  FULL text of a named skill into the worker, which is a lever aimed exactly at
  the cost problem this entry measures, and no definition in `agents/` uses it;
  (b) **sibling roster** — a system reminder listing `main` and every other
  NAMED agent as valid `SendMessage` targets, v2.1.206+, present only when the
  worker's tools include `SendMessage` and another agent has a name; (c)
  `includeGitInstructions`, which can remove the git-status snapshot; (d) fork
  subagents, which inherit the parent conversation instead of starting fresh.
  (a) and (b) are now noted in `20-dispatch.md` §roster; (c) and (d) change no
  rule here yet.
- history: the Explore exception sat unverified in `20-dispatch.md`'s roster
  table from birth; cost was never measured; the auto-memory gap was unknown
  until 2026-08-15; doc re-read 2026-09-06 (2.1.257) — claims unchanged, list
  grew by four
- review-when: a Claude Code upgrade changes the "what loads at startup" list —
  it is product behaviour, not contract, and the whole entry rests on one doc
  page plus two probes against build 2.1.226/2.1.229. Re-checking is CHEAP and
  is the doc page, not the probes: fetch `code.claude.com/docs/en/sub-agents`
  §"What loads at startup" and diff the bullet list against the four claims
  above. Spend a probe only if a claim moved.
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
- evidence 2026-09-08 (vocabulary rebuild, the phase-2 step the docstring
  promised): replayed the extractor over all 451 subagent transcripts on disk,
  so `verified` is decided by the real tool_result pairing rather than projected
  from the log's `commands` field. would_block 251/295 = 85.1% of the write
  population on the portable framework vocabulary, 178/295 = 60.3% once this
  environment's own verdict shapes are named (`controls.py`, `--selftest`,
  lint/audit/gate scripts, `diff`). 73 rescued rows were verified deliveries
  the instrument had no word for (L-044). `git status` / `grep` / `ls` were
  deliberately NOT added — 140 of the remaining 178 ran one, and counting them
  would drive the rate near zero and make the gate unfalsifiable; they are
  recorded in a separate `weak_evidence` field instead.
- history: born shadow 2026-08-11; enforcement not yet enabled; vocabulary
  rebuilt 2026-09-08 with a two-sided suite (5 must-rescue, 3 must-not,
  1 erroring result) — the false-positive measurement that gates enablement is
  still outstanding, and this narrows what it will be measuring
- evidence 2026-09-11 (shadow-hook eval for R-3, `outputs/shadow-hook-eval-2026-09-10.md`
  §3): 15 of the 283 `would_block ∧ dispatch` rows hand-judged — ~8/15 false,
  3 of them `dotnet build -c Release` + an acceptance script on real `.cs`
  edits (BenchRuns C3-0x) that `VERIFY_SHELL` had no word for; the rest
  Explore-type dispatches or scratch-only writes. `dotnet|msbuild|nunit|vstest`
  added the same day (a second vocabulary gap of the L-044 kind, found by
  reading rows). User ruling: KEEP-SHADOW with a date.
- review-when: **2026-09-24** — re-sample `would_block ∧ dispatch` rows written
  after 2026-09-11; if the hand-judged false share is still above ~30 %, RETIRE
  rather than run a third vocabulary pass (two passes that each moved the rate
  and still left it high mean the predicate, not the vocabulary, is wrong);
  if below, this is the enable decision. Or `SubagentStop`'s payload shape
  changes on a Claude Code upgrade, which is what `resolve_transcript()` works
  around.
- rollback: unregister from `settings.json`; commits 4239d27 / 44fe7e4

### context runway (`hooks/context_runway_shadow.py`)

**Status 2026-09-05: GRADUATED at the 300k band** (user ruling C/D3) — visible notice
asking for a handoff snapshot (`cache/handoff/<session>.md`, `hooks/handoff_snapshot.py`);
150k band stays shadow; second condition is now "no fresh snapshot", not "no phase-log".
Siblings: `compact_bookmark.py` PreCompact deny on auto (D1) — **DISABLED same day**: platform
controls #2/#3 showed 2.1.257 ignores the deny on the auto path (`DENY_ENABLED=False`, code kept);
`compact_loss_record.py` PostCompact recorder + `tools/compact-loss-audit/`. Auto-compact window
400k via `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (settings.json env; verified to override `--autocompact`).
Design + results: `references/compaction-pipeline-design.md` §7. Live-verified: the 300k notice
fired in a local session and a snapshot was written. Still unverified: Desktop honours the env;
auto summaries honour CLAUDE.md Compact Instructions — the first Desktop session past 400k decides.
- current: UserPromptSubmit, SHADOW ONLY — logs the notice it would emit,
  stdout stays empty even though this is one of only three events whose stdout
  Claude would actually see (`SessionStart`, `UserPromptSubmit`,
  `UserPromptExpansion`; verified against the hooks reference 2026-08-15).
- why: the failure is not context SIZE — it is reaching a compaction with
  nothing written down. Hence the CONJUNCTION and the shadow band below the
  graduated one: a notice that fires on size alone fires in most long sessions,
  and a notice that fires when there is nothing to do teaches the reader to
  dismiss the one that matters. What it buys is a snapshot, not a warning.
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

### xi card guard (`hooks/xi_card_guard.py`) — SHADOW
- current: PostToolUse on `Write|Edit`, shadow only (`ok` / `would-warn` /
  `would-deny` rows in `telemetry/xi-card-guard.jsonl`, never a deny). Born
  2026-08-30 for the cross-index M3 card grammar on stores whose
  `covers_state` is `final`.
- why: the M3 card grammar governs instances of a store's object class, and the
  hook's own docstring names "the rule-registry entry that names this hook" as
  its graduation gate — no such entry existed until 2026-09-11 (shadow-hook eval
  for R-3), so the gate was circular.
- evidence: 2026-09-11 — 2,449 rows / 100 sessions; the 90 would-deny/would-warn
  rows collapse to 15 distinct (path, verdict, reason) incidents — 50 rows are
  repeat-fire on two mid-draft files (every Edit re-trips the same verdict),
  4 are the guard's own fixtures, and every organic `bad-date` deny was a skill
  asset TEMPLATE. Fix shipped the same day: `TEMPLATE_RX` skips templates (a
  template is not an instance of the store's object class). Repeat-fire on WIP
  files is NOT fixed — enforcing today would deny every save of a draft.
  Source: `outputs/shadow-hook-eval-2026-09-10.md` §3.
- history: born 2026-08-30 shadow (PSM M3, D-2); 2026-09-11 entry added +
  template skip.
- review-when: **2026-09-24** — count distinct organic incidents (not rows)
  after 2026-09-11; graduate to `warn` only if the repeat-fire class has a
  carrier (e.g. one verdict per (session, path), or a `draft:` front-matter
  escape that leaves a mark) — otherwise stay shadow or retire. Also: a
  store's `covers_state` flips (the hook's own re-check trigger).
- rollback: unregister from `settings.json`; `XI_CARD_GUARD_LOG` redirects the log.

### intake match shadow (`hooks/intake_match_shadow.py`) — SHADOW
- current: UserPromptSubmit, shadow only — would-inject lesson cards
  (`intake.py match`) and logs `n_cards` + `prompt_len`, never the prompt
  text.
- why: a lesson card only helps if it is injected where the prompt would have
  hit the pitfall; whether `intake.py match` finds THAT prompt is a precision
  question no design argument settles, so it went in as shadow first.
- evidence: 2026-09-11 — 427 rows / 72 sessions, `n_cards > 0` on 86. The
  graduation metric its docstring names (precision on ~20 real prompts) is
  NOT computable from this log by design — the log has no prompt text — so
  the false-positive question is structurally open, not merely unmeasured.
  Cost: a second subprocess (`intake.py match`, ~100–300 ms) on EVERY prompt.
  Source: `outputs/shadow-hook-eval-2026-09-10.md` §3.
- history: born 2026-09-06 shadow; 2026-09-11 entry added (none existed).
- review-when: no date (user ruling 2026-09-11). Graduates only after a live
  hand-labelling pass: someone reads ~20 prompts beside the `ids` the shadow
  would have injected and records precision in THIS entry. If no one has done
  that by the time the per-prompt cost is questioned again, retire — a
  measurement nobody can take is not a measurement.
- rollback: unregister from `settings.json`; `INTAKE_MATCH_LOG` redirects the log.

### extdispatch route shadow (`hooks/extdispatch_route_shadow.py`) — SHADOW
- current: PreToolUse on `Agent|Workflow`, shadow only — `would_route`
  external|subagent per `20-dispatch.md` §4a, logged to
  `tools/extdispatch/route-shadow.jsonl` (NOT under `telemetry/`; the
  2026-09-10 audit misread that as "no telemetry").
- why: `20-dispatch.md` §4a only routes when it is READ; a session that reaches
  for the Agent tool without opening the dispatch layer never sees the external
  tier. The probe measures how often that happens before anyone is nagged.
- evidence: 2026-09-11 — 486 rows, `would_route` external 20 / subagent 466.
  The 20 external rows cluster into ~6 tasks (a multi-lane AssetVault check
  alone is 5 rows) and none matched the hook's own named false-positive shape
  (Explore/Plan). Rows carried NO `session_id`, so dedup by task was
  impossible; the field was added the same day. Source:
  `outputs/shadow-hook-eval-2026-09-10.md` §3.
- history: born 2026-08-15 shadow; 2026-09-11 entry added (the docstring
  pointed at a registry entry that did not exist) + `session_id` field.
- review-when: **2026-10-11** or ≥ 30 `would_route=external` rows WITH
  `session_id`, whichever first — compute tasks (distinct session_id), judge
  each; graduate to a notice ("§4a says this could go external") only if the
  task-level false share is low. Cheapest of the shadows (Agent-only matcher),
  so no cost pressure to retire early.
- rollback: unregister from `settings.json`.

### telemetry writers — `CLAUDE_TELEMETRY_DIR` + the suite-session allowlist (O-2)
- current: every telemetry writer under `hooks/` (deny_receipt.py + 21 hooks
  with their own LOG_PATH, plus `extdispatch_route_shadow`'s file under
  `tools/extdispatch/` and `report_fp.py`'s misfire log) resolves its
  directory as **per-hook override var > `CLAUDE_TELEMETRY_DIR` > default**.
  Production never sets the var; every suite sets it to a temp dir
  (`pol.py` sets it once for all ~25 suites it runs). Readers that want a
  CLEAN production number join against
  `tools/telemetry-framing/suite-sessions.json`: `literals` = synthetic
  session ids skipped in every file; `session_files` = real session id →
  the files its suite runs polluted, skipped only there. No `.jsonl` is
  ever edited; `framing.py` reports skipped rows as a separate count and
  `report_fp.py --rate` prints the rate with AND without them.
- why: user ruling 2026-09-11 (rules-debt audit O-2, "寫入端 redirect"):
  the deny stream could not be judged because suites fired real deny rows
  into production (secret-file-guard: 402 of 402 rows from 7 sessions;
  shell-transport-guard: 797 of 1,190 under `synthtest-transport`). By
  first principles the clean fix is at the WRITER (one env var, one
  precedence rule), not at every reader; the allowlist exists only for the
  rows already written.
- evidence: `outputs/telemetry-writers-inventory-2026-09-10.md` (writer
  census); `test_secret_file_guard.py` `telemetry_isolation_check()` is the
  two-sided control (positive: row lands under the temp dir; negative:
  production count unchanged); framing `controls.py` C-12..C-14 pin the
  per-file skip (literal skipped everywhere, real id skipped ONLY in its
  listed file, missing allowlist skips nothing). Verified 2026-09-11 with a
  before/after snapshot over 29 production files across 23 suites: no
  production file gained a suite row (rule-loads +3 were live
  InstructionsLoaded events from three other Desktop sessions).
- history: 2026-09-11 born. The drafting agent's first cut keyed the
  allowlist by SESSION only; measured the same day, every listed id was a
  real working session with rows in a dozen other files (6daa8834: 374 rows
  / 17 files), so the key became (session, file). The agent also leaked 16
  rows into `secret-file-guard.jsonl` (402 → 418) by running one control
  against the real hook — recorded as the 8th allowlist entry, scoped to
  that one file, not scrubbed.
- review-when: a hook gains a NEW telemetry file (it must resolve through
  the same precedence — grep `CLAUDE_TELEMETRY_DIR` in the new writer; the
  proof-of-life suite for that hook must set the var or its own override);
  `report_fp.py --rate` shows a hook whose two rates differ by more than
  ~10 points (then the allowlist is doing real work and the KNOWN LIMIT —
  a genuine deny by a listed session in a listed file is skipped too —
  needs a look); a suite is found writing to production again (the
  `telemetry_isolation_check` pattern goes into THAT suite).
> **Share note.** `tools/telemetry-framing/` (`framing.py`, `report_fp.py`) is
> source-only (excluded-by-decision, `tools/share-manifest.toml`). The hooks'
> raw `.jsonl` telemetry ships nowhere either; this entry documents the
> precedence rule as design, not a report this copy can run.
- rollback: the env var is additive — unset, every writer lands where it
  did before; delete `suite-sessions.json` and both readers count every row
  (C-14 pins that a missing list skips nothing).

### process ledger (`tools/process-ledger/`, general) + unattended run (`hooks/unattended_run.py`, branch)
Irreducible principle (user ruling 2026-09-05, design §0): process data written AT ORIGIN in distilled
form, read MECHANICALLY at every resumption, never washed. General branch, any session: decision charter
appends every choice+reason to `projects/<proj>/<session>.ledger.jsonl` (beside the transcript — the
one tree the daily mirror copies; cache/telemetry are cleanup targets); runway hook writes
`cache/handoff/current-session.json` each prompt and, at the 150k band (D3 AMENDED: canary only, no
checkpoint nag), plants the canary pair in `<session>.canary.json`; `compact_pointer.py` injects the
last 40 ledger rows after compaction; `run_audit.py` scores F1/F4/F6 + canary for any session, F3/F7
only under a manifest. Offline branch below adds the manifest and the two guards.
Live 2026-09-05 (design `references/long-run-probe-design.md`, tools `tools/process-ledger/`).
> **Share note.** `tools/process-ledger/` and `tools/compact-loss-audit/` are
> source-only (excluded-by-decision, `tools/share-manifest.toml`). The
> `ledger.py`/`run_audit.py`/`report.py` commands below do not ship; the
> hooks that write `*.ledger.jsonl` and `cache/handoff/*.json` do ship
> (`hooks/unattended_run.py` and siblings), so the DATA this describes is
> still produced — reading and summarising it is left to the adopter.
One manifest (`cache/handoff/<session>.run.json`, written when a prompt carries `[unattended-run]`;
every other field optional — scope defaults to cwd/**, canary auto-generated, deliverables/acceptance
model-derived via `ledger.py manifest` and marked `filled_by: model`, user ruling 2026-09-05 "no form-filling")
feeds two FAIL-class guards that rule only on determinable facts: PreToolUse Write/Edit outside
scope ∪ deliverables ∪ carriers → deny; Stop with a question-ending final message or no
`reports/*-run-<slug>.md` → block (max 2 per manifest). Ledger = project registers (borrowed) +
`ledger.py add` appendix; `report.py` skeleton; `run_audit.py` F1/F3/F4/F6/F7 + canary, advisory.
Controls: `tools/process-ledger/controls.py` ALL PASS + `tools/compact-loss-audit/hook_controls.py` 34/34 (positive + negative, isolated config dir).
Amended 2026-09-11 (user rulings A + C, L-080): the 150k keep text no longer opens
"Standing constraint for the rest of this session" and names the `<session>.canary.json` it
just wrote, so a reader can tell a local hook from injected text the way
`appdata_view_guard.py` already does — the old opening is the costume
`transcript_read_guard.py` removed in 2026-08-29, and a local session refused the plant
on exactly that reading. `run_audit.py` now splits a keep MISS by cause
(`keep_fail_reason` ∈ refused-by-model / not-carried / undetermined, with `refused`
evidence lines); a refusal also clears `summarizer_calibrated`, because it measures the
reader, not the summarizer. The scan is skipped when the token was carried — that is what
removes the measured false positives (2 of 3 hand-run flags). Base rate at the time:
60 planted sessions, 1 confirmed refusal, a LOWER bound (the ruler only sees a refusal
that echoes the token). Option B — widening `rules/hook-deny-message.md` to all 12
text-emitting hooks — declined by the user: no second symptom.
Not covered: shell-side writes, prose scope, mid-message questions, a silent refusal that
never quotes the token. review-when: Stop/PreToolUse
hook contract changes; any control FAIL; a second hook's injected text is refused (that is
option B's trigger). Tier-B compliance meter:
`tools/compact-loss-audit/notice_compliance.py` (first row: fable 1/1, denominator 1).
- current: LIVE on both branches — the general ledger in every session, the
  offline branch armed only by an `[unattended-run]` tag and disarmed by the
  user's next untagged prompt (the manifest stays, for the audit).
- why: what a compaction loses is not text but DECISIONS, and the summary that
  would preserve them is written by the same model that has already stopped
  remembering why. So the write happens AT ORIGIN, in the reader's own format,
  and the read is mechanical — a summariser cannot wash what it never rewrites
  (user ruling 2026-09-05). The offline guards are a branch of that ledger, not
  a second regime, which is why they rule only on determinable facts.
- evidence: `tools/process-ledger/controls.py` 31/31 and
  `tools/compact-loss-audit/hook_controls.py` 26/26, both with positive AND
  negative cases in an isolated config dir; live since 2026-09-05, with the
  300k notice and its snapshot verified end-to-end in session 3d1d5e42.

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
  2026-09-09 (F-8): `compact_bookmark`'s deferral NOTICE opened
  `[handoff-snapshot]` — the name of the module that composed the sentence, not
  of the hook that spoke, and nothing the reader could check. It now names the
  hook, and one receipt row is written and quoted by BOTH the deny text and the
  notice instead of two. Conditions unchanged; `hook_controls.py` 34/34.
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
> **Share note.** `tools/context-budget/` and `tools/glob-fitness.py` are
> source-only (excluded-by-decision, `tools/share-manifest.toml`). Substitute:
> grep `telemetry/rule-loads.jsonl` by hand for the same `session_start` /
> `path_glob_match` breakdown, and write a small recall/precision script
> against your own rule globs if you need the reachability check.
- rollback: `ops/environment.md` "Instruction-loading mechanics"

### advisory-output surfacing — ops-health check 13
- current (2026-09-10): **two scopes, deliberately asymmetric.** MAY be polled:
  any `outputs/**/*.md` that stamps ITSELF (opting in is what the stamp does),
  minus `outputs/skill-reviews/` — its disposition convention (D-032) already
  carries status. OWES a stamp: still only candidates files
  (`outputs/retrospectives/global-rule-candidates-*.md`) + experiment metrics
  (`outputs/experiments/*/metrics.md`), post-2026-08-16. The ruler is the
  convention's own vocabulary; identical status text inside one directory
  collapses to ONE row with a count; a stamp matching neither SPENT nor a
  waiting word is counted as unruleable in the same message, never silenced.
- why: handled-but-unannounced artifacts cost a full read to discover they
  are spent (user finding 2026-08-16). A maintained index file was rejected
  as a silently-rotting control; the surface is DERIVED from the files at
  each session start instead. Convention + entry command + cleanup semantics:
  `rules-usage-dict.md` §7 "advisory-output status line".
- evidence: two-sided fixture run 2026-08-16 — planted OPEN and missing-line
  fixtures both surfaced, an old-dated status-less fixture stayed silent
  (grandfathered), and the real corpus (3 artifacts, all spent) prints
  nothing. Widening measured BEFORE shipping, 2026-09-10: the corpus holds 40
  self-stamped files, and "not SPENT" alone would have printed **35 findings** —
  the alarm nobody reads, and the reason the original scope was narrow. With
  the vocabulary ruler + directory collapse the same corpus prints **6 rows for
  26 waiting files** (23 trigger-probe reports are two standing residuals, not
  23 offers) plus one unruleable count of 9. Suite `tools/ops-health-test/`
  71/71, five new `13-scope` cases: the motivating self-stamped file outside
  the owed globs (known-TRUE), an unstamped file outside them (known-FALSE),
  a stamped `skill-reviews/` file (known-FALSE), the x3 collapse (known-TRUE),
  and the regression guard for an unruleable-only run (known-TRUE — the count
  used to ride inside the OPEN message and vanished with it).
- history: 2026-08-16 born narrow (two globs, any non-SPENT line surfaces) →
  2026-09-10 widened to self-stamped opt-in with a vocabulary ruler, after a
  deferred-extraction record (`outputs/numberref-extraction-deferred-2026-09-10.md`)
  filed outside the globs proved invisible to the screen.
- review-when: the corpus's waiting rows exceed ~8 at a session start (the
  collapse is no longer paying and the ruler needs another axis), or the
  unruleable count stops falling (the convention's three words are not being
  adopted and the vocabulary, not the scan, is the thing to fix).
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
  `git show 483435f:archive/interop-refs-2026-08-11/`; `backups/2026-08-15/`
  `ops_health_nudge.py.pre-interop-check12`; removed rows →
  `git show 483435f:archive/2026-08-15-interop-targets-removed/README.md` (last commit `596cfc0`)

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
  `git show 483435f:archive/agents-2026-08-12/README.md` (the definitions: `git show 96c9525 -- agents/`)

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
  Brief + dispositions: a dated brief and outcome note under the source's
  outputs/ tree, which this repo does not ship.
- evidence: headless 1.4–1.5s WITH pixels vs pane 5s timeout with none; fresh
  pane born hidden/0×0/rAF-stalled; archive-wide 80 pane-screenshot calls vs
  853 DOM/state reads; hook suite 20/20 (`tools/ui-verify-test/`); live
  router check in-session (marker annotated `hidden`, route denial fired).
- history: detect-first CLAUDE.md line (2026-08-05) → PreToolUse gate
  (2026-08-08) → result-aware router + default inversion + durable runner
  (2026-08-16)
- review-when: `<browser_surfaces>` or the screenshot tool's error wording
  changes on an upgrade; the suite or `tools/ui-shot/doctor.mjs` fails; a
  probe marker stays `unknown` in live use (`tool_response` unpopulated). A
  user "I'm watching" is a temporary premise flip, not an edit trigger.
> **Share note.** `tools/ui-shot/` and `tools/ui-verify-test/` are source-only
> (excluded-by-decision, `tools/share-manifest.toml`); `hooks/ui_verify_guard.py`
> ships and still routes/denies. Substitute your own headless Playwright
> screenshot script for the durable runner; there is no shipped `doctor.mjs`
> to check it.
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
> **Share note.** `tools/playwright-mcp/` (the pinned install + its README) is
> source-only (excluded-by-decision, `tools/share-manifest.toml`). To
> reproduce this server, `npm install @playwright/mcp@0.0.79` yourself and
> register it in `~/.claude.json` the same way.
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
  Report a dated shell-command-error audit under the source's outputs/ tree,
  which this repo does not ship; `lessons.md` L-024.
- history: no routing rule existed before this entry (grep of CLAUDE.md,
  AGENTS.md, ops/*, skill-trigger-dict.md returned nothing) → born 2026-08-18
- review-when: Claude Code updates — run `tools/shell-audit/PROBES.md` P1/P2/P4
  (hand-run; they test the TOOL boundary and cannot be scripted) then
  `python tools/shell-audit/sweep.py --since <10d ago>`. If either Bash defect
  disappears, the routing argument weakens to a preference and this entry should
  be re-judged. Once the live transcripts age out (cleanupPeriodDays, ~30d), add
  `--root <MIRROR_ROOT>`.
> **Share note.** `tools/shell-audit/` is source-only (excluded-by-decision,
> `tools/share-manifest.toml`). On this copy, re-derive P1/P2/P4 by hand
> against your own harness and re-time the Write/Bash/PowerShell/Grep calls
> yourself; there is no shipped `sweep.py` to run.
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
  untouched 97.2%. Suite `tools/shell-transport-test/` **41/41 (2026-09-09;
  was 32/32 on 2026-08-23, 23/23 before that)**, two-sided (2 deny cases
  against 37 allow/notice — rule 3 adds M1–M8:
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
  2026-09-09 (finding F-2 of the AP-62 drain, raised by the guards-2 chip after
  its merge): sink membership stopped being an EXTENSION LIST. Two halves, and
  only the second set the scope — (a) the list omitted .rb/.go/.rs/.java/.lua,
  and (b) when nothing matched, the guard did not fall quiet: it asserted
  "Nothing here writes the result to a file or executes it as source, so any
  damage shows up in this turn's own output", which for `printf … > gen.rb` was
  FALSE. Scoped from (a) alone the repair reads as "extend the list", leaving
  the else-branch making the same untrue claim about the next unlisted
  extension; so `REDIRECT_ANY` now makes the redirect itself the predicate
  (closed over extensions, L-044) and the list only supplies the label, while
  the fall-through notice states what it CHECKED rather than a universal
  negative — a program invoked in the command can still write the bytes, and
  this guard cannot see that (AP-62: rule only on what you can determine).
  Suite 32 → 41; verified in both directions (pre-repair hook fails A7–A10 and
  A15; an over-broad `REDIRECT_ANY = re.compile(r">")` fails A11–A13 while
  A7–A10 stay green). The suite's own tally was folding the new rows into no
  class at all and printing a plausible 31-of-41 total; it now classifies by
  prefix and PRINTS whatever it cannot name.
  2026-09-09 (F-8): the notice TEXT moved its identity and its receipt onto the
  transport (`notice()`), and a read-elsewhere pointer was removed from the MSYS
  branch. No condition changed; suite still 41/41. See `AGENT_FACING_TEXT`.
- review-when: any Claude Code upgrade — `tools/shell-audit/PROBES.md` P1 and
  P3; if the collapse disappears the notice branch becomes noise, and if the
  ceiling moves `SIZE_LIMIT` is stale in the UNSAFE direction. Drift check:
  `python tools/shell-audit/invariants.py` prints the guard's deny/notice counts
  against the backtested 0.14% / 2.7%; a notice rate far above 2.7% of the Bash
  total (from `sweep.py`) means the sink patterns drifted. Discount the first
  ~90 telemetry rows — the test suite writes real entries.
> **Share note.** `tools/shell-audit/` is source-only (excluded-by-decision,
> `tools/share-manifest.toml`), so `invariants.py`'s drift check does not ship
> either. Substitute: read the hook's own deny/notice counters from
> `telemetry/shell-transport-guard.jsonl` and compare by hand against the
> 0.14%/2.7% rates above.
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
  2026-09-09 (F-8): identity and receipt moved onto the notice transport and the
  `Detail:` pointer dropped from `compose()`; no condition changed, suite 47/47.
  See `AGENT_FACING_TEXT`.
- review-when: (a) any Claude Code upgrade, or a move off Windows PowerShell
  5.1 — PowerShell 7.3+ ships `PSNativeCommandUseErrorActionPreference`, which
  makes direction (B) *stop being true*; if the shell changes, re-verify with
  `tools/shell-audit/PROBES.md` before trusting this annotation, because half of
  it would then be wrong in the confident direction. (b) `integrity-sweep.md`
  check 21 each sweep. (c) if the backtest's Edit or Bash rows accumulate fires
  while unregistered, the matcher decision reopens — that is the evidence it was
  deferred for, and it is measured whether or not anyone remembers to ask.
> **Share note.** `tools/shell-audit/` (PROBES.md) and `tools/ps-errorpref-*`
> are source-only (excluded-by-decision, `tools/share-manifest.toml`).
> Substitute: hand-test a `$ErrorActionPreference='Stop'` native call under
> your own PowerShell version and confirm which of directions (A)/(B) still
> holds.
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
  2026-09-09 (F-8): identity and receipt moved onto the notice transport (the
  log stem is named explicitly, since it is not the hook's name) and the
  `Detail:` pointer dropped; no condition changed, suite 51/51.
  See `AGENT_FACING_TEXT`.
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
> **Share note.** `tools/shell-audit/` and `tools/ps-pipeline-close-*` are
> source-only (excluded-by-decision, `tools/share-manifest.toml`). Substitute:
> re-check the alias table (`curl`/`wget`/`ls`/`sort`) by hand against
> whichever PowerShell version you run.
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
> **Share note.** `tools/shell-audit/invariants.py` is source-only
> (excluded-by-decision, `tools/share-manifest.toml`). Substitute:
> `git diff --stat` after a bulk write, or `git grep -Il $'\r'` for a quick
> CRLF-presence check, and confirm the count of touched files matches intent.
- rollback: delete `.gitattributes`; `core.autocrlf=true` resumes governing.
  Working-tree endings revert on the next checkout.

### graph rot watchdog — ops-health check 15 + daily task
- current: `tools/graph-snapshot/gs_watchdog.py` rebuilds the graph, compares
  live-surface broken-link count and premise metric against the previous run,
  and writes `out/watchdog-status.json` (+ a history jsonl). Carrier: the
  daily graph-watchdog scheduled task (12:30, same convention
  as the transcript mirror). Surfacing: `ops_health_nudge.py` check 15 reads
  the status file at session start (cwd == `~/.claude` only, report-only,
  fail-open) and fires on: status older than **3 days** (`WATCHDOG_STALE_DAYS`,
  provisional — daily task, so 3 tolerates two missed days), live count grown,
  or premise under **90%** (`gs_watchdog.PREMISE_FLOOR`, the design's
  pre-registered line).
> **Share note.** `tools/graph-snapshot/` is source-only (excluded-by-decision,
> `tools/share-manifest.toml`); `hooks/ops_health_nudge.py` check 15 ships and
> still runs, but the watchdog it reads (`gs_watchdog.py`, `gsnap.py`) does
> not, so the status file it expects will simply never appear on this copy.
- round 4 (2026-09-03, obsidian_Nathan D-24 — audit G-1 "MOC lag undetected"):
  the status file also carries `moc_lag_files` (content-defined lag from
  `gs_moc.lag_report`: would `emit-moc` change any `references/_moc` file for
  this graph); `evaluate()` JOINS its findings in priority order (build FAILED
  alone > links grew > MOC lags > premise floor) instead of letting the
  long-standing premise alarm shadow the rest; check 15 picks the remedy by
  finding (MOC lag → regenerate `baseline/build/verify` + `emit-moc` and commit
  `references/_moc`; otherwise harvest). Detection only — the task never writes
  a tracked file (user ruling: B/C/D rejected, see the design record
  `references/obsidian_Nathan-round4-design.md` §2.3). Task settings owed by
  the user (D-27): `StartWhenAvailable` + `ExecutionTimeLimit PT30M`.
- why: a knowledge graph rots by ADDITION. Every file added can break a link
  while every headline number stays plausible, so the rot is invisible both to
  the session that caused it and to the next one that reads the graph. Detection
  needs a remembered PREVIOUS run, which no session has — hence a daily task
  plus a session-start reader, and hence detection only: a watchdog that repairs
  its own subject is judging its own work.
- round 5 (2026-09-09, **the watchdog's own failed runs**): the status file is a
  COPY of "what the last run found", written after the work, so a run that dies
  leaves it holding the previous run's value and "ran and was fine" becomes
  indistinguishable from "did not finish". `gs_watchdog.py` now writes
  `out/watchdog-run.json` **before** it measures anything (`begin_run`) and
  closes it after (`end_run`, which also records a crash); a record still
  reading `state: "started"` is a run that never came back. Check 15 reads that
  record FIRST and, while it stands, reports the unfinished run instead of a
  status file describing an earlier one. The test is the record's **pid**, not
  its age — liveness is determinable, so a killed run is named with no waiting
  period, and a live pid is never accused. `WATCHDOG_RUN_LIMIT_MIN = 30` is only
  the backstop for a record with no pid or a host where liveness cannot be read;
  it is DERIVED from the task's own `ExecutionTimeLimit` (PT30M, verified on the
  registered task), not guessed. The carrier stopped appending
  `out/watchdog-task.log` (retired, kept as history): a line written after the
  python call could never record a run that did not return, and beside the run
  record it would be a second copy of one fact — the copy-census shape
  (`tools/copy-census/copies.py record()`). Closes copy-census row R12's
  `review-when`.
- round 5b (2026-09-09, **a kind with no branch**): `evaluate()` sets
  `remedy_kind` to `build` / `harvest` / `regenerate`, and check 15 branched on
  `regenerate` only — everything else took the harvest else. Measured line:
  `watchdog build FAILED (steps {'baseline': 0, 'build': 1, 'verify': 1}) — the
  graph, not the corpus, needs attention first — harvest due: read
  tools/graph-snapshot/out/integrity-report.md`, i.e. the reader was told the
  graph needs attention first and then sent to a report the failed build did
  not regenerate: the LAST GOOD build's output, read as today's. The `build`
  branch now says to re-run `gsnap.py baseline` / `build` / `verify` and see
  which step exits nonzero, and names the common non-defect cause — the corpus
  changing under the build, which `verify` reports as an INV-2 zero-touch
  violation (another session editing `~/.claude` while it ran). The FALLBACK
  arm (a status file written before `remedy_kind` existed) maps the same three
  kinds, so it cannot reach the wrong remedy either. The generalisable defect
  is not the missing sentence: reading a KIND instead of matching substrings
  fixed the wrong-remedy class only for the kinds enumerated, and an
  unenumerated kind fails into whichever branch happens to be the `else`.
  Controls: 2 new cases in `check15_remedy_cases()` (both known-TRUE, both
  FAIL against the pre-fix hook — measured 63/65 — and the group's known-FALSE
  is unchanged). **65/65 on 2026-09-09.**
- review-when: the graph-watchdog scheduled task's `ExecutionTimeLimit`
  changes (the 30-minute backstop is read off it); `gs_watchdog.evaluate()`
  gains a `remedy_kind` value (check 15 must gain the matching branch — the
  three kinds are a TABLE and the default is reserved for a kind this surface
  does not know, so an unenumerated one now SAYS SO in the session line instead
  of borrowing the harvest sentence; L-070).
- evidence: 2026-09-08 status `live_broken 0 / premise 93.9% / moc_lag 0`
  (`out/watchdog-status.json`, generated from d88ebb2). The check has earned its
  place twice on its own numbers: round 4's G-1 audit found MOC lag going
  undetected because the long-standing premise alarm shadowed it (fixed by the
  priority JOIN above), and the 2026-09-08 sweep found the live-surface count
  itself inflated by template text the parser had no word for — 15 → 5 once it
  learned the class, and the 5 that survived were real. Round 5's own measured
  case: `LastRunTime 2026-09-09 14:49:58`, `LastTaskResult 0xC000013A`
  (STATUS_CONTROL_C_EXIT), `out/MANIFEST.sha256.pre` and `out/gitstatus.pre.txt`
  written 14:50, no log line, and `watchdog-status.json` still reporting the
  previous day's all-clear — the session-start line was silent while the
  watchdog was dead. Controls: 10 hermetic cases in
  `tools/ops-health-test/test_ops_health_nudge.py` (5 known-TRUE, 5 known-FALSE;
  all 5 known-TRUE fail against the pre-round hook, which is what says they
  measure the new arm) plus a live end-to-end pair,
  `tools/graph-snapshot/tests/live_run_record_control.py` — a real run really
  killed, then one run to completion. **2/2 and 62/62 on 2026-09-09.**

### copy census — ops-health check 18 + tools/copy-census
- current: `tools/copy-census/rows.toml` declares every item this machine holds
  in more than one place inside the two roots ruled in S-3 (`~/.claude`,
  the operator's Obsidian vault; the work tree excluded by the user 2026-09-09), each with
  a verdict (`guard` / `regenerate` / `guarded-elsewhere` / `frozen` / `mount` /
  `distinct`), a per-row equality predicate, and the detector that would fire.
  Carrier `ClaudeCopyCensus-Daily` (13:10 daily **and** at logon) runs
  `version-census --refresh --write-note` first — regeneration is the fix,
  comparison is only for what cannot be regenerated (S-1) — then
  `copies.py --check --record`. Surfacing: `ops_health_nudge.py` check 18 reads
  ONE small JSON (cwd == `~/.claude`, report-only, fail-open); missing record or
  older than **3 days** (`COPY_CENSUS_STALE_DAYS`, provisional — same
  two-missed-days argument as check 15) fires; a host without the tool is silent
  by design. Test seam: `OPS_NUDGE_COPY_CENSUS_STATUS`.
> **Share note.** `tools/copy-census/` (and `version-census`) is source-only
> (excluded-by-decision, `tools/share-manifest.toml`); check 18 ships and stays
> silent by design on a host without the tool — which this copy is, until you
> build or adapt your own duplicate-tracking census.
- why: `version-census` shipped 2026-09-09 writing two status notes with nothing
  comparing them (V-18 / SG-6) — a tool whose whole case was "a rule nobody
  checks is worse than no rule" had produced an unguarded copy of its own. The
  sweep that followed found the disease is rare (ONE diverging cross-root pair,
  because exactly one script writes into both roots) and the false positives are
  not: an uncalibrated copy detector reported 22 junction-mounted files as
  duplicated across both roots, consistently and wrongly. Hence the four silent
  verdicts: on this data, being SPECIFICALLY quiet is most of the work.
- landed drafts hold no artifacts (user ruling 2026-09-09): asked what should
  happen to a proposal folder whose change has landed, the user answered with a
  criterion — 「重點在於未來沒有任何機會導致誤判或誤讀，做最乾淨的選擇」— and
  the cleanest reading of `70-evolution.md` §2 is that its lifecycle already
  says this: artifacts stay in `drafts/` on the **rejected/superseded** branch
  only; on the applied branch the commit carries the event and this registry
  carries the standing reason, so a surviving copy has no assigned job and one
  assigned risk. 12 copies in 3 folders were removed 2026-09-09; the 8
  `APPLY.md` and the `BRIEF`/`CIM`/`PIM` design record stay, because they are
  the argument, not a copy of anything live. Row R5 (`drafts/*`, `frozen`) was
  retired with them, so a copy appearing there is now an UNKNOWN-COPY finding
  rather than declared silence — an in-flight proposal is visible, and so is a
  close-out that forgot to clear its artifacts. Measured cost of the old
  silence: on 2026-08-28 pytest byte-compiled the copy of
  `test_ui_verify_guard.py` in `drafts/2026-08-16-pane-pixel-route/`, 12 days
  after it landed and 33 diff lines behind the live suite, while that folder's
  `APPLY.md` still read "pending user ruling" — for 24 days.
- review-when: either root moves (`scan.py` `CLAUDE_HOME` / `VAULT_ROOT`);
  `version-census` stops writing two notes; Task Scheduler stops being this
  machine's scheduled carrier; a second script starts writing into both roots
  (today `census.py:335` `write_notes()` is the only one); **an in-flight
  proposal's UNKNOWN-COPY line is judged noise rather than a to-do** — that is
  the one cost of retiring R5 and the trigger to reconsider it.

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
> **Share note.** `tools/claude-session-transcript-mirror.ps1` is source-only
> (excluded-by-decision, `tools/share-manifest.toml`); `hooks/ops_health_nudge.py`
> check 17 ships and still reads the marker, so bring your own copy job (or
> adapt this one) if you want the marker it is looking for to ever exist.
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
  **2026-09-06, first harvest actually run against the number** (commit
  `633f1fa`): of the 9 live-surface broken links, **zero were a missing
  file**. Four resolver classes, each a shape the corpus writes routinely and
  the instrument had no word for — a path AT A COMMIT (`git show <sha>:path`),
  a suffix past the extension (`x.py.pre-check15`, which also made a DELETED
  `settings.json.pre-E2` resolve clean against the live file — the same bug
  certifying a rollback pointer that is gone), a dated `skills/*/evals/` run
  record that must never be edited, and an evidence line declaring its own
  root (a `locator:` line built from an absolute private path). Fixed in the resolver, not in the
  corpus: 9 → 0, total broken 324 → 308, smoke checks 77 → 92. The report's
  three calibration probes had all PASSED throughout — they test whether the
  gate can say yes and no, not whether its object vocabulary covers the
  corpus (`ops/lessons.md` L-033 hit 2). The live/historical predicate was
  also in THREE copies (this file's consumer, `gs_moc.py`, `gs_watchdog.py`)
  under a comment claiming one; collapsed into
  `gs_watchdog.is_live_surface()`, which is where `FROZEN_SEGMENTS` could
  then land once.
  The **premise metric was deliberately not touched**: 89.2% → 89.6%, still
  REFUTED against the pre-registered ≥90% floor. The floor is a claim about
  the corpus; the resolver fix is a claim about the ruler; they were kept
  separable on purpose, and the fact that the fix does not cross the floor is
  the evidence that they are.
  **2026-09-06, second ruling the same day — the ALARM CHANNEL** (user
  ruling; `gs_watchdog.evaluate`): the channel carries the live-surface COUNT,
  its growth, MOC lag and a failed build. It no longer carries the premise
  metric. Reason: after the resolver fix, 308 of the metric's 308 broken links
  sit in historical records where a dead link is CORRECT (a change log naming
  a file that existed then), so the ≥90% floor has no path to being met short
  of rewriting history — it alarmed every session forever, and it shared its
  message with `live_broken`, the number that does mean something. The metric
  is still measured, the verdict is still **REFUTED** in the integrity report
  (where an unmet design premise belongs), and `premise_under_floor` +
  `premise_floor_pct` are in the status file so re-arming is one edit. **The
  pre-registered number and its floor were NOT redefined** — only the channel
  changed. Second change in the same commit: the count now fires at any
  nonzero LEVEL, not only on growth. Growth alone sufficed while the number
  had no reachable zero; it reached 0 the same day, so a count sitting at 3
  run after run (delta 0) would otherwise have gone quiet. Third: the hook's
  remedy branch reads `remedy_kind` from the payload instead of matching
  substrings of a sentence the watchdog owns — the old arm keyed on the
  literal "broken links" and would have picked the wrong remedy the moment
  the wording became "3 live-surface broken link(s)"; the substring arm
  survives as the fallback for an older status file, with that exact
  regression as a test case.
- review-when: the daily task is removed or the machine's scheduling story
  changes; graph-snapshot's covers change enough that "live surface" means
  something else; the premise floor is re-ruled. **Also: any session that
  finds a live-surface finding to be a false positive** — the number's whole
  value is that 0 means 0, and one standing false positive turns the harvest
  into noise. **And: a rule or lesson file acquiring a prose note telling a
  human not to let a tool "fix" something** — that note names a class the tool
  cannot see and belongs in the tool's fixtures instead (L-033 hit 2).
  **And (armed 2026-09-06): the premise metric crossing back above its floor,
  or a session wanting it to alarm again** — the measurement never stopped, so
  re-arming is one condition in `evaluate()`, and the status file already
  carries both the rate and the verdict.
- rollback: `backups/2026-08-26/ops_health_nudge.py.pre-check15`;
  delete the graph-watchdog scheduled task (`schtasks /Delete /TN`, name from
  your own Task Scheduler); delete
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
> **Share note.** `tools/cc-delta/` is source-only (excluded-by-decision,
> `tools/share-manifest.toml`); check 16 ships and still stamps the mismatch,
> but producing the actual delta is left to you — read the CLI's own
> changelog for the version range by hand.
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

### `ENTRY_SCHEMA` — one field set for every classification/routing entry + per-principle asset properties
- current: every entry on the 14 classifying/routing surfaces carries `id / owner /
  status / kind / detect` (+ `trigger / on-fire` when `kind: routing`) in its
  surface's OWN spelling; a field a surface cannot hold lives in the carrier the
  adapter table names (`ops/references/entry-schema.md` §4 — 14/14 rows, honest
  "not representable" column). Each PHILOSOPHY §一 belief (`PH-n`) and each global
  CLAUDE.md engineering-judgement bullet (cited by its bold trigger phrase, never
  by position) resolves into asset properties `AP-nn`, each with a `detect:` line
  (`ops/references/principle-design-guide.md`). Enforced subset
  `tools/entry-schema-lint/` ES-1..ES-8: legacy artifacts (first commit on or
  before 2026-09-08) WARN with a count that must not rise, born-after FAIL, lost
  anchor exit 2; wired as integrity-sweep check 29 and `config-self-audit` §4
  (`--path`). No parser changed (INV-1); no new hook, no CLAUDE.md prose (INV-6);
  `AP`/`ES`/`PH` registered in `LABEL-REGISTRY.md` §2 the same commit (INV-7).
> **Share note.** `tools/entry-schema-lint/` is source-only (excluded-by-decision,
> `tools/share-manifest.toml`); integrity-sweep check 29 cites it as a dead
> pointer on this copy. `ops/references/entry-schema.md` (the adapter table
> ES-1..ES-8 checks against) ships and stays useful as a manual checklist.
- why: user 2026-09-08 — CLAUDE.md and PHILOSOPHY complement each other, but the
  principles are forgotten at the layer where the small artifact (skill, hook,
  rules file, project CLAUDE.md, routing row) is built, and every such surface
  spelled its own classification vocabulary — 14 surfaces, no shared protocol,
  interaction loss at every boundary. L-059 (SSLD T44: seven page builders, no
  shared shell, a ruling bound to a tool) is the measured case. Design record:
  `drafts/2026-09-08-principle-design-guide/` (BRIEF / CIM / PIM / APPLY).
- evidence: a local session (ledger rows 1–11);
  born-RED baseline 0 FAIL / 59 WARN on `~/.claude` (ES-1 24 · ES-2 17 · ES-3 6
  · ES-5 11 · ES-8 1) and 16 ES-7 WARN / 6 independent shells on SSLD; controls
  32/32 two-sided, including the `selfdecl` false-negative the first ES-7 cut had.
- history: 2026-09-08 born (this entry); the 26-hook `STATUS:` backfill and the
  CLAUDE.md pointer were proposed as 🔴 diffs, not applied. 2026-09-08 R1 applied
  (user ruling, recommended value): CLAUDE.md index line now points at the
  principle guide (22,915 B), rationale sentence sunk into `CLAUDE_MD_CAP` why.
  2026-09-08 R2 applied (user ruling, recommended value): 24 registered hooks
  carry `STATUS: LIVE since <first-commit date> (backfilled …)`, the three
  `*_shadow.py` carry `STATUS: SHADOW … graduation criterion`; ES-1 24 → 0,
  total 59 → 35 WARN; docstrings only, py_compile clean, hook suites unchanged.
  2026-09-08 R3 applied (user ruling, recommended value): model3d-pipeline
  SKILL.md:49 subject is now the figure class, not the pipeline (RD-1); ES-8
  1 → 0, total 35 → 34 WARN. All three red items closed the day after birth.
  2026-09-08 evening (a local session): ES-2/ES-3 rebuilt off POSITION
  predicates → 16 WARN; the three uncovered hooks gained control suites and
  ES-2 went 5 → 0; the 11 ES-5 registry entries got their `why:`/`evidence:`
  written, one judgement each → **0 FAIL / 0 WARN, the born-RED baseline closed
  in one day**. Consequence, applied the same commit: ES-1..ES-5 added to
  `SEVERITY_PROMOTED` under a SECOND named trigger recorded in `lint.py` — a
  class whose legacy count reaches 0 promotes to FAIL, because "WARN = legacy
  debt" then describes nothing and the next WARN would be a regression printed
  quietly. ES-7/ES-8 stay WARN (a heuristic may never rule FAIL). The same pass
  found the promotion had been INERT for ES-1's graduation case, ES-3, ES-4 and
  ES-5: those four findings hardcoded `"WARN"` instead of calling
  `severity_for`, so the trigger this entry names could not have fired — now
  wired, with C-05/C-05b/C-05c as its two-sided control (controls 39 → 41).
  That finding was folded back into the belief rather than left as an anecdote:
  **AP-63a** in `principle-design-guide.md` extends AP-63 one level in — a
  control suite EXERCISES every escalation lever the artifact documents (a
  promotion set, a severity flag, a shadow/live switch, a `[marker]` escape),
  because a lever nothing pulls is indistinguishable from a wired one, and it
  is worse than an undocumented one: three files cite it and every reader
  trusts it.
- review-when: (a) a 15th classifying surface appears → its adapter row lands
  before it ships; (b) the SKILL.md loader accepts extra frontmatter keys →
  surface 14's carrier moves back into the frontmatter; (c) a WARN class rises
  for two consecutive sweeps, OR a still-WARN class reaches 0 →
  `SEVERITY_PROMOTED` in `lint.py` (only ES-7/ES-8 remain eligible, and both are
  heuristics, so the honest answer there may be "never"); (d) three sweeps
  with born-after hooks still missing `STATUS:` → the P2/P3 carriers do not reach
  authors; a path-scoped `rules/` stub is the named upgrade, not the default.
- rollback: restore `backups/2026-09-08/principle-design-guide/` (8 files); delete
  `ops/references/entry-schema.md`, `ops/references/principle-design-guide.md`,
  `tools/entry-schema-lint/`; remove sweep check 29 and the three LABEL rows.

### `NO_SILENT_FAIL` — a mechanism must survive its own corpus growing
- current: `PHILOSOPHY.md` §一.11 states the belief; `ops/references/principle-design-guide.md`
  PH-11 resolves it into four asset properties. AP-61 extension clause (the growth
  rule is in the artifact's own text). AP-62 enumerated, CLOSED object classes — an
  input matching no declared class is reported `undetermined` and excluded from every
  verdict count, never folded into the nearest class; the instrument's `controls.py`
  carries one specimen per declared class PLUS one deliberately unclassifiable input.
  AP-63 a RECURRING proof-of-life that EXECUTES the control suite — being named in
  the sweep is not being run by it. AP-64 a failing verdict prints the repair site
  (`file:line` or a runnable command), not only the symptom. PH-11 governs SURVIVAL;
  PH-2 / AP-43 govern BIRTH.
- why: user 2026-09-08 — 「未來即使擴充也有明示的原則，不會靜默壞，或者要好維修，
  且也有固定概念」. A birth-only calibration proves the instrument was right on the day
  it shipped; nothing re-runs it when the corpus grows a class its author never saw, so
  the instrument does not break — it silently stops applying while still being trusted.
  Two of the most-hit CLAUDE.md engineering rules (L-044 vocabulary coverage, L-047
  position-free predicates) had no parent belief in PHILOSOPHY §一 before this entry,
  which is itself the signal the belief was missing rather than duplicated.
- evidence: the 2026-09-08 debt sweep, three independent measurements. (a) graph
  broken-link resolver: 15 live-surface hits → 9 placeholder tokens (`L-nnn.md`,
  `L-999.md`, `references/x.md`), 1 stale-graph artifact, 4 frozen records, 1
  actionable = 6.7% precision; the 0→9 delta of 2026-09-07 is entirely the
  closeout-intake lessons split introducing the placeholder idiom. (b) `shell-audit`
  line-ending invariant: 31 MIXED tracked files, 31/31 binary (PNG), 0 text — 0%
  precision, and its printed remedy ("use Edit, not `cat >>`") cannot apply to a PNG.
  (c) 17 of 29 registered hooks named in no sweep check; 8 have no behavioural
  verification anywhere, and `hooks/unattended_run.py` was silently fail-open on a
  missing import until a manual audit found it (`reports/2026-09-08-hooks-env-tools-
  consolidation.md` §2).
- history: 2026-09-08 born (this entry) — belief + AP-61..AP-64 recorded first, then
  the two false-positive instruments repaired against AP-62 and `NUDGE_CAP` moved to
  a position-free form against AP-45. Same day, AP-63 shipped its mechanism:
  `tools/hook-proof-of-life/pol.py` + sweep check 31 EXECUTE each registered hook's
  declared suite, the declaration living in the hook's own docstring
  (`Proof-of-life: \`python …\``).
> **Share note.** `tools/hook-proof-of-life/` and `tools/class-closure/` are
> source-only (excluded-by-decision, `tools/share-manifest.toml`); checks 31
> and 33 cite them as dead pointers on this copy. Each shipped hook's own test
> file (named in its docstring, where one ships) still runs stand-alone.
  Coverage went 3 → 19 executable of 29 by
  backfilling declarations onto suites that ALREADY EXISTED — the sixteen were
  never untested, only unrun, which is the belief's whole claim in one number.
  `detect:` for AP-63 upgraded from candidate to check 31 in the same commit.
  Also 2026-09-08: `gc.reflogExpire` / `gc.reflogExpireUnreachable` set to `never`
  on this checkout after sweep check 19's date baseline was found wrong — it had
  counted only the 90-day knob and forgotten the 30-day unreachable one, so the
  real undo window on a repo with NO REMOTE was 29 days, not the assumed 64. The
  check's predicate is now the config value, not a date.
  2026-09-09 (user: 「AP62可以先建」): AP-62's unclassifiable-input half gained a
  mechanism — `tools/class-closure/closure.py` + sweep check 33 enumerate every
  control suite (31 on the day, through pol.py's declaration grammar) and report the
  ones that never assert `undetermined`: 3 carry / 28 lack, the 28 recorded BY NAME as
  the legacy set, FAIL for any suite born without the case, WARN for the legacy ones,
  promotion when the set empties. The per-class-specimen half stays audit — the check
  cannot know an instrument's class list, and says so.
  2026-09-09, same day, PROMOTED (user: 「都走建議值」): the 28-name legacy set was
  drained to 0 and `LEGACY_LACKING` plus the WARN branch were deleted, so a lacking
  suite is FAIL wherever it came from — the second class to be born-RED and closed
  within a day, after ES-1..ES-5. Shape: the 11 rule-tier suites by this session
  (OPS hard rule 6 — a subagent may not write `hooks/`), the other 17 by four
  dispatched slices, each in its own worktree on its own branch, merged and re-run
  in the canonical tree by the dispatcher; `closure.py` stayed single-writer so the
  set literal never took a 4-way conflict and the register's author was never its
  own verifier. `controls.py` 24 → 22 cases: four legacy/WARN cases deleted, two
  no-downgrade regression cases added so the WARN branch cannot silently return.
  What the drain found is the entry's strongest evidence, and none of it was visible
  from a count: five hooks FOLDED an unclassifiable input into a real verdict
  (`browser_pane_scope_guard` recorded a non-string url as a navigation that
  happened; `fieldwork_threshold_notice` counted one as a read file, walking a
  session toward its own threshold), and ten of thirty registered hooks CRASHED on a
  payload that parses but is not an object while their docstrings claimed fail-open.
  Two of this round's own new cases were controls that could not fail (asserting a
  decision the fold answers identically) and were rewritten to assert the path the
  decision carries — a control that never fails is not a control.
- review-when: (a) a third instrument is found reporting ≥50% false positives from a
  corpus class it cannot name → AP-62's remaining audit half (one specimen per declared
  class) is promoted to a lint; (b) ES-9 (AP-61) ships → AP-61's `detect: none (candidate: …)` is upgraded
  in the same commit; (c) a PHILOSOPHY §一.12 is added → `principle-design-guide.md`
  line 17's belief count moves with it (sweep check 17 reads prose counts); (d) CONSUMED
  2026-09-08 — check 31's `uncovered` reached 0 and its WARN became FAIL that day;
  (e) CONSUMED 2026-09-09 — check 33's `LEGACY_LACKING` reached 0 and the set plus the
  WARN branch were deleted the same day; (f) a suite is added to a NEW exemption set in
  either check, under any name → that is this belief failing in the way it warns about
  (an instrument that silently stops applying while still being trusted), and the set
  is deleted rather than grown.
- rollback: remove PHILOSOPHY §一.11 and the PH-11 section; restore
  `principle-design-guide.md` line 17 to "ten beliefs"; the instrument repairs stand
  on their own measured false-positive rates and are not rolled back with the belief.

### `WORKTREE_SCOPE` — a linked worktree of ~/.claude announces itself and cannot strand state
- current: `hooks/worktree_scope_guard.py` (SessionStart, every session; PreToolUse
  `Write|Edit|NotebookEdit|Bash|PowerShell`). In a linked worktree it prints the
  worktree, branch, canonical checkout, unmerged-commit count and the ignored state
  dirs present; in the canonical tree it prints the linked worktrees that still
  exist with +unmerged / dirty / ignored-state. It DENIES a Write/Edit/NotebookEdit
  whose target git ignores inside a linked worktree of `~/.claude` (names the
  canonical target; opt-in file `<gitdir>/worktree-scope-allow`), and a
  relative-path `gsnap.py build|verify|emit-moc|bench` / `xi.py emit|register|union`
  run from such a worktree (absolute canonical path, an earlier `cd <canonical>`,
  or the marker `[worktree-ok]` passes). Other repos' worktrees are announce-only.
  Asset properties stated in `ops/references/shared-tree-git.md` §1a; sweep check 30.
- why: user 2026-09-08 (repeat since 2026-08-30; "handle it at the source") — the Desktop app
  places every parallel session on a git repo in a pooled worktree before the
  first prompt (docs verified 2026-09-08; no per-repo off switch ships), so the
  coupling-class routing in shared-tree-git §1 never gets to fire, and from inside
  a worktree the copy is indistinguishable from the canonical tree. Sessions then
  hand out `~/.claude/references/...` paths that resolve only on an unmerged
  branch, build gitignored state (graph-snapshot `out/`) that never travels, and
  the canonical tree reports "MOC lags" against a graph that exists two folders
  away. A 2026-09-02 cleanup round did not stop it because it cleaned the
  instances, not the class.
- evidence: a local session (ledger rows 3–4; report
  `reports/2026-09-08-worktree-scope-root-cause.md`): 10 `~/.claude` sessions in
  linked worktrees 2026-08-27 → 09-08 (session archive, cwd filter); the Desktop
  pool registry names 7 worktrees across 3 repos with `leasedBy`/`pooledAt`; the
  2026-09-08 handoff card existed only on `claude/intelligent-brahmagupta-6799e8`
  until this session ff-merged it; `tools/graph-snapshot/out/` dated 09-08 03:55 in
  a worktree vs 09-07 12:30 in the home; two whole-repo worktrees had been created
  inside `skills/*/` (residue archived `archive/2026-09-08-worktree-residue/`);
  16 `projects/<worktree-slug>/` transcript dirs across five repos. Selftest
  two-sided on real temp repos (`--selftest`, ALL PASS), hook-deny-lint FAIL 0.
- history: 2026-09-08 born; the five merged clean worktrees removed and the eight
  merged `claude/*` branches deleted the same day (one empty dir held by a file
  watcher, `.claude/worktrees/modest-pasteur-ff4097`, clears on its own).
  2026-09-09 check-up (a local session): selftest 27/27, canonical-tree
  SessionStart silent, no linked worktree; the empty dir had NOT cleared on its
  own and was removed by hand; the two other repos' merged Desktop worktrees
  (FlashGrab `happy-poincare-d632d8` — content in main by `git cherry`, branch
  needed `-D`; DIT `peaceful-heyrovsky-090c2c`) removed with their branches on
  the user's ruling; review-when (a) closed as "Desktop option reads
  `cc-landing-worktree-enabled: false` and three consecutive ~/.claude sessions
  since 09-08 opened in the canonical tree" — the Desktop pool registry still
  lists the removed leases (app-owned, its GC reconciles).
  2026-09-09 later (a local session, after the AP-62 drain's four chip
  worktrees): the "empty dir held by a file watcher, clears on its own" story
  in the line above was **refuted a second time and replaced by a measurement**.
  Removing four worktrees printed `error: failed to delete <path>: Permission
  denied` — a hard error AFTER git had already emptied each tree and dropped
  its own admin directory — and the holder is the **cwd of the chip session
  process**, not a watcher, so it clears when that session closes. The ritual
  in `shared-tree-git.md` §1a now says to judge removal by `git worktree list`
  and not by the exit code (L-063). The bigger finding is what the guard did in
  that state: `git worktree list` named nothing, so the canonical announce
  returned "" while four worktree-shaped directories sat in the pool, and both
  readings available to a person running `ls` were wrong. So the hook gained a
  RESIDUE clause — a pool directory git does not name is announced as residue,
  empty or `(NOT empty)` — with `POOL_DIRS` as its single edit point and
  R-1..R-7 as its two-sided control (selftest 30 → **37**, inverted at
  `POOL_DIRS = ()` and observed failing R-1..R-5 before shipping). Also added
  to §1a: when N dispatched sessions share one REGISTER file, that register has
  a single writer who is not any executor — the drain's `closure.py`.
- review-when: (a) the Desktop app ships a per-repo "no worktree" switch → set it
  for `~/.claude` and demote the deny half to announce; (b) worktrees move off
  `<repo>/.claude/worktrees` → the announcement still resolves through the `.git`
  file, but re-run the selftest; (c) a third false positive in the hook's log →
  narrow the condition (STATE_DIRS prefix AND ignored); (d) a session is again
  found handing out a non-resolving path with the announcement present in its
  transcript → the carrier is wrong, not the fact — promote to a UserPromptSubmit
  reminder, not a longer announcement; (e) a second worktree pool location
  appears (another host app, or a hand-placed one) → add it to `POOL_DIRS`, the
  single edit point, and extend R-1/R-6; (f) `git worktree remove` stops
  leaving the directory behind on Windows → R-5's shape becomes unreachable in
  practice, but one clean run is not evidence to delete the clause — it needs a
  git release note or a reproduced failure to remove.
- rollback: remove the two settings.json entries and the hook file; keep §1a and
  this entry with `status: retired` — the measured cost stands whether or not the
  mechanism does.

### `DISPATCH_COMMIT_PATHSPEC` — a main-loop commit while a dispatched agent is outstanding is scoped by pathspec
- current: `hooks/dispatch_commit_notice.py` (PreToolUse `Agent|Workflow` records a
  dispatch per session in `cache/dispatch-commit-notice/<session>.json`;
  SubagentStop pops one; PreToolUse `Bash|PowerShell` injects a NOTICE via
  `additionalContext` when a `git commit` without `-- <pathspec>` and without
  the marker `[dispatch-ok]` is about to run with a dispatch younger than 4 h
  outstanding). Never blocks. Asset property stated in
  `ops/references/shared-tree-git.md` §4 (the "dispatched agent is a party in
  the SAME index" paragraph); lesson L-061.
- why: commit `a272c58` (2026-09-08, a local session): the main loop ran a bare
  `git commit -m` while a sonnet work-card agent had four files staged; the
  files landed under the wrong subject and the agent reported "another session
  took the index". The retrospective recorded the fix as a sentence in its
  "next" list — the recall-only carrier the same day's PH-11 work was
  replacing. The dispatcher lacked one fact ("an agent of yours is still
  running") at one moment (a commit reads the shared index); the hook supplies
  exactly that. NOTICE not DENY: the reader is the committing LLM
  (gate-severity-by-consumer, user ruling 2026-08-26), and a positional
  pathspec without `--` is invisible to the matcher, so a deny would misfire on
  a correct command.
- evidence: retrospective `outputs/retrospectives/retrospective-claude-config-debt-
  sweep-2026-09-08.md` 「下半場我自己犯的錯」 2; the sonnet agent's own report in
  that local session. Selftest `--selftest` two-sided (bare commit / `-a` /
  `--amend` / `git -C` form → notice; `-- <paths>` / marker / no dispatch /
  other session / TTL-expired / non-git → silent; SubagentStop FIFO; subprocess
  stdin path incl. garbage); hook-deny-lint clean (no deny text).
- history: 2026-09-09 born (a local session, user authorization "缺少的儀器或針對
  原則的防禦建置" in the same message that ruled the clean-up).
- review-when: (a) Claude Code gives every subagent its own worktree/index →
  retire, keep §4 as history; (b) notices appear with no dispatch in the
  transcript (SubagentStop drift) → shorten TTL, do not widen the marker;
  (c) the Agent/Workflow tool is renamed → matcher + `DISPATCH_TOOLS`; (d) a
  second swallowed-stage incident with the notice present in the transcript →
  promote to DENY with a deny_receipt; (e) three observed false positives →
  ignore read-only subagent types (Explore, code-reviewer, security-engineer)
  rather than widen the escape.
- rollback: remove the three settings.json entries and the hook file; keep the
  §4 paragraph and this entry with `status: retired`.
- history: 2026-09-09 (F-8) its notice text gained the hook's self-identification
  and a receipt sentence — the notice surface is ruled on now (`AGENT_FACING_TEXT`
  below); no condition changed, `--selftest` still 32/32.

### `AGENT_FACING_TEXT` — two surfaces, and which requirement binds which
- current: `rules/hook-deny-message.md` governs every string a hook sends into a
  tool result, over TWO named surfaces: **block** (`permissionDecisionReason`, a
  `block` reason) and **notice** (`additionalContext`, `systemMessage`). P1–P4
  and R1 bind both. R2 (retry mechanics) and R3 (misfire exit) bind block only;
  the notice surface carries **R2n** (say what the reader may do — "nothing"
  counts, checked on the situation text with the receipt sentence removed) and
  **R3n** (name the row this notice left). Enforced by
  `tools/hook-deny-lint/lint.py`, four fixtures, two per surface.
> **Share note.** `tools/hook-deny-lint/` is source-only (excluded-by-decision,
> `tools/share-manifest.toml`). `rules/hook-deny-message.md` still ships and is
> readable as a manual checklist; there is no shipped `lint.py` to run it.
- why: the contract is a property of the TEXT, and the text does not become safe
  by not blocking anything. Measured 2026-09-09: 12 notice messages in 8 hooks
  were emitting agent-facing text that nothing ruled on — the object-vocabulary
  failure of L-044 inside the instrument built to prevent it. Three of them
  carried a defect the block surface would have failed on sight: two
  `Detail: ops/lessons.md …` pointers (P2), one `tell the user …` (P4), one
  message that named no actor at all and one that named a MODULE
  (`[handoff-snapshot]`) rather than the hook that spoke. R2/R3 were dropped
  rather than kept for form: they compensate for a BLOCKED call, and a notice
  blocks nothing (ruling H-1, model-origin, recommended value taken).
- evidence: `python tools/hook-deny-lint/lint.py` → 19 hooks, block 31 sites /
  14 hooks, notice 12 sites / 8 hooks, FAIL 0, warn 24, unresolved 0 (from
  32 sites / FAIL 0 / warn 14 / unresolved 3, block-only). Calibration is
  two-sided per surface: the notice known-bad fails P1, P2, R1, R2n and R3n —
  every notice-side check has a known-true positive. Six inversion probes plus
  a negative control, re-runnable and side-effect-free:
  `outputs/inversion-probes-notice-surface-2026-09-09/invert_notice_surface.py`.
  Probe I-4 corrected the design: R2n was passing on every notice because the
  receipt sentence contains its own action verbs. Seven hook suites re-run
  unchanged (appdata both-sides, dispatch 32/32, shell-transport 41/41,
  model-cap 37/37, ps-errorpref 47/47, ps-pipeline 51/51, compact-loss 34/34) —
  none of them asserts message TEXT, which is why the lint has to.
- history: born as the deny-message contract 2026-09-07 (sunk from
  `transcript_read_guard`'s docstring after the 2026-08-29 false positives).
  2026-09-09 (F-8): split into two surfaces; helper/builder resolution added so
  a message is ruled on at the site that EMITS it (unresolved 3 → 0, and
  `browser_pane_scope_guard`'s only deny message came back into the check after
  the first version of that change silently dropped it); `report_fp.py --rate`
  gained a notices column, because a misfire report does not name a surface and
  denies alone would have overstated `shell_transport_guard`'s rate ~6× (187
  denies against 942 notices).
- review-when: (a) a THIRD agent-facing text surface appears — a new hook-output
  key, or a new event whose stdout the harness injects. One is already measured
  and NOT ruled on: bare stdout of `SessionStart`/`UserPromptSubmit` hooks, 7
  entries in settings.json (F-9), named in the lint's summary line every run;
  (b) the harness stops delivering `additionalContext` or `systemMessage` to the
  model — the notice requirements were written for a reader that cannot
  authenticate them; (c) a notice misfire is reported and the rate is
  unmeasurable → the receipt form is not paying for itself, revisit R3n.
- rollback: `SURFACE_KEYS["notice"] = ()` restores the block-only instrument in
  one line (probe I-6 asserts this is the load-bearing switch); the hooks' text
  repairs stand on their own and are not reverted with it.

### numberref extraction — deferred, both triggers named
- current: **NOT extracted.** The SSLD NumberRef citation registry
  (`07_案卷/_registry/numberref.py`) stays project-local. Full case, the
  execution plan and the adaptation risks:
  `outputs/numberref-extraction-deferred-2026-09-10.md`
  (`status: deferred-pending-second-customer`). User ruling 2026-09-10
  (「C1先等等，但我覺得很有價值」).
- why: it is the mechanism three rules here already describe and none owns, but
  it has ONE customer. SSLD has a JSON fact layer for a selector to point into;
  nobody else does. Extracting now would be generality predicted, not observed.
- evidence: SSLD T48 page build `value-gate [124 numbers in the reader's text,
  107 registered]` with an injected-unregistered negative control; the weaker
  sibling shipped 2026-09-10 (`tools/audience-fit-gate values`) matches value to
  value across two prose documents, never value to field, and prints its own
  false-accept rate.
- review-when: **fires** when a SECOND project produces a durable human-facing
  artifact with a hand-typed number — a real defect of the class outside SSLD
  (most likely first sighting: an `audience-fit-gate values` false accept a
  human then catches). **Abandons** at 12 months unobserved, or when a document
  format that carries sources inline by construction is adopted.
- rollback: none to undo — this entry records a deliberate non-action; deleting
  it would only lose the trigger.

### literature access — an institutional VPN is not a crawling permit
- current: `rules/literature-access.md`. A citation-bearing evidence artifact
  records its access route and licence basis per source, and never holds content
  obtained by defeating an access control. Routing ladder: open access /
  preprint / repository -> official metadata or TDM API -> ordinary HTTP on
  hosts that serve it, named targets only -> the in-app browser at human pace
  for a NAMED article on a host whose terms permit agent access -> hand it to
  the user. Anti-bot challenge = routing signal, never an obstacle; the
  curl -> WebFetch -> headless -> real-profile escalation ladder is ONE
  prohibited attempt in four costumes. NTU is currently the only institution
  this machine has been observed entitled through.
- why: the technical control IS the licensor's enforcement of the licence term,
  so circumventing it is not a grey area about volume. IEEE Xplore's
  Institutional Subscriber terms forbid robots or intelligent agents to
  "access, search and/or systematically download" any portion -- the verbs
  include plain access, so a program reading one article is already outside the
  licence while a person reading it is inside. NTU's own campus network rule
  forbids unlawful downloading/reproduction of copyrighted works and any abuse
  of network resources. The enforcement mode that matters is the publisher
  suspending the whole institution's IP range, which takes the university
  offline rather than the operator. A headless browser or a logged-in profile
  makes the access look human while remaining an agent -- aggravation, not
  mitigation -- and entering credentials is separately out of bounds.
- evidence: IEEE Xplore Terms of Use, "Terms of Use for Institutional
  Subscribers", read verbatim 2026-09-10 through an NTU-entitled session;
  NTU 校園網路使用規範 (計中, 101.4.24 修正) 第二條 / 第三條, fetched the same
  day. Measured host table and the VPN detection command:
  `ops/environment.md` "Institutional literature access". Live instance that
  provoked the rule: SSLD wave W15, where a dispatch prompt named a browser
  surface for a banned host and the subagent escalated curl -> WebFetch ->
  playwright-headless -> claude-in-chrome to reach it.
- history: first entry 2026-09-10.
- review-when: the VPN resolves to an institution other than NTU; a publisher on
  the routing table changes its Terms of Use; an official TDM API becomes
  available for a host currently on the hand-to-the-user row; a publisher blocks
  the institution's IP range (that retires the automated row entirely).

### literature host guard — the access rule as a machine-readable table, enforced at the tool boundary
- key: `hooks/literature-host-policy.json` (the table) · `hooks/literature_host_guard.py`
  (PreToolUse deny) · `skills/literature-search-extract/connectors/access_policy.py`
  (the skill's read of the same table) · `verify/fetchsrc.py` (the fetch instrument).
- current: one row per scholarly host with `class` (`open` · `metadata_api` ·
  `landing_page` · `agent_banned` · `institutional_only`) and the `agent_surfaces` the
  row grants (`script` · `webfetch` · `browser_headless` · `browser_user`), plus
  `max_per_run`, `retention` (full | excerpt), `licence_basis`, `verified`. 32 rows on
  2026-09-11: the seven hosts `ops/environment.md` measured on 2026-09-10 (IEEE Xplore,
  ScienceDirect, Wiley, MDPI, Southampton eprints = `agent_banned`; Optica, IOP =
  `landing_page`, one document per run, webfetch only), the public APIs, the OA hosts,
  Scopus / Web of Science / airiti / SLIM = `institutional_only`. An UNLISTED host gets
  one plain fetch of a named URL and no browser surface (user ruling R2); the skill caps
  a run at three distinct unlisted hosts; the hook rules only on listed hosts and on
  browser surfaces to the `unmeasured_publisher_hosts` list. The hook fails OPEN on an
  unreadable file (loud telemetry row) because it sits on WebFetch and every shell
  command; the skill's reader fails CLOSED (only the built-in public-API core reachable).
  Matcher: `WebFetch|Bash|PowerShell|mcp__(Claude_Browser|claude-in-chrome)__(navigate|preview_start|browser_batch)|mcp__playwright-headless__browser_navigate`;
  Bash/PowerShell are judged on `https?://<host>` literals in the command.
- why: user ruling 2026-09-11 (R1) after the NTU Library AI-literacy guide
  (研究生防雷指南, 2026-09-11, slide 18): unless a host is explicitly released, a program
  does not retrieve from an access-controlled site — the enforcement mode is the
  publisher blocking the institution's IP range and the library disabling the VPN. A
  rule in prose was the state on 2026-09-10 and the skill's own `search-sources.md`
  still told the executor to render "anti-bot" pages headless; the table + hook make
  the rule the same object for the skill and for every other session.
- evidence: `hooks/tests/test_literature_host_guard.py` (D-01..D-18 / A-01..A-15 /
  M-1..M-2 / R-1..R-4 / FO-1..FO-10 / L-1..L-5b / I-1, all green 2026-09-11);
  `access_policy.py --selftest` 20 cases (6 allow / 14 refuse); `fetchsrc.py --selftest`
  24 cases incl. "a challenge ends the host: ONE call, no retry", a redirect judged on the
  FINAL host, a traversal `--name` refused; hook-deny-lint FAIL 0. Independent QA the same
  day (report `%LOCALAPPDATA%\Temp\claude\qa-lse-2026-09-11\qa-report.md`, verdict PASS
  WITH FINDINGS) found the trailing-dot bypass (F-1) in BOTH the hook and the skill's
  reader — fixed within the hour, D-17/D-18 hold it.
  Design of record: `references/lse-access-verification-upgrade-design.md`.
- history: born 2026-09-11 (settings backup
  `backups/2026-09-11/settings.json.pre-literature-host-guard`).
- review-when: a new browser MCP server is registered (surface mapping + matcher
  line); a listed host changes side (new challenge, or a challenge that stops); a
  publisher exposes an official TDM API (row gains `tdm_api`); the FALSE-POSITIVE LOG
  in the hook's docstring reaches 3 (then the ROW is re-derived, never the hook
  widened); `<browser_surfaces>` wording changes.
- rollback: remove the matcher entry from `settings.json` (backup above); the table
  stays and the skill keeps refusing on its own.

### deliverable reader pass — no gate has an object for a sentence

- key: `rules/deliverable-doc-refs.md`, clause "No gate reads a SENTENCE".
- current: a human-facing deliverable claimed "gates pass" ships with a model
  read of the RENDERED reader text, stated in the delivery along with what it
  named. Prose twin of `rules/figure-self-read.md`; neither replaces the user's
  own confirmation.
- why: the gate family in that file binds numbers to sources, terms to a canon
  and blocks to byte-equality. None of them has an object for whether the claim
  assembled from those pieces holds together, so a self-refuting sentence is
  not misjudged -- it is unjudgeable. Adding a consistency gate is not the fix
  either: the classes are open-ended (a comparison across tolerance classes, a
  disagreeing row summarised inside a clean sweep, a reassuring frame around a
  number that says otherwise). A reading pass covers the open set; a gate
  covers only what someone already named.
- evidence: SSLD T55 page shipped 「最大的相對差是 6.489 %，遠小於 0.5 % 的判定
  門檻」 with 18 page gates and 52 figure gates green, every number legitimately
  registered. Same round, the same defect in a figure (one 0.5 % threshold line
  drawn across two tolerance classes, the only out-of-tolerance point clipped
  off the axis) and in a second figure (a reject-nothing 0 drawn beside the
  chapter debunking it). All three were caught by re-reading the rendered
  output, none by a gate. `ops/lessons.md` L-071, L-072, L-076.
- history: first entry 2026-09-10.
- review-when: a consistency checker lands that can rule on cross-class
  comparisons in prose (the pass then names what the checker covers and reads
  for the rest); or the deliverable class stops being human-facing.

### dispatch prompts name the routing table, not a tool surface

- key: `ops/20-dispatch.md` §4a, closing paragraph.
- current: a dispatch prompt names the routing table and the acceptance shape,
  never a browser, fetch command or client. The licensed empty answer stays
  reachable -- a worker that stops at a barred route and reports the gap has
  succeeded.
- why: naming a surface hands the worker a path whose legality the dispatcher
  has not checked. If the path is barred, the violation is committed at
  dispatch time and the subagent merely executes it; blaming the worker
  misplaces the fault and leaves the prompt template intact to do it again.
- evidence: SSLD wave W15-L1 escalated curl -> WebFetch -> playwright-headless
  -> claude-in-chrome against a host whose terms bar agent access; the dispatch
  prompt had named a browser. Recorded as dispatcher fault in that wave's
  `route_compliance` block, three source rows marked PARTIALLY NON-COMPLIANT.
  `ops/lessons.md` L-075; the licence side lives in
  `rules/literature-access.md`.
- history: first entry 2026-09-10.
- review-when: the external dispatch tier gains a mechanical route allowlist a
  prompt can cite by name (the clause then points at it).
