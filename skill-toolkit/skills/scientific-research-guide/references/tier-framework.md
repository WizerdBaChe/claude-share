# 科研方法論七層框架（Tier 0→7）

> 自然科學 × 工程科學通用方法論骨架。整合自 Nature Methods、Nature Communications、
> IEEE/Engineering Research Methodology、MIR Framework (NIH PMC)、SciML V&V (arXiv)。
> 用途：供 skill 依 Gate A 定位使用者所在 §N 後載入對應段落，回覆階段精準的方針。
> 各 Tier 非嚴格線性；下游結果可回饋觸發任一上層修正（見 §7.1 與 SKILL Gate E）。

## 目錄 (Table of Contents)
- §0 前置框架 — 問題定義（含可行性三問）/ 目標 / 理論框架 / 操作化 / 研究類型 / 卡關分類
- §1 文獻與知識積累 — 系統搜尋 / 篩選 / 品質評估 / 萃取 / 空缺 / 綜合
- §2 研究設計 — 假設 / 實驗設計 / 控制 / 抽樣 / 儀器 / 倫理
- §3 資料蒐集 — 原始 / 二次 / 標注 / 排除 / 品質
- §4 建模 — 選模 / 假設 / 參數 / 訓練校準 / V&V / UQ
- §5 數據分析與擬合 — EDA / 檢定 / 擬合 / 多變量 / 多重比較 / Bootstrap / 指標
- §6 報告與可重現性 — 可重現設計 / 資料代碼開放 / 圖表 / 局限 / 報告結構 / 投稿準備 / Story Line 論證路徑自檢
- §7 橫切關注 — 迭代 / 模組整合 / 品質標準 / 進度追蹤
- 來源引用

---

## §0 前置框架（Pre-Research Framework）
> 對應 MIR Framework 的 Conceptual Design 階段。來源 PMC5897493。

**0.1 研究問題定義（Problem Formulation）** — 好問題須滿足五條件：(1) 有明確歸屬主體；
(2) ≥2 個可選行動方案；(3) ≥2 種優劣有別的結果；(4) 存在不確定性；(5) 有可解決的環境脈絡。
問題不可過窄、過模糊、爭議過大、或已被過度研究。定義步驟：一般性陳述 → 理解問題本質 →
文獻調查 → 討論精化 → 形成工作命題。

**可行性三問（Feasibility check，形成工作命題後、進 §0.2 前逐題答是／否）**：
(a) **資料拿得到嗎**——樣品、量測、資料集由誰提供、何時、要什麼權限；
(b) **真的是缺口嗎**——不是「我沒搜到」：文獻端要過 `literature-search-extract` 的 recall check
（扣住一篇已知相關文獻、確認檢索式找得到它）才算「沒人做過」；
(c) **時程與資源做得完嗎**——以現有設備、經費、剩餘時程倒推。
任一題答「否」或「不知道」，先處理那一題，不往下走。來源：researcher.tw 方法論文章〈教授叫你先寫點東西〉
（2026-09-14 讀取，借用帳 B-7）。

**0.2 研究目標（Research Objective）** — 明確回答 Why（為何做）與 What（要產出什麼知識）；
須在團隊與委託方之間達成共識。研究目的決定後續所有設計決策方向。

**0.3 理論框架選擇** — 理工優先以物理模型（Physical Model）為概念骨架；社會/跨域以理論
（Theory）扮演同等角色。框架功能：提出研究問題、定義概念如何被理解、指引測量方式。

**0.4 概念操作化（Operationalization）** — 抽象概念轉為可量測觀測指標；多維度概念需跨領域
討論各維度加權（Portfolio Approach）。測量尺度：名義/序數/區間/比例（Nominal/Ordinal/
Interval/Ratio）— 此決定 §5 可用的統計方法。操作化完成才能正式提出研究問題與假設。

**0.5 研究類型分類** — 依目的：探索性/描述性/假設檢驗性；依方法：定量/定性/混合；
依性質：基礎/應用/概念性/實驗性。類型影響 §2 設計與 §5 分析路徑。

**0.6 卡關分類（只在使用者說「卡住／卡關／寫不下去／做不下去」時啟用）** — 先分類，再給建議；三類的
處方不同，套錯類型的建議等於沒建議（同一來源，借用帳 B-7）：

| 類型 | 徵兆 | 處方 |
|---|---|---|
| 概念還沒成形 | 說不出一句話的研究問題；每次描述都不一樣 | 回 §0.1 五條件＋可行性三問；先寫出一句「想知道 X 在 Y 條件下是否 Z」 |
| 材料不足 | 問題清楚，缺的是資料、文獻、樣品或量測 | 列出缺哪一項、誰能給；文獻缺口交 `literature-search-extract`，資料缺口回 §3 |
| 情緒逃避 | 問題與材料都在，卻遲遲不開始，理由一直在換 | **不是方法問題——直接說出來**；只給一個當天做得完的最小下一步，不再追加方法論 |

**第四類（本環境增補，非上述來源；2026-09-17）——路徑斷了**：徵兆是題目、材料、數據都在，卡的
是「寫出來不通順／講不出為什麼要這樣做／自己讀都覺得跳」。處方不在 §0：走 §6.8 的跳層檢查，先把
七環各寫一句話、逐個相鄰對念 warrant，斷點會自己浮出來。與前三類的分辨法：前三類缺的是**東西**
（問題、材料、動力），這一類東西齊全，缺的是**連接**。

分類結果經使用者同意寫進 `research-state.md` 的「目前阻礙」（≤3 條，每條註明類型與下一個最小動作）。

---

## §1 文獻與知識積累（Literature & Knowledge Base）
> 對應 Engineering Research Methodology 的 Extensive Literature Survey。
> 調用點：本 §1 的搜尋+萃取工作（1.1 搜尋、1.3 品質評估、1.4 萃取、1.6 綜合）可整段委派給
> `literature-search-extract` skill（Mode 2，傳 request contract、接 result contract）；
> 本框架保留方法學判斷（搜尋策略、納入/排除、證據如何回答研究問題）。詳見 SKILL Gate B。

**1.1 系統性文獻搜尋** — 預先定義：關鍵字策略、資料庫範圍、語言限制、時間範圍。主要庫：
Web of Science、IEEE Xplore、PubMed、Scopus、ACM DL。輸出：含檢索式記錄的原始文獻清單。
（若 prism MCP 可用，可用其主題排序/相似節點/引用地圖輔助定位。）

**1.2 篩選與納入/排除標準** — 依 PRISMA 2020 四步：識別 → 篩選 → 資格審查 → 納入；產出
PRISMA 流程圖。標準須在搜尋前預先定義，不可事後調整（否則引入選擇偏差）。

**1.3 文獻品質評估** — 工具：Cochrane RoB、GRADE。面向：隨機化品質、盲化、結果完整性、報告偏差。

**1.4 文獻資訊萃取** — 標準化提取表單，逐篇記錄：研究設計、樣本數、測量方法、主要結果、
統計方法、局限性。

**1.5 研究空缺識別（Gap Analysis）** — 從文獻地圖找：未回答的問題、矛盾結果、未探索的條件。
成果直接驅動 §0.1 精化迭代。工具：`literature-search-extract` 的概念矩陣（Concept matrix；列＝來源、
欄＝概念，Webster & Watson 2002）——空白欄或（概念×系統）空格是**缺口候選**，過了 recall check 才能寫成
「沒有人做過」。

**1.6 文獻綜合（Synthesis）** — 敘述性綜合（概念整合、描述知識邊界）；條件允許時做定量整合
（Meta-Analysis，統計整合多研究效果量）。輸出：現有知識地圖與研究方向定位。敘述性綜合以概念為軸
（沿概念矩陣的欄往下寫），不逐篇摘要——逐篇寫出來的是註解書目，不是綜合。

---

## §2 研究設計（Research Design）
> 對應 MIR Framework 的 Technical Design。

**2.1 假設提出** — 假設連結自變量與依變量的預測陳述；可偽性（Popper）為基本判準。四種來源：
同行討論、資料初探、類似研究回顧、初步田野調查。區分虛無假設(null hypothesis) H₀ 與對立假設(alternative hypothesis) H₁。

**2.2 實驗設計** — 非正式：前後對照 / 後測含對照組。正式：CRD 完全隨機、RBD 隨機區塊、
拉丁方、因子設計（多因子交互作用）。須指定：實驗單元、處理（Treatment）、對照組。
（設計選擇準則見 method-selection.md。）

**2.3 控制變數** — 識別外擾變數，三原則消除偏差：隨機化（機會誤差均勻分布）、重複
（提高統計精確性）、局部控制（主動控制已知干擾源）。注意交絡（Confounding）。

**2.4 抽樣方案** — 描述/清查 → 隨機抽樣；解釋特定現象 → 目的性抽樣。須決定：母體、抽樣策略、
樣本量、飽和準則（Saturation）。樣本量不足是常見的下游致命傷（見 Gate E）。

**2.5 量測儀器設計/選擇** — 類型：物理裝置 / 標準化量表 / 訪談指引 / 資料庫查詢表單。無現成
儀器符合跨領域操作化需求時自行設計。明確觀測者角色：中立外部者 vs. 本身為測量工具一部分。

**2.6 倫理審查** — 須在設計初期處理（非事後）。人體研究依 Belmont Report（受益、公正、尊重）
與 Declaration of Helsinki；另含動物福利、生態影響、數據共享政策、開放存取要求。

---

## §3 資料蒐集（Data Collection）

**3.1 原始資料蒐集** — 觀察法 / 儀器量測法 / 訪談法 / 問卷法。依調查性質、研究目標、資源時間選擇。

**3.2 二次資料蒐集** — 使用已發表資料庫（PANGAEA、European Social Survey、領域公開資料集）。
須記錄：來源、版本、存取時間、使用授權。

**3.3 資料標記/標注** — 對 AI/ML 研究尤其關鍵。須定義：標注類別（含邊界情況規則）、標注人員
資質、標注 SOP、品質控管（多人標注取共識，≥2 名專家）、加速策略（先標 25% → 訓練初始模型 →
以預測輔助後續標注）。

**3.4 排除標準執行** — 資料蒐集同步執行預定義排除準則；避免事後選擇性排除（post-hoc）造成
選擇偏差。

**3.5 資料品質驗證** — 檢查完整性 / 一致性 / 量測品質（解析度、SNR）。影像/訊號類（模糊、
染色失敗、破損）須有明確排除規則。

---

## §4 建模（Modeling）
> 自然科學 × 工程科學交叉核心。來源 Engineering Research Methodology；SciML V&V (arXiv 2502.15496)。

**4.1 模型選擇/架構** — 理學面：物理方程（ODE/PDE）、統計模型、機率圖模型。工學面：半經驗模型、
數值近似（如 Navier-Stokes 數值解）、機器學習（CNN/Transformer）。工程研究特徵：處理「物理已知
但過於複雜無法精確求解」，尋找可解近似。

**4.2 模型假設說明** — 每個模型都有成立前提，須明確列出；假設違反 → 模型失效 → 重選或修正。
這是工程研究 vs. 純科學研究最明顯差異點，也是 §5 擬合失敗時的第一回溯點（Gate E）。

**4.3 參數定義** — 三類：可學習參數（數據驅動）、超參數（研究者設定、影響學習過程）、
固定物理常數（理論決定、不從數據學）。

**4.4 訓練/校準** — ML：損失函數、優化器（如 RAdam）、訓練策略（交叉驗證）。物理模型：
反問題求解、貝葉斯校準。記錄：初始學習率、學習率策略、停止準則、批次大小、訓練輪數。

**4.5 驗證與確認（V&V）** — 驗證（Verification）：模型是否正確求解其數學公式（數學一致性）；
確認（Validation）：模型是否正確描述真實世界（物理/現象一致性）。兩者獨立，不可混淆。
通常需內部測試集 + 外部驗證集。

**4.6 不確定性量化（UQ）** — 推斷參數不確定性並傳播至預測；含敏感度分析（識別對預測影響最大的
參數）。科學聲明中須明確說明預測信賴區間。

**4.7 自建模擬 vs 專業求解器的角色邊界**（2026-09-01 使用者裁定沉澱，SSLD 案）——
研究者/agent 自寫的模擬（解析鏈、簡化數值、自製 angular-spectrum 等）合法角色只有三種：
(a) 可行性與 challenge **背書**（量級正確即可）；(b) 報告佐證；(c) 未來專業模擬的 V&V
正對照錨點。**不得投入資源使其逼近專業求解器**（COMSOL/FDTD/BPM/商用光線追跡）：網格
收斂、材料庫、邊界條件工程是工具成本而非研究貢獻。升級判準：結論將受外部審視（投稿/
廠商/決策門檻）或數字進入規格 → 交給專業工具，自建結果降為 sanity check。此時的正確
交付形＝**模擬計畫書**（deliverables.md T4b）：逐項列待模擬項、推薦軟體（名稱/模組屬
volatile 外部事實，Gate B 查證後才可寫）、V&V 錨點、驗收偏差閾值——把「未來人工以專業
工具檢核」變成可執行規劃。Advisor 端（Gate A/C）遇使用者要求「跑模擬」時，先分流：
背書級自算 vs 專業級開計畫書，不確定 → 問一句，不默默硬算。

---

## §5 數據分析與擬合（Data Analysis & Fitting）
> 來源 Nature Communications s41467-023-36173-0；Nature Methods nmeth.2471。
> 方法選擇的判斷表集中在 method-selection.md；本節給流程與原則。

**5.1 EDA 探索性分析** — 分布描述（均值/中位數/IQR）、視覺化（箱型圖/散點/直方圖/熱圖）、
異常值偵測。**原則：先 EDA 再檢驗**，不要在不了解分布下直接套統計方法。

**5.2 統計假設檢驗** — 依資料類型與分布選檢定（見 method-selection.md 決策樹）。Nature 要求：
說明單/雙尾、顯著水準 α、報告確切 p 值（不只 p<0.05）。α 通常 0.05，高標準領域 0.01/0.001。

**5.3 數據擬合** — OLS / 非線性擬合 / 貝葉斯推斷。必報：擬合優度（R²、RMSE、AIC、BIC）、
殘差分析（是否隨機分布？有無系統性偏差？）。Loess 平滑可用於探索性趨勢。殘差有結構 → 回 §4.2。

**5.4 多變量分析** — 線性迴歸、Cox 比例風險；降維 PCA、對應分析；SEM 同時估計多因果。
模型比較：C-statistic（辨別力）、AIC/BIC（複雜度懲罰）。

**5.5 多重比較校正** — 同時多檢定時 Type-I 錯誤率膨脹必須校正。Bonferroni（保守）/
Benjamini-Hochberg FDR（較寬鬆）。**忽略此步是頂尖期刊審稿最常見的統計錯誤之一。**

**5.6 Bootstrap 信賴區間** — 小樣本或分布未知時優先（勝過假設常態）。標準做法：5000 次重抽樣
取 95% CI。

**5.7 效能評估指標** — 依任務選（見 method-selection.md）：分類 F1/AUC-ROC/Precision-Recall；
分割 Dice(iDSC)/IoU；預測 C-statistic/AIC/BIC；迴歸 R²/RMSE/MAE。閾值設定須說明依據。

---

## §6 結果報告與可重現性（Reporting & Reproducibility）
> 來源 Nature Methods nmeth.2471；Nature 投稿指引。

**6.1 可重現性設計** — 從實驗設計初期就考慮：資料存儲與版本控制、代碼管理（GitHub/Zenodo）、
協議公開（Protocol Exchange）。可重現性是設計的一部分，不是投稿前補救。

**6.2 資料可用性聲明** — 明確存放位置（Figshare/PANGAEA/Zenodo/領域庫）。某些類型（基因組、
結構生物）Nature 強制公開存放。須含 Source Data 支撐圖表數值。

**6.3 代碼可用性聲明** — 自定義軟體須說明：是否公開、存取方式、版本。未提供分析軟體是重現性
障礙主要來源。

**6.4 圖表規範** — 誤差棒須定義類型（SD/SEM/95% CI）；小樣本應顯示個別數據點而非只顯示
均值±誤差棒；n 值精確定義；區分生物重複 vs. 技術重複。

**6.5 局限性討論** — 方法局限（儀器精度、模型假設）、資料局限（樣本代表性、缺失）、可推廣性
局限。誠實討論局限反而增加可信度，是 Nature/Science 審稿重點。

**6.6 報告標準結構** — 見 deliverables.md 完整模板。骨架：Title/Abstract → Introduction
（背景/空缺/目標）→ Methods（Study Design/Data Collection/Statistical Analysis/Software）→
Results（客觀描述，不含解讀）→ Discussion（解讀/與文獻比較/局限）→ Conclusion →
Data & Code Availability → Ethics → References → Extended/Supplementary。

**6.7 投稿準備（Submission Readiness；Tier 6 且使用者準備投稿時才展開）** — 6.1–6.6 讓稿子站得住，
本節讓稿子投對地方、第一關不被退。五步依序，模板見 deliverables.md T6b：
1. **目標期刊短名單（3–5 本，排出投稿順序）**：先統計自己稿件參考文獻的期刊分布（引用最多的期刊＝讀者
   所在）；再用出版社的期刊推薦工具交叉（Elsevier JournalFinder、Springer Nature Journal Suggester、IEEE
   Publication Recommender，貼題目與摘要）；影響因子、CiteScore／SJR 分區、首次決定時間只當參考，不當排序
   的唯一依據；陌生期刊的可信度走 `literature-search-extract` credibility rubric §4（DOAJ／COPE 等）。
2. **Desk reject 自檢（編輯初審三問）**：(a) 範圍——目標期刊近 3 年刊出的文章裡有沒有同類題目（點名 2 篇）；
   (b) 意義——結論只在特定地區／樣品／條件下成立，還是對該刊讀者普遍有用；(c) 新穎性——能否一句話說出
   「相對於 X，本文新增 Y」。任一題答不出來：換刊或改稿，不要硬投。
3. **預印本與自行典藏政策**：先上 arXiv 之前，用 Jisc Open Policy Finder（原 Sherpa Romeo，2024-11 整併）
   查目標期刊是否接受預印本、接受稿能否存放典藏庫與禁止期；資助機構的開放取用要求一併查。
4. **Cover letter 要素**：一句話的核心發現與新穎性（接 2c）；為什麼適合這本期刊（接 2a，點名近年相關文章）；
   未一稿多投、利益衝突、資料可用性聲明；期刊有欄位時附建議／迴避審稿人。
5. **審稿回覆（收到意見後）**：三欄表——審稿意見原文（逐條編號）｜回應（同意並修改／部分同意／不同意＋
   證據）｜稿件修改位置（頁、行）。每一條都回，含「未修改」的；不同意時給證據，不給態度。

來源：researcher.tw〈給第一次投稿的研究生〉〈期刊選擇策略〉（2026-09-14 讀取，二手指引，借用帳 B-4；
使用者 2026-09-14 同意 R1 形狀：不動 SKILL.md、不加觸發詞）。工具名稱與整併日期 2026-09-14 WebSearch 核對；
review-when：任一工具改名或下線。

**6.8 Story Line：論證路徑的寫法與自洽檢查（Tier 6 且使用者在寫稿／改稿時展開；也可在 Tier 0 先立骨架）**

稿子讀起來「不通順」，多半不是句子問題，是**論證路徑（story line）斷了**。Story line 是一條鏈，
七環，每一環帶三樣東西：它回答的問題、讓上一環推得出它的 warrant（理由）、它在稿子裡的落點。

| 環 | 名稱 | 這一環回答 | 理工科的落點與詞彙換算 |
|---|---|---|---|
| 1 | 現象 Observation | 我們觀察到什麼？什麼值得探究？ | Intro 開頭：實測異常、既有元件的效能瓶頸、可重複的製程現象 |
| 2 | 缺口 Gap | 為何重要？現有研究缺什麼？ | Intro 中段；「我沒搜到」不算缺口，要過 §1 的 recall check |
| 3 | 假說／機制 Hypothesis | 為何預期會這樣？依據哪個模型？ | §0.3 理論框架的下游；理工＝物理模型、機制假設、尺度論證 |
| 4 | 方法與可信度策略 Approach | 如何得到結果？為何方法合理？ | Methods。社科的「識別策略 (identification strategy)」＝理工的**量測配置＋控制變因＋模型成立條件**；「識別假設 (identifying assumptions)」＝儀器前提與近似的適用範圍（§2、§4.2） |
| 5 | 證據 Evidence | 發現了什麼？穩不穩？ | Results。社科的「穩健性檢驗 (robustness check)」＝**重複性、誤差棒類型定義（§6.4）、參數掃描、敏感度分析與 UQ（§4.6）** |
| 6 | 詮釋 Interpretation | 結果代表什麼？與文獻異同？限制在哪？ | Discussion ＋ §6.5 局限性 |
| 7 | 貢獻 Contribution | 新增了什麼知識？對誰有影響？ | Conclusion；接 §6.7 步驟 2(c)「相對於 X，本文新增 Y」 |

**寫法——先鏈，後章節。** 七環各寫**一句話**（不是章節標題）；相鄰兩環之間念出 warrant，念不出來
就先補那一環，不要往下展開。七句話站得住，才把每一環展成 §6.6 的章節。這個順序的理由：先有章節
骨架會讓人用「填空」的方式寫，填滿了也可能沒有路徑。

**三個可判定的檢查**（逐條判得出結果，不是態度）：
1. **跳層檢查** — 走完六個相鄰對（1-2, 2-3 … 6-7），每一對念出 warrant。念不出來的那一對就是斷點。
   最常見兩處：2→3（有缺口，沒說為何預期這樣做會補上它）與 5→7（有數據，直接宣稱貢獻，中間沒詮釋）。
2. **孤兒檢查** — 稿子的每一節指回它服務的那一環。指不回去的節＝寫了但不承重，刪掉或降為附錄。
3. **對齊檢查** — 第 7 環宣稱的貢獻，第 5 環有沒有對應證據？第 2 環宣稱的缺口，第 6 環有沒有回收？
   宣稱大於證據的那一條，就是審稿人會抓的那一條（接 §6.7 步驟 2 的 desk reject 自檢）。

**畫出來。** Story line 是鏈狀結構——一環一格、環間標 warrant、斷點留白——畫成方塊圖比讀七段文字
更快看出斷在哪。載體與畫法走 `diagram-authoring`；本節不定義圖型。

**與既有節的關係**：§6.6 給章節骨架，本節給章節之間的**路徑**，互補不重疊；§0.1 五條件自檢管的是
題目站不站得住，本節管的是論述接不接得起來。讀**別人**論文的同一條鏈不歸這裡——那是
來源環境另外兩個論文深讀／論文簡報 skill 的工作，本 share 未收錄。
模板見 deliverables.md T6c。

來源：IG DcoRWkeDbKW〈學術表達的七層結構〉（2026-08-29 貼文；2026-09-17 post-brief 紀錄，存於來源環境、未隨本 share 出貨），二手指引。原文
屬計量經濟／社科體系，第 4、5 環的詞彙已換成理工對應並標明換算，未逐字沿用。使用者 2026-09-17
裁定形狀：核心是 story line **一個物件、分析與產出兩個方向**，產出方向歸本 skill；不動 SKILL.md、
不加觸發詞（沿用 2026-09-14 R1）。review-when：原文的層名或層數被作者改動，或本節的換算詞與某個
domain profile 的用語衝突。

---

## §7 橫切關注（Cross-Cutting Concerns）
> 貫穿全流程，不屬單一步驟。

**7.1 迭代循環** — 各 Tier 非線性。典型觸發：擬合失敗 → 回 §4.2；樣本不足 → 回 §2.4；
文獻發現已有類似研究 → 回 §0.1。對應 SKILL Gate E。

**7.2 模組整合策略** — 跨領域研究須明確整合時機：收斂型（並行後整合）/ 序列型（前模組驅動
後模組）/ 嵌入型（互相依賴、蒐集與分析交織）。未規劃整合易淪為各自獨立子研究，無法回答總問題。

**7.3 科學品質標準** — 三角驗證（多方法/來源交叉確認）、效度（測到的是否真為目標概念）、
信度（重複測量是否一致）、飽和準則（新資料不再產生新洞見）。

**7.4 進度追蹤** — 各 Tier 輸出物清單：

| Tier | 主要輸出物 |
|------|-----------|
| 0 | 研究問題陳述書、概念框架圖 |
| 1 | 文獻清單、PRISMA 流程圖、空缺分析報告 |
| 2 | 研究設計文件、假設清單、倫理審查申請 |
| 3 | 原始資料集、標注文件、排除記錄 |
| 4 | 模型架構文件、訓練記錄、V&V 報告 |
| 5 | 統計分析報告、圖表、效能指標表 |
| 6 | 論文草稿、資料/代碼存儲庫、補充材料、投稿準備（短名單＋desk reject 自檢＋cover letter） |
| 7 | 迭代記錄、整合計畫書 |

---

## 來源引用
- Nature Methods – Enhancing reproducibility: https://www.nature.com/articles/nmeth.2471
- Nature Communications – NGM case study: https://www.nature.com/articles/s41467-023-36173-0
- Engineering Research Methodology (USP): https://edisciplinas.usp.br/pluginfile.php/4125670/mod_resource/content/1/engineering_research_methodology.pdf
- MIR Framework (NIH PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC5897493/
- Nature Methods Content Types: https://www.nature.com/nmeth/content
- Nature Submission Guidelines: https://www.nature.com/documents/nature_3a_initial_revised_submissions.pdf
- SciML V&V Framework (arXiv): https://arxiv.org/html/2502.15496v2
- Jisc — Sherpa services combined into open policy finder: https://www.jisc.ac.uk/news/all/sherpa-services-combined-into-new-user-friendly-platform-open-policy-finder
- Springer Nature — Find the right journal for your manuscript: https://support.springernature.com/en/support/solutions/articles/6000134500-find-the-right-journal-for-your-manuscript
