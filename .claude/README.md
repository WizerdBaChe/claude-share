# `.claude/` — 這個分支專用的 Cloud session 設定

## 這是什麼

讓 **Claude Code on the web（cloud session）** 開在這個 repo 時，能自動載入本 repo
已經收錄的個人設定 —— 全域偏好 (`CLAUDE.md`)、五條 path-scoped 規則、十七個
skills。在此之前 cloud 環境等於裸機：`~/.claude/CLAUDE.md`、`~/.claude/rules/`、
`~/.claude/ops/` 全都不存在，只有平台自己注入的 CCR hook 和帳號同步的 skills。

## ⚠ 只活在這個分支，永遠不 merge 回 `main`

`main` 的 `.gitignore` 用 `.claude/` 把整個目錄擋掉，這是刻意的設計。
`ADOPTERS.md` 寫得很明白：

> **Do not clone this repo inside a directory your agent scans.**
> Cloned into a workspace, this repo stops being reference material and becomes
> live instructions you did not choose.

也就是說，這個 repo 對 adopter 的承諾是「**參考資料，不是可安裝的設定**」。一旦
`.claude/` 進了 `main`，任何人 clone 下來用編輯器打開，就會無聲無息地套用一整套
別人的規則和十七個 skills —— 正好是 `ADOPTERS.md` 警告的那件事。

所以本分支 (`claude/cloud-env-claude-skill-sync-elmbhu`) 做了兩件只屬於這裡的修改：

| 檔案 | 分支上的改動 | 為什麼不能進 `main` |
|---|---|---|
| `.gitignore` | `.claude/` → `.claude/*` 加四條 negation | 解除忽略才追蹤得到；`main` 需要保持忽略 |
| `CLAUDE.md`（repo 根目錄） | 新增 | `main` 上沒有根 CLAUDE.md 是刻意的 |

**要同步 `main` 的新內容就 rebase，不要 merge 回去：**

```bash
git fetch origin main
git rebase origin/main
./.claude/sync-from-repo.sh          # 重新複製 rules/ 和 skills/
./.claude/sync-from-repo.sh --check  # 確認沒有 drift
```

## 內容與來源

| 路徑 | 來源（本 repo 內） | 關係 |
|---|---|---|
| `.claude/rules/`（5 檔） | `global-claude-md/rules/` | **逐位元組相同**，`sync-from-repo.sh` 產生 |
| `.claude/skills/`（17 個 skill、94 檔、1.2 MB） | `skill-toolkit/skills/` | **逐位元組相同**，同上 |
| `/CLAUDE.md` | `global-claude-md/CLAUDE.md` | **手工適配**，非逐位元組。腳本不會重新產生它 |

`CLAUDE.md` 為什麼要手工改：源檔是 Windows／PowerShell 機器的設定，而且引用
`~/.claude/ops/`、`~/.claude/skill-trigger-dict.md` 這些在容器裡不存在的路徑。適配
版做了三件事 —— 路徑改指向這個 clone 裡真的存在的檔案、刪掉三條在 Linux 上不可能
觸發的 PowerShell 條目、在檔尾加一張「Cloud-session deltas」表列出所有這個環境**沒
有**的機制。沒有任何一條規則被無聲刪除。

## `tools/share_gate.py` 在這個分支會紅 —— 而且**應該**紅

repo 自己的發布閘門有一條規則：追蹤路徑只要含 `/.claude/` 就是 finding，處置是
「untrack it」。這條規則正是在保護上面說的那個承諾，而本分支明知故犯地推翻它。

**所以不要把它弄綠。**改閘門或改 `share-manifest.toml` 讓紅燈消失，等於拆掉保護
`main` 的控制 —— 而且閘門自己就寫著：

> Nothing is auto-fixed on purpose: automatic scrubbing is what produced the
> damage this gate exists to catch.

改成把「預期的紅」釘成**可驗證的形狀**：

```bash
./.claude/sync-from-repo.sh --gate
```

它斷言閘門的每一個 finding 都只會是這兩種其中之一：

| 形狀 | 數量 | 是什麼 |
|---|---|---|
| `[S] .claude/…` | 每個追蹤檔一個（目前 101） | 上述發布政策規則，預期中 |
| `[L] .claude/skills/…` | 7 | skill 文件裡**刻意的教學範例**（一個磁碟機代號配單字元目錄，故意寫成反斜線／正斜線／小寫三種拼法），在 `skill-toolkit/` 原路徑早已審過並列入 `[[allow]]`；`[[allow]]` 綁死檔案路徑，所以副本沒被涵蓋。不是外洩 |

出現**任何第三種形狀**就是這個分支真的引入了問題，`--gate` 會 exit 1 並指名到
`file:line`。這條斷言做過雙向校準：乾淨樹回 exit 0；在一個 skill 檔尾植入一條假的
磁碟機絕對路徑後回 exit 1，並正確指出 `workflow-checkpoint/SKILL.md:230`；移除後回
到 exit 0。

（這段文字本身不寫出那些路徑的字面形式 —— 寫了就會變成閘門的 finding。這不是假設：
初稿寫了，`--gate` 當場抓到 `.claude/README.md` 的兩行，才改成現在的描述式寫法。）

順帶一提，`tools/test_share_gate.py` 在這個分支是 9/11（乾淨的 `main` 上是 11/11）。
失敗的兩個都是 control 案例，它們拿當前工作樹當「應該乾淨」的基準 —— 同一個原因，
同樣不該用改測試的方式弄綠。

## 已知問題：`env-cleanup` 會出現兩次

Claude Code 的 skill 去重是**按檔案**而不是按名稱，所以同名但不同檔的 skill 會同時
載入。你的帳號層 (`~/.claude/skills/synced/`) 已經同步了一份 `env-cleanup`，本
`.claude/skills/` 又有一份，於是清單裡會看到兩個。

**專案這份（2026-09-02）才是對的。**帳號同步那份停在 2026-07-20，具體錯三個地方：

1. 說歸檔紀錄寫進 `Global_skill_update.md` —— 該檔 2026-08-11 已凍結，現在紀錄走
   git commit message 加批次的 `CLEANUP-REPORT.md`。
2. 把 `telemetry/` 標成超過門檻就可刪 —— 新版明訂那是快照序列 (snapshot series)，
   過去狀態無法重建，且 `skill-routing-audit.py --snapshot` 會讀歷史，只能封存。
3. 缺 2026-08-16 加的根目錄清單 —— 沒有它，整棵目錄樹對分類是隱形的（當初就是這樣
   讓一個 726 MB 的 `memory-archive/` 完全沒被分類到）。

**根治方式（只有你能做，需要在 claude.ai 上操作）**：到 Settings → Capabilities →
Skills，把那個 custom skill `env-cleanup` 更新成 `skill-toolkit/skills/env-cleanup/`
的現行版本，或直接刪掉讓專案這份唯一。改完之後所有 cloud session 都會生效，不限
這個 repo。

## 這次沒有同步的東西

以下都在 repo 裡，但**刻意沒有**放進 `.claude/`：

- `hooks/`（18 支）與 `hooks/settings.example.json` —— 需要 `.claude/settings.json`
  才會掛載，其中 2 支只能跑 PowerShell、2 支需要 Claude_Browser MCP。
- `agents/`（8 個 subagent 定義）
- `claude-ops/ops/`（15 個規則檔）—— 不自動載入，但 `CLAUDE.md` 的引用已經改指到
  `claude-ops/ops/`，需要時讀得到，這正是源檔本來的用法。

要加的話跟我說一聲就好。
