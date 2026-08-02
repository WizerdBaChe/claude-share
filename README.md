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

### `claude-ops/` snapshot details

- Source: `~/.claude/ops/` (12 Markdown files), copied manually on 2026-07-11; refreshed 2026-07-31.
- Review scope: usernames, local paths, account or machine identifiers, and email-like strings.
- Result: one source username was removed (`ops/environment.md`); references between the operational documents were intentionally retained.
- This is a point-in-time snapshot, not a synchronization target. Folder-level documentation is maintained separately.

### `skill-toolkit/` snapshot details

- Source: `~/.claude/skill-trigger-dict.md`, `~/.claude/skills/`, and `~/.claude/Global_skill_update.md`, copied manually on 2026-07-11; refreshed 2026-07-31.
- Contents: a bilingual trigger dictionary, 12 skill directories with their referenced material and evaluations, plus the append-only global skill update log.
- Review scope: usernames, email-like strings, absolute local paths, internal project or package names, and runtime lock metadata.
- Result: non-skill paths and identifiers were replaced with portable placeholders; the runtime lock metadata was redacted. No new identifiers found in the 2026-07-31 refresh.
- Exception: historical paths in `Global_skill_update.md` that point directly to skill files were intentionally retained verbatim to preserve the update log's traceability.
- This is a point-in-time snapshot, not a synchronization target. Installation guidance and the complete skill inventory live in `skill-toolkit/README.md`.

### `environment-guide/` snapshot details (new 2026-07-31)

- Source: `~/.claude/PHILOSOPHY.md`, `~/.claude/OPERATOR-GUIDE.md`, `~/.claude/COMMIT-TEMPLATES.md`, copied manually on 2026-07-31.
- Review scope: usernames, local paths, account or machine identifiers.
- Result: two username occurrences in path examples were replaced with generic `<user>` placeholders.
- This is a point-in-time snapshot, not a synchronization target. See `environment-guide/README.md`.

### `global-claude-md/` snapshot details (new 2026-08-02)

- Source: `~/.claude/CLAUDE.md`, copied manually on 2026-08-02 (captures the 2026-08-01 update that added the Windows/PowerShell environment rule and the Feature-Sliced Design architecture rule).
- Review scope: usernames, local paths, account or machine identifiers, machine-bound environment facts.
- Result: the file carried no personal identifiers; its "Environment" section pinned a specific OS/shell/line-ending combination and was replaced with `<OS_NAME>` / `<SHELL_NAME_AND_VERSION>` / `<LINE_ENDING_CONVENTION>` placeholders (original values kept as an inline comment for reference). Cross-references to the operational rule layer and skill-trigger dictionary were generalized to `<OPS_DIR>` and `<SKILL_TRIGGER_DICT_PATH>`, which map to `claude-ops/` and `skill-toolkit/skill-trigger-dict.md` in this same repo.
- This is a point-in-time snapshot, not a synchronization target. See `global-claude-md/README.md`.

## Conventions

- One git repo at this root (`CLAUDE_SHARE/.git`); each share is a subfolder,
  so future additions land as new folders/commits without touching prior
  shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
