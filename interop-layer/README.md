# interop/ — 跨 agent 遷移層｜Cross-agent migration layer

> **中文摘要｜Chinese summary**：本層把可攜的 Core 從 Claude host contract 中抽出，
> 再按目標 surface 寫 Adapter；Integration（MCP、connector、credentials、外部
> 動作與常駐服務）不會從 Claude 設定直接複製。Codex 的檔案式 target、ChatGPT
> 的 import 與 Web package 是三種不同 surface，必須分開驗收。
>
> **English summary**: This layer separates portable Core from Claude host contracts,
> then writes a target-specific Adapter. Integration—MCP, connectors, credentials,
> external actions, and persistent services—is never copied from Claude settings.
> Codex file targets, ChatGPT import, and ChatGPT Web packages are distinct surfaces
> with distinct acceptance evidence.

## 快速導覽｜Quick guide

| 項目 | 中文 | English |
|---|---|---|
| 先讀 | 先讀 MIGRATION-MAP.md，再讀本 README 的 target／package 分界 | Read MIGRATION-MAP.md, then the target/package boundary here |
| 要編譯 | `interop.py build` 只處理 registry 內的檔案式 targets | `interop.py build` handles only file-based targets in the registry |
| 要搬 skill | 先做 Core／Adapter／Integration 盤點，再過 self-contained SKILL fence | Classify Core/Adapter/Integration, then pass the self-contained SKILL fence |
| 要匯入 | ChatGPT import 是使用者控制的 product flow，不回寫本 repo | ChatGPT import is a user-controlled product flow and does not write back here |
| 驗收 | `scan`、`status`、`acceptance-evals.md` 各回答不同問題，不能互相代替 | `scan`, `status`, and acceptance-evals answer different questions |

> 給人讀的手冊。機器讀的本體:`MIGRATION-MAP.md`(分層地圖)、
> `portable-core.md`(可攜規則唯一源)、`interop.py`(編譯器)、
> `genesis-prompt.md`(機制翻譯)、`acceptance-evals.md`(驗收)。
> 建立於 2026-07-10。哲學脈絡見 `~/.claude/PHILOSOPHY.md`。
> 注意分工:本層只編譯可攜規則給**其他 agent 系統**;要把整個環境
> 搬到另一台機器的 Claude Code,見 `~/.claude/OPERATOR-GUIDE.md`。

## 這是什麼｜What this layer does

把 `~/.claude` 的**可攜部分**單向編譯到有檔案式規則入口的 agent 系統；
Codex／ChatGPT 的 skill、plugin 與官方 import 則依目標 surface 另行處理:

| 目標端 | 生成位置 | 狀態 |
|---|---|---|
| opencode | `~/.config/opencode/AGENTS.md` | compiler target, profile `full` |
| Codex | `$CODEX_HOME/AGENTS.md`（未設定時 `~/.codex/AGENTS.md`） | compiler target, profile `full`; `AGENTS.override.md` 會遮蔽它 |
| ChatGPT desktop / Codex CLI import | `Settings > Import` / `/import` | **手動 product flow**, 不由 `interop.py` 寫入 |
| ChatGPT Web | `plugin.json` + `skills/<name>/SKILL.md` | **package surface**, 不生成 global `AGENTS.md` |

> **2026-09-18 更新：Codex 已重新加入 registry。** 2026-08-15 的移除
> 裁定是因為當時的 Codex 路徑與擴充點停留在未重驗的舊快照；本輪已用
> 官方文件重新確認 `~/.codex/AGENTS.md`、`CODEX_HOME` 與
> `AGENTS.override.md` precedence，故現在可安全列為 `full` compiler target。
> 舊裁定仍保留在 `archive/2026-08-15-interop-targets-removed/` 作為歷史，
> 不再代表目前狀態。Antigravity 仍維持退役，不因本輪重驗而恢復。

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
git 歷史（`git show 483435f:archive/interop-refs-2026-08-11/`；原始正典未動）。

現在改成 `interop.py` 的 `delegation_block()`:告訴目標 agent
上面那些是使用者的常規偏好、原樣適用;需要更深的方法時,**去讀它自己平台
當下的官方文件**找對應的擴充點,並在安裝任何長期性設定前先向使用者提案。
這和 `genesis-prompt.md` 對機制層用的原則是同一條——「你最懂你自己的平台」
——只是延伸到方法層。

## Codex／ChatGPT 遷移規則｜Codex/ChatGPT migration rules (2026-09-18)

跨宿主時把資產拆成三層，不要把整份 Claude 設定檔當成 skill payload：

- **Core**：領域目的、決策規則、工作流程、輸出 schema、品質標準、必要
  references／scripts／assets／測試資料。這層通常可重用。
- **Adapter**：工具名稱、路徑、shell/runtime、檔案發現、權限與確認語意、
  metadata、routing 與缺依賴 fallback。這層要按 Codex 或 ChatGPT 重寫。
- **Integration**：MCP server、connector、credential、外部動作與持續服務。
  另行授權、重新登入與縮小 scope；不能從 Claude 設定複製 secrets。

因此採三分類：

1. **原封可攜**：只依賴對話、使用者提供的檔案與通用推理；只需改 metadata
   或封裝。
2. **可攜但需 adapter**：保留 Core，重寫 host contract 與 fallback。
3. **不可直接可攜**：本機 vault／CAD／媒體 pipeline、私有服務、credentials、
   hooks 或持續外部動作；保留 local-only，或拆成 Web 可做的分析 Core 加上
   獨立授權的 remote integration。

### SKILL 依賴範圍閘門｜SKILL dependency fence

本輪只調整遷移規則與 repo 內既有紀錄，**不新增 SKILL 或 plugin**。日後若
真的要搬一個 skill，只接受自包含的單一 `SKILL.md`，以及隨包附上的 repo-local
`references/` 或靜態 assets；這些檔案必須能在包內解析，不得靠未收錄的路徑。

含有必需的其他 tools、可執行 script、hook、MCP／connector、資料庫、私有
vault、外部檔案、遠端服務或常駐 process 的 skill，不在本次搬移範圍；應標成
「不可直接可攜」或延後，等使用者另行授權 integration。這裡的官方文件連結只
是查證來源，不是 skill 的 runtime dependency。現有 `skill-toolkit/` 內容不因
本輪規則更新而複製、拆包或升級。

不可把 `CLAUDE.md`、Claude `settings.json`、hooks、session state、cache、
derived index、MCP credentials、token、cookie、絕對工作站路徑直接塞進
Codex plugin 或 ChatGPT Web skill。缺能力時要寫明缺少什麼與替代方案，不能
刪掉執行步驟後宣稱功能等價，也不能模擬成功。

### Codex 的檔案式目標｜Codex file target

`interop.py build` 只負責產生 Codex 的 portable global preferences；目前
目標是 `$CODEX_HOME/AGENTS.md`，未設定時為 `~/.codex/AGENTS.md`。官方規則中
`AGENTS.override.md` 優先於同層 `AGENTS.md`，project instructions 再由
repo root 向目前目錄合併。若 override 存在，`build` 仍可保留生成檔供日後
移除 override 後使用，但 `status` 必須報 `shadowed`，不能把它算成 live proof。

### ChatGPT 的 package 與 import surface｜ChatGPT package and import surfaces

ChatGPT Web 沒有本層可直接生成的 global `AGENTS.md`。可攜 workflow 應用
skills 或 plugin 發布：最小 skills-only package 是根目錄 `plugin.json` 加上
`skills/<skill-name>/SKILL.md`；Codex／Plugin Creator scaffold 可能另有
`.codex-plugin/plugin.json` compatibility manifest。兩者是 package contract，
不是把 Claude 設定搬過去的理由。

ChatGPT desktop 的 `Settings > Import` 與 Codex CLI 的 `/import` 是另一條
使用者選取的 product flow；它可搬支援的 instructions、settings、skills、
plugins、project folders、memories、chats、MCP config、hooks、slash commands
與 subagents，但不會改動既有 setup。匯入完成後仍要檢查 permission、MCP auth、
hooks、marketplace、prompt 中的 path placeholder；這些匯入結果不回寫本 repo，
也不等於 `interop.py` 已部署。

官方文件（每次新增／恢復 target 前重新核對）：

- [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Import from another agent](https://learn.chatgpt.com/docs/import)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Build plugins](https://learn.chatgpt.com/docs/build-plugins)

**外洩閘門(2026-08-11 新增)**:`build` 會先在記憶體組出所有 payload、
掃過一遍,**全部乾淨才寫**;命中就整批中止、退出碼 1、一個檔都不寫。
`python interop.py scan` 可單獨跑同一道閘門(並額外檢查 portable-core.md
本身)。掃描項目:email、JWT、有前綴的 API key、secret 形狀的賦值、
32 字元以上連續 hex(門檻設在 32 是為了不誤傷來源戳記需要的 git short
hash)、以及路徑中的帳號名。帳號名是**執行時從環境讀取**,不寫死在檔案裡
——寫死的話 `interop.py` 自己就變成外洩源。

## 日常操作｜Daily operations

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

## 維運原則｜Operating invariants

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
   (MIGRATION-MAP.md 的 target registry)會過時;新增、恢復或改動目標端時,
   先查官方文件再改 registry,不憑記憶。凍結超過查證週期又沒人重驗的列,
   要標成歷史或移除；本輪 Codex 是完成重驗後才恢復，不是把舊快照解凍。
7. **不外洩。** 每次 `build` 前都先把全部 payload 掃過一遍;命中即整批
   中止、一個檔都不寫(`scan` 可單獨跑同一道閘門)。
8. **編譯、匯入、發布分開。** `interop.py` 只處理 `TARGETS` 中的檔案式
   規則目標；ChatGPT import 與 plugin／skill 安裝要在目標產品中另做，且
   必須有各自的環境／行為證據。
9. **任何 capability claim 都要有 fallback。** 目標端沒有 shell、local
   filesystem、runtime、connector、MCP 或 hook 時，列出缺口與替代方案，
   不要用另一個 agent 的 tool 名稱假裝通用。

## 新增一個目標 agent｜Add a target agent

1. 查官方文件:全域規則檔路徑、權限設定、hook/plugin 機制與目前支援的
   distribution surface (易變事實,必查證)。
2. 在 `MIGRATION-MAP.md` 的 target registry 加一列;在 `interop.py` 的
   `TARGETS` 加一項(僅限真正的檔案式 compiler target；package/import surface
   只加 migration rule，不要硬塞成一個檔案目標)。
3. `build` → 確認生成檔內容合理。
4. 目標 agent 內跑 `genesis-prompt.md`(機制翻譯)→ 產出 genesis 報告。
5. 目標 agent 內跑 `acceptance-evals.md` → 記錄結果。全過才算完成。
6. 若是 skill/plugin → 先做 Core／Adapter／Integration 盤點，再套用 SKILL
   依賴範圍閘門；只有自包含的 `SKILL.md` 加上隨包 references/assets 才能
   繼續驗 manifest、entry links、缺依賴 fallback 與高影響操作確認。安裝後在
   新 conversation 做代表性測試；需要其他 tools 或資料源的候選項先停在
   「不可直接可攜」，不要為它新增配套 skill。
7. 若是官方 import → 由使用者選取項目並確認 existing setup 未被改動，之後
   逐項 review permission、MCP auth、hooks、marketplace 與 path-dependent
   prompt；不要把 import state commit 回這個 share repo。

## 已知邊界｜Known boundaries by design

- 翻譯層的語意等價無法保證——不同模型對同一段規則的詮釋有差,驗收
  eval 是緩解不是根治;eval FAIL 的處方是強化規則措辭後重測,不是放寬
  eval。
- 記憶(`projects/<slug>/memory/`)與環境事實(`ops/environment.md`)
  在本層的 share/compiler pipeline 中各平台各自為政,永不同步。官方
  product import 若提供 memories/chats 的選取搬移,那是使用者控制的
  product state，不是本 repo 的可發布 artifact。
- Claude Code 的 skill 路由與 ops 派工框架不遷移——它們假設 Claude Code
  的 subagent 機制存在。方法層現在全面委派給目標 agent 自己查當下的官方
  文件,不再嘗試把內容蒸餾搬過去(reference-compile 已於 2026-08-11 退役)。
- `portable-core.md` 不是 ChatGPT Web skill。Web workflow 必須由 Core +
  Adapter + Integration 重新包裝成 skill/plugin，不能把 global preference
  compiler 當成 plugin publisher。
- **反向依賴(本層單向流動模型沒算到的)**:opencode 會直接掃
  `~/.claude/skills/` 讀取外部 skill,繞過這整套策展 / profile / 外洩閘門
  機制——規則從正典源流出去是受管的,skill 卻是它自己伸手進來拿。
  2026-08-12 以 `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` 關閉,量測與反轉
  兩次的過程見 `MIGRATION-MAP.md` 的 target registry 註解。
