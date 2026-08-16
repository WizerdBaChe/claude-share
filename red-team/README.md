# red-team — 讓「紅隊審查」的結論可以被機械驗證的運作模式

> 這不是一支工具,是一組**運作模式 (operating mode)**:一份 prompt 形狀、
> 一條六層驗收梯 (acceptance ladder)、兩支把其中四層寫成程式的檢查器,
> 合起來回答一個問題——**當一個模型告訴你「這裡有 bug」,你憑什麼相信它?**
>
> 2026-08-15/16 於來源環境實測,包含一次真實的捏造 (fabrication)、一次
> 因驗收層過嚴而毀掉兩個真發現的事故、以及修正後的回歸測試。細節見
> [`ACCEPTANCE.md`](ACCEPTANCE.md)。

## 問題形狀

派一個模型去審查程式碼,它會回一份看起來很專業的報告。問題是:

- **格式漂亮不等於讀過檔案。** 2026-08-15,一個外部免費層模型回了單一發現,
  格式完美,宣稱某行缺少 `await`——而那一行的實際內容是
  `await page.addStyleTag(...)`。輸出本身沒有任何破綻,是推理軌跡 (reasoning
  trace) 洩漏的,而軌跡不是每次都有。
- **輸出壓力會製造發現。** 那次捏造的軌跡寫著「need to output findings.
  Provide none. But perhaps there's a defect:」。模型不是想騙人,是被
  「交出東西」的隱含要求推過去的。
- **完美的錨點也可能指錯目標。** 另一次實測:一個 arm 的引文與檔案逐字元相符,
  而那個檔案不在受審 commit 裡、不在任何 commit 裡、根本沒被 git 追蹤。
  錨點驗證的是**引文**,不是**主題 (subject)**。

所以「讓 reviewer ≠ author」只解決了一半——另一半是:**這份報告要能被機器
反駁**,而且反駁的成本要低於捏造的成本。

## 機制:六層驗收梯

```
  [1] prompt 形狀            prompts/redteam-v2*.txt
       │  格式指令放第一行 · 每個宣稱附逐字引文 + file:line · 明列受審檔案
       │  · 明文授權空答案([] 是正確答案,不扣分)
       ▼
  (任何 dispatcher:本機 subagent / 外部模型 / 你自己的 HTTP 客戶端)
       │
       ▼
  [報告] 一個 JSON array,每個 finding 六個 key
       │
       ▼
  [2] structure   ┐
  [3] anchor      ├─ score_redteam.py  ←  jsonspan.py
  [4] scope +     │     引文對得上檔案?在受審範圍內?捏造一個就整份作廢
      spot-check  ┘     --repair 產出行號修正版,餵給下一層
       │
       ▼
  [5] adversarial  redteam_verify.py   ← 你的 dispatcher(契約見下)
       │     每個 finding 派一個「去反駁它」的**不同**模型
       │     三值:survived / refuted / inconclusive
       ▼
  [6] ledger chain  by construction — 帳是 dispatcher 寫的,不是 worker 寫的
```

第 6 層不需要程式:只要**紀錄由派工方寫入、受審方碰不到**,worker 就無法
自己記自己的帳。這是結構性質,不是檢查。

## 為什麼是這個形狀(每一條都有實測)

| 設計 | 依據 | 樣本 |
|---|---|---|
| 輸出格式指令放**第一行** | 放結尾時模型會忽略 | 12/12 接受 vs 8/8 拒絕 |
| 每個宣稱附**逐字引文 + file:line** | 讓捏造變貴:抄一行不用讀檔是不可能的 | 抓到 2026-08-15 那次捏造 |
| **一個壞錨點作廢整份報告** | 捏造過一次的模型,其他宣稱的價值已經被它自己說明了 | — |
| **明列受審檔案**,不要只說「審這個 commit」 | 錨點驗證引文、不驗證主題 | 未列:438 秒錨在未追蹤檔案;列出四個檔名:3/3 錨定、ACCEPTED、110 秒 |
| **授權空答案**(「回 `[]` 是正確的,不花你任何代價」) | 錨點提高捏造成本,這一條降低誠實成本;分開用都比較弱 | 捏造那次是在可見的輸出壓力下發生的 |
| verifier **必須**不同於 author | 模型檢查自己的作品會複製自己的錯誤 | 工具層硬性拒絕 |
| `inconclusive` 是**第三個值**,不是 refuted | 工具失敗不是關於宣稱的證據 | 首次實跑 3 個裡錯 2 個,全錯同一方向 |

### 一個要付出的代價,先講清楚

錨點式 prompt 會**壓抑無法錨定的發現,包含真的**。同一個 sonnet reviewer
對同一個 commit:未錨定版回 7 個發現,錨定版回 2 個。請把兩種 prompt 當成
**兩種不同的量具**,而不是 v2 取代 v1。要廣度時用未錨定版並自己讀;要能
自動化驗收時用錨定版。

## 這個 share 交付什麼

| 檔案 | 是什麼 |
|---|---|
| `prompts/redteam-v2.txt` | commit 範圍版 prompt 模板(`<COMMIT_SHA>` 待填) |
| `prompts/redteam-v2.1.txt` | **檔案清單範圍版**(建議預設)。四個 `<FILE_UNDER_REVIEW_n>` 待填 |
| `score_redteam.py` | 驗收層 2–4。純標準庫,不需要任何 dispatcher |
| `jsonspan.py` | 從模型回覆裡取出 JSON 的唯一一份掃描器(見下方「三份拷貝」) |
| `redteam_verify.py` | 驗收層 5。需要一個 dispatcher,契約見下 |
| `test_score_anchor.py` | 錨點層的 10 個回歸案例,含「捏造仍然作廢報告」的守門案例 |
| `test_parser_rulers.py` | 貪婪正則 vs 平衡掃描的 8 個邊界案例 |
| `ACCEPTANCE.md` | 真火驗收清單:哪幾項來源環境已驗過、哪幾項留給你 |

**不交付的**:來源環境的 dispatcher 本身(`extdispatch.py`)。它綁定特定
供應商、金鑰處理、以及一份本機專案路徑白名單——那是一台機器的性質,不是這套
方法的性質。方法論的完整敘述(量測、樣本數、失效簽章)在
[`../claude-ops/ops/references/external-dispatch.md`](../claude-ops/ops/references/external-dispatch.md)。

## 三種接法

**A. 純本機(最省事,不需要外部模型)。** 用這個 repo 的
[`../agents/engineering-code-reviewer.md`](../agents/engineering-code-reviewer.md) subagent 當 reviewer:
唯讀工具白名單、fresh context、`permissionMode: dontAsk`。把
`prompts/redteam-v2.1.txt` 的內容當成它的任務描述,把它輸出的 JSON 存檔,
再跑 `score_redteam.py`。層 5 用第二個**不同**的 subagent。派工契約在
`../claude-ops/ops/20-dispatch.md` 的 **T5 Review/red-team**。

**B. 外部模型層。** 自備 dispatcher(見下一節),層 5 全自動。

**C. 混合。** 本機出報告,外部模型反駁——這是最便宜的組合,因為層 5 每個
finding 只要一次短呼叫。

安裝:把 `red-team/` 整個資料夾放到任何地方,`python -m pip` 不需要跑任何東西。
需求:Python 3.10+,**只用標準庫**。

```git bash
python score_redteam.py --repo ../my-project --report arm.json --commit a1b2c3d --repair repaired.json
python redteam_verify.py --repo ../my-project --report repaired.json \
    --author model-a --verifier model-b --grant "$GRANT" --dispatcher ./my_dispatcher.py
```

`--commit` 是**選用但強烈建議**的:沒有它就不做範圍檢查,而範圍漂移
(scope drift) 正是錨點層抓不到的那一類。

## 把層 5 接上你自己的 dispatcher

`redteam_verify.py` 用 `--dispatcher` 依名稱載入模組(預設 `extdispatch`,
也就是來源環境的呼叫方式原封不動)。契約只有兩個符號:

```python
# my_dispatcher.py — 大約 20 行,對著你自己的模型層寫
MODELS = {"model-a": ..., "model-b": ...}   # 只需支援 `in` 與 iteration

def dispatch(profile, prompt, repo, grant, verbose=False, only_model=None):
    """回傳 {"ok": bool, "answer": str, "trail": [{"stage": str}, ...]}

    ok=False 代表「沒問到」,不是「被反駁」——層 5 會把它記成
    inconclusive 並要求重跑。這個分別是這一層最容易寫錯的地方。
    """
```

`profile` 這裡固定是 `"review"`;`grant` 是你自己的配額/授權概念,不需要就忽略。
不滿足契約時工具會在花掉任何一次呼叫**之前**拒絕並印出缺什麼。

## 可調參數 (tunables)

| 參數 | 在哪 | 出貨值 | 合理範圍 / 說明 |
|---|---|---|---|
| 必要欄位集合 | `score_redteam.py` `REQUIRED_KEYS` | 六個 key | 加欄位要同步改 prompt,否則整批 MALFORMED |
| 不可錨定的宣告字串 | `score_redteam.py` `NOT_FOUND` | `SOURCE-NOT-FOUND` | 改了就要改 prompt 裡的同一字串 |
| 致命判定集合 | `score_redteam.py` `fatal` list | `FABRICATED` / `BAD-PATH` / `MALFORMED` / `OUT-OF-SCOPE` | 把 `MISALIGNED` 加回去 = 退回 2026-08-16 之前的行為,會毀掉真發現 |
| 空白容忍 | `check_anchor()` | 忽略前後空白的相符算 `OK` | 不建議放寬到「子字串相符」——那等於放棄錨點 |
| 反駁指令語氣 | `redteam_verify.py` `PROMPT` | 「你的工作是**反駁**」+ 不確定即 refuted | 改成「請確認」會讓 verifier 附和 |
| verifier 數量 | 目前每個 finding 一個 | 1 | 多數決 (2/3、3/5) 是合理的加強;成本線性成長 |
| 嚴重度詞彙 | prompt 內 | high / medium / low | 自由;`score_redteam.py` 不解讀它 |

## 缺哪一塊,你會看到什麼

| 少了 | 症狀 |
|---|---|
| 錨點規則(prompt) | 報告變長、變好看,`score_redteam.py` 全部 `MALFORMED`(沒有 `quote` 欄) |
| 範圍明列(prompt) | 完美錨點指向你沒在審的檔案;只有 `--commit` 能抓到 |
| 空答案授權(prompt) | 乾淨的 commit 也會生出發現。這是捏造最常見的入口 |
| `score_redteam.py` | 你回到用眼睛讀報告——那正是 2026-08-15 沒攔下來的那條路 |
| `--commit` | `OUT-OF-SCOPE` 永遠不會出現,範圍漂移靜默通過 |
| `redteam_verify.py`(層 5) | 你只知道模型**讀過**檔案,不知道它**說對**了 |
| verifier ≠ author | 附和。工具會直接拒絕,所以這一格只會發生在你自己手動跑的時候 |
| `jsonspan.py` | `score_redteam.py` 匯入即失敗——兩個檔案必須同目錄 |

## 已知邊界與失效模式

- **UTF-8 BOM。** PowerShell 的 `Out-File -Encoding utf8` 會寫入 `EF BB BF`,
  而 `.strip()` 不會移除它,於是完美的 JSON 被判成 `STRUCTURE-FAIL`,錯怪模型。
  已在 `extract_findings` 修掉;凡是 PowerShell 重導向餵給 parser 的地方都要
  預期同一形狀。**更一般的問題**:一個機械閘因為沒人指定過的傳輸細節而否決
  正確內容——這是開放的規範問題,不是已解的。閘只能對它**能判定**的事下判斷。
- **三份拷貝的教訓。** 同一個 JSON 掃描器曾經被寫了三份:層 5 一份、實驗腳本
  一份、層 2 一份用的是 `find("[") .. rfind("]")` 的貪婪切法。前兩份各自修好過,
  第三份活到 2026-08-16——**兩次獨立修復正是第三份能存活的原因**,因為每一次
  從自己的位置看都像修完了。更糟的是 `test_parser_rulers.py` 當時匯入的是
  實驗那份,所以測試覆蓋的不是驗收路徑跑的程式。現在只有 `jsonspan.py` 一份。
- **`file_sha` 指紋。** 錨點是「某個時刻對某個檔案」的宣稱。同一份報告重跑兩次
  可以合法地得到不同行號,因為檔案動了(實測:另一個 session 正好修掉了受審的
  缺陷,所有錨點位移五十幾行)。沒有這個指紋,第二次評分看起來會像評分器壞了。
- **100% 通過率本身就是紅旗。** 先懷疑量具,再相信結果。這個 repo 的
  `../tools/test_share_gate.py` 有兩個案例是斷言閘**保持安靜**的——只用
  「該抓的」校準的閘,靠全部否決就能拿 100 分。
- **儀式化 (ritualization)。** 紅隊連續幾輪全過,通常代表這道關卡已經變成儀式,
  不代表品質變好。`../claude-ops/ops/40-maintenance.md` 把這件事寫成明文警告。
- **層 5 沒有解決真值問題。** 它把「一個模型說的」換成「兩個立場相反的模型說的」。
  對事實性缺陷(這行會不會 crash)很有效;對設計品味無效。

## 平台契約與重新查證

這套機制**不依賴**任何 Claude Code hook、API 或 SDK 型別——它是兩支讀檔案、
比字串的 Python 腳本加一份 prompt。要重新查證的只有三件事,而且都在本機:

```git bash
python test_score_anchor.py     # 10 個案例,含捏造回歸守門
python test_parser_rulers.py    # 8 個邊界案例
git -C ../my-project show --pretty=format: --name-only a1b2c3d   # 範圍層問 git 的那句
```

第三行是 `commit_files()` 唯一的外部依賴。任何能回答「這個 commit 動了哪些檔案」
的 VCS 都可以替換掉它。

## 去識別化說明 (de-identification notes)

依 [`../tools/COLLECTION-RULES.md`](../tools/COLLECTION-RULES.md) 收錄,每筆編輯
都登記在 [`../tools/share-manifest.toml`](../tools/share-manifest.toml) 的
`[[collected]] edits`。這裡摘要**讀者會注意到的三處**:

1. 兩支腳本 docstring 裡的 `--repo` 範例原本是一個私有第二磁碟的絕對路徑,
   換成 `<project-root>`。
2. `redteam_verify.py` 原本寫 `import extdispatch as ed`,直接綁死來源環境的
   dispatcher。這裡改成依名稱載入(預設值仍是 `extdispatch`,所以來源環境的
   呼叫方式完全沒變),並加上契約檢查。這是本次收錄**唯一的行為性編輯**。
3. 兩份 prompt 的受審目標(一個 commit sha、四個私有專案檔案路徑)換成模板 token。
   `redteam-v2.1-kys.txt` 是同一結構的第三份、指向另一個私有專案,沒有收錄——
   模板化之後它與 `redteam-v2.1.txt` 完全相同,理由記在 manifest。

`test_parser_rulers.py` 裡的 `R509` **保留**:那是一個對等環境 (peer environment)
的代號,不是帳號、路徑或主機名。它讓「這條 parse 規則是誰交過來的」這個宣稱
對持有來源的人仍然可查——依收錄規則,可查證性的識別碼不是清洗目標。

## 與這個 repo 其他部分的關係

| 你可能在找 | 在哪 |
|---|---|
| 方法論全文(量測、樣本數、失效簽章表) | `../claude-ops/ops/references/external-dispatch.md` |
| 派工契約 T5(reviewer ≠ author 的規則面) | `../claude-ops/ops/20-dispatch.md` |
| 收件流程:spot-check → red-team → sign-off | `../claude-ops/ops/10-command-loop.md` |
| 紅隊儀式化的警告、設定變更的紅隊 | `../claude-ops/ops/40-maintenance.md` |
| 唯讀審查 subagent 的定義 | `../agents/engineering-code-reviewer.md` |
| 為什麼一個閘只能對它能判定的事下判斷 | `../tools/README.md`、`../tools/COLLECTION-RULES.md` |

**如果你拿到的是 zip 而不是整個 repo**:交付包裡只放了這個機制跑得起來所需要的
東西——`red-team/` 全部,加上 `claude-ops/ops/references/external-dispatch.md`
(方法論全文)與 `agents/engineering-code-reviewer.md`(本機 reviewer)。上表
其餘的相對連結會指到不存在的檔案,那是**刻意的**:它們是這個 repo 的治理與規則層,
不是這套機制的一部分。要它們就去拿整個 repo。
