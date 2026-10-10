// io.ts — the slice of the engine interface the observer uses, as plain closures.
// The validator holds `$` to its call sites (`$.noun.method(...)`), so `$` is never passed,
// stored or bound; the session.start hook builds this object inline from its own `$` and the
// rest of the module works through it. Every member mirrors one `$` call, nothing more.
import type { MessageLike } from './window'

export type CompleteRequest = {
  model: string
  effort: string
  system: string
  prompt: string
  maxTokens: number
  timeoutMs: number
}

export type Io = {
  exists(path: string): Promise<boolean>
  read(path: string): Promise<string>
  write(path: string, text: string): Promise<void>
  list(path: string): Promise<{ name: string }[]>
  now(): Promise<number>
  after(ms: number, fn: () => void): void
  log(text: string, debug?: boolean): void
  storeGet(key: string): Promise<unknown>
  storeSet(key: string, value: unknown): Promise<void>
  messages(): Promise<MessageLike[]>
  complete(req: CompleteRequest): Promise<any>
  sessionId(): Promise<string>
  sessionRoot(): Promise<string>
  /** The attached surfaces now; empty in a plain -p run. An SDK host (Desktop) attaches after session.start. */
  surfaces(): Promise<readonly string[]>
  /** `$.env.get` takes literal names only (validator), so the two reads are named here. */
  configDir(): Promise<string | undefined>
  userHome(): Promise<string | undefined>
  pluginRoot(): string
  registerCommand(name: string, description: string): Promise<unknown>
}
