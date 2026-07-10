# interop/ — 跨 agent 環境同步層(使用與維運手冊)

> 給人讀的手冊。機器讀的本體:`MIGRATION-MAP.md`(分層地圖)、
> `portable-core.md`(可攜規則唯一源)、`interop.py`(編譯器)、
> `genesis-prompt.md`(機制翻譯)、`acceptance-evals.md`(驗收)。
> 建立於 2026-07-10。哲學脈絡見 `~/.claude/PHILOSOPHY.md`。

## 這是什麼

把 `~/.claude` 的**可攜部分**單向編譯到其他 agent 系統的全域規則檔:

| 目標端 | 生成位置 | Profile |
|---|---|---|
| opencode(輕量任務) | `~/.config/opencode/AGENTS.md` | light(最小集,不背整套框架) |
| codex(目標導向任務) | `~/.codex/AGENTS.md` | full(含判斷框架核心) |
| Antigravity | `~/.gemini/AGENTS.md` | full(Gemini CLI 也會讀到) |

「同步」的定義是**分層單向同步 + 過期偵測**,不是即時雙向鏡像:
指令層機械編譯(真同步)、機制層 agent 翻譯 + 版本戳(偵測過期後重翻)、
記憶層刻意不同步(跨 CLI 隔離裁決)。

## 日常操作(只有三個指令)

```
python ~/.claude/interop/interop.py build     # 重新編譯並部署到所有目標端
python ~/.claude/interop/interop.py status    # 新鮮度報告:誰過期、為什麼
python ~/.claude/interop/interop.py curated   # 記錄「已對照 CLAUDE.md 完成一次策展」
```

**什麼時候跑什麼:**

1. **改了 `portable-core.md`** → 先 commit,再 `build`。
   (不先 commit 也能跑,但版本戳會指向舊 commit,腳本會警告。)
2. **改了全域 `CLAUDE.md`** → 下次 `status` 會提示「策展過期」並列出
   變更的 commit。人工判斷:改動可攜嗎?可攜就同步改 `portable-core.md`
   再 `build`;不可攜(Claude 專屬)就不動。無論哪種,最後跑 `curated`
   蓋章。
3. **不確定現況** → `status`。全綠(exit 0)代表三個目標端與策展都是
   新鮮的。
4. **新目標端首次部署後 / 機制翻譯後** → 到目標 agent 裡跑
   `acceptance-evals.md` 的驗收(活體證明,沒跑過不算遷移完成)。

## 維運原則(長期營運的不變量)

1. **單向,永遠單向。** `~/.claude` 是唯一正典源;目標端的 AGENTS.md 是
   建置產物,**永不手改**(手改會在下次 build 被覆蓋,且不會回流)。
   在 opencode/codex 學到的教訓,回頭改正典源(CLAUDE.md 或
   portable-core.md),再向外編譯。
2. **portable-core.md 是策展物,不是鏡像。** 它是 CLAUDE.md 可攜子集的
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
   (MIGRATION-MAP.md 的 target registry,查證於 2026-07-10)會過時;
   新增目標端或行為異常時,先查官方文件再改 registry,不憑記憶。

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
- Claude Code 的 skills、skill 路由、ops 派工框架不遷移——它們假設
  Claude Code 的 subagent 機制存在。
