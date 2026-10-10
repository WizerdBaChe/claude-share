import { test, expect, describe } from 'claude-code/testing'

// FO-INV-9 presence, rung 0 (scenarios). Regression for 2026-10-02: the Desktop engine runs as an
// SDK host (stream-json), so session.start arrives with isInteractive false and surface null and the
// desktop surface attaches afterwards; the old start-time predicate left every Desktop session inert
// and /fo-calibrate unregistered. Activation is observed through $.store.get, which only start() calls.

type Stubs = { surfaces: string[]; storeGets: number; registered: string[]; files?: { name: string }[]; hangModel?: boolean }

function stub(on: any, s: Stubs): void {
  const v = (value: unknown) => ({ value })
  on('session.start', (_$: any, e: any) => ({ cwd: e.cwd }))
  on('session.attach', (_$: any, e: any) => ({ clientId: e.clientId }))
  on('command.run', () => ({}))
  on('session.surfaces', () => v(s.surfaces))
  on('session.id', () => v('feedcafe-test-session'))
  on('session.root', () => v('C:/nowhere'))
  on('session.messages', () => v([]))
  on('command.register', (_$: any, e: any) => { s.registered.push(e.name); return v({ command: e.name }) })
  on('store.get', () => { s.storeGets += 1; return v(undefined) })
  on('store.set', () => v(undefined))
  on('env.get', () => v(undefined))
  on('fs.exists', () => v(false))
  on('fs.read', () => v('prompt'))
  on('fs.write', () => v(undefined))
  on('fs.list', () => v(s.files ?? []))
  on('model.complete', () => s.hangModel ? new Promise(() => { /* never answers */ }) : v({ isAnswered: true, text: '[]' }))
  on('clock.now', () => v(0))
  on('clock.after', () => v(undefined))
  on('ui.log', () => v(undefined))
}

describe('presence', () => {
  test('SDK host: no activation at session.start, activation when the desktop surface attaches', async ($: any, on: any) => {
    const s: Stubs = { surfaces: [], storeGets: 0, registered: [] }
    stub(on, s)
    await $.session.start({ cwd: 'C:/nowhere', surface: null, isInteractive: false })
    expect(s.registered).toContain('fo-calibrate')
    expect(s.storeGets).toBe(0)
    s.surfaces = ['desktop']
    await $.session.attach({ surface: 'desktop', clientId: 'desktop:default' })
    expect(s.storeGets).toBe(1)
  })

  test('REPL: activation at session.start', async ($: any, on: any) => {
    const s: Stubs = { surfaces: ['terminal'], storeGets: 0, registered: [] }
    stub(on, s)
    await $.session.start({ cwd: 'C:/nowhere', surface: 'terminal', isInteractive: true })
    expect(s.storeGets).toBe(1)
  })

  test('/fo-calibrate returns at once while the model call never answers (P-9: the session waits on command.run)', async ($: any, on: any) => {
    const s: Stubs = { surfaces: ['terminal'], storeGets: 0, registered: [], files: [{ name: 'a.window.txt' }], hangModel: true }
    stub(on, s)
    await $.session.start({ cwd: 'C:/nowhere', surface: 'terminal', isInteractive: true })
    const t0 = Date.now()
    await $.command.run({ command: 'fo-calibrate' })
    expect(Date.now() - t0 < 1000).toBe(true)
  })

  test('-p run: no surface ever attaches, so a prompt and /fo-calibrate leave it inert', async ($: any, on: any) => {
    const s: Stubs = { surfaces: [], storeGets: 0, registered: [] }
    stub(on, s)
    await $.session.start({ cwd: 'C:/nowhere', surface: null, isInteractive: false })
    await $.command.run({ command: 'fo-calibrate' })
    expect(s.storeGets).toBe(0)
  })
})
