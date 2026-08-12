---
name: config-self-audit
description: >-
  Cheap audit of durable Claude Code config; fixes only after consent. DEFAULT
  mode (ONE artifact): a skill, hook, subagent definition (`agents/*.md`), global
  CLAUDE.md rule, or settings.json change — trigger when asked to
  audit/check/review one, when a NEW skill/hook/subagent was just authored here
  (before declaring it done), or when a /doctor-style report needs verifying.
  ADOPTION mode: config copied in from another environment, or a `reconciled: no`
  stamp — audits RELATIONS between rules: trigger collisions, ordering,
  mechanisms that did not ship. NOT for authoring skills (→ skill-creator), ONE
  third-party skill (→ skill-share-packaging), or file cleanup (→ env-cleanup).
  Disambiguation: ~/.claude/skill-trigger-dict.md.
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
  stamps anywhere is itself the first finding: reconstruct the inventory from the
  source and stamp as part of the fix. Everything below is scoped to the stamped
  set plus whatever local rules it collides with.
- **AD2 Trigger-collision table** — one row per rule: trigger condition →
  `file:line` → operative verb. Same trigger twice is a finding **even with zero
  shared vocabulary** — an adaptation pass paraphrases, so grep is blind here and
  the bodies must be read side by side. Classify `exact` / `refinement` /
  `conflict` / `layered`; `refinement` merges into one rule in one file. This is
  the one check allowed to cost more than a single-artifact audit, because it is
  the one the cheap path structurally cannot perform.
- **AD3 Ordering & precedence** — do imported cross-references resolve, and did
  supersession tags arrive with BOTH halves (an orphan tag is decoration, and the
  tagged rules all fire). Do NOT ask "does a precedence statement exist here" —
  `ops/OPS.md` has carried one since birth, so that sub-check returns clean
  always and is ritual (§4.3); it is a finding only when an imported rule asserts
  a DIFFERENT precedence.
- **AD4 Mechanism shipped, or degraded to prose?** — this is §8's **Phantom
  references** bullet, widened past `agents/*.md` to any imported rule claiming
  external enforcement ("hook enforced", "mechanically flagged", "blocked at
  startup"). Read the method there; only two things are added here: that wider
  scope, and that **the §2 gate is INVERTED** — a dangling mechanism reference is
  the live finding, not a reason to void one. Record as `DEGRADED to prose` with
  its consequence; the user chooses install / reword / drop.
- **AD5 Inherited values** — size and cost caps, reply language, standing
  rulings, default relaxation levels, model-tier and shell assumptions. Flag,
  never batch-fix: each is a user-origin premise, and the user of origin is not
  this user.

Procedure, the copy-time SOP, and the stamp format: `references/imported-config.md`.

## Order of operations (non-negotiable)

**§2 runs first**, before every other section and before evaluating any claim
from an external report. Any finding — yours or an external tool's — referencing a
path, command, hook, or event that does not exist NOW is **void**: mark it
`stale finding`, cite the check that voided it, drop it. Then §1 and §3–§8 in any
order. **Adoption mode inverts this**: in adopted config a reference to a missing
mechanism IS the finding, not a reason to void one (AD4). Run AD1 first there.

Why a rule, not a preference: a measured `/doctor` run (2026-07-25) made "a hook
times out on 98.6% of 220 tool calls" its headline finding for a script archived
18 days earlier. One `Test-Path` voids it. Record: `references/telemetry.md`.

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
  the instruction reads as correct and nothing ever lands. Known frozen here:
  `Global_skill_update.md` (2026-08-11). Sweep:
  `grep -rn "Global_skill_update" --include=*.md . | grep -v -E "^\./(backups|archive|audit-archive)"`
  — four live instruction files still pointed at it three weeks after the freeze.

For settings/config files, two checks a successful parse does NOT cover — run both,
commands in `references/telemetry.md` §2:
- **Duplicate AND variant-collision keys.** Exact duplicates pass silently (last
  wins). Keys differing only by case or separator (`D:\x` / `D:/x` / `d:/x`) are
  distinct to JSON — a duplicate-only check calls the file clean — yet
  case-insensitive consumers reject it and the product fragments per-project state
  across them. Measured here: 0 exact, 6 collision groups.
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
- Overlap: read ALL existing skill descriptions; if two can match the same user
  sentence, add mutual-disambiguation lines to both.
- **Cross-surface duplicates:** check every source reaching the skill listing, not
  just `~/.claude/skills` — plugin namespaces (`<plugin>:<skill>`) and the desktop
  skills cache — BOTH roots under `%APPDATA%/Claude/local-agent-mode-sessions/`:
  `skills-plugin/` (15 as of 2026-08-12) and `*/*/rpm/plugin_*/skills/` (35).
  Checking only the first misses the larger one.
  Same name or description = routing ambiguity plus wasted listing budget, and a
  copy rots the moment the canonical file changes.
- CLAUDE.md additions: must not duplicate or contradict an existing rule; if it
  refines one, merge instead of appending a near-duplicate. This bullet covers a
  rule being ADDED; for near-duplicates already installed across two files — the
  standing failure — use AD2, which reads bodies instead of grepping them.
- New enumerable labels (`Mode X`, `L2`, `Tier-3`, a checklist's numbering) must
  clear `~/.claude/LABEL-REGISTRY.md` §4 (`40-maintenance.md` §3 Label birth).

### 5. Performance / token cost
- Hooks on `PreToolUse`/`PostToolUse` with matcher `*` run on EVERY tool call — flag
  process spawns, network calls, timeouts; require fail-fast when the backend is absent.
- Skill body size: SKILL.md loads whole on trigger. If >~150 lines, move detail to
  `references/`.
- The skill listing is budgeted at ~1% of context; once summed descriptions exceed
  it, entries truncate and routing degrades.
- **Usage is measurable locally — measure it, don't guess and don't defer.**
  `python ~/.claude/tools/usage-window.py --days 30` reports per-skill, per-MCP,
  per-hook and denial activity keyed on event timestamps (§7).
- **Zero usage is not a removal verdict.** Classify intent first: `intent: on-demand`
  (domain tool, rare by design — a research or incident skill used twice a year is
  working as intended) vs `intent: routine` (a long-term zero means the trigger
  failed or the need was imagined). Recommend removal only for `routine`; otherwise
  ask. Reversibility is not the counter-argument — the config is reversible, the
  user's memory that the tool existed is not.

### 6. Language & format conventions (this user's global rules)
- SKILL.md, hooks, config, comments: entirely English (machine-read).
- Reports for the user: Traditional Chinese.
- CLAUDE.md rules: conditional phrasing, `type(scope)` style consistency.

### 7. Telemetry window integrity
Any finding derived from session transcripts — yours or an external report's — is
unusable until all three hold:
- **Timestamps, not mtimes.** Selecting the N most-recently-modified transcripts is
  fine; dating an event from those mtimes is not. A resumed session rewrites its
  mtime while its content stays old (measured 2026-07-25: 20 of 50 files skewed
  ≥3 days, max 26).
- **Spot-check any claimed window.** Open one cited finding, confirm its in-file
  `timestamp` falls in the stated range. One check exposes a whole-report skew.
- **Present state wins.** Where telemetry and the filesystem disagree, the
  filesystem is right: downgrade to `stale finding` and say when it was actually
  true (`git log` of the fix is usually one command away).

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
  (`ops/20-dispatch.md`); an unreferenced definition is roster noise, not a spare.
  `color:` must be one of the eight documented values; anything else is an imported
  invention. Duplicate `name:` in one directory resolves by filesystem order — no
  documented precedence — so treat any duplicate as a defect.

### 9. External health-check tools (optional input, lowest priority)
This checklist does not depend on `/doctor` (alias `/checkup`). Run §1–§8 and
report; reach for it only on request, or for what §1–§8 cannot produce (install /
PATH repair, version currency). Its findings are UNVERIFIED claims — §2 gate → §7
→ then §1/§3/§5 — and never batch-accepted: CLAUDE.md trims fall under §1,
permission proposals under §3, "never used → remove" under §5. A headless run is a
full nested session (61 tool calls, measured), not a cheap probe — disclose that
before invoking it. Mechanics, the Git-Bash path-mangling trap, and its measured
defects: `references/telemetry.md` §3–§4.

## Output format

Group findings by artifact. One line each:
`現況 → 建議修法 → [STATIC-VERIFY: exact command + expected value | MANUAL-VERIFY: action + expected result] → 影響(高/中/低)`
Discard any finding for which neither verification method can be written. List
voided items separately as `stale finding` with the check that voided them — they
are evidence the gate worked, not noise. Order by severity. If everything passes,
say so explicitly with the checks performed.

Adoption mode adds a **reconciliation ledger** — one row per imported artifact:
`artifact | source | collisions | class | resolution | mechanism status | stamp`.
Flip a stamp to `reconciled: <YYYY-MM-DD>` only when its row has no unresolved
collision and no undecided inherited value; partial stays `no`, because a
half-reconciled file that reads as done is worse than an unreconciled one — the
grep that would have found it now returns nothing.

## After applying fixes (only with user consent)

- Re-run the STATIC-VERIFY commands and paste results.
- Record it where that kind of fact lives — NOT in `Global_skill_update.md`, which
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
