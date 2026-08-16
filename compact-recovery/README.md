# compact-recovery — 壓縮後找得回去的運作模式 (post-compact recall operating mode)

> 這不是單一工具,是一組**運作模式 (operating mode)**:三支 hook、一支摘要卡產生器、
> 一條召回紀律,合起來回答一個問題——`/compact` 之後,摘要裡沒有的東西要怎麼找回來,
> 而且**不能**把壓縮省下的 context 又整份吃回去。
>
> 2026-08-16 於來源環境全鏈真火驗收通過(含壓縮當下的實際觸發);細節見
> [`ACCEPTANCE.md`](ACCEPTANCE.md)。

## 問題形狀

Claude Code 的 compaction 把整段對話換成一份有損摘要 (lossy summary)。完整紀錄
其實**還在磁碟上**(transcript jsonl),但壓縮後的模型三件事都不知道:自己的
session id、原檔在哪、什麼時候「可以」回去讀。結果是:摘要漏掉的事實,靜默地
永久消失——除非有人把「回去的路」重新塞進 context。

塞回去的東西又不能太大,否則壓縮白做。這個模式的核心論證:

- **壓縮省的是 resident tokens**——之後每一輪都要重付的那種。
- **召回花的是 on-demand tokens**——一次查詢付一次。
- 指標卡約 130 resident tokens,指向它背後的幾十萬;唯一會讓 context 重新膨脹的
  行為是「整檔重讀」,而那一步被 hook 結構性拒絕。
- 實測摘要卡 (digest) 約為原始逐字稿的 1%(50KB vs 4.3MB,一個真實 session)。

## 機制:一對事件的橋接

平台契約(2026-08-16 對 code.claude.com hooks 文件與 Agent SDK 型別查證):

| 事件 | 能做什麼 | 不能做什麼 |
|---|---|---|
| `PreCompact` | 壓縮**前**跑副作用(讀 stdin 的 `session_id` / `transcript_path` / `trigger`) | stdout **不會**注入 context |
| `SessionStart`(matcher `"compact"`) | stdout **會**注入壓縮後的新 context;manual 與 auto compact 都觸發 | 拿不到壓縮前的行數/大小 |

所以機制拆成兩半,以一個書籤檔為橋:

```
/compact
   │
   ├─ PreCompact ──► compact_bookmark.py
   │                   1. 寫 cache/compact-recovery/<session-id>.json
   │                      {transcript_path, line_count, size_bytes, trigger, ts}
   │                   2. 順跑 preserve.py(≤45s,best-effort)──► 活 session 的
   │                      digest 卡在「壓縮那一刻」就存在,不用等 SessionEnd
   │
   ├─ (平台產生摘要)
   │
   └─ SessionStart("compact") ──► compact_pointer.py
                         讀書籤,印出 ~130 token 的指標卡:
                         digest 路徑(grep FIRST)、原檔路徑 + 壓縮前區段
                         (lines 1..N)、兩個召回觸發條件、視窗化讀取紀律
```

第三支 hook 讓紀律變成結構而不是散文:

- `transcript_read_guard.py`(PreToolUse `Read`):語料根目錄下、大於 128KB 的
  檔案,沒帶 `limit` 或 `limit > 120` 的 Read 一律 deny,並在拒絕訊息裡指出
  合規路徑(先 Grep 定位 → 視窗 Read)。Grep/Glob 不受影響,小檔自由讀。
  規則寫成**資產屬性**(「這類檔案不得無界讀取」),不是路徑指令(「讀 X 時記得 Y」)
  ——後者只跟讀者的記性一樣可靠,而它最容易失守的時刻,正是壓縮後急著找事實的
  那個當下。

## 召回梯 (recall ladder)

指標卡上寫的紀律,由上而下、花費遞增:

1. **Digest 卡 Grep**(~原文 1%):具名詞彙,`≤3` hits、小 `-C`。
2. **原檔區段 Grep**:digest 因 per-turn 截斷而沒有 → 對 jsonl 用窄 pattern
   (`-o` 或小 `-C`;jsonl 單行可超過 100KB,別讓整行進 context)。
3. **視窗 Read**:Grep 定位到行號後 `offset` + `limit ≤ 120`(hook 強制)。
4. **你自己的鏡像/檢索層**(可選):CONFIG 裡加自己的 mirror 根目錄;
   grep → 視窗讀這個原語,就是未來跨 session 索引/RAG 層直接繼承的介面。

召回**只在**兩種情況啟動:(a) 使用者明說要查原文;(b) 一個**具名的**承重事實
(決策、數字、路徑、措辭)在摘要裡缺席。「整份重讀一遍以防萬一」不在其中,
而且被 guard 擋掉。

## 檔案

| 檔案 | 裝到哪 | 角色 |
|---|---|---|
| `../hooks/compact_bookmark.py` | `<CLAUDE_HOME>/hooks/` | PreCompact:寫書籤 + 順跑 preserve |
| `../hooks/compact_pointer.py` | `<CLAUDE_HOME>/hooks/` | SessionStart("compact"):注入指標卡 |
| `../hooks/transcript_read_guard.py` | `<CLAUDE_HOME>/hooks/` | PreToolUse(Read):視窗紀律硬強制 |
| `preserve.py` | `<CLAUDE_HOME>/tools/memory-pipeline/` | 歸檔 + digest 卡產生器(零依賴、零模型、零網路) |

`compact_bookmark.py` 以 `<CLAUDE_HOME>/tools/memory-pipeline/preserve.py` 這個
路徑呼叫 preserve——裝在別處它只會安靜跳過(fail-open),digest 那一階梯子退化為
「直接 Grep 原檔」,其餘照常。

## 安裝

1. 複製四個檔案到上表位置。
2. 把下面三個區塊**併進**你的 `settings.json`(`<PYTHON_EXE>`、`<CLAUDE_HOME>`
   換成絕對路徑;Claude Code 不展開 `~` 與環境變數):

```json
"PreCompact": [
  { "matcher": "",
    "hooks": [ { "type": "command",
      "command": "\"<PYTHON_EXE>\" \"<CLAUDE_HOME>/hooks/compact_bookmark.py\"",
      "timeout": 60 } ] }
]
```

```json
"SessionStart": [
  { "matcher": "compact",
    "hooks": [ { "type": "command",
      "command": "\"<PYTHON_EXE>\" \"<CLAUDE_HOME>/hooks/compact_pointer.py\"",
      "timeout": 10 } ] }
]
```

(已有 `SessionStart` 陣列就把這個 entry 追加進去,不要蓋掉原有的。)

```json
"PreToolUse": [
  { "matcher": "Read",
    "hooks": [ { "type": "command",
      "command": "\"<PYTHON_EXE>\" \"<CLAUDE_HOME>/hooks/transcript_read_guard.py\"",
      "timeout": 5 } ] }
]
```

3. **可選**——session 結束時也歸檔(這是 preserve 原生的觸發點;沒有它,digest
   只在每次壓縮時刷新):

```json
"SessionEnd": [
  { "matcher": "",
    "hooks": [ { "type": "command",
      "command": "\"<PYTHON_EXE>\" \"<CLAUDE_HOME>/tools/memory-pipeline/preserve.py\"",
      "timeout": 60 } ] }
]
```

4. 手動驗證各檔 fail-open(安靜 exit 0 即健康):

```powershell
Get-Content NUL | & "<PYTHON_EXE>" "<CLAUDE_HOME>/hooks/compact_pointer.py"
```

5. 跑一次 `/compact` 走 [`ACCEPTANCE.md`](ACCEPTANCE.md) 的七項清單。
   **複製不等於生效**——hooks 對進行中的 session 立即套用(來源環境實測),
   但驗收要看的是卡片真的出現,不是檔案在不在。

## 可調參數(集中一處,附調整表)

| 想改什麼 | 參數 | 所在 | 出貨值 | 合理範圍 |
|---|---|---|---|---|
| 多大的檔才受視窗紀律管 | `SIZE_GATE` | transcript_read_guard.py | 128KB | 64–512KB |
| 視窗 Read 上限 | `LINE_WINDOW` | transcript_read_guard.py | 120 行 | 60–200 |
| digest 落後多久才標「may lag」 | `DIGEST_LAG_GRACE_S` | compact_pointer.py | 300s | 60–600 |
| digest 刷新最多佔用壓縮多久 | `PRESERVE_TIMEOUT_S` | compact_bookmark.py | 45s | 15–50(< settings timeout) |
| digest 每則訊息保留多少字 | `user_msg_max` / `assistant_msg_max` | preserve.py CONFIG | 1200 / 500 | 視你的召回習慣 |
| 語料根目錄 | `CORPUS_ROOTS` | transcript_read_guard.py CONFIG | projects + memory-archive | 加你的 mirror 根 |

`SIZE_GATE` 與 `LINE_WINDOW` 在來源環境登記為 PROVISIONAL:定案依據是「哪一次
deny 擋到了**正當的**整檔需求」——遇到就記下場景再調,不要憑感覺放寬。

## 失敗模式(跑不動時你會看到什麼)

- **書籤缺失**(機制上線前的壓縮、寫入失敗)→ 指標卡降級:仍有原檔路徑與大小,
  但沒有行數區段。卡片本身是交付物,靜默空白視為缺陷,所以降級卡是刻意設計。
- **digest 缺失**(preserve 沒裝、被噪音過濾、刷新失敗)→ 卡上明講
  「not generated … use the transcript region」,梯子從第 2 階開始。
- **guard 誤擋正當整檔需求** → 訊息裡永遠帶著合規路徑;真的需要整檔時,
  記錄場景、調 `SIZE_GATE`/`LINE_WINDOW`,而不是拔 hook。
- **全部 fail-open**:任何解析錯誤 exit 0,守衛的 bug 不會擋住工作。

## 平台契約備忘(review-when 的復查配方)

這個模式押在三個平台行為上,任何一個變了就先復查再信卡片
(hook docstring 的 review-when 都指到這一節):

1. **Compact 落盤幾何**:`compact_boundary` 系統列**就地附加**在同一份 session
   jsonl 中段,session id 不變;多次壓縮會疊多個 boundary。復查法:對
   `projects/*/*.jsonl` grep boundary 列的行號——出現在檔案中段即未變。
   (另觀察過 resume 進新檔時 boundary 靠檔頭的變體;書籤按 session id 對齊,
   兩種幾何都成立。)
2. **PreCompact stdin 欄位**:`session_id` / `transcript_path` / `trigger`。
3. **SessionStart stdout 注入 + matcher `"compact"` 雙觸發**(manual 與 auto)。

查證基準日 2026-08-16(code.claude.com 的 hooks 文件 + Agent SDK 型別)。

## 邊界(明知不蓋的地方)

- Guard 只管 `Read` 工具;shell 側(`cat`/`Get-Content`)是**已登記的擴充觸發
  事件**——等它真的成為慣性繞道再擴,不預建。
- Subagent 的 transcript 不在卡上(它們不經歷 compaction)。
- auto-compact 觸發的卡(`trigger=auto`)在來源環境驗收時尚未自然發生過一次;
  機制對兩種 trigger 同構,但那一格證據還空著。
- 跨 session 檢索/RAG 不在本模式內——本模式只保證「留下乾淨的語料層與
  grep → 視窗讀的取用原語」讓那一層future 有得接。

## 識別化說明 (de-identification)

依本 repo `tools/COLLECTION-RULES.md` 處理;每一筆編輯都宣告在
`tools/share-manifest.toml` 的 `[[collected]]` 條目:

- 一個 session id、一個排程任務名、一條第二磁碟的鏡像絕對路徑、指向來源環境
  私有樹(memory/、rule registry、設計文件)的指標——**移除或改指向本 README**。
- 量測數字、日期、裁決代號(D1/D2/D3)、失敗模式——**全數保留**,那是讓主張
  可被驗證的部分。
