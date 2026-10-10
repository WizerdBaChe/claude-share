import { test, expect, describe } from 'claude-code/testing'
import {
  COOLDOWN_MS, COOLDOWN_TURNS, MAX_CADENCE, MAX_CHECKS, consume, decide, initialState, isSubsystemWrite,
  restoreState, settle, type State,
} from '../hooks/gate'

const quiet = { toolCalls: 0, touchedSubsystem: false, aborted: false, now: 0 }
const heavy = { toolCalls: 6, touchedSubsystem: false, aborted: false, now: 0 }

function afterCooldown(s: State, now: number): State {
  return { ...s, mainTurns: s.lastCheckTurn + COOLDOWN_TURNS, lastCheckAt: now - COOLDOWN_MS }
}

describe('gate', () => {
  test('5 tool calls is not substantial, 6 is; a subsystem write is', async () => {
    const s = initialState()
    expect(decide(s, { ...quiet, toolCalls: 5 })).toBe(null)
    expect(decide(s, { ...quiet, toolCalls: 6 })).toBe('cadence')
    expect(decide(s, { ...quiet, touchedSubsystem: true })).toBe('cadence')
    expect(isSubsystemWrite('Edit', 'C:\\Users\\x\\.claude\\hooks\\a.py')).toBe(true)
    expect(isSubsystemWrite('Edit', 'C:\\Users\\x\\.claude\\reports\\a.md')).toBe(false)
    expect(isSubsystemWrite('Read', 'C:\\Users\\x\\.claude\\hooks\\a.py')).toBe(false)
  })

  test('cooldown blocks a second cadence check within 3 turns or 10 minutes', async () => {
    let s = consume(initialState(), 'cadence', 1_000)
    s = { ...s, mainTurns: s.lastCheckTurn + 2 }
    expect(decide(s, { ...heavy, now: 1_000 + COOLDOWN_MS })).toBe(null)       // turns
    s = { ...s, mainTurns: s.lastCheckTurn + COOLDOWN_TURNS }
    expect(decide(s, { ...heavy, now: 1_000 + COOLDOWN_MS - 1 })).toBe(null)   // minutes
    expect(decide(s, { ...heavy, now: 1_000 + COOLDOWN_MS })).toBe('cadence')
  })

  test('a pending close-out forces a check inside the cooldown and even on a quiet turn', async () => {
    let s = consume(initialState(), 'cadence', 1_000)
    s = { ...s, closeoutPending: true }
    expect(decide(s, { ...quiet, now: 1_001 })).toBe('forced')
    const after = consume(s, 'forced', 1_001)
    expect(after.closeoutPending).toBe(false)
    expect(after.cadenceChecks).toBe(1)
    expect(after.checks).toBe(2)
  })

  test('cadence checks stop at MAX_CADENCE while forced checks still run; the cap ends everything', async () => {
    let s = initialState()
    let now = 0
    for (let i = 0; i < MAX_CADENCE; i++) {
      now += COOLDOWN_MS
      s = afterCooldown(s, now)
      expect(decide(s, { ...heavy, now })).toBe('cadence')
      s = consume(s, 'cadence', now)
    }
    now += COOLDOWN_MS
    s = afterCooldown(s, now)
    expect(decide(s, { ...heavy, now })).toBe(null)                            // 10th cadence refused
    s = { ...s, closeoutPending: true }
    expect(decide(s, { ...heavy, now })).toBe('forced')                        // slots remain for forced
    s = consume(s, 'forced', now)
    s = consume({ ...s, closeoutPending: true }, 'forced', now)
    s = consume({ ...s, closeoutPending: true }, 'forced', now)
    expect(s.checks).toBe(MAX_CHECKS)
    s = settle(s, 'ok', 10)
    expect(s.mode).toBe('exhausted')
    expect(decide({ ...s, closeoutPending: true }, { ...heavy, now })).toBe(null)
  })

  test('errors double the cooldown and three in a row disable; refused disables at once', async () => {
    let s = consume(initialState(), 'cadence', 1_000)
    s = settle(s, 'error', 5)
    expect(s.consecutiveErrors).toBe(1)
    s = { ...s, mainTurns: s.lastCheckTurn + COOLDOWN_TURNS }
    expect(decide(s, { ...heavy, now: 1_000 + COOLDOWN_MS })).toBe(null)        // doubled
    s = { ...s, mainTurns: s.lastCheckTurn + 2 * COOLDOWN_TURNS }
    expect(decide(s, { ...heavy, now: 1_000 + 2 * COOLDOWN_MS })).toBe('cadence')
    s = settle(settle(s, 'timeout', 6), 'error', 7)
    expect(s.mode).toBe('disabled')
    expect(settle(consume(initialState(), 'manual', 0), 'refused', 1).mode).toBe('disabled')
    expect(settle(initialState(), 'no-prompt', 0).mode).toBe('disabled')
    expect(settle(settle(consume(initialState(), 'cadence', 0), 'error', 1), 'ok', 2).consecutiveErrors).toBe(0)
  })

  test('settle advances lastCount monotonically', async () => {
    const s = settle({ ...initialState(), lastCount: 9 }, 'ok', 4)
    expect(s.lastCount).toBe(9)
    expect(settle(s, 'ok', 12).lastCount).toBe(12)
  })

  test('restoreState tolerates garbage and keeps a dead mode', async () => {
    expect(restoreState(undefined)).toEqual(initialState())
    expect(restoreState({ mode: 'nonsense', checks: 'x' }).mode).toBe('idle')
    expect(restoreState({ mode: 'disabled', checks: 4 }).checks).toBe(4)
    expect(restoreState({ mode: 'disabled' }).mode).toBe('disabled')
  })
})
