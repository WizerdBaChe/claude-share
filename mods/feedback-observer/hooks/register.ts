// feedback-observer — observe-only mod. Design: references/feedback-observer-design.md
// (FO-INV-1..9, §2.3 state machine). STATUS: SHADOW (sensor S-8 lists, never counts).
//
// Every event hook here returns next(e) with e untouched (FO-INV-1). The only
// user-visible output is $.ui.log (FO-INV-2). The only writes are the per-session
// record file and $.store (FO-INV-3). The only model is sonnet/medium (FO-INV-4).
// `$` is used only in the hooks below; the module works through the Io closures the
// session.start hook builds (the validator holds `$` to its call sites).
import type { Register } from 'claude-code'
import type { Io } from './io'
import { buildWindow, type Window } from './window'
import { parseReply, type Finding } from './parse'
import {
  CLOSEOUT_RE, MAX_CHECKS, consume, decide, initialState, isSubsystemWrite, restoreState, settle,
  type Outcome, type State, type Trigger,
} from './gate'
import { Recorder, projectDirName } from './record'

export const MODEL = 'sonnet'
export const EFFORT = 'medium'
export const MAX_TOKENS = 2000
export const TIMEOUT_MS = 120_000
const UNATTENDED_TAG = '[unattended-run]'
const STORE_PREFIX = 'feedback-observer:'

type Ctx = {
  io: Io
  sid: string
  storeKey: string
  state: State
  prompt: string
  rec: Recorder
  inFlight: boolean
  pending: Trigger | null
  toolCalls: number
  touched: boolean
  checkNo: number
}

// Module-level: a hot reload starts it over; $.store carries the state across (host-owned).
let ctx: Ctx | null = null
// session.start saw no surface: an SDK host (the Desktop app) attaches its surface afterwards,
// a plain -p run never does. Held until session.attach or a prompt finds a surface (FO-INV-9).
let pendingIo: Io | null = null

const sec = (ms: number) => Math.floor(ms / 1000)

async function homeDir(io: Io): Promise<string> {
  const root = io.pluginRoot().replace(/\\/g, '/')
  const m = root.match(/^(.*)\/mods\/feedback-observer$/)
  if (m) return m[1]
  const cfg = await io.configDir()
  if (cfg) return String(cfg).replace(/\\/g, '/').replace(/\/$/, '')
  const up = (await io.userHome()) || ''
  return String(up).replace(/\\/g, '/').replace(/\/$/, '') + '/.claude'
}

async function recordPath(io: Io, home: string, sid: string): Promise<{ path: string; location: 'projects' | 'fallback' }> {
  try {
    const root = (await io.sessionRoot()).replace(/\\/g, '/')
    const dir = `${home}/projects/${projectDirName(root)}`
    if (await io.exists(dir)) return { path: `${dir}/${sid}.observer.jsonl`, location: 'projects' }
  } catch { /* fall through */ }
  return { path: `${home}/telemetry/feedback-observer/${sid}.jsonl`, location: 'fallback' }
}

async function persist(): Promise<void> {
  if (!ctx) return
  try { await ctx.io.storeSet(ctx.storeKey, ctx.state) } catch { /* FO-INV-8 */ }
}

function userPrompt(windowText: string): string {
  return '## Transcript window (main agent, oldest first)\n\n' + windowText +
    '\n\n## Reply\nA JSON array only (see the system prompt). `[]` when there is no subsystem defect.'
}

/**
 * Activation body, run once a surface is known to be attached (the caller decides presence).
 * Returns without setting ctx when the session is one the observer must not run in (FO-INV-9).
 */
async function start(io: Io): Promise<void> {
  const sid = await io.sessionId()
  const home = await homeDir(io)
  try {                                                                         // a live unattended run → inert
    const mp = `${home}/cache/handoff/${sid}.run.json`
    if (await io.exists(mp)) {
      const m = JSON.parse(await io.read(mp))
      if (m && !m.ended) return
    }
  } catch { /* unreadable manifest: not evidence of a run */ }
  const storeKey = STORE_PREFIX + sid
  const state = restoreState(await io.storeGet(storeKey))
  if (state.mode === 'inert') return
  const { path, location } = await recordPath(io, home, sid)
  const rec = new Recorder(io, path)
  let prompt = ''
  try { prompt = await io.read(`${io.pluginRoot()}/prompt.md`) } catch { prompt = '' }
  ctx = { io, sid, storeKey, state, prompt, rec, inFlight: false, pending: null, toolCalls: 0, touched: false, checkNo: state.checks }
  if (!prompt.trim()) {
    ctx.state = settle(ctx.state, 'no-prompt', ctx.state.lastCount)
    await rec.append([{ kind: 'run', ts: sec(await io.now()), session: sid, trigger: 'start', outcome: 'no-prompt', location, model: MODEL, effort: EFFORT }])
    await persist()
  }
  if (location === 'fallback') io.log(`feedback-observer: project dir not found, recording to ${path}`, true)
}

/** Activates a session that waited for its surface; false while none is attached (still headless). */
async function activatePending(): Promise<boolean> {
  const io = pendingIo
  if (!io || ctx) return !!ctx
  let attached = false
  try { attached = (await io.surfaces()).length > 0 } catch { attached = false }
  if (!attached) return false
  pendingIo = null
  await start(io)
  return !!ctx
}

function schedule(trigger: Trigger): void {
  if (!ctx) return
  if (ctx.inFlight) {
    ctx.pending = ctx.pending === 'forced' ? 'forced' : trigger
    return
  }
  const c = ctx
  c.io.after(0, () => { void runCheck(c, trigger) })
}

function complete(io: Io, system: string, windowText: string) {
  return io.complete({ model: MODEL, effort: EFFORT, system, prompt: userPrompt(windowText), maxTokens: MAX_TOKENS, timeoutMs: TIMEOUT_MS })
}

function findingRow(c: Ctx, f: Finding, i: number, ts: number, trigger: Trigger, windowRange: number[]) {
  return {
    kind: 'finding', id: `${c.sid.slice(0, 8)}-${c.checkNo}-${i + 1}`, ts, session: c.sid, check: c.checkNo, trigger,
    window: windowRange, target: f.target, target_status: f.target_status, symptom: f.symptom,
    finding_kind: f.kind, evidence: f.evidence, confidence: f.confidence,
  }
}

async function runCheck(c: Ctx, trigger: Trigger): Promise<void> {
  if (ctx !== c || c.inFlight || c.state.mode !== 'idle') return
  const io = c.io
  let win: Window
  try {
    win = buildWindow(await io.messages(), c.state.lastCount)
  } catch { return }
  if (!win.text) {
    if (trigger === 'manual') io.log('feedback-observer: nothing new since the last check')
    return                                                                      // no slot spent, no row
  }
  c.inFlight = true
  const t0 = await io.now()
  let outcome: Outcome = 'error'
  let usage: unknown
  let raw: string | undefined
  let findings: Finding[] = []
  let dropped = 0
  let undetermined = 0
  try {
    c.state = consume(c.state, trigger, t0)
    c.checkNo += 1
    let r: any = null
    try { r = await complete(io, c.prompt, win.text) } catch (err) { outcome = 'refused'; raw = String(err).slice(0, 300) }
    if (r) {
      usage = r.usage
      if (r.isAnswered) {
        const p = parseReply(String(r.text ?? ''), win.text)
        outcome = p.outcome; findings = p.findings; dropped = p.dropped; undetermined = p.undetermined; raw = p.raw
      } else {
        outcome = r.reason === 'aborted' ? 'timeout' : 'error'
        raw = [r.reason, r.status, r.error].filter(x => x !== undefined && x !== null).join(' ')
      }
    }
  } catch (err) {
    outcome = 'error'
    raw = String(err).slice(0, 300)
  } finally {
    try {
      const before = c.state.mode
      c.state = settle(c.state, outcome, win.toIndex)
      const ts = sec(await io.now())
      const windowRange = [win.fromIndex, win.toIndex]
      const rows: Record<string, unknown>[] = [{
        kind: 'run', ts, session: c.sid, check: c.checkNo, trigger, window: windowRange,
        chars: win.text.length, truncated: win.truncated, reset: win.reset,
        outcome, n: findings.length, dropped, undetermined, usage, model: MODEL, effort: EFFORT,
        ms: (await io.now()) - t0, ...(raw ? { raw } : {}),
      }]
      findings.forEach((f, i) => rows.push(findingRow(c, f, i, ts, trigger, windowRange)))
      if (c.state.mode === 'disabled' && before !== 'disabled' && (outcome === 'timeout' || outcome === 'error')) {
        rows.push({ kind: 'run', ts, session: c.sid, check: c.checkNo, trigger, outcome: 'backoff-disabled' })
      }
      if (c.state.mode === 'exhausted' && before !== 'exhausted') {
        rows.push({ kind: 'run', ts, session: c.sid, check: c.checkNo, trigger, outcome: 'cap-reached' })
      }
      await c.rec.append(rows)
      await persist()
      if (findings.length > 0) io.log(`feedback-observer: ${findings.length} finding(s) recorded`)
    } catch { /* FO-INV-8 */ }
    c.inFlight = false
    const p = c.pending
    c.pending = null
    if (p && c.state.mode === 'idle') io.after(0, () => { void runCheck(c, p) })
  }
}

async function onMainTurn(c: Ctx, aborted: boolean): Promise<void> {
  c.state.mainTurns += 1
  const facts = { toolCalls: c.toolCalls, touchedSubsystem: c.touched, aborted, now: await c.io.now() }
  c.toolCalls = 0
  c.touched = false
  const trig = decide(c.state, facts)
  if (trig) schedule(trig)
  else await persist()
}

async function calibrate(c: Ctx): Promise<string> {
  const io = c.io
  const dir = `${io.pluginRoot()}/calibration`
  let entries: { name: string }[] = []
  try { entries = await io.list(dir) } catch { return `feedback-observer: no calibration dir at ${dir}` }
  const cases = entries.map(x => x.name).filter(n => n.endsWith('.window.txt')).sort()
  const out: Record<string, unknown>[] = []
  let pass = 0
  for (const file of cases) {
    const name = file.replace(/\.window\.txt$/, '')
    let windowText = ''
    let expect: Record<string, unknown> = {}
    try { windowText = await io.read(`${dir}/${file}`) } catch { continue }
    try { expect = JSON.parse(await io.read(`${dir}/${name}.expect.json`)) } catch { expect = {} }
    const t0 = await io.now()
    let r: any = null
    let rejected: string | undefined
    try { r = await complete(io, c.prompt, windowText) } catch (err) { rejected = String(err).slice(0, 300) }
    const parsed = r?.isAnswered ? parseReply(String(r.text ?? ''), windowText) : null
    const targets = parsed ? parsed.findings.map(f => f.target) : []
    const wantTarget = typeof expect.expect_target === 'string' ? (expect.expect_target as string) : null
    const wantEmpty = expect.expect_empty === true
    const ok = parsed !== null && (wantEmpty ? parsed.findings.length === 0 : wantTarget ? targets.includes(wantTarget) : true)
    if (ok) pass += 1
    out.push({
      name, expect, pass: ok, ms: (await io.now()) - t0, rejected,
      reply_raw: r ? (r.isAnswered ? r.text : r) : null,
      outcome: parsed?.outcome ?? (rejected ? 'refused' : 'error'),
      findings: parsed?.findings ?? [], dropped: parsed?.dropped ?? 0, undetermined: parsed?.undetermined ?? 0,
      asserted: wantEmpty ? { count: parsed?.findings.length ?? null } : { target_found: wantTarget ? targets.includes(wantTarget) : null, targets },
      usage: r?.usage,
    })
  }
  const report = { at: new Date().toISOString(), model: MODEL, effort: EFFORT, session: c.sid, cases: out, pass, total: cases.length }
  try { await io.write(`${dir}/calibration_run.json`, JSON.stringify(report, null, 1)) } catch { /* FO-INV-8 */ }
  return `feedback-observer: calibration ${pass}/${cases.length} passed -> ${dir}/calibration_run.json`
}

let calibrating = false

async function runCalibration(c: Ctx): Promise<void> {
  let line = ''
  try { line = await calibrate(c) } catch (err) { line = `feedback-observer: calibration failed (${String(err).slice(0, 160)})` }
  finally { calibrating = false }
  try { c.io.log(line) } catch { /* FO-INV-8 */ }
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    ctx = null
    pendingIo = null
    const io: Io = {
      exists: (p) => $.fs.exists(p),
      read: async (p) => String(await $.fs.read(p)),
      write: (p, t) => $.fs.write(p, t),
      list: async (p) => (await $.fs.list(p)) as { name: string }[],
      now: () => $.clock.now(),
      after: (ms, fn) => { $.clock.after(ms, fn) },
      log: (t, debug) => { if (debug) $.ui.log(t, { to: 'debug' }); else $.ui.log(t) },
      storeGet: (k) => $.store.get(k),
      storeSet: (k, v) => $.store.set(k, v),
      messages: async () => (await $.session.messages()) as any[],
      complete: (r) => $.model.complete(r as any),
      sessionId: () => $.session.id(),
      sessionRoot: () => $.session.root(),
      surfaces: () => $.session.surfaces(),
      configDir: async () => (await $.env.get('CLAUDE_CONFIG_DIR')) as string | undefined,
      userHome: async () => ((await $.env.get('USERPROFILE')) || (await $.env.get('HOME'))) as string | undefined,
      pluginRoot: () => String($.plugin.root ?? ''),
      registerCommand: (name, description) => $.command.register({ name, description }),
    }
    try {
      // Registered before presence is known, so a first-message /fo-calibrate in a Desktop
      // session resolves; each handler activates or reports inert itself.
      await io.registerCommand('observe', 'feedback-observer: run one side check on the recent window now (shadow)')
      await io.registerCommand('fo-calibrate', 'feedback-observer: run the prompt over the calibration fixtures and write calibration_run.json')
      const ev = e as any
      // A REPL has its surface now; an SDK host (the Desktop app) attaches it after this event
      // (2026-10-02: Desktop engine 2.1.286 runs stream-json, isInteractive false, surface null).
      if (ev.isInteractive && ev.surface) await start(io)
      else pendingIo = io
    } catch (err) {
      ctx = null
      try { $.ui.log(`feedback-observer: start failed, inert (${String(err).slice(0, 120)})`, { to: 'debug' }) } catch { /* nothing */ }
    }
    return next(e)
  })

  on('session.attach', async ($, e, next) => {
    try { await activatePending() } catch (err) {
      ctx = null
      try { $.ui.log(`feedback-observer: start failed, inert (${String(err).slice(0, 120)})`, { to: 'debug' }) } catch { /* nothing */ }
    }
    return next(e)
  })

  on('tool.call', ($, e, next) => {
    const ev = e as any
    if (ctx && ctx.state.mode === 'idle' && !ev.agentId) {
      ctx.toolCalls += 1
      if (isSubsystemWrite(String(ev.tool), ev.file_path ?? ev.notebook_path)) ctx.touched = true
    }
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const ev = e as any
    if (ctx && !ev.agentId) {
      try { await onMainTurn(ctx, ev.reason === 'aborted') } catch { /* FO-INV-8 */ }
    }
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    const ev = e as any
    if (!ctx && pendingIo) {
      try { await activatePending() } catch { /* FO-INV-8 */ }
    }
    if (ctx) {
      try {
        if (String(ev.text ?? '').includes(UNATTENDED_TAG)) {
          ctx.state.mode = 'inert'
          await persist()
        } else if (ev.origin?.kind === 'composer' && ctx.state.mode === 'idle' && CLOSEOUT_RE.test(String(ev.text ?? ''))) {
          ctx.state.closeoutPending = true
          await persist()
        }
      } catch { /* FO-INV-8 */ }
    }
    return next(e)
  })

  on('session.end', async ($, e, next) => {
    if (ctx) {
      try {
        if (ctx.inFlight) {
          await ctx.rec.append([{ kind: 'run', ts: sec(await ctx.io.now()), session: ctx.sid, check: ctx.checkNo, trigger: 'end', outcome: 'lost' }])
        } else {
          await ctx.rec.flush()
        }
      } catch { /* FO-INV-8 */ }
    }
    return next(e)
  })

  on('command.run', { command: 'observe' }, async ($) => {
    try { await activatePending() } catch { /* FO-INV-8 */ }
    if (!ctx) { $.ui.log('feedback-observer: not active in this session (inert)'); return {} }
    if (ctx.state.mode !== 'idle') { $.ui.log(`feedback-observer: ${ctx.state.mode} (${ctx.state.checks}/${MAX_CHECKS} checks used)`); return {} }
    schedule('manual')
    return {}
  })

  // The handler returns at once and the calibration runs detached: the session waits on a
  // command.run hook, so awaiting two model calls here froze a Desktop session (2026-10-02, P-9).
  on('command.run', { command: 'fo-calibrate' }, async ($) => {
    try { await activatePending() } catch { /* FO-INV-8 */ }
    if (!ctx) { $.ui.log('feedback-observer: not active in this session (inert)'); return {} }
    if (calibrating) { $.ui.log('feedback-observer: a calibration is already running'); return {} }
    const c = ctx
    calibrating = true
    c.io.after(0, () => { void runCalibration(c) })
    $.ui.log('feedback-observer: calibration started in the background; the result line follows')
    return {}
  })
}

/** Test seams: the module's live context (null when inert). */
export function _ctx(): Ctx | null { return ctx }
export function _reset(): void { ctx = null; pendingIo = null; calibrating = false }
export { initialState }
