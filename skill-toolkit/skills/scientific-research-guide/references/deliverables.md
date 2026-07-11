# 各階段輸出物模板與檢查清單（Deliverables & Templates）

> 供 SKILL Gate D 需要「寫文件」時載入。文件預設輸出繁體中文、開新檔（勿覆寫使用者既有研究
> 文件）；文件內的程式碼/設定/prompt 用英文。每份模板都是骨架，依實際研究刪修，不要硬填。

## 使用原則
- 只在使用者要求產出文件、或輸出屬可重用研究資產時才寫檔（診斷/建議用對話回覆即可）。
- 產出前先確認：這份文件對應哪個 Tier、要交給誰看（自己/共同作者/IRB/期刊）。
- 涉及方法選擇的欄位，先依 SKILL Gate B 查證當前標準版本再填。

---

## T0 研究問題陳述書（Research Question Statement）
```
# 研究問題陳述書
## 一句話問題
## 五條件自檢（Problem Formulation）
- 歸屬主體：
- 可選行動方案（≥2）：
- 可能結果與優劣（≥2）：
- 不確定性所在：
- 環境脈絡/可解性：
## 研究目標
- Why（為何做）：
- What（要產出什麼知識）：
## 理論/物理框架
## 概念操作化
| 概念 | 觀測指標 | 測量尺度(名/序/區/比) | 說明 |
## 研究類型（目的/方法/性質）
## 邊界：本研究不做什麼
```

## T1 系統性文獻回顧計畫 + PRISMA（Systematic Review Plan）
```
# 文獻回顧計畫
## 檢索策略（搜尋前定義，不可事後改）
- 研究問題（PICO/PECO 若適用）：
- 關鍵字與布林式：
- 資料庫：Web of Science / IEEE Xplore / PubMed / Scopus / ACM DL
- 語言/時間範圍限制：
## 納入/排除標準
- 納入：
- 排除：
## PRISMA 2020 流程（填數字）
Identification: 檢索得 n=____（去重後 n=____）
Screening:      標題摘要篩除 n=____
Eligibility:    全文評估 n=____，排除 n=____（附理由）
Included:       最終納入 n=____
## 品質評估工具：Cochrane RoB / GRADE
## 資料萃取表欄位：設計 / 樣本數 / 測量 / 主要結果 / 統計方法 / 局限
## 綜合方式：敘述性 / Meta-analysis
## 空缺分析 → 回饋 T0 的精化點
```

## T2 研究設計文件 + 統計分析計畫（Study Design & SAP）
```
# 研究設計文件
## 假設
- H₀：
- H₁：
- 可偽性說明：
## 變量
| 角色 | 變量 | 操作型定義 | 尺度 |
（自變量/依變量/外擾變量/交絡）
## 實驗設計：CRD / RBD / Latin Square / Factorial / 準實驗
- 實驗單元 / 處理 / 對照組：
- 三控制原則落實（隨機化/重複/局部控制）：
## 抽樣方案
- 母體 / 策略 / 樣本量（power analysis: α, effect size, power）/ 飽和準則：
## 量測儀器：類型 / 現成或自製 / 觀測者角色
## 倫理：IRB/Helsinki、動物福利、數據共享、開放存取
## 統計分析計畫（Pre-registered SAP）
- 主要分析：檢定/模型（依 method-selection.md 準則說明選擇）
- 多重比較校正方法：
- 缺失值處理：
- 敏感度分析：
```

## T4 建模與 V&V 報告（Modeling & V&V Report）
```
# 建模與 V&V 報告
## 模型選擇與理由：物理/統計/ML；為何此近似
## 模型假設（逐條列，違反即失效）
## 參數：可學習 / 超參數 / 固定物理常數
## 訓練/校準記錄：損失、優化器、學習率與策略、停止準則、批次、輪數、交叉驗證
## Verification（數學一致性）：收斂性、解析解對照、守恆檢查
## Validation（現象一致性）：內部測試集 vs. 外部驗證集結果
## 不確定性量化 UQ：參數不確定性、傳播、敏感度分析、預測 CI
```

## T5 統計分析報告（Statistical Analysis Report）
```
# 統計分析報告
## EDA：分布描述、視覺化、異常值處理（先於檢驗）
## 假設檢驗：檢定名、單/雙尾、α、確切 p 值、效果量、CI
## 擬合：方法、R²/RMSE/AIC/BIC、殘差診斷結論
## 多變量/降維（如適用）
## 多重比較校正：方法與校正後結果
## 效能指標表（依任務，附閾值依據）
## Bootstrap CI（小樣本/分布未知）
```

## T6 報告與可重現性檢查清單（Reporting & Reproducibility Checklist）
標準論文結構：
```
Title & Abstract
Introduction   — 背景 / 研究空缺 / 研究目標
Methods        — Study Design / Data Collection / Statistical Analysis / Software & Tools
Results        — 客觀描述發現，不含解讀
Discussion     — 解讀 / 與文獻比較 / 局限性
Conclusion     — 核心貢獻再陳述
Data Availability Statement
Code Availability Statement
Ethics Statement
References
Extended Data / Supplementary Materials
```
投稿前逐項自檢：
- [ ] 資料可用性聲明：存放位置（Figshare/PANGAEA/Zenodo/領域庫）＋ Source Data
- [ ] 代碼可用性聲明：是否公開、存取方式、版本
- [ ] 圖表：誤差棒類型已定義（SD/SEM/95% CI）；小樣本顯示個別點
- [ ] n 值精確定義；生物重複 vs. 技術重複已區分
- [ ] 統計：確切 p 值、效果量、CI、多重比較校正皆已報告
- [ ] 局限性：方法 / 資料 / 可推廣性三面向誠實討論
- [ ] 倫理聲明與核准編號
- [ ] 可重現性：數據版本控制、代碼倉庫、協議公開

## T7 迭代記錄與整合計畫（Iteration Log & Integration Plan）
```
# 迭代記錄
| 日期 | 觸發（哪個下游結果）| 回溯到哪個 Tier | 修正內容 | 結果 |
# 模組整合計畫（跨領域研究）
- 整合型態：收斂 / 序列 / 嵌入
- 各子模組整合時機與介面：
- 品質標準：三角驗證 / 效度 / 信度 / 飽和
```
