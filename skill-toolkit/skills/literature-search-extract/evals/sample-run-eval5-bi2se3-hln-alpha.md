# Eval 5 sample run — Bi₂Se₃ WAL HLN α (exhaustive depth)

> Machine-kept sample of a real exhaustive-depth run (2026-07-10, sonnet subagent,
> live web pipeline). Kept as (a) grading evidence for evals.json id 5 and (b) a worked
> example of the exhaustive output contract. Mid-run the agent hit a real usage-limit
> truncation and applied the resilience rules (degradation to Crossref, truncation
> recorded in flow table/gaps, resumable E4 list) — see E1 row 7-8 and Gaps item 1.
> The scientific content below was produced by the run; spot-checked but not
> independently re-verified line-by-line.

---

# 文獻查證報告：Bi₂Se₃ 薄膜 WAL 之 HLN 前置因子 α 值 — 參數表 (parameter sheet)

**深度：exhaustive（PRISMA-style 可追溯搜尋與萃取）**

> **範疇誠實聲明：** 本報告為單一 agent 執行的 PRISMA-style 可追溯搜尋與萃取，**非**完整人工系統性回顧——無雙人獨立篩選、無正式 risk-of-bias 工具、無 meta-analysis。若需可發表的系統性回顧，本產出僅為其搜尋/萃取骨幹。
>
> **執行中斷聲明：** 搜尋於 E1 階段後段遭遇 WebSearch 用量上限 (session limit)，強制截斷。已完成的萃取與查核不受影響；截斷影響範圍已誠實記錄於流程表 (E3) 與 Gaps。

---

## 0. 符號慣例（讀表前必看）

HLN 公式 ΔG(B) = −α·(e²/2π²ℏ)·[ψ(½ + B_φ/B) − ln(B_φ/B)]。**文獻存在兩種等價的正負號慣例**：多數論文將負號寫入公式、報 α<0（單一相干通道 WAL ⇒ α = −1/2）；部分論文（如 Gautam 2022）將負號吸收進公式、報 α>0（單通道 ⇒ α = +0.5）。**下表照原文正負號記錄，不擅自統一**；比較時取 |α|。物理解讀共識：|α| = 0.5 ⇒ 一個相干通道；|α| = 1 ⇒ 兩個完全去耦通道；0.5 < |α| < 1 ⇒ 表面/塊材部分耦合；|α| > 1 或 → 0 為特殊情形（見各列條件）。

## 1. 參數表 (Parameter sheet)

### 1a. 直接讀取之來源（primary extraction）

| parameter | value | unit | conditions | source |
|---|---|---|---|---|
| α (HLN prefactor) | −0.7 → ~−1（隨閘壓連續調變） | 無因次 | 20 nm MBE 薄膜 (Si(111) 基板)，T = 0.3 K，B ⊥ 膜面 ±數 T，V_TG 由 +6 V 掃至 −8 V；V_TG=−8 V 時 α∼−1（頂面與其餘系統去耦） | (Steinberg et al. 2011, PRB 84, 233101; Fig. 3(d) 及正文) [full] |
| α | −0.75（低摻雜 Device B, V_TG=0）；−0.5（高摻雜 Device C） | 無因次 | 同上薄膜；Device B: l_φ = 175 nm；Device C: l_φ = 300 nm, R_H = −3.7 Ω/T, G = 57 e²/h | (Steinberg et al. 2011, Fig. 4(b)) [full] |
| α(T) | regime (ii): −0.75 → ~−1；regime (i): −1 → −1.15；Device C 高溫時 α 上升 | 無因次 | T = 1.5–47 K 溫度掃描；α<−1 解讀為底面亦開始與塊材去耦 | (Steinberg et al. 2011, Fig. 4(d) 及正文) [full] |
| α | −0.31（未摻雜）；−0.35（Pb 摻雜） | 無因次 | 45 QL (~45 nm) MBE 薄膜於 6H-SiC(0001)，T = 500 mK，擬合範圍 −2 kOe < H < 2 kOe；**條件關鍵**：此為 WL+EEI（電子—電子交互作用）聯合擬合，非純 HLN——作者明言偏離預期之 −1/2 | (Wang et al. 2011, PRB 83, 245438; §III-C 正文) [full] |
| α | 0.65 / 0.83 / 1.56（正號慣例） | 無因次 | RF 磁控濺鍍膜，厚度 40 / 80 / 160 nm，T = 2 K，B = −1~+1 T；160 nm 樣品用 modified HLN（外加線性項 λB 扣除古典線性 MR）；作者解讀 α 隨厚度增大 = 表面態與塊材通道逐步去耦/塊材通道增加 | (Gautam et al. 2022, Sci. Rep. 12, DOI 10.1038/s41598-022-13600-8; Fig. 6(d–f) 及正文) [full] |
| α（回顧作者自有數據） | ~−0.5 | 無因次 | 15–60 nm PLD 膜於藍寶石基板，T = 2 K | (Gracia-Abad et al. 2021, Nanomaterials 11, 1077, DOI 10.3390/nano11051077; Table 1) [full] |

### 1b. 經回顧文章彙整之文獻值（[secondary]，出處為該回顧之 Table 1；原始論文未逐一開啟）

以下各列標註「as cited in Gracia-Abad 2021, Table 1」，引用時建議回溯原始文獻核實：

| α value | thickness | temperature | growth | original ref.（依回顧編號） |
|---|---|---|---|---|
| −0.5 | 2–50 nm | 1.6 K | MBE | [13] |
| −1 ~ −0.5 | 20 nm | 0.3–10 K | [not stated] | [14] |
| −0.52 | ~38 nm | 1.8 K | MBE | [30] |
| −0.6 ~ 0.5 | 1–100 nm | 1.5 K | MBE | [31] |
| −0.5 | 5–20 nm | 1.2 K | MBE on SrTiO₃ | [32] |
| −0.6 | 10 nm | 0.4–10 K | [not stated] | [42] |
| −0.6 ~ −0.2 | 7 nm | 2.5 K | 於 SiO₂/Si | [44] |
| −0.6 ~ −0.3 | 1–6 nm | 1.5 K | MBE（超薄極限；<5 QL 時 α 驟降趨 0，因表面態開隙） | [51] |
| −0.55 ~ −0.35 | 6–22 nm | 2 K | [not stated] | [54] |
| −0.56 | 30 nm | 2 K | CVD | [56] |
| −1.08 ~ 0.16 | 9–54 nm | 2–9 K | 磁控濺鍍 | [57] |
| −0.6 | 10–245 nm | 1.5 K | MBE | [64] |
| −0.72 ~ −0.34 | 30–300 nm | 10 K | [not stated] | [67] |
| −0.4 | 9.8–23 nm | 0.3–8 K | [not stated] | [68] |
| −0.5 | 5 nm | 2–20 K | [not stated] | [69] |
| −0.7 ~ −0.6 | 12 nm | 1.6–6 K | [not stated] | [70] |

**`[synthesis]` 全域圖像**：文獻主體落在 |α| ≈ 0.3–1.2；t > 3 QL 的多數樣品 α ≈ −0.5（單一等效相干通道，表面—塊材強耦合）；閘壓去耦、低摻雜或增厚可推向 −1（雙通道）；<5 QL 因雜化開隙 α → 0 並可轉為 WL；含 EEI 修正的聯合擬合 (Wang 2011) 或含線性 MR 修正的 modified HLN (Gautam 2022) 會系統性改變 α 數值——**跨論文比較 α 前必須先確認擬合模型與正負號慣例**。

---

## 2. PRISMA-style 附錄

### E0 — Protocol

- **Question**：Bi₂Se₃ 薄膜弱反局域化 (WAL) 磁導以 HLN 公式擬合時，文獻報導的前置因子 α 之數值、量測/擬合條件與物理解讀。
- **Extraction targets**（P1 清單）：α 數值±不確定度、正負號慣例、膜厚、生長法、溫度、磁場擬合範圍、擬合模型變體（標準 HLN / modified HLN / WL+EEI）、l_φ（若同列報導）、作者對 α 之通道解讀。
- **納入準則**：正式學術來源（期刊/預印本）；材料為 Bi₂Se₃ 薄膜（含輕摻雜 Bi₂Se₃）；報導 HLN α 數值；語言：英文（本領域文獻以英文為主——此為明示之協定決定，記入 §6 語言偏斜檢查）；年代不限。
- **排除代碼**：E1 離題 · E2 錯誤材料/系統（如 Bi₂Te₃、三元化合物）· E3 無可萃取之 α 數據 · E4 無法取得全文/因用量截斷未評估（→ gaps）· E5 重複 · E6 信度不符。
- **計畫資訊源**：WebSearch（scholarly discovery）+ arXiv 全文 + PMC 全文 + Crossref（識別碼與撤稿查核）+ 雙向引文追蹤；prism 本地語料庫（先查一次）。
- **來源總量上限**：使用者指定 ≤10 篇（協定內建 quota）。

### E1 — 搜尋日誌

| # | channel | query / call | hits→篩選 |
|---|---|---|---|
| 1 | prism `list_topics` | （語料庫檢查） | 僅 perovskite / LLM 兩宇宙，無相關 → 跳過 prism |
| 2 | WebSearch | Bi2Se3 thin film weak antilocalization HLN alpha prefactor magnetoconductance | 9 hits, 5 取入 |
| 3 | WebSearch | Hikami-Larkin-Nagaoka fit alpha Bi2Se3 topological insulator thin film | 10 hits, 3 新增 |
| 4 | WebFetch | PMC8143463（回顧全文）；PMC9192768（Gautam 全文） | 兩篇 [full] 萃取成功 |
| 5 | WebSearch ×4 | 針對 He 2011 / Liu 2012 / Wang 2011 / Steinberg 2011 之定位查詢（回顧 Table 1 之反向引文追蹤） | 4 篇原始論文定位成功 |
| 6 | WebFetch | arXiv:1104.1404 (Steinberg)、arXiv:1310.5194 (Wang H. 2014)、arXiv:1008.0141 (He, Bi₂Te₃)、arXiv:1012.0271 (Wang 2011)、arXiv:1103.3353 (Liu 2012) PDF | Steinberg 與 Wang 2011 成功以 [full] 讀畢；Wang H. 2014 改經 PMC 讀取；He 2011 確認為 Bi₂Te₃ (E2)；Liu 2012 PDF 無法解析且未及重試（E4） |
| 7 | WebSearch ×4 | 4 篇載重來源之 retraction 查詢 | **遭遇 session limit — 截斷點** |
| 8 | WebFetch | Crossref `api.crossref.org/works/<doi>` ×4（改道完成撤稿查核） | 4 篇全數乾淨 |

**飽和/截斷聲明**：查詢 #3 起新命中已高度重疊（Gautam、回顧、Steinberg 反覆出現），主題核心文獻呈飽和跡象；但 exhaustive 要求的**逐篇 2-hop 引文追蹤未能完成**（僅完成回顧→原始論文之 1-hop 反向追蹤），截斷肇因為 WebSearch 用量上限，非飽和達成。停止條件：quota（≤10 篇）+ 外部截斷，兩者並記。

### E2 — 兩段式篩選（去重後 15 筆獨立候選）

| 候選 | Pass 1 | Pass 2 | 代碼 |
|---|---|---|---|
| Gracia-Abad 2021 回顧 (Nanomaterials) | 納 | **納入** [full] | — |
| Gautam 2022 (Sci. Rep.) | 納 | **納入** [full] | — |
| Steinberg 2011 (PRB 84, 233101) | 納 | **納入** [full]（arXiv v3 全文） | — |
| Wang 2011 (PRB 83, 245438) | 納 | **納入** [full]（arXiv v2 全文） | — |
| Wang H. 2014 (Sci. Rep. 4, 5817) | 納 | 排除：用 Dugaev-Khmelnitskii 平行場公式，無 HLN α | E3 |
| He 2011 (PRL 106, 166805) | 納 | 排除：材料為 Bi₂Te₃ | E2 |
| Bi₂TeₓSe₃₋ₓ (Sci. Rep. 2020) | 排除：三元系 | — | E2 |
| Liu 2012 (PRL 108, 036805, Cr-Bi₂Se₃) | 納 | 未評估（PDF 不可解析＋截斷） | E4 |
| Chen 2011 (PRB 83, 241304)；Chen 2010 (PRL 105, 176602)；Sci. Rep. srep25291 (2016)；Nanoscale 2016 (c5nr07296d)；JAP 2024 (Cr-doped)；AIP Conf. Proc. 2019；arXiv:1011.1055 | 納（潛在相關） | 未評估（quota + 截斷） | E4 ×7 |

### E3 — 流程統計

| stage | count |
|---|---|
| records identified（WebSearch 8 次查詢 + 1-hop 引文追蹤，去重前） | ~28 |
| duplicates removed（同一論文多入口：PMC/Nature/arXiv/ResearchGate） | ~13 |
| screened (pass 1) | 15 |
| excluded pass 1（E2 ×1：三元系） | 1 |
| assessed (pass 2) | 14 |
| excluded pass 2（E2 ×1；E3 ×1；E4 ×8，其中截斷所致者已標記） | 10 |
| **included** | **4**（+回顧 Table 1 之 16 筆 [secondary] 資料點） |

### E4 — 信度與偏誤檢查

- **撤稿/更正查核**（Crossref `update-to`/`relation`，4 篇載重來源全查）：Gautam 2022、Gracia-Abad 2021、Steinberg 2011、Wang 2011 — **均無撤稿、更正或關切聲明**。
- **Venue tier**：PRB ×2、Sci. Rep. ×1 = Tier A/A−；Nanomaterials (MDPI, DOAJ/Scopus 收錄) = Tier B。四篇皆非預印本（arXiv 版本均已核對對應正式發表版）。
- **Preprint→published**：arXiv:1104.1404 → PRB 84, 233101 ✓；arXiv:1012.0271 → PRB 83, 245438 ✓（引用正式版，實際閱讀為 arXiv 終版）。
- **集合層偏誤**：(1) *引文泡泡*——納入來源有獨立入口（fresh keyword ×2 + 回顧反向追蹤），非單一引用譜系 ✓；(2) *群組集中*——Wang 2011 與回顧 Table 1 之 [14]（疑為同群）、及多筆 MBE 數據集中於清華/中科院 MBE 群（Chang, He, Xue, Ma 合著網絡），**載重之 MBE α 值有中度群組集中風險**，已記入 confidence；(3) *語言偏斜*——僅英文檢索，為明示協定決定（本主題中文文獻多以英文期刊發表），仍列 gaps；(4) *正結果偏斜*——α 偏離 −0.5 之「異常值」（>1、→0）在本集合中有代表（Gautam、回顧 [31][51][57]），未見一面倒。

---

## 3. Gaps

1. **E4 未評估清單（截斷所致，逐筆列名）**：Liu et al., PRL 108, 036805 (2012, Cr-Bi₂Se₃ WAL→WL crossover 之 α)；Chen et al., PRB 83, 241304 (2011, 閘控 α)；Chen et al., PRL 105, 176602 (2010)；Sci. Rep. 6, 25291 (2016, 濺鍍厚度系列)；Nanoscale 2016 (10.1039/c5nr07296d, 多通道耦合)；J. Appl. Phys. 135, 194401 (2024, Cr 摻雜濺鍍)；AIP Conf. Proc. 2115, 030405 (2019)；arXiv:1011.1055。後續 UPDATE run 可由此清單續作。
2. 回顧 Table 1 之 16 筆 [secondary] α 值未逐篇回溯原文核實（原始 DOI 未逐一解析）——引用個別數值前應開啟原文。
3. 逐篇 2-hop forward citation chasing（尋找更正/反駁/複現）未完成。
4. α 之**不確定度（誤差棒）**：所有已讀來源均未在正文/圖說給出 α 的擬合誤差 `[not stated]`——文獻慣例即少報，此為系統性缺口。
5. 僅英文檢索（協定決定）。

## 4. Confidence

| 關鍵主張 | 支持度 | 衝突 |
|---|---|---|
| 多數 Bi₂Se₃ 薄膜 (t>3 QL) HLN α ≈ −0.5（單等效通道） | ≥10 個獨立資料點（4 [full] + 回顧彙整）；回顧本身明言此為文獻常態 | 無 |
| α 可由閘壓/溫度在 −0.5↔−1 間調變（通道去耦） | 2 條獨立證據線（Steinberg 2011 [full]；回顧引 Chen 2011 [secondary]）| Steinberg 正文指出 Chen 2011 將同現象歸因於電子/電洞通道相干長度變化——**機制解讀存在文獻內爭議，未解決**，兩說並記 |
| WL+EEI 聯合擬合下 α 偏小（−0.31/−0.35） | 1 來源 (Wang 2011)，直接擬合；為模型相依值 | 與純 HLN 之 −0.5 表觀不合——非數據衝突，是**擬合模型差異**（該文明示） |
| 厚膜 α 可 >1（濺鍍、需 modified HLN） | 1 來源 (Gautam 2022)，單群組、單製程 | 與 MBE 主流 α≤1 表觀不合；條件（濺鍍多晶、線性 MR 修正）可能解釋 `[synthesis]` |
| <5 QL 時 α→0（開隙、WAL 減弱） | 回顧綜述陳述 + 其引 [51] | 未回溯原文，[secondary] |

## 5. Sources

1. Gracia-Abad, R., Sangiao, S., Bigi, C., Chaluvadi, S.K., Orgiani, P., De Teresa, J.M. (2021). "Omnipresence of Weak Antilocalization (WAL) in Bi₂Se₃ Thin Films: A Review on Its Origin." *Nanomaterials* 11(5), 1077. DOI: 10.3390/nano11051077 — [full]（PMC8143463）；locators: Table 1、正文綜述段。
2. Gautam, S., Aggarwal, V., Singh, B., Awana, V.P.S., Ganesan, R., Kushvaha, S.S. (2022). "Signature of weak-antilocalization in sputtered topological insulator Bi₂Se₃ thin films with varying thickness." *Sci. Rep.* 12. DOI: 10.1038/s41598-022-13600-8 — [full]（PMC9192768）；locators: Fig. 6(d–f)、Results and Discussion。
3. Steinberg, H., Laloë, J.-B., Fatemi, V., Moodera, J.S., Jarillo-Herrero, P. (2011). "Electrically tunable surface-to-bulk coherent coupling in topological insulator thin films." *Phys. Rev. B* 84, 233101. DOI: 10.1103/PhysRevB.84.233101 — [full]（arXiv:1104.1404v3 全文讀畢）；locators: Eq. 1、Fig. 3(d)、Fig. 4(b,d)。
4. Wang, J., DaSilva, A.M., Chang, C.-Z., He, K., Jain, J.K., Samarth, N., Ma, X.-C., Xue, Q.-K., Chan, M.H.W. (2011). "Evidence for electron-electron interaction in topological insulator thin films." *Phys. Rev. B* 83, 245438. DOI: 10.1103/PhysRevB.83.245438 — [full]（arXiv:1012.0271v2 全文讀畢）；locators: Eq. 2、§III-C。
5. （[secondary] 彙整層）Gracia-Abad 2021 Table 1 所引之 refs [13][14][30][31][32][42][44][51][54][56][57][64][67][68][69][70] — 均標註 "as cited in Gracia-Abad 2021"，未逐篇開啟。

## 6. Search trail（摘要）

prism 本地語料庫：已查、無相關宇宙（logged）。WebSearch ×8（含 4 次 retraction 查詢遭 session limit 截斷）；WebFetch：PMC ×3、arXiv PDF ×5、Crossref API ×4（撤稿查核改道完成；Crossref 匿名池，未附 mailto，無個人資源消耗）。降級事件：arXiv PDF 之 WebFetch 文字解析失敗 ×5 → 降級為 Read 工具直接讀 PDF（成功 ×2）；Nature.com 登入牆 → 改 PMC 鏡像（成功）。1-hop 反向引文追蹤（回顧→原始論文）完成；2-hop 未完成（截斷）。
