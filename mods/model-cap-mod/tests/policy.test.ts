import { test, expect, describe } from 'claude-code/testing'
import { APPROVAL_MARKER, approvedIn, decide, decideEffort, decideStep, denyText, effortNoticeText, faultDenyText, noticeText, refusalText, tierOf, withHeartbeat } from '../hooks/policy'

const base = { prompt: 'do the thing', subagentType: 'general-purpose', fork: false, parentModel: 'claude-fable-5-1' }
const step = { model: 'claude-fable-5-1', isAgent: true, approved: false }

describe('model-cap policy (mirror of tools/model-cap-test classes)', () => {
  test('tier: family name or full id, both directions; unknown is unrecognised, never folded', async () => {
    expect(tierOf('opus')).toBe('blocked')
    expect(tierOf('claude-fable-5-1')).toBe('blocked')
    expect(tierOf('sonnet')).toBe('within-cap')
    expect(tierOf('claude-haiku-4-5-20251001')).toBe('within-cap')
    expect(tierOf('gpt-5.6-luna')).toBe('unrecognised')
    expect(tierOf(undefined)).toBe('unrecognised')
  })

  test('spawn must-deny: explicit opus/fable, fork of a fable parent (model ignored for forks)', async () => {
    expect(decide({ ...base, model: 'opus' }).action).toBe('deny')
    expect(decide({ ...base, model: 'claude-fable-5-1' })).toEqual({ action: 'deny', detail: 'blocked', model: 'claude-fable-5-1', route: 'its `model` argument' })
    expect((decide({ ...base, fork: true, model: 'sonnet' }) as any).detail).toBe('fork-inherits-blocked')
  })

  test('spawn must-pass: sonnet/haiku, the approval marker, a fork of a sonnet parent', async () => {
    expect(decide({ ...base, model: 'sonnet' })).toEqual({ action: 'pass', detail: 'within-cap' })
    expect(decide({ ...base, model: 'haiku' }).action).toBe('pass')
    expect(decide({ ...base, model: 'opus', prompt: `urgent ${APPROVAL_MARKER} go` })).toEqual({ action: 'pass', detail: 'approved' })
    expect(decide({ ...base, fork: true, parentModel: 'claude-sonnet-5-5' })).toEqual({ action: 'pass', detail: 'fork-within-cap' })
  })

  test('spawn: an omitted model is DEFERRED to the step judge, never denied on a definition lookup (ruling 2026-10-09)', async () => {
    // the r22 false-deny class: whatever the parent or the definition, spawn does not guess
    expect(decide({ ...base })).toEqual({ action: 'pass', detail: 'deferred' })
    expect(decide({ ...base, subagentType: 'section-worker' })).toEqual({ action: 'pass', detail: 'deferred' })
  })

  test('step must-refuse: an agent resolved to opus/fable without approval — the 2026-10-02 escape shape', async () => {
    expect(decideStep(step)).toEqual({ action: 'refuse', detail: 'resolved-blocked', model: 'claude-fable-5-1' })
    expect(decideStep({ ...step, model: 'claude-opus-5-5' }).action).toBe('refuse')
  })

  test('step must-pass: within cap (a pinned haiku worker), approved, an engine-internal loop on the main model', async () => {
    expect(decideStep({ ...step, model: 'claude-haiku-5-5' })).toEqual({ action: 'pass', detail: 'within-cap' })
    expect(decideStep({ ...step, approved: true })).toEqual({ action: 'pass', detail: 'approved' })
    expect(decideStep({ ...step, isAgent: false })).toEqual({ action: 'pass', detail: 'engine-loop' })
  })

  test('step must-notice: an unrecognised resolved model on an agent', async () => {
    expect(decideStep({ ...step, model: 'mystery-9' }).action).toBe('notice')
    expect(decideStep({ ...step, model: 'mystery-9', isAgent: false }).action).toBe('pass')
  })

  test('approval at step: own first prompt (non-fork), a spawn-seen approved prompt (fork too); a fork quoting the marker is not approval', async () => {
    const own = [{ role: 'user', text: `task ${APPROVAL_MARKER}` }, { role: 'assistant', text: 'ok' }]
    expect(approvedIn(own, [], false)).toBe(true)
    expect(approvedIn(own, [], true)).toBe(false)
    const forkRows = [{ role: 'user', text: 'parent talk' }, { role: 'user', text: 'fork directive P' }]
    expect(approvedIn(forkRows, ['fork directive P'], true)).toBe(true)
    expect(approvedIn(forkRows, ['other'], true)).toBe(false)
    expect(approvedIn([{ role: 'user', text: 'plain' }, { role: 'user', text: APPROVAL_MARKER }], [], false)).toBe(false)
    expect(approvedIn([], [''], false)).toBe(false)
  })

  test('deny/refusal text: identity first, retry, no-silent-swap clause, misfire exit, receipt; no pointer or rule id', async () => {
    const texts = [
      denyText(decide({ ...base, model: 'opus' }) as any, 'abc123'),
      denyText(decide({ ...base, fork: true }) as any, 'abc123'),
      refusalText('claude-fable-5-1', 'section-worker', 'abc123'),
    ]
    for (const t of texts) {
      expect(/^(Dispatch denied|Subagent refused) by model-cap, a local Claude Code mod/.test(t)).toBe(true)
      expect(t).toContain(APPROVAL_MARKER)
      expect(t).toContain('do NOT swap it')
      expect(t).toContain('report_fp.py --hook model-cap')
      expect(t).toContain('row abc123 to telemetry/model-cap-mod.jsonl')
      expect(/\b(see|read|refer to) [^ ]+\.md/i.test(t)).toBe(false)
      expect(/\b(L|D|INV)-\d+/.test(t)).toBe(false)
      expect(/Policy:/.test(t)).toBe(false)
    }
    expect(texts[2]).toContain("'claude-fable-5-1'")
    expect(texts[2]).toContain('was not sent')
    // the refusal must not push a blind swap: it names pinning as the route, never "re-dispatch with model: 'sonnet' (default)"
    expect(texts[2]).not.toContain("re-dispatch with model: 'sonnet' (default)")
    const f = faultDenyText('TypeError: boom')
    expect(f.startsWith('Dispatch denied by model-cap, a local Claude Code mod')).toBe(true)
    expect(f).toContain('TypeError: boom')
    expect(f).toContain('report_fp.py --hook model-cap')
    const n = noticeText({ model: 'gpt-5.6-luna', route: 'its `model` argument' })
    expect(n.startsWith('model-cap, a local Claude Code mod')).toBe(true)
    expect(n).toContain('going through unjudged')
  })

  test('heartbeat map: adds the session, keeps the newest N', async () => {
    expect(withHeartbeat({}, 's1', 10)).toEqual({ s1: 10 })
    const m = withHeartbeat({ a: 1, b: 2, c: 3 }, 'd', 4, 2)
    expect(Object.keys(m).sort()).toEqual(['c', 'd'])
  })
  test('effort axis (2026-10-10): xhigh/max on an unapproved subagent is a NOTICE; high, approval, engine loops pass', async () => {
    const f = { isAgent: true, approved: false }
    expect(decideEffort({ ...f, effort: 'max' })).toEqual({ action: 'notice', detail: 'effort-over-cap', effort: 'max' })
    expect(decideEffort({ ...f, effort: 'XHigh' }).action).toBe('notice')
    expect(decideEffort({ ...f, effort: 'high' })).toEqual({ action: 'pass', detail: 'within-cap' })
    expect(decideEffort({ ...f, effort: undefined }).action).toBe('pass')
    expect(decideEffort({ ...f, effort: 5 }).action).toBe('pass')
    expect(decideEffort({ effort: 'max', isAgent: true, approved: true })).toEqual({ action: 'pass', detail: 'approved' })
    expect(decideEffort({ effort: 'max', isAgent: false, approved: false })).toEqual({ action: 'pass', detail: 'engine-loop' })
    const n = effortNoticeText('max', 'general-purpose', 'abc123')
    expect(n.startsWith('model-cap, a local Claude Code mod')).toBe(true)
    expect(n).toContain('abc123')
    expect(n).not.toMatch(/tell the user|Policy:|see [\w./-]+\.md/i)
  })
})
