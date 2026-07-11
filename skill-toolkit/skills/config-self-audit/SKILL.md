---
name: config-self-audit
description: >-
  Lightweight, read-only audit of ONE durable Claude Code config artifact: a skill,
  hook, global CLAUDE.md rule, or settings.json change. Trigger when the user asks to
  audit/check/review such an artifact, when a NEW skill/hook was just authored in this
  conversation (run before declaring it done), or when asked whether a proposed global
  rule is safe/efficient. Deliberately cheap (a few Reads + greps); fixes only after
  consent. NOT for authoring skills (→ skill-creator) or file-level cleanup (→
  env-cleanup). Full disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Config Self-Audit

Cheap, repeatable safety/consistency check for durable config under `~/.claude/`
(or a project `.claude/`). Derived from a full external audit (2026-07-03); this is
the distilled version without heavy data mining.

## Scope of one run

Audit ONLY the artifact(s) named or just created — not the whole config tree.
Budget: a handful of Read/Grep/Test-Path calls. If a finding would require mining
session logs or running servers, note it as out-of-scope instead of doing it.
This checklist is deliberately narrow: when the user asks for a COMPREHENSIVE
or from-scratch review (全面/加強), run the checklist first, then hand off to
the clean-sheet extension in `ops/30-judgment.md` R8 pass 1 — do not widen
this skill's own budget to cover it.

## Checklist (run every item; each finding must carry a verification method)

### 1. Claims vs implementation
For every behavioural claim the artifact makes about itself ("no X", "automatically Y",
"protected Z", "lightweight", "read-only"), grep the implementation for X/Y/Z and quote
line numbers before accepting the claim. A docstring is not evidence.

### 2. Existence of everything referenced
Every path, interpreter, command, event name, and file the artifact references:
run `Test-Path` / `Get-Command` (or equivalent) and cite the result. Special cases:
- Hook interpreter paths: must not point into another project's venv unless that
  dependency is documented and stdlib-independence was checked.
- Hook event names: confirm the name is a real Claude Code hook event.
- Skill `references/` links: confirm the files exist.

### 3. Security review (blocking findings)
- **Permission bypass:** a PreToolUse hook must never emit an unconditional
  `permissionDecision: "allow"`. Any auto-allow must be narrowly scoped and justified.
- **Blocking blast radius:** any `sys.exit(2)` / deny path must be gated so it cannot
  fire in unrelated projects. Ask: "what happens in a repo that has nothing to do
  with this tool?"
- **Write scope:** list every path the artifact writes. Writes outside its own home
  (`~/.claude/` for global config) need explicit justification.
- **Cross-CLI isolation:** state and config must stay inside the owning platform's
  home (`~/.claude/`). Never resolve to or share state with another CLI's directory
  (e.g. `~/.gemini/*`) — cross-tool state contamination is a confirmed failure mode.
- **Secrets:** no tokens/keys inline; no committing `.env`-like files.

### 4. Trigger quality (skills and CLAUDE.md rules)
- Conditional, not always-on: the description/rule must name the situation that fires
  it ("When X..."). "Always trigger proactively" is a defect — rewrite as ask-first.
- Overlap: read the descriptions of ALL existing skills; if two descriptions can match
  the same user sentence, add explicit mutual-disambiguation lines to both.
- CLAUDE.md additions: check the new rule does not duplicate or contradict an existing
  rule; if it refines one, merge instead of appending a near-duplicate.

### 5. Performance / token cost
- Hooks on `PreToolUse`/`PostToolUse` with matcher `*` run on EVERY tool call — flag
  process spawns, network calls, and timeouts there; require fail-fast when the
  backend is absent.
- Skill body size: everything in SKILL.md loads into context on trigger. If >~150
  lines, move detail to `references/` files loaded on demand.
- A rule that fires on every turn is noise — gate it or drop it.

### 6. Language & format conventions (this user's global rules)
- SKILL.md, hooks, config, comments: entirely English (machine-read).
- Reports for the user: Traditional Chinese.
- CLAUDE.md rules: conditional phrasing, `type(scope)` style consistency with the
  existing file.

## Output format

Group findings by artifact. One line each:
`現況 → 建議修法 → [STATIC-VERIFY: exact command + expected value | MANUAL-VERIFY: action + expected result] → 影響(高/中/低)`
Discard any finding for which neither verification method can be written.
Order by severity. If everything passes, say so explicitly with the checks performed.

## After applying fixes (only with user consent)

- Re-run the STATIC-VERIFY commands and paste results.
- Append an entry to `~/.claude/Global_skill_update.md` (what changed + absolute timestamp).
- Never delete or overwrite prior config: back up to `~/.claude/backups/<date>/` first.
