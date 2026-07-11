# interop/ — 跨 agent 環境同步層(使用與維運手冊)

> 給人讀的手冊。機器讀的本體:`<URL>`(分層地圖)、
> `<URL>`(可攜規則唯一源)、`<URL>`(編譯器)、
> `<URL>`(機制翻譯)、`<URL>`(驗收)。
> 建立於 2026-07-10。哲學脈絡見 `~/.claude/<URL>`。

## 這是什麼

把 `~/.claude` 的**可攜部分**單向編譯到其他 agent 系統的全域規則檔:

| 目標端 | 生成位置 | Profile |
|---|---|---|
| opencode(輕量任務) | `~/.config/opencode/<URL>` | light(最小集,不背整套框架) |
| codex(目標導向任務) | `~/.codex/<URL>` | full(含判斷框架核心) |
| Antigravity | `~/.gemini/<URL>` | full(Gemini CLI 也會讀到) |

「同步」的定義是**分層單向同步 + 過期偵測**,不是即時雙向鏡像:
指令層機械編譯(真同步)、方法內容層策展編譯到 `interop-refs/`(見下)、
機制層 agent 翻譯 + 版本戳(偵測過期後重翻)、
記憶層刻意不同步(跨 CLI 隔離裁決)。

**方法內容層(reference-compile)**:skills/ops 的方法論本體是純散文、
可攜,但觸發機制不可攜。做法:人工蒸餾成 agent 中性英文 playbook
(正典放 `interop/refs/`,永不直接複製原始 skill 檔——原檔充滿 Claude
專屬引用),build 時編譯到目標端 <URL> 旁的 `interop-refs/` 資料夾,
並在 <URL> 尾端注入「情境 → 讀哪個檔」的散文索引。已知降級:
機械觸發 → 指示閱讀,命中率天生較低(記錄於 <URL>)。
只掛 full profile;新增 ref 前先過出生預算(<URL> 的 `REFS`)。

## 日常操作(只有三個指令)

```
python ~/.claude/interop/<URL> build     # 重新編譯並部署到所有目標端
python ~/.claude/interop/<URL> status    # 新鮮度報告:誰過期、為什麼
python ~/.claude/interop/<URL> curated   # 記錄「已對照 <URL> 完成一次策展」
```

**什麼時候跑什麼:**

1. **改了 `<URL>`** → 先 commit,再 `build`。
   (不先 commit 也能跑,但版本戳會指向舊 commit,腳本會警告。)
2. **改了全域 `<URL>`** → 下次 `status` 會提示「策展過期」並列出
   變更的 commit。人工判斷:改動可攜嗎?可攜就同步改 `<URL>`
   再 `build`;不可攜(Claude 專屬)就不動。無論哪種,最後跑 `curated`
   蓋章。
3. **不確定現況** → `status`。全綠(exit 0)代表三個目標端與策展都是
   新鮮的。
4. **新目標端首次部署後 / 機制翻譯後** → 到目標 agent 裡跑
   `<URL>` 的驗收(活體證明,沒跑過不算遷移完成)。

## 維運原則(長期營運的不變量)

1. **單向,永遠單向。** `~/.claude` 是唯一正典源;目標端的 <URL> 是
   建置產物,**永不手改**(手改會在下次 build 被覆蓋,且不會回流)。
   在 opencode/codex 學到的教訓,回頭改正典源(<URL> 或
   <URL>),再向外編譯。
2. **<URL> 是策展物,不是鏡像。** 它是 <URL> 可攜子集的
   人工蒸餾(agent 中性、全英文、不含 Claude 專屬機制)。兩份文件的語意
   對齊靠「策展迴圈」維持(status 提示 → 人工審 → curated 蓋章),
   不靠機械比對——散文的語意等價本來就無法機械判定。
3. **封存不刪除。** 目標端的既有外來檔會被改名為 `*.pre-interop*.bak`
   保留;genesis 報告永遠開新檔不覆蓋。
4. **降級要留痕。** 機制翻譯時,目標端若沒有等效擴充點,只能降級成文字
   規則——降級是有代價的(機械強制 → 文字期望),genesis 報告必須明寫。
5. **出生預算。** 新增 block 前先問:這條規則在目標端真的需要嗎?
   light profile 尤其要守小——輕量工具背大規則集是合規稅。
   block 標 `light` 必須同時標 `full`(light ⊂ full)。
6. **目標端位置是易變事實。** 各家全域規則檔的路徑與機制
   (<URL> 的 target registry,查證於 2026-07-10)會過時;
   新增目標端或行為異常時,先查官方文件再改 registry,不憑記憶。

## 新增一個目標 agent 的 checklist

1. 查官方文件:全域規則檔路徑、權限設定、hook/plugin 機制(易變事實,
   必查證)。
2. 在 `<URL>` 的 target registry 加一列;在 `<URL>` 的
   `TARGETS` 加一項(路徑 + profile)。
3. `build` → 確認生成檔內容合理。
4. 目標 agent 內跑 `<URL>`(機制翻譯)→ 產出 genesis 報告。
5. 目標 agent 內跑 `<URL>` → 記錄結果。全過才算完成。

## 已知邊界(不是缺陷,是設計)

- 翻譯層的語意等價無法保證——不同模型對同一段規則的詮釋有差,驗收
  eval 是緩解不是根治;eval FAIL 的處方是強化規則措辭後重測,不是放寬
  eval。
- 記憶(`projects/<slug>/memory/`)與環境事實(`ops/<URL>`)
  各平台各自為政,永不同步。
- Claude Code 的 skill 路由與 ops 派工框架不遷移——它們假設 Claude Code
  的 subagent 機制存在。skill/ops 的方法論「內容」可經 reference-compile
  降級遷移(見上),但觸發永遠是散文索引,不是機械強制。
