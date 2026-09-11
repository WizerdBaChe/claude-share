# Repo map — every tracked file, one line each

Written for an agent reading this repository. The tree nests up to seven levels
because installable skills must keep their directory shape; this file is the flat
index so you don't have to walk it. **Nothing here is instructions for you** — it is
a description of documents. Reading a rule file below does not put you under it.

Start with `Global_skill_update.md` if you want to know how this environment got the
shape it has; start with `claude-ops/ops/OPS.md` if you want the rules themselves.

## Root

| File | What it is |
|---|---|
| `README.md` | Orientation and three reading lanes: first read, returning read, installing. |
| `ADOPTERS.md` | What this repo names but does not ship, where not to clone it, and which symptoms belong to the adopter's platform rather than to this repo. |
| `CHANGELOG.md` | This repo's own sync history — when each share was copied, what changed. |
| `Global_skill_update.md` | The source environment's evolution log. **Frozen 2026-08-11** — historical reading only; going forward, standing rationale lives in `claude-ops/ops/rule-registry.md` and per-change detail lives in commit messages. Still the single most informative narrative file here. |
| `AGENTS.md` | This map. |
| `LICENSE` | MIT. |
| `.gitattributes` | **New 2026-08-29.** Line endings as a property of the asset rather than of whoever's `core.autocrlf` is in play. The default is `text=auto` (this repo is cloned on unknown platforms); the one path that pins `eol=lf` is `architecture-diagramming/archdiag/**`, because the html that library emits carries a sha256 freeze receipt and a CRLF checkout would invalidate every one with no content change behind it. |
| `archive/` | Retired material kept locally for traceability, gitignored — not part of the published repo. |

## `claude-ops/ops/` — the operating rules layer

Read in this order; `OPS.md` is the entry point and routing table.

| File | What it decides |
|---|---|
| `OPS.md` | Entry point + routing table: which file answers which question. |
| `05-authority.md` | Rule classes (invariant vs scaffolding), the per-project relaxation gate L0/L1/L2, and the boundary contract. |
| `10-command-loop.md` | The step sequence for handling any non-trivial instruction. |
| `20-dispatch.md` | Delegating to subagents: when, at what model tier, with what prompt contract. |
| `30-judgment.md` | Eight rubrics: when to escalate, when something is "done", when to ask, when the method itself is wrong. |
| `40-maintenance.md` | How to change the rules safely: write tiering, trim discipline, audit-entry schema. |
| `50-coach.md` | Metacognitive habits for a non-frontier model driving the loop. |
| `60-bootstrap.md` | First session in a project: environment facts, ticket ledger, work cards, decision journal. |
| `60-record-templates.md` | Full templates for the record types `60-bootstrap.md` governs. |
| `70-evolution.md` | Proposing changes to hooks/settings; whether something belongs in rules or memory. |
| `environment.md` | Machine-specific facts, per-block dated. Subagent cost cap, dispatch mechanisms, browser-pane UI verification, instruction-loading mechanics. |
| `lessons.md` | The pitfall ledger — real incidents with the fix that followed. |
| `rule-registry.md` | **New 2026-08-11.** Keyed by RULE, not by date: why each size cap, standing ruling, and mechanism holds its current value, plus its value history. Replaces the old chronological-rotation model. |
| `rules-usage-dict.md` | Index: which layer owns what, record-schema registry. Agent-roster routing itself moved to `20-dispatch.md` — this file keeps only a pointer. |
| `../references/PROJECTS.md` | **New 2026-08-14.** The project-index format the ops layer and two skills cite — header and column semantics only; the source environment's rows are its own inventory and do not ship. |
| `references/` | Detail files for the rule above them, loaded on demand and never at session start — the landing zone when a rule file hits its size cap. `inbound-routing.md` (what arrives from outside, and which procedure it gets), `integrity-sweep.md` (the executable grep checks behind `40-maintenance.md` §5), `project-map.md` (the read-time layer behind `60-bootstrap.md` §H), and **new 2026-08-16** `external-dispatch.md` (the detail behind `20-dispatch.md` §4a — measured prompt shape, acceptance layers, failure signatures; the dispatcher itself is not shipped, but since 2026-08-17 its acceptance layers ship as running code in `red-team/`) and `skill-trigger-classes.md` (why a skill's zero fire count is or is not a defect). **New 2026-08-29**, both because the same round's refresh replaced shipped prose with pointers to them: `dispatch-templates.md` (the worked ✅/❌ contract pair and the five task-template field lists that used to sit inline in `20-dispatch.md`) and `shared-tree-git.md` (the concurrency discipline behind L-023 — the routing ruling by coupling class, the commit ritual in full, and what each kind of shared-state damage looks like, including the mitigation that turned a LOUD failure into a silent one). |
| `README.md` | Folder note. |

## `global-claude-md/` — the always-loaded preferences file

| File | What it is |
|---|---|
| `CLAUDE.md` | The global preferences the ops layer hangs off. Machine-specific values are `<PLACEHOLDER>`s — substitute your own. Opens with a "Path-scoped rules" index pointing at `rules/`. |
| `rules/frontend-layering.md`, `rules/shader-failure-modes.md` | **New 2026-08-11.** Two rules sunk out of CLAUDE.md's body into path-scoped files (only load when a matching file is read) — FSD module layering and GLSL silent-failure modes. |
| `README.md` | Cross-reference map back into `claude-ops/`. |

## `skill-toolkit/` — installable skills

`skill-trigger-dict.md` is the disambiguation index; each `skills/<name>/SKILL.md` is
self-contained, with detail in its own `references/` loaded on demand.

| Skill | For |
|---|---|
| `ai-coding-guardrails` | Designing the guardrail *system* around AI coding agents (5 references). |
| `audience-fit` | **New 2026-09-02.** Post-production audience tuning: rewriting an engineer-voiced deliverable for a non-developer reader, or moving UI copy from the builder's view to the user's. One document serves one primary audience, and the rewrite ships paired with the original — evidence strength, causal register and stated limits may not shift in the retelling. |
| `code-review-deep-checklist` | Deep/holistic code review: single review, project health, dependency fitness. |
| `config-self-audit` | Auditing one config artifact — a skill, hook, or rule — cheaply. |
| `design-system-suite` | Design tokens and contracts across a multi-product frontend suite. |
| `diagram-authoring` | **New 2026-08-27.** Precision diagram production & gap finding: structural text model first, geometry self-check asserts, a fabrication firewall, mandatory gap report. The production third of the `architecture-diagramming/` capability set; its theory lives in two `product-design-thinking` references it cites rather than copies. |
| `env-cleanup` | File-level cleanup of a config environment or project tree; archives, never deletes. |
| `literature-search-extract` | Finding scholarly sources and extracting into evidence tables, with citation traceability. |
| `mechanism-share-packaging` | **New 2026-08-17.** Exporting a behavioural MECHANISM — an operating mode spanning hooks, tools, wiring and docs — into a governed share repo: scope it as a runtime, land each file where the target's structure says, sweep the ripples arrival causes, loop the target's gate. Delegation is its first hard rule — the target repo's collection rules stay authoritative and are never restated inside it. `compact-recovery/` and `red-team/` are its two live runs. |
| `motion-design` | Motion/animation methodology + Three.js. `vendor/lottiefiles/` is third-party MIT, verbatim. |
| `product-design-thinking` | Heavyweight design mode for a new product: prior-art sweep, then build-ready docs. |
| `project-retrospective` | End-of-project extraction of lessons into a guide + rules snippet. |
| `scientific-research-guide` | Research-methodology advisory. **Domain profiles excluded from this share** — see `domains/README.md`; the template, manifest format, and expansion spec ship. The eval suite left with them 2026-08-27 — it had become the withheld profiles' routing test harness (manifest `[[not_shipped]]` carries the reversal). |
| `security-deep-checklist` | Defensive security audit: code, deployment posture, detection readiness. |
| `skill-co-upgrade` | **New 2026-08-16.** Field-test loop: run a real task through a skill, collect gaps under "a gap exists iff the executor had to BYPASS the skill to do it right", verify every citation, hand off via disposition files. |
| `skill-share-packaging` | Exporting a skill for others, or auditing a downloaded one. Includes `scripts/prescan.py`. |
| `ux-walkthrough` | **New 2026-09-07.** Task-level UX walkthrough of an existing or designed interactive surface: can a specific person find the entry, predict each action's consequence, wait/cancel/recover, and come back next time — on keyboard and narrow layout too. Output is executable findings plus show/disable/hide rulings and a wait-cancel-recovery contract. The instrument behind `product-design-thinking`'s "UX semantics are the user's decision"; hands wording work to `audience-fit` and takes it back. |
| `workflow-checkpoint` | Phase archiving and context rebuild across long multi-session projects. |

## `hooks/` — the mechanical enforcement layer

Collected 2026-08-14, extended on 2026-08-16, 2026-08-29 and 2026-09-07.
**Eighteen hooks** across PreToolUse / UserPromptSubmit / SessionStart /
PreCompact / PostCompact / SubagentStop / InstructionsLoaded — the enforcement
layer the ops rules had been citing without ever shipping it; all fail-open,
none machine-bound. Install steps and the per-hook table are in
`hooks/README.md`; `settings.example.json` is the mounting template with
`<PYTHON_EXE>` / `<CLAUDE_HOME>` to substitute, and it mounts every hook that
ships. Two `.py` files are deliberately outside that rule and neither is a
defect: `tests/` is a regression matrix run by hand, and
`handoff_snapshot.py` is a shared library the compact-recovery hooks import —
it has no event to mount at. Both exemptions are declared in
`tools/share-manifest.toml` and checked, so neither can quietly become a hook
nobody wired up.

| File | Enforces |
|---|---|
| `dangerous_command_guard.py` | Deny-list for irreversible shell commands (the compensating control for a widened allowlist). |
| `model_cap_guard.py` | Subagent model cost cap, with the SendMessage-resume bypass documented rather than hidden. |
| `ui_verify_guard.py` | Browser-pane measurement discipline (lessons L-009/L-010) — denies, does not warn. |
| `browser_pane_scope_guard.py` + `browser-pane-allowlist.json` + `browser-pane-blocklist.json` | Records every pane navigation; **allowlist** since 2026-08-14 — loopback is allowed by the hook, everything else is denied and handed to an out-of-process route. The blocklist stays for its recorded crash reasons, which make a denial specific (L-013). |
| `ops_health_nudge.py` | Thirteen maintenance thresholds at session start; silent when healthy. |
| `delivery_gate_shadow.py` | Shadow mode only — measures what a delivery gate WOULD block before anything is blocked. |
| `context_runway_shadow.py` | **New 2026-08-16.** Shadow: long context *and* no checkpoint written yet. The conjunction is the trigger — context alone fires in 65% of sessions at 150k, the pair in 26%. |
| `fieldwork_threshold_notice.py` | **New 2026-08-16.** Shadow: main-session Read/Grep/Glob measured against `20-dispatch.md` §1's literal thresholds. High-volume matcher — read its cost note before mounting it. |
| `instructions_loaded_logger.py` | Observation only: which instruction files load, when. |
| `compact_bookmark.py` | **New 2026-08-16.** PreCompact half of the compact-recovery bridge: bookmarks the pre-compact transcript (path, line count, trigger), then best-effort refreshes digest cards. |
| `compact_pointer.py` | SessionStart("compact") half: injects a ~130-token pointer card — digest-first recall ladder, exact pre-compact region, the two recall triggers. |
| `transcript_read_guard.py` | Deny on unbounded Reads of large session RECORDS; identity is by SHAPE since 2026-08-29 (`.jsonl`, or `.md` under `digests/`), so the caches and PDFs sharing those directories read freely — the fix for two measured false denials, with the decision table, the tested bypasses and the deny-message contract all in its docstring. The quartet's overview lives in `compact-recovery/README.md`. |
| `compact_loss_record.py` | **New 2026-09-07.** PostCompact recorder: appends one row per compaction (trigger, snapshot presence, snapshot age at compaction) to `compact-loss.jsonl`, and nudges when the summary arrived with no snapshot behind it. It only records — it never denies. Ships with its audit half missing, stated plainly in `compact-recovery/README.md` rather than left for the adopter to discover. |
| `handoff_snapshot.py` | **New 2026-09-07. Not a hook** — the shared library the three above import (`snapshot_path`, `is_fresh`, `notice`). It has no event to mount at; removing it breaks all three, which is what `compact-recovery/ACCEPTANCE.md` item 9 checks. |
| `tests/test_transcript_read_guard.py` | **New 2026-08-29.** That guard's regression matrix — 22 cases including every alias form (8.3 short name, `\\?\` prefix, junction) and every accepted bypass. Run by hand; not a hook, and deliberately not mounted. |
| `shell_transport_guard.py` | **New 2026-08-29.** The Bash tool's three SILENT transport defects: backslash-run collapse (annotates — a 5,113-call backtest found 89 of 112 hits were the author already compensating, so the gate cannot determine intent), the ~7.7 KB size ceiling (denies — 7 of 7 corpus hits already failed), and MSYS `/flag`→path rewriting (annotates). Persists the full command before any denial. |
| `ps_errorpref_guard.py` | **New 2026-08-29.** `$ErrorActionPreference='Stop'` governing a native exe — wrong in both directions at once (fires on a harmless stderr line, misses a non-zero exit). Annotates, never denies. Mounted on `Write` because that is where 47 of 53 real payloads arrived, not on the tool the ticket asked for. |
| `ps_pipeline_close_guard.py` | **New 2026-08-29.** `\| Select-Object -First N` closes the pipeline and KILLS the upstream process; the output looks truncated for its own reasons and the exit code says failure, so both halves point away from the cause. Its backtest put the surface on `PowerShell` — the opposite of its sibling's, which is why each was measured rather than copied. |
| `branch_commit_guard.py` | **New 2026-08-29.** A `git commit` into a checkout inside `~/.claude` must land on `main` unless the command carries `[branch-ok]` or the worktree has opted in. The compensating control for two same-day incidents where the prose ritual RAN and did not gate — it was a non-gating spectator in a `&&` chain. Carries its own incident log and false-positive count. |

Ten of the source's twenty-nine hook-layer files are deliberately **not** here,
and `tools/share-manifest.toml` carries a disposition for every one. Two gate an
external-dispatch entry point this repo does not ship; `session_board_register.py`
and `project_registry_gist.py` are each one half of a source-environment tool
(the ticket board, the project registry) whose other half is not a rules asset —
and `20-dispatch.md` §7a carries the share note saying its registration is done
by hand here. `secret_file_guard.py` is one operator's own file list.
`xi_card_guard.py` (with its test) shadows a cross-index pipeline this share does
not carry. **New 2026-09-07:** `intake_guard.py` and `intake_match_shadow.py` are
the deny guard and shadow probe for the lesson-intake store — shipping the guard
without the CLI it points at would block writes to a path this repo does not even
have; and `unattended_run.py` mounts three times for the `[unattended-run]`
carrier, whose Stop guard blocks on a report only a tool outside this repo can
generate. `settings.example.json` mounts every hook that ships and nothing else,
with the two not-a-hook exemptions named above; that is the invariant to re-check
whenever this table changes, and check S5 of the gate is what re-checks it.

## `compact-recovery/` — post-compact recall as an operating mode

New 2026-08-16, extended 2026-09-07. Not a single tool but one mechanism
spanning six files: the four compact hooks above (three mounted plus the shared
library they import) and the digest generator here. What a `/compact` summary
drops stays recoverable at on-demand token cost; the one move that would
re-inflate context — a wholesale re-read — is structurally denied.

| File | What it is |
|---|---|
| `README.md` | The operating mode (中文): event-pair bridge, recall ladder, token economics, install steps incl. the optional SessionEnd mount, tunables table, platform-contract re-check recipes, de-identification notes. **2026-09-07:** the handoff-snapshot and loss-record halves, and a named gap — the recorder ships without its audit tool, so the `compact-loss.jsonl` it writes has no reader here. |
| `ACCEPTANCE.md` | Nine-item real-fire checklist (中文), plus what the source environment already verified on 2026-08-16 — including a full-chain live compaction. Item 8 carries a negative control; item 9 checks that removing the shared library breaks the other three, which is the only way the not-a-hook claim is testable. |
| `preserve.py` | Transcript archiver + mechanical digest-card generator (stdlib-only, HOME-relative). The one file of the source's 279-file memory-pipeline product that ships; the rest stays not-shipped — see the manifest. |

## `red-team/` — machine-checkable adversarial review

New 2026-08-17. The second mechanism export, and the answer to a question
`agents/engineering-code-reviewer.md` alone does not close: when a model says "there is a
bug here", what makes that claim expensive to fabricate? A prompt shape, a
six-layer acceptance ladder, and the four layers of it that are code. Layers
2–4 run with no model and no dispatcher at all; layer 5 takes one by name.

| File | What it is |
|---|---|
| `README.md` | The operating mode (中文): the ladder as a data-flow diagram, the measurement behind each design choice, three ways to wire it (local subagent / external tier / hybrid), the dispatcher contract, a tunables table, per-part failure modes, de-identification notes. |
| `ACCEPTANCE.md` | Two-part checklist (中文): section A is mechanical and blind-runnable with no model — five items, all re-verified on this copy 2026-08-17; section B needs a real model and stays open in the adopter's environment, with the source's own numbers beside each item. |
| `score_redteam.py` | Layers 2–4: structure, anchor, scope, spot-check. Separates a CITATION error (verbatim quote, wrong line — repaired) from a FABRICATION (quote appears nowhere — voids the report). Stdlib-only. |
| `jsonspan.py` | The one JSON-span extractor for the whole layer. Exists because the same scanner had been written three times and the copy in the *structure* gate was the one never fixed. |
| `redteam_verify.py` | Layer 5: one refuter per finding, verifier ≠ author enforced. Three outcomes, and `inconclusive` is load-bearing — tool failure is not evidence about a claim. The only file here with a behavioural share edit: it loads a dispatcher by name instead of importing the source's. |
| `test_score_anchor.py` | Ten cases. Two of them are the regression guard for the day this layer was *loosened* — an invented quote must still void the report. |
| `test_parser_rulers.py` | Eight cases mapping where a greedy `{.*}` regex fails and a balanced scan does not. |
| `prompts/redteam-v2.txt`, `prompts/redteam-v2.1.txt` | The prompt as an instrument: format instruction first, evidence anchor per claim, explicit file scope, and a written licence to return `[]`. Templates — `<COMMIT_SHA>` and four `<FILE_UNDER_REVIEW_n>` are yours to fill. |

The dispatcher that sends these prompts is still **not** here, and the
`tools/extdispatch/` manifest entry — narrowed from `excluded-by-decision` to
`partial` on the day this folder was born — says per file what stayed behind
and why. The method-level write-up remains
`claude-ops/ops/references/external-dispatch.md`; this folder is that document's
executable half.

## `architecture-diagramming/` — the diagram capability set, packaged for verification

New 2026-08-27. The third mechanism export, and the first whose parts live in
`skill-toolkit/skills/` rather than beside the map: theory (two
`product-design-thinking` references — view selection, integrity instrument),
production (`diagram-authoring`, collected the same day), audit
(`code-review-deep-checklist` Mode B's view layer). This folder is the
integration map plus the checklist that lets an outside verifier test the SET
rather than three skills separately.

| File | What it is |
|---|---|
| `README.md` | The capability set (中文): three independent failure shapes of architecture diagrams, the two-entry loop (design entry / audit entry), file-and-ownership table, install set with its side-by-side requirement, notation coverage grid (incl. Petri-slice ownership), failure modes when a part is missing, de-identification notes. |
| `ACCEPTANCE.md` | Fourteen-item blind-runnable external checklist (中文): trigger/routing probes incl. a negative one, theory/production/audit items, stress items on the fabrication firewall — plus what the source environment verified 2026-08-27 and which evidence cells stay open (PPTX carrier, BPMN branch, two never-live-fired probes). |
| `archdiag/` | **New 2026-08-29 — the set's executable half.** Twelve files: the audit-drawing library the `diagram-authoring` skill routes to for precision view sets. `index.mjs` is the pipeline (schema → build-time geometry asserts → marker closure → deterministic emission → sha256 receipt); `selfcheck.mjs` is the SINGLE source of the in-page check script, which is the whole point — per-file copies of it drifted within one day, and that drift is what the library exists to kill. `route.mjs` is an orthogonal edge router behind a provider seam (field-accepted at 89/89 edges, 0 hand-fixes, against a 4–5 baseline); `delta.mjs` automates the model diff that used to be a ~12-minute hand procedure. **New 2026-09-07:** `tokens.mjs` is the style-token table plus a WCAG contrast check over the palette — run `node tokens.mjs --check` and it grades the colours it actually emits rather than the ones the docs claim. `vendor/archify-geometry.mjs` is third-party (tt-a1i/archify, MIT), verbatim. The reference BUILD scripts stay in the source's deliverable tree; what ships is the library plus the `build()` contract in its README. Pinned to LF by this repo's `.gitattributes`: the emitted html's sha256 IS the freeze receipt, so a CRLF checkout would silently invalidate every one. |

## `instruments/` — verification tools the shipped rules name as their enforcement

New 2026-09-12. The source environment's `tools/` tree stays excluded, but two
of its tools are what shipped rule files literally invoke: `claude-ops/ops/environment.md`
names `page-fill-gate` as the "Enforcement:" of its display rule, and
`claude-ops/ops/references/integrity-sweep.md` check 7b imports
`check_cap_binding`. Excluding them left both citations pointing at nothing,
so this folder ships exactly those two, verbatim except one README. The
sub-paths match the source's, so an adopter copies `instruments/<x>/` to
`~/.claude/tools/<x>/` and every citation resolves unedited. Nothing else from
`tools/` qualifies; the manifest's `tools/` entry records why.

| File | What it is |
|---|---|
| `README.md` | Admission criterion (中文): shipped file runs, imports or names it as enforcement; stdlib-only; self-calibrating; reads no private tree. Per-tool table, install, measured known limits. |
| `page-fill-gate/` | Six files. `fill_gate.py` measures whether a human-read HTML page uses the width it is given; the named defect is the left-anchored cap. How full a page must be is a row of `page_classes.json`, not a code branch. Every run first checks a known-bad and a known-good fixture and refuses a verdict if either control fails. Needs Playwright + Chromium; exit 2 means the instrument is absent, never a pass. |
| `ops-health-test/check_cap_binding.py` | Sweep check 7b: each cap constant in `hooks/ops_health_nudge.py` must match the value the rule text states; reports drift or a lost anchor. `--selftest` runs one known-true and four known-false cases. Resolves paths relative to the INSTALLED `~/.claude` layout, so it does not run in place against this repo's renamed `claude-ops/ops/` tree — measured, and stated in the folder README. The rest of that source directory (the hook's own test suite) does not ship. |

## `agents/` — subagent definitions

Collected 2026-08-14, byte-verbatim. The nine agent types `claude-ops/ops/20-dispatch.md`
routes to: `backend-architect`, `frontend-developer`, `software-architect`,
`code-reviewer`, `security-engineer`, `testing-qa-engineer`, `api-tester`,
`testing-bug-fixer`, and — **new 2026-09-07** — `work-card-executor`, which
executes ONE build-ready work card to its machine-checkable acceptance and stops
at any interpretation fork the card does not settle. Each carries a `tools:`
capability allowlist (so "read-only"
is a fact, not a request), always includes `Skill`, and defines its output format
with evidence and attribution grading. Lineage and licence reasoning: `agents/README.md`.

## `environment-guide/` — why it is shaped this way

| File | What it is |
|---|---|
| `PHILOSOPHY.md` | The ten beliefs the whole environment is built on, plus a system map. |
| `OPERATOR-GUIDE.md` | Human-facing manual: what to run, what to expect, what each file is for. |
| `COMMIT-TEMPLATES.md` | Commit-message conventions used across this environment. |
| `README.md` | Folder note incl. migration checklist. |

## `interop-layer/` — porting the rules to other agents

| File | What it is |
|---|---|
| `portable-core.md` | The provider-neutral rule subset — preferences only, as of 2026-08-11. |
| `interop.py` | Compiles that subset into other agents' instruction files; leak-scans every payload before writing. |
| `MIGRATION-MAP.md` | What maps to what across agents. |
| `genesis-prompt.md` | Bootstrapping prompt for a fresh environment. |
| `acceptance-evals.md` | Checks that a port actually landed. |
| `test_interop.py` | **New 2026-08-16.** The compiler's self-test: parser positive *and* negative controls, plus a two-sided leak-gate calibration (15 known-TRUE samples, 5 known-FALSE). Running it here is what proved this repo's own leak patterns were missing two key shapes. |
| `README.md` | The source environment's own operating manual for the layer (中文). Collected, not written here — unlike every other `README.md` in this repo. |

**Collected, and declared as such since 2026-08-15**: every file above has a
`[[collected]]` entry in `tools/share-manifest.toml`, and `interop-layer/` is a
`collected_root`, so check C now enforces provenance here. Before that it did
not, and the copy silently drifted in both directions for weeks. Three files
carry declared, deliberate edits — `interop.py` imports the leak patterns from
`tools/sharelib.py` instead of defining them inline, `test_interop.py`'s
truncation case is restated against that gate's return shape, and
`MIGRATION-MAP.md` carries a share-repo-only section on disposition classes.
None of the three back-flows.

**As of 2026-08-16 that regime covers every collected root**, not three.
`claude-ops/`, `global-claude-md/`, `environment-guide/`, `skill-toolkit/` and
`thinking-notes/` joined it — 118 further files, each declaring its source path
and every edit. `red-team/` was declared a root on its creation day, 2026-08-17,
bringing the list to nine. If you are looking for what this repo changed on the
way in from the source environment, `[[collected]] edits` is now the complete
answer rather than a partial one.

**Retired 2026-08-11**: the `refs/` method-playbook folder and its compile step. Method depth is now delegated to each target agent's own official docs (`interop.py`'s `delegation_block()`) rather than shipped as curated prose — the trigger never ported, only the content did, and that degraded to "read either always or never". See `MIGRATION-MAP.md` and `README.md` for the reasoning.

## `tools/` — the publishing gate

Run `python tools/share_gate.py` before any push that touches shipped content;
exit 0 is the release condition.

| File | What it is |
|---|---|
| `share_gate.py` | Six fail-closed checks over every tracked file — **L** leak, **P** placeholder position, **R** reference disposition, **S** packaging structure, **C** collection provenance, **D** dead declarations — plus **V**, which needs `--source <path>` and is the only one that can see a declared edit reverted by a refresh. Never edits anything; automatic scrubbing is the failure it exists to catch. |
| `COLLECTION-RULES.md` | The decision procedure the gate enforces: what may be collected from the source environment, in which of five verdicts, and the mandatory copy → diff → declare → verify steps. Read it before adding or refreshing anything collected. |
| `sharelib.py` | The leak patterns, defined once. Imported by both `share_gate.py` and `interop-layer/interop.py`, so the two gates cannot drift apart — a claim that was false from 2026-08-11 to 2026-08-16 and is recorded as such in the manifest. Now also catches absolute paths on a non-system drive, the class that let nine private pointers through a single refresh. |
| `share-manifest.toml` | The only way past a finding: `[[allow]]` leak exceptions, `[[not_shipped]]` dependency dispositions + fallbacks, the `[placeholders]` position vocabulary, and the source-environment → repo path map. |
| `test_share_gate.py` | Sixteen cases, every one a real incident: the `<URL>` over-scrub, an undeclared hook, planted personal data, an unrecorded edit, a second-drive private path, an unmounted hook, a dead permission, a declared edit reverted by a refresh, a hooks/tests matrix that is not a hook, an expired unmounted-hook declaration, an inventory table behind the tree, and — new 2026-09-12 — the two private-id shapes the leak scan could not see: this machine's account name outside a home path (SKIP, not PASS, where the account name is stock or short) and a session-id UUID. **Three of the sixteen assert the gate stays quiet** — a gate calibrated only on what it should catch scores 100% by rejecting everything. (This row said "ten" until 2026-09-12; the suite had grown to fourteen on 2026-09-07.) |
| `triage.py` | **New 2026-09-12.** Sorts a source delta (`source_aligned`..HEAD, plus uncommitted state) into the procedure each path needs — `refresh`, `candidate`, `recheck`, `never`, `uncommitted`, `source-gone`, `deleted` — using only what the manifest already declares. A sort, not a verdict: it never decides whether anything ships. A `[[collected]]` entry beats a `[[not_shipped]]` directory, which is how the archdiag files under the excluded `tools/` tree stay on procedure B. |
| `test_triage.py` | **New 2026-09-12.** Seventeen cases: one per bucket and per precedence edge (collected-beats-directory, segment boundary, `archive` as a directory not a filename, a rename whose old path an entry still names), plus a positive control that removes a branch and must be noticed. |
| `SYNC-RUNBOOK.md` | **New 2026-09-12.** The orchestration around `COLLECTION-RULES.md` for a multi-worker round: Step 0 and triage, splitting lanes by coupling, one brief template for every lane (Appendix A), the manifest-editing protocol that makes lanes merge mechanically, the merge-time cross-lane race check, and close-out. |
| `README.md` | Operator manual (中文): why the layer exists, how to write a manifest entry, how to add a check, and how a whole round runs. |

## `thinking-notes/` — essays, not rules

Twelve numbered notes (`01`–`12`) on one-shot delivery, debugging epistemology,
unverifiable domains, ask-vs-decide, cross-language asymmetry, AI reading AI,
delegation economics, implementation-capability gaps, and legacy revival. These are
argument, not policy — nothing here binds a reader. `README.md` indexes them.
