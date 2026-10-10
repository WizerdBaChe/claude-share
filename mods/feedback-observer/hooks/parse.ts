// parse.ts — pure: the model's reply → validated findings.
// Design: references/feedback-observer-design.md §2.4 (parse.ts row), FO-INV-6.

export const KINDS = ['bypass', 'misfire', 'missed-rule', 'workaround', 'stale-doc'] as const
export type Kind = (typeof KINDS)[number]
export const CONFIDENCES = ['low', 'med', 'high'] as const
export type Confidence = (typeof CONFIDENCES)[number]
/** feedback-pool's closed target vocabulary (INV-9); the observer never widens it. */
export const TARGET_PREFIXES = ['hook:', 'skill:', 'tool:', 'rule:', 'subsystem:', 'lesson:', 'project:'] as const
export const EVIDENCE_CHARS = 200
export const RAW_KEEP = 2000

export type Finding = {
  target: string
  target_status: 'ok' | 'undetermined'
  symptom: string
  kind: Kind
  evidence: string
  confidence: Confidence
}

export type Parsed = {
  outcome: 'ok' | 'undetermined'
  findings: Finding[]
  /** Items rejected: not an object, bad kind, evidence missing from the window, duplicate. */
  dropped: number
  /** Findings kept with target_status 'undetermined' (prefix outside the vocabulary). */
  undetermined: number
  /** The reply, clipped, when it was not a JSON array (outcome undetermined). */
  raw?: string
}

/** The first JSON array in the text: fenced or bare, whole-reply or embedded. */
export function extractArray(text: string): unknown[] | null {
  const t = (text ?? '').trim()
  const candidates: string[] = []
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/i)
  if (fence) candidates.push(fence[1].trim())
  candidates.push(t)
  const a = t.indexOf('[')
  const b = t.lastIndexOf(']')
  if (a >= 0 && b > a) candidates.push(t.slice(a, b + 1))
  for (const c of candidates) {
    try {
      const v = JSON.parse(c)
      if (Array.isArray(v)) return v
    } catch { /* next candidate */ }
  }
  return null
}

function str(v: unknown): string | null {
  return typeof v === 'string' && v.trim() ? v.trim() : null
}

function normConfidence(v: unknown): Confidence | null {
  const s = str(v)?.toLowerCase()
  if (s === 'medium' || s === 'mid') return 'med'
  return (CONFIDENCES as readonly string[]).includes(s ?? '') ? (s as Confidence) : null
}

export function parseReply(text: string, windowText: string): Parsed {
  const arr = extractArray(text)
  if (!arr) return { outcome: 'undetermined', findings: [], dropped: 0, undetermined: 0, raw: (text ?? '').slice(0, RAW_KEEP) }
  const findings: Finding[] = []
  const seen = new Set<string>()
  let dropped = 0
  let undetermined = 0
  for (const item of arr) {
    if (!item || typeof item !== 'object' || Array.isArray(item)) { dropped++; continue }
    const o = item as Record<string, unknown>
    const target = str(o.target)
    const symptom = str(o.symptom)
    const kind = str(o.kind)?.toLowerCase() as Kind | undefined
    const evidence = str(o.evidence)
    const confidence = normConfidence(o.confidence) ?? 'low'
    if (!target || !symptom || !kind || !evidence) { dropped++; continue }
    if (!(KINDS as readonly string[]).includes(kind)) { dropped++; continue }
    if (evidence.length > EVIDENCE_CHARS || !windowText.includes(evidence)) { dropped++; continue }
    const key = target + '\u0000' + evidence
    if (seen.has(key)) { dropped++; continue }
    seen.add(key)
    const ok = TARGET_PREFIXES.some(p => target.startsWith(p))
    if (!ok) undetermined++
    findings.push({
      target,
      target_status: ok ? 'ok' : 'undetermined',
      symptom: symptom.slice(0, 300),
      kind,
      evidence,
      confidence,
    })
  }
  return { outcome: 'ok', findings, dropped, undetermined }
}
