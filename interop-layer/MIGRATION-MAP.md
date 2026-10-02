# Migration Map — layered portability of the Claude / Codex / ChatGPT environment

Machine-and-human reference for what transfers to other agent systems, how,
and what deliberately does not. Consumed by the genesis prompt during
mechanism-layer translation. Human operating manual: README.md (中文).

## Layer model

| Layer | Assets | Portability | Sync method |
|---|---|---|---|
| Instructions | portable subset of CLAUDE.md (distilled into `portable-core.md`) | HIGH — plain prose | Deterministic compile to file-based targets: `interop.py build` (true sync) |
| Method content | **RETIRED 2026-08-11** — was: curated playbooks in `interop/refs/` | NONE. The content ported; the TRIGGER never did, and "instructed read" is not a trigger | Delegated: `delegation_block()` tells the target agent to consult ITS OWN current official docs and propose the adaptation |
| Mechanisms | hooks (`model_cap_guard.py`, `ops_health_nudge.py`), permissions (`settings.json`), skill routing | LOW — bound to each platform's extension points | Agent-assisted translation via `genesis-prompt.md`, stamped, re-translated on staleness flag |
| Distribution / import | skill payloads, portable plugin packages, and supported product import flows | MEDIUM — target surface decides what is actually executable | Target-native packaging or user-selected import; never treat it as a second canonical source |
| Memory / state | `projects/<slug>/memory/`, sessions, `ops/environment.md` | NONE by design | Never synced. Cross-CLI isolation is a standing ruling. |

## Portability classes (per asset)

- **Verbatim-compile** (→ portable-core.md blocks): the user's own standing
  preferences — the rules no documentation can supply, which is exactly why
  they have to travel. The authoritative membership list is the block set in
  `portable-core.md` itself (`parse_blocks()` reads it; `build` prints
  `blocks=`/`bytes=` per target). This file deliberately does not restate
  it: the restatement here still named 11 items on 2026-08-16, five blocks
  behind the real set, while §Profiles a few lines below was current — an
  enumeration kept in two places gets read as fact from whichever copy rots
  first. Membership is decided by a TEST, not by a list: a rule belongs here
  iff it binds the same way on any platform with no platform mechanism
  needed to fire it at the right moment. Anything that needs a trigger is
  method-shaped — see "Delegate to the target" below.
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
  git history (`git show 483435f:archive/interop-refs-2026-08-11/`; their SOURCES are untouched and still
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

## OpenAI migration rule — Core + Adapter + Integration

The reusable part of a skill is not the same thing as the host contract or the
external connection. Classify those parts separately before moving anything:

| Part | Keep / rewrite | Rule |
|---|---|---|
| **Core** | Keep | Domain purpose, decision rules, workflow, output schema, quality bar, references, scripts, assets, and test fixtures that are actually required by the workflow. |
| **Adapter** | Rewrite per target | Tool names, paths, shell/runtime assumptions, file discovery, permission and confirmation semantics, host routing, metadata, and fallback behavior. |
| **Integration** | Add only when separately authorised | MCP servers, connectors, credentials, external actions, and persistent services. Re-authenticate and re-scope them on the target; never copy secrets or pretend a missing connection exists. |

Use the following portability classes:

- **Verbatim-portable**: conversation-only work, user-provided files, and
  general reasoning. Keep the core and change only target metadata or
  packaging when needed.
- **Portable with adapter**: the core remains useful, but the host contract
  must be rewritten for Codex, ChatGPT, or another agent.
- **Not directly portable**: local vaults, CAD/media pipelines, private
  services, credentials, hooks, or continuing external actions. Keep the
  local implementation, or split out a web-capable analysis core and build a
  separately authorised remote integration.

Do not silently delete execution steps to make a skill look portable. If the
target lacks the capability, state the missing evidence and the fallback.

### Skill admission fence for this share

This migration pass updates rules and existing records; it does **not** add a
new skill or plugin. If a later migration proposes a skill, admit it only when
the deliverable is self-contained: one `SKILL.md` plus optional bundled,
repo-local `references/` or static assets that are included with the
deliverable and have no unresolved links.

Do not add or migrate a skill that requires another tool, executable script,
hook, MCP server, connector, database, private vault, unbundled file, remote
service, or persistent process. Such a candidate is `not directly portable` or
deferred until the user separately authorises and supplies the integration.
Official documentation links in this migration map are verification sources;
they are not runtime dependencies of a skill package. Existing skills in this
repo are not duplicated or upgraded under this rule unless the user explicitly
requests that separate scope.

### Codex file target versus ChatGPT package/import surfaces

Codex has a file-based instruction target: the default global file is
`~/.codex/AGENTS.md`, or `$CODEX_HOME/AGENTS.md` when `CODEX_HOME` is set.
`AGENTS.override.md` takes precedence at the same global scope; project and
nested instructions are then discovered from the repository root down to the
current directory. The `codex` entry in `interop.py` therefore compiles only
the portable preference payload, uses `full`, and reports an active override as
`shadowed` instead of claiming that the generated file is live.

ChatGPT Web is **not** a global `AGENTS.md` target. A reusable workflow for
ChatGPT and Codex is distributed as a skill or a plugin. The current portable
skills-only package is:

```text
plugin-root/
├── plugin.json
└── skills/
    └── <skill-name>/
        └── SKILL.md
```

The root `plugin.json` is the portable package format. A Codex/Plugin Creator
scaffold may also provide `.codex-plugin/plugin.json` as a compatibility
manifest; it is not a reason to copy Claude settings into the package. Keep
the skill description specific enough for ChatGPT and Codex to recognise its
scope, use a stable kebab-case package name, and test the package in a new
conversation after installation.

The official import surface is a separate, user-selected operation. The
ChatGPT desktop app can import supported setup and recent work from Claude
Code, Claude Cowork, or Cursor; Codex CLI can import supported setup from
Claude Code or Cursor. Import may map instruction files, settings, skills,
plugins, project folders, memories, chats, MCP configuration, hooks, slash
commands, and subagents into target-native destinations. It leaves the
existing setup unchanged, but imported permissions, MCP authentication,
hooks, marketplaces, and path-dependent prompts still require review.

These facts are the current product surface, not a promise that every account,
workspace, client, or plugin has the same availability. Re-check the official
documentation before adding a new target or relying on an import capability:

- Codex instruction discovery: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- Import from another agent: <https://learn.chatgpt.com/docs/import>
- Build skills: <https://learn.chatgpt.com/docs/build-skills>
- Build plugins: <https://learn.chatgpt.com/docs/build-plugins>

The share compiler does not automate the product import flow and does not
publish a ChatGPT Web plugin from `portable-core.md`. Import and plugin
installation are verified target operations, not evidence that the share repo
has synchronised global state.

## Disposition classes — why something is absent (added 2026-08-14)

> **Share-repo-only section.** It is not in the source environment's copy of
> this file and must not be back-flowed into it: everything it describes —
> `tools/share-manifest.toml`, `tools/share_gate.py`, `tools/COLLECTION-RULES.md`
> — is machinery built HERE, for publication. The source has no such layer and
> would gain nothing but a dangling citation. Declared as an edit on this
> file's `[[collected]]` entry.

"Do not migrate" above conflated four different causes, and an outside adopter
had to re-derive the distinction before they could tell which absences were
decisions and which were just gaps. Naming them costs nothing here and saves the
next adopter the same cycle. **Machine-readable form:
`tools/share-manifest.toml` `[[not_shipped]]`; check R of `tools/share_gate.py`
fails any citation that neither resolves nor carries one of these.**

| Class | Means | Example |
|---|---|---|
| `upstream-absent` | the source environment has no such artifact either | MCP servers, connectors — never existed here |
| `referenced-only` | it exists at the source, but only its INTENT ships; no portable artifact was ever produced | `LABEL-REGISTRY.md` was the standing example until 2026-10-02, when it began shipping as a template (`environment-guide/LABEL-REGISTRY.md`); the class is now empty and kept for the next arrival |
| `excluded-by-decision` | a concrete file exists and was deliberately withheld | `skills/asset-vault` — operates a private library at a hardcoded path and delegates authority to a non-public file |
| `partial` | only part of it ships | `settings.json` — structure and permission example ship as a template; the two absolute paths cannot |

**`referenced-only` is the class that rots.** It is a claim about the source
made at one moment, and nothing re-tests it. Three hook entries sat in that
class for a month on the reasoning "machine-bound"; a 2026-08-14 source audit
found every one of them resolves paths through `Path.home()` /
`CLAUDE_CONFIG_DIR` with no machine-bound value at all — they had simply never
been collected, and they now ship under `hooks/`. Re-verify a
`referenced-only` entry against the source before relying on it;
`tools/COLLECTION-RULES.md` makes that step mandatory rather than optional.

Every entry states the FALLBACK: what the adopter actually gets instead —
mechanism, or prose. That is the *Translate per target* rule above — "the loss
must be visible, not silent" — made checkable rather than remembered. The
failure it prevents: a rule saying "mechanically enforced"
while the enforcing file is absent, which is indistinguishable from a working
mechanism until something goes wrong.

## Profiles

- **light** — lightweight-task agents. Minimal rent, 8 blocks: preamble,
  language output, environment/shell, git workflow, evidence over claims,
  decision charter, pre-existing issues, file hygiene.
- **full** — goal-oriented agents. light + judgment core, 8 more: visual
  acceptance, canonical-method discipline, volatile facts, done definition,
  failure visibility, approach-wrong signals, scope restraint, gates and
  controls (added 2026-08-16).

Superset rule: light ⊂ full. A block tagged `light` must also carry `full` —
ENFORCED by `parse_blocks()` since 2026-08-16, no longer prose-only.
16 blocks total as of 2026-08-16. These counts are derivable — `parse_blocks()`
in `interop.py` is the source of truth, and both this file and README.md have
carried a wrong count before (README said 6-of-13 while the share copy said
8-of-15; neither matched the 7-of-15 the parser reports) — and this very
paragraph carried "15 total" for a day after the 16th block landed, caught by
an external review 2026-08-16. Re-derive, do not copy the sentence: `build`
now prints blocks/bytes per target.

## Target registry (re-verify volatile facts before adding or re-enabling a target)

| Target / surface | Entry or generated artifact | Profile / mode | Relevant extension points or boundary |
|---|---|---|---|
| opencode | `~/.config/opencode/AGENTS.md` | **full** (user ruling 2026-08-15) | `~/.config/opencode/opencode.json` — `permission`, `agent(s)/`, `command(s)/`, `skill(s)/`, `plugin`, `mcp` |
| codex | `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`) | **full**, compiler target re-added 2026-09-18 | Global `AGENTS.override.md` precedence; project/nested `AGENTS.md` chain; Codex `config.toml`, skills, plugins, hooks, and subagents are target-native mechanisms |
| chatgpt-import | ChatGPT desktop `Settings > Import`, or Codex CLI `/import` | **manual product flow** | User selects supported setup/work/projects/recent work; imported permissions, MCP auth, hooks, marketplaces, and path-dependent prompts require review |
| chatgpt-web | No generated global file; skill or plugin package | **package surface** | Use portable skill core, root `plugin.json`, `skills/<name>/SKILL.md`, and separately authorised MCP/connectors; do not assume local filesystem or shell |

Notes:
- **Historical Codex removal superseded 2026-09-18.** The 2026-08-15 ruling
  correctly removed Codex while its path and extension points were only stale
  snapshots. The current official Codex documentation now re-verifies the
  global file, override precedence, project chain, and `CODEX_HOME`, so Codex
  is re-added as a `full` file target. The old removal rationale remains in
  `archive/2026-08-15-interop-targets-removed/`; it is history, not the current
  registry state.
- **Antigravity remains retired.** Its application was confirmed uninstalled
  on 2026-08-13; it is not re-added merely because the target table changed.
- **Codex is not ChatGPT Web.** Codex's `AGENTS.md` target is a persistent
  instruction surface. ChatGPT Web receives skills/plugins and enabled
  connectors, while the desktop import flow is a user-selected migration
  operation. A plugin install or product import must not be represented as an
  `interop.py` file deployment.
- **Codex override shadowing is observable.** If
  `$CODEX_HOME/AGENTS.override.md` exists, `interop.py build` may retain the
  generated `AGENTS.md`, but `interop.py status` reports it as `shadowed` and
  does not count it as a live target. This prevents a generated-but-ignored
  file from being mistaken for active evidence.
- **opencode profile is `full` (user ruling 2026-08-15, was `light`)**, set in
  `interop.py` TARGETS. Two reasons, and the first one is a measurement that
  INVERTED the birth-budget argument that had picked `light`: no AGENTS.md had
  ever been deployed, so opencode was falling back to `~/.claude/CLAUDE.md`
  (~16.5 KB, all of it Claude-Code-specific mechanism a non-Claude worker
  cannot act on). `full` was 11,129 B / 15 blocks at the ruling (by
  2026-08-16: 13,639 B / 16 blocks — re-derive via `build`, which prints
  both) — it costs the worker LESS context than the status quo it replaced,
  not more, so "light profile 尤其要守小" never applied to this target in the
  first place. Second: the role changed — opencode is now a dispatch target
  (free-tier workers execute work cards and run cross-family red-team
  review), so it needs the preference set the dispatcher assumes it has.
  Effect on the block set: every block now reaches a live target (15 at the
  ruling, 16 since 2026-08-16); before it, the `full`-only ones reached nobody.
  Standing reason: `ops/rule-registry.md`, key `interop`.
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

  What the shadow was hiding, and why retiring it was the right call rather
  than refreshing it: **`~/.agents/skills/` held a second physical copy of the
  entire 14-skill corpus** — real directories, not symlinks — frozen at
  **2026-08-03**. All 14 differed from live. Ten by 1–7 bytes (line-ending
  artefacts of the copy); **four substantively**, worst `config-self-audit` at
  **−7,235 bytes**, missing the whole adoption mode added 2026-08-12. That is a
  second source of truth for the corpus, which `40-maintenance.md` §2 ("a rule
  lives in exactly one file") forbids at rule scale and nothing was watching at
  corpus scale: `ops_health_nudge` check 10 walks `~/.claude/skills/` only, and
  `config-self-audit` §4 names the plugin roots, not this one.

  **Current state, re-verified 2026-08-15** (this entry described an open
  decision for three days after that decision was made — the resolution above
  was prepended and the superseded tail was left standing, so it is stated once,
  here, with its proof): `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` is set at the
  Windows User level, so it survives a reboot rather than living in one shell;
  `~/.agents/` is empty; the snapshot is at
  `archive/2026-08-12-agents-skills-retired/`. Proof of life —
  `opencode debug skill` returns exactly **1** entry, the built-in
  `customize-opencode`, with zero from `~/.claude/skills/` or `~/.agents/skills/`.
  Re-run that command before trusting this paragraph; it is the only statement
  here that a change on either side can silently falsify. Routing context:
  `ops/references/inbound-routing.md`.
- Keep every target's content agent-neutral (which portable-core already
  guarantees): a global rules file at a shared path — `~/.gemini/AGENTS.md`
  was the known case — can be read by more than the agent it was written for.

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
6. **Separate compile, import, and publish.** `interop.py build/status` only
   handles file-based instruction targets registered in `TARGETS`. The
   ChatGPT/Codex product import flow and plugin installation are separate
   user-facing operations; neither is proof that the share repo is deployed.
7. **Do not copy global state into a skill package.** Exclude global settings,
   permissions, hooks, sessions, caches, derived indexes, credentials, tokens,
   cookies, and absolute workstation paths unless a target adapter explicitly
   defines a safe, reviewed replacement. Official product import may offer
   selected memories or chats, but that remains user-selected state and never
   becomes a published repo artifact.
8. **Capability claims require a fallback.** If a Codex or ChatGPT target does
   not expose a shell, local filesystem, executable, connector, MCP server, or
   hook, the migrated workflow must state the missing capability and its
   fallback. It must not simulate a successful run or silently remove the
   step.
9. **Re-verify on product-surface change.** Changes to Codex discovery,
   plugin manifests, supported import sources, marketplace behavior, client
   availability, or workspace policy trigger an official-docs recheck before
   editing the target registry. These are volatile facts, not portable prose.
