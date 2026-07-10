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

## Conventions

- One git repo at this root (`CLAUDE_SHARE/.git`); each share is a subfolder,
  so future additions land as new folders/commits without touching prior
  shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
