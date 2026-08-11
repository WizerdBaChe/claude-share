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

## Dispatch mechanisms available (as-of 2026-07-07)

- **Agent tool**: per-call `model` (haiku/sonnet/opus/fable) and custom
  `subagent_type` from `agents/`. Model precedence: call param > agent
  frontmatter > inherit the main-loop model.
- **Workflow tool**: deterministic fan-out; per-`agent()` call supports
  `model`, `effort` (low/medium/high/xhigh/max), `schema` (machine-enforced
  output-format contract — prefer this over prompt-side format pleading),
  `isolation: 'worktree'`, `agentType`.
- **Effort parameter exists** and is per-dispatch. Global default:
  `effortLevel: medium` in settings.json. Rule of thumb: low for mechanical
  stages, high for verification/judgment stages.

## Red-team / reviewer separation (as-of 2026-07-07)

No independent second CLI agent from a different model family is available in
this environment. The `20-dispatch.md` §4 fallback is therefore the DEFAULT
here: red-team = fresh-context sonnet (high effort), never the author, with an
adversarial framing. Do not spend time looking for a cross-family reviewer.

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

## Browser-pane UI verification (as-of 2026-08-08)

Two recorded properties of an in-app browser pane tool surface, both
measured, both worth enforcing by hook rather than by recall (why:
`lessons.md` L-011):

| Property | Consequence | Recorded in |
|---|---|---|
| An occluded pane reports `document.visibilityState === "hidden"`; compositing stops while CDP/devtools-protocol reads keep working | every screenshot call TIMES OUT — a display-state fault, never a permission one | L-009 |
| `getComputedStyle()` during a CSS transition returns the interpolated mid-flight value | hover/focus assertions come back FLAKY, not stably wrong | L-010 |

**Enforcement**: a PreToolUse hook matched to the browser-pane tool names,
where the harness supports PreToolUse hooks. It denies a `getComputedStyle`
call carrying no settle token in the same call, and denies a screenshot until
a `visibilityState` probe has run in this session (a per-session marker with a
short TTL). Both denials name the corrective call, so the cost is one retry.
Escape hatch: a literal marker anywhere in the script call stands down the
settle-check branch, for the rare case where the mid-transition value IS the
thing being measured. Known gap: only explicit `getComputedStyle`-family calls
are visible; a style value inferred from an accessibility-tree read is not —
theoretical, since those tools do not report computed style.

**Out-of-process pictures**: a headless-browser probe script that drives
hover/focus, finishes animations, and returns computed styles plus an
optional screenshot as JSON is the recommended path for a real picture when
the in-app pane cannot be trusted for one — build one appropriate to your own
tooling if the environment doesn't already have one.

## Instruction-loading mechanics (as-of 2026-08-11)

Measured, not read off the docs — official docs tend to describe path-scoping
and user-level rules separately and never state that the two compose.

| Carrier | Charged at session start? | Verified how |
|---|---|---|
| The always-loaded global instructions file | yes, in full | startup instrumentation, `load_reason: session_start` |
| `@path` imports inside it | yes ("imported files still load at launch") | official docs only |
| A user-level rule file **without** a path scope | yes | probe file, 2 runs |
| The same kind of file **with** a path scope | **no** | same 2 runs — absent from startup |
| ...that scoped file, when a matching file is read | loaded then | probe file, `load_reason: path_glob_match`, content observed in context |
| A skill | only when invoked/judged relevant | official docs |

So the only carriers that reduce startup cost are: delete/merge, a
path-scoped user rule, or a skill. Splitting into imports or unscoped rules
saves nothing. Sinking an INTENT-triggered rule into an ops-style layer makes
it a ghost rule (`lessons.md` L-011) if that layer is itself only reached via
a conditional routing clause.

**Observability**: a logging-only hook on whatever "instructions loaded"
event the harness exposes (fail-open, never denies) can append a small
per-file record — file path, memory type, load reason — to a local log. This
is what the table above was verified against.

**Trim effect sizes can fall below measurement noise.** A trim that removes a
few hundred bytes from a startup prompt whose observed per-session spread
spans many thousands of tokens is not a usable acceptance test by itself — a
sub-1% signal cannot be recovered from a much wider range no matter how many
sessions are collected. Judge context-budget work by adherence evidence (the
rule firing when it should) and by the on-disk inventory, not by a token
delta alone.

**Shell results carry no reliable exit-code signal by themselves.** A
tool-layer "error" flag is exactly "the shell reported non-zero" — no
divergence to find between the two. The gap that matters is upstream:
`cmd || true` and `cmd | head` both exit 0 while the command inside failed,
and can report success while `FAILED` sits in stdout. Any gate keying on the
tool-layer error flag must also sniff stdout, or downgrade piped /
`||`-guarded verifications to "weak" rather than counting them as verified.

## Refresh triggers

Re-verify a block (and move its `as-of`) when: model names in the harness
change; the Agent or Workflow tool schema changes; the user revises the cost
cap; a hook test (`hooks/model_cap_guard.py`, the UI-verification hook if one
exists) starts failing; `settings.json` `model:` is edited; the browser-pane
tool names change (a UI guard's matcher is keyed to them). Whole-file sweep:
any block older than ~90 days.
