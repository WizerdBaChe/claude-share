# 誠實數據與可閱讀性兼顧的技術文件指南

> **目的**：將研究報告、效能比較、技術評估、實驗摘要、審計報告或專案成果文件，改寫為一般讀者可順暢理解的內容；同時保留數據真實性（factual integrity）、不確定性、限制、修正歷程與可追溯性（traceability）。
>
> **核心立場**：可閱讀性不是刪除不利資訊，也不是將複雜結論偽裝成確定結論；它是把「讀者首先需要理解的結論」與「支撐該結論的完整審計材料」安排在不同層次。

---

## 基本原則

```yaml
governing_principles:
  truth_before_simplicity:
    rule: "不得為了容易閱讀而改變數據、因果強度、適用範圍或不確定性。"
    implication: "可簡化表達，但不可把『觀察到』改成『證明』、把『可能』改成『必然』。"

  readability_before_exhaustiveness:
    rule: "正文優先服務理解；完整資料與修正紀錄放入可查閱的附錄。"
    implication: "讀者不必先閱讀所有過程，才能知道目前最可信的結論。"

  final_result_in_main_text:
    rule: "正文呈現已對帳、可追溯的最終數字與目前有效結論。"
    implication: "過時數字、修正過程與逐筆帳目不混入主要敘事。"

  limitations_are_first_class:
    rule: "限制、未驗證項目與無法宣稱的結果，必須明確、可掃讀、可追溯。"
    implication: "限制不可只藏在腳註、附錄或否定句中。"

  traceability_without_interruption:
    rule: "每個重要主張都可追溯，但追溯資訊不應破壞正文節奏。"
    implication: "正文使用短引用或附錄索引；完整檔案路徑、版本與計算式置於附錄。"
```

---

## 文件分責與分層

```yaml
document_responsibilities:
  reader_facing_report:
    purpose: "讓讀者理解研究問題、最終發現、證據強度、實際意義與限制。"
    must_include:
      - "研究問題與比較對象"
      - "一句話主結論"
      - "關鍵發現：發現、證據、意義"
      - "可執行建議或決策含意"
      - "限制與不確定性"
    must_exclude_or_link_out:
      - "逐筆原始記錄"
      - "修正歷史的完整推導"
      - "完整統計輸出、內部檔名與提交識別"

  methods_summary:
    purpose: "讓讀者判斷結果適用範圍與證據強度。"
    must_include:
      - "樣本、分組與比較方式"
      - "量測項目與主要判定規則"
      - "研究時間範圍與環境"
      - "哪些維度有測、哪些沒有測"
    depth: "可理解但不需具備統計或程式實作能力。"

  technical_appendix:
    purpose: "提供進階讀者檢查計算、統計方法與工程實作。"
    must_include:
      - "完整數據表與計算方式"
      - "統計檢定、樣本排除與例外處理"
      - "術語表、代號表與方法細節"
      - "正文主張對應的證據索引"
    rule: "附錄可深入，但不應是理解正文的先決條件。"

  audit_log:
    purpose: "保留研究過程中的發現、錯誤、修正、版本演進與對帳紀錄。"
    must_include:
      - "原值、修正後值、修正原因與影響"
      - "資料品質缺陷與處理決策"
      - "未解決問題與待驗證項目"
      - "原始檔案、版本與再現步驟"
    rule: "審計日誌是誠實性的證據，不是正文的敘事骨架。"

  source_archive:
    purpose: "保存原始輸入、量測輸出、程式、資料表與版本快照。"
    rule: "所有正文的重要數字都必須能回到此層重新檢查。"
```

文件不應在「可讀」與「可查」之間二選一。正確做法是讓正文負責可讀、附錄負責可驗、審計日誌負責完整歷史、來源封存負責可再現。

---

## 正文敘事順序

```yaml
main_report_order:
  section_1_question:
    reader_question: "這份研究想回答什麼？"
    content:
      - "比較或評估的對象"
      - "研究關心的結果指標"
      - "讀者應如何使用這份結果"

  section_2_answer:
    reader_question: "最終答案是什麼？"
    content:
      - "一句話主結論"
      - "結論成立的範圍"
      - "結論不涵蓋的範圍"
    rule: "先給答案，再展開證據。"

  section_3_key_findings:
    reader_question: "哪些證據支持這個答案？"
    content:
      - "3 至 5 項最重要發現"
      - "每項使用『發現 → 證據 → 意義』結構"
    rule: "每項只處理一個核心訊息。"

  section_4_recommendations:
    reader_question: "我該怎麼據此行動？"
    content:
      - "適用情境"
      - "建議行動"
      - "不適用或需額外驗證的情境"

  section_5_limits:
    reader_question: "哪些地方我不能過度解讀？"
    content:
      - "已知限制"
      - "未測量維度"
      - "統計或樣本限制"
      - "尚未定案的問題"

  section_6_methods:
    reader_question: "這些結果怎麼得到的？"
    content:
      - "研究設計摘要"
      - "樣本與測量範圍"
      - "資料品質與驗證措施"

  section_7_traceability:
    reader_question: "我在哪裡可以檢查細節？"
    content:
      - "附錄索引"
      - "審計日誌位置"
      - "資料與程式封存位置"
```

這個順序讓讀者先形成結論地圖，再閱讀證據與限制；而不是先掉進資料清理、對帳、代號與事後修正的歷史裡。

---

## 關鍵發現的最小單位

```yaml
finding_unit:
  required_fields:
    finding: "直接回答一個問題的結論。"
    evidence: "樣本、量測、比較基準與重要數字。"
    interpretation: "數字代表什麼，不能代表什麼。"
    implication: "對讀者選擇、操作或後續研究的意義。"
    boundary: "適用條件、限制或不確定性。"
    trace: "附錄、表格、資料集或審計記錄的位置。"

  writing_template: |
    ### {發現標題}
    **發現**：{一句話結果}。
    **證據**：在{樣本／情境}中，{指標}為{數字}，相較於{基準}為{差異}。
    **意義**：這表示{實際含意}。
    **界線**：此結果只適用於{範圍}；{未測或不確定內容}不能據此推論。
    **追溯**：{附錄或證據索引}。
```

以這個單位寫作時，數字不再是孤立物件：讀者可知道它在比較什麼、代表什麼、以及不能被拿去證明什麼。

---

## 數據誠實規則

```yaml
data_integrity_rules:
  final_values:
    rule: "正文使用已完成對帳的最終值。"
    exception: "若修正本身改變主要結論，正文必須簡述變更與目前狀態。"

  corrections:
    main_text:
      - "說明最終值與結論是否受影響。"
      - "在需要時以一句話交代修正類型，例如『經資料去重與對帳後』。"
    audit_log:
      - "保留原值、修正值、原因、日期、責任者與重算方法。"
      - "保留修正前後是否影響結論的判定。"
    prohibited:
      - "在正文反覆呈現已被撤回或不可追溯的舊數字。"
      - "用『數字未變』掩蓋不同錯誤恰好抵銷的情況。"

  uncertainty:
    rule: "不確定性必須與數字一起呈現，而非只在文末聲明。"
    examples:
      - "樣本數 n"
      - "範圍、分布、中位數或信賴區間"
      - "統計顯著性與效應量"
      - "未能分離的混雜因子（confounders）"

  causal_language:
    observed: "在本資料中，A 與 B 同時出現／呈現差異。"
    associated: "A 與 B 有關聯；研究設計不足以確認因果。"
    causal: "在具控制、對照與足夠證據的前提下，A 導致 B。"
    rule: "用語強度不得超過研究設計能支撐的強度。"

  negative_results:
    rule: "未達顯著、未測得差異、未完成驗證與無法判定，都必須視為結果的一部分。"
    prohibited: "將『沒有證據顯示差異』寫成『證明沒有差異』。"
```

---

## 數字呈現規則

```yaml
number_presentation:
  every_number_needs_context:
    include:
      - "比較對象或基準線"
      - "單位與方向：較高是較好、較差或僅代表較多"
      - "樣本數、時間點或適用範圍"
      - "必要時的變異或不確定性"

  preferred_order:
    - "先說結論或總差異"
    - "再給關鍵數字"
    - "最後提供分解、統計細節與追溯入口"

  translate_multipliers:
    pattern: "{倍率}×"
    reader_form: "相較於基準增加／減少 {百分比}%"
    example: "1.336× = 比基準高 33.6%。"

  statistical_reporting:
    required:
      - "先寫一般語言判讀"
      - "再附 p 值、檢定法、樣本數或效應量"
    template: "此差異在本樣本中{可／不可}與隨機波動區分（{檢定名稱}，n={樣本數}，p={p值}）。"
    caution: "統計顯著不等於實際影響大；未達顯著也不等於沒有差異。"

  ranges:
    rule: "給範圍時，要說明範圍是全距、四分位距、信賴區間或其他定義。"
    recommended: "在有代表性的情況下，同時給典型值，例如中位數。"

  rounding:
    rule: "正文使用符合決策需求的精度；附錄保留原始精度與計算方法。"
    prohibited: "過度四捨五入到改變比較方向、顯著性或風險判讀。"
```

**範例**：不要只寫「成本為 1.722×」。應寫成「在此樣本與設定下，Desktop 的成本比 CLI 高 72.2%；此差異部分與權限模式不同有關，但現有樣本不足以完全分離通道與權限模式的影響。」這保留數值、限制與正確因果強度。

---

## 不確定性與限制寫法

```yaml
limitations_protocol:
  limitation_record:
    required_fields:
      limitation: "缺少什麼資料、控制或驗證？"
      reason: "為什麼會有此限制？"
      affected_claim: "它限制哪一項結論？"
      reader_impact: "讀者應如何調整解讀或行動？"
      status: "已知、修正中、待驗證、無法補救或未定案。"
      trace: "附錄或審計紀錄位置。"

  categories:
    coverage: "樣本、情境、平台、規模或期間未涵蓋。"
    measurement: "儀器只量到某個維度，不能代表整體品質。"
    design: "混雜因子、缺少對照、樣本不足或預先規則未涵蓋。"
    implementation: "資料收集、去重、價格表、工具或流程存在缺陷。"
    interpretation: "結果可描述但不足以推論因果、優劣或可推廣性。"

  main_text_rule: "正文列出會改變讀者決策或結論強度的限制。"
  appendix_rule: "附錄列出完整限制台帳、處理歷程與所有技術細節。"
```

推薦以表格呈現，但每列必須回答「這會影響哪個結論」與「讀者要怎麼解讀」。限制表不是錯誤清單，而是結論的適用邊界。

|限制|影響的結論|讀者應如何解讀|狀態|
|---|---|---|---|
|樣本數不足以完全分離兩個因子|不可將成本差異完全歸因於單一因素|可描述差異，但不宣稱單一原因|已記錄|
|某一維度未進行測試|不可將該測試結果延伸為整體品質保證|需針對該維度額外驗證|待驗證|

---

## 修正與審計資訊寫法

```yaml
correction_protocol:
  classify_correction:
    cosmetic: "不影響數字、分析或結論，例如名稱、格式、拼寫。"
    numeric_nonconsequential: "數字更正，但比較方向與主要結論不變。"
    interpretive: "數字或方法更正，改變某項詮釋、界線或建議。"
    conclusion_changing: "更正後主要結論、推薦或研究問題答案改變。"

  disclosure_location:
    cosmetic: "版本紀錄即可。"
    numeric_nonconsequential: "正文短註 + 附錄完整說明。"
    interpretive: "正文的相關發現中說明 + 附錄完整說明。"
    conclusion_changing: "摘要、主結論、相關段落與審計日誌都必須明確說明。"

  correction_entry:
    fields:
      - "修正識別與日期"
      - "原始說法或原始數值"
      - "修正後說法或數值"
      - "原因與證據"
      - "受影響的圖、表、章節與結論"
      - "重算或驗證方式"
      - "是否改變讀者建議"
```

修正資訊應可被找到，但不應讓正文每一段都變成勘誤公告。正文回答「現在可信的是什麼、這次修正是否改變結論」；審計日誌回答「當時如何錯、如何發現、如何重算」。

---

## 語言轉譯規則

```yaml
language_translation:
  audience_assumption:
    primary: "具基本數字理解與電腦使用經驗，但不預設熟悉研究方法、統計或程式實作。"

  sentence_priority:
    - "先說讀者需要知道的結論"
    - "再說證據"
    - "最後說限制、例外與追溯位置"

  term_policy:
    first_mention: "白話名稱（English term 或縮寫，簡短定義）"
    later_use: "優先使用白話名稱；必要時保留縮寫"
    glossary: "集中保存完整定義、代號對照與方法細節"

  preferred_patterns:
    - "在{範圍}內，{比較對象}呈現{結果}。"
    - "這表示{實際意義}，但不代表{不可推論事項}。"
    - "由於{限制}，目前只能{可成立的結論}。"
    - "若你的情境是{條件}，建議{行動}。"

  avoid_patterns:
    - "用代號、檔名、工具名或內部縮寫作為段落主詞"
    - "先列公式、p 值與乘數，最後才交代問題"
    - "用『未發現』『未達』『不宣稱』代替清楚的結果描述"
    - "將作者的除錯過程直接當成讀者的閱讀流程"

  rewrite_examples:
    audit_first: "事後由檔案回推，原設計未登記組間差異。"
    reader_first: "兩組的權限模式不同，因此無法把觀察到的成本差異完全歸因於使用通道。"

    isolated_number: "成本為 1.722×。"
    interpreted_number: "在此樣本中，成本比基準高 72.2%；現有設計不足以完全確認差異來自哪一個因素。"

    vague_negative: "未達完全分離。"
    explicit_boundary: "樣本數不足以把通道與權限模式的影響分別估計，因此本結果僅描述關聯，不主張單一原因。"
```

---

## 視覺化責任

```yaml
visualization_roles:
  conclusion_card:
    reader_question: "我應先記住什麼？"
    content:
      - "一句話結論"
      - "適用範圍"
      - "最重要限制"
    rule: "不使用裝飾性指標；每個結論都需有證據索引。"

  comparison_chart:
    reader_question: "差異有多大、方向是什麼？"
    content:
      - "清楚的比較基準線"
      - "單位與方向說明"
      - "樣本數與必要的不確定性"
    rule: "圖標題直接說明讀者應讀出的結論。"

  evidence_flow:
    reader_question: "結論如何由資料得到？"
    content:
      - "研究問題"
      - "資料與方法"
      - "結果"
      - "限制"
      - "可採取的行動"
    rule: "呈現推論鏈，而不是工程執行細節。"

  limitation_matrix:
    reader_question: "哪些結論能信到什麼程度？"
    content:
      - "主張"
      - "支持證據"
      - "限制"
      - "解讀強度"
    rule: "以『可描述／可比較／可推論因果／尚不可判定』區分證據強度。"

  audit_timeline:
    reader_question: "重要修正是否影響目前結論？"
    content:
      - "發現問題"
      - "完成修正"
      - "結論是否變動"
    placement: "附錄或版本紀錄；只有重大修正才在正文摘要提及。"
```

圖表不應把所有原始數據壓縮成一張「看起來完整」的圖。每張圖只回答一個問題：差異、流程、證據強度或限制；完整數據仍保留於附錄。

---

## 主張強度矩陣

```yaml
claim_strength_matrix:
  descriptive:
    allowed_when: "有觀察資料，但沒有足夠控制或樣本進行比較推論。"
    wording:
      - "在本樣本中觀察到…"
      - "結果顯示…"
      - "此資料的範圍為…"

  comparative:
    allowed_when: "比較設計與量測一致，可描述組間差異。"
    wording:
      - "相較於…，…較高／較低。"
      - "差異為…；統計判讀為…"

  causal:
    allowed_when: "存在適當控制、識別策略與足夠證據排除主要替代解釋。"
    wording:
      - "在此控制條件下，…導致…"
      - "結果支持…的因果影響。"

  unresolved:
    allowed_when: "資料不足、測試未完成、結果矛盾，或預先規則未涵蓋觀察。"
    wording:
      - "目前無法判定…"
      - "此結果同時支持多種解釋，需額外資料區分。"
      - "不將此觀察歸入既有分類。"
```

寫作時先判定證據能承受哪一級主張，再選擇相符語句。誠實不是每句都加上大量保留語，而是在正確位置使用正確強度的結論。

---

## 改寫工作流程

```yaml
rewrite_workflow:
  step_1_claim_inventory:
    action: "抽取文件中的所有結論、數字、比較、因果說法、限制與修正。"
    output: "主張台帳（claim register）。"

  step_2_verify_status:
    action: "為每個主張標記目前最終值、證據位置、修正狀態與主張強度。"
    output: "已對帳主張清單。"

  step_3_audience_routing:
    action: "判斷每項資訊屬於正文、方法摘要、技術附錄或審計日誌。"
    output: "資訊分流表。"

  step_4_write_answer_first:
    action: "先寫研究問題、一句話答案、關鍵發現與可行建議。"
    output: "可獨立閱讀的正文初稿。"

  step_5_attach_boundaries:
    action: "在每項發現旁補上適用範圍、未測維度、混雜因子與不可推論事項。"
    output: "帶有誠實界線的關鍵發現。"

  step_6_translate_numbers:
    action: "為每個數字補足基準、方向、單位、樣本、意義與必要的不確定性。"
    output: "可判讀的表格與圖表。"

  step_7_build_traceability:
    action: "建立正文主張到附錄、審計日誌與來源封存的單向索引。"
    output: "追溯索引與附錄結構。"

  step_8_reader_and_technical_review:
    action: "分別由非作者讀者檢查可理解性、由技術審查者檢查事實與推論強度。"
    output: "閱讀問題清單與事實校驗紀錄。"

  step_9_publish_with_versioning:
    action: "發布正文、附錄、審計日誌與資料版本；後續修正依 correction_protocol 處理。"
    output: "可讀、可驗、可維護的發布包。"
```

---

## 發布前檢核

```yaml
release_checklist:
  reader_comprehension:
    - "讀者是否能在一分鐘內說出研究問題與主結論？"
    - "讀者是否知道結論適用於哪些條件，以及不適用於哪些條件？"
    - "每個關鍵數字是否有比較基準、方向與意義？"
    - "讀者是否能找到『我該怎麼做』的建議？"

  integrity:
    - "正文是否只使用已對帳的最終值？"
    - "每個重要主張是否可以追溯到證據？"
    - "修正是否依嚴重度揭露，且未隱藏會改變結論的修正？"
    - "限制是否明確指出受影響的結論？"
    - "主張語氣是否沒有超過證據強度？"

  structure:
    - "正文是否先給答案，再給證據、限制與方法？"
    - "原始數據、完整計算與修正歷史是否已移至附錄或審計日誌？"
    - "附錄是否可獨立查核，而不要求所有讀者先閱讀？"

  language:
    - "代號、縮寫與內部工具名稱是否首次出現就被定義？"
    - "是否用清楚的結果描述取代模糊的否定語句？"
    - "是否避免讓讀者沿著作者的除錯歷程才能理解結論？"

  visuals:
    - "每張圖是否只回答一個問題？"
    - "圖表是否清楚標示比較基準、方向、單位與樣本？"
    - "圖表中的主張是否與正文、附錄數字一致？"
```

---

## 最小可用模板

```yaml
minimum_report_template:
  title: "{研究主題}：給讀者的結果摘要"

  one_sentence_answer: "在{研究範圍}內，{主結論}；但{最重要限制}。"

  key_findings:
    - "發現 1：結果 → 證據 → 意義 → 界線 → 追溯"
    - "發現 2：結果 → 證據 → 意義 → 界線 → 追溯"
    - "發現 3：結果 → 證據 → 意義 → 界線 → 追溯"

  reader_actions:
    - "若你的情境是{條件}，建議{行動}。"
    - "若你的情境包含{限制條件}，不要直接套用本結論；請{額外驗證}。"

  study_scope:
    - "比較對象、樣本、時間範圍、量測指標"

  limitations:
    - "限制 → 影響的結論 → 正確解讀 → 狀態 → 追溯"

  traceability:
    - "技術附錄：完整數據、方法與統計"
    - "審計日誌：修正紀錄、缺陷與決策"
    - "來源封存：原始資料、程式與版本"
```

---

## 最終判準

```yaml
success_criteria:
  readable: "未參與研究的讀者能不靠作者解釋，就說出問題、答案、證據、限制與下一步。"
  honest: "任何重要數字、主張、修正與限制都能被定位、追溯、重新檢查，且不被淡化。"
  balanced: "正文不強迫所有人閱讀審計日誌；審計日誌也不因追求易讀而遺失。"
  maintainable: "新資料或修正出現時，可以更新結論、附錄與審計紀錄，而不製造相互矛盾的版本。"
```

真正可靠的技術文件，不是把所有不確定性塞進正文，也不是把所有不利資訊藏到附錄；而是讓讀者先清楚知道「目前最可信的答案」，並且隨時能查到「這個答案憑什麼成立、在哪裡失效、如何被修正」。
