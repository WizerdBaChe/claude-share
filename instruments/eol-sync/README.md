---
what: eol-sync — 把已追蹤檔案的工作樹行尾 (line ending) 對齊 .gitattributes 的宣告，commit 時自動執行 (realign working-tree line endings to the .gitattributes pin, run on every commit)
layer: instrument
audience: builder
date: 2026-10-01
status: live
---

# eol-sync — 行尾對齊

`.gitattributes` 依**主要讀者**決定行尾（使用者裁決 2026-10-01）：
人會打開來讀、複製的文字，以及 Windows 原生腳本（`.bat`/`.cmd`/`.ps1`…）用 CRLF；
其他給機器讀的檔案（程式碼、設定、skill、規則、JSON）用 LF。

問題是沒有任何 agent 寫檔路徑會遵守這個宣告：Write 工具、Python、heredoc 一律寫 LF。
git 的 index 會正規化，所以檔案一出生就偏離宣告，`git status` 卻顯示乾淨，偏差會一直留著。
ops-health check 21 在 session 開始時**偵測**偏差；這支工具**移除**偏差，
並由 `tools/git-hooks/post-commit` 在每次 commit 時執行——commit 正是新檔案變成資產的那一刻。

```git bash
python -X utf8 tools/eol-sync/eol_sync.py                  # HEAD 這個 commit 碰到的檔案（hook 跑的就是這個）
python -X utf8 tools/eol-sync/eol_sync.py --all            # 全部已追蹤檔案（改宣告後的一次性遷移）
python -X utf8 tools/eol-sync/eol_sync.py --all --check    # 只回報；有偏差 exit 1
python -X utf8 tools/eol-sync/eol_sync.py --wiring         # post-commit hook 有沒有接上
python -X utf8 tools/eol-sync/test_eol_sync.py             # 兩面控制（11 項）
```

## 安全性

- 只改**乾淨**的檔案（內容與 index 只差行尾）；有未提交修改的檔案一律跳過並列出。
- 寫入的是 index blob 加上宣告的行尾，不是把工作樹的內容重新編碼，所以不可能遺失或憑空產生內容。
- 二進位檔、index 內容不是 LF 正規化的檔案也會跳過並列出。
- 改寫後用 `git checkout -- <path>` 讓 index 記下新的檔案狀態：實測只改行尾時 `git status` 會顯示 ` M`
  但 diff 是空的，`update-index --refresh` 與 `--really-refresh` 都清不掉。

## 接線

`git config core.hooksPath tools/git-hooks`（repo 本機設定，不進版控）。換 clone 或被 unset 時對齊會無聲停掉，
所以 system-hmi 的 `uncommitted-work.eol-sync-wiring` 每次採集都檢查它。

## 已知的盲點

- 未追蹤的檔案不處理（還不是資產）；它在第一次 commit 時才會被對齊。
- Write 寫出的 CRLF 類檔案在 commit 之前是 LF——要到 commit 才變 CRLF。commit 後檔案內容被改寫，
  同一個 session 之後要 Edit 它時，可能需要先重新讀取。
