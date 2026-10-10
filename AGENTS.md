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

The ChatGPT/Codex literature package moved on 2026-09-18 to its standalone
public repository at https://github.com/WizerdBaChe/literature-search-chatgpt;
its files are intentionally absent from this map.

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
| `references/` | Detail files for the rule above them, loaded on demand and never at session start — the landing zone when a rule file hits its size cap. `inbound-routing.md` (what arrives from outside, and which procedure it gets), `integrity-sweep.md` (the executable grep checks behind `40-maintenance.md` §5), `project-map.md` (the read-time layer behind `60-bootstrap.md` §H), and **new 2026-08-16** `external-dispatch.md` (the detail behind `20-dispatch.md` §4a — measured prompt shape, acceptance layers, failure signatures; the dispatcher itself is not shipped, but since 2026-08-17 its acceptance layers ship as running code in `red-team/`) and `skill-trigger-classes.md` (why a skill's zero fire count is or is not a defect). **New 2026-08-29**, both because the same round's refresh replaced shipped prose with pointers to them: `dispatch-templates.md` (the worked ✅/❌ contract pair and the five task-template field lists that used to sit inline in `20-dispatch.md`) and `shared-tree-git.md` (the concurrency discipline behind L-023 — the routing ruling by coupling class, the commit ritual in full, and what each kind of shared-state damage looks like, including the mitigation that turned a LOUD failure into a silent one). Also here, each named by the rule that loads it: `uat.md` (the user-acceptance procedure behind `30-judgment.md`), `entry-schema.md` (the field schema every registry entry conforms to; `instruments/entry-schema-lint/` checks it), `principle-design-guide.md` (how a principle becomes an asset property, PH-1..PH-11), `computer-use-probe-2026-09-07.md` (a dated measurement of the desktop-automation surface), and **new 2026-10-02** `gate-design.md` (the clauses behind `CLAUDE.md`'s automated-gate rule: determinable-only, two-sided calibration, emitted-artifact reads), `harness-measurements.md` (measured facts about the Claude Code harness the rules rest on — context budgets, tool shapes, injected blocks — two machine paths generalized) and `maintenance-cases.md` (the worked cases behind `40-maintenance.md`). **New 2026-10-10:** `ticket-supervision.md` (the field-by-field detail behind `20-dispatch.md` §7a: registration fields, board authority, shared-tree lines) and `platform-source-registry.json` (the platform list behind `30-judgment.md` R7, read by `instruments/platform-search/`). |
| `README.md` | Folder note. |

## `global-claude-md/` — the always-loaded preferences file

| File | What it is |
|---|---|
| `CLAUDE.md` | The global preferences the ops layer hangs off. Machine-specific values are `<PLACEHOLDER>`s — substitute your own. Opens with a "Path-scoped rules" index pointing at `rules/`. |
| `rules/` (fourteen files) | Path-scoped rules: each loads only when a matching file is read (or, on 2.1.288+, written), and `CLAUDE.md`'s opening index names all fourteen. **2026-10-10:** `shader-failure-modes.md` left — the source retired it on 2026-10-09 (one load in 1,094+ sessions; its project is finished); and two new source rules, `decision-sheet.md` and `explainer-deliverables.md`, are withheld because each is defined by a source-only tool (manifest `[[not_shipped]]`, and the index line says so). **New 2026-10-02:** `source-quotation-evidence.md` (copyrighted page: locator + a short quote + local OCR, never a transcript; its instrument `quote-evidence` ships under `instruments/`), `layout-convergence.md` (figure/slide crowding: tiers and a stop rule), `native-render-first.md` (a tool result's figure: the tool's own render first) and `android-device-states.md` (every window/config state an Android app is accepted on). `frontend-layering.md` was one of the first two sunk out of CLAUDE.md's body (2026-08-11): FSD module layering. `deliverable-doc-refs.md` (human-facing HTML: define before use, hover cards, the page-class width registry), `office-deck-deliverables.md` (programmatic PPTX), `visual-gate-scope.md` (measure the glyph, gate the class), `verification-ladder.md` (evidence rungs 0–5, plus the verification record a durable claim ships with). **New 2026-09-12:** `web-navigation-state.md`, `hook-deny-message.md`, `naming-and-placement.md`, `figure-self-read.md`, and `literature-access.md`, which ships with its enforcing hook `hooks/literature_host_guard.py`. (This row named two files until 2026-09-12; four had arrived since without it changing.) |
| `README.md` | Cross-reference map back into `claude-ops/`. |

## `skill-toolkit/` — installable skills

`skill-trigger-dict.md` is the disambiguation index; each `skills/<name>/SKILL.md` is
self-contained, with detail in its own `references/` loaded on demand.

| Skill | For |
|---|---|
| `ai-coding-guardrails` | Designing the guardrail *system* around AI coding agents (5 references). |
| `audience-fit` | **New 2026-09-02.** Post-production audience tuning: rewriting an engineer-voiced deliverable for a non-developer reader, or moving UI copy from the builder's view to the user's. One document serves one primary audience, and the rewrite ships paired with the original — evidence strength, causal register and stated limits may not shift in the retelling. |
| `case-library` | **New 2026-10-02.** Building a case library over a run of same-kind examples (videos, posts, layouts, UI patterns): classify → collect → specialised analysis → controlled imitation → extract the repeatable workflow. Eight invariants, among them a controlled vocabulary with a self-testing validator, generated-only indexes, no numbers from an uncalibrated instrument, and "looks good" decided only by the user watching. The reference implementation is a private project at the source; the skill stands without it. |
| `clean-room-rebuild` | **New 2026-10-10.** Rebuilding an external source (repo, article, dataset, prompt set) as our own version by concept, not copy: reading and writing kept apart, an expression-free spec card, every unit tagged source concept / our interpretation / added info / deviation. Ships the surface-overlap gate `scripts/overlap_check.py` with its two-sided controls (`controls.py`, 38 controls). Promises no source expression, a process on record and visible additions — not a legal clean room. |
| `code-review-deep-checklist` | Deep/holistic code review: single review, project health, dependency fitness. |
| `comsol-agent-pipeline` | **New 2026-10-02.** Driving COMSOL 6.2 headless from Python (MPh): pick a mode card by observable → build or load a seed → solve → read back → rule PASS/FAIL/UNDET against an analytic gate with its control. Every number carries a source tag; 106 measured API pitfalls in `references/api-rules.md` (a generated snapshot — the rig and its generator stay at the source); 16 mode cards and script skeletons. |
| `config-self-audit` | Auditing one config artifact — a skill, hook, or rule — cheaply. |
| `design-system-suite` | Design tokens and contracts across a multi-product frontend suite. |
| `diagram-authoring` | **New 2026-08-27.** Precision diagram production & gap finding: structural text model first, geometry self-check asserts, a fabrication firewall, mandatory gap report. The production third of the `architecture-diagramming/` capability set; its theory lives in two `product-design-thinking` references it cites rather than copies. |
| `env-cleanup` | File-level cleanup of a config environment or project tree; archives, never deletes. |
| `literature-search-extract` | Finding scholarly sources and extracting into evidence tables, with citation traceability. |
| `mechanism-share-packaging` | **New 2026-08-17.** Exporting a behavioural MECHANISM — an operating mode spanning hooks, tools, wiring and docs — into a governed share repo: scope it as a runtime, land each file where the target's structure says, sweep the ripples arrival causes, loop the target's gate. Delegation is its first hard rule — the target repo's collection rules stay authoritative and are never restated inside it. `compact-recovery/` and `red-team/` are its two live runs. |
| `motion-design` | Motion/animation methodology + Three.js. `vendor/lottiefiles/` is third-party MIT, verbatim. |
| `pptx-review` | **New 2026-10-02.** The deck review loop inside PowerPoint: resolve "this slide / this box" to what the user has open and selected, read the reviewer's comments, apply them to the deck's BUILD SOURCE by per-comment confidence (anchor or unique quote: apply; pin position: only if the text fits; conflict: skip and report, never guess), rebuild, gate, report applied/skipped/general rulings. Its read-only instrument ships as `instruments/pptx-review/`. |
| `product-design-thinking` | Heavyweight design mode for a new product: prior-art sweep, then build-ready docs. |
| `project-retrospective` | End-of-project extraction of lessons into a guide + rules snippet. |
| `scientific-research-guide` | Research-methodology advisory. **Domain profiles excluded from this share** — see `domains/README.md`; the template, manifest format, and expansion spec ship. The eval suite left with them 2026-08-27 — it had become the withheld profiles' routing test harness (manifest `[[not_shipped]]` carries the reversal). |
| `security-deep-checklist` | Defensive security audit: code, deployment posture, detection readiness. |
| `skill-co-upgrade` | **New 2026-08-16.** Field-test loop: run a real task through a skill, collect gaps under "a gap exists iff the executor had to BYPASS the skill to do it right", verify every citation, hand off via disposition files. |
| `skill-share-packaging` | Exporting a skill for others, or auditing a downloaded one. Includes `scripts/prescan.py`. |
| `ux-walkthrough` | **New 2026-09-07.** Task-level UX walkthrough of an existing or designed interactive surface: can a specific person find the entry, predict each action's consequence, wait/cancel/recover, and come back next time — on keyboard and narrow layout too. Output is executable findings plus show/disable/hide rulings and a wait-cancel-recovery contract. The instrument behind `product-design-thinking`'s "UX semantics are the user's decision"; hands wording work to `audience-fit` and takes it back. |
| `workflow-checkpoint` | Phase archiving and context rebuild across long multi-session projects. |

## `hooks/` — the mechanical enforcement layer

Collected 2026-08-14, extended on 2026-08-16, 2026-08-29, 2026-09-07,
2026-09-12, 2026-10-02 and 2026-10-10. **Thirty-five mounted hooks** across PreToolUse /
PostToolUse / UserPromptSubmit / SessionStart / Stop / PreCompact /
PostCompact / InstructionsLoaded — the enforcement
layer the ops rules had been citing without ever shipping it; all fail-open,
none machine-bound. Install steps and the per-hook table are in
`hooks/README.md`; `settings.example.json` is the mounting template with
`<PYTHON_EXE>` / `<CLAUDE_HOME>` to substitute, and it mounts every hook that
ships. Some `.py` files are deliberately outside that rule and none is a
defect: `tests/` holds regression matrices run by hand; `handoff_snapshot.py`
and `deny_receipt.py` are shared libraries with no event to mount at;
`fieldwork_threshold_notice.py` was retired at the source on 2026-09-12 and
ships unmounted, as the source runs it; and `delivery_gate_shadow.py` joined it
on 2026-10-02 (its SubagentStop mount removed at the source, file kept). Every exemption is declared in
`tools/share-manifest.toml` and checked, so none can quietly become a hook
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
| `fieldwork_threshold_notice.py` | **New 2026-08-16, retired 2026-09-12.** Shadow: main-session Read/Grep/Glob measured against `20-dispatch.md` §1's literal thresholds. Retired at the source (ruling R-3: at least 52% of 293 shadow rows were false positives); ships unmounted with its test suite, as the source runs it. |
| `instructions_loaded_logger.py` | Observation only: which instruction files load, when. |
| `compact_bookmark.py` | **New 2026-08-16.** PreCompact half of the compact-recovery bridge: bookmarks the pre-compact transcript (path, line count, trigger), then best-effort refreshes digest cards. |
| `compact_pointer.py` | SessionStart("compact") half: injects a ~130-token pointer card — digest-first recall ladder, exact pre-compact region, the two recall triggers. |
| `transcript_read_guard.py` | Deny on unbounded Reads of large session RECORDS; identity is by SHAPE since 2026-08-29 (`.jsonl`, or `.md` under `digests/`), so the caches and PDFs sharing those directories read freely — the fix for two measured false denials, with the decision table, the tested bypasses and the deny-message contract all in its docstring. The quartet's overview lives in `compact-recovery/README.md`. |
| `compact_loss_record.py` | **New 2026-09-07.** PostCompact recorder: appends one row per compaction (trigger, snapshot presence, snapshot age at compaction) to `compact-loss.jsonl`, and nudges when the summary arrived with no snapshot behind it. It only records — it never denies. Its audit half, `compact-loss-audit`, ships under `instruments/` since 2026-10-02 (the README said otherwise until 2026-10-10). |
| `handoff_snapshot.py` | **New 2026-09-07. Not a hook** — the shared library the three above import (`snapshot_path`, `is_fresh`, `notice`). It has no event to mount at; removing it breaks all three, which is what `compact-recovery/ACCEPTANCE.md` item 9 checks. |
| `tests/test_transcript_read_guard.py` | **New 2026-08-29.** That guard's regression matrix — 22 cases including every alias form (8.3 short name, `\\?\` prefix, junction) and every accepted bypass. Run by hand; not a hook, and deliberately not mounted. |
| `shell_transport_guard.py` | **New 2026-08-29.** The Bash tool's three SILENT transport defects: backslash-run collapse (annotates — a 5,113-call backtest found 89 of 112 hits were the author already compensating, so the gate cannot determine intent), the ~7.7 KB size ceiling (denies — 7 of 7 corpus hits already failed), and MSYS `/flag`→path rewriting (annotates). Persists the full command before any denial. |
| `ps_errorpref_guard.py` | **New 2026-08-29.** `$ErrorActionPreference='Stop'` governing a native exe — wrong in both directions at once (fires on a harmless stderr line, misses a non-zero exit). Annotates, never denies. Mounted on `Write` because that is where 47 of 53 real payloads arrived, not on the tool the ticket asked for. |
| `ps_pipeline_close_guard.py` | **New 2026-08-29.** `\| Select-Object -First N` closes the pipeline and KILLS the upstream process; the output looks truncated for its own reasons and the exit code says failure, so both halves point away from the cause. Its backtest put the surface on `PowerShell` — the opposite of its sibling's, which is why each was measured rather than copied. |
| `branch_commit_guard.py` | **New 2026-08-29.** A `git commit` into a checkout inside `~/.claude` must land on `main` unless the command carries `[branch-ok]` or the worktree has opted in. The compensating control for two same-day incidents where the prose ritual RAN and did not gate — it was a non-gating spectator in a `&&` chain. Carries its own incident log and false-positive count. |
| `dispatch_commit_notice.py` | **New 2026-09-12.** Three mounts, one tracker: a subagent dispatch is recorded, and a bare `git commit` by that agent with no matching process-ledger call is annotated at the next related event. Never denies. |
| `published_record_guard.py` | **New 2026-09-12.** Denies a Write/Edit into any tree whose root carries `tools/COLLECTION-RULES.md` (this repo included) when the payload matches a private-value shape: a drive-rooted or POSIX home path, the account name read at run time, a 32+ hex run, a UUID. It gated this round's own collection work. |
| `worktree_scope_guard.py` | **New 2026-09-12.** A session inside a git worktree is told so at start, and a command that would mutate the canonical checkout is denied unless it carries the opt-in or runs from the canonical cwd. |
| `literature_host_guard.py` + `literature-host-policy.json` | **New 2026-09-12.** Enforces `global-claude-md/rules/literature-access.md` at the tool-call boundary: the policy table puts each scholarly host on a tier (open, API, human-paced, no proxied access), and the guard denies the last. One mechanism with the skill-side `connectors/access_policy.py` and `verify/fetchsrc.py`. |
| `deny_receipt.py` | **New 2026-09-12. Not a hook** — the receipt helpers `rules/hook-deny-message.md` requires, so an agent reading a deny text can check sideways that a local hook wrote it. Imported by fifteen of the shipped hooks — every guard whose text reaches the agent. |
| `tests/` (nine more suites) | **New 2026-09-12, four more 2026-10-02.** Regression matrices for `browser_pane_scope_guard.py`, `instructions_loaded_logger.py`, `fieldwork_threshold_notice.py`, `literature_host_guard.py`, and — this round — `golive_check.py`, `project_registry_gist.py`, `session_search_query_notice.py`, `system_hmi_summary.py` and `verbatim_dispatch_notice.py`, beside the 2026-08-29 one. Run by hand. The suites for the other hooks live under `instruments/<name>-test/`, where the source keeps them. |
| `appdata_view_guard.py` | **New 2026-09-07** (collected 2026-10-02). On one machine the assistant's shell and the user's own shell can answer differently for the same `%LOCALAPPDATA%` path or HKCU value, and neither errors (the 2026-09-05 incident that deleted 36 dashboard settings as "duplicates"); the guard makes a command that reads those views say which shell it is in. |
| `boundary_contract_notice.py` | **New 2026-10-02.** One notice per session when an L1/L2 main loop writes its first code file with neither a boundary contract nor a waiver in the process ledger. Annotates only; depends on `instruments/process-ledger/`. |
| `feedback_notice.py` | **New 2026-10-02.** One notice when the main loop first edits one of its own subsystem files (hooks/skills/tools/ops/rules) and the ledger holds no feedback row for that target. Annotates only; depends on `instruments/feedback-pool/` and the process ledger. |
| `tree_noise_gist.py` | **New 2026-10-02.** SessionStart: classifies the dirty working tree with `instruments/tree-noise/noise.py` (git only) and prints one line when some of it is content-neutral noise, so a session does not read it as unfinished work. |
| `golive_check.py` | **New 2026-10-02.** PostToolUse on a hook file: saving a hook puts it live, so the save runs the `Proof-of-life:` command the hook's own docstring declares (and the suites of hooks reading the same data) and notices on failure. Never blocks; writes telemetry first. |
| `system_hmi_summary.py` | **New 2026-10-02.** SessionStart: tells the session which rows of the last `system-hmi` snapshot are unhealthy and where the known-good mark is; prints one "snapshot unavailable" line when there is none. The tool ships as a template under `instruments/system-hmi/`. |
| `view_launcher_gist.py` | **New 2026-10-02.** SessionStart: injects the core view pages (purpose → path) from `instruments/view-launcher/views.json`; silent when the registry is absent. The tool ships as a template. |
| `verbatim_dispatch_notice.py` | **New 2026-10-02.** A dispatch prompt that asks a subagent to transcribe pages or images verbatim gets a notice (the output filter blocks long copyrighted text, so the whole subagent is wasted); routes to `rules/source-quotation-evidence.md` and `instruments/quote-evidence/`. Annotates only. |
| `session_search_query_notice.py` | **New 2026-10-02.** The session-search tool treats a multi-word query as one literal substring, so it almost always returns "no matching sessions" — indistinguishable from a true null. A multi-word query gets a notice to use a single keyword. |
| `intake_guard.py` | **New 2026-09-07, excluded then, collected 2026-10-02.** DENY guard over `ops/lessons/` and `ops/lessons.md`: a record cannot be rewritten after birth, only extended through `intake.py add / event / render`. Its deny text points at `instruments/closeout-intake/`, which ships this round; without that CLI the guard would block writes with no way through, which is why it stayed out before. |
| `intake_match_shadow.py` | **New 2026-09-07, collected 2026-10-02.** Shadow on every prompt: runs `intake.py match` and records which lesson cards WOULD be injected; never prints, never blocks. |
| `unattended_run.py` | **New 2026-09-07, collected 2026-10-02.** One file, three mounts (`scope` on Write/Edit, `kickoff` on UserPromptSubmit, `stop` on Stop): the carrier of the `[unattended-run]` mode. Armed only when a prompt carries the tag; then the scope guard denies writes outside the run's declared list and the Stop guard blocks until the report `instruments/process-ledger/report.py` generates exists. The mounts pass a subcommand after the script — the shape that gate check S5 learned to read this round. |
| `secret_file_guard.py` | **New 2026-09-07, collected 2026-10-02.** Denies reads of credential-shaped filenames (`.env`, `*.pem`, `*.key`, `credentials.json`, `id_rsa`, …) on Read/Grep/Bash/PowerShell after stripping commit-message bodies and metadata-only git subcommands; templates (`.env.example`) pass; escape hatch `[user-approved-secret-read]`. Its two-sided suite ships as `instruments/secret-guard-test/`. The earlier "one operator's own file list" reading was wrong: the pattern is generic. |
| `project_registry_gist.py` | **New 2026-09-07, collected 2026-10-02.** SessionStart: compresses `references/PROJECTS.md` into one injected card, anchored on the declared columns — says so when they drift rather than injecting garbage; silent when the registry is absent (this repo ships the registry as a template). |
| `offline_approval_notice.py` | **New 2026-10-10.** UserPromptSubmit: when a prompt says the user will be away or cannot approve dialogs, it prints the `permissions.ask` patterns read live from the settings files, with the route (build outside them, put ask-path content on a card as drafts, or use the `[unattended-run]` tag) — because an ask-path write waits for a human even in bypass mode (one recorded wait: 2.9 h). A notice, never a block; suite `tests/test_offline_approval_notice.py` reads the installed `settings.json`. |
| `stash_worktree_notice.py` | **New 2026-10-10.** PreToolUse: `refs/stash` is one ref shared by the canonical tree and every linked worktree, so a stash pushed in one can be popped by a peer in another with exit 0. Notices a stash-writing `git stash` in a repository that has linked worktrees; a notice, not a deny, until a first loss incident. Needs only git; suite `tests/test_stash_worktree_notice.py` (17 cases). |

Twenty-two of the source's seventy-three hook-layer files are deliberately **not** here
(fourteen hooks and eight of their tests),
and `tools/share-manifest.toml` carries a disposition for every one. Two gate an
external-dispatch entry point this repo does not ship, and `codex_dispatch_guard.py`
gates a second dispatcher the same way; `session_board_register.py` is one half of
a source-environment tool (the ticket board) whose other half is not a rules
asset — `20-dispatch.md` §7a carries the share note saying its registration is
done by hand here. `xi_card_guard.py` and `moc_closeout_notice.py` (with their
tests) serve a cross-index pipeline this share does not carry;
`past_work_recall_inject.py` and `subagent_retrieval_brief.py` (with their tests)
query the recall store that stays out with it; `user_profile_gist.py` (with its
test) injects one person's profile, and `registry_row_guard.py` imports it, so a
copy here could never run; `deliverable_birth_notice.py` registers deliverables
into the same private index. **New 2026-10-10:** `candidate_shelf_notice.py` (with its
test) reads a private asset library's index and CLI; `session_pid_registry.py` and
`session_reaper_launch.py` feed and launch a one-machine process reaper that does not
ship. **Reversed 2026-10-02:** five hooks excluded on
2026-09-07 and 2026-09-12 because their only private dependency was a tool under
`tools/` — `intake_guard.py`, `intake_match_shadow.py`, `unattended_run.py`,
`secret_file_guard.py`, `project_registry_gist.py` — ship now that those tools
ship under `instruments/`; the manifest entries carry the reversal.
`settings.example.json` mounts every hook that ships and nothing else, with the
exemptions named above; that is the invariant to re-check
whenever this table changes, and check S5 of the gate is what re-checks it.

## `compact-recovery/` — post-compact recall as an operating mode

New 2026-08-16, extended 2026-09-07. Not a single tool but one mechanism
spanning six files: the four compact hooks above (three mounted plus the shared
library they import) and the digest generator here. What a `/compact` summary
drops stays recoverable at on-demand token cost; the one move that would
re-inflate context — a wholesale re-read — is structurally denied.

| File | What it is |
|---|---|
| `README.md` | The operating mode (中文): event-pair bridge, recall ladder, token economics, install steps incl. the optional SessionEnd mount, tunables table, platform-contract re-check recipes, de-identification notes. **2026-09-07:** the handoff-snapshot and loss-record halves, and a named gap that closed on 2026-10-02 when the audit tool (`instruments/compact-loss-audit/`) began to ship; corrected in the README on 2026-10-10, which also lists `context_runway_shadow.py` (the handoff-snapshot reminder) in the install set. |
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

New 2026-09-12, widened 2026-10-02 and 2026-10-10. It began as the two tools shipped rule
files literally invoke: `claude-ops/ops/environment.md` names `page-fill-gate`
as the "Enforcement:" of its display rule, and
`claude-ops/ops/references/integrity-sweep.md` check 7b imports
`check_cap_binding`. The owner's 2026-10-02 ruling opened the source's `tools/`
tree to method tools and hook test suites, so the folder now holds forty-seven
directories (169 files besides its README) in four groups, each a table in
`instruments/README.md`: **A** the original two; **B** every hook's hand-run
test suite (`branch-guard-test`, `dangerous-command-test`, `model-cap-test`,
`ps-errorpref-test`, `ps-pipeline-close-test`, `shell-transport-test`,
`ui-verify-test`, `e2-gate-test`, `ops-health-test`, `secret-guard-test`, the
two `*-backtest` corpora, which since 2026-10-10 import the shared corpus-walk
harness `hook-backtest`); **C** rule, record-format and proof-of-life
instruments (`hook-deny-lint`, `entry-schema-lint`, `class-closure`,
`hook-proof-of-life`, `telemetry-framing`, `context-budget`); **D** the method
tools the rules name as their procedure or gate (`process-ledger`,
`closeout-intake`, `feedback-pool`, `tree-noise`, `cc-delta`, `routing-loop`,
`eol-sync` + `git-hooks` (with a pre-commit budget and escape check since
2026-10-10), `quote-evidence`, `audience-fit-gate`,
`compact-loss-audit`, `rule-usage-census`, `shell-audit`, `tracking-refs`,
`status-line`, `ui-shot`, the three PPTX gates `pptx-edit-headroom` /
`pptx-line-start` / `pptx-presentation-gate`, `pptx-review`,
`skill-routing-audit.py` with its test, `glob-fitness.py`, the one shipped
file of `cross-index`, and — new 2026-10-10 — `mod-review` (the review gate
`hooks/ops_health_nudge.py` names for a mod change), `platform-search` (the
external-discussion search `CLAUDE.md` routes to; its dispatcher leg degrades
to unavailable here) and `token-key-gate` (cited by
`rules/deliverable-doc-refs.md`; needs Playwright, exits 2 without it)) and two monitoring tools as **templates** — `system-hmi`
and `view-launcher`, whose registries carry a schema and one worked row.
The sub-paths match the source's, so an adopter copies `instruments/<x>/` to
`~/.claude/tools/<x>/` and every citation resolves unedited; `[source_map]`
carries one line per directory. What stays out of `tools/` is the operator's
personal stores and carriers (recall, cross-index, graph-snapshot, the session
board, the place ledger, the census tools, the memory pipeline, scheduled and
backup carriers, the external dispatcher's runtime); the manifest's `tools/`
entry records each with its reason. Nearly every suite is written for an
INSTALLED config home; `instruments/README.md` says which also run in place
here and what each needs.

| File | What it is |
|---|---|
| `README.md` | Admission criterion (中文): shipped file runs, imports or names it as enforcement; stdlib-only; self-calibrating; reads no private tree. Per-tool table, install, measured known limits. |
| `page-fill-gate/` | Six files. `fill_gate.py` measures whether a human-read HTML page uses the width it is given; the named defect is the left-anchored cap. How full a page must be is a row of `page_classes.json`, not a code branch. Every run first checks a known-bad and a known-good fixture and refuses a verdict if either control fails. Needs Playwright + Chromium; exit 2 means the instrument is absent, never a pass. |
| `ops-health-test/check_cap_binding.py` | Sweep check 7b: each cap constant in `hooks/ops_health_nudge.py` must match the value the rule text states; reports drift or a lost anchor. `--selftest` runs one known-true and four known-false cases. Resolves paths relative to the INSTALLED `~/.claude` layout, so it does not run in place against this repo's renamed `claude-ops/ops/` tree — measured, and stated in the folder README. The rest of that source directory (the hook's own test suite) does not ship. |

## `model-bench/` — tier-routing benchmark for the dispatch table

New 2026-10-08. Measures which rows of `claude-ops/ops/20-dispatch.md` §4 a cheap
tier can carry: twelve tasks, each with a MACHINE gate (no LLM judge), run through
`claude -p` per (task, model, effort, repetition). Rounds 1–2 ran in a cloud
container; rounds 3–5 on the owner's workstation (the canonical copy of the tool lives
there; this folder is its share copy, not a collected root — `[source_map]` maps
`tools/model-bench/` here so source citations resolve). Round 5 (2026-10-10)
re-measured three tasks after the source fixed a fixture that wrote the answer
file into the model's workdir.

| File | What it is |
|---|---|
| `README.md` | Operator manual (中文): question, task table, run commands, record fields, ruling rule, per-round results, the owner's rulings, the deck. |
| `DESIGN.md` | How the bench was derived, what each task examines, comparison with public benchmarks. |
| `bench.py` | The runner: `list` / `selftest` (two-sided controls per gate) / `run` / `summarize` / `rejudge` / `judge`. Stdlib only. |
| `judge_agent.py` | Gates one Agent-tool run from its subagent transcript (`MB_SESSION_DIR`) by summing usage and calling `bench.py judge`. |
| `pricing.json` | List prices used for the cross-check cost column, incl. Haiku's long-prompt tier. |
| `tasks/` | One module per task: seeded fixture generator + gate. |
| `results/` | Per-round run records (`*.jsonl`, rounds 2–5), machine summaries, reports, the 2026-10-08 dispatch proposal, and the one-off Agent-path judge scripts of rounds 4–5 (they read `MB_SESSION_DIR`). |
| `post/` | General-audience explainer post (中文, 10 image cards + editable `EX1.pptx` + `caption.txt`): Haiku 5.5 effort levels vs Sonnet 5.5 on one ruler, what to hand Haiku, when to switch, safety, a dispatch checklist. Replaced the round-2 HTML report on 2026-10-08. |

## `mods/` — Claude Code mods (in-process plugins)

New 2026-10-10. Two TypeScript mods that Claude Code 2.1.287+ loads in-process,
collected as code. The reason to have them beside the Python hooks: an in-process
hook is awaited by the engine, so a timeout cannot turn into a pass. Both come with
tests that run under `claude plugin test`. A third source mod, `pending-items`, does
not ship (it reads one operator's session digests); nor do `feedback-observer`'s
calibration fixtures, which are excerpts of real sessions — `make_fixture.py` ships
so an adopter can build their own.

| File | What it is |
|---|---|
| `README.md` | Folder note (中文): what is here, install via `CLAUDE_CODE_PLUGIN_DIRS`, and what stays out. |
| `model-cap-mod/` | The subagent model cost cap as a mod: `agent.spawn` denies an explicit top-tier dispatch, `turn.step` judges the model the engine actually resolved and refuses before a request is sent. Mirrors `hooks/model_cap_guard.py`; its README has the split of duties. `tests/policy.test.ts`, 11 cases. |
| `feedback-observer/` | An observe-only side check that reads the recent transcript window with a mid-tier model and records suspected subsystem defects for the feedback pool, in shadow (not counted). `hooks/` holds the gate, window, parser and recorder, `prompt.md` the system prompt, `judge.py` the user's per-finding verdict, `tests/` 24 cases. |

## `agents/` — subagent definitions

Collected 2026-08-14, byte-verbatim. The ten agent types `claude-ops/ops/20-dispatch.md`
routes to: `backend-architect`, `frontend-developer`, `software-architect`,
`code-reviewer`, `security-engineer`, `testing-qa-engineer`, `api-tester`,
`testing-bug-fixer`, and — **new 2026-09-07** — `work-card-executor`, which
executes ONE build-ready work card to its machine-checkable acceptance and stops
at any interpretation fork the card does not settle; and — **new 2026-10-10** —
`cheap-worker`, a cheap-tier mechanical worker for tasks with a hard
machine-checkable gate that deliberately carries no user instruction layer. Each carries a `tools:`
capability allowlist (so "read-only"
is a fact, not a request), always includes `Skill`, and defines its output format
with evidence and attribution grading. Lineage and licence reasoning: `agents/README.md`.

## `environment-guide/` — why it is shaped this way

| File | What it is |
|---|---|
| `PHILOSOPHY.md` | The ten beliefs the whole environment is built on, plus a system map. |
| `OPERATOR-GUIDE.md` | Human-facing manual: what to run, what to expect, what each file is for. |
| `COMMIT-TEMPLATES.md` | Commit-message conventions used across this environment. |
| `KNOWLEDGE-PACKS.md` | **New 2026-10-02.** What a knowledge pack is (a SKILL.md of triggers and judgement over a `references/` of dated, sourced, review-when-stamped topic files), the four criteria a pack must meet to be registered, depended on per branch, shared, or split and retired, and a dated status table of the source's three packs. Written at the source so it could ship verbatim in place of the packs, which stay withheld. |
| `LABEL-REGISTRY.md` | **New 2026-10-02, template.** The rules and maintenance procedure for enumerable labels (`Mode X`, `L2`, `Tier-3`, list ordinals): criteria and procedure complete, the family table reduced to its header for the adopter to fill. Until this round the standing example of a `referenced-only` disposition. |
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
not, and the copy silently drifted in both directions for weeks. Several files
carry declared, deliberate share-side edits: `interop.py` imports the leak
patterns from `tools/sharelib.py` and now adapts the Codex/share layout;
`test_interop.py` tests that contract; `MIGRATION-MAP.md`, `README.md`,
`genesis-prompt.md`, and `acceptance-evals.md` record the Codex/ChatGPT
file-target, package/import, and self-contained-skill boundaries. None of these
edits back-flow into the source environment.

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
| `sharelib.py` | The leak patterns, defined once. Imported by both `share_gate.py` and `interop-layer/interop.py`, so the two gates cannot drift apart — a claim that was false from 2026-08-11 to 2026-08-16 and is recorded as such in the manifest. Now also catches absolute paths on a non-system drive, the class that let nine private pointers through a single refresh. **2026-10-03:** a known-personal-names class read at run time from a private list kept beside the repo (never in it); findings name the entry number, never the name, and the CLEAN line says whether the list was loaded. |
| `share-manifest.toml` | The only way past a finding: `[[allow]]` leak exceptions, `[[not_shipped]]` dependency dispositions + fallbacks, the `[placeholders]` position vocabulary, and the source-environment → repo path map. |
| `test_share_gate.py` | Twenty-seven cases (2026-10-10: six for the three pointer shapes check R learned to read — an `.html` path, a glob, the script argument of a `python` command — each with a positive and a negative half, and one asserting a full run leaves the fixtures it touches byte-identical in `git status`; before that, twenty: case 18, 2026-10-03, in two halves: a listed name fires, and the same short name used as an English word stays quiet; eighteen before it, sixteen until 2026-10-02, when case 17 arrived in two halves: a mount that passes an argument after the hook script is still that hook's mount, and the same shape on a file that does not ship is still named correctly — check S5 had read the command's last token as the hook name), every one a real incident: the `<URL>` over-scrub, an undeclared hook, planted personal data, an unrecorded edit, a second-drive private path, an unmounted hook, a dead permission, a declared edit reverted by a refresh, a hooks/tests matrix that is not a hook, an expired unmounted-hook declaration, an inventory table behind the tree, and — new 2026-09-12 — the two private-id shapes the leak scan could not see: this machine's account name outside a home path (SKIP, not PASS, where the account name is stock or short) and a session-id UUID. **Five of the twenty assert the gate stays quiet** — a gate calibrated only on what it should catch scores 100% by rejecting everything. (This row said "ten" until 2026-09-12; the suite had grown to fourteen on 2026-09-07.) |
| `triage.py` | **New 2026-09-12.** Sorts a source delta (`source_aligned`..HEAD, plus uncommitted state) into the procedure each path needs — `refresh`, `candidate`, `recheck`, `never`, `uncommitted`, `source-gone`, `deleted` — using only what the manifest already declares. A sort, not a verdict: it never decides whether anything ships. A `[[collected]]` entry beats a `[[not_shipped]]` directory, which is how the archdiag files under the excluded `tools/` tree stay on procedure B. |
| `test_triage.py` | **New 2026-09-12.** Seventeen cases: one per bucket and per precedence edge (collected-beats-directory, segment boundary, `archive` as a directory not a filename, a rename whose old path an entry still names), plus a positive control that removes a branch and must be noticed. |
| `SYNC-RUNBOOK.md` | **New 2026-09-12.** The orchestration around `COLLECTION-RULES.md` for a multi-worker round: Step 0 and triage, splitting lanes by coupling, one brief template for every lane (Appendix A), the manifest-editing protocol that makes lanes merge mechanically, the merge-time cross-lane race check, and close-out. |
| `README.md` | Operator manual (中文): why the layer exists, how to write a manifest entry, how to add a check, and how a whole round runs. |

## `thinking-notes/` — essays, not rules

Twelve numbered notes (`01`–`12`) on one-shot delivery, debugging epistemology,
unverifiable domains, ask-vs-decide, cross-language asymmetry, AI reading AI,
delegation economics, implementation-capability gaps, and legacy revival. These are
argument, not policy — nothing here binds a reader. `README.md` indexes them.
