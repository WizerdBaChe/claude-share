# Environment Facts — Claude Code cloud container (recorded per `20-dispatch.md` §0)

Facts about THIS environment: Claude Code on the web (claude.ai/code), Linux
container, installed from this share repo by `cloud-bootstrap/bootstrap.py`.
This file REPLACES the source machine's `ops/environment.md` inside the
container (`claude-ops/ops/environment.md` in the repo is that file, kept
unedited as the Windows record); the block headings below are the same so
every cross-reference in `ops/*` and the global CLAUDE.md still lands on a
block, and each block says what changed. Recorded observations, not
assumptions — if a dispatch behaves as if a fact below is stale, re-verify and
update this file (in the repo, then re-run the installer); never silently work
around it.

**Dating rule (invariant, inherited)**: every block carries its OWN `as-of`
line. A single file-level date is banned.

## Subagent cost cap — tier → model (as-of 2026-09-02, unchanged policy)

Scope: **dispatched subagents only** (Agent / Workflow `agent()`). Says nothing
about the main-loop model — see "Main-loop model" below.

| Tier role | Model id | Notes |
|---|---|---|
| cheap | `haiku` | mechanical / high-volume stages |
| mid | `sonnet` | default for implementation / verification dispatches |
| top (capped) | `sonnet` + `effort: high` | the approved ceiling for ALL subagent work |
| forbidden | `opus`, `fable` | blocked by hook; per-instance exception needs explicit user approval |

**Cap policy (owner: user, 2026-07-07)** carries over verbatim: haiku or
sonnet only; severity on two axes, model × effort.

**Enforcement here**: `hooks/model_cap_guard.py`, mounted by the repo's
`.claude/settings.json` on `PreToolUse` matcher `Agent|Workflow` through
`.claude/hooks/run-hook.sh` (the shim execs the repo copy; the installed copy
under `~/.claude/hooks/` is identical and is what the rule files cite).
Verified 2026-09-02 by `bootstrap.py verify`: `model: opus` → deny, `model:
sonnet` → allow. The exception marker `[user-approved-top-tier]` and the two
known gaps (Workflow via `scriptPath` unscanned; `SendMessage`-resume inherits
the main-loop model) are unchanged from the source machine.

## Dispatch mechanisms available (as-of 2026-09-02, CLI 2.1.258 in the container)

- **Agent tool**: present, with per-call `model` (`haiku`/`sonnet`/`opus`/
  `fable`) and custom `subagent_type` from `~/.claude/agents/` (the eight
  definitions in `agents/` are installed there). Model precedence and the
  `fork` exception are as recorded on the source machine.
- **Spawns run in the BACKGROUND by default**; `run_in_background: false`
  only when the very next action needs the result.
- **Spawn depth is capped at 1** in this environment
  (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` in the container env): a subagent
  cannot itself dispatch. Plan fan-out from the main session only.
- **Cross-session messaging**: `ListAgents` / `SendMessage` exist; the
  container is single-session, so peers are the account's other cloud
  sessions, not processes on this machine. The Claude Code Remote MCP tools
  (`create_session`, `send_message`, triggers) are the cloud-native third
  dispatch path — none of them is scanned by `model_cap_guard.py`, so the cap
  is rules-enforced only on that path (same class as the `scriptPath` gap).
- **Capability is set in the definition, not at dispatch** — unchanged; the
  `tools:` allowlist is the only unconditional control.
- **Workflow tool — PRESENT in the container's first session.** The source
  pin `disableWorkflows: true` lives in user-scope `settings.json`, which the
  installer writes during SessionStart; a setting read at process start cannot
  take effect for the session that wrote it. From the second session of a
  cached container on, the pin holds. Either way the tool requires an explicit
  user opt-in ("ultracode", "use a workflow") before it may be called, so the
  practical exposure is one session's tool listing, not one session's use.
- **Effort is NOT settable per Agent-tool call** — unchanged. Note the host
  sets the session's effort (`CLAUDE_EFFORT` in the container env) and the
  installer deliberately does not carry `effortLevel` into `settings.json`.

## Red-team / reviewer separation (as-of 2026-09-02)

**The external dispatch tier does NOT exist here** — no `opencode`, no
`tools/extdispatch/`, no NIM key. Option 1 of the source machine's ordering is
unavailable; the fallback IS the route: fresh-context `sonnet` (high effort),
never the author, adversarial framing. `red-team/` (in the repo) ships the
acceptance layers 2–4 as running code with no dispatcher needed; layer 5 has
no transport in this container.

## External dispatch tier (as-of 2026-09-02) — ABSENT

Not installed, not installable (the dispatcher and its allowlist do not ship;
`tools/share-manifest.toml` `[[not_shipped]]` `tools/extdispatch/`). Every
rule that routes to it (`20-dispatch.md` §4a) takes the "no external tier"
branch. `hooks/extdispatch_entrypoint_guard.py` is not shipped either, so
nothing denies a direct `opencode` call — there is simply no `opencode` to
call.

## Main-loop model — READ IT, never infer it (as-of 2026-09-02)

The cloud host picks the session model; there is no `model:` pin in
`settings.json` here (the installer drops it on purpose). Procedure is
unchanged: take the tier from the session's own reported identity; when the
CLI withholds it, the `get_session` tool of the Claude Code Remote MCP server
reports `session_context.model` and `external_metadata.last_served_model`
(the two can differ — a fallback can serve a turn on another model). Relaxation
gate consequence (`05-authority.md` §2) is evaluated against that observation.

## Browser pane — recorded properties (as-of 2026-09-02) — NO PANE

There is no in-app Browser pane and no `mcp__Claude_Browser__*` /
`mcp__claude-in-chrome__*` tool in the container. `hooks/ui_verify_guard.py`
and `hooks/browser_pane_scope_guard.py` are mounted for fidelity and never
match (their matchers name those tools). What exists instead, measured:

| Property | Consequence |
|---|---|
| Chromium is pre-installed for Playwright (`PLAYWRIGHT_BROWSERS_PATH`, `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`); do not run `playwright install` | out-of-process pixels are the ONLY pixel route — which is already the source machine's default, so the standing premise ("the foreground is not commandeerable") holds trivially |
| No display server | `hidden` is not a state to probe for; a screenshot is always headless |
| Pictures reach the user via `SendUserFile` or an Artifact | unchanged rule, one fewer exception |

The L-009/L-010/L-013 lessons stay on record; none of their triggers can fire
here. review-when: a browser MCP tool appears in the container's tool list.

## Instruction-loading mechanics (as-of 2026-09-02 — NOT re-measured here)

Same platform, same loader; the source machine's table (CLAUDE.md charged in
full and after every compact; `paths:`-scoped rules charged only on a matching
read; skills only on invoke) is carried as a premise, not a measurement. Two
cloud-specific facts, observed:

- The global `~/.claude/CLAUDE.md` is written by the SessionStart installer.
  On a FRESH container the ordering between that write and the first system
  prompt is a platform property this file has not measured; from the second
  session of a cached container on, the file pre-exists and loads normally.
  Acceptance item A1 in `cloud-bootstrap/README.md` is the live check.
- `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` and
  `CLAUDE_ADDITIONAL_DIRECTORIES=/mnt/user-data` are set: a CLAUDE.md under
  the user-data mount would also load. None ships there today.

**Bash results carry no exit code** — unchanged (`is_error` is "shell reported
non-zero"; piped / `||`-guarded verifications are weak).

## Auto-mode environment scoping (as-of 2026-09-02) — NOT APPLICABLE

The container runs the permission mode the session was created with; no
`autoMode.environment` block is written. The rule ("keep the block
org/user-generic") has nothing to bind here.

## Local toolchain — measured, not assumed (as-of 2026-09-02)

Every line was run in the container on 2026-09-02. The traps the source
machine recorded (Store `python3` shim, `bash` → WSL, missing `rg`) are all
Windows facts and do NOT apply; the rows that replace them:

| Fact | Value | Why it is written down |
|---|---|---|
| OS | Ubuntu 24.04 LTS, x86_64, kernel 6.18 | the global CLAUDE.md's `<OS_NAME>` renders to this |
| Bash tool's shell | `/bin/bash` 5.2.21 — a real POSIX bash, no MSYS layer | `shell_transport_guard.py`'s MSYS-rewrite annotation (defect 3) cannot occur; defects 1–2 (backslash halving, ~7.7 KB ceiling) are Bash-tool transport facts and are left mounted as annotations |
| PowerShell | **absent** (`pwsh`, `powershell` not on PATH); no `PowerShell` tool | `ps_errorpref_guard.py` / `ps_pipeline_close_guard.py` are mounted and dormant; the CLAUDE.md PowerShell bullets are defect knowledge, not live guidance |
| `python3` / `python` | both resolve to CPython 3.11.15 | the hooks need 3.10+; the shim picks `python3` first |
| node / npm | v22.22.2 / 10.9.7 | `tools/archdiag/` (installed) runs on it |
| git | 2.43.0; committer identity re-asserted by the platform's own SessionStart hook | the platform's Stop hook refuses to end a turn with uncommitted or unpushed work — commit and push are part of "done" here |
| `rg`, `jq` | on PATH | a bare `rg` inside Bash works, unlike the source machine |
| `gh` | **absent** | GitHub goes through the `mcp__github__*` tools, never the CLI |
| CPU / RAM | 4 vCPU / 15 GB | fan-out of local processes is bounded by this, not by the 20-subagent ceiling |
| Disk | a fixed per-session allowance; `df` under-reports | "no space left" means delete build droppings, not that the machine is broken |
| Network | outbound HTTPS through the agent proxy (`HTTPS_PROXY`, CA bundle under `~/.ccr/`); never disable TLS verification | a 403/407 from the proxy is policy, not a defect in a tool |
| Time zone | UTC | every `as-of` and record timestamp here is UTC unless it says otherwise |
| Line endings | LF; `core.autocrlf` unset; the repo's `.gitattributes` governs | `<LINE_ENDING_CONVENTION>` renders to LF |

## Display & UI-build premise (as-of 2026-09-02, user-stated — carried, not measured)

The user's stated screens and scaling (2560×1440 or 2560×1600, 150%; FHD-class
baseline for premises) are facts about the USER, not the machine, and carry
over unchanged: UI deliverables built here are judged on that display. The
container itself has no display; nothing here can measure `devicePixelRatio`
except a headless browser, whose value is not the user's.

## Execution surface — cloud session (as-of 2026-09-02)

The engine is Claude Code (CLI 2.1.258) hosted by Claude Code on the web;
entry points are claude.ai/code, the mobile app, and the desktop app's cloud
sessions. The standing consequences:

- **The container is ephemeral.** The repo is cloned fresh; `~/.claude` is
  regenerated. Anything worth keeping is committed and pushed — the platform's
  Stop hook enforces this, and the operator's "never delete, archive instead"
  rule has no `archive/` that survives a container; archive INTO the repo or
  accept the loss knowingly.
- **The container is cached after the SessionStart hook completes**, so the
  installed `~/.claude` survives across sessions that resume the same
  container. `cloud-bootstrap.json` at the config root records which repo
  commit installed it; `bootstrap.py status` says whether HEAD has moved.
- **Records**: every session still writes `~/.claude/projects/<slug>/<cliSessionId>.jsonl`;
  it lives as long as the container. The session-transcript mirror
  (`ops_health_nudge.py` check 17) has no carrier here and stays silent by
  its own absence-is-normal rule; `compact-recovery` digests likewise live for
  one container. The durable record of a cloud session is the claude.ai
  session view, not a local file.
- **Memory**: `projects/<slug>/memory/` from the source machine is NOT here
  and nothing in this repo can bring it (OPERATOR-GUIDE.md 2.2). A session
  that needs a remembered user/project fact must ask or read it from a
  committed record.
- **Routing (cloud)**: unattended / batch / long work → a cloud session with
  a trigger (Routines) or a child session via the Claude Code Remote MCP
  tools; anything needing a real browser with the user's logins → not here.

## Cloud bootstrap — what installed this (as-of 2026-09-02)

`cloud-bootstrap/bootstrap.py install`, run by `.claude/hooks/session-start.sh`
on every SessionStart of a remote session (`CLAUDE_CODE_REMOTE=true`), copies
the shares into the config root: `CLAUDE.md` (rendered: OS/shell/line-ending
placeholders filled, adopter notes dropped), `rules/`, `ops/` (this file
overlaying `environment.md`), `references/PROJECTS.md`, `skill-trigger-dict.md`,
`skills/`, `hooks/`, `agents/`, `PHILOSOPHY.md`, `OPERATOR-GUIDE.md`,
`COMMIT-TEMPLATES.md`, `tools/memory-pipeline/preserve.py`, `tools/archdiag/`,
`thinking-notes/`, and a user-scope `settings.json` (permissions, env,
`disableWorkflows`; no `model`, no `effortLevel`, no hooks). Hooks are mounted
by the repo's `.claude/settings.json`. `bootstrap.py verify` is the acceptance
run; `cloud-bootstrap/README.md` is the manual.

Re-verify a block (and move its `as-of`) when: the CLI version in the
container changes; a browser or PowerShell tool appears in the tool list; the
installer's copy map changes; the platform documents SessionStart ordering
against the first system prompt; the user revises the cost cap. Whole-file
sweep: any block older than ~90 days.
