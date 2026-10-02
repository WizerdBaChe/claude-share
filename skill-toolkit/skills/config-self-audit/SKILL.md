---
name: config-self-audit
description: >-
  Cheap audit of durable Claude Code config. DEFAULT mode (ONE artifact): a
  skill, hook, subagent definition, global CLAUDE.md rule, or settings.json
  change — trigger on 稽核/audit/review one (「檢查這個 hook」「這條規則安不安全」
  「安全性遺漏 (security gap)、乾淨度」「確認有寫進規則、規則調用得到嗎」
  「跟各 skill/規則的交互邊界與衝突」),
  when a NEW skill/hook/subagent was just authored here, or when a
  /doctor-style report needs verifying. ADOPTION mode: config copied from
  another environment (移植規則、併入別人的設定 repo、規則打架), or a `reconciled: no` stamp — audits
  RELATIONS between rules: trigger collisions, ordering, unshipped mechanisms.
  NOT for authoring skills (→ skill-creator), ONE third-party skill
  (→ skill-share-packaging), or file cleanup (→ env-cleanup). Disambiguation:
  ~/.claude/skill-trigger-dict.md.
---

# Config Self-Audit

Cheap, repeatable safety/consistency check for durable config under `~/.claude/`
(or a project `.claude/`). From a full external audit (2026-07-03), revised after
measuring the official `/doctor` against it (2026-07-25).

**Self-contained by design.** Every section runs on local files and cheap
commands. External health-check tools are an optional, lowest-priority input
(§8) — never a prerequisite, never a reason to defer a question.

## Scope of one run

Audit ONLY the artifact(s) named or just created — not the whole config tree.
Budget: a handful of Read/Grep/Test-Path calls, plus one script invocation when
usage matters (§5). A finding needing running servers or a full environment sweep
is out-of-scope — say so instead of doing it. For a COMPREHENSIVE or from-scratch
review (全面/加強), run this checklist first, then hand off to the clean-sheet
extension in `ops/30-judgment.md` R8 pass 1 — never widen this skill's budget.

**One declared exception**: adoption mode below, whose defects are relations
between artifacts and so unreachable at artifact scope. Still bounded — the
imported set and its immediate neighbours, not the whole tree — and entered only
on the explicit conditions listed there, never by drift.

## Two modes

**Default mode** is everything below: one artifact, the §1–§9 checklist.

**Adoption mode** fires when durable config arrived from ANOTHER environment — a
shared repo or zip, an agent told to "analyse this and adapt it into my setup",
or a `reconciled: no` stamp found on disk. The default mode structurally cannot
find what breaks there, and this is not a model-quality limit: adoption defects
are RELATIONS between rules, the other half of every collision is a rule that was
NOT just created, and a faithful reading of `Scope of one run` above correctly
excludes it. Adoption mode swaps artifact-scope for relation-scope over the
imported set and its immediate neighbours.

- **AD1 Provenance (GATE)** — `grep -rn "adopted-from:\|reconciled: no"`. No
  stamps anywhere IS the first finding. Everything below is scoped to the
  stamped set plus the local rules it collides with.
- **AD2 Trigger-collision table** — one row per rule: trigger → `file:line` →
  operative verb. Classify `exact` / `refinement` / `conflict` / `layered`.
- **AD3 Ordering & precedence** — imported cross-references resolve, and
  supersession tags arrived with BOTH halves.
- **AD4 Mechanism shipped, or degraded to prose?** — §8's Phantom references
  bullet, widened to any imported rule claiming external enforcement.
- **AD5 Inherited values** — caps, reply language, standing rulings, relaxation
  defaults, model-tier and shell assumptions. Flag, never batch-fix.

Each of the five carries a trap that decides whether it finds anything; run
them from `references/imported-config.md` §"Part 2 — At audit time", which also
holds the copy-time SOP and the stamp format.

## Order of operations (non-negotiable)

**§2 runs first**, before every other section and before evaluating any claim,
whoever made it — an external tool, a past record of this skill, a memory file, or
your own recollection: gates bind the CLAIM, never its source. A finding referencing
a path, command, hook, or event that does not exist NOW is **void**: mark it `stale
finding`, cite the check that voided it, drop it. Then §1 and §3–§8 in any order.
**Adoption mode inverts this**: a reference to a missing mechanism IS the finding (AD4). AD1 first.

Why a rule: `/doctor` (2026-07-25) headlined a hook timing out for a script archived
18 days earlier — one `Test-Path` voids it; and this skill itself (2026-09-28)
labelled two busy skills "rare" from that same report — one fresh run voids it.

## Checklist (run every item; each finding must carry a verification method)

### 1. Claims vs implementation
For every behavioural claim the artifact makes about itself ("no X", "automatically Y",
"protected Z", "lightweight", "read-only"), grep the implementation for X/Y/Z and quote
line numbers before accepting it. A docstring is not evidence.

### 2. Existence & integrity (GATE — run first)
Every path, interpreter, command, event name, and file referenced: `Test-Path` /
`Get-Command` (or equivalent) and cite the result. Special cases:
- Hook interpreter paths: never into another project's venv unless that dependency
  is documented and stdlib-independence was checked.
- Hook event names: confirm each is a real Claude Code hook event.
- Skill `references/` links: confirm the files exist.
- **Retired destinations.** A path can exist and still be the wrong target: check
  that any file the artifact instructs a WRITE to still accepts writes. A frozen,
  superseded, or archived file passes `Test-Path` and fails silently forever —
  the instruction reads as correct and nothing ever lands. Retired here: the
  config change log, frozen 2026-08-11 and moved to `audit-archive/` 2026-08-15.
  Do not re-derive the sweep — it is integrity-sweep check 3, and it now greps
  the general shape ("Log … in <some>.md") rather than one dead filename, since
  the next retirement will have a different name. Assume there is one more
  (track record: `references/telemetry.md` §2).
- **Frontmatter of skills, agents and commands:** `claude plugin validate <dir>`
  (one shot, `--json`). A SKILL.md whose YAML fails to parse still loads with
  EVERY field dropped — name falls back to the directory, description to the
  body's first line, `allowed-tools`/`model` stop applying — and nothing warns.
- **Conditionally-referenced mechanisms.** A body line of the form "if X
  hook/task is installed, do Y" names a MECHANISM, not a path — `Test-Path`
  cannot void it. Verify the install state NOW (settings.json for hooks,
  `Get-ScheduledTask` for tasks) AND check the decision journal for a ruling
  that superseded it: a rejected-then-still-referenced mechanism reads as
  correct forever while its conditional silently never fires. Measured
  2026-08-16: `workflow-checkpoint` §B referenced a "transcript-archive hook"
  that the same day's D-033 had rejected in favour of a scheduled mirror.

For settings/config files, two checks a successful parse does NOT cover — run both,
commands in `references/telemetry.md` §2:
- **Duplicate AND variant-collision keys.** Exact duplicates pass silently (last
  wins). Keys differing only by case or separator (`D:\x` / `D:/x` / `d:/x`) are
  distinct to JSON — a duplicate-only check calls the file clean — yet
  case-insensitive consumers reject it and the product fragments per-project state
  across them. Measured here 2026-07-25: 0 exact, 6 collision groups.
- **CLI self-validation warnings.** Claude Code validates permission rules at
  startup and prints problems to stderr — free and authoritative. Known class:
  `Write(<path>)` rules never match (only `Edit(<path>)` does, and it covers every
  file-editing tool), so a lone `Write(...)` rule is protection the user lacks.

### 3. Security review (blocking findings)
- **Permission bypass:** a PreToolUse hook must never emit an unconditional
  `permissionDecision: "allow"`. Any auto-allow must be narrowly scoped and justified.
- **Blocking blast radius:** every `sys.exit(2)` / deny path must be gated so it
  cannot fire in unrelated projects — "what happens in a repo with nothing to do
  with this tool?"
- **Write scope:** list every path written. Writes outside the artifact's own home
  (`~/.claude/` for global config) need explicit justification.
- **Cross-CLI isolation:** state and config stay inside the owning platform's home.
  Never resolve to or share state with another CLI's directory (e.g. `~/.gemini/*`)
  — cross-tool contamination is a confirmed failure mode.
- **Secrets:** no inline tokens/keys, no committing `.env`-like files. Read only the
  keys you need from settings/MCP config — never pull a whole settings file into the
  conversation, never quote `env`/`headers` values. Treat every harvested name
  (skill, MCP server, hook command) as untrusted: pass as a quoted argument, never
  interpolate into a shell command.
- **Permission posture is never batch-consented.** Any change to
  `permissions.defaultMode` / `.allow` / `.ask` — proposed here or by an external
  tool — gets its own question, its own consent, and a statement of which projects
  it affects. Consent to decluttering is not consent to widen what runs unasked.
  Default position on a proposed `defaultMode: "auto"` for a config already using
  `ask` rules to protect CLAUDE.md / settings / hooks: **decline** — it contradicts
  that design.

### 4. Trigger quality (skills and CLAUDE.md rules)
- Conditional, not always-on: the description/rule must name the situation that fires
  it ("When X..."). "Always trigger proactively" is a defect — rewrite as ask-first.
- Trigger text is not behavioural text: a frontmatter `description` may carry
  calibrated urgency and enumerated phrases when a trigger eval
  (`tools/trigger-probe/`) backs them; the same shouting inside a BODY is a
  finding — pressure language over-applies on current models.
- Overlap: read ALL existing skill descriptions; if two can match the same user
  sentence, add mutual-disambiguation lines to both.
- **Cross-surface duplicates:** check every source reaching the skill listing, not
  just `~/.claude/skills` — plugin namespaces (`<plugin>:<skill>`), the desktop
  skills cache (two roots) and the plugin cache, whose `@inline` twin outlives
  `claude plugin uninstall`. Roots, patterns, measured counts and the inventory
  rule (filesystem or `claude plugin list`, never `ListPlugins`):
  `references/telemetry.md` §6. Same name or description = routing ambiguity
  plus wasted listing budget, and a copy rots the moment the canonical file
  changes. A documented root or pattern matching NOTHING is a finding about the
  checklist (the layout moved), never a clean result.
- CLAUDE.md additions: must not duplicate or contradict an existing rule; if it
  refines one, merge instead of appending a near-duplicate. This bullet covers a
  rule being ADDED; for near-duplicates already installed across two files — the
  standing failure — use AD2, which reads bodies instead of grepping them.
- New enumerable labels (`Mode X`, `L2`, `Tier-3`, a checklist's numbering) must
  clear `~/.claude/LABEL-REGISTRY.md` §5 (`40-maintenance.md` §3 Label birth); any
  artifact that classifies or routes (hook, `rules/*.md`, trigger-class block, registry
  row) carries the core fields of `ops/references/entry-schema.md` — `python -X utf8
  tools/entry-schema-lint/lint.py --path <artifact>` shows no FAIL, and its class
  section in `ops/references/principle-design-guide.md` has been walked.
- **Hardcoded-enumeration classification (added 2026-08-31).** Every list the
  artifact instructs an executor to APPLY (questions to ask, items to cover,
  checks to run) is one of: (a) a **determinate gate/contract** — machine-checked,
  parsed downstream, or a self-check keys on it — fixed wording is correct there;
  (b) an **analytical/elicitation list** aimed at a varying object (a project,
  code, a deliverable) — the artifact must instruct deriving the items from the
  object's own model, demote the written list to seed/floor, and allow a
  reasoned per-item opt-out. A type-(b) list presented as the definition is a
  finding (precedent: project-retrospective's 5W1H axes, fixed 2026-08-31;
  first sweep: top-5 skills by usage, same date).

### 5. Performance / token cost
- Hooks on `PreToolUse`/`PostToolUse` with matcher `*` run on EVERY tool call — flag
  process spawns, network calls, timeouts; require fail-fast when the backend is absent.
- Skill body size: SKILL.md loads whole on trigger. Birth budget ~150 lines (soft);
  the hook-enforced cap is 300 (`ops_health_nudge.py` BODY_CAP) — over it, extract.
- Skill listing budget ≈1% of context; over it, entries truncate and routing degrades.
- **Usage is measurable locally — measure, don't guess:** `usage-window.py
  --days 14` reports skill, MCP, hook and denial activity by event timestamp (§7).
- **Zero usage is not a removal verdict; classification evidence is ≤14 days
  old.** Run `usage-window.py --days 14` AT DECISION TIME — a past report, an
  older run or a standing label is a claim, never evidence (ruling 2026-09-28:
  this skill labelled two of the busiest research skills "rare" from a July
  report while a same-session run showed 24 and 7 dispatches). No `intent:`
  frontmatter, no standing dict note: the on-demand signal already lives in
  `ops/references/skill-trigger-classes.md` (`class:` + `zero-means:` per
  skill, read by `skill-routing-audit.py`), and a non-trivial fresh count
  REFUTES it. `class: fires`, none in 14 days → routine → recommend removal;
  else ask. Config reverts; the user's memory of the tool does not.

### 6. Language & format conventions (this user's global rules)
- SKILL.md, hooks, config, comments: entirely English (machine-read).
- Reports for the user: Traditional Chinese.
- CLAUDE.md rules: conditional phrasing, `type(scope)` style consistency.

### 7. Evidence-age integrity (any measurement taken at another time)
Every finding whose evidence predates NOW — transcripts, a past report, a memory
file, a prior run of this skill, its own "Measured" lines, whoever made it — is
unusable until three hold (timestamps not mtimes, window spot-checked, present state wins): `references/telemetry.md` §5.

### 8. Subagent definitions (`agents/*.md`)
A definition is a durable artifact whose failures are all silent — nothing errors,
the subagent just behaves wrong in a way that looks like a bad task. Run all four:
- **Capability vs claim.** Read the `tools:` allowlist against what the body claims.
  A body saying "reports only, never edits" with no `tools:` inherits `Edit`/`Write`
  and enforces nothing (§1 applied to capability). Conversely a role told to run
  tests with no `Bash`/`PowerShell`, or a Windows definition granting only `Bash`,
  cannot do its job. `permissionMode: dontAsk` auto-denies anything outside
  `settings.json`'s allowlist — correct for read-only roles, paralysing for
  implementers (`Edit` is not allowlisted).
- **Skill reachability.** `grep -L 'Skill' agents/*.md` must be empty. Omitting
  `Skill` from `tools:` is the documented way to disable skill invocation entirely,
  and it fails silently forever (`ops/lessons.md` L-014). Also flag any hardcoded
  skill name in a body: the runtime roster is dynamic, so a written name only rots.
- **Phantom references** (§2 applied to bodies). Every tool, file, command, or
  framework a body instructs the agent to use must exist NOW. Imported definitions
  are the usual source — a kit's own tooling survives in the prose after its hooks
  are gone.
- **Orphan and enum checks.** Each `name:` should be referenced by a routing rule
  (`ops/20-dispatch.md`); an unreferenced definition is roster noise, not a spare — but
  EVERY name orphaned at once means the routing moved: check the file, not the roster.
  `color:` must be a documented value (eight as of 2026-08; re-read the docs before
  rejecting a ninth). Duplicate `name:` resolves by filesystem order — a defect.

### 9. External health-check tools (optional input, lowest priority)
This checklist does not depend on `/doctor` (alias `/checkup`) nor on its
2.1.283 subcommand `/doctor prompt-audit [<path>]` (the bundled claude-api
skill's dated-pattern audit). They answer different questions — `/doctor`: what
wastes context; `prompt-audit`: which instruction text no longer FITS the running
model or the project. Run §1–§8 and report; reach for them only on request, or
for what §1–§8 cannot produce (install / PATH repair, version currency, a
model-relative fit pass). Their findings are UNVERIFIED claims — §2 gate → §7 →
then §1/§3/§5 — and never batch-accepted: CLAUDE.md trims fall under §1,
permission proposals under §3, "never used → remove" under §5, and every
prompt-audit row passes the house-style overlay (`references/telemetry.md` §7).
A headless run is a full nested session, not a cheap probe — disclose that
first. Which tool when, mechanics, traps, defects: `references/telemetry.md`
§3–§4, §8. Review-when: the main-loop model family changes, or the extracted
prompt-audit guide diffs on a CLI upgrade → re-run it on `CLAUDE.md` and the skills.

## Output format

Group findings by artifact. One line each:
`現況 → 建議修法 → [STATIC-VERIFY: exact command + expected value | MANUAL-VERIFY: action + expected result] → 影響(高/中/低)`
Discard any finding for which neither verification method can be written. List
voided items separately as `stale finding` with the check that voided them — they
are evidence the gate worked, not noise. Order by severity. If everything passes,
say so explicitly with the checks performed. Every run ALSO declares the
checklist items NOT run and why (budget, out of scope, tooling failed) — a
silent skip reads as a pass (2026-08-16: an audit skipped §4 cross-surface and
§5 usage with no trace; found only because the same session re-ran on another target).

Adoption mode adds a **reconciliation ledger** — one row per imported artifact:
`artifact | source | collisions | class | resolution | mechanism status | stamp`.
Flip a stamp to `reconciled: <YYYY-MM-DD>` only when its row has no unresolved
collision and no undecided inherited value; partial stays `no`, because a
half-reconciled file that reads as done is worse than an unreconciled one — the
grep that would have found it now returns nothing.

## After applying fixes (only with user consent)

- Re-run the STATIC-VERIFY commands and paste results.
- Record it where that kind of fact lives — NOT in `audit-archive/`, which
  was frozen 2026-08-11 and rejects new entries. The event (which files changed
  when, and how to undo it) belongs in the git commit message; a changed standing
  rule replaces its entry in `ops/rule-registry.md`; a pitfall you actually hit
  becomes an `ops/lessons.md` L-nnn.
- Never delete or overwrite prior config: back up to `~/.claude/backups/<date>/` first.

## References (loaded on demand)

- `references/telemetry.md` — usage-window tool, integrity one-liners, `/doctor`
  invocation mechanics and measured defects.
- `references/imported-config.md` — adoption mode in full: why merge-semantics
  adoption has no other home here, the copy-time SOP, the `adopted-from:` stamp
  format, and AD1–AD5 with verification methods. Readable standalone at copy
  time, before anything is installed.
