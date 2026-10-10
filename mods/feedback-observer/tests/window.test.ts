import { test, expect, describe } from 'claude-code/testing'
import { buildWindow, renderMessage, clip, WINDOW_CHARS } from '../hooks/window'

const msg = (i: number, len = 50) => ({ role: i % 2 ? 'assistant' : 'user', text: `m${i} ` + 'x'.repeat(len) })

describe('window', () => {
  test('nothing new → empty text and the same indices', async () => {
    const w = buildWindow([msg(0), msg(1)], 2)
    expect(w.text).toBe('')
    expect(w.fromIndex).toBe(2)
    expect(w.toIndex).toBe(2)
    expect(w.truncated).toBe(false)
    expect(w.reset).toBe(false)
  })

  test('window starts at lastCount and ends at length', async () => {
    const ms = [msg(0), msg(1), msg(2), msg(3)]
    const w = buildWindow(ms, 2)
    expect(w.fromIndex).toBe(2)
    expect(w.toIndex).toBe(4)
    expect(w.text).toContain('m2 ')
    expect(w.text).toContain('m3 ')
    expect(w.text).not.toContain('m1 ')
  })

  test('a shrunken list (compaction) resets to 0 and says so', async () => {
    const w = buildWindow([msg(0), msg(1)], 10)
    expect(w.reset).toBe(true)
    expect(w.fromIndex).toBe(0)
    expect(w.toIndex).toBe(2)
  })

  test('tail-biased trim never exceeds the limit and keeps the newest messages', async () => {
    // Property over a size grid (rung 1 — exhaustive over the grid, no Hypothesis in TS here).
    for (const count of [1, 2, 5, 13, 40]) {
      for (const len of [10, 300, 2_000, 9_000]) {
        for (const limit of [500, 4_000, WINDOW_CHARS]) {
          const ms = Array.from({ length: count }, (_, i) => msg(i, len))
          const w = buildWindow(ms, 0, limit)
          expect(w.text.length).toBeLessThanOrEqual(limit)
          const full = ms.map((m, i) => renderMessage(m, i)).join('\n\n')
          expect(w.truncated).toBe(full.length > limit)
          if (full.length <= limit) expect(w.text).toBe(full)
          // whole-message trim keeps the NEWEST message whenever it fits on its own
          else if (renderMessage(ms[count - 1], count - 1).length <= limit) expect(w.text).toContain(`m${count - 1} `)
          else expect(w.text.endsWith('x')).toBe(true)      // single oversize message: its tail
        }
      }
    }
  })

  test('a single oversize message is clipped to its tail and flagged truncated', async () => {
    const w = buildWindow([{ role: 'assistant', text: 'A'.repeat(100) + 'TAIL' }], 0, 50)
    expect(w.text.length).toBe(50)
    expect(w.text.endsWith('TAIL')).toBe(true)
    expect(w.truncated).toBe(true)
  })

  test('tool uses render as one line each with clipped input and output', async () => {
    const line = renderMessage({
      role: 'assistant', text: 'doing',
      toolUses: [{ name: 'Bash', input: { command: 'rm -rf build && ' + 'y'.repeat(500) }, text: 'ok ' + 'z'.repeat(500), isError: true }],
    }, 7)
    expect(line.startsWith('### assistant #7\ndoing\n[tool Bash ERROR] ')).toBe(true)
    const toolLine = line.split('\n')[2]
    expect(toolLine.length).toBeLessThanOrEqual('[tool Bash ERROR] '.length + 200 + ' -> '.length + 200)
    expect(clip('a  b\n c', 10)).toBe('a b c')
  })
})
