# Environment Facts — recorded per `20-dispatch.md` §0

Facts about THIS environment (Claude Code on Windows, user gunda). These are
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
`model:` options before invoking).

**Known gap 2 — resume bypass (as-of 2026-07-10, hooks API offers no fix)**:
resuming a stopped background subagent via `SendMessage` restarts it on the
main session's CURRENT main-loop model, not its spawn model, and no hook event
can see or block this (SendMessage payload has no model field; SubagentStart
cannot deny). **Rule**: for cost-capped work, when the main-loop model is above
the cap tier, prefer re-spawning a fresh Agent with an explicit capped `model`
over SendMessage-resume; if a resume is genuinely needed (context too costly
to rebuild), disclose the model escalation to the user before sending.
Details + evidence: `ops/lessons.md` L-001, hook header.

## Dispatch mechanisms available (as-of 2026-08-12)

- **Agent tool**: per-call `model` (haiku/sonnet/opus/fable) and custom
  `subagent_type` from `agents/`. Model precedence: call param > agent
  frontmatter > inherit the main-loop model.
- **Capability is set in the definition, not at dispatch** (verified
  2026-08-12): a definition that omits `tools:` inherits every tool a subagent
  may hold — including `Edit`/`Write` — so "read-only" written in a prompt
  enforces nothing. The `tools:` allowlist is the only unconditional control.
  `permissionMode` is defence-in-depth only: a parent session in `acceptEdits`
  or `bypassPermissions` overrides it, and a parent in `auto` mode makes the
  frontmatter value be ignored outright.
- **Workflow tool**: deterministic fan-out; per-`agent()` call supports
  `model`, `effort` (low/medium/high/xhigh/max), `schema` (machine-enforced
  output-format contract — prefer this over prompt-side format pleading),
  `isolation: 'worktree'`, `agentType`.
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

A cross-family reviewer NOW EXISTS. The previous entry said "no independent
second CLI agent from a different model family is available… do not spend time
looking for one"; that was true when written and is false now. It is corrected
here rather than merely deleted, because it is the shape of stale fact that does
not read as stale — a session would have obeyed it and never looked.

Two options, in order:

1. **External dispatch** (`## External dispatch tier` below) — genuinely a
   different model family, free, no credential. Measured 2026-08-16 on a real
   commit: 3 anchored findings in 110 s, two overlapping a sonnet control's
   seven and one the control missed in both of its runs (a reproduced
   `TypeError`). Route red-team here first.
2. **Fallback, unchanged**: fresh-context sonnet (high effort), never the
   author, adversarial framing — for anything the external tier may not see
   (see the redline rules below).

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

**Enforcement**: `hooks/ui_verify_guard.py` (PreToolUse matcher
`mcp__(Claude_Browser\|claude-in-chrome)__(computer\|javascript_tool)`, plus a
PostToolUse javascript_tool matcher). Denies a `getComputedStyle` call with no
settle token; denies a screenshot until a `visibilityState` probe has run
(marker `%TEMP%\claude-ui-verify-guard\<session>.probe`, 300s TTL); and ROUTES
— deny + ready-to-run headless command — when the probe's RESULT was `hidden`
(PostToolUse writes the result into the marker; parse failure degrades to the
plain gate). `visible` unlocks the pane screenshot, so visible+timeout stays a
distinct fault. Escape hatch: literal `intentional-midflight` stands down the
L-010 branch. Tested 2026-08-16: 19/19 (`tools/ui-verify-test/`) + live
(marker annotated `hidden`, route denial fired). Known gap: hook header
(`read_page`-inferred styles invisible — theoretical).

**Pane-scope enforcement (as-of 2026-08-14, re-verified 2026-08-16)**:
`hooks/browser_pane_scope_guard.py` (PreToolUse, matcher
`mcp__(Claude_Browser\|claude-in-chrome)__(navigate\|preview_start)`) logs
every pane navigation to `telemetry/browser-nav.jsonl` (live — the app's own
log never records preview URLs) and enforces an **ALLOWLIST**: loopback hosts
allowed by the hook itself; anything else needs
`hooks/browser-pane-allowlist.json`, edited only by the user; denials are loud
and route to claude-in-chrome (separate process, never denied) / WebFetch /
headless Playwright. The blocklist file survives only to annotate deny
messages with recorded crash reasons.
Standing reason, evidence (7/7), history, and the third-party rule of thumb
(unchanged; promote on a second independent incident): `rule-registry.md`
"in-app Browser pane" + `lessons.md` L-013.

**Out-of-process pictures — the DEFAULT pixel route (as-of 2026-08-16,
measured)**: headless Playwright in its own process. Full probe
(hover+settle+`--shot`) 1.4s, `npx playwright screenshot` 1.5s, PNGs
delivered; the hidden pane: 5s timeout, none. The `playwright` package
resolves ONLY from the npx cache, so `node ui-probe.mjs` needs a dir tree
with playwright installed. Recipes, resolution facts, representativeness
limits, E-6 flag research, asset + browser paths:
`ops/references/browser-pane-pixel-route.md`.

## Instruction-loading mechanics (as-of 2026-08-11, Claude Code 2.1.220)

Measured, not read off the docs — the docs describe path-scoping and
user-level rules separately and never state that the two compose.

| Carrier | Charged at session start? | Verified how |
|---|---|---|
| `~/.claude/CLAUDE.md` | yes, in full | hook log, `load_reason: session_start` |
| `@path` imports inside it | yes ("imported files still load at launch") | official docs only |
| `~/.claude/rules/x.md` **without** `paths:` | yes | probe `_probe-always.md`, 2 runs |
| `~/.claude/rules/x.md` **with** `paths:` | **no** | same 2 runs — absent from startup |
| ...the same file, when a matching file is read | loaded then | probe `_probe-match.md`, `load_reason: path_glob_match`, content observed in context |
| skill | only when invoked/judged relevant | official docs |

So the only carriers that reduce startup cost are: delete/merge, a
`paths:`-scoped user rule, or a skill. Splitting into imports or unscoped
rules saves nothing. Sinking an INTENT-triggered rule into `ops/` makes it a
ghost rule (`lessons.md` L-011) — `ops/*` is reached only via CLAUDE.md's
project-operations clause.

**Observability**: `hooks/instructions_loaded_logger.py` (InstructionsLoaded,
logging only, fail-open) appends to `telemetry/rule-loads.jsonl`. Payload
fields: `file_path`, `memory_type`, `load_reason`. Startup-cost baseline:
`tools/context-budget/startup_baseline.py`.

`load_reason` values observed so far: `session_start`, `path_glob_match`,
and **`compact`** — CLAUDE.md is re-injected after every `/compact`, so its
byte cost is paid per compaction as well as per session. Blind spot: only
CLAUDE.md has ever emitted this event. `MEMORY.md` is injected (it appears in
context) but never appears in the log, so the logger cannot be used to prove a
memory file did or did not load.

**Trim effect sizes are below the measurement noise floor.** The E1 trim
removed 1,286 B net (~320 tokens at 4 chars/token) from a startup prompt whose
observed per-session spread in this project is 57.3k-70.4k tokens. A ~0.5%
signal cannot be recovered from a ~13k-token range no matter how many sessions
are collected, so "the MIN floor drops after the change" is not a usable
acceptance test. Judge context-budget work by adherence evidence
(`rule-loads.jsonl` shows the rule firing when it should) and by the on-disk
inventory, not by a token delta.

**Bash results carry no exit code** (measured 2026-08-11). A successful Bash
`toolUseResult` is a dict of `interrupted / isImage / noOutputExpected /
stderr / stdout`; on failure it degenerates to a plain string beginning
`"Exit code N"` and the result block is flagged `is_error: true`. So
`is_error` is exactly "the shell reported non-zero" -- no divergence exists to
find between them. The gap that matters is upstream: `cmd || true` and
`cmd | head` both exit 0 while the command inside failed, and both were
observed reporting `is_error: false` with `FAILED` sitting in stdout. Any gate
keying on `is_error` must also sniff stdout, or downgrade piped / `||`-guarded
verifications to "weak" rather than counting them as verified.

**Baseline for `C--Users-gunda--claude`** (24 sessions since 2026-07-25):
startup prompt MIN 36,742 / MEDIAN 58,891 tokens; always-loaded instruction
files 17,139 B. CLAUDE.md is therefore ~11% of the floor (estimate) — the
dominant startup cost is the tool/MCP/skill roster, not the rules.

## Auto-mode environment scoping (as-of 2026-08-16, Claude Code claude.exe 2026-08-15 build)

`settings.json` `autoMode.environment` is applied UNCONDITIONALLY, in every
project — the classifier reads user + managed + `--settings` scopes only and
DELIBERATELY ignores project `.claude/settings.json` / `settings.local.json`
(anti-injection: a repo must not be able to set its own classifier rules), so
there is no per-project filter, re-derivation, or supported per-project
carrier. Scopes CONCATENATE (personal entries extend managed ones, never
remove them). The setup flow writes to userSettings (docs silent; verified in
the binary: setup/reset both target `"userSettings"`, and projectSettings/
localSettings autoMode is ignored with a logged warning). The block is
"spliced into the classifier prompt on every auto-mode decision" (verbatim
binary string; an over-size warning says "consider pruning stale entries").
Consequence: project-specific facts written there leak into every other
project's auto-mode decisions — keep the block org/user-generic; a
project-bound profile has no home other than per-invocation `--settings`.
Incident: an NTUMail2TG session wrote a project profile there 2026-08-16;
user removed it same day. Evidence: code.claude.com/docs/en/auto-mode-config
(externally verified) + `claude.exe` string probe (locally verified, minified
source — behaviour-level claims only).

Re-verify a block (and move its `as-of`) when: model names in the harness
change; the Agent or Workflow tool schema changes; the user revises the cost
cap; a hook test (`hooks/model_cap_guard.py`, `hooks/ui_verify_guard.py`,
`hooks/browser_pane_scope_guard.py`)
starts failing; `settings.json` `model:` is edited; the Browser-pane MCP tool
names change (the UI guard's matcher is keyed to them). Whole-file sweep: any
block older than ~90 days.
