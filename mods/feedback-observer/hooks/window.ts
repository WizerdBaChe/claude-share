// window.ts — pure: the transcript window one observer check reads.
// Design: references/feedback-observer-design.md §2.4 (window.ts row).
// No `$` in here, so `claude plugin test` and a plain reader can both run it.

export const WINDOW_CHARS = 40_000
const CLIP = 200

/** The subset of SessionMessage / ToolUseSummary this module reads; every field optional so a
 *  shape change in the engine degrades to "less text", never to a throw. */
export type ToolUseLike = {
  /** `tool` is the engine's field (ToolUseSummary); `name` is accepted for fixtures. */
  tool?: string
  name?: string
  input?: unknown
  text?: string
  result?: unknown
  isError?: boolean
}
export type MessageLike = {
  role?: string
  text?: string
  toolUses?: readonly ToolUseLike[]
}

export type Window = {
  /** What the model reads; '' when nothing new. */
  text: string
  /** Index of the first message in the window (inclusive). */
  fromIndex: number
  /** Index one past the last message (== messages.length). */
  toIndex: number
  /** True when the head of the new span was cut to fit WINDOW_CHARS. */
  truncated: boolean
  /** True when messages.length < lastCount: the list was rewritten (compaction), so the span restarted at 0. */
  reset: boolean
}

export function clip(s: unknown, n = CLIP): string {
  const t = typeof s === 'string' ? s : s === undefined ? '' : safeJson(s)
  const one = t.replace(/\s+/g, ' ').trim()
  return one.length > n ? one.slice(0, n - 1) + '…' : one
}

function safeJson(v: unknown): string {
  try { return JSON.stringify(v) ?? '' } catch { return String(v) }
}

/** One message as the model sees it: a role line, its text, one line per tool use. */
export function renderMessage(m: MessageLike, index: number): string {
  const lines: string[] = [`### ${m.role ?? '?'} #${index}`]
  const text = (m.text ?? '').trim()
  if (text) lines.push(text)
  for (const u of m.toolUses ?? []) {
    const out = u.text ?? (u.result === undefined ? '' : u.result)
    lines.push(`[tool ${u.tool ?? u.name ?? '?'}${u.isError ? ' ERROR' : ''}] ${clip(u.input)} -> ${clip(out)}`)
  }
  return lines.join('\n')
}

/**
 * The window since the previous check. Tail-biased: when the new span is longer than `limit`,
 * whole messages are dropped from the HEAD until it fits (the latest work is what a close-out
 * check must see), and `truncated` says so. A single oversize message is clipped to the limit.
 */
export function buildWindow(messages: readonly MessageLike[], lastCount: number, limit = WINDOW_CHARS): Window {
  const total = messages.length
  const reset = lastCount > total
  const from = reset ? 0 : Math.max(0, lastCount)
  if (from >= total) return { text: '', fromIndex: from, toIndex: total, truncated: false, reset }

  const blocks: string[] = []
  let used = 0
  let truncated = false
  for (let i = total - 1; i >= from; i--) {
    let b = renderMessage(messages[i], i)
    const cost = b.length + (blocks.length ? 2 : 0)
    if (used + cost > limit) {
      if (blocks.length === 0) {               // one message alone exceeds the budget: keep its tail
        b = b.slice(Math.max(0, b.length - limit))
        blocks.push(b)
        used = b.length
      }
      truncated = true
      break
    }
    blocks.push(b)
    used += cost
  }
  blocks.reverse()
  const text = blocks.join('\n\n')
  return { text, fromIndex: from, toIndex: total, truncated, reset }
}
