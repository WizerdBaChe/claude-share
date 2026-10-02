# T-007 驗收：確認下沉的規則真的會載入

目的：證明 `~/.claude/rules/` 底下那兩條規則 (path-scoped rules) **啟動時不載入、
讀到對應檔案時才載入**。這件事目前只證明到「pattern 正確」，還沒證明「這兩個檔
本身會註冊」——所以以下步驟必須在**新的 session** 跑（規則清單在 session 啟動時建立）。

全程約 2 分鐘。不會改到任何規則檔。

---

## 步驟 0 — 前置（在現在這個 PowerShell 視窗執行）

建立兩個誘餌檔並清空紀錄，讓結果沒有歧義：

```powershell
cd $HOME\.claude; New-Item -ItemType Directory -Force drafts\rulecheck | Out-Null; Set-Content drafts\rulecheck\probe.tsx 'export const a = 1;' -Encoding utf8; Set-Content drafts\rulecheck\probe.frag 'void main(){ gl_FragColor = vec4(1.0); }' -Encoding utf8; Remove-Item telemetry\rule-loads.jsonl -ErrorAction SilentlyContinue; Write-Host "ready"
```

## 步驟 1 — 開一個**新的** Claude Code session

在 `$HOME\.claude` 開啟。**重點是新 session**——沿用舊視窗會讀不到新的
規則清單，測不到東西。

## 步驟 2 — 貼這段 prompt

```
Use the Read tool on drafts/rulecheck/probe.tsx and then on drafts/rulecheck/probe.frag. Do not edit anything, do not run any command, and do not summarize. Just reply: read both.
```

（一定要讓它**真的用 Read 工具**讀這兩個檔；path-scoped 規則是在「讀到符合的檔案」
那一刻才載入的，用猜的、用 grep 的都不會觸發。）

## 步驟 3 — 檢查（回到 PowerShell）

```powershell
python -c "import json,os;p=os.path.expanduser(r'~\.claude\telemetry\rule-loads.jsonl');[print(json.loads(l)['payload'].get('load_reason'),'|',os.path.basename(str(json.loads(l)['payload'].get('file_path')))) for l in open(p,encoding='utf-8')]"
```

---

## 判讀

**通過**（三個條件全中）：

```
session_start    | CLAUDE.md
path_glob_match  | frontend-layering.md
path_glob_match  | shader-failure-modes.md
```

1. 有 `session_start | CLAUDE.md` → hook 還活著，這次量測有效。
2. 兩個規則檔以 `path_glob_match` 出現 → 下沉成功、規則沒死。
3. 兩個規則檔**都沒有**以 `session_start` 出現 → 啟動時確實不計費，省下來的是真的。

**其他結果的意思**：

| 看到 | 意思 | 怎麼辦 |
|---|---|---|
| 完全沒有檔案／檔案是空的 | `InstructionsLoaded` hook 沒觸發 | 這次量測無效。先確認 `settings.json` 裡的 `InstructionsLoaded` 區塊還在，再重跑 |
| 只有 `session_start \| CLAUDE.md`，沒有那兩個規則檔 | **兩條規則是死的**——已被移出 CLAUDE.md 但不會載入 | 回報給我；救援方式：`git revert c46663d`，或把兩個檔的內容貼回 CLAUDE.md 並刪掉前言的索引行 |
| 規則檔以 `session_start` 出現 | `paths:` 沒生效，等於白搬 | 同上，回報後改走 skill 或留在 CLAUDE.md |

## 步驟 4 — 收尾

```powershell
Remove-Item -Recurse -Force $HOME\.claude\drafts\rulecheck
```

（`telemetry\rule-loads.jsonl` 留著沒關係——它是 gitignored 的，而且之後看
「哪些規則檔在什麼時候被載入」還會用到。）
