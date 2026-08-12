# Migration Map — layered portability of the ~/.claude environment

Machine-and-human reference for what transfers to other agent systems, how,
and what deliberately does not. Consumed by the genesis prompt during
mechanism-layer translation. Human operating manual: README.md (中文).

## Layer model

| Layer | Assets | Portability | Sync method |
|---|---|---|---|
| Instructions | portable subset of CLAUDE.md (distilled into `portable-core.md`) | HIGH — plain prose | Deterministic compile: `interop.py build` (true sync) |
| Method content | **RETIRED 2026-08-11** — was: curated playbooks in `interop/refs/` | NONE. The content ported; the TRIGGER never did, and "instructed read" is not a trigger | Delegated: `delegation_block()` tells the target agent to consult ITS OWN current official docs and propose the adaptation |
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
- **Reference-compile** — **RETIRED 2026-08-11** (user ruling). It shipped
  ~20K of agent-neutral method playbooks to a target-side `interop-refs/`
  folder plus a prose routing index. The degradation recorded right here
  turned out to be fatal rather than acceptable: mechanical trigger →
  instructed read means no target platform can fire the text at the right
  moment, so it is read either always or never. Playbooks archived to
  `archive/interop-refs-2026-08-11/` (their SOURCES are untouched and still
  canonical). Replaced by delegation — see the class below. The governing
  principle is now: **preference ports, method does not.**
- **Delegate to the target** (→ `delegation_block()` in the generated
  AGENTS.md): everything method-shaped. The block states that the rules above
  it are the user's own standing preferences, not derivable from any docs and
  binding verbatim; and that for method depth the agent must read THIS
  platform's current official documentation for its own extension points, then
  propose the adaptation to the user before installing anything durable. This
  is the same principle `genesis-prompt.md` already applied to the mechanism
  layer — "you know your own platform best" — extended to the method layer.
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

## Target registry (opencode row re-verified 2026-08-11 against the CLI and
the official docs; the other two are frozen at 2026-07-10 and OFF. Re-verify
before adding targets — these locations are volatile facts)

| Target | Global rules file | Profile | Mechanism extension points |
|---|---|---|---|
| opencode | `~/.config/opencode/AGENTS.md` | light | `~/.config/opencode/opencode.json` — `permission` (allow/ask/deny, per-tool patterns, LAST match wins), `agent(s)/`, `command(s)/`, `skill(s)/`, `plugin` (TS/JS hooks incl. `tool.execute.before`, `permission.ask`), `mcp` |
| codex | `~/.codex/AGENTS.md` | **SYNC OFF** (was: full) | `~/.codex/config.toml` (sandbox/approval), command hooks (`/hooks` in TUI) |
| Antigravity | `~/.gemini/AGENTS.md` (cross-tool, >=1.20.3) | **SYNC OFF** (was: full) | `~/.gemini/GEMINI.md` (Antigravity-specific overlay, higher priority); `.agent/rules/` per workspace |

Notes:
- **codex sync is OFF (user ruling 2026-08-11)**, marked `"disabled"` in
  `interop.py` TARGETS. Reason: that environment cannot use this one's design
  wholesale — its ops tree lives at `~/.codex/ops/codex-ops/` and its own
  `05-authority.md` still specifies a 4-section boundary contract against this
  side's 5 — and the compiled output was judged not worth overwriting a
  hand-tuned file with. Codex-side changes are made FROM codex, by hand.
  `build` will not write there (verified: real `cmd_build()` run against a
  codex-only target registry left the file's sha256, size and mtime identical
  and created no `interop-refs/`), and `status` reports it as `[off]` without
  counting it as drift. Re-enabling is not a one-liner in practice: the file
  there is now foreign, so `build` would back it up and replace it.
- **Antigravity sync is OFF (user ruling 2026-08-11)**, marked `"disabled"` in
  `interop.py` TARGETS: the agent is no longer used. Leftovers from the
  2026-07-10 build at the target are deliberately not touched from here —
  removing them is the user's call on that machine, not this repo's.
- **opencode CLI verified working 2026-08-11**: `opencode` v1.18.16 on PATH at
  `~/AppData/Roaming/npm/opencode` (npm global). The Electron desktop app
  (v1.18.11, `AppData/Local/Programs/@opencode-aidesktop/`) is a SEPARATE
  install and is not a CLI — `OpenCode.exe --version` opens the GUI. Useful
  local, zero-exposure introspection: `opencode debug config` (resolved
  config), `opencode debug skill` (every skill it can see), `opencode models`.
- **Rules precedence, quoted from the official docs 2026-08-11**: (1) local
  files walking UP from the cwd — `AGENTS.md`, then `CLAUDE.md`; (2) global
  `~/.config/opencode/AGENTS.md`; (3) `~/.claude/CLAUDE.md` "unless disabled".
  First match wins per category. So deploying our global AGENTS.md does
  supersede (3) — but it does NOT stop opencode from reading a PROJECT's
  `CLAUDE.md` at (1), which outranks it. Any expectation that deployment gives
  full control of what opencode reads is wrong.
- **INBOUND dependency the layer model did not account for** — *the 2026-08-11
  entry was RIGHT; a same-day "correction" was wrong and is retracted below.*

  **Resolved 2026-08-12: `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` is set** (user
  decision), and `~/.agents/skills/` is retired to
  `archive/2026-08-12-agents-skills-retired/`. opencode now supplies itself from
  the share repo instead.

  The measurement trail, because it inverted twice and the shape is instructive:
  `opencode debug skill` first returned only 3 entries — 1 built-in + 2 from
  `~/.agents/skills/`, zero from `~/.claude/`. That was read as "the 2026-08-11
  claim named the wrong path". **It did not.** `~/.agents/skills/` was
  SHADOWING the `~/.claude/` scan. Retiring it flipped the count from 3 to 15,
  with all 14 live skills now listed from `~/.claude/skills/` — exactly what the
  original entry said, and momentarily MORE exposure than before, in the middle
  of a change meant to reduce it. Verified fix: unset → 15 entries;
  `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` → 1; `OPENCODE_DISABLE_EXTERNAL_SKILLS=1`
  → 1. Per opencode's own built-in skill, both flags "skip the external skill
  scans under `~/.claude/` and `~/.agents/`".

  Lesson: an observation taken while a SHADOWING artifact is in place measures
  the shadow, not the system. Removing the shadow is part of the measurement,
  not a separate step.

  What exists instead is worse and was invisible: **`~/.agents/skills/` holds a
  second physical copy of the entire 14-skill corpus** — real directories, not
  symlinks — frozen at **2026-08-03**. All 14 differ from live. Ten differ by
  1–7 bytes (line-ending artefacts of the copy); **four are substantively
  stale**, worst `config-self-audit` at **−7,235 bytes**, missing the whole
  adoption mode added 2026-08-12. So opencode reads a rotting snapshot, and
  only 2 of the 14 surface at all.

  This is a second source of truth for the corpus, which `40-maintenance.md` §2
  ("a rule lives in exactly one file") forbids at rule scale and nothing was
  watching at corpus scale: `ops_health_nudge` check 10 walks `~/.claude/skills/`
  only, and `config-self-audit` §4 names the plugin roots, not this one.

  Kill switches (`OPENCODE_DISABLE_EXTERNAL_SKILLS=1`,
  `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`) are now the wrong lever: the second
  would change nothing observable, the first would only hide the 2 stale
  entries. **The live decision is what to do with `~/.agents/skills/`** — refresh
  it deliberately, retire it, or keep it frozen on purpose. Open, user's call;
  routing context in `ops/references/inbound-routing.md`.
- `~/.gemini/AGENTS.md` is also read by Gemini CLI; keep its content
  agent-neutral (which portable-core already guarantees).

## Leak gate (added 2026-08-11)

`build` assembles every enabled target's payload in memory, scans it, and only
then writes; a hit aborts the whole build with exit 1 and writes NOTHING
(scanning inside the write loop would leave earlier targets already written
when a later one trips). `interop.py scan` runs the same gate standalone and
also covers `portable-core.md` itself. Patterns: email, JWT, prefixed API keys
(`sk-`/`gh?_`/`AKIA`/`xox?-`), secret-shaped assignments, hex runs >=32 chars
(shorter would flag the git short hash the source stamp needs), and the
account name inside a filesystem path. The account name is read from the
environment at runtime -- hardcoding it would make `interop.py` itself the
leak. Verified 2026-08-11 by planting one secret of each class inside a real
block: 6/6 aborted with nothing written, control build unaffected. The probe
asserts the plant actually reached the payload first -- two earlier versions
silently tested nothing because the plant landed outside the block markers.

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
