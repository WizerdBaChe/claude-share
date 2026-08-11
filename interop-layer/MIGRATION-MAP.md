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

- **Verbatim-compile** (→ portable-core.md blocks): language rules,
  environment/shell conventions, git workflow, evidence-over-claims,
  decision charter, pre-existing-issue attribution, file hygiene,
  visual acceptance, canonical-method discipline, volatile-fact
  verification, done definition, failure visibility, approach-wrong
  signals, scope restraint.
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
  moment, so it is read either always or never. Playbooks archived locally
  (their SOURCES are untouched and still canonical in the source
  environment). Replaced by delegation — see the class below. The
  governing principle is now: **preference ports, method does not.**
- **Delegate to the target** (→ `delegation_block()` in the generated
  AGENTS.md): everything method-shaped. The block states that the rules
  above it are the user's own standing preferences, not derivable from any
  docs and binding verbatim; and that for method depth the agent must read
  THIS platform's current official documentation for its own extension
  points, then propose the adaptation to the user before installing
  anything durable. This is the same principle `genesis-prompt.md` already
  applied to the mechanism layer — "you know your own platform best" —
  extended to the method layer.
- **Do not migrate**: skill ROUTING (skill-trigger-dict.md, automatic
  triggering), ops/ dispatch framework (assumes platform subagent
  machinery), settings.json machine-bound paths, ops/environment.md
  (environment facts must be re-established per platform, never assumed),
  memory, credentials.

## Profiles

- **light** — lightweight-task agents. Minimal rent: language, environment,
  git, evidence, decision charter, pre-existing issues, file hygiene.
- **full** — goal-oriented agents. light + judgment core: visual
  acceptance, canonical-method discipline, volatile facts, done
  definition, failure visibility, approach-wrong signals, scope restraint.

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
  wholesale — its ops tree lives at a separate path and its own
  `05-authority.md` still specifies a 4-section boundary contract against
  this side's 5 — and the compiled output was judged not worth overwriting a
  hand-tuned file with. Codex-side changes are made FROM codex, by hand.
  `build` will not write there and `status` reports it as `[off]` without
  counting it as drift. Re-enabling is not a one-liner in practice: the file
  there is now foreign, so `build` would back it up and replace it.
- **Antigravity sync is OFF (user ruling 2026-08-11)**: the agent is no
  longer used. Leftovers from the 2026-07-10 build at the target are
  deliberately not touched from here — removing them is the user's call on
  that machine, not this repo's.
- **opencode CLI verified working 2026-08-11**: a standalone CLI binary is
  on `PATH` via a global package-manager install, separate from any
  Electron desktop app (which is not a CLI). Useful local, zero-exposure
  introspection commands: `opencode debug config` (resolved config),
  `opencode debug skill` (every skill it can see), `opencode models`.
- **Rules precedence, quoted from the official docs 2026-08-11**: (1) local
  files walking UP from the cwd — `AGENTS.md`, then `CLAUDE.md`; (2) global
  `~/.config/opencode/AGENTS.md`; (3) `~/.claude/CLAUDE.md` "unless disabled".
  First match wins per category. So deploying our global AGENTS.md does
  supersede (3) — but it does NOT stop opencode from reading a PROJECT's
  `CLAUDE.md` at (1), which outranks it. Any expectation that deployment gives
  full control of what opencode reads is wrong.
- **INBOUND dependency the layer model did not account for**: opencode
  auto-loads external skills from `~/.claude/skills/<name>/SKILL.md` (stated
  in its own built-in `customize-opencode` skill). This is the reverse of
  interop's one-way flow — the target reads this repo directly, bypassing
  curation, profiles, the leak gate, and the "preference ports, method does
  not" ruling entirely. All skills here would be exposed to it unadapted if
  both environments coexist on the same machine. Kill switches, per the same
  source: `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` or
  `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`. Whether to set one is an open user
  decision — it is not obviously wrong to share the skills, but it IS
  currently unmanaged and invisible.
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
environment at runtime — hardcoding it would make `interop.py` itself the
leak. Verified 2026-08-11 by planting one secret of each class inside a real
block: 6/6 aborted with nothing written, control build unaffected. The probe
asserts the plant actually reached the payload first — two earlier versions
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
   the change is portable, then runs `curated`. Narrowed to CLAUDE.md alone
   on 2026-08-11 — the retired refs/ playbooks no longer need tracking.
4. **Living proof.** After any mechanism-layer translation (genesis run)
   and after first deploy to a new target, run the acceptance evals
   (`acceptance-evals.md`) inside the target agent. Compile-only refreshes
   of the instructions layer need only a spot-check.
5. **Archive, never delete.** Foreign files at target paths are renamed to
   `*.pre-interop*.bak`, not removed.
6. **Nothing identifying leaves this machine.** Every payload is
   leak-scanned before any write (see Leak gate above); a hit aborts the
   whole build.
