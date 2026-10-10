// gate.ts — pure: when a check may start, and the per-session state it reads.
// Design: references/feedback-observer-design.md §2.3 state machine, FO-R-1/3, FO-INV-5.

export const MAX_CHECKS = 12          // all checks per session (FO-R-3)
export const MAX_CADENCE = 9          // of which cadence checks; the rest is kept for forced ones
export const MIN_TOOL_CALLS = 6       // a "substantial" main turn (FO-R-1 a)
export const COOLDOWN_TURNS = 3
export const COOLDOWN_MS = 10 * 60_000
export const MAX_CONSECUTIVE_ERRORS = 3
/** Edit/Write under ~/.claude's subsystem roots also makes a turn substantial. */
export const SUBSYSTEM_PATH = /[\\/]\.claude[\\/](hooks|skills|tools|ops|rules)[\\/]/i
/** The user's own close-out words (FO-R-1 b); matched on origin.kind === 'composer' only. */
export const CLOSEOUT_RE = /收工|收掉|收尾/

export type Mode = 'idle' | 'inert' | 'disabled' | 'exhausted'
export type Trigger = 'cadence' | 'forced' | 'manual'

export type State = {
  mode: Mode
  /** messages.length at the end of the last check's window (next window starts here). */
  lastCount: number
  checks: number
  cadenceChecks: number
  mainTurns: number
  lastCheckTurn: number
  lastCheckAt: number
  consecutiveErrors: number
  closeoutPending: boolean
}

export function initialState(): State {
  return {
    mode: 'idle', lastCount: 0, checks: 0, cadenceChecks: 0, mainTurns: 0,
    lastCheckTurn: -1_000_000, lastCheckAt: 0, consecutiveErrors: 0, closeoutPending: false,
  }
}

/** Restore from `$.store`: unknown or malformed → initial; a persisted dead mode stays dead. */
export function restoreState(v: unknown): State {
  const s = initialState()
  if (!v || typeof v !== 'object') return s
  const o = v as Record<string, unknown>
  for (const k of Object.keys(s) as (keyof State)[]) {
    if (k in o && typeof o[k] === typeof s[k]) (s as any)[k] = o[k]
  }
  if (!['idle', 'inert', 'disabled', 'exhausted'].includes(s.mode)) s.mode = 'idle'
  return s
}

export type TurnFacts = { toolCalls: number; touchedSubsystem: boolean; aborted: boolean; now: number }

/**
 * At a MAIN turn.complete: which check, if any, may start now. Pure; the caller then
 * mutates state through `consume()` once the check actually starts.
 */
export function decide(s: State, t: TurnFacts): Trigger | null {
  if (s.mode !== 'idle') return null
  if (s.checks >= MAX_CHECKS) return null
  if (s.closeoutPending) return 'forced'
  if (t.aborted) return null
  const substantial = t.toolCalls >= MIN_TOOL_CALLS || t.touchedSubsystem
  if (!substantial) return null
  if (s.cadenceChecks >= MAX_CADENCE) return null
  if (s.checks === 0) return 'cadence'          // no previous check: nothing to cool down from
  const mult = s.consecutiveErrors > 0 ? 2 : 1
  if (s.mainTurns - s.lastCheckTurn < COOLDOWN_TURNS * mult) return null
  if (t.now - s.lastCheckAt < COOLDOWN_MS * mult) return null
  return 'cadence'
}

/** A check is starting: spend the slot(s) it takes. */
export function consume(s: State, trigger: Trigger, now: number): State {
  const n = { ...s }
  n.checks += 1
  if (trigger === 'cadence') n.cadenceChecks += 1
  if (trigger === 'forced') n.closeoutPending = false
  n.lastCheckTurn = n.mainTurns
  n.lastCheckAt = now
  return n
}

export type Outcome =
  | 'ok' | 'undetermined' | 'skipped' | 'timeout' | 'error' | 'refused'
  | 'backoff-disabled' | 'cap-reached' | 'no-prompt' | 'lost'

/** A check settled with `outcome`: error bookkeeping and the dead-state transitions. */
export function settle(s: State, outcome: Outcome, toIndex: number): State {
  const n = { ...s, lastCount: Math.max(s.lastCount, toIndex) }
  if (outcome === 'ok' || outcome === 'undetermined' || outcome === 'skipped') n.consecutiveErrors = 0
  if (outcome === 'timeout' || outcome === 'error') n.consecutiveErrors += 1
  if (outcome === 'refused' || outcome === 'no-prompt') n.mode = 'disabled'
  if (n.consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) n.mode = 'disabled'
  if (n.mode === 'idle' && n.checks >= MAX_CHECKS) n.mode = 'exhausted'
  return n
}

export function isSubsystemWrite(tool: string, filePath: unknown): boolean {
  if (!['Edit', 'Write', 'MultiEdit', 'NotebookEdit'].includes(tool)) return false
  return typeof filePath === 'string' && SUBSYSTEM_PATH.test(filePath)
}
