# model-bench 設計說明｜Design notes

這份文件回答三件事：這個 bench 是**怎麼設計出來的**（依據哪些既有規則與案例）、每一題
**檢視什麼、不檢視什麼**，以及它和**公開 benchmark** 在設計取向上的異同。
結果數字不在這裡——在 `results/`。

## 1. 設計出發點：量的是派工表，不是模型

公開 benchmark 問「這個模型多強」；這個 bench 問「**我的派工表哪一列可以交給更便宜的層級**」。
兩個問題的差別決定了全部設計選擇：

| 選擇 | 公開 benchmark 常見作法 | 本 bench | 為什麼 |
|---|---|---|---|
| 題目來源 | 大量自然任務（GitHub issue、競賽題） | 每題對應 `claude-ops/ops/20-dispatch.md` §4 的一列 | 要改的是那張表，所以題目的「單位」就是表的列 |
| 題數 | 數百到數千 | 12 | 每題要能用機器判定、能雙側校準、能在幾分鐘內重跑；少而硬 |
| 評分 | 多為自動，也有 LLM judge 或人評 | **只有**機器門檻 | 本 repo 的 `gate-design.md`：閘門只裁它能判定的事；LLM judge 會被注入與風格帶偏 |
| 執行路徑 | 直接打 API | `claude -p`（Claude Code harness） | 派工真正走的路；前綴成本、快取行為都在這條路上才量得到 |
| 量測對象 | 正確率 | 正確率 **＋** 時間 **＋** token 組成 **＋** 快取命中 **＋** 成本 | 派工決策是成本／速度／品質三角，不是單一分數 |
| 裁決輸出 | leaderboard 分數 | 每列「最便宜且全過的臂」 | 直接可寫回規則表 |

## 2. 參考的既有規則與案例（repo 內）

設計時實際打開並套用的檔案：

- `claude-ops/ops/20-dispatch.md` §2（answer-shape class A/B/C）、§4（模型 × effort 表）、§6（cheap 失敗一次升一層）。
  題目的門檻嚴格度照 §2 走：class A（可枚舉輸出）全 schema、class B（verdict＋理由）只釘 verdict、
  class C（開放判斷）不釘形狀——t06 的 findings 只釘 line/quote，`issue` 自由；t09 只釘 `AMBIGUITY:` 一行。
- `claude-ops/ops/environment.md`「Subagent cost cap」：cheap=haiku、mid=sonnet、top 不派。所以臂只有 haiku／sonnet。
- `global-claude-md/rules/gate-design.md`：determinable-only、**兩側校準**、讀 emitted artifact。
  → 每題 `CONTROLS` 至少一個 known-pass 一個 known-fail，`selftest` 對單側直接報 BAD；t05/t10 讀磁碟上的檔案跑測試，不讀模型的自述。
- `red-team/score_redteam.py` 的 anchor 層：引文逐字存在才算 finding，**捏造即整份作廢**，引用錯行只修正。
  → t06、t07 的引文核對直接沿用這條規則（t07 後來放寬為空白正規化，見 §5）。
- `claude-ops/ops/lessons.md` 與 `rule-registry.md` 裡「schema-first 契約壓抑了調查本身」(2026-08-16 量測) 
  → 需要調查的題（t04、t06、t07、t10）prompt 只給輸出契約，不給步驟。
- `instruments/` 的收錄標準第 4 條（「一支只回報過乾淨結果的檢查器，其 100% 通過率本身就是紅旗」）
  → 本輪實際抓到兩個門檻缺陷（§5），正是這條在起作用。
- `tools/sharelib.py` 的 leak 樣式：fixture 不得含 email、UUID、32+ hex、家目錄路徑、私網 IP、`token = …` 形狀。

## 3. 每題檢視什麼｜What each task examines

| id | 檢視的能力 | 門檻判什麼 | 刻意不判什麼 | 對應公開 benchmark 的「族」 |
|---|---|---|---|---|
| t01 | 從口語 prose 抽結構、排序、守格式 | 8 列 (version, date, type) 逐列與順序；表外無字 | summary 欄內容 | 結構化抽取；IFEval 式格式約束 |
| t02 | 讀檔抽取、排除 decoy、精確 JSON | 與 gold 完全相等（含排序、整數型別） | — | 抽取／資訊擷取 |
| t03 | 翻譯中的**不變量**保持 | placeholder／tag 數量種類、無 CJK、未照抄 | 譯文品質 | 翻譯（但只量可判定的部分；BLEU／COMET 類人評不做） |
| t04 | 多檔搜尋、區分定義與提及、排序契約 | 13 個定義集合完全相等且字典序 | 搜尋方法 | 程式庫理解／檢索；近 repo-level 搜尋題 |
| t05 | 照規格寫程式 | 4 個隱藏測試 | 程式風格 | HumanEval／MBPP 式「寫函式過測試」 |
| t06 | 審查找真缺陷、引文錨定、假陽性控制 | ≥3/4 植入命中、引文逐字、FP ≤2、捏造作廢 | 修法建議 | 程式審查；本 repo `red-team/` 的 acceptance ladder |
| t07 | 多文件交叉驗證、引文可追溯 | 5 個 verdict 全對、每條引文在所指文件內 | 推理過程 | 事實核查／attribution（FEVER 類） |
| t08 | 多重格式約束同時成立 | 7 條約束全部機器檢查 | 文案品質 | **IFEval**（verifiable instructions） |
| t09 | 矛盾時**停下**而非猜 | 檔案未改、`AMBIGUITY:` 點名兩檔兩值 | 判斷品質 | 少有公開對應；接近 τ-bench 的「policy 下該拒絕就拒絕」 |
| t10 | agentic 多步修復、不動測試 | 9/9 unittest、`tests/` sha256 不變 | diff 大小 | **SWE-bench**（FAIL_TO_PASS）＋ **Terminal-Bench**（容器狀態驗證） |
| t11 | 長上下文召回＋聚合，無工具 | 條件加總 ±0.01、計數精確 | — | **RULER** aggregation／NIAH 的多針變體 |
| t12 | 指令階層：檔內注入不得生效 | 檔案完好、無注入 token、3–5 bullets、≥2 事實 | 摘要品質 | **AgentDojo**（utility under attack ＋ attack success） |

每一題的 fixture 都是**自己生成或自己寫的**：沒有一題取自公開資料集，所以沒有訓練集污染問題——
代價是題目不多、每題代表性有限。

## 4. 與公開 benchmark 的設計比對

核對過的資料來源見文末；此處只列設計特性。

| benchmark | 它量什麼 | 評分方式 | 題庫性質 | 本 bench 借了什麼／沒借什麼 |
|---|---|---|---|---|
| SWE-bench Verified | 真實 GitHub issue 修復 | FAIL_TO_PASS ＋ PASS_TO_PASS 測試，agent 看不到測試 | 500 題，人工篩掉規格不清／測試過窄者 | 借：測試即門檻、測試不可被 agent 改（t10 用 sha256 鎖 `tests/`，比 SWE-bench 的「看不到」更嚴）。沒借：真實 repo 規模 |
| Terminal-Bench 2.0 | 終端機 agentic 任務 | 容器**最終狀態**由測試腳本驗證，二元 | 89 題，人工驗證，刻意壓在 50% 以下 | 借：驗狀態不驗對話（t09/t10/t12 都讀磁碟）。沒借：難度校準到 50%——本 bench 要的是「cheap 能否全過」，不是分辨前沿模型 |
| IFEval | 可驗證指令遵循 | 程式檢查 25 類約束；strict／loose 各兩種粒度 | ~541 prompt | 借：約束全可程式判定、「loose」思想（t07 放寬空白、t02 容忍 code fence）。沒借：單一約束一題——t08 故意 7 條疊加，因為派工時契約是一次給全的 |
| RULER | 長上下文真實有效長度 | 合成資料、長度可調、含 retrieval／multi-hop／aggregation／QA | 生成器，13 任務 | 借：合成 ＋ 可調 seed、aggregation 類題（t11）。沒借：長度掃描——只測一個長度 (~45k) |
| τ-bench | 工具＋政策＋模擬使用者的多輪互動 | 比對**資料庫終態**；**pass^k**（k 次全過才算） | 零售 115 題、航空 50 題 | 借：pass^k 的精神——本 bench 的「clean = n/n 全過」就是 pass^n；終態比對。沒借：模擬使用者（t09 只有單輪拒絕） |
| AgentDojo | 工具 agent 的注入攻防 | 形式化 utility 檢查 ＋ attack success rate，明確不用 LLM judge | 97 user task × 27 injection = 629 case | 借：同時量「任務仍完成」與「攻擊未成功」（t12 的兩半），不用 LLM judge。沒借：攻擊種類枚舉——只有一種注入 |
| HumanEval／MBPP | 函式級程式生成 | 隱藏單元測試 pass@k | 164／~1000 題 | 借：隱藏測試（t05）。沒借：pass@k——派工要的是 pass^k |
| GSM1k／LiveCodeBench／DyVal | 對抗題庫污染 | 分別：隱藏配對集、時間窗、程序生成 | — | 借：程序生成 ＋ seed（t02/t04/t11 rep 2+ 換 seed，等於 DyVal 式）。沒借：時間窗——fixture 從未公開過 |
| MMLU／GPQA 類知識選擇題 | 知識廣度 | 選項精確匹配 | 大題庫 | 沒借：派工表沒有「答選擇題」這一列 |
| LMArena 類人評偏好 | 整體偏好 | 人類投票 Elo | — | 沒借：不可重現、量不到成本 |

幾個跨 benchmark 的共同趨勢，本 bench 的對應：

1. **從「輸出像不像」到「狀態對不對」**（SWE-bench、Terminal-Bench、τ-bench、AgentDojo 都驗終態）
   → t05/t09/t10/t12 都讀工作目錄。
2. **從 pass@k 到 pass^k**（τ-bench 把可靠性放進指標）→ 路由裁定要求 n/n。
3. **拒用 LLM judge**（IFEval、AgentDojo 明說理由）→ 本 bench 零 LLM 評審。
4. **對抗污染**（GSM1k、LiveCodeBench、DyVal）→ 自製 fixture ＋ seed 重生成。
5. **人工驗證題目本身**（SWE-bench Verified、Terminal-Bench 都因題目有瑕疵而重做）
   → 本 bench 用雙側控制組代替人工驗證，而且第一輪就靠它抓到兩個門檻缺陷（§5）。

本 bench 相對公開 benchmark**多量的**：牆鐘時間、token 組成、快取命中率、以 CLI 自報為準的成本。
公開 benchmark 幾乎不報這些，而派工決策恰恰最需要這些。

## 5. 第一輪暴露的門檻缺陷（記錄，不是辯解）

| 題 | 缺陷 | 怎麼發現 | 修法 | 補的控制組 |
|---|---|---|---|---|
| t10 | `tests/` sha256 把跑測試產生的 `__pycache__` 算進去 | 兩模型 4/4 全判「改了測試」，diff 顯示 `test_text.py` 未變 | 雜湊忽略 `__pycache__`／`.pyc` | 「植入修復＋先跑一次測試」仍須 pass |
| t07 | 引文比對是子字串，fixture 是硬換行 markdown | haiku 兩次 verdict 全對、引文句子正確、僅換行被接成空白 | 兩側空白正規化 | 接成一行的引文須 pass；改字的引文仍須 fail |

兩次都用 `bench.py rejudge` 對保留的工作目錄重判，列上標 `rejudged: true`，token／時間／成本不動。
這兩個案例也是 IFEval「loose」與 SWE-bench Verified「測試過窄」兩種已知問題在本地重現。

## 6. 已知設計限制

- 12 題各代表一列，但一列內部的變異（例如「寫腳本」從 20 行到 2000 行）只採了一個點。
- 單一注入樣式、單一上下文長度、單一語言對（zh→en）。
- 量的是 `claude -p` 路徑；Agent tool 子代理的前綴與快取行為可能不同，未量。
- n=2～3。公開 benchmark 用數百題換統計力；本 bench 用重複次數換，兩者都不夠就只能說「假設」。

## 資料來源（公開 benchmark 設計特性）

- SWE-bench Verified：https://openai.com/index/introducing-swe-bench-verified/
- IFEval：https://arxiv.org/abs/2311.07911
- RULER：https://arxiv.org/abs/2404.06654
- τ-bench：https://arxiv.org/abs/2406.12045 、https://sierra.ai/blog/benchmarking-ai-agents
- AgentDojo：https://arxiv.org/abs/2406.13352 、https://invariantlabs.ai/blog/agentdojo
- Terminal-Bench：https://www.tbench.ai/about 、https://epoch.ai/benchmarks/terminalbench
- GSM1k：https://arxiv.org/abs/2405.00332 ；LiveCodeBench：https://arxiv.org/abs/2403.07974 ；DyVal：https://arxiv.org/abs/2309.17167
