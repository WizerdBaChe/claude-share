# Migration Map — layered portability of the ~/.claude environment

Machine-and-human reference for what transfers to other agent systems, how,
and what deliberately does not. Consumed by the genesis prompt during
mechanism-layer translation. Human operating manual: README.md (中文).

## Layer model

| Layer | Assets | Portability | Sync method |
|---|---|---|---|
| Instructions | portable subset of CLAUDE.md (distilled into `portable-core.md`) | HIGH — plain prose | Deterministic compile: `interop.py build` (true sync) |
| Method content | curated playbooks in `interop/refs/` (distilled from skill bodies / ops rubrics) | HIGH for the content; the TRIGGER does not port | Deterministic compile to target-side `interop-refs/` + prose routing index in AGENTS.md (`interop.py build`) |
| Mechanisms | hooks (`model_cap_guard.py`, `ops_health_nudge.py`), permissions (`settings.json`), skill routing | LOW — bound to each platform's extension points | Agent-assisted translation via `genesis-prompt.md`, stamped, re-translated on staleness flag |
| Memory / state | `projects/<slug>/memory/`, sessions, `ops/environment.md` | NONE by design | Never synced. Cross-CLI isolation is a standing ruling. |

## Portability classes (per asset)

- **Verbatim-compile** (→ portable-core.md blocks): language rules, git
  workflow, evidence-over-claims, decision charter, pre-existing-issue
  attribution, file hygiene, canonical-method discipline, volatile-fact
  verification, done definition, approach-wrong signals, scope restraint.
- **Translate per target** (genesis prompt): permission boundaries,
  cost/model-cap enforcement, health/anti-bloat checks. If the target has
  no equivalent extension point, DEGRADE to a prose rule in its AGENTS.md
  and record the loss in the genesis output (degradation = losing
  mechanism-over-prose; the loss must be visible, not silent).
- **Reference-compile** (→ `interop/refs/*.md`, registry in `interop.py`
  `REFS`): high-value methodology whose CONTENT is plain prose but whose
  TRIGGER is platform machinery. The content is manually distilled into an
  agent-neutral English playbook (same curation discipline as
  portable-core.md — never a verbatim copy of the skill/ops file, which is
  full of platform-specific references) and compiled to the target-side
  `interop-refs/` folder; a prose routing index ("situation → read this
  file") is appended to the generated AGENTS.md. Known degradation:
  mechanical trigger → instructed read; hit rate is inherently lower and
  the loss is recorded here, not hidden. Birth budget applies: full profile
  only, registry stays small. Current refs: design-protocol
  (product-design-thinking), judgment-protocol (ops/30-judgment R7/R8),
  phase-log-protocol (workflow-checkpoint).
- **Do not migrate**: skill ROUTING (skill-trigger-dict.md, automatic
  triggering), ops/ dispatch framework (assumes platform subagent
  machinery), settings.json machine-bound paths, ops/environment.md
  (environment facts must be re-established per platform, never assumed),
  memory, credentials. Skill/ops BODIES are eligible for reference-compile
  above when their value justifies the context rent — the raw files
  themselves never ship.

## Profiles

- **light** — lightweight-task agents. Minimal rent: language, git,
  evidence, decision charter, pre-existing issues, file hygiene.
- **full** — goal-oriented agents. light + judgment core: visual
  acceptance, canonical-method discipline, volatile facts, done
  definition, approach-wrong signals, scope restraint.

Superset rule: light ⊂ full. A block tagged `light` must also carry `full`.

## Target registry (verified 2026-07-10; re-verify before adding targets —
these locations are volatile facts)

| Target | Global rules file | Profile | Mechanism extension points |
|---|---|---|---|
| opencode | `~/.config/opencode/AGENTS.md` | light | `opencode.json` (permissions), JS/TS plugins (hooks) |
| codex | `~/.codex/AGENTS.md` | full | `~/.codex/config.toml` (sandbox/approval), command hooks (`/hooks` in TUI) |
| Antigravity | `~/.gemini/AGENTS.md` (cross-tool, >=1.20.3) | full | `~/.gemini/GEMINI.md` (Antigravity-specific overlay, higher priority); `.agent/rules/` per workspace |

Notes:
- opencode falls back to reading `~/.claude/CLAUDE.md` when its own global
  AGENTS.md is absent. Deploying our AGENTS.md overrides that fallback —
  this is desired (the fallback fed it Claude-specific noise).
- `~/.gemini/AGENTS.md` is also read by Gemini CLI; keep its content
  agent-neutral (which portable-core already guarantees).

## Sync invariants

1. **One-way flow.** `~/.claude` is canonical. Target-side files are build
   artifacts. Lessons learned inside another agent flow back by editing
   the canonical source (CLAUDE.md / portable-core.md), then rebuilding.
   Never edit a generated AGENTS.md in place.
2. **Staleness over mirroring.** Sync = freshness detection
   (`interop.py status`) + regeneration, not real-time mirroring.
3. **Curation gate.** portable-core.md is a manual distillation of
   CLAUDE.md. When CLAUDE.md changes, `status` flags re-curation; a human
   (or main-session Claude) reviews the diff, updates portable-core.md if
   the change is portable, then runs `curated`.
4. **Living proof.** After any mechanism-layer translation (genesis run)
   and after first deploy to a new target, run the acceptance evals
   (`acceptance-evals.md`) inside the target agent. Compile-only refreshes
   of the instructions layer need only a spot-check.
5. **Archive, never delete.** Foreign files at target paths are renamed to
   `*.pre-interop*.bak`, not removed.
