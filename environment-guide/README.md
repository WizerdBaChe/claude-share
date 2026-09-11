# environment-guide

Human-facing documentation for how one personal `~/.claude` configuration
environment is organized, why it's organized that way, and how to migrate
it to a new machine or platform.

## Contents

| File | Purpose |
|---|---|
| `PHILOSOPHY.md` | Non-normative worldview behind the ruleset: the beliefs each rule traces back to, the system map, and the core-asset tiering used when deciding what must survive a migration. |
| `OPERATOR-GUIDE.md` | Practical operator manual — permission modes, the three questions the model will ask a new operator, environment conventions, an asset map, and a step-by-step migration checklist (Claude Code → Claude Code). |
| `COMMIT-TEMPLATES.md` | Conventional-Commits templates and type/scope conventions derived from this environment's actual commit history. |

These three documents cross-reference the operational rule layer and skill
set described in `claude-ops/` and `skill-toolkit/` in this same repo —
they were written to be read together, so those references are retained
rather than stripped.

## Snapshot details

- Source: `~/.claude/PHILOSOPHY.md`, `~/.claude/OPERATOR-GUIDE.md`,
  `~/.claude/COMMIT-TEMPLATES.md`, copied 2026-07-31.
- Review scope: usernames, local paths, account or machine identifiers.
- Result: one username in a project-memory path example (`OPERATOR-GUIDE.md`)
  and one username in a Python interpreter path example (`PHILOSOPHY.md`)
  were replaced with generic `<user>` placeholders. No other identifiers
  found.
- 2026-09-12 refresh (align to source `7c9867b`): `PHILOSOPHY.md` gained an
  entirely new belief section ("機制要能被擴充而不靜默失效") and a second
  Tier-2 bullet, plus a re-added annotation pointing an ASCII-diagram node and
  a §五 closing-paragraph mention at this repo's `Global_skill_update.md`.
  Two source-only tool/path citations inside the new material were
  generalized (a per-lesson-card path under the source's own record tree; a
  source-only session-archiving tool) rather than shipped literally. No
  identifiers found beyond the pattern already covered above.
- This is a point-in-time snapshot, not a synchronization target.
