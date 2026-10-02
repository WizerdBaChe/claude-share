---
xi: 1
what: tracking-refs 工具說明 — 找出「已提交的指令檔指向 git 沒收的檔案」：判定類別、執行方式、兩個觸發點、限制 (guide to the tracking-refs checker: committed instruction surfaces pointing at untracked files — verdict classes, how to run, the two moments it fires, limits)
tags: [tool, git, integrity-sweep, ops-health, readme]
aliases: [追蹤參照檢查, 懸空指標檢查, dangling pointer check, tracking refs]
date: 2026-09-18
status: live
---
# tracking-refs

**問的只有一件事：** 某個已經進 git 的指令檔（CLAUDE.md、skill、hook、rule、ops、路由表……）
提到了一個檔案，而那個檔案存在、卻沒被 git 收進去嗎？

這種狀態叫 **懸空指標 (dangling pointer)**。它的風險在於：回滾 (rollback) 到那段期間任何一個
commit，會把「指標」還原回來，卻沒有「目標」。

起因：2026-09-18 發現 `skills/comsol-agent-pipeline/` 四天都沒進 git，而已提交的 PROJECTS.md
指著它；已提交的 CLAUDE.md 也用裸名稱索引了未追蹤的 `rules/layout-convergence.md`。
完整過程見 `reports/2026-09-18-git-tracking-sweep.md`。

## 判定類別

| 類別 | 意思 | 嚴重度 |
|---|---|---|
| `dangling` | 來源已追蹤，目標存在但未追蹤（也沒被 ignore） | **FAIL**，exit 1 |
| `pending` | 來源和目標都還沒提交——兩端都在進行中，年齡歸 ops-health check 14 管 | 報告 |
| `ignored` | 目標被 .gitignore 刻意排除（執行期狀態、產生物） | 報告 |
| `undetermined` | 到處都找不到目標（像路徑的散文、指向別的 repo 的相對路徑） | 另計，不影響 exit |
| （無聲） | 目標已追蹤 | — |

根目錄不是 git 工作樹時，整次執行判為 `undetermined`（exit 2），不會回報「0 dangling」。

## 認得的引用形式

- **路徑形式**：`tools/x/y.py`、`~/.claude/skills/...`、`C:\Users\...\.claude\...`，含反斜線。
  先從 repo 根解析，再從來源檔的每一層上層資料夾解析（所以 skill 裡寫的 `tools/sync_rules.py`
  會對到 `skills/<那個 skill>/tools/sync_rules.py`）。
- **名稱形式**：反引號包住的裸名稱 → `rules/<名稱>.md`；skill-trigger-dict 的 `### <skill>`
  標題 → `skills/<skill>`。只有檔案真的存在時才算引用，所以一般的反引號單字不會被誤判。

## 執行

```powershell
python tools/tracking-refs/refs.py
```

```powershell
python tools/tracking-refs/refs.py --verbose
```

```powershell
python tools/tracking-refs/controls.py
```

第一行是摘要加 dangling 列表，第二行多列出三個報告類別，第三行是工具自身的兩面對照組（最後一行應為 `ALL PASS n/n`）。另有 `--json` 與 `--root <路徑>`。

出現 FAIL 時：把目標按路徑提交（`git add -- <目標>`）；如果目標本來就不該存在，就改指標。**不要用擴大 .gitignore 的方式讓它安靜。**

## 兩個觸發點

1. **Session 開場提醒**（`hooks/ops_health_nudge.py` check 18）：cwd 是 `~/.claude` 時，
   只要 check 14 的 `git status` 看到 skills/tools/hooks/rules/agents/commands 底下有未追蹤檔，
   就在同一個行程裡跑這支工具；有 dangling 就印一行提醒。樹上沒有未追蹤檔時完全不花成本。
   沒有年齡門檻——指標已經在歷史裡，洞從它出現的那一刻就是真的。
2. **定期完整檢查**（`ops/references/integrity-sweep.md` check 34）：跑 sweep 時一併執行，含對照組。

## 限制

- 無法判斷某個 `undetermined` 字串本來是不是路徑，也無法判斷某個 `ignored` 目標**該不該**被忽略；
  兩者都會列出來源，交給人判斷。
- 只讀「指令面 (instruction surface)」；`outputs/`、`drafts/`、`reports/`、`archive/` 是歷史紀錄，
  裡面的死連結可能本來就是正確的，不掃。
- 引用形式若改了（例如規則不再用反引號裸名稱索引），名稱形式會靜默失效——這列在
  `ops/rule-registry.md`「tracking refs」條目的 review-when。
