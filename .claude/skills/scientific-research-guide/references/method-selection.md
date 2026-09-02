# 方法選擇決策輔助（Method Selection Aids）

> 供 Tier 4–5（建模、分析）或任何「該用哪個方法」提問時載入。每張表給的是**判斷準則**，
> 不是照抄答案 — 回覆時務必連同準則（假設、資料型態、任務型態）一起說明，讓使用者能向審稿人辯護。
> 方法的當前規範/期刊要求會變動：遇到具體標準（PRISMA 版本、Nature 圖表規則、套件簽名）時，
> 仍須依 SKILL Gate B 以連網搜尋或本地文件確認，不要只憑本表記憶。

## 1. 統計檢定選擇樹（Statistical Test Selection）

先問四件事，再選檢定：
1. **依變量的測量尺度**？（名義/序數/區間/比例 — 見 tier-framework §0.4）
2. **幾組、是否配對**？（單組 / 兩組獨立 / 兩組配對 / 多組）
3. **分布是否近似常態、變異數是否同質**？（先做 §5.1 EDA 判斷，別預設）
4. **樣本量**？（小樣本或分布未知 → 傾向非參數或 Bootstrap §5.6）

| 情境 | 常態成立 | 常態不成立 / 序數 |
|---|---|---|
| 兩組獨立比較 | 獨立樣本 t 檢定 | Mann-Whitney U / Wilcoxon 秩和 |
| 兩組配對比較 | 配對 t 檢定 | Wilcoxon 符號秩檢定 |
| ≥3 組比較 | 單因子 ANOVA（F 檢定） | Kruskal-Wallis |
| 兩分布是否相同 | — | Kolmogorov-Smirnov / Anderson-Darling |
| 類別 × 類別關聯 | — | Chi-square 卡方（期望次數<5 用 Fisher exact） |
| 兩連續變量相關 | Pearson r | Spearman ρ / Kendall τ |

報告要求（Nature）：單/雙尾、α、**確切 p 值**（非 p<0.05）、效果量（effect size）與 CI。

## 2. 實驗設計選擇（Experimental Design Chooser）

| 需求 | 設計 |
|---|---|
| 單一因子、單位同質 | 完全隨機設計 CRD |
| 已知一個干擾源（批次/場地/日期） | 隨機區塊設計 RBD（把干擾源設為 block） |
| 兩個交叉干擾源、資源有限 | 拉丁方設計 Latin Square |
| 多因子且關心交互作用 | 因子設計 Factorial（2ᵏ 起） |
| 不能隨機分派（觀察型） | 準實驗 + 統計控制（配對/傾向分數/共變量調整） |

三控制原則必到位：隨機化、重複（replication，非 pseudoreplication）、局部控制。明確標出
實驗單元、處理、對照組。

## 3. 抽樣策略（Sampling）

| 研究目的 | 策略 |
|---|---|
| 描述母體/普查估計 | 隨機抽樣（簡單/分層/叢集/系統） |
| 解釋特定機制/深描 | 目的性抽樣 Purposive |
| 稀有母體/滾雪球可及 | 立意 + 滾雪球 Snowball |
| 質性、以飽和為停止準則 | 理論抽樣，收集到 saturation 為止 |

量化研究須做**樣本量/檢定力估計（power analysis）**：給定 α、期望效果量、power(常 0.8)，
反推所需 n。事後才發現 n 不足 → 回 tier-framework §2.4（Gate E）。

## 4. 擬合優度與殘差檢查（Fitting Goodness & Residuals）

- **報告指標**：R²（解釋變異比例，但不懲罰複雜度）、Adjusted R²、RMSE/MAE（同單位誤差）、
  AIC/BIC（跨模型比較，懲罰參數數；BIC 懲罰更重、偏好簡約）。
- **殘差診斷（比單一 R² 更重要）**：殘差對擬合值散點應無結構（無漏斗狀＝異質變異、無曲線＝
  漏了非線性項）；常態 QQ 圖；自相關（時間序列用 Durbin-Watson）。
- 殘差有系統性偏差 → 不是換優化器的問題，是模型設定/假設問題 → 回 tier-framework §4.2。
- 小樣本/分布未知的參數不確定性 → Bootstrap 95% CI（5000 次）勝過假設常態。

## 5. 多重比較校正（Multiple Comparison Correction）

同時做 m 個檢定時，至少一個假陽性的機率 ≈ 1−(1−α)^m，會膨脹。必校正：

| 方法 | 控制對象 | 適用 |
|---|---|---|
| Bonferroni（α/m） | Family-wise error rate | 檢定數少、要求保守（確認性研究） |
| Holm-Bonferroni | FWER，較 Bonferroni 有檢定力 | 一般 FWER 情境優先於純 Bonferroni |
| Benjamini-Hochberg | False Discovery Rate | 大量檢定、探索性（基因組、影像體素） |

省略此步是頂尖期刊最常被點名的統計錯誤之一。

## 6. 效能評估指標（Performance Metrics by Task）

| 任務 | 指標 | 選擇要點 |
|---|---|---|
| 二元分類 | Precision/Recall、F1、AUC-ROC、AUC-PR | 類別不平衡時 AUC-PR、F1 勝過 accuracy/AUC-ROC |
| 多元分類 | macro/micro/weighted F1、混淆矩陣 | 類別不平衡選 macro 看少數類 |
| 影像分割 | Dice(iDSC)、IoU | 閾值須說明依據（如 iDSC>0.5 才算 TP） |
| 迴歸/預測 | R²、RMSE、MAE | RMSE 對大誤差敏感，MAE 對離群穩健 |
| 存活/風險 | C-statistic、AIC/BIC | C-stat 為辨別力（0.5 隨機、1 完美） |
| 校準（機率預測） | Calibration curve、Brier score | 辨別力好 ≠ 校準好，兩者分開報 |

## 7. V&V 與 UQ 檢查清單（Verification, Validation & Uncertainty）

- **Verification（數學一致性）**：數值收斂性（網格/步長細化）、與解析解或製造解（MMS）對照、
  守恆量檢查、單元測試。回答「有沒有正確解出方程」。
- **Validation（現象一致性）**：對照獨立實驗/外部驗證集；區分內部測試集 vs. 外部驗證集，
  兩者不可重疊。回答「模型是否描述了真實世界」。
- **UQ**：參數不確定性推斷（貝葉斯後驗/自助法）並傳播至預測；敏感度分析找對輸出影響最大的參數；
  科學聲明附信賴/可信區間。
- 三者是獨立步驟，不可用「validation 通過」代替 verification，反之亦然。

## 8. 常見統計/方法地雷（Reviewer Red Flags）

- 未做 EDA 直接套參數檢定，事後才發現分布違反假設。
- 未預先定義排除標準，事後選擇性排除（post-hoc exclusion）。
- 多重比較未校正。
- pseudoreplication：把技術重複當生物重複灌大 n。
- 只報 p 值不報效果量與 CI；只報均值±SE 不顯示小樣本個別點。
- 以 R² 高低論斷擬合好壞卻不看殘差。
- validation set 資訊洩漏（前處理/特徵選擇用到了驗證集）。
