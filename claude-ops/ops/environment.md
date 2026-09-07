# Environment Facts — recorded per `20-dispatch.md` §0

Facts about THIS environment (Claude Code on Windows). These are
recorded observations, not assumptions — if a dispatch behaves as if a fact
below is stale (new model names, missing parameters), re-verify and update this
file; never silently work around it.

**Dating rule (invariant)**: every block below carries its OWN `as-of` line. A
single file-level date is banned — it goes stale silently and cannot express
that one block was re-verified while another was not. Updating a block without
moving its `as-of` is the same defect as not updating it.

## Subagent cost cap — tier → model (as-of 2026-07-07)

Scope: **dispatched subagents only** (Agent / Workflow `agent()`). It says
nothing about which model the main session itself runs — that is a separate
fact, see "Main-loop model" below; do not read this table as a session default.

| Tier role | Model id | Notes |
|---|---|---|
| cheap | `haiku` | Lowest-cost dispatch tier — mechanical / high-volume stages |
| mid | `sonnet` | Default for implementation / verification dispatches |
| top (capped) | `sonnet` + `effort: high` | The approved ceiling for ALL subagent work |
| forbidden | `opus`, `fable` | Blocked by hook; per-instance exception requires explicit user approval |

**Cap policy (owner: user, 2026-07-07)**: subagent dispatches use haiku or
sonnet only — never opus/fable-tier. Severity is expressed on two axes:
model (haiku ↔ sonnet) × effort (low ↔ high). `sonnet + high effort` replaces
what would otherwise go to opus.

**Enforcement**: `hooks/model_cap_guard.py` (PreToolUse, matcher
`Agent|Workflow`) denies blocked models. Exception mechanism: the orchestrator
may include the literal marker `[user-approved-top-tier]` in the dispatch
prompt/script ONLY after the user approved that specific instance in
conversation. Known gap: a Workflow launched via `scriptPath` is not scanned
by the hook — for those, the cap is rules-enforced only (review the script's
`model:` options before invoking). **Since 2026-09-05 the hook also denies an
Agent call that omits `model`** unless `subagent_type` names a local
`agents/*.md` definition whose frontmatter pins a model within the cap
(built-in types general-purpose / Explore / Plan / claude-code-guide inherit the
main loop's model, which here is opus/fable — measured 46 such dispatches in
2026-08-06..09-04). Always pass `model: "sonnet"` (or `"haiku"` for read-only
search) on built-in types.

**Known gap 2 — resume bypass (as-of 2026-07-10, hooks API offers no fix)**:
resuming a stopped background subagent via `SendMessage` restarts it on the
main session's CURRENT main-loop model, not its spawn model, and no hook event
can see or block this (SendMessage payload has no model field; SubagentStart
cannot deny). **Rule**: for cost-capped work, when the main-loop model is above
the cap tier, prefer re-spawning a fresh Agent with an explicit capped `model`
over SendMessage-resume; if a resume is genuinely needed (context too costly
to rebuild), disclose the model escalation to the user before sending.
Details + evidence: `ops/lessons.md` L-001, hook header.

## Dispatch mechanisms available (as-of 2026-08-26, CLI 2.1.246)

- **Agent tool**: per-call `model` (haiku/sonnet/opus/fable) and custom
  `subagent_type` from `agents/`. Model precedence: call param > agent
  frontmatter > inherit the main-loop model — EXCEPT `subagent_type: "fork"`,
  which ignores `model` and always inherits the parent's.
- **Spawns run in the BACKGROUND by default, and forking is on by default.**
  In an interactive session every non-teammate spawn is backgrounded unless
  `run_in_background: false` — pass that only when the very next action depends
  on the result. `subagent_type: "fork"` inherits the full conversation and the
  prompt cache; a plain `Agent` call starts fresh.
- **Fan-out has hard ceilings**: 20 concurrent subagents and 200 spawns per
  session (both overridable by env var). Plan against these, not "unbounded".
- **Cross-session messaging is a THIRD dispatch path** and it works on Windows
  as of 2.1.239: `ListAgents` to discover sessions on this machine, then
  `SendMessage`. Unlike a subagent it talks to a session that already has its
  own context; unlike external dispatch it stays inside Claude Code.
  Versions, citations and the reconciliation that produced this block:
  `ops/references/harness-measurements.md` §Dispatch semantics.
- **Capability is set in the definition, not at dispatch** (verified
  2026-08-12): a definition that omits `tools:` inherits every tool a subagent
  may hold — including `Edit`/`Write` — so "read-only" written in a prompt
  enforces nothing. The `tools:` allowlist is the only unconditional control.
  `permissionMode` is defence-in-depth only: a parent session in `acceptEdits`
  or `bypassPermissions` overrides it, and a parent in `auto` mode makes the
  frontmatter value be ignored outright.
- **Workflow tool — NOT AVAILABLE IN THIS ENVIRONMENT.** `settings.json` sets
  `"disableWorkflows": true`, which drops the tool definition outright; it is
  absent from the tool list, so nothing here may route to it (verified
  2026-08-26 against a live 2.1.246 session). Dynamic workflows and ultracode
  go with it. Kept on record because the choice is a live setting, not a fact
  about the product — flipping that key restores it. What it offers when
  enabled: `harness-measurements.md` §Dispatch semantics.
- **Effort is NOT settable per Agent-tool call** (verified 2026-08-12 against
  the live tool schema + `code.claude.com/docs/en/sub-agents`). Two setpoints
  only: the `effort:` frontmatter field in an `agents/*.md` file (overrides the
  session level whenever that subagent is active), and Workflow's per-`agent()`
  `opts.effort`. Global default: `effortLevel: medium` in settings.json;
  omitting `effort:` from a definition means it inherits that. To dispatch one
  role at a different intensity, edit its definition — there is no per-call
  override. Rule of thumb: low for mechanical stages, high for
  verification/judgment stages.

## Red-team / reviewer separation (as-of 2026-08-16 — SUPERSEDES the 2026-07-07 entry)

A cross-family reviewer NOW EXISTS (the 2026-07-07 entry said the opposite —
true then, false now; why it is corrected rather than deleted, and the
measurement: `ops/references/harness-measurements.md`). Two options, in order:

1. **External dispatch** (`## External dispatch tier` below) — genuinely a
   different model family, free, no credential. Route red-team here first.
2. **Fallback, unchanged**: fresh-context sonnet (high effort), never the
   author, adversarial framing — for anything the external tier may not see
   (redline rules below).

## External dispatch tier (as-of 2026-08-16)

A SECOND DISPATCH PATH, disjoint from the Agent tool. Keep the two apart in your
head: they take different work, carry different risk, and only one of them can
be pointed at private material.

- **Entry point, and the only one**: `python ~/.claude/tools/extdispatch/extdispatch.py`
  (`status` / `grant` / `run` / `probe`). `hooks/extdispatch_entrypoint_guard.py`
  denies direct `opencode` invocation and hand-rolled POSTs to the local serve
  API on Bash|PowerShell, so there is no second route to find.
- **Transport**: `opencode serve` on `127.0.0.1:4096`, started on demand.
- **Providers**: `opencode` (Zen) — NO API key, 7 models, `GET /config/providers`
  is the roster authority; and `nvidia` (NIM) — needs `NVIDIA_API_KEY`, carries a
  (key, model) cooldown. Chains lead with Zen and end on NIM.
- **Profiles**: `code`, `longctx`, `agentic`, `mechanical`, `review`.
  `extdispatch.py status` prints the live chains and per-model health. Which
  PATH to use is `20-dispatch.md` §4a; profile/prompt/acceptance detail is
  `ops/references/external-dispatch.md`.
- **Gates, all mechanical**: redline prefixes (exit 3), project allowlist
  (3), single-use grant (4), daily cap 40 (6), concurrency lock 1 (7), and a
  full-content audit of every dispatch under `tools/extdispatch/audit/`.
- **Cost shape**: ~7.3–8.0 K input tokens of preamble per dispatch and $0,
  against ~49 K for one Claude `general-purpose` subagent. Wall-clock is the
  real currency here, not money.
- **Redlines and disclosure**: `20-dispatch.md` §4b. The asymmetry is the point
  — the subagent path may see anything, this path may not.

## Main-loop model — READ IT, never infer it (as-of 2026-08-07)

Terms (used file-wide, and across `ops/*`): **main session** = the top-level
session, as opposed to dispatched subagents — it has no tier. **Main-loop
model** = the model that session is actually running on — this is what carries
a tier (cheap / mid / frontier).

`settings.json` holds `"model": "haiku"`, a deliberate cost pin. **That is the
configured default, NOT proof of what is running**: the app/IDE model picker,
`/model`, and per-session overrides all win over it. Verified 2026-08-07 —
settings.json still said `haiku` while the session ran Opus 5.

**Procedure** (owner: whoever hits the gate). At the `05-authority.md` §2
relaxation gate, and any other point where a rule branches on main-loop tier:

1. Take the tier from the session's own reported model identity (the one the
   gate already requires be stated in one line). That is the observation.
2. `settings.json` `model:` is a *fallback* answer only when no identity is
   available — mark it "assumed", not "verified".
3. Never derive the tier from this file's prose. A written-down tier is a
   snapshot; the gate needs the live value.

Consequence for `05-authority.md` §2: "L0 applies automatically whenever the
main-loop model is cheap/mid" is evaluated against step 1, not against the
`haiku` pin. Residual weak points when the main-loop model IS cheap/mid: R6
taste calls and the intake gates; mitigation: raise the model manually for
judgment-heavy sessions, or lean on fresh-context sonnet review for intake.

## Browser pane — recorded properties (as-of 2026-08-16)

Three recorded properties of the in-app Browser pane, all measured, all
enforced by hook rather than by recall (why: `lessons.md` L-011). The first two
are about reading OUT of the pane; the third is about what you let IN.

| Property | Consequence | Recorded in |
|---|---|---|
| An occluded pane reports `document.visibilityState === "hidden"`; compositing stops while CDP reads keep working | every `computer{action:"screenshot"}` TIMES OUT — a display-state fault, never a permission one | L-009 |
| `getComputedStyle()` during a CSS transition returns the interpolated mid-flight value | hover/focus assertions come back FLAKY, not stably wrong | L-010 |
| A third-party page loaded in the pane can crash the Electron GPU child (`exitCode 101457950`); Electron does not relaunch it | window stops compositing, main process wedges (8m26s of log silence, observed), in-flight turn of EVERY session in the app is lost | L-013 |

**Standing premise (user, 2026-08-16): the foreground is not commandeerable.**
「絕大部分時間我一定都在做別的事情，不可能讓你跳視窗到我眼前」 — `hidden` is
the pane's STEADY STATE, not an exception: a fresh `preview_start` pane is
born `hidden` (0×0, rAF stalled, no focus stolen) and its screenshot times
out (5s, zero pixels) while script/CDP stay alive. Consequences: no rule,
remedy, or delivery note may ask the user to bring a window forward; pixels
default to the out-of-process route; pictures reach the user via
`SendUserFile`/links. FLIP: only while the user explicitly says they are
watching, for that stated scope (their words are the flip; this file does not
change). Detail: `ops/references/browser-pane-pixel-route.md`. review-when:
the pane gains an always-visible surface, or `<browser_surfaces>` wording
changes.

**Enforcement** (hooks, not recall): `hooks/ui_verify_guard.py` denies an
unsettled `getComputedStyle` and denies a screenshot until a `visibilityState`
probe has run, routing to the headless command when the probe said `hidden`
(`visible` unlocks the pane screenshot, so visible+timeout stays a distinct
fault). `hooks/browser_pane_scope_guard.py` logs every pane navigation and
enforces the pane **ALLOWLIST** (`hooks/browser-pane-allowlist.json`,
user-edited). Matchers, marker paths, TTLs, test counts, escape hatch,
standing reason and the promote-on-second-incident rule of thumb:
`ops/references/browser-pane-pixel-route.md` "Enforcement", `rule-registry.md`
"in-app Browser pane", `lessons.md` L-013.

**Out-of-process pictures are the DEFAULT pixel route (as-of 2026-08-16,
measured)**: headless Playwright in its own process delivers PNGs in ~1.5 s
where the hidden pane times out at 5 s with none. Recipes, the measured
comparison, resolution facts, representativeness limits, E-6 flag research and
the asset/browser paths: `ops/references/browser-pane-pixel-route.md`.

**Playwright MCP — ONE user-scope server (as-of 2026-08-25)**:
`playwright-headless` (`--browser chrome --headless --isolated`) is the
logged-OUT browser route; for anything needing the user's real logged-in state
use `mcp__claude-in-chrome__*`. It is a separate process, so L-009's occlusion
fault, L-013's allowlist and the `hidden`-probe hook do NOT apply to it (user
upheld 2026-08-23). `playwright-chrome` (`--extension`) was trialed 2026-08-23
and REMOVED 2026-08-25 — do not re-add it without reading why. Flags,
measurements, the removal mechanism and the review-when:
`ops/references/browser-pane-pixel-route.md` §"Playwright MCP servers";
`tools/playwright-mcp/README.md`.

## Instruction-loading mechanics (as-of 2026-08-18, Claude Code 2.1.233 — re-verified after the 2.1.220 review trigger fired)

Measured, not read off the docs (how each row was verified, the observability
hook, `load_reason` values, trim effect sizes and the startup baseline:
`ops/references/harness-measurements.md`).

| Carrier | Charged at session start? |
|---|---|
| `~/.claude/CLAUDE.md` | yes, in full — and again after every `/compact` |
| `@path` imports inside it | yes |
| `~/.claude/rules/<name>.md` **without** `paths:` | yes |
| `~/.claude/rules/<name>.md` **with** `paths:` | **no** — loaded when a matching file is read |
| skill | only when invoked/judged relevant |

So the only carriers that reduce startup cost are: delete/merge, a
`paths:`-scoped user rule, or a skill. Splitting into imports or unscoped
rules saves nothing. Sinking an INTENT-triggered rule into `ops/` makes it a
ghost rule (`lessons.md` L-011) — `ops/*` is reached only via CLAUDE.md's
project-operations clause. Trim effect sizes are below the measurement noise
floor (a ~0.5% signal in a ~13k-token per-session spread), so judge
context-budget work by adherence evidence (`telemetry/rule-loads.jsonl` shows
the rule firing when it should) and the on-disk inventory, never by a token
delta; CLAUDE.md is ~11% of the startup floor — the roster dominates.

**Bash results carry no exit code** (measured 2026-08-11): `is_error` is
exactly "the shell reported non-zero", so `cmd || true` and `cmd | head` report
success with `FAILED` in stdout. Any gate keying on `is_error` must also sniff
stdout, or downgrade piped / `||`-guarded verifications to "weak".

## Auto-mode environment scoping (as-of 2026-08-16, Claude Code claude.exe 2026-08-15 build)

`settings.json` `autoMode.environment` is applied UNCONDITIONALLY, in every
project — the classifier reads user + managed + `--settings` scopes only and
deliberately ignores project-level settings (anti-injection), scopes
CONCATENATE, and the block is spliced into the classifier prompt on every
auto-mode decision. Consequence: project-specific facts written there leak into
every other project's auto-mode decisions — keep the block org/user-generic; a
project-bound profile has no home other than per-invocation `--settings`.
Evidence (docs + binary string probe) and the 2026-08-16 incident:
`ops/references/harness-measurements.md`.

## Local toolchain — measured, not assumed (as-of 2026-08-18)

Every line here was run on this machine on 2026-08-18. Three of them are traps
that no rule recorded before that sweep, and all three fail LOUDLY but with a
message that does not name the cause.

| Fact | Value | Why it is written down |
|---|---|---|
| PowerShell | **5.1.26100.9168 Desktop; `pwsh` NOT installed** | every PS 5.1 caveat in CLAUDE.md applies unconditionally — there is no PS7 to fall back to |
| Bash tool's shell | **Git Bash / MSYS2, `/usr/bin/bash` 5.2.37, `MINGW64_NT`** | see next row |
| `bash` from PowerShell | **`C:\Windows\system32\bash.exe` → WSL Ubuntu** | TRAP: a different OS with a different filesystem view. `bash -c` from PowerShell does NOT reach the Bash tool's shell. WSL has Ubuntu + docker-desktop registered |
| `python` | 3.12.7 at `AppData\Local\Programs\Python\Python312` | works |
| `python3` | **`AppData\Local\Microsoft\WindowsApps\python3.exe` — the Store shim** | TRAP: always fails with "Python was not found; run without arguments to install from the Microsoft Store". 6 hits in the 10-day sweep. Use `python`, never `python3` |
| `rg` | **not on PATH** | TRAP: the Grep TOOL ships its own ripgrep and works, but a bare `rg` inside a Bash command does not |
| node / npm | v24.14.1 / 11.11.0 | |
| dotnet SDK | 10.0.301 | |
| git | 2.51.0.windows.2; `core.autocrlf=true` in the SYSTEM gitconfig | superseded for `~/.claude` by its committed `.gitattributes` (2026-08-18) |
| ACP / OutputEncoding | **65001 both**; Culture zh-TW, UICulture en-US | why a missing `.ps1` BOM has no symptom on THIS machine while breaking any CP950 machine — `outputs/script-encoding-audit-2026-08-16.md` |
| OS / RAM | Windows 11 Home build 26200 / 31.2 GB | |
| GPU | RTX 5070 Laptop, **8,151 MiB per `nvidia-smi`** (+ integrated Radeon 610M) | `Win32_VideoController.AdapterRAM` reports 4 GB — a 32-bit field overflow, NOT a smaller card. Do not "correct" the 8 GB figure from it |
| CPU | Ryzen 9 8940HX, 16C/32T | |

## Display & UI-build premise (as-of 2026-09-04; screen facts user-stated 2026-08-31, not measured)

Primary screens: **2560×1440 (16:9)** or **2560×1600 (16:10)**, Windows custom
scaling **150%**. Derived (from those two facts, not probed): logical viewport
≈ **1707×960 / 1707×1067**, browser `devicePixelRatio` 1.5 — verify in-page
before any pixel-exact claim depends on it.

**Baseline rule (owner: user, 2026-08-31)**: screen-related build premises are
judged against an **FHD-class baseline** (簡易判定以 FHD 為基礎); special
aspect ratios / ultrawide are OPT-IN extra adaptation when actually needed,
never a default requirement. Consequence: when confirming premises for
UI/viewport/canvas/layout work, assume this display + 150% scaling, and trim
generic boundary-case lists accordingly (CLAUDE.md boundary/compatibility
`[BC]` rule — these are now KNOWN environment facts, not guesses).

**Horizontal property (owner: user, 2026-09-04 — a dated width-void diagnosis
note under the source's outputs/ tree, which this repo does not ship)**: a
human-facing HTML page must USE the width these screens give it. The named
defect is the
**left-anchored cap** — a container or painted, row-alone block capped in width
and hugging the left edge, leaving an asymmetric right void (one shell's
`max-width:1060px` became 13 deliverables at 60–69 % fill). How much fill a
page owes depends on its CLASS, declared as `<html data-page-class="…">` and
kept as DATA in `tools/page-fill-gate/page_classes.json` (document-short =
centred + symmetric · document-long / deck / tool / dashboard = fill ≥ 85–90 %
· diagram = centred-or-fill). A new kind of page is a new registry row plus a
fixture pair, never a prose exception; an undeclared page is inferred and can
only WARN. Enforcement: `python tools/page-fill-gate/fill_gate.py <built
html…>` — two-sided controls every run, exit 2 = instrument missing (say so,
never claim). Width is ALLOCATED proportionally (fr / % / cqw / minmax /
clamp); pixels are for intrinsic sizes only (hit targets, hairlines, icons,
minimum legible type, a panel's minimum) and `clamp()` is the bridge; a cap
above 1920 px is a clamp, not a cap. The built-in artifact-design skill's
"~65 characters" measure is met by column structure (main + `data-rail`,
grids), never by a left-anchored column.

review-when: the user reports a new monitor or a changed scaling factor;
`page_classes.json` gains a row (re-run `tools/page-fill-gate/tests`);
Anthropic's artifact-design wording on reading measure changes.

## Execution surface — CLI headless vs Desktop (measured 2026-08-22 on CLI 2.1.238 / Desktop-bundled claude.exe 2.1.237)

**CLI is now 2.1.246 (2026-08-26); this block's re-verify trigger has fired.**
The ROUTING below still holds; every measured NUMBER is eight builds old and
unre-verified — re-probe registered as E10 in
`reports/2026-08-26-cc-version-reconcile-2.1.200-2.1.246.md`.

Same engine, different host: Desktop is the same Claude Code engine (its own
bundled `%APPDATA%\Claude\claude-code\<ver>\claude.exe`) behind a larger
host-injected prefix and different defaults, so the same work costs more there.
The standing consequences:

- **For autonomous coding work in Desktop pick Bypass, not Auto** — permission
  mode is about HALF the Desktop premium, so expect to save half, not all; the
  other half is the host itself and has no verified knob.
- **Do NOT trim remote connectors for cost.** They are deferred-loaded; turning
  28 tools off moved the session-start prefix by single-digit tokens.
- **Records**: every session, CLI or Desktop, writes
  `~/.claude/projects/<slug>/<cliSessionId>.jsonl` — the only durable LOCAL
  record. A session viewed through Remote Control is a server-side mirror whose
  live view ends with the process; it is not a local record.

**Every number behind those four — arm sizes, ratios, p-values, T0 counts, the
E3 C2B cell, the exact record paths — is in `references/harness-measurements.md`
§Execution surface (extracted 2026-08-27, `40-maintenance.md` §3). Quote from
there with its staleness caveat, never from memory.**

**Routing (user ruling 2026-08-22):** unattended / batch / long / subagent
fan-out / needs `--max-budget-usd`, `--output-format json` (note: `--max-turns`
is NOT in `claude --help` — an Agent SDK option only; re-checked at 2.1.246) →
CLI headless (`claude -p`) or `claude --bg` + `claude agents` · diff
line-comments / Browser-pane preview / parallel sidebar / Dispatch / computer
use → Desktop · GUI view or approval of a RUNNING CLI session → Remote Control
(`claude --remote-control`, in-session `/rc`) on claude.ai/code, mobile,
Desktop; whole-session move → `/desktop` (one-way) · after-the-fact disclosure
of any session → the JSONL via
`tools/session-find.py` (live tail: claude-code-trace) · Desktop session into
the CLI → `claude --resume <cliSessionId>` (undocumented direction; try
`--fork-session` first).

Re-verify this block (move its `as-of`) when: the Desktop-bundled claude.exe or
the CLI minor version changes; the auto-mode instruction or the Workflow tool
schema changes; the bench is re-run, or a pending probe lands (those are
tracked with the measurements, not here).

## Computer use — desktop control (as-of 2026-09-07, FIRST record; grant PROBED)

A THIRD browsing/driving surface, distinct from the Browser pane and
Claude-in-Chrome above: `mcp__computer-use__*` drives the Windows desktop
(screenshot / zoom / click family / type / key / scroll / drag /
`open_application` / clipboard / `switch_display` / `computer_batch`, plus the
`teach_step`-`teach_batch` guided-tour mode). Routing already sends it to
Desktop (see "Execution surface"); the app's own settings page says it is
"Not available in cloud Code sessions".

**The allowlist is not configuration — it is a session artifact.** This is the
fact that makes the surface behave unlike everything else here:

| | Where it lives | Lifetime |
|---|---|---|
| ALLOW | built at runtime by `request_access`, one OS dialog, whole-set approve-or-deny | the session; a new session starts empty |
| DENY | app settings page, "Denied apps" list | persistent |

So there is no allow-list UI and there cannot be one: `settings.json`
`permissions.allow` gates only the Claude Code tool-call layer, never the app
grant. **Consequence for unattended work: `[unattended-run]` cannot use this
surface at all** — the grant needs a human at the dialog, and the user is by
definition away. Do not design an offline workflow around it without solving
that first.

**Measured on this machine 2026-09-07** (a local session): `allowedApps` empty,
all three grant flags (`clipboardRead` / `clipboardWrite` / `systemKeyCombos`)
false; zero occurrences of `computer-use` in `settings*.json`, `rules/`, or
`rule-registry.md`; **no hook matcher covers `mcp__computer-use__*`** —
`ui_verify_guard.py` and `browser_pane_scope_guard.py` are both keyed to
`mcp__(Claude_Browser|claude-in-chrome)__*`, so the DOM-over-pixels discipline
above does NOT extend here. This surface is currently ungoverned locally; its
only gate is the platform's per-app consent.

App settings page, user-observed 2026-09-07: "Enable computer use" ON,
"Unhide apps when Claude finishes" ON ("apps hidden during a task are
restored when Claude stops" — implies full-control mode HIDES apps rather than
fronting them; unverified), "Denied apps" empty.

**Platform limits (from the tool schemas — authoritative, not inferred):**
- Elevated processes (Task Manager, UAC prompts, admin installers) cannot be
  driven at all: Windows UIPI blocks input from a lower-integrity process.
- Tiers by app category: browsers -> `read` (screenshot only); terminals and
  IDEs (VS Code, Visual Studio, PyCharm, 終端機) -> `click` (no typing, no
  right-click, no modifier-click, no drag); everything else -> `full`.
- `request_access` resolves ONLY Start-menu-registered applications. A loose
  `D:\...\*.exe` returns `notInstalled` and **the request never reaches the
  user** (measured 2026-08-21, bench-claude-arms; the detour to a read-only
  geometry probe produced better evidence than the GUI plan would have).
- `screenshot` ERRORS on an empty allowlist; non-allowlisted windows are masked
  with solid rectangles rather than shown.

**Start-menu scan, 2026-09-07** (232 shortcuts): grantable targets include
FreeCAD, COMSOL 6.2, Photoshop 2026, VS Code / Visual Studio 2022 / PyCharm
(click-tier), OBS, CapCut, Notepad++, Obsidian, Zotero, Docker Desktop, Ollama,
Office. **KiCad is not installed. Blender exists only as a portable tree**
(`model3d-pipeline\tools\blender-5.2.1-windows-x64\blender.exe`), so
it is NOT grantable as-is. Untested cheap hypothesis: adding a Start-menu
shortcut may make a portable exe resolvable.

### PROBE 2026-09-07 (a local session, user-authorised: FreeCAD + 記事本)

The grant path WORKS in the Desktop Code tab. One dialog, whole set, both
granted `tier: "full"`, `denied: []`. Measured behaviour, in order of how much
it should change a plan:

1. **A screenshot HIDES every non-allowlisted window — it does not mask them.**
   The response named them: Radmin VPN, Samsung Notes, Everything, Brave, plus
   `textinputhost.exe`, `msedgewebview2.exe`, `nvidia overlay.exe`,
   `systemsettings.exe`. The desktop came back empty but for the taskbar. The
   `request_access` response advertises `screenshotFiltering: "mask"`; the
   observed effect is HIDE, and the settings page's "Unhide apps when Claude
   finishes" is the restore path. **So one screenshot rearranges the user's
   session.** This, not foreground theft, is the real collision with the
   "foreground is not commandeerable" premise — and unlike a Browser-pane
   screenshot it cannot be routed out-of-process.
2. **`open_application` DOES bring the app to the front** (corrected — the
   first probe said otherwise and was wrong). A COLD launch of 記事本 left the
   desktop shell frontmost, which read as "no foreground steal"; calling
   `open_application` again on the already-running app raised it over the
   user's windows. The cold-start case is a timing artifact, not a policy. So
   this surface **does** commandeer the foreground, and the error text of the
   click gate says so outright: "use `open_application` to bring it forward".
3. **A THIRD gate: the desktop shell.** A click while the desktop, taskbar,
   Start menu, Search or File Explorer is frontmost is refused with:
   *"call request_access with exactly \"File Explorer\" in the apps array —
   that single grant covers all of them. That grant is click-only: typing into
   the shell stays blocked."* This tier rule is not in the MCP server
   instructions; it is a shell-specific click-only grant on top of the
   documented browser=read / IDE=click tiers.
4. **Coordinate frame 1389x868 — resolved, and the Display premise is
   CONFIRMED, not contradicted.** Measured: single monitor, physical
   2560x1600 (AMD 610M), logical desktop bounds 1707x1067, i.e. exactly the
   150% scaling the Display section records. 1389x868 preserves 16:10
   (1.6002) and is a uniform ~1.229x downscale of the logical desktop.
   Computer use simply reports its OWN frame with every screenshot — use that
   number, never derive coordinates from the Display section. **Single monitor
   means the video's multi-monitor drift cannot occur here**; `switch_display`
   is untested for want of a second display.
5. **Portable-exe hypothesis CONFIRMED.** A `Blender.lnk` written to
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\` made the portable
   `blender.exe` immediately grantable (`tier: "full"`, resolved to the real
   `model3d-pipeline\...` path). **The installed-apps list is live, not cached at
   session start** — the shortcut was seconds old. This is the 30-second
   workaround to the 2026-08-21 bench-claude-arms limit: the limit is real,
   its practical bite is not.
6. **`bundleId` shapes differ by install kind**: a filesystem path for
   FreeCAD/Blender, an MSIX AUMID for Notepad
   (`Microsoft.WindowsNotepad_8wekyb3d8bbwe!App`).
7. Grant flags stay false unless requested in the SAME `request_access` call —
   adding one later costs a second dialog.

**Friction points from the other product — status after the probe.** Source: a
2026-09-06 YouTube walkthrough of ChatGPT/Codex GPT-6 Astra computer use
(analysis: a dated write-up in the user's private media-analysis notes).

| # | Claim | Status here |
|---|---|---|
| 1 | Foreground request hangs | no hang, but foreground IS taken — `open_application` raises the app over the user's windows |
| 2 | Multi-monitor drift | **cannot occur — single monitor** |
| 3 | Human locked out of input while agent drives | unprobed; the window-hiding of probe 1 is the nearer problem |
| 4 | Per-app dialog, conversation-scoped | CONFIRMED here, by construction |

That walkthrough is a FAILURE demo, not a capability demo: it ran out of
credits having produced nothing, and its author's own conclusion was to stop
using computer use. Its one architectural lesson is that GUI control was used
only to BOOTSTRAP (open apps, tick a checkbox) while the real work was routed
through Blender MCP — the same "script/protocol channel does the work"
conclusion `model3d-pipeline` reached independently.

### Scripting channels for candidate GUI targets (inventory 2026-09-07)

The routing question is never "can computer use drive app X" but "does X have a
channel that makes GUI driving unnecessary". Measured:

All three headless channels SMOKE-TESTED 2026-09-07, not merely found on disk:

| App | Present | Channel | Smoke test | GUI needed? |
|---|---|---|---|---|
| Blender 5.2.1 LTS | portable, `model3d-pipeline\tools\blender-5.2.1-windows-x64\blender.exe` | `-b --python-expr`, wired in `m3p/render_blender.py` (`BLENDER_EXE`) | **PASS** (`bpy` 5.2.1 LTS) | no |
| FreeCAD 1.1.3 | `FreeCAD\bin\FreeCADCmd.exe` | FreeCADCmd `-c`, wired (`FREECAD_CMD`) | **PASS** (1.1) | no |
| COMSOL 6.2 | `COMSOL62\Multiphysics\bin\win64\` | `comsolbatch.exe` (+ `comsolclusterbatch`) | **PASS** (help) | no |
| KiCad | **not installed** | would be `kicad-cli` | — | n/a |
| **Keysight ADS 2016.01** | **GONE** — was residue only (13 files / 47 MB, DLLs, zero executables); user deleted `ADS2016_01` 2026-09-07. `EEsof_License_Tools` REMAINS: 899 files / 308 MB (`bin` 211 MB, `jre` 88 MB, own uninstaller, `license.lic`); no EEsof/HPEESOF env vars | see below | n/a | n/a |

Supporting toolchain, smoke-tested same day: Python 3.12.7, Node 24.14.1,
git 2.51.0, ffmpeg 8.1, yt-dlp 2026.08.18, Docker 29.7.2, pdfTeX (TeX Live
2026). Ollama installed but **no running instance**. `klayout` is not on PATH
but lives in the model3d-pipeline venv (0.30.12) alongside gdsfactory 9.49.0,
build123d 0.11.1, trimesh 5.0.0, ezdxf 1.4.4, shapely 2.1.2, numpy 2.5.2.

**Keysight ADS — the version gate matters more than the install.** Even a
working ADS 2016.01 would have AEL only: the Process API for bidirectional
external-program communication arrived in **ADS 2022 Update 2**, and the
Python API / `run_python_ads2024beta()` in **ADS 2024** (Keysight docs, checked
2026-09-07). So automating ADS is not a computer-use question at all — it is a
licence-and-version question. The remaining `EEsof_License_Tools` half is
`app-residue-sweep`'s object and the user owns that cleanup; its own
uninstaller ships in the folder, and the licence-server service and registry
residue were NOT surveyed.

review-when: ADS is (re)installed — check the version against the 2022 U2 /
2024 API gates before assuming any scripting surface.

Full probe log, raw tool responses, the two conclusions this session
overturned, and the refutability statement live in a dated probe write-up
under the source's outputs/ tree, which this repo does not ship.

**Blender MCP is NOT installed on this machine** — no addon matching `*mcp*` in
the portable tree, no `blender-mcp` pip package; the user config dir
(`%APPDATA%\Blender Foundation\Blender\5.2`) holds only an empty extensions
cache. Configured MCP servers are `prism` (ConnectionRefused) and
`playwright-headless` only. So the video's actual working channel does not
exist here yet; adopting it is an unmade decision, not a gap to backfill.

review-when: a click-to-front or `switch_display` probe runs (settles friction
2-3 and the 1389x868 discrepancy); the app settings page gains an allow-list or
persistent-grant control; a hook is written for `mcp__computer-use__*`; KiCad,
Blender MCP, or a non-portable Blender is installed.

Re-verify a block (and move its `as-of`) when: model names in the harness
change; the Agent or Workflow tool schema changes; the user revises the cost
cap; a hook test (`hooks/model_cap_guard.py`, `hooks/ui_verify_guard.py`,
`hooks/browser_pane_scope_guard.py`)
starts failing; `settings.json` `model:` is edited; the Browser-pane MCP tool
names change (the UI guard's matcher is keyed to them). Whole-file sweep: any
block older than ~90 days.
