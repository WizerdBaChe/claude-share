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
- This is a point-in-time snapshot, not a synchronization target.
