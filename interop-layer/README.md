# interop/ — 跨 agent 環境同步層(使用與維運手冊)

> 給人讀的手冊。機器讀的本體:`MIGRATION-MAP.md`(分層地圖)、
> `portable-core.md`(可攜規則唯一源)、`interop.py`(編譯器)、
> `genesis-prompt.md`(機制翻譯)、`acceptance-evals.md`(驗收)。
> 建立於 2026-07-10。哲學脈絡見 `~/.claude/PHILOSOPHY.md`。
> 注意分工:本層只編譯可攜規則給**其他 agent 系統**;要把整個環境
> 搬到另一台機器的 Claude Code,見 `~/.claude/OPERATOR-GUIDE.md`。

## 這是什麼

把 `~/.claude` 的**可攜部分**單向編譯到其他 agent 系統的全域規則檔:

| 目標端 | 生成位置 | 狀態 |
|---|---|---|
| opencode | `~/.config/opencode/AGENTS.md` | **唯一目標端**,profile `full` |

> **2026-08-15 裁定:codex 與 Antigravity 從 registry 整條移除。**
> 兩者自 2026-08-11 起同步關閉,但兩列的路徑與擴充點都還凍結在 2026-07-10
> 的查證結果——而 registry 自己就寫著「目標端位置是易變事實,要重查」。
> Antigravity 的應用程式已於 2026-08-13 確認解除安裝,那列根本無從再驗。
> 「留著是已查證事實」的理由因此反過來:留著的是**過期快照**,不是事實。
> 要重新加回任一個,走下面「新增一個目標 agent 的 checklist」第 1 步
> (查當下官方文件)比信任舊值更快也更安全。移除的原文保存在
> `archive/2026-08-15-interop-targets-removed/`。

> **2026-08-15 裁定:opencode 改吃 `full`**(原為 `light`)。目前只剩它一個
> 啟用目標,所以這條裁定的效果是 `portable-core.md` 的 15 個 block 全部
> 都有人收——在此之前,7 個 `full`-only 的 block 誰都收不到。
>
> 理由是「出生預算 (birth budget)」的論證量過之後反轉了:opencode 根本
> 還沒部署過 AGENTS.md,所以它一直回退去讀 `~/.claude/CLAUDE.md`
> (約 16.5 KB,而且整份都是非 Claude 系統用不上的 Claude Code 專屬機制)。
> 換成 `full`(11,129 B、15 個 block)之後,worker 付的 context 反而**比
> 原本的現狀更少**,不是更多。另一個理由是角色變了:opencode 從偶爾用的
> 側邊工具升成派工目標(免費額度的 worker 執行施工卡、跑跨家族紅隊審查),
> 需要的就是派工端假設它有的那整組偏好。
> 裁定同時記在 `interop.py` TARGETS 的註解與 `ops/rule-registry.md`。

「同步」的定義是**分層單向同步 + 過期偵測**,不是即時雙向鏡像:
指令層機械編譯(真同步)、方法層委派給目標 agent 自行適配(見下)、
機制層 agent 翻譯 + 版本戳(偵測過期後重翻)、
記憶層刻意不同步(跨 CLI 隔離裁決)。

**核心原則(2026-08-11 確立):立場可攜,方法不可攜。**
會搬過去的只有使用者自己的常規偏好——語言規則、git 流程、檔案衛生、
決策授權、環境與 shell 慣例——這些**沒有任何官方文件產得出來**,只能搬。
方法論則相反:它依賴平台機制才能在對的時機被觸發,搬過去只是散文。

**方法層(委派,取代原本的 reference-compile)**:原設計把 skills/ops
的方法論蒸餾成 agent 中性 playbook,編譯到目標端的 `interop-refs/`,
再於 AGENTS.md 尾端注入「情境 → 讀哪個檔」的散文索引。**2026-08-11 退役**
——`MIGRATION-MAP.md` 當初就記下的降級(機械觸發 → 指示閱讀)其實是致命的:
目標平台根本沒有機制能在對的時機叫出那段文字,結果只有「每次都讀」或
「永遠不讀」兩種。約 20K 的 playbook 已移至
`archive/interop-refs-2026-08-11/`(原始正典未動)。

現在改成 `interop.py` 的 `delegation_block()`:告訴目標 agent
上面那些是使用者的常規偏好、原樣適用;需要更深的方法時,**去讀它自己平台
當下的官方文件**找對應的擴充點,並在安裝任何長期性設定前先向使用者提案。
這和 `genesis-prompt.md` 對機制層用的原則是同一條——「你最懂你自己的平台」
——只是延伸到方法層。

**外洩閘門(2026-08-11 新增)**:`build` 會先在記憶體組出所有 payload、
掃過一遍,**全部乾淨才寫**;命中就整批中止、退出碼 1、一個檔都不寫。
`python interop.py scan` 可單獨跑同一道閘門(並額外檢查 portable-core.md
本身)。掃描項目:email、JWT、有前綴的 API key、secret 形狀的賦值、
32 字元以上連續 hex(門檻設在 32 是為了不誤傷來源戳記需要的 git short
hash)、以及路徑中的帳號名。帳號名是**執行時從環境讀取**,不寫死在檔案裡
——寫死的話 `interop.py` 自己就變成外洩源。

## 日常操作(只有四個指令)

```
python ~/.claude/interop/interop.py build     # 重新編譯並部署到所有啟用目標端
python ~/.claude/interop/interop.py status    # 新鮮度報告:誰過期、為什麼
python ~/.claude/interop/interop.py curated   # 記錄「已對照 CLAUDE.md 完成一次策展」
python ~/.claude/interop/interop.py scan      # 只跑外洩閘門,不寫任何檔案
```

**什麼時候跑什麼:**

1. **改了 `portable-core.md`** → 先 commit,再 `build`。
   (不先 commit 也能跑,但版本戳會指向舊 commit,腳本會警告。)
2. **改了全域 `CLAUDE.md`** → 下次 `status` 會提示「策展過期」並列出
   變更的 commit。人工判斷:改動可攜嗎?可攜就同步改 `portable-core.md`
   再 `build`;不可攜(Claude 專屬)就不動。無論哪種,最後跑 `curated`
   蓋章。
3. **不確定現況** → `status`。全綠(exit 0)代表啟用中的目標端與策展都是
   新鮮的;關閉中的目標端一律顯示 `[off]`,不計入 drift。
   `status` 現在也有人替你跑:`hooks/ops_health_nudge.py` 的 check 12 會在
   每次 session 開始時用便宜的 stat 掃一遍(目標檔在不在、是不是本層產的、
   有沒有比來源舊、策展戳有沒有過期),命中就叫你去跑 `status`。
   它是篩子不是權威——真正判定過期的是 `status` 看的 commit,不是 mtime。
4. **新目標端首次部署後 / 機制翻譯後** → 到目標 agent 裡跑
   `acceptance-evals.md` 的驗收(活體證明,沒跑過不算遷移完成)。

## 維運原則(長期營運的不變量)

1. **單向,永遠單向。** `~/.claude` 是唯一正典源;目標端的 AGENTS.md 是
   建置產物,**永不手改**(手改會在下次 build 被覆蓋,且不會回流)。
   在目標 agent 內學到的教訓,回頭改正典源(CLAUDE.md 或
   portable-core.md),再向外編譯。
2. **portable-core.md 是策展物,不是鏡像。** 它是 CLAUDE.md 可攜子集的
   人工蒸餾(agent 中性、全英文、不含 Claude 專屬機制)。兩份文件的語意
   對齊靠「策展迴圈」維持(status 提示 → 人工審 → curated 蓋章),
   不靠機械比對——散文的語意等價本來就無法機械判定。
3. **封存不刪除。** 目標端的既有外來檔會被改名為 `*.pre-interop*.bak`
   保留;genesis 報告永遠開新檔不覆蓋。
4. **降級要留痕。** 機制翻譯時,目標端若沒有等效擴充點,只能降級成文字
   規則——降級是有代價的(機械強制 → 文字期望),genesis 報告必須明寫。
   方法層現在整層都是這種降級,見上方「核心原則」。
5. **出生預算。** 新增 block 前先問:這條規則在目標端真的需要嗎?
   light profile 尤其要守小——輕量工具背大規則集是合規稅。
   block 標 `light` 必須同時標 `full`(light ⊂ full)。
6. **目標端位置是易變事實。** 各家全域規則檔的路徑與機制
   (MIGRATION-MAP.md 的 target registry)會過時;新增目標端或行為異常時,
   先查官方文件再改 registry,不憑記憶。**2026-08-15 起 registry 只留還在
   用的目標端**——凍結超過一個查證週期又沒人重驗的列,留著只會被當成事實
   讀,codex / Antigravity 兩列就是這樣被拔掉的。
7. **不外洩。** 每次 `build` 前都先把全部 payload 掃過一遍;命中即整批
   中止、一個檔都不寫(`scan` 可單獨跑同一道閘門)。

## 新增一個目標 agent 的 checklist

1. 查官方文件:全域規則檔路徑、權限設定、hook/plugin 機制(易變事實,
   必查證)。
2. 在 `MIGRATION-MAP.md` 的 target registry 加一列;在 `interop.py` 的
   `TARGETS` 加一項(路徑 + profile)。
3. `build` → 確認生成檔內容合理。
4. 目標 agent 內跑 `genesis-prompt.md`(機制翻譯)→ 產出 genesis 報告。
5. 目標 agent 內跑 `acceptance-evals.md` → 記錄結果。全過才算完成。

## 已知邊界(不是缺陷,是設計)

- 翻譯層的語意等價無法保證——不同模型對同一段規則的詮釋有差,驗收
  eval 是緩解不是根治;eval FAIL 的處方是強化規則措辭後重測,不是放寬
  eval。
- 記憶(`projects/<slug>/memory/`)與環境事實(`ops/environment.md`)
  各平台各自為政,永不同步。
- Claude Code 的 skill 路由與 ops 派工框架不遷移——它們假設 Claude Code
  的 subagent 機制存在。方法層現在全面委派給目標 agent 自己查當下的官方
  文件,不再嘗試把內容蒸餾搬過去(reference-compile 已於 2026-08-11 退役)。
- **反向依賴(本層單向流動模型沒算到的)**:opencode 會直接掃
  `~/.claude/skills/` 讀取外部 skill,繞過這整套策展 / profile / 外洩閘門
  機制——規則從正典源流出去是受管的,skill 卻是它自己伸手進來拿。
  2026-08-12 以 `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` 關閉,量測與反轉
  兩次的過程見 `MIGRATION-MAP.md` 的 target registry 註解。
