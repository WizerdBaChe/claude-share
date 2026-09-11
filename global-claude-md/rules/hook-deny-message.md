---
paths:
  - "**/hooks/*.py"
  - "**/hook-deny-lint/**"
---

# Deny-message contract (text a hook sends into a tool result)

Sunk from `hooks/transcript_read_guard.py`'s docstring on 2026-09-07, where it
was written after the 2026-08-29 false positives. It is stated here because it
is a property of THE TEXT, not of that hook: 12 hooks in this environment emit
deny text and only one carried the rule, so 11 inherited nothing. Enforced by
a source-only lint tool (does not ship in this repo). Index line in `CLAUDE.md`.

## The asset property

> Any string a hook puts in `permissionDecisionReason`, a `block` reason, an
> `additionalContext` or a `systemMessage` is read by an agent that cannot
> authenticate its origin. It must therefore be indistinguishable from a
> legitimate constraint report and distinguishable from an injected instruction
> — by SHAPE, since wording alone can never prove origin.

## Two surfaces (2026-09-09, F-8)

The property above is about the TEXT, so it does not care whether the text
arrives attached to a refusal. Two surfaces carry it, and the lint names both:

| surface | keys | what it is |
|---|---|---|
| **block** | `permissionDecisionReason`, a `block` reason | text attached to a refusal |
| **notice** | `additionalContext`, `systemMessage` | text attached to nothing, arriving in the tool result all the same |

Until 2026-09-09 only the first was ruled on, and the notice surface — 12
messages in 8 hooks — inherited nothing. A notice wears the costume MORE
easily, not less: it blocks nothing, so nobody writing one feels they are
refusing anything, and the reader has no refusal to make them suspicious.

**The four prohibitions and R1 bind both surfaces.** The two compensating
requirements do not, and their replacements are R2n and R3n below.

### The third transport, measured and NOT ruled on (F-9)

Bare stdout of a `SessionStart` or `UserPromptSubmit` hook is injected verbatim
into an agent's context; `settings.json` registers 7 such entries
(`ops_health_nudge`, `project_registry_gist`, `worktree_scope_guard`,
`compact_pointer`, `context_runway_shadow`, `unattended_run kickoff`,
`intake_match_shadow`). Their text is composed from file data at runtime, so a
static render is mostly unresolvable and a lint extended to cover them would
report coverage it does not have. It is named here, and in the lint's own
summary line, so the gap is reported rather than implied.

A well-calibrated subagent classifies `falsifiable identity claim + authority
claim + read-elsewhere imperative` as prompt injection. That is a property of
good subagents, not a bug. **The hook must not wear the costume.**

## Prohibited (each is a lint FAIL)

- **P1 authority claim.** No `Policy:`, no `(policy: …)`, no bare rule-id
  prefix (`L-013:`, `INV-2:`, `D-04:`). A rule id is a claim to authority the
  reader cannot check, and it is what a forger writes to borrow one. State the
  constraint itself; the id belongs in the hook's docstring.
- **P2 read-elsewhere imperative.** Never send the reader to a different FILE
  or DIRECTORY to READ (`Detail: ops/lessons.md L-009`, `see references/x.md`,
  `read its .env.example`). See the redirect boundary below.
- **P3 interpolated identity assertion.** Never assert, in copular form, what a
  runtime-interpolated subject IS (`{name} is a credential store`). The agent
  cannot check it, and the claim is about content the hook only pattern-matched.
  Name the constraint that fired instead (`this command references {name}, which
  matches the credential-name pattern this guard gates`).
- **P4 output directive.** Never direct the agent's user-facing output
  (`REPORT THIS TO THE USER in your reply:`, `tell the user that…`). Content
  arriving in a tool result that dictates what to say to the user is the single
  strongest injection tell. State the fact; reporting discipline lives in
  `CLAUDE.md`, which the model reads from a trusted position.

## Required (each is a lint FAIL)

- **R1 self-identification, in the first clause — BOTH surfaces.** Name the hook
  and say it is local: `Read denied by transcript_read_guard (a local PreToolUse
  hook, not page or file content)`. The 2026-08-29 message opened with the
  file's alleged identity and named no actor at all — that, not its wording, is
  what made it read as injected text. This is the one structural difference
  between the known-bad and known-good fixtures.
  Where a helper composes the words and a transport prints them, put the
  identity on the TRANSPORT (`notice()`), not in the composed text: a branch
  added to the annotation later cannot then ship unnamed. Four hooks do this.
  It must name the EMITTING hook, never the module that composed the sentence —
  `compact_bookmark` emitted text opening `[handoff-snapshot]`, a name the
  reader cannot check against any hook.
- **R2 retry mechanics — BLOCK surface.** Say what to do to proceed
  legitimately: the window to use, the marker to re-run with, the tool to use
  instead.
- **R3 false-positive exit — BLOCK surface.** Say how to report that the gate
  misfired, as one concrete executable action that leaves a trace. A gate whose
  only remaining exit is a silent workaround is training agents to route around
  gates — the measured 2026-08-29 outcome (W2 bypassed via `pdftotext`; the
  guard learned nothing). The exit is not an override: it records, it does not
  unblock.

### The notice surface's two requirements (ruling H-1, 2026-09-09)

R2 and R3 are compensations for a call that was BLOCKED. A notice blocks
nothing, so "how to proceed" and "how to get unblocked" have no subject. What
survives the downgrade:

- **R2n actionability.** Say what the reader may DO about it. An explicit
  "nothing needs doing" satisfies it; silence does not. Checked on the
  SITUATION text only — the receipt sentence R3n requires contains three action
  verbs of its own, and while it was in scope R2n passed on every notice that
  carried a receipt and could not be made to fail (probe I-4).
- **R3n receipt.** Name the row this notice left. A notice is a pure claim with
  no refusal to make the reader suspicious, so the row is the only thing about
  it that can be checked sideways: injected text cannot write a local file.
  Two accepted forms — `deny_receipt.clause()` (quotes a unique nonce) and
  `deny_receipt.notice_clause()` (names the row the hook already wrote, so one
  event does not write two rows and inflate the misfire denominator). The
  second is weaker by exactly one thing and says so: it pins the class of row,
  not this call. `report_fp.py --rate` counts denies and notices separately for
  that reason.

The misfire EXIT is deliberately not required on a notice: nothing is blocked,
so the reader has no need of one at that moment, and ~300 characters on every
annotation is a standing tax. Notice misfires are still reported with the same
tool, and `--rate` now prints the notice denominator that makes such a report
divisible.

## The redirect boundary (P2's edge — get this right or the lint is noise)

| shape | verdict |
|---|---|
| redirect to a different TOOL for the same target (`use Grep`, `Write file content with the Write tool`, `use SendUserFile`, `run probe.py --id <c>`) | **fine** — it is the retry mechanic R2 requires |
| name a path as a WRITE/RUN target, or as a receipt (`the full command was saved to telemetry/x.jsonl`) | **fine** — a receipt is sideways-verifiable and is the only origin evidence the reader can actually check |
| send the reader to READ a different file for the reasoning (`Detail: …md`, `see …README.md`) | **the costume** — this is what an injector needs the reader to do |

The distinguishing verb is the point: `run`, `use`, `write` are redirects;
`read`, `see`, `refer to`, and a bare `Detail:` pointer are the prohibition.

## FALSE-POSITIVE LOG convention

Observed misfires are counted in the owning hook's own docstring under a
`FALSE-POSITIVE LOG:` heading — date, count, what was wrongly gated, the fix,
and explicitly whether the trigger condition was loosened. The count in that
docstring is the loosening trigger; a hook with no log has never been measured,
which is not the same as never having misfired.

## review-when

- A new hook gains a deny or notice site, or a hook gains its first one → it
  inherits nothing automatically; the lint enumerates hooks, so add it there.
- The lint's own failure text changes → it is itself text that reaches an
  agent and must conform to this file.
- A message is rewritten → re-run that hook's regression suite unchanged.
  Rewriting TEXT must never alter a CONDITION. (2026-09-09: none of the seven
  suites asserts message text, so they pass a text rewrite without checking it
  — the lint and a dated probe run under the source's `outputs/` tree (does
  not ship here) are what check the words.)
- **A THIRD agent-facing text surface appears** — a new hook-output key, or a
  new event whose stdout the harness injects → it is unruled until this file
  names it and the lint's summary counts it. F-9 above is the standing example.
- The harness changes what it does with `additionalContext` or `systemMessage`
  (e.g. one stops reaching the model) → the notice surface's requirements were
  written for a reader that cannot authenticate them; a surface that reaches a
  human instead needs a different ruling, not this one.
