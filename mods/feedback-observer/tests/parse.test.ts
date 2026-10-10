import { test, expect, describe } from 'claude-code/testing'
import { parseReply, extractArray } from '../hooks/parse'

const WINDOW = '### assistant #3\nI will re-route the body through a file.\n[tool Bash] cat > x.sh <<EOF -> denied by dangerous_command_guard'
const good = {
  target: 'hook:dangerous_command_guard', symptom: 'heredoc text misread as a delete', kind: 'misfire',
  evidence: 'denied by dangerous_command_guard', confidence: 'high',
}

describe('parse', () => {
  test('a valid array yields findings and counts', async () => {
    const p = parseReply(JSON.stringify([good]), WINDOW)
    expect(p.outcome).toBe('ok')
    expect(p.findings.length).toBe(1)
    expect(p.findings[0].target_status).toBe('ok')
    expect(p.dropped).toBe(0)
    expect(p.undetermined).toBe(0)
  })

  test('[] and a fenced [] are ok with zero findings', async () => {
    expect(parseReply('[]', WINDOW).findings.length).toBe(0)
    const p = parseReply('```json\n[]\n```', WINDOW)
    expect(p.outcome).toBe('ok')
    expect(p.findings.length).toBe(0)
  })

  test('prose and truncated JSON are undetermined and keep the raw text', async () => {
    const prose = parseReply('I found nothing of note in this window.', WINDOW)
    expect(prose.outcome).toBe('undetermined')
    expect(prose.raw).toContain('nothing of note')
    const cut = parseReply('[{"target": "hook:x", "symptom": "s", "kind": "bypass", "evi', WINDOW)
    expect(cut.outcome).toBe('undetermined')
    expect(cut.findings.length).toBe(0)
  })

  test('an unknown prefix is kept as undetermined and counted', async () => {
    const p = parseReply(JSON.stringify([{ ...good, target: 'agent:code-reviewer' }]), WINDOW)
    expect(p.findings.length).toBe(1)
    expect(p.findings[0].target_status).toBe('undetermined')
    expect(p.undetermined).toBe(1)
  })

  test('fabricated evidence is dropped and counted, not kept', async () => {
    const p = parseReply(JSON.stringify([{ ...good, evidence: 'this sentence is not in the window' }]), WINDOW)
    expect(p.findings.length).toBe(0)
    expect(p.dropped).toBe(1)
  })

  test('bad kind, missing fields, non-objects and duplicates are dropped; confidence is normalised', async () => {
    const p = parseReply(JSON.stringify([
      { ...good, kind: 'smell' },
      { target: 'hook:x', kind: 'bypass' },
      'not an object',
      { ...good, confidence: 'medium' },
      { ...good, confidence: 'medium' },
    ]), WINDOW)
    expect(p.findings.length).toBe(1)
    expect(p.findings[0].confidence).toBe('med')
    expect(p.dropped).toBe(4)
  })

  test('extractArray finds an embedded array in prose', async () => {
    expect(extractArray('Here: [1, 2] done')).toEqual([1, 2])
    expect(extractArray('{"a": 1}')).toBe(null)
  })
})
