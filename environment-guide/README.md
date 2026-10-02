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
| `KNOWLEDGE-PACKS.md` | 「知識包」這類資產的形狀、抽象判準與現況紀錄；三個知識包本體不出貨，本檔代替它們對外說明 | The shape, criteria and status record of "knowledge packs"; stands in for the three withheld packs |
| `LABEL-REGISTRY.md` | 可列舉標籤（`Mode X`／`L2`／`Tier-3`／清單序號）的登記規則與維護程序，**以範本形式出貨**：判準與規則完整，家族表只留表頭與一列範例 | The label-registration rules and maintenance procedure, shipped as a **template**: rules complete, family table reduced to its header and one example row |

These five documents cross-reference the operational rule layer and skill
set described in `claude-ops/` and `skill-toolkit/` in this same repo —
they were written to be read together, so those references are retained
rather than stripped. `~/.claude/LABEL-REGISTRY.md` and
`~/.claude/KNOWLEDGE-PACKS.md`, as cited by other files in this repo, resolve
to the two pages above through the manifest's source map.

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
- 2026-10-02 refresh (align to source `183c129`): `PHILOSOPHY.md` gained one
  line in its section-2 tree (an entry for `KNOWLEDGE-PACKS.md`), re-copied with
  every earlier edit re-applied; no new identifier found. Two files are new.
  `KNOWLEDGE-PACKS.md` was written at the source on 2026-10-02 so that it could
  ship unchanged, and does: it was read in full and carries no path, account
  name or session id; it states that the three knowledge-pack skills it
  describes are withheld from this share, and this page is what represents them.
  `LABEL-REGISTRY.md` ships as a **template** (user ruling 2026-10-02): the
  source file is two things, rules (what makes a label need registering, the
  generation axis for project lists, the filename rule, the pre-birth grep) and
  rows (this environment's own families and collisions). The rules ship
  unchanged; the family table keeps its header and one worked row, the
  collision block keeps one worked collision, and the remaining rows — the
  source environment's own label set — do not ship. Three small pointers inside
  the kept rule sections were generalized (two filenames from the source's
  private `references/` tree, and an account name inside a home-path example,
  now `<user>`). The earlier "referenced only, not shipped" disposition for this
  file is reversed; the manifest keeps the superseded reasoning beside the new
  entry.
- This is a point-in-time snapshot, not a synchronization target. It documents
  migration decisions; it does not perform migration or promise cross-host equivalence.
