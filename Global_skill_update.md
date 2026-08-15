# Global Skill Update Log

> **FROZEN 2026-08-11 — historical event log. Do not add new entries in the
> source environment.**
>
> Standing rationale ("why does this rule hold this value") now lives in
> **`claude-ops/ops/rule-registry.md`**, keyed by the RULE rather than by the
> date. The per-change event record — which files changed on which day, and
> the rollback path — lives in the source environment's git commit messages.
>
> Why the split: this file grew as O(changes) while its value is O(rules), so
> it needed rotation forever, and rotation evicts the OLDEST rationale — which
> is the most settled and therefore the most load-bearing. That is not
> theoretical: a rotation pass once evicted a standing user ruling that then
> survived only in gitignored backup copies, recovered by luck during a later
> cleanup. Rulings now live in `rule-registry.md`, in version control.
>
> This snapshot stays readable and stays in git. The entries below 2026-08-08
> are this share's own last refresh, added as one batch — not accumulated
> append-only the way the source log was.

Append-only log of changes made by skills that modify durable config (CLAUDE.md, skills).
Each entry: what was newly added/changed + when (absolute timestamp).
Entry fields, from 2026-08-07 on: trigger / change / result / rollback / open.

**Order is NOT uniform, by history**: entries from 2026-08-08 on are
prepended directly below this header (newest first); everything from
2026-07-25 to 2026-08-07 sits below them in the original ascending order.
Read the top block downward for recent work, and the lower block bottom-up.

---

## [2026-08-11, interop] Preference ports, method does not — refs retired, leak gate added, curation cleared

- **trigger**: user ruling — Antigravity sync dropped (agent no longer used);
  opencode sync kept, but with a preference shift toward "the target agent
  reads its own current official docs and adapts, rather than inheriting a
  copied-over method playbook"; and a question of whether the interop layer
  should keep only identification/security-risk screening and delegate
  everything else. Confirmed before implementing: the delegation applies to
  the METHOD layer only — `portable-core.md` (the user's own standing
  preferences) stays transplanted, because no official documentation can
  produce it.
- **change**: `interop.py`'s reference-compile class (a `REFS` registry that
  compiled ~20K of curated method playbooks to a target-side `interop-refs/`
  folder plus a prose routing index) retired entirely, replaced by
  `delegation_block()` — "the preferences above are the user's own standing
  rules … for method depth, consult THIS platform's own current official
  documentation … propose the adaptation to the user before installing
  anything durable." A new L0 leak gate assembles every enabled target's
  payload in memory, scans it, and only writes if clean; a hit aborts the
  whole build with nothing written. `portable-core.md` curated against the
  accumulated CLAUDE.md changes since the last pass: two new blocks
  (environment/shell conventions, failure visibility) and two merges. Not
  ported as method: depth-tier triage, boundary-contract format, relaxation
  gate, the browser-pane hook rule, path-scoped rules index.
- **result**: `status` now reports one active target (opencode), `[off]` for
  both disabled ones, and curation up to date. Leak gate verified
  adversarially: one planted secret of each of 6 pattern classes inside a
  REAL block → 6/6 aborted with nothing written, control build still writes.
  The first two probe versions reported false failures because the plant
  landed outside the block markers — fixed by asserting the plant reached the
  assembled payload before judging the gate.
- **rollback**: `interop-layer/` git history predating this refresh; retired
  playbooks kept locally (not published) for traceability.
- **open**: opencode deployment itself is NOT done — writing into another
  agent's config is outward-facing and wasn't asked for. With only opencode
  enabled on the `light` profile, several `full`-only blocks — including the
  new failure-visibility one — currently ship to nobody; whether opencode
  should take `full` is an open user decision.
  *(Annotation added 2026-08-15, by exception — this file is frozen and the
  bullet above is unchanged. That open decision was closed on 2026-08-15: the
  profile is `full`, the target is deployed, and all 15 blocks now reach it.
  Standing reason: `claude-ops/ops/rule-registry.md`, key `interop`; the event:
  `CHANGELOG.md`, the two 2026-08-15 entries.)*

## [2026-08-11] Codex push-sync disabled + SKILL.md body cap 250 → 300

- **trigger**: user ruling after a drift sweep — the codex-side environment
  cannot fully use this design as-is and its own compiled sync quality wasn't
  good; separately, whether the SKILL.md body-line cap should widen so new
  skills don't shave completeness just to dodge the trigger.
- **change**: codex marked disabled in the interop target registry (build
  skips it, status reports `[off]` without counting it as drift — a disabled
  target is a decision, not backlog). SKILL.md body cap raised 250 → 300
  lines; a new maintenance rule states explicitly that a size trigger means
  EXTRACT, not delete-until-it-fits.
- **result**: corpus at the time of the raise: 14 skills, median 153.5 lines,
  62.9 B/line, exactly one skill over 250 (256) and none over 260 — so a
  smaller raise would have bought one nudge and no headroom. 300 lines is
  roughly 1.25× the CLAUDE.md cap, paid once per skill invocation (never at
  session start). A prior compression pass that cut lines from two SKILL.md
  bodies without extracting to a references file, landing one skill at
  exactly the old cap, was the concrete case the new rule now names.
- **rollback**: pre-change backup of the health-check hook; the commits that
  follow this entry in the source environment's history.
- **open**: the wider interop curation backlog and antigravity's stale state
  were untouched by this ruling — it named codex only.

## [2026-08-11] Audit-trail rotation retired → rule-registry.md born; default session model raised

- **trigger**: user directive to address the growing chronological log
  (rotation had become recurring maintenance) and to check for other drifted
  or stale leftovers; separately, to raise the default session model tier
  (kept for simple/mechanical dispatch use only — the cost-cap policy for
  actual subagent dispatch is unaffected).
- **change**: the source environment's `Global_skill_update.md` — the file
  this share mirrors — was frozen as a historical log (see the banner at the
  top of this file) and its standing-rationale role handed to a new
  rule-keyed `ops/rule-registry.md`, which replaces the growing log with a
  file whose size tracks the number of RULES rather than the number of
  changes. A drift sweep also surfaced that the interop curation backlog and
  one disabled target were not properly reflected in the status report,
  addressed in the interop entry above.
- **result**: no entry was lost — the rotated content is preserved (kept
  locally in this share for traceability rather than published, since it is
  older, already-superseded internal history). The default session model
  change does not affect the subagent cost cap, which is enforced by a
  dedicated hook reading the dispatch call's own model argument, never the
  session default.
- **rollback**: pre-change backups of the rotated log and the settings file,
  in the source environment.
- **open**: the interop re-curation itself was deferred as a separate,
  judgement-heavy pass (covered in the interop entry above) rather than done
  as part of this cleanup.

## [2026-08-11] CLAUDE.md trim + Opus→L1 standing ruling + dead permission rules removed

- **trigger**: user directive after reviewing a measured startup baseline —
  clean up a set of dead permission-ask rules that a CLI diagnostic showed
  never matched anything (a `Write(...)` rule shape that the file-permission
  checker does not evaluate — only `Edit(...)` rules are), and set the
  ops-relaxation level for an Opus-tier main-loop model to L1 as a standing
  grant rather than an ask-every-time gate.
- **change**:
  - Removed 4 dead `Write(...)` permission-ask entries (each path already had
    a live, functioning `Edit(...)` rule covering the same file-editing
    tools); added an `Edit(...)` rule for the new `rules/` directory, which
    becomes a rule-tier carrier in this same change.
  - Global CLAUDE.md relaxation-gate bullet gained the standing ruling:
    "**Standing ruling (2026-08-11): an Opus-tier main-loop model runs at L1
    (core relaxed) in every project — don't ask, just state the identity and
    the level; a project CLAUDE.md may override with its own
    `ops-relaxation:` line.**" Mirrored into `ops/05-authority.md` §2 as a
    named user grant (explicitly not a self-relaxation).
  - Three restated engineering-judgement bullets about browser-pane UI
    verification collapsed into one shorter bullet — the enforcement detail
    now lives only in `ops/lessons.md` L-009/L-010, and the CLAUDE.md line
    points there instead of restating it.
  - The whole `## Architecture` (FSD layering) section moved out of CLAUDE.md
    into a new path-scoped rule file (`rules/frontend-layering.md`); the GLSL
    parenthetical of the runtime-failure bullet moved into
    `rules/shader-failure-modes.md`. Both carry a path scope so they cost
    nothing at session start until a matching file is actually read. An index
    line in the CLAUDE.md preamble lists both, with a scheduled review date.
- **result**: CLAUDE.md shrank by roughly 8%, clearing the size-nudge
  threshold, net of new content added in the same commit (the standing ruling
  and the index line). Path-scope mechanics were established BEFORE any rule
  moved, by probe: a scoped user rule is absent from session-start loading and
  loads only when a matching file is read.
- **rollback**: pre-change backups of CLAUDE.md and the settings file, in the
  source environment.
- **open**: acceptance of the path-scope mechanism for these two specific
  files was not fully closed at the time of this entry — a fresh-session
  check (read a matching file, confirm it loads on-read and not at start) was
  still outstanding.

## [2026-08-11] Context-budget instrumentation + evidence-block schema

- **trigger**: evaluating which parts of an external agent-harness design were
  worth adopting. Two real gaps were found after ruling out duplicated
  mechanisms: supplemental instruction state has no scope/expiry (context
  budget), and there was no evidence-block schema tying a claimed pitfall or
  proposal back to the moment it happened. A review round required that any
  context-cost claim be MEASURED rather than estimated before a rule moves.
- **change**: added a logging-only startup-instrumentation hook (never denies,
  never injects context) and a read-only startup-baseline reporting script,
  both purely observational. `ops/lessons.md` and `70-evolution.md` gained a
  required `Evidence:` line on new entries (session / digest / locator /
  captured), registered as a schema in `rules-usage-dict.md` §7. Both schema
  changes apply from 2026-08-11 on, no backfill.
- **result**: the instrumentation hook was exercised against synthetic
  payloads (normal / empty / malformed / oversized / edge cases) before being
  trusted — all handled correctly, fail-open on anything odd. The measured
  finding that reshaped the whole line of work: an always-loaded instructions
  file turned out to be roughly a tenth of the measured startup floor rather
  than the dominant cost, so trimming it is an ADHERENCE lever (make it more
  likely to be followed), not a token-cost lever — the dominant startup cost
  is the tool/MCP/skill roster, out of scope for a rules trim.
- **rollback**: pre-change backups of the touched ops files, in the source
  environment.
- **open**: whether the instrumentation hook fires at all depends on harness
  version support for its trigger event — unverified until a fresh session
  produces a non-empty log. Whether a user-level path-scoped rule file
  actually honours its path scope (vs. always loading) was also unverified at
  this point — see the CLAUDE.md-trim entry above, which treats it as
  unproven until a fresh-session probe confirms it.

## [2026-08-08] NEW hook — browser-pane UI-verification enforcement (L-009/L-010)

- **trigger**: whether the L-009/L-010 browser-pane verification pitfalls,
  which lived only in rules-layer text (global CLAUDE.md + `ops/lessons.md`),
  were actually guaranteed to fire — raised as a design question, not
  discovered by a failure. The answer was no; see `ops/lessons.md` L-011 for
  why (trigger-shape mismatch: both pitfalls fire mid-measurement, when the
  agent is already confident and reading past a reminder line — L-009 alone
  recurred for about a month under a CLAUDE.md-only rule).
- **change**: a new PreToolUse hook matched to the browser-pane tool names.
  Denies a script-execution call containing a `getComputedStyle`-family read
  with no settle token in the same call (escape hatch: a literal marker for
  the rare case where the mid-transition value IS what's being measured).
  Denies a screenshot call until a `visibilityState` probe has run this
  session (a short-TTL per-session marker). CLAUDE.md's existing L-009/L-010
  lines were kept but now cite the hook as the enforcer, not the mechanism
  itself; `ops/lessons.md` L-009 got an amendment note, and new entries
  L-010 (the pitfall) and L-011 (the routing-design rationale) were added.
  `ops/environment.md` gained a "Browser-pane UI verification" block as the
  environment-facts anchor the hook's refresh trigger points at.
- **result**: the hook compiled clean and was exercised against 8 synthetic
  payloads covering both deny branches, the escape hatch, cross-session
  marker isolation, non-matching actions, and malformed input (fail-open):
  8/8 as expected. A companion out-of-process headless-browser probe script
  (implementing the same settle-then-measure logic) was verified against a
  control run proving a naive hover-then-measure never reaches a transition
  target on the same fixture — the mechanism was measured, not just asserted.
- **rollback**: pre-change backups of CLAUDE.md, the settings file, and
  `environment.md`, in the source environment.
- **open**: the hook only sees explicit `getComputedStyle`-family text in
  script-execution calls — a style value inferred from an accessibility-tree
  read is invisible to it (theoretical gap; those tools don't report computed
  style). Not yet exercised against a real occluded-pane screenshot or a real
  hovered-element measurement in a live session at the time of this entry —
  only synthetic payloads and the out-of-process fixture had been run.

> Older entries (2026-06-28 – 2026-07-10) rotated to `archive/Global_skill_update-2026-06-28--2026-07-10.md` on 2026-07-19 (ops/40-maintenance.md S3).

## [2026-07-11] literature-search-extract P6: semantic-contract patches (update-plan v2, user-approved)

- Context: an external AI (reading the STALE 2026-07-08 raw copy under `~/.agents/skills/`) proposed a 12-problem overhaul. Adjudicated against the live skill: 8 claims obsolete/wrong (evals, PRISMA exhaustive, TODO sync, slim frontmatter all already shipped 07-10); 3.5 valid. Rejected explicitly: exhaustive→extended rename (would delete shipped+eval'd PRISMA capability), evidence_core schema, frontmatter rewrite, capability-aware handoff (interop-layer responsibility). Full adjudication: skill dir `literature-search-extract-update-plan-v2.md`.
- SKILL.md (+14 lines net, ≤15 budget): (a) P2 route-first block — source-provided (no auto-expansion) / discovery (default) / mixed (search_trail splits supplied vs discovered); (b) Mode 1 clarification split — ONE pre-search question only for scope/target-changing ambiguity; presentation-only ambiguity never blocks (catalog Use-when inference, default inline summary, post-delivery conversion offer); (c) P5 file authorization — inline by default, file only on explicit user/caller request, length never justifies a file.
- References sync: search-sources.md header scoped to discovery/mixed paths; output-templates.md Language-and-Mode rules gained the inline-default/explicit-file-request line. extraction-playbook.md + credibility-rubric.md grep-checked: no conflicts, untouched.
- evals.json: appended eval 6 (source-provided path, Nagpal 2009 Methods/Limitations only) + eval 7 (file authorization, multi-source digest w/o report request). passed/evidence left null — live run needs separate subagent authorization.
- Verification: quick_validate.py "Skill is valid!"; semantic greps (new terms present; extended/evidence_core absent; exhaustive ×8 preserved; contract 5 fields intact; frontmatter diff-identical); JSON valid (7 evals); config-self-audit clean (all 5 references exist, no exec surface, machine files English-only; body 257 lines — pre-existing, adjudicated 07-07). Backup: backups/literature-search-extract-20260711-pre-v2/.
- Flagged for separate task: `~/.agents/skills/` holds 11 stale raw skill copies (violates interop "never copy raw skill files"); root cause of the external AI's misdiagnosis. Candidate-skill proposals (ingest/SR/citation-audit/corpus/synthesis) adjudicated in chat — none built.
- Addendum (same day, user-authorized): evals 6-7 executed live via one haiku subagent each. Eval 7: 3/3 passed (inline delivery + gaps/confidence, zero file creation, zero format questions). Eval 6: 3/4 passed; full-text-extraction assertion left null — not exercisable (Science paywall, 403 on all channels) — while the paywall degradation itself behaved exactly per P3 ([abstract]-tagged quote only, refused reconstruction, no supplementation, no extra-literature search). evals.json passed/evidence filled; TODO item 18 closed; TODO item 19 added (candidate: share-packaging portability pass — provider-neutral local-corpus slot, strip personal files).

## [2026-07-11] NEW skill skill-share-packaging + first live export (literature-search-extract) + provider-neutral corpus slot

- Context: user adopting Zotero soon + wants shareable skills + a written rule-set for cross-environment skill sharing (motivated by internet-shared skills breaking on other machines / leaking data).
- literature-search-extract canonical: prism hardcoding generalized to a provider-neutral local-corpus slot (SKILL.md P2 tool priority + reference map; search-sources.md gained a slot-note: prism = reference implementation, Zotero/Obsidian MCP slot into the same routing rules, verify actual tool set before relying). No behavior change — "fully functional with web search alone" preserved.
- NEW ~/.claude/skills/skill-share-packaging/ (112 lines, via skill-creator conventions): Mode A export (scope manifest → de-environment pass → data-leak pass → audience decision → verify → package to outputs/skill-share/) + Mode B import audit (quarantine, reverse greps, instruction-hygiene red flags, trigger collision, then config-self-audit). Hard rules: canonical never modified for sharing; share copy = one-way build product outside skills tree. Registered in skill-trigger-dict.md (環境設定 family + 2 quick-table rows + skill-creator mutual disambiguation). evals/evals.json: 2 evals.
- Living proof (Mode A first run): outputs/skill-share/literature-search-extract-20260711/ (+zip +SHARE-NOTES.md). Removed 6 personal items (TODO, PDF-GUIDE, 2 plans, sample-run, .claude/); 10 rewrites in the copy (trigger-dict ref dropped, sibling-skill names genericized, "Traditional Chinese" → "the requester's language"); leak/coupling grep 0 hits; quick_validate.py valid; all internal refs resolve; canonical untouched by the build. skill-share-packaging eval 1 filled from this run (4/4); eval 2 (import audit) pending a real third-party skill.
- config-self-audit on the new skill: validator OK, referenced paths exist, conditional trigger + NOT clauses, no exec surface, 112 lines < 150.

## [2026-07-11] skill-share-packaging: prescan.py mechanical pre-pass (adopted from lifeos-memory analysis)

- Context: user-directed adoption round after analyzing D:\Analyze\lifeos-memory-master (external repo, README + full source read; adopt-vs-skip adjudicated in chat). Approved items: (1) pitfall-card convention into memory, (2) mechanical scanner into skill-share-packaging. Explicitly NOT adopted verbatim: their 80-line SKILL.md hard cap (user ruling: line budget must weigh information density and skill weight case-by-case), claw/watchdog/realtime-summary harness (POSIX-only, redundant with harness context continuation, standing haiku cost).
- NEW scripts/prescan.py (179 lines, stdlib-only, Windows-safe ASCII output): adapted from lifeos-memory skill-vetting scan.py, restructured into mode-tagged pattern sets — import mode (code-exec, subprocess, obfuscation incl. zero-width unicode, network incl. raw-IP URLs and curl|sh, destructive file ops, prompt-injection/reviewer-social-engineering phrasing) + export mode (env-coupling and data-leak patterns mirroring SKILL.md A2/A3, incl. a partial-key-trace pattern). Exit 0 clean / 1 findings / 2 usage; --format json available.
- SKILL.md (+10 lines): prescan wired into Mode A step A3 (export self-check) and Mode B as mandatory first step, both with the explicit caveat that findings are review pointers and a CLEAN result is not a safety verdict — full manual pass still required.
- Verification: py_compile OK; live fixture run against lifeos skill-vetting dir — import mode 33 findings (all expected: it's a pattern database documenting the very patterns), export mode caught the real partial-API-key trace in their GOTCHAS.md (`key: rii5...TylN`) that manual reading had also flagged; clean-fixture run returns CLEAN/exit 0; findings exit code 1 confirmed. Merged via feat/skill-share-prescan (--no-ff), branch deleted.
- Memory side (gitignored, not in this repo's history): pitfall-card-convention.md written — write gate (>few minutes AND recurring AND not repo-derivable), hit_count/last_hit recurrence on existing card, hit_count>=2 → propose promotion to standing rule (user decides), superseded_by for reversals, load-on-demand only (index line always, body only when task touches the area).

## [2026-07-11] lifeos-memory adoption round 2 (C1-C4; C5-C8 adjudicated skip)

- Context: second user-confirmed round from the lifeos-memory analysis. Approved: C1-C4. Skipped by ruling: C5 defensive-daemon reference card (no current daemon-authoring need), C6 80-line cap (ops/40-maintenance S3 is the density-adjusted equivalent), C7 per-skill GOTCHAS.md (superseded by pitfall-card convention), C8 vector search (memory corpus too small).
- C2 ops/70-evolution.md §1.4 (+5 lines): no-duplicate-mechanisms invariant extended with L2 (community-solution quick search, ≤10 min) and L3 (state where their assumptions break in our context; the diff IS the justification — no diff → adopt/extend, don't build). Source: lifeos-memory skill-author Step 0.
- C3+C1 workflow-checkpoint SKILL.md (+12/-2): §A gains a self-check step before reporting (four headings present, absolute date, Detail link resolves — guards checkpoints written near context exhaustion); §C gains a crash-recovery fallback (phase-log missing/stale → consent-gated rebuild from persisted transcripts, then offer a catch-up checkpoint). Deliberately replaces lifeos' cron summarizer + watchdog respawn with zero-standing-cost equivalents.
- C4 skill-share-packaging SKILL.md A6 (+4/-1): share-notes now include three recipient verification steps (install location, one positive trigger probe, one negative probe). Extracted from lifeos doc-to-skill activation verification; their full installer/uninstaller machinery judged overkill for single-skill sharing.
- Verification: grep-confirmed all four edits landed, §A step numbering deduplicated (one "Then proceed to §B"), line counts 119/72/125. Merged via feat/lifeos-adoption-r2 (--no-ff, 3 semantic commits), branch deleted.

## [2026-07-12] Prism PSM incident fold-in: R2 claim-calibration + product-design-thinking sole-source contract rules

- Context: external Codex review of Prism PSM_REMEDIATION_v1.0.md (8 findings) re-audited and confirmed in-session; user directed system-level rule adjustments instead of project fixes. Root causes distilled into ops/lessons.md L-002 (delta-doc economy, append-only v-bump without consistency pass, claim strength > evidence strength, semantic compression of two-proposition verdicts, plus a skill-trigger miss).
- ops/30-judgment.md R2 (+18 lines): claim-calibration corollary — universal/completion claims require enumerable evidence (matrix/exhaustive diff/real run), one-pass survey only supports "initial pass found no further gaps"; refutations must give per-proposition verdicts. With ENV-01-derived example pair.
- skills/product-design-thinking/SKILL.md (+26 lines, description +2): Phase 3.4 gains sole-source contract rules (self-contained or drop the claim; build-ready bar per item; skeleton-plus-incomplete-report over silent thinness; single decision register with status; in-place version bumps require full-doc consistency pass). Description + skill-trigger-dict.md widened: PSM-grade remediation/re-planning of an EXISTING product triggers the skill.
- Backups in backups/2026-07-12/. Finding 8 (unsourced market claims) judged a violation of existing R5, not a rule gap — no edit.

## [2026-07-12] thinking-notes/11 fold-in round 1: judgment additions + pitfall-ledger consolidation

- Context: user-approved plan `drafts/2026-07-12-implementation-gaps-adjustment-plan.md` (v2). Source thinking-notes/11 was re-audited before execution: citations to notes 01/05/06/09 all verified; four plan-level corrections made (empty card layer, write-gate violation, rule-budget overflow, gap-2 omitted from source's priority table). User rulings: no one-shot skill (principles apply to ALL deliveries → global rules); merge duplicate pitfall stores.
- ops/30-judgment.md: trimmed 10,959 → 10,227 chars (< 10,240 cap; kept one example per ✅/❌ pair, dropped Usage meta-sentence). Added: R2 delivery-summary claim→artifact-location rule (gap 6); R8 Delivery mental-simulation two-class reporting (shallow 1) + 選型 rejection-table line (one of the three previously-agreed deliverables — the other two already covered by ops/10 Step 4 and R5/R8).
- Pitfall-ledger consolidation (user-directed): ops/lessons.md declared SOLE pitfall ledger; its tags: field now requires task-type trigger words (absorbs the task-type-index need). memory/pitfall-card-convention.md marked superseded_by: ops/lessons.md (zero cards were ever written; kept for provenance), MEMORY.md index line rewritten, rules-usage-dict.md layer-map row 6 updated. Net mechanism count: -1.
- thinking-notes/06: one-paragraph addendum — constraints (one-shot/urgent/tech-mandate) are unverified premises; the four-variable model applies to accepting them.
- config-self-audit on 30-judgment.md + one-line changes: pass (size cap verified via hooks/ops_health_nudge.py SIZE_CAP; reference existence, no contradictions across the three touched rule files, language conventions OK). Backups in backups/2026-07-12/.
- Pending (next step, 🔴): global CLAUDE.md 5-item diff (B1) awaiting user confirmation.
- B1 applied 2026-07-12 (user confirmed the 5-item diff verbatim): global CLAUDE.md now 10,572 chars (<12K). Commit c97af8e; backup backups/2026-07-12/CLAUDE.md.

## [2026-07-12] mattpocock/skills fold-in: tracer-bullet slicing + project domain glossary + dict-sync guard

- Context: user-approved evaluation of github.com/mattpocock/skills (R8 two-pass). Adopted as conventions, NOT new skills: to-tickets tracer-bullet discipline, wayfinder investigation/fog concepts, domain-modeling CONTEXT glossary + ADR triple gate. Rejected: wayfinder concurrency machinery (single-user env), standalone always-on domain-modeling skill (trigger-surface cost), grilling family (user's Q-NN flow already covers alignment).
- ops/60-bootstrap.md (+59): SC gains slicing discipline (vertical complete slices, context-window sized, expand-contract exception for wide refactors, investigation ticket type, fog section stays coarse); new SE project domain glossary at references/<project>-context.md (lazy creation, live updates, challenge-don't-consume, ADR triple gate: hard-to-reverse + surprising + trade-off); SA step 1 reads it.
- Vocabulary tiers formalized in rules-usage-dict.md: skill-trigger-dict (env: triggers) / rules-usage-dict (env: layer boundaries) / project context.md (project: domain terms). Maintenance mounts: workflow-checkpoint SKILL.md gains glossary-sweep step 5 + reconstruction reads context file; product-design-thinking Phase 3 glossary persists to context file.
- ops/40-maintenance.md S2: dict-sync corollary — routing-surface changes update affected dicts in the SAME commit; enforced mechanically by hooks/ops_health_nudge.py new check 10 (skills/ vs skill-trigger-dict diff; verified with real positive [zz-drift-probe detected] and negative [silent, 12/12 in dict] runs; ~0 token cost when clean, user-approved).
- config-self-audit: one finding fixed (OPS.md routing line 56 lagged the new 60-bootstrap scope — itself a dict-sync case); budgets verified (60-bootstrap 7,010 / 40-maintenance 7,098 / rules-usage-dict 10,008 of 10,240 — NEAR CAP, trim candidate on next touch; wf-checkpoint 98 lines; pdt 208 lines pre-existing debt; trigger-dict 16,113 of 20,480). skill-trigger-dict.md intentionally unchanged (no trigger-surface change). Backups in backups/2026-07-12/.

## [2026-07-12] literature-search-extract: non-Claude portability layer + web-provider fallback facts + TODO retirement

- NEW references/portability.md: capability self-assessment for running this skill outside Claude — 7 tool slots, substitutes per slot, minimum viable profile, degradation-honesty requirement, explicit ignore-don't-emulate list for Claude-only constructs (e.g. prism MCP). search-sources.md: NEW degradation ladder rung 3b (extraction fallback via Tavily/Exa/self-hosted Firecrawl when the primary web-search path is unavailable) + provider quota table refreshed and web-verified 2026-07-12 (Brave free tier killed 2026-02; DDGS marked best-effort, not guaranteed). SKILL.md reference map five->six, new READ-FIRST-outside-Claude entry pointing at portability.md. Skill re-synced to the `~/.agents` and `~/.codex` copies (interop mirror, not the canonical source).
- TODO.md retired (all 21 P1-P7 items done — the ledger had become history, not a work list): archived to archive/2026-07-12-lse-update-plans/TODO.md; remaining open items (share-packaging decision, 3 MANUAL-VERIFY acceptances, optional SKILL.md slim, interop compile option) moved into a new FUTURE-WORK.md.
- No config-self-audit / eval re-run recorded for this batch — flagged here as a gap, not asserted as done.

## [2026-07-12] scientific-research-guide: first eval run + cross-session research-state mechanism

- First execution of evals/evals.json (4 cases, sonnet, protocol-level adversarial grading via subagents): 4/4 cases, 15/15 assertions pass; results and per-assertion evidence written back; one known limitation recorded (generic metrics have no calibrated range-check). NEW STATUS.md as a single-file continuation point; run logged in FUTURE-WORK.md; scripts/ backlog item marked a deliberate deferral, not an unfinished gap. No SKILL.md behaviour change in this pass.
- Cross-session research-state mechanism added: Gate A gains a continuity check (fires before Step 0) that reads the project's research-state.md first and rebuilds progress without re-asking; Gate D gains a consent-gated update rule (offers a write on tier/decision/iteration advance, writes only on yes, append-only iteration log). NEW 跨 Session 進度追蹤器 template added to references/deliverables.md as the living-document instance of tier-framework §7.4.
- NEW eval case 5 + fixture (evals/fixtures/research-state.example.md) verifying the skill uses recorded state instead of re-asking, still sanity-checks the prerequisite chain, and keeps writes consent-gated; case 5 run 4/4 pass, full suite now 5/5 cases / 19/19 assertions. Closes FUTURE-WORK item ①. Two prose-only residual gaps logged in run.known_limitation.

## [2026-07-14] Boundary-contract mechanism + relaxation-gate reliability fix (frontier-tier completeness shift)

- Context: user-approved design discussion (L2 granted). Diagnosis: the 05-authority relaxation gate almost never fired because (1) its trigger demanded a prediction ("start of heavyweight work") instead of an observation, (2) the rule sat two conditional reads deep, (3) harness autonomy prompts oppose mid-flow meta-questions, (4) no-ask defaults to safe L0 so violations are silent. Fix moves the trigger from model discipline into the harness + durable config.
- hooks/ops_health_nudge.py NEW check 11: reads hook stdin JSON cwd; if a project CLAUDE.md exists without `ops-relaxation:`, prints a one-line nudge (silent when key recorded, no project CLAUDE.md, or cwd is ~/.claude itself). Verified with real runs: fires on missing key, silent on the three exclusions, exit 0, py_compile OK.
- ops/05-authority.md: §2 trigger rewritten to four discrete observable events (first subagent dispatch / ticket-ledger creation / plan mode entry / ops-health nudge); recording in project CLAUDE.md promoted to same-turn default (one ask per project). NEW §4 Boundary Contract: L1/L2 + Tier-2 implementation tasks emit a 4-section ≤15-line contract (interpretation forks / boundary inputs / acceptance / non-goals & degradation) before method work; plan mode plan = contract carrier; delivery-time re-check duty; supersedes the four [BC]-tagged global rules while live. File 6,520 chars (<10K cap).
- Global CLAUDE.md: relaxation-gate bullet rewritten to the discrete-event trigger; NEW boundary-contract trigger bullet in engineering judgement; four rules tagged `[BC]` (manual-acceptance checklist, doubted-interpretation isolation, degradation order, boundary/compat enumeration) — superseded only while a live contract exists, bind as written at L0. File 11,310 chars (<12K cap).
- ops/60-bootstrap.md §A NEW step 5 (record relaxation level first session); ops/10-command-loop.md step 4 L1/L2 note (step substance delivered as the boundary contract); OPS.md routing row updated.
- config-self-audit: pass. Findings (low, accepted): nudge repeats in projects that never do heavyweight work (silence by recording `ops-relaxation: L0`); [BC] tags precede their defining bullet in reading order. MANUAL-VERIFY open: next real SessionStart in a keyless project shows the nudge line (stdin path tested synthetically only).

## [2026-07-14] OPERATOR-GUIDE.md: operator manual + whole-environment migration guide

- NEW root OPERATOR-GUIDE.md (Traditional Chinese, human-read): Part 1 operator manual for non-author operators (layer model, permission-mode selection, the three questions the model asks incl. L0/L1/L2, 深想/快答 keywords, ops-health signals, environment conventions); Part 2 asset map (git-tracked canon / non-git memory at path-derived slug / optional-carry archives / never-carry runtime+secrets); Part 3 step-by-step migration checklist with per-step verification + machine-binding table (settings.json hook paths x2 = the ONLY hardcoded absolute paths in tracked files, verified by grep; memory slug rename; credentials re-login; environment.md re-verify; interop targets rebuild); Part 4 division of labor vs interop/ (cross-agent compile, not same-system relocation). interop/README.md gains a two-line cross-reference.
- Closes the gap the user named: interop covered cross-agent rule sync only; whole-environment Claude Code -> Claude Code relocation had no document.

## [2026-07-14] COMMIT-TEMPLATES.md: repo-specific commit conventions

- NEW root COMMIT-TEMPLATES.md distilled from actual history (docs 32 / feat 28 / chore 9 / merge 7 / test 2 / fix 2 / refactor 1): type-selection table with config-repo semantics (feat = new mechanism, docs = rule-text/trail/notes), boundary-case rulings, scope conventions, fill-in templates + real examples + one anti-example, companion rules (rule-tier change pairs with a trail entry; branch + merge --no-ff convention). OPERATOR-GUIDE.md par.1.5 cross-references it.

## [2026-07-16] Work-card format (施工卡) codified as ops/60-bootstrap.md §F

- Context: user asked whether the work-card granularity used in remediation examples (ARCH-03/SYNC-01 style) was codified; audit found the sole-source build-ready bar covered Objects/Rollback/Acceptance but the card FORMAT (fields, IDs, Severity/Confidence, Blast radius, Commit) existed only as per-conversation improvisation. User approved codifying it.
- ops/60-bootstrap.md NEW §F: 9-field card template; declared a FORMAT not a ledger (content lives in the PSM item or ticket body — no card registry, §C 3-line stub stays the tracking minimum). Field ownership by reference: severity scale → code-review-deep-checklist output contract; commit format → global CLAUDE.md git rule with an explicit warning that COMMIT-TEMPLATES.md is this config repo's own semantics, never target projects'; Objects/Rollback/Acceptance render the product-design-thinking build-ready bar (normative minimum unchanged — a bar-compliant item missing only card-level fields is NOT a skeleton). Usage scope: recommended for sole-basis build docs + deep-review remediation output; optional for ticket bodies, dispatch orders, expand-contract batches, postmortem items.
- product-design-thinking SKILL.md: one pointer line under the build-ready bar (recommended rendering → §F); no normative change to the bar itself (field expansion deferred — needs a user-confirmed field list per the original proposal).
- Index sync: OPS.md routing row + rules-usage-dict.md rows 44/149 (grep-enumerated per L-004); skill-trigger-dict.md intentionally unchanged (no trigger-surface change).
- config-self-audit: pass. Notes (low): 60-bootstrap now 9,636 chars (94% of ~10K cap — trim candidate on next touch); rules-usage-dict 10,129 of 10,240 (pre-existing near-cap, +121); §F placeholder enumerates the four severity values (usability over pure reference; ownership note mitigates drift). Backups in backups/2026-07-16/.

## 2026-07-19 — ops/50-coach.md C11 + ops/30-judgment.md R2 pointer
- Added C11 "Close-out sweep" habit (evidence-gated proactive tail: passing observations / failure mode / decision-changing next step; empty allowed, cap 3, generic advice banned).
- Added advisory pointer in 30-judgment.md R2 (explicitly marked non-invariant after config-self-audit).
- Audit: config-self-audit passed; contradiction grep clean (10-command-loop report format and 05-authority close-out duty are complementary).

## 2026-07-19 — ops-health maintenance sweep (S3 trim discipline)
- Global_skill_update.md rotated: entries 2026-06-28..2026-07-10 moved to archive/Global_skill_update-2026-06-28--2026-07-10.md with pointer note (68K -> 24K).
- product-design-thinking frontmatter description slimmed 870 -> 678 chars; trigger detail already covered by skill-trigger-dict.md (verified before trim).
- literature-search-extract SKILL.md 261 -> 250 lines: compressed Known-callers and Reference-map routing lines only; P1-P5 pipeline text untouched (eval-passed content preserved).
- ops/30-judgment.md trimmed under 10K (10482 -> 10185): compressed R8 wording and the C11 pointer, semantics unchanged.
- Verified: hooks/ops_health_nudge.py re-run -> zero findings. Backups in backups/2026-07-19/ (pre-edit 30-judgment/50-coach recoverable from git HEAD).

## 2026-07-19 — project visibility layer 1+2 (PROJECTS.md index, dashboard generator)
- Pain point: no global project index, no enforced human-readable close-out docs, config design state only recoverable via git log.
- NEW references/PROJECTS.md: authoritative project registry (one machine-parseable table row per project; header documents column semantics and maintainers).
- Mounts: workflow-checkpoint SKILL.md new step 6 "Index row update" (refresh row at every checkpoint, covered by checkpoint consent); project-retrospective Step 5 new item 3 "Close-out visibility gate" (row status -> done/archived + README currency check, generate only on consent); ops/60-bootstrap.md SA step 1 reads PROJECTS.md and registers missing rows.
- NEW tools/project-dashboard.py: read-only generator -> references/PROJECTS-dashboard.md (gitignored, regenerable): registry rows + phase-log/tickets parsing + git state + staleness flag (commit newer than checkpoint by >7d) + unclassified-file detection + environment section (skills/hooks/recent commits). Verified: exit 0 on current environment, tolerates non-git project path (PaperLens) and no-ledger projects.
- NEW references/project-visibility-L2L3-eval.md: evaluation of full layer-2 and layer-3 options (build vs graft Obsidian/GitHub/Notion/Backstage vs plugin packaging); external-tool claims explicitly marked unverified.
- Audit: contradiction grep clean; 60-bootstrap.md 9,746 chars (95% of ~10K cap — trim candidate stands).
- Follow-up (same day, user-approved): claude-config registered as a PROJECTS.md row with "ops-relaxation: L1" recorded in its status cell (chosen area — avoids polluting global CLAUDE.md; ops_health_nudge.py deliberately skips home cwd so no mechanism conflict). Generator enhanced: git queries scoped to project subtree ("-- ."), unaccounted-commits list since last checkpoint, file-budget warnings mirroring nudge thresholds. Verified exit 0; warnings correctly surface 4 near-cap ops files + CLAUDE.md at 92%.

## 2026-07-19 — visibility extension M1-M4 shipped (design-verified, user-accepted)
- Design: references/project-visibility-design.md (PIM+PSM, non-author verified, D1-D5 approved). Ledger: references/claude-config-tickets.md (T-002..T-005 done -> Archive; T-001 packaging stays blocked until a 2nd project completes a full cycle).
- tools/project-dashboard.py rewritten: collect -> ViewModel (schema v1) -> renderer registry (md/html/readme-draft). Fixtures passed: INV-3 partial failure, INV-4 import allowlist, INV-5 html.escape. README drafts write README.draft.md only (promotion is manual).
- workflow-checkpoint SKILL.md step 6: dashboard regen mounted after index-row update (non-blocking on missing Python).
- tools/open-dashboard.bat: user-requested quick entry (regen + auto-open HTML), verified end-to-end.
- .gitignore: PROJECTS-dashboard.html + **/README.draft.md added as derived views.

## [2026-07-25] File-output language rule → 4-class by primary consumer + product-design-thinking restructure

- Trigger: user observed that recent PSM/施工卡 documents (DIT R8 workcards, R7B baseline) came out fully Chinese despite build-spec intent. Root cause diagnosed, not a trigger miss: the old `File output` rule's stated axis was "who reads it" but its examples split by artifact type (all code-like on the English side), so any prose `.md` under `docs/` was pulled to Chinese. No project CLAUDE.md in DIT and no language section in product-design-thinking → both lower layers silent → global default won.
- `CLAUDE.md` File output rewritten from a 2-way to a 4-way split, axis restated as PRIMARY CONSUMER: human-read (Chinese) / machine-read (English, now explicitly naming phase log + `references/<project>-context.md` + retrospective's CLAUDE.md snippet, which had their own English contracts) / **build spec an agent will execute** (English spec body, Chinese only on the user's ruling surfaces: 盤點結果, ADR rationale, decision register, manual UAT, degradation declaration, open questions) / **concept-level design docs** (bilingual: Chinese semantics + rationale, English glossary/INV-n/schema/state names). Escape hatch for concepts whose Chinese wording carries the meaning.
- `product-design-thinking` restructured per skill-creator progressive-disclosure guidance: SKILL.md 245 → 111 lines (config-self-audit's ~150 budget, previously flagged as pre-existing debt on 2026-07-16). Detail externalized to NEW `references/prior-art-sweep.md` (58), `references/design-rules.md` (68, incl. security-by-design), `references/document-ladder.md` (95, incl. sole-source contract rules). Language integrated as a **column of the ladder table in the always-loaded body** rather than an appended section — the miss happened because the rule was absent where the ladder is read. Frontmatter description unchanged (coupled to skill-trigger-dict.md).
- Coupling fixes from the config-self-audit pass: `OPERATOR-GUIDE.md` §1.5 language bullet now points at CLAUDE.md instead of restating a stale 2-way version; `ops/60-bootstrap.md` §F work-card field-ownership list gained a **Language** row (its silence on language was the mechanism that let cards default to Chinese); §-number cross-refs repointed to `references/document-ladder.md` §4 in `ops/60-bootstrap.md` and `ops/lessons.md`.
- Interop sources updated in a follow-up (same day, user-requested): `portable-core.md` `block:language-output` carries the 4-class split in agent-neutral English (no platform/skill/path references, per that file's content policy); `refs/design-protocol.md` Phase 3 gained a per-rung language table plus the "a PSM's next reader is the implementing session" rationale. The stale generated `AGENTS.md` was archived to `archive/2026-07-25-agents-md-stale-mirror/` rather than hand-synced; user re-runs `interop.py build`.
- **Curation NOT marked done.** `interop.py status` reports curation sources changed across **13 commits** since the last curation (`c99c33e`) — this batch is 2 of them. The other 11 (visibility mounts, relaxation gate, glossary maintenance, R2/R8 judgment trims, sole-source rules, checkpoint self-check…) have never been reviewed against `portable-core.md`/`refs/`. `interop.py curated` was deliberately not run: marking curation complete would claim a review that did not happen. A dedicated curation pass is owed. Also pre-existing: `refs/design-protocol.md` still lacks the sole-source contract rules that landed in the canonical skill on 2026-07-12, and `~/.codex/AGENTS.md` is `[foreign]` (exists, not interop-managed).
- Verification: 3 reference files `test -f` OK; all SKILL.md `references/*.md` pointers resolve to existing files; root `AGENTS.md` confirmed absent; no other cross-reference to the moved sections remains (repo-wide grep, excluding backups/archive/memory-archive). Backups: `backups/2026-07-25/`.
- Not run: skill-creator's eval/benchmark loop (needs subagent dispatch + user review; offered, not executed).

## 2026-07-25 — config-self-audit made self-sufficient; /doctor demoted to optional input
- Trigger: measured the official `/doctor` (CLI 2.1.220) against this skill by extracting its
  full prompt from the binary and running it headless (`claude -p "/doctor"`, write tools
  disabled). Analysis: `reports/2026-07-25-doctor-vs-config-self-audit.md`.
- Finding that drove the change: `/doctor`'s headline result was a false positive — a hook
  reported timing out on 217/220 tool calls whose script had been archived 18 days earlier
  (events dated 07-03/04, claimed window 07-20..07-25). Root cause: its scan window is keyed
  on transcript file mtime, not event timestamp. Measured skew here: 20 of 50 files >=3 days,
  max 26 days (43 files / max 25 days over a 30-day window).
- SKILL.md rewritten (120 -> 173 lines): removed the "Harness-level pre-step" block that
  routed disuse questions to `/doctor`; added "Order of operations" (section 2 is a gate that
  voids any finding referencing a non-existent path); section 2 gains duplicate/variant-collision
  key detection and CLI startup-warning capture; section 3 gains a permission-posture rule
  (defaultMode/allow/ask never batch-consented; decline `auto` when ask-rules guard config);
  section 4 gains cross-surface duplicate detection (plugin namespaces + desktop skills cache);
  section 5 gains local usage measurement and the on-demand vs routine intent rule; NEW section 7
  telemetry window integrity; NEW section 8 demotes `/doctor` to lowest-priority optional input.
- NEW skills/config-self-audit/references/telemetry.md: usage-window tool usage, integrity
  one-liners, `/doctor` invocation mechanics (PowerShell required — Git Bash rewrites "/doctor"
  to C:/Program Files/Git/doctor via MSYS path conversion), and 8 measured defects (D-1..D-8).
- NEW tools/usage-window.py (stdlib only, read-only): per-skill / per-MCP / per-hook / denial
  activity keyed on event timestamps, plus an mtime-skew list. Verified: compiles, runs in text
  and --json mode, 139 transcripts scanned.
- skill-trigger-dict.md: config-self-audit's `/doctor` division-of-labour line rewritten to
  match the demotion.
- Self-audit of the change: two defects found and fixed before delivery — (a) the slash-command
  parser in usage-window.py consumed an entire quoted transcript when the closing tag was
  missing; (b) the duplicate-key check as first written found 0 hits on `~/.claude.json` because
  the real problem is case/separator variant collisions (6 groups, 14 entries = 6 projects),
  which JSON treats as distinct keys. Both corrected and re-verified.
- Open item: SKILL.md is 173 lines against its own ">~150 lines, move detail to references/"
  guidance in section 5. Further splitting would fragment the checklist itself; user ruling pending.
- Backups: backups/2026-07-25/ (config-self-audit-SKILL.md.pre-A1A7, skill-trigger-dict.md.pre-A1A7).
  Branch: feat/config-self-audit-selfsufficient (uncommitted at time of writing).

## [2026-07-29] scientific-research-guide: domain expansion synced from external editing copy
- Context: user maintains a duplicate of this skill at `D:\SHARE\CLAUDE_SHARE\skill-toolkit\skills\scientific-research-guide\` for editing outside this environment; asked to verify the copy's new changes against skill conventions, clean up as needed, and sync back.
- Verified against `domains/domain-expansion-guide.md`'s two-gate decision tree and sub-profile mini-template: 6 new domain files (3 under `plasmonic_waveguide/` — 1 sub-profile, 1 reference, 1 boundary note; 4 under `topological_insulator/` — including a content addition to the existing `bi2se3_material.md`) all correctly classified, each active sub-profile has parent link/branch axis/Node 4-6/Decision-Trigger Checklist/Evidence Anchors. `domains/_routing.md` rows match the actual files.
- Copied into canonical: `domains/plasmonic_waveguide/{active_modulation,terminology_and_geometry,split_ring_resonators}.md`, `domains/topological_insulator/{wal_hln_transport,surface_and_composition_characterization,device_fabrication}.md`, updated `bi2se3_material.md` and `_routing.md`.
- Cleanup applied during sync (source content unchanged): the source copy's root-level `INTEGRATION-AUDIT-2026-07-28.md` was relocated to `reports/2026-07-28-scientific-research-guide-domain-integration-audit.md` (skill dirs keep only STATUS/FUTURE-WORK as living docs; ad hoc audit trails belong in `reports/`, per the 2026-07-25 doctor-audit precedent). `STATUS.md` rewritten to reflect the new file set and today's date, and to record three pre-existing (not newly introduced) defects the audit report itself flagged: `domains/topological_insulator.md` base profile truncates right after its "Standard Modeling Toolchain" heading (no Nodes 4-8), still carries 35 `[web:n]` placeholder citations, and STATUS.md's old "all cross-references verified consistent" claim did not account for either — softened. `domain-expansion-guide.md`'s Appendix directory listing (previously illustrative placeholder filenames) rewritten to the actual current file layout.
- Not fixed (flagged only, out of scope for this sync — user has not asked for a `topological_insulator.md` repair): the truncated base profile and its `[web:n]` citations.
- config-self-audit run after the sync (see its own findings, if any, appended separately or by the invoking session).

## 2026-07-29 — dangerous_command_guard hook (new)
- Added hooks/dangerous_command_guard.py: PreToolUse deny-list for destructive Bash/PowerShell commands (recursive-force deletes outside temp, git push --force / reset --hard / clean -f / whole-tree discard, registry writes, machine-state commands). Fail-open; escape marker [user-approved-destructive].
- settings.json: registered the hook (matcher Bash|PowerShell) and widened permissions.allow with 13 evidence-based entries from a 50-session transcript scan (git add/commit, mkdir, npx vitest/tsc/oxlint, npm test, 5 read-only Claude_Browser MCP tools).
- Verified: 34/34 hook test cases passed; settings.json parses; config-self-audit run (no blocking findings).

## 2026-07-31 — scan-contract adoption (security-deep-checklist + code-review-deep-checklist)
- security-deep-checklist: new references/scan-contract.md (findings/coverage JSON manifests, ruleId+anchor+instance→fingerprint identity, three evidence receipts w/ deferred discipline, inventory-first coverage dispositions, Part 0 ↔ SECURITY-POLICY.md policy layer). SKILL.md: Part 0 item 0, output-contract pointer, handoff boundary, reference entry.
- code-review-deep-checklist: new references/output-contract.md (light contract: identity + inventory-first coverage only; no receipts pipeline). SKILL.md: output-contract pointer, coverage-from-manifest line, sec.* discovery-candidate boundary, reference entry.
- Source: openai/codex-security _bundled_plugin (scan-contract.md, findings/coverage schemas, shared-hard-rules, define-security-policy) — contract borrowed, product (CLI/SQLite/SARIF) not.
- config-self-audit: passed after fixing severity/confidence field-shape mismatch in output-contract.md.

## 2026-07-31 — FSM/state-machine verification added to both deep-checklist skills
- code-review-deep-checklist: single-review.md new section 10 (gated stateful-logic
  consistency: FSM reconstruction from design semantics, transition-table artifact,
  per-state invariants, observability, single-writer, trap/race checks);
  project-review.md new cross-module state-ownership lens; output-contract.md
  ruleId example review.state.*; SKILL.md pitfalls + reference list updated.
- security-deep-checklist: code-audit.md new section 9 (state-machine & business-flow
  attacks: step-skip, replay, TOCTOU race, enforcement desync, cross-context state
  leakage, fail-open transitions, trap-state DoS); scan-contract.md ruleId example
  sec.state.*; SKILL.md pitfalls + reference list updated.
- Verified via config-self-audit; one duplicated partial section (misplaced edit)
  found and removed (commit 95cd1f2). Commits: afb0c28, merge 4f31991.

## 2026-07-31 — cross-boundary contract & twin-logic drift lens (code-review-deep-checklist only)
- single-review.md new section 11 (gated: both-sides check for mirrored contracts,
  canonical-source/derivation question, rolling-deploy compatibility, error-shape
  contract, temporal coupling). project-review.md new "Contract & Twin-Logic Drift"
  lens (boundary-contract + twin-implementation inventories, drift gates,
  architecture fitness functions, documentation-drift spot-check with handoff to
  engineering:documentation / engineering:tech-debt). ruleId family review.contract.*.
- security-deep-checklist deliberately unchanged (attacker-facing projections
  already covered by its sections 1/4/5/9).
- Verified via config-self-audit: sections 1-11 unique, cross-refs resolve,
  SKILL.md 149 lines. Commits: 19b00df, merge on main.

## 2026-07-31 — scale-label qualifier pass (relaxation levels)
- Root cause: bare L0/L1/L2 labels read against the ASVS-style convention
  (higher = stricter) while this scale is inverted; owner misread L2 as a
  permission level. Also found (L2)/(L3) reused for a different scale in
  70-evolution.
- Changes: direction + precedence-orthogonality paragraphs in 05-authority s2;
  glosses at both gate-ask sites (global CLAUDE.md line 41, 60-bootstrap sA);
  scale-label qualifier rule in 40-maintenance s3 birth budgets; 70-evolution
  renamed to (layer 2)/(layer 3); lessons L-008 (plus L-005..L-007 committed).
- Audit: collision grep clean; all remaining L-label use sites carry a
  relaxation qualifier or sit in the defining file. CLAUDE.md at 12,842 chars —
  pre-existing over-budget (>12K), trim pass pending as a separate task.
- Backups: backups/2026-07-31/. Commit 24d12b5.

## 2026-08-02 — motion-design imported into this share (Three.js content excluded)

- Source: `~/.claude/skills/motion-design/`, exported via `skill-share-packaging`
  Mode A conventions (prescan + grep checklist on the copy, canonical skill
  left untouched).
- `vendor/lottiefiles/` copied verbatim — MIT with LICENSE and named copyright
  holder, no issue.
- `vendor/threejs/` (upstream `cloudai-x/threejs-skills`) deliberately **not
  copied**: the canonical environment's own `Global_skill_update.md` entry for
  this skill (2026-08-01) recorded that upstream's license defect — no
  `LICENSE` file, no named copyright holder — as "blocks redistribution until
  upstream fixes it." This share honours that ruling. `SKILL.md`, `NOTICE.md`,
  and `local/currency.md` were adjusted to point at the upstream URL instead
  of reproducing the text, and `local/env-bridge.md`'s hardcoded
  `D:\AIWork\AssetVault\registry.json` path was generalized (machine-specific,
  and pointed at a skill — `asset-vault` — not included in this share).
- `skill-trigger-dict.md`: new 動效與 3D section + 3 disambiguation rows,
  ported from the source dictionary (no personal paths in that section).
- `asset-vault` itself was NOT imported this round (tied to a separate
  in-progress project; deferred by request).

## 2026-08-06 — scientific-research-guide: GaN power/microLED domains + Bi2Se3 plasmonic sub-profile + citation inbox (refresh from source)

- Source: `~/.claude/skills/scientific-research-guide/`, refreshed to match the
  canonical environment's 2026-08-03 domain-expansion sync. Changed/new files:
  `SKILL.md` (+reference-file index entry, +citation-triage delegation note),
  `STATUS.md` (changelog + updated Structure section), `domains/_routing.md`
  (+2 base rows, +1 sub-profile row), `domains/domain-expansion-guide.md`
  (+§3.1 swappable-slot convention for optional external tools, updated
  Appendix tree), `domains/gan_power_device.md` (new base profile: vertical
  GaN trench MOSFET/OG-FET/CAVET, field-shield design, TCAD, electrical
  extraction), `domains/microled.md` (new base profile: InGaN blue-green +
  AlGaInP red microLED size/sidewall effect, recombination, optical
  extraction), `domains/topological_insulator/bi2se3_plasmonic_photoresponse.md`
  (new method sub-profile: Dirac/bulk/2DEG plasmon channels, CPGE/LPGE,
  waveguide-coupled photocurrent), `domains/topological_insulator/
  bi2se3_material.md` (+cross-reference, no content duplication),
  `domains/plasmonic_waveguide.md` (its `Notes for AI use:` terminology-vault
  line rewritten as a swappable slot per the new §3.1 convention — the source
  environment's own fix for a hardcoded personal path, carried over verbatim
  since it removed the identifier rather than introducing one),
  `references/user-supplied-citations.md` (new: source-provenance inbox for
  user-supplied URLs), `workflow-checkpoint/SKILL.md` (+journal sweep step,
  +premise re-confirmation on resume — see the ops entry below for the
  matching rule-set).
- Review scope: usernames, local paths, account/machine identifiers. Result:
  none found in the synced content itself. This round's source-side drafting
  had used this very share's `scientific-research-guide/` directory as an
  isolated editing copy; the leftover raw-notes packet (`material/`) and its
  verification report (`MATERIAL-INTEGRATION-VERIFICATION-REPORT.md`, which
  names local machine paths) were moved to `scientific-research-guide/archive/`
  — fully superseded by the integrated domain files above, and excluded from
  git via `.gitignore` (contains machine-specific paths; see the archive's own
  README).
- This is a point-in-time snapshot, not a synchronization target.

## 2026-08-06 — Premises / refutability / know-why / record-schema rule-set (ops + global CLAUDE.md + PHILOSOPHY.md)

- Source: `~/.claude/ops/{05-authority,10-command-loop,30-judgment,
  40-maintenance,60-bootstrap,OPS,lessons,rules-usage-dict}.md` +new
  `ops/60-record-templates.md`, `~/.claude/CLAUDE.md`, `~/.claude/PHILOSOPHY.md`,
  refreshed to match commits `9a67cbe`..`f8a9c69` (2026-08-06).
- Content: a new premise-gate + refutability-statement duty (`30-judgment.md`
  R2/R8, `05-authority.md` §4 boundary contract gains a "Premises" section,
  4→5 sections / 15→18 line cap), a per-project Decision & Process Journal
  (`60-bootstrap.md` new §G, know-why layer between ADR and a ticket's
  one-line note; templates extracted to the new `60-record-templates.md`),
  a record-type schema registry (`rules-usage-dict.md` new §7), a
  `workflow-checkpoint` journal-sweep + resume-time premise re-confirmation
  step, a `lessons.md` L-009 entry (browser-pane screenshot timeout
  misdiagnosis — DOM-read tools keep working over CDP while the screenshot
  tool times out when the page reports itself hidden), and an ops-file
  size-trigger raise (~10K→~12K chars, same "lossless trim capped out short
  of the old cap" pattern as the 2026-08-01 CLAUDE.md 12K→15K raise).
  Global CLAUDE.md gained the matching premises&refutability bullet, the BC
  5-section/18-line sync, and a generalized (tool-name-free) version of the
  L-009 screenshot-detection rule — kept portable rather than naming this
  environment's specific tool set, consistent with how this share already
  treats the Environment/OS-shell rule.
- Review scope: usernames, local paths, machine identifiers. Result: none
  found in the synced content; the `lessons.md` L-009 entry references only
  generic tool behavior (screenshot capability, page-visibility state, DOM
  read tools), not a specific product name, so it was carried over as-is in
  `claude-ops/`.
- This is a point-in-time snapshot, not a synchronization target.

## 2026-08-07 — Environment recency + main-loop terminology + audit-entry schema
- **trigger**: external reader review of the 2026-08-06 rule round raised two
  objections, both re-verified in-session against the files. (1) `environment.md`
  carried one file-level `Verified on 2026-07-07` while its own body recorded a
  2026-07-10 fact, and asserted "settings.json pins haiku ⇒ the dispatcher is a
  non-frontier model" — `settings.json:34` still said `haiku` while the session
  ran Opus 5, so `05-authority.md` §2's "L0 applies automatically when the main
  model is cheap/mid" was branching on a stale inference (decision-affecting,
  not cosmetic). Also four spellings in circulation (main session / main model /
  main-session model / 主 session) with tier attached to *session*, and
  30-judgment's rule-class line ordered R2/R5/R7 → R1/R4/R6/R8 → R3. (2) Entries
  in this log list files and sections but not what the rules now say vs said —
  root cause found: `rules-usage-dict.md` §7 registers minimum fields for 11
  record types, and this log's own entries were the only unregistered one.
- **change (before→after)**:
  - `environment.md`: single header date → per-block `as-of` lines + an invariant
    banning file-level dating. Cap table retitled "Subagent cost cap" with an
    explicit "says nothing about which model the main session runs"; the row note
    `cheap | haiku | Default main-session model` → `Lowest-cost dispatch tier`.
    Section "Main-session model" (static inference) → "Main-loop model — READ IT,
    never infer it": 3-step procedure (take tier from the session's stated
    identity; `settings.json` is a *fallback* marked "assumed"; never derive it
    from this file's prose) + the §2 consequence spelled out. Refresh triggers
    now per-block, plus a ~90-day sweep.
  - Terminology fixed at the category slip, not by mass rename: **main session** =
    top-level session (no tier), **main-loop model** = the model it runs on (has
    the tier). `30-judgment.md`:5 was "advisory for a frontier main session" →
    "advisory only when the main-loop model is frontier-tier AND the user granted
    L1/L2"; same line's rule classes reordered to R1..R8 numeric. Parallel fixes:
    `05-authority.md` (header, §1 scaffolding, §2 gate, §3), `60-bootstrap.md`:23,
    `30-judgment.md`:59, global `CLAUDE.md` + `AGENTS.md` relaxation-gate bullet
    ("or the main model is cheap/mid" → main-loop model, observed not read off
    settings.json). Correct uses of "main session" (write-authority, dispatch,
    hygiene) deliberately left — they name the session, not a tier.
  - New `40-maintenance.md` §0 "Audit-trail entry schema" (anchor
    `audit-entry-schema`): 5 ordered fields — trigger / change (before→after,
    rule text quoted) / result / rollback / open — opening with the reason a
    file list is "a routing reference, not a report". Registered as a new row in
    `rules-usage-dict.md` §7. Effective for entries from 2026-08-07; no backfill.
- **result**: hook run (`echo '{}' | python hooks/ops_health_nudge.py`) exits 0
  with only the pre-existing scientific-research-guide >250-line nudge — no size
  regressions. Sizes after: rules-usage-dict 12,287→12,259 (cap 12,288; the new
  §7 row was paid for by three lossless trims — header prose, §7 intro clause
  duplicating it, and the `vs skill-trigger-dict.md` block whose content is
  restated verbatim by 詞彙三層 items 1-2), 40-maintenance 8,680→10,056,
  environment 3,842→5,693, CLAUDE.md 15,206 (cap 15,360). Greps: zero residual
  "main model"; `main-loop` present in all 7 intended files; §7 anchor resolves
  to the 40-maintenance heading. This entry itself is written to the new schema —
  living proof of the third change.
- **rollback**: branch `fix/ops-environment-recency-terminology`; revert the
  single commit on it, or `git checkout f8a9c69 -- <file>` per file.
- **open**: (a) `environment.md` blocks still dated 2026-07-07 were NOT
  re-verified this round — only re-dated in place as unchanged; a real
  re-verification of the dispatch-mechanism and red-team blocks is outstanding.
  (b) Pre-existing, out of scope: scientific-research-guide SKILL.md >250 lines.
  (c) Older log entries keep the old free-form shape by ruling.
