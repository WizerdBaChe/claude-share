// record.ts — the per-session JSONL record file (FO-INV-3) with the fail-silent buffer (FO-INV-8).
// Append-by-rewrite: the mods fs API has read/write, not append. One live process per session id
// is the contract; a file that grew under us is noted as `contended`, never overwritten.
import type { Io } from './io'

export type Row = Record<string, unknown>

export class Recorder {
  private buffer: string[] = []
  private lastText: string | null = null
  /** Rows that could not be written yet (for the run row's bookkeeping / tests). */
  get pending(): number { return this.buffer.length }

  constructor(private readonly io: Pick<Io, 'exists' | 'read' | 'write'>, public readonly path: string) {}

  async append(rows: readonly Row[]): Promise<boolean> {
    for (const r of rows) {
      try { this.buffer.push(JSON.stringify(r)) } catch { /* unserialisable row: dropped, never thrown */ }
    }
    return this.flush()
  }

  async flush(): Promise<boolean> {
    if (!this.buffer.length) return true
    try {
      let current = ''
      if (await this.io.exists(this.path)) current = await this.io.read(this.path)
      if (this.lastText !== null && current.length > this.lastText.length) {
        this.buffer.unshift(JSON.stringify({ kind: 'note', contended: true, ts: Math.floor(Date.now() / 1000) }))
      }
      const sep = current && !current.endsWith('\n') ? '\n' : ''
      const text = current + sep + this.buffer.join('\n') + '\n'
      await this.io.write(this.path, text)
      this.lastText = text
      this.buffer = []
      return true
    } catch {
      return false                      // keep the buffer; the next append or session.end retries
    }
  }
}

/** The transcript's project folder name for a session root, as the engine spells it
 *  (`C:\Users\you\.claude` -> `C--Users-you--claude`): every non-alphanumeric byte is a dash. */
export function projectDirName(root: string): string {
  return root.replace(/[^A-Za-z0-9]/g, '-')
}
