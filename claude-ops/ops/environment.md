# Environment Facts — recorded per `20-dispatch.md` §0

Facts about THIS environment (Claude Code on Windows, user gunda). Verified on
2026-07-07. These are recorded observations, not assumptions — if a dispatch
behaves as if a fact below is stale (new model names, missing parameters),
re-verify and update this file; never silently work around it.

## Tier → model mapping (the cost-cap policy)

| Tier role | Model id | Notes |
|---|---|---|
| cheap | `haiku` | Default main-session model (deliberate lowest-cost choice) |
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

**Known gap 2 — resume bypass (2026-07-10, hooks API offers no fix)**:
resuming a stopped background subagent via `SendMessage` restarts it on the
MAIN session's current model, not its spawn model, and no hook event can see
or block this (SendMessage payload has no model field; SubagentStart cannot
deny). **Rule**: for cost-capped work, when the main session runs above the
cap tier, prefer re-spawning a fresh Agent with an explicit capped `model`
over SendMessage-resume; if a resume is genuinely needed (context too costly
to rebuild), disclose the model escalation to the user before sending.
Details + evidence: `ops/lessons.md` L-001, hook header.

## Dispatch mechanisms available

- **Agent tool**: per-call `model` (haiku/sonnet/opus/fable) and custom
  `subagent_type` from `agents/`. Model precedence: call param > agent
  frontmatter > inherit main session.
- **Workflow tool**: deterministic fan-out; per-`agent()` call supports
  `model`, `effort` (low/medium/high/xhigh/max), `schema` (machine-enforced
  output-format contract — prefer this over prompt-side format pleading),
  `isolation: 'worktree'`, `agentType`.
- **Effort parameter exists** and is per-dispatch. Global default:
  `effortLevel: medium` in settings.json. Rule of thumb: low for mechanical
  stages, high for verification/judgment stages.

## Red-team / reviewer separation

No independent second CLI agent from a different model family is available in
this environment. The `20-dispatch.md` §4 fallback is therefore the DEFAULT
here: red-team = fresh-context sonnet (high effort), never the author, with an
adversarial framing. Do not spend time looking for a cross-family reviewer.

## Main-session model

`settings.json` pins `model: haiku` — a deliberate cost choice. Implication:
the dispatcher/judge is a non-frontier model, which is exactly the reader the
ops/ layer is written for. Residual weak points are R6 taste calls and the
intake gates; mitigation: escalate the main-session model manually for
judgment-heavy sessions, or lean on fresh-context sonnet review for intake.

## Refresh triggers

Re-verify this file when: model names in the harness change; the Agent or
Workflow tool schema changes; the user revises the cost cap; a hook test
(`hooks/model_cap_guard.py`) starts failing.
