# Harness measurements behind `environment.md` (owner: `environment.md`)

Detail file for `ops/environment.md`. The FACTS (what is charged at session
start, what `is_error` means, how auto-mode scoping works) stay in
`environment.md` with their `as-of` lines; this file holds the measurements,
probes and incidents those facts rest on, so the facts file stays a facts file.
Re-measure rather than trust when the `as-of` of the owning block is older than
the Claude Code build in use. Loaded on demand.

## Instruction-loading mechanics (as-of 2026-08-18, Claude Code 2.1.233)

Measured, not read off the docs — the docs describe path-scoping and user-level
rules separately and never state that the two compose. The carrier table itself
is in `environment.md`; how each row was verified:

| Carrier | Verified how |
|---|---|
| `~/.claude/CLAUDE.md` charged at session start, in full | hook log, `load_reason: session_start` |
| `@path` imports inside it charged at launch | official docs only ("imported files still load at launch") |
| `~/.claude/rules/<name>.md` **without** `paths:` charged at start | probe `_probe-always.md`, 2 runs |
| `~/.claude/rules/<name>.md` **with** `paths:` NOT charged at start | same 2 runs — absent from startup |
| …the same file loaded when a matching file is read | probe `_probe-match.md`, `load_reason: path_glob_match`, content observed in context |
| skill loaded only when invoked/judged relevant | official docs |

**Observability**: `hooks/instructions_loaded_logger.py` (InstructionsLoaded,
logging only, fail-open) appends to `telemetry/rule-loads.jsonl`. Payload
fields: `file_path`, `memory_type`, `load_reason`. Startup-cost baseline:
`tools/context-budget/startup_baseline.py`.

`load_reason` values observed so far: `session_start`, `path_glob_match`, and
**`compact`** — CLAUDE.md is re-injected after every `/compact`, so its byte
cost is paid per compaction as well as per session. Blind spot: only CLAUDE.md
has ever emitted this event. `MEMORY.md` is injected (it appears in context)
but never appears in the log, so the logger cannot be used to prove a memory
file did or did not load.

**Trim effect sizes are below the measurement noise floor.** The E1 trim
removed 1,286 B net (~320 tokens at 4 chars/token) from a startup prompt whose
observed per-session spread in this project is 57.3k–70.4k tokens. A ~0.5%
signal cannot be recovered from a ~13k-token range no matter how many sessions
are collected, so "the MIN floor drops after the change" is not a usable
acceptance test. Judge context-budget work by adherence evidence
(`rule-loads.jsonl` shows the rule firing when it should) and by the on-disk
inventory, not by a token delta.

**Baseline for `C--Users-<user>--claude`** (24 sessions since 2026-07-25):
startup prompt MIN 36,742 / MEDIAN 58,891 tokens; always-loaded instruction
files 17,139 B. CLAUDE.md is therefore ~11% of the floor (estimate) — the
dominant startup cost is the tool/MCP/skill roster, not the rules.

## Bash tool results carry no exit code (measured 2026-08-11)

A successful Bash `toolUseResult` is a dict of `interrupted / isImage /
noOutputExpected / stderr / stdout`; on failure it degenerates to a plain string
beginning `"Exit code N"` and the result block is flagged `is_error: true`. So
`is_error` is exactly "the shell reported non-zero" — no divergence exists to
find between them. The gap that matters is upstream: `cmd || true` and
`cmd | head` both exit 0 while the command inside failed, and both were observed
reporting `is_error: false` with `FAILED` sitting in stdout. Any gate keying on
`is_error` must also sniff stdout, or downgrade piped / `||`-guarded
verifications to "weak" rather than counting them as verified. (The PowerShell
twin of `| head` — `| Select-Object -First N` — additionally KILLS the upstream:
`lessons.md` L-027, `hooks/ps_pipeline_close_guard.py`.)

## Auto-mode environment scoping — the evidence (as-of 2026-08-16)

The fact in `environment.md`: `settings.json` `autoMode.environment` is applied
UNCONDITIONALLY in every project. How it was established:

- The classifier reads user + managed + `--settings` scopes only and
  DELIBERATELY ignores project `.claude/settings.json` / `settings.local.json`
  (anti-injection: a repo must not be able to set its own classifier rules), so
  there is no per-project filter, re-derivation, or supported per-project
  carrier. Scopes CONCATENATE (personal entries extend managed ones, never remove
  them).
- The setup flow writes to userSettings (docs silent; verified in the binary:
  setup/reset both target `"userSettings"`, and projectSettings/localSettings
  autoMode is ignored with a logged warning). The block is "spliced into the
  classifier prompt on every auto-mode decision" (verbatim binary string; an
  over-size warning says "consider pruning stale entries").
- Incident: an NTUMail2TG session wrote a project profile there 2026-08-16; the
  user removed it the same day.
- Evidence: code.claude.com/docs/en/auto-mode-config (externally verified) +
  `claude.exe` string probe (locally verified, minified source — behaviour-level
  claims only).

## Red-team / reviewer separation — the corrected entry (as-of 2026-08-16)

The previous `environment.md` entry (2026-07-07) said "no independent second
CLI agent from a different model family is available… do not spend time looking
for one". That was true when written and false after the external dispatch tier
landed; it is recorded here rather than merely deleted because it is the shape
of stale fact that does not read as stale — a session would have obeyed it and
never looked. Measured 2026-08-16 on a real commit: the external tier produced 3
anchored findings in 110 s, two overlapping a sonnet control's seven and one the
control missed in both of its runs (a reproduced `TypeError`).

## Dispatch semantics — two load surfaces this layer had never recorded (reconciled 2026-09-06, 2.1.257)

Found by re-reading `code.claude.com/docs/en/sub-agents` §"What loads at
startup" during the 2.1.246 → 2.1.257 reconcile. The four load-bearing claims
that `rule-registry.md` §subagent instruction surface rests on were all
unchanged; the LIST had grown. Neither of these is used by any definition in
`agents/` today, and both are recorded because they are levers, not defaults.

**`skills:` preloading.** An agent definition may name skills in a `skills:`
frontmatter field; the FULL text of each named skill is placed in the worker's
initial context. This aims directly at the cost problem that registry entry
measures — the standing problem that a rule living in a skill reaches a worker
only if the worker thinks to invoke it. The price is paid on EVERY dispatch of
that agent, in full, whether or not the skill turns out to be relevant, so the
move is: measure one dispatch with and without before writing it into a
definition. Built-in agents do not preload skills at all.

**Sibling roster.** When a worker's `tools:` include `SendMessage` AND at least
one other agent in the session has a name, the harness injects a system
reminder listing `main` and every other named agent as valid `to` values
(v2.1.206+). Two consequences: worker-to-worker messaging is gated on the
`tools:` allowlist, like every other capability (§capability is set in the
definition); and the roster is a SNAPSHOT taken when that worker starts, so an
agent named later never appears in it — if two workers must talk, name them and
start them in the right order rather than expecting discovery.

Two further items from the same list change no rule here yet, recorded so the
next reconcile does not re-derive them: `includeGitInstructions` (settings) can
remove the git-status snapshot from a subagent's context, and `subagent_type:
"fork"` inherits the parent conversation instead of starting fresh.

## Dispatch semantics — what changed under us between 2.1.200 and 2.1.246 (reconciled 2026-08-26)

`environment.md` §Dispatch mechanisms carried an `as-of` of 2026-08-12 and was
overtaken four separate times before anyone looked. Citations are `## <version>`
headings in `~/.claude/cache/changelog.md`, with that file's line number:

| Change | Version | cache line |
|---|---|---|
| Subagent forking on by default; `subagent_type: "fork"` inherits full conversation + prompt cache; non-teammate spawns in interactive sessions default to BACKGROUND | 2.1.232 | L187 |
| Cross-session `SendMessage` + `ListAgents` added (macOS/Linux first) | 2.1.224 | L334 |
| Skills with `context: fork` default to background (`background: false` opts out) | 2.1.218 | L514 |
| Concurrent-subagent cap, default 20 (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) | 2.1.217 | L537 |
| Per-session spawn cap, default 200 (`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`) | 2.1.212 | L643 |
| `/fork` becomes a background-session copy; the old in-session subagent is now `/subtask` | 2.1.212 | L640 |
| SessionStart hooks report source `"fork"` (not `"resume"`) when a session begins as a fork | 2.1.214 | L636 |
| `DirectoryAdded` hook event added, fires after `/add-dir` | 2.1.219 | L456 |
| **Windows: cross-session messaging available** | 2.1.239 | upstream CHANGELOG |

Two of these invert an earlier written rule rather than extend it: the model
precedence line (`call param > frontmatter > inherit`) is FALSE for
`subagent_type: "fork"`, which ignores `model` outright; and fan-out planning
that assumed no ceiling now has two.

The instrument note matters more than any single row. `claude update` refreshes
NEITHER `cache/changelog.md` (unchanged at 535,333 bytes / mtime 8/21 / top
entry 2.1.238 across a 2.1.239→2.1.246 upgrade) NOR
`.last-update-result.json` (still recording the previous 2.1.238→2.1.239 run).
Any check that reads a version from either file is reading a stale number that
looks live. `claude --version` is the only source. `tools/cc-delta/` is built on
that finding.

Full reconciliation, including the seven entries verified as still-true and the
five registered for probing: a dated CC-version reconciliation report under
the source's `reports/` tree, which this repo does not ship.

### What the Workflow tool offers when enabled

Extracted from `environment.md` §Dispatch mechanisms 2026-08-27 — it describes a
tool that `"disableWorkflows": true` currently removes from this environment, so
it is inert detail until that key is flipped. Deterministic fan-out; per-`agent()`
call supports `model`, `effort` (low/medium/high/xhigh/max), `schema`
(machine-enforced output-format contract — prefer this over prompt-side format
pleading), `isolation: 'worktree'`, `agentType`.

## Execution surface — the measurements (measured 2026-08-22, CLI 2.1.238 / Desktop-bundled claude.exe 2.1.237)

Extracted from `environment.md` "Execution surface" 2026-08-27 under
`40-maintenance.md` §3 (the file was 2.0K over the 22K review trigger; the
routing, the standing rules and the re-verify conditions stayed in the owner).
**Every number here was measured eight CLI builds before 2.1.246 and is
unre-verified** — the owner block says so too, and the re-probe is registered
as E10 in that same reconciliation report (source-only). Quote a
number from here only with that caveat attached; quote none of them as current.

Bench tree `_bench-claude-arms` (under the source's work root), n=4/arm, exact MW; full write-ups in
that tree's `ANALYSIS_CHANNEL_MECHANISM_2026-08-22.md` and
`ANALYSIS_CHANNEL_CONFOUNDS_2026-08-22.md`.

**Pending probes that would move these numbers** (tracked here rather than in
the owner block, which lists only environment-facing re-verify conditions): the
Desktop-side `disableWorkflows` probe, and the Desktop × `bypassPermissions`
rerun — E2-Desktop / E3 in the CONFOUNDS doc. When either lands, update this
section and move the owner block's `as-of`.

- Desktop = 1.336× CLI fresh tokens, 1.722× cost (p=0.0286). T0 ≈49.0k (CLI)
  vs ≈67.7k (Desktop); with T0 subtracted the conversation is still 1.37×
  larger (p=0.0286); request count NOT separated (p=0.20). Desktop-side knob
  ceiling ≈6–7% of total cost; the 1.37× growth has no verified knob.
- Confound in that comparison: CLI arm `bypassPermissions`, Desktop arm
  auto/default (auto injects the "route file ops through Bash" instruction +
  classifier). **E3 cell C2B (Desktop × Opus/high × bypassPermissions), n=4
  (2026-08-22, `results/C2B-02/03/05/06`, $35.31; C2B-04 excluded — prompt
  pasted from a rendered view, formatting lost)**: permission mode explains
  about HALF of the Desktop premium, not most of it — fresh tokens 1.336× =
  1.139× (channel, mode aligned) × 1.172× (permission mode, channel fixed);
  cost 1.722× = 1.265× × 1.361×; conversation growth C2B 125.7k vs CLI 112.0k
  vs Desktop-auto 154.1k (runs 118.6k/131.6k/106.8k/145.9k — 2 in the CLI band,
  1 in the gap, 1 in the Desktop band). Neither factor is separated at n=4
  (p 0.0571–0.3429) → descriptive; the n=1 "mostly permission mode" reading did
  NOT fully replicate. Aligning the mode also shrank the Desktop arm's spread
  (cost CV 35.8% → 14.7%). The other half is the host itself (T0 prefix +38%
  plus ~1.12× conversation growth). Detail: CONFOUNDS §6.2, PAPER §7.2.1.
- Remote connectors are deferred-loaded: Notion (28 tools) on/off moved T0 by
  ≤8 tokens — which is why the owner block says not to trim connectors for cost.
- `"disableWorkflows": true` (settings.json; official, every surface) drops the
  Workflow tool definition: CLI T0 49,053 → 41,156 (−7,897, −16%) and Desktop
  T0 65,961 → 58,061 (−7,900; same-day A/B probes, Opus/high/bypass, 2.1.237),
  both 2026-08-22. `--disallowedTools Agent,Workflow` drops 10,953 → Agent
  ≈3.1k (CLI-only flag). Worth ≈2.5–3% of a Desktop task's cost.
- Session-record paths in full: `~/.claude/projects/<slug>/<cliSessionId>.jsonl`
  (both surfaces); Desktop's sidebar index is
  `%APPDATA%\Claude\claude-code-sessions\<acct>\<org>\local_<id>.json`
  (metadata only; `cliSessionId` → JSONL). A CLI session shown in
  Desktop/claude.ai via Remote Control is a server-side mirror (retained under
  Anthropic's data policy, not on disk here); its live view ends with the CLI
  process. Desktop transcript view: Summary / Normal / Verbose (`Ctrl+O`);
  Verbose ≙ `--verbose`.
