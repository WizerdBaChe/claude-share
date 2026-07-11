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

### `claude-ops/` snapshot details

- Source: `~/.claude/ops/` (12 Markdown files), copied manually on 2026-07-11.
- Review scope: usernames, local paths, account or machine identifiers, and email-like strings.
- Result: one source username was removed; references between the operational documents were intentionally retained.
- This is a point-in-time snapshot, not a synchronization target. Folder-level documentation is maintained separately.

### `skill-toolkit/` snapshot details

- Source: `~/.claude/skill-trigger-dict.md`, `~/.claude/skills/`, and `~/.claude/Global_skill_update.md`, copied manually on 2026-07-11.
- Contents: a bilingual trigger dictionary, 12 skill directories with their referenced material and evaluations, plus the append-only global skill update log.
- Review scope: usernames, email-like strings, absolute local paths, internal project or package names, and runtime lock metadata.
- Result: non-skill paths and identifiers were replaced with portable placeholders; the runtime lock metadata was redacted.
- Exception: historical paths in `Global_skill_update.md` that point directly to skill files were intentionally retained verbatim to preserve the update log's traceability.
- This is a point-in-time snapshot, not a synchronization target. Installation guidance and the complete skill inventory live in `skill-toolkit/README.md`.

## Conventions

- One git repo at this root (`CLAUDE_SHARE/.git`); each share is a subfolder,
  so future additions land as new folders/commits without touching prior
  shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
