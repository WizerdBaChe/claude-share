# environment-guide｜環境導覽

> **中文摘要｜Chinese summary**：這一層是給人讀的導覽，不是 runtime 設定。
> 它說明一套個人 `~/.claude` 環境為何這樣分層、哪些資產需要保留，以及如何
> 依 host contract 搬到新機器或其他 agent 平台。
>
> **English summary**: This is the human-facing guide to the structure and rationale of
> one personal `~/.claude` environment. It explains migration priorities and commit
> conventions; it is documentation, not executable runtime configuration.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 先讀 | `PHILOSOPHY.md`：理解分層與資產優先序 | `PHILOSOPHY.md`: understand the system map and asset tiers |
| 要操作 | `OPERATOR-GUIDE.md`：權限、環境慣例與搬移 checklist | `OPERATOR-GUIDE.md`: permissions, environment conventions, and migration checklist |
| 要提交 | `COMMIT-TEMPLATES.md`：Conventional Commits 格式 | `COMMIT-TEMPLATES.md`: Conventional Commits templates |
| 跨平台 | Claude → Codex／ChatGPT 的 target／package 規則請讀 [`../interop-layer/README.md`](../interop-layer/README.md) | Use the interop layer for Claude-to-Codex/ChatGPT target and package rules |

## 內容｜Contents

| File | 中文用途 | English purpose |
|---|---|---|
| `PHILOSOPHY.md` | 規則背後的非規範性信念、系統圖與搬移時的核心資產分級 | Non-normative beliefs, system map, and core-asset tiering for migration |
| `OPERATOR-GUIDE.md` | 權限模式、環境慣例、資產地圖與逐步搬移手冊 | Permission modes, environment conventions, asset map, and migration procedure |
| `COMMIT-TEMPLATES.md` | 依實際 commit history 整理的 Conventional Commits 範本 | Conventional Commits templates derived from the environment's commit history |

These three documents cross-reference the operational rule layer and skill
set described in `claude-ops/` and `skill-toolkit/` in this same repo —
they were written to be read together, so those references are retained
rather than stripped.

## 快照細節與證據界線｜Snapshot details and evidence boundary

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
- This is a point-in-time snapshot, not a synchronization target. It documents
  migration decisions; it does not perform migration or promise cross-host equivalence.
