# Evolution Protocol — how the harness improves itself, safely

Governs proposing and applying changes to GUARDRAIL files (settings.json,
hooks/, permissions) and other harness machinery. Complements
`40-maintenance.md` (which governs editing the rule TEXT); this file governs
changing what the machine ENFORCES.

## §1 Invariants

1. **Proposals, not edits**: an agent never edits guardrail files on its own
   initiative. It writes a proposal; the human applies it — or grants explicit,
   named authorization for a specific change set, in which case the agent still
   backs up first, applies exactly the reviewed artifacts, verifies, and logs.
2. **Every proposal argues benefit > risk, or it isn't made.** Required fields
   (§2). A change that can't name its failure pattern is change for change's
   sake — global CLAUDE.md already forbids that.
3. **Staged rollout when possible**: test on one project/session before wider
   use; name the regression signal that would trigger rollback.
4. **No duplicate mechanisms**: before proposing new machinery, check what
   already exists (audit trail, backups/, drafts/, memory system, skills,
   scheduled tasks). Extending an existing mechanism beats adding a parallel one.

✅ "PreToolUse hook X misfires in unrelated repos — proposal: gate it on
project id; risk: gate too narrow, hook silent where wanted; rollback signal:
reminder absent in a registered project."
❌ Silently adding a second changelog file because the first one's format felt
inconvenient — now two histories drift.

## §2 Proposal format and location

Location: `~/.claude/drafts/<YYYY-MM-DD>-<name>/` containing `APPLY.md` plus
ready-to-apply artifacts. `APPLY.md` states, per change:

- **Problem**: which observed failure pattern or gap this fixes (cite evidence).
- **Change**: exact file/rule/hook/skill added or modified (artifact included).
- **Benefit**: what improves (reliability, cost, speed, clarity).
- **Risks**: what might get worse; known residual gaps stated honestly.
- **Rollout & verification**: how to apply, how to test, what regression looks
  like, how to roll back (backup path).

Lifecycle: applied → log in the audit trail (`Global_skill_update.md`) + git
commit; rejected/superseded → one-line note in the audit trail, artifacts stay
in drafts/ as record.

## §3 Instruction memory vs auto-memory (route knowledge to the right store)

- **Instruction memory** (human-governed rules): global/project `CLAUDE.md`,
  `ops/`, `skills/` — changes follow `40-maintenance.md` tiers.
- **Auto-memory** (agent-updated knowledge): the harness memory directory
  (`MEMORY.md` index + one-fact-per-file), plus `ops/lessons.md` for
  operational pitfalls.
- Project knowledge (API quirks, environment facts, patterns that worked) goes
  to auto-memory or the project's Environment-facts block — NOT into CLAUDE.md
  or ops/ unless the user asks or a lesson recurs enough to harden into a rule
  (`40-maintenance.md` §4.4).

✅ "This API rate-limits at burst" → memory fact file, indexed in MEMORY.md.
❌ Appending the same discovery as a new rule paragraph in global CLAUDE.md —
rules bloat with facts that belong in memory.

## §4 Degraded environments

When the current environment lacks a mechanism these rules assume (no subagent
tool, no scheduler, single-agent harness): keep the INVARIANT, negotiate the
mechanism — separation of duties survives even when the roles run in one agent
(see `20-dispatch.md` §1a). State the deviation explicitly in your reasoning
and, if recurring, log it in `ops/lessons.md`.
