# CLAUDE_SHARE

Public-facing extracts from a personal `~/.claude` configuration environment,
shared piecemeal. Each subfolder is one self-contained share; content is
reviewed for local machine identifiers (usernames, absolute paths, emails)
before being copied here.

Licensed under [MIT](LICENSE).

## Shares

| Folder | Contents |
|---|---|
| `interop-layer/` | Cross-agent sync layer: compiles a portable rules subset into global instruction files for opencode / codex / Antigravity. See `interop-layer/README.md`. |
| `skill-toolkit/` | Portable AI-agent skills and bilingual trigger dictionary, reviewed for personal identifiers and local paths. See `skill-toolkit/README.md`. |
| `claude-ops/` | Anonymized snapshot of operational guidance for a Claude Code environment. See `claude-ops/README.md`. |
| `thinking-notes/` | Numbered design-thinking notes on one-shot delivery, debugging epistemology, delegation economics, and related topics. See `thinking-notes/README.md`. |
| `environment-guide/` | Human-facing philosophy, operator manual, and commit-message conventions for the source `~/.claude` environment, including a full migration checklist. See `environment-guide/README.md`. |
| `global-claude-md/` | The top-level global `CLAUDE.md` entry point itself — conditional working preferences for Git workflow, environment/shell syntax, interaction style, engineering judgement, frontend layering (FSD), skill routing, project-operations tiering, file hygiene, and reply language. See `global-claude-md/README.md`. |

## Where things are

| If you want | Read |
|---|---|
| A one-line map of every file here | `AGENTS.md` |
| How the source environment evolved, rule by rule | `Global_skill_update.md` |
| When each share was copied and what changed | `CHANGELOG.md` |
| The rules layer itself | `claude-ops/ops/` (start at `OPS.md`) |
| The global preferences file these rules hang off | `global-claude-md/CLAUDE.md` |
| Installable skills | `skill-toolkit/skills/` (inventory in `skill-toolkit/README.md`) |
| Why any of this is shaped this way | `environment-guide/PHILOSOPHY.md` |

## Conventions

- One git repo at this root (`CLAUDE_SHARE/.git`); each share is a subfolder,
  so future additions land as new folders/commits without touching prior
  shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
