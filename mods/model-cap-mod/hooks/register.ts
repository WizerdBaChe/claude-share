// model-cap — in-process subagent model cost cap. STATUS: LIVE, it denies and refuses.
// Why a mod and not only the Python hook: a command hook that times out is a PASS (2026-10-02,
// one SHARE round: two dispatches escaped onto claude-fable-5-1 at 5.4 s / 6.5 s hook latency).
// Two hooks, both fail closed:
//   agent.spawn — awaited by the engine; denies an explicit opus/fable `model` and a fork of an
//     opus/fable parent (forks ignore `model`). An omitted `model` is deferred: the engine has not
//     resolved it yet at this event.
//   turn.step  — in a subagent's loop, sees the model the ENGINE resolved (any definition source,
//     else the parent's) before the request is sent; above the cap and unapproved, it answers
//     without `next`, so no request goes out and the subagent ends with the refusal as its answer.
//     Also covers what spawn cannot: SendMessage resume onto the main model, a fallback model.
//     (Live probe 2026-10-09, CC 2.1.294: resume kept the definition/call pin, so that path has not fired.)
// Ruling 2026-10-09 (user): judge the resolved model, never re-derive agent resolution from files.
// Policy: ./policy.ts (one reading, shared with hooks/model_cap_guard.py).
import type { Register } from 'claude-code'
import { APPROVAL_MARKER, approvedIn, decide, decideEffort, decideStep, denyText, effortNoticeText, faultDenyText, noticeText, refusalText, withHeartbeat } from './policy'

const TELEMETRY = 'telemetry/model-cap-mod.jsonl'
const HEARTBEAT = 'telemetry/model-cap-mod-alive.json'
const KEEP_LINES = 5000
const PENDING_WAIT_MS = 2000

function homeOf(root: string): string {
  const r = root.replace(/\\/g, '/')
  const m = r.match(/^(.*)\/mods\/model-cap-mod$/)
  return m?.[1] ?? r.replace(/\/[^/]+\/?$/, '')
}

/** Append one row to the telemetry file (read + rewrite, bounded). Fail-silent: a lost row never blocks a spawn. */
async function record($: any, home: string, row: Record<string, unknown>): Promise<void> {
  const path = `${home}/${TELEMETRY}`
  try {
    let lines: string[] = []
    if (await $.fs.exists(path)) lines = String(await $.fs.read(path)).split('\n').filter(Boolean)
    lines.push(JSON.stringify({ ts: Math.floor(Date.now() / 1000), ...row }))
    if (lines.length > KEEP_LINES) lines = lines.slice(lines.length - KEEP_LINES)
    await $.fs.write(path, lines.join('\n') + '\n')
  } catch { /* nothing */ }
}

const nonce = () => Math.random().toString(16).slice(2, 8)

// Module state; a reload starts it over (the engine's agent list and the transcript still answer).
const approvedPrompts = new Set<string>()        // prompts spawned WITH the marker, so a fork's approval survives into its steps
const spawned = new Set<string>()                // agentIds this mod saw spawned
const pending = new Set<Promise<void>>()         // spawns whose next(e) has not settled: a first step can arrive before it does
const judged = new Map<string, 'pass' | 'refused' | 'noticed'>()   // per agentId|model: judge once per model, so a resume or fallback onto another model is judged again
const judgedEffort = new Set<string>()           // per agentId|effort: the effort axis is a notice, said once per agent and level

function refusalSteps(e: any, text: string) {
  return (async function* () {
    yield { kind: 'text', index: 0, text } as any
    yield { kind: 'stop', stopReason: 'end_turn', usage: null } as any
    return { turnId: e.turnId, index: e.index, answer: text, toolUses: [], stopReason: 'end_turn', usage: null } as any
  })()
}

export const register: Register = (on) => {
  // Heartbeat: the Python PreToolUse guard defers an unresolved omitted `model` to this mod only
  // for a session listed here — no listing, no deferral (the Python deny stands).
  on('session.start', async ($, e, next) => {
    try {
      const home = homeOf(String($.plugin.root ?? ''))
      const path = `${home}/${HEARTBEAT}`
      let map: Record<string, number> = {}
      try { if (await $.fs.exists(path)) map = JSON.parse(String(await $.fs.read(path))) } catch { map = {} }
      await $.fs.write(path, JSON.stringify(withHeartbeat(map, String(await $.session.id()), Math.floor(Date.now() / 1000))) + '\n')
    } catch { /* a lost heartbeat only means the Python guard keeps denying */ }
    return next(e)
  })

  on('agent.spawn', async ($, e, next) => {
    const ev = e as any
    const home = homeOf(String($.plugin.root ?? ''))
    const sid = String(await $.session.id())
    const facts = {
      model: typeof ev.model === 'string' && ev.model ? ev.model : undefined,
      prompt: String(ev.prompt ?? ''),
      subagentType: String(ev.subagentType ?? ''),
      fork: Boolean(ev.fork) || ev.subagentType === 'fork',
      parentModel: String(ev.parentModel ?? ''),
    }
    const v = decide(facts)
    if (v.action === 'deny') {
      const n = nonce()
      await record($, home, { kind: 'deny', nonce: n, detail: v.detail, model: v.model, route: v.route, subagentType: facts.subagentType, parentModel: facts.parentModel, fork: facts.fork, session: sid })
      $.ui.log(`model-cap: denied ${facts.subagentType || 'agent'} (${v.detail}: ${v.model})`)
      return { deny: denyText(v, n) }
    }
    if (v.action === 'notice') {
      await record($, home, { kind: 'notice', detail: v.detail, model: v.model, route: v.route, subagentType: facts.subagentType, parentModel: facts.parentModel, session: sid })
      $.ui.log(noticeText(v))
    }
    if (v.detail === 'approved') approvedPrompts.add(facts.prompt)
    let settle!: () => void
    const p = new Promise<void>(res => { settle = res })
    pending.add(p)
    try {
      const r = await next(e)
      const id = (r as any)?.agentId
      if (id) spawned.add(String(id))
      await record($, home, { kind: 'spawn', detail: v.detail, requested: facts.model ?? null, resolved: (r as any)?.model ?? null, agentId: id ?? null, denied: Boolean((r as any)?.deny), subagentType: facts.subagentType, parentModel: facts.parentModel, fork: facts.fork, session: sid })
      return r
    } finally {
      pending.delete(p)
      settle()
    }
  }).catch(async ($, e, next) => {
    // A hook that throws or overruns is skipped, and the spawn would run judged only by the
    // Python guard (timeout = pass). Fail closed — unless the spawn already started (next.called),
    // where denying is impossible; its first turn.step still judges the resolved model.
    if (next.called) return next(e)
    if (String((e as any).prompt ?? '').includes(APPROVAL_MARKER)) return next(e)
    return { deny: faultDenyText(String((next as any).error?.message ?? (next as any).error ?? '')) }
  })

  on('turn.step', async function* ($, e, next) {
    const id = e.agentId
    if (!id) return yield* next(e)                         // the main loop is not capped
    // Effort axis (2026-10-10): notice only, see decideEffort. Judged before the model cache, which skips cached steps.
    const effortLevel = typeof e.effort === 'string' ? e.effort.toLowerCase() : ''
    if (effortLevel && !judgedEffort.has(`${id}|${effortLevel}`) && decideEffort({ effort: effortLevel, isAgent: true, approved: false }).action === 'notice') {
      judgedEffort.add(`${id}|${effortLevel}`)
      const einfo: any = (await $.agent.list()).find((a: any) => a.id === id)
      const eIsAgent = Boolean(einfo) || spawned.has(id)
      const erows = eIsAgent ? await $.session.messages({ agentId: id }) : []
      const eApproved = Array.isArray(erows) && approvedIn(erows as any, approvedPrompts, einfo?.type === 'fork')
      const ev = decideEffort({ effort: effortLevel, isAgent: eIsAgent, approved: eApproved })
      if (ev.action === 'notice') {
        const n = nonce()
        await record($, homeOf(String($.plugin.root ?? '')), { kind: 'notice', nonce: n, detail: ev.detail, effort: ev.effort, model: e.model, agentId: id, subagentType: einfo?.type ?? null, session: String(await $.session.id()) })
        $.ui.log(effortNoticeText(ev.effort, String(einfo?.type ?? ''), n))
      }
    }
    const key = `${id}|${e.model}`
    const prior = judged.get(key)
    if (prior === 'pass' || prior === 'noticed') return yield* next(e)
    const home = homeOf(String($.plugin.root ?? ''))
    // Is this loop an agent (spawned or listed), or an engine-internal fork (compaction, memory),
    // which carries an id no list names? A first step can precede its spawn's settle (probe
    // 2026-10-09: step at +0 ms, spawn settled at +26 ms), so wait for in-flight spawns first.
    let info: any = (await $.agent.list()).find((a: any) => a.id === id)
    if (!info && !spawned.has(id) && pending.size) {
      await Promise.race([Promise.all([...pending]), $.clock.sleep(PENDING_WAIT_MS, { signal: next.signal }).catch(() => undefined)])
      info = (await $.agent.list()).find((a: any) => a.id === id)
    }
    const isAgent = Boolean(info) || spawned.has(id)
    let approved = false
    const tierProbe = decideStep({ model: e.model, isAgent, approved: false })
    if (tierProbe.action === 'refuse') {
      const rows = await $.session.messages({ agentId: id })
      approved = Array.isArray(rows) && approvedIn(rows as any, approvedPrompts, info?.type === 'fork')
    }
    const v = decideStep({ model: e.model, isAgent, approved })
    const sid = String(await $.session.id())
    if (v.action === 'refuse') {
      const n = nonce()
      judged.set(key, 'refused')
      await record($, home, { kind: 'refuse', nonce: n, detail: v.detail, model: v.model, agentId: id, subagentType: info?.type ?? null, step: e.index, session: sid })
      $.ui.log(`model-cap: refused ${info?.type || 'subagent'} ${id} (resolved ${v.model})`)
      return yield* refusalSteps(e, refusalText(v.model, String(info?.type ?? ''), n))
    }
    if (v.action === 'notice') {
      judged.set(key, 'noticed')
      await record($, home, { kind: 'notice', detail: v.detail, model: v.model, route: 'the resolved model', agentId: id, session: sid })
      $.ui.log(noticeText({ model: v.model, route: 'the model the engine resolved for this subagent' }))
    } else {
      judged.set(key, 'pass')
      if (v.detail !== 'within-cap') await record($, home, { kind: 'step', detail: v.detail, model: e.model, agentId: id, session: sid })
    }
    return yield* next(e)
  }).catch(async function* ($, e, next) {
    // A failed step hook would be absent and the request would go out unjudged: fail closed for a
    // subagent's loop that resolved above the cap, unless the step already went out (next.called).
    if (next.called || !e.agentId) return yield* next(e)
    let isAgent = spawned.has(e.agentId)
    if (!isAgent) {
      // an engine-internal loop (compaction) must not be refused; when even the list fails, a spawn in flight counts as an agent
      try { isAgent = (await $.agent.list()).some((a: any) => a.id === e.agentId) } catch { isAgent = pending.size > 0 }
    }
    if (decideStep({ model: e.model, isAgent, approved: false }).action !== 'refuse') return yield* next(e)
    return yield* refusalSteps(e, faultDenyText(String((next as any).error?.message ?? (next as any).error ?? '')))
  })
}
