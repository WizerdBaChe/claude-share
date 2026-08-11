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
| `README.md` | Orientation: what each share folder holds. |
| `CHANGELOG.md` | This repo's own sync history — when each share was copied, what changed. |
| `Global_skill_update.md` | The source environment's evolution log. **Frozen 2026-08-11** — historical reading only; going forward, standing rationale lives in `claude-ops/ops/rule-registry.md` and per-change detail lives in commit messages. Still the single most informative narrative file here. |
| `AGENTS.md` | This map. |
| `LICENSE` | MIT. |
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
| `code-review-deep-checklist` | Deep/holistic code review: single review, project health, dependency fitness. |
| `config-self-audit` | Auditing one config artifact — a skill, hook, or rule — cheaply. |
| `design-system-suite` | Design tokens and contracts across a multi-product frontend suite. |
| `env-cleanup` | File-level cleanup of a config environment or project tree; archives, never deletes. |
| `literature-search-extract` | Finding scholarly sources and extracting into evidence tables, with citation traceability. |
| `motion-design` | Motion/animation methodology + Three.js. `vendor/lottiefiles/` is third-party MIT, verbatim. |
| `product-design-thinking` | Heavyweight design mode for a new product: prior-art sweep, then build-ready docs. |
| `project-retrospective` | End-of-project extraction of lessons into a guide + rules snippet. |
| `scientific-research-guide` | Research-methodology advisory. **Domain profiles excluded from this share** — see `domains/README.md`; the template, manifest format, and expansion spec ship. |
| `security-deep-checklist` | Defensive security audit: code, deployment posture, detection readiness. |
| `skill-share-packaging` | Exporting a skill for others, or auditing a downloaded one. Includes `scripts/prescan.py`. |
| `workflow-checkpoint` | Phase archiving and context rebuild across long multi-session projects. |

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

**Retired 2026-08-11**: the `refs/` method-playbook folder and its compile step. Method depth is now delegated to each target agent's own official docs (`interop.py`'s `delegation_block()`) rather than shipped as curated prose — the trigger never ported, only the content did, and that degraded to "read either always or never". See `MIGRATION-MAP.md` and `README.md` for the reasoning.

## `thinking-notes/` — essays, not rules

Twelve numbered notes (`01`–`12`) on one-shot delivery, debugging epistemology,
unverifiable domains, ask-vs-decide, cross-language asymmetry, AI reading AI,
delegation economics, implementation-capability gaps, and legacy revival. These are
argument, not policy — nothing here binds a reader. `README.md` indexes them.
