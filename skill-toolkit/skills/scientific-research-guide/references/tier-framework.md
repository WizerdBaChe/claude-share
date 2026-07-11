# 科研方法論七層框架（Tier 0→7）

> 自然科學 × 工程科學通用方法論骨架。整合自 Nature Methods、Nature Communications、
> IEEE/Engineering Research Methodology、MIR Framework (NIH PMC)、SciML V&V (arXiv)。
> 用途：供 skill 依 Gate A 定位使用者所在 §N 後載入對應段落，回覆階段精準的方針。
> 各 Tier 非嚴格線性；下游結果可回饋觸發任一上層修正（見 §7.1 與 SKILL Gate E）。

## 目錄 (Table of Contents)
- §0 前置框架 — 問題定義 / 目標 / 理論框架 / 操作化 / 研究類型
- §1 文獻與知識積累 — 系統搜尋 / 篩選 / 品質評估 / 萃取 / 空缺 / 綜合
- §2 研究設計 — 假設 / 實驗設計 / 控制 / 抽樣 / 儀器 / 倫理
- §3 資料蒐集 — 原始 / 二次 / 標注 / 排除 / 品質
- §4 建模 — 選模 / 假設 / 參數 / 訓練校準 / V&V / UQ
- §5 數據分析與擬合 — EDA / 檢定 / 擬合 / 多變量 / 多重比較 / Bootstrap / 指標
- §6 報告與可重現性 — 可重現設計 / 資料代碼開放 / 圖表 / 局限 / 報告結構
- §7 橫切關注 — 迭代 / 模組整合 / 品質標準 / 進度追蹤
- 來源引用

---

## §0 前置框架（Pre-Research Framework）
> 對應 MIR Framework 的 Conceptual Design 階段。來源 PMC5897493。

**0.1 研究問題定義（Problem Formulation）** — 好問題須滿足五條件：(1) 有明確歸屬主體；
(2) ≥2 個可選行動方案；(3) ≥2 種優劣有別的結果；(4) 存在不確定性；(5) 有可解決的環境脈絡。
問題不可過窄、過模糊、爭議過大、或已被過度研究。定義步驟：一般性陳述 → 理解問題本質 →
文獻調查 → 討論精化 → 形成工作命題。

**0.2 研究目標（Research Objective）** — 明確回答 Why（為何做）與 What（要產出什麼知識）；
須在團隊與委託方之間達成共識。研究目的決定後續所有設計決策方向。

**0.3 理論框架選擇** — 理工優先以物理模型（Physical Model）為概念骨架；社會/跨域以理論
（Theory）扮演同等角色。框架功能：提出研究問題、定義概念如何被理解、指引測量方式。

**0.4 概念操作化（Operationalization）** — 抽象概念轉為可量測觀測指標；多維度概念需跨領域
討論各維度加權（Portfolio Approach）。測量尺度：名義/序數/區間/比例（Nominal/Ordinal/
Interval/Ratio）— 此決定 §5 可用的統計方法。操作化完成才能正式提出研究問題與假設。

**0.5 研究類型分類** — 依目的：探索性/描述性/假設檢驗性；依方法：定量/定性/混合；
依性質：基礎/應用/概念性/實驗性。類型影響 §2 設計與 §5 分析路徑。

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
成果直接驅動 §0.1 精化迭代。

**1.6 文獻綜合（Synthesis）** — 敘述性綜合（概念整合、描述知識邊界）；條件允許時做定量整合
（Meta-Analysis，統計整合多研究效果量）。輸出：現有知識地圖與研究方向定位。

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
| 6 | 論文草稿、資料/代碼存儲庫、補充材料 |
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
