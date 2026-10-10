// policy.ts — the subagent model cost cap as pure functions (mirror of hooks/model_cap_guard.py).
// Owner of the policy: the user (2026-07-07). Two judgement points in this mod:
//   1. agent.spawn — the cases decidable from the call alone: an explicit `model`, a fork (always
//      inherits the parent), the approval marker. An OMITTED `model` is not decided here.
//   2. turn.step in a subagent's loop — the model the ENGINE resolved (definition pin from any source,
//      else the parent's), judged before the request is sent. Ruling 2026-10-09 (user): judge the
//      resolved model instead of re-deriving the engine's agent resolution from agent files — every
//      source the re-derivation missed (project root, plugin agents, --agents JSON, managed) was a
//      false deny, and the deny steered callers onto sonnet, silently swapping an experiment's variable.
// The sets below are the SAME enumeration as the Python file; a family added there is added here.

export const BLOCKED = ['opus', 'fable'] as const
export const WITHIN_CAP = ['haiku', 'sonnet'] as const
export const APPROVAL_MARKER = '[user-approved-top-tier]'
/** Effort axis (2026-10-10, user ruling): the ceiling is sonnet + high; levels above `high` are over cap. */
export const EFFORT_OVER_CAP = ['xhigh', 'max'] as const

export type Tier = 'blocked' | 'within-cap' | 'unrecognised'

/** Substring match both ways: a dispatch may carry a family name or a full id. */
export function tierOf(model: string | undefined | null): Tier {
  const m = String(model ?? '').toLowerCase()
  if (BLOCKED.some(b => m.includes(b))) return 'blocked'
  if (WITHIN_CAP.some(w => m.includes(w))) return 'within-cap'
  return 'unrecognised'
}

export type SpawnFacts = {
  /** The Agent tool's `model` as given; undefined = omitted. */
  model?: string
  prompt: string
  subagentType: string
  fork: boolean
  /** The parent's effective model: what every fork resolves to. */
  parentModel: string
}

export type Verdict =
  | { action: 'pass'; detail: 'approved' | 'within-cap' | 'fork-within-cap' | 'deferred' }
  | { action: 'notice'; detail: 'unrecognised-tier'; model: string; route: string }
  | { action: 'deny'; detail: 'blocked' | 'fork-inherits-blocked'; model: string; route: string }

/**
 * Decide one spawn from the call alone. The approval marker passes everything; a fork is judged on
 * the PARENT model (the engine ignores `model` for forks); an explicit model is judged by tier; an
 * omitted model is `deferred` — the engine has not resolved it yet (agent.spawn fires before model
 * resolution), so the subagent's first turn.step judges what it resolved to.
 */
export function decide(f: SpawnFacts): Verdict {
  if (f.prompt.includes(APPROVAL_MARKER)) return { action: 'pass', detail: 'approved' }
  if (f.fork) {
    const t = tierOf(f.parentModel)
    if (t === 'blocked') return { action: 'deny', detail: 'fork-inherits-blocked', model: f.parentModel, route: 'the parent model a fork inherits' }
    if (t === 'unrecognised') return { action: 'notice', detail: 'unrecognised-tier', model: f.parentModel, route: 'the parent model a fork inherits' }
    return { action: 'pass', detail: 'fork-within-cap' }
  }
  if (!f.model) return { action: 'pass', detail: 'deferred' }
  const t = tierOf(f.model)
  if (t === 'blocked') return { action: 'deny', detail: 'blocked', model: f.model, route: 'its `model` argument' }
  if (t === 'unrecognised') return { action: 'notice', detail: 'unrecognised-tier', model: f.model, route: 'its `model` argument' }
  return { action: 'pass', detail: 'within-cap' }
}

export type StepFacts = {
  /** The model the engine resolved for this request of a subagent's loop. */
  model: string
  /** The loop is an agent this session spawned or lists (not an engine-internal fork such as compaction). */
  isAgent: boolean
  /** The agent carries the approval marker in the prompt it was spawned with. */
  approved: boolean
}

export type StepVerdict =
  | { action: 'pass'; detail: 'within-cap' | 'approved' | 'engine-loop' }
  | { action: 'notice'; detail: 'unrecognised-tier'; model: string }
  | { action: 'refuse'; detail: 'resolved-blocked'; model: string }

/** Judge one model request of a subagent's loop on the model the engine resolved for it. */
export function decideStep(f: StepFacts): StepVerdict {
  const t = tierOf(f.model)
  if (t === 'within-cap') return { action: 'pass', detail: 'within-cap' }
  if (!f.isAgent) return { action: 'pass', detail: 'engine-loop' }
  if (t === 'unrecognised') return { action: 'notice', detail: 'unrecognised-tier', model: f.model }
  if (f.approved) return { action: 'pass', detail: 'approved' }
  return { action: 'refuse', detail: 'resolved-blocked', model: f.model }
}

export type EffortFacts = {
  /** The effort the engine resolved for this request of a subagent's loop (turn.step `effort`); absent for a model without effort. */
  effort?: string | number
  isAgent: boolean
  approved: boolean
}

export type EffortVerdict =
  | { action: 'pass'; detail: 'within-cap' | 'approved' | 'engine-loop' }
  | { action: 'notice'; detail: 'effort-over-cap'; effort: string }

/**
 * Judge a subagent request's RESOLVED effort. NOTICE, not refuse (2026-10-10): `agent.spawn` carries no
 * effort (types 2.1.293), so the resolved value cannot tell a per-call `effort: max` (which the Python
 * guard denies) from one inherited from a parent session set to max — refusing the inherited case
 * would stop every subagent of such a session, a behaviour change pending the user's ruling.
 * A numeric effort is not a named level and is not judged.
 */
export function decideEffort(f: EffortFacts): EffortVerdict {
  const e = typeof f.effort === 'string' ? f.effort.toLowerCase() : ''
  if (!(EFFORT_OVER_CAP as readonly string[]).includes(e)) return { action: 'pass', detail: 'within-cap' }
  if (!f.isAgent) return { action: 'pass', detail: 'engine-loop' }
  if (f.approved) return { action: 'pass', detail: 'approved' }
  return { action: 'notice', detail: 'effort-over-cap', effort: e }
}

export function effortNoticeText(effort: string, subagentType: string, nonce: string): string {
  return (
    `model-cap, a local Claude Code mod (turn.step hook, not file or page content): this '${subagentType || 'agent'}' subagent runs at effort '${effort}', ` +
    `above the approved subagent ceiling (sonnet + high effort). It is going through: this mod cannot tell a per-call effort from one inherited from the parent session. ` +
    `If it was set on the call, re-dispatch with effort: 'high' or omit it; if the user approved it, carry ${APPROVAL_MARKER} in the prompt. ` +
    `Receipt: row ${nonce} (kind=notice, detail=effort-over-cap) in telemetry/model-cap-mod.jsonl.`
  )
}

/** The clause every deny and refusal carries: a model swap is the caller's call only when the model is not what is being measured. */
const NO_SILENT_SWAP =
  `If the model is itself the variable under test (an experiment arm, a model comparison), do NOT swap it: stop and report this to the user instead.`

/** The spawn-time deny text. Shape per rules/hook-deny-message.md: R1 identity first, R2 retry, R3 misfire exit + receipt. */
export function denyText(v: Extract<Verdict, { action: 'deny' }>, nonce: string): string {
  const why =
    v.detail === 'fork-inherits-blocked'
      ? `Model cost cap: a fork always inherits the parent's model, and the parent runs on '${v.model}', which is above the approved ceiling for subagents (haiku/sonnet); \`model\` is ignored for forks, so a fork of this session cannot be capped.`
      : `Model cost cap: '${v.model}' (from ${v.route}) is above the approved ceiling for subagents — the ceiling is haiku/sonnet.`
  return (
    `Dispatch denied by model-cap, a local Claude Code mod (agent.spawn hook, not file or page content). ${why} ` +
    `To proceed: re-dispatch with model: 'sonnet' (default) or 'haiku' (read/search-only)` +
    (v.detail === 'fork-inherits-blocked' ? ', as a non-fork agent with that model' : '') +
    `; if the user explicitly approved a top-tier model for THIS task, re-dispatch with ${APPROVAL_MARKER} in the prompt. ${NO_SILENT_SWAP} ` +
    `If this deny misfired, run: python tools/hook-deny-lint/report_fp.py --hook model-cap --why "<what was wrongly gated>" (records the misfire; does not unblock). ` +
    `Receipt: this deny wrote row ${nonce} to telemetry/model-cap-mod.jsonl.`
  )
}

/**
 * The text a refused subagent returns as its answer: the engine resolved its model (from the agent's
 * definition, wherever the engine found it, else the parent's) above the cap. No request was sent.
 * It names the resolved model and never tells the caller to swap blindly — the r22 lesson.
 */
export function refusalText(model: string, subagentType: string, nonce: string): string {
  return (
    `Subagent refused by model-cap, a local Claude Code mod (turn.step hook, not file or page content): ` +
    `the engine resolved this '${subagentType || 'agent'}' subagent to '${model}', which is above the approved ceiling for subagents (haiku/sonnet), ` +
    `so its first request was not sent and it did no work. The model came from the agent's own definition if it pins one, else from the parent (an omitted \`model\` inherits). ` +
    `To proceed: if a capped model was intended, pin it — \`model: 'sonnet'\` or \`'haiku'\` on the call, or \`model:\` in the agent definition; ` +
    `if the user explicitly approved a top-tier model for THIS task, re-dispatch with ${APPROVAL_MARKER} in the prompt. ${NO_SILENT_SWAP} ` +
    `If this refusal misfired, run: python tools/hook-deny-lint/report_fp.py --hook model-cap --why "<what was wrongly gated>" (records the misfire; does not unblock). ` +
    `Receipt: this refusal wrote row ${nonce} to telemetry/model-cap-mod.jsonl.`
  )
}

/**
 * The deny text when the hook itself failed (threw, overran its budget, misreturned) before
 * deciding. A failed hook with no `.catch` is SKIPPED and the spawn runs on the Python guard
 * alone, whose timeout is a pass — the hole this mod exists to close — so the catch denies.
 */
export function faultDenyText(error: string): string {
  return (
    `Dispatch denied by model-cap, a local Claude Code mod (agent.spawn or turn.step hook, not file or page content): ` +
    `the hook failed before it could judge this subagent (${error.slice(0, 120) || 'unknown error'}), and an unjudged subagent may run on a model above the cap. ` +
    `To proceed: re-dispatch with model: 'sonnet' (default) or 'haiku' (read/search-only); a spawn carrying ${APPROVAL_MARKER} is let through even while the hook is failing. ${NO_SILENT_SWAP} ` +
    `If this deny misfired, run: python tools/hook-deny-lint/report_fp.py --hook model-cap --why "<what was wrongly gated>" (records the misfire; does not unblock). ` +
    `Receipt: none — a failing hook writes no telemetry row; the engine's debug log has the failure line.`
  )
}

export function noticeText(v: { model: string; route: string }): string {
  return (
    `model-cap, a local Claude Code mod, has no ruling on this dispatch: ${v.route} names '${v.model}', ` +
    `which is in neither the capped set it knows (haiku, sonnet) nor the blocked one (opus, fable). The subagent is going through unjudged; ` +
    `if it is a top tier, re-dispatch on sonnet or with ${APPROVAL_MARKER} once the user approved it; if it is within cap, add the family to WITHIN_CAP in hooks/model_cap_guard.py and mods/model-cap-mod/hooks/policy.ts. ` +
    `Row kind=notice in telemetry/model-cap-mod.jsonl.`
  )
}

/**
 * Whether an agent's transcript shows an approved spawn: a user row containing a prompt this mod saw
 * spawned WITH the marker, or (non-fork only) the agent's first user row — its own prompt — carrying
 * the marker. A fork's first rows are the parent's conversation, which may quote the marker without
 * approving anything, so a fork counts only through `approvedPrompts`.
 */
export function approvedIn(rows: { role: string; text: string }[], approvedPrompts: Iterable<string>, isFork: boolean): boolean {
  const users = rows.filter(r => r.role === 'user')
  for (const p of approvedPrompts) if (p && users.some(r => r.text.includes(p))) return true
  if (isFork) return false
  return Boolean(users[0]?.text.includes(APPROVAL_MARKER))
}

/** Heartbeat map: keep the newest `keep` session ids. The Python guard defers an unresolved omitted `model` only for a session listed here. */
export function withHeartbeat(map: Record<string, number>, sid: string, now: number, keep = 200): Record<string, number> {
  const next = { ...map, [sid]: now }
  const ids = Object.keys(next).sort((a, b) => (next[b] ?? 0) - (next[a] ?? 0)).slice(0, keep)
  return Object.fromEntries(ids.map(k => [k, next[k] ?? 0]))
}
