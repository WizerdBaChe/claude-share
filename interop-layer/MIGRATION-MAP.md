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
| `referenced-only` | it exists at the source, but only its INTENT ships; no portable artifact was ever produced | `LABEL-REGISTRY.md` — the citing rules degrade from "use the registered label" to "use a consistent label" |
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

## Target registry (opencode row re-verified 2026-08-11 against the CLI and
the official docs. Re-verify before adding targets — these locations are
volatile facts)

| Target | Global rules file | Profile | Mechanism extension points |
|---|---|---|---|
| opencode | `~/.config/opencode/AGENTS.md` | **full** (was light; user ruling 2026-08-15) | `~/.config/opencode/opencode.json` — `permission` (allow/ask/deny, per-tool patterns, LAST match wins), `agent(s)/`, `command(s)/`, `skill(s)/`, `plugin` (TS/JS hooks incl. `tool.execute.before`, `permission.ask`), `mcp` |

Notes:
- **codex and Antigravity were REMOVED from this registry (user ruling
  2026-08-15)**, having been sync-off since 2026-08-11. Not "disabled" any
  more — gone. Both rows had been frozen at their 2026-07-10 verification
  while the heading directly above them says those locations are volatile
  facts requiring re-verification, and nobody re-verified them for five weeks;
  Antigravity's application was confirmed uninstalled 2026-08-13, so its row
  could not be re-verified at all. The reason originally given for keeping
  them ("the path + profile + cross-tool caveat are verified facts worth
  keeping") had inverted: they were no longer verified facts, just a stale
  snapshot presented as a registry. Re-adding either target goes through the
  README.md checklist step 1 — look the current paths and extension points up
  in that platform's own docs — which is both faster and safer than trusting
  the old values. Removed text preserved at
  `archive/2026-08-15-interop-targets-removed/`; the last commit containing it
  is `596cfc0`. The `disabled` mechanism itself stays in `interop.py` (the
  `[off]` branches of `build`/`status`, and check 12's skip) with no target
  using it, so a future sync-off ruling does not have to re-add it.
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
