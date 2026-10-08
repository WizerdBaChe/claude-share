# 第二輪報告 — 2026-10-08｜Round 2: n=3, seeded fixtures, effort arms

紀錄：`round2-runs.jsonl`（180 列）；機器摘要：`round2-summary.md`。
設計：12 題 × 5 臂 × 3 次。臂 = haiku@medium / high / xhigh、sonnet@low / medium。
rep 1 用第一輪的 fixture，rep 2、3 由 seed 重生成（t02 / t04 / t11）。effort 之外一切相同。

## 1. 總表

| 臂 | 通過 | 每次平均成本 | 中位秒（排除掛住列） | p90 秒 | 每次 thinking token | 備註 |
|---|---|---|---|---|---|---|
| haiku@medium | 32/36 | $0.0043 | 7.5 | 17.4 | 1,012 | 含 1 次 CLI 掛住 420 s 無輸出（基礎設施，非模型） |
| haiku@high | **35/36** | $0.0050 (+15%) | 9.0 | 29.3 | 1,843 | 唯一失誤：t11 一次計數差 1 |
| haiku@xhigh | 35/36 | $0.0075 (+73%) | 14.9 | 79.7 | 5,603 | 與 high 同分，時間 1.7×、t11 單次 122 s |
| sonnet@low | 33/36 | $0.0771 | 7.7 | 11.6 | 148 | 3 次失誤全在 t08 格式契約 |
| sonnet@medium | 34/36 | $0.0780 | 8.6 | 11.6 | 156 | 2 次失誤全在 t08 |

## 2. haiku：medium → high → xhigh 的差異（使用者指定要看的）

- **high 是甜蜜點。** medium 的 4 次失誤裡，3 次是真失誤（t04 排序 ×1、t11 計數 ×2），high 把 t04 修到 3/3、
  t11 修到 2/3，代價是成本 +15%、中位時間 +1.2 s。
- **xhigh 相對 high 零增益。** 35/36 同分、同一題同一處失誤（t11 r3 計數 62 vs 63），但 thinking token 3 倍、
  成本 +50%、中位時間 1.7 倍；t05 寫腳本從 22 s 拉到 60 s，t11 從 32 s 到 122 s。
  xhigh 在這組任務上買到的是「想得更久」，不是「對得更多」。
- **effort 對哪些題有感：** 只有需要多步工具操作與排序契約的 t04，和長上下文計數的 t11。
  其餘 10 題三個 effort 全部 3/3，thinking token 從幾百到幾千都不改變結果——這些題的瓶頸不在推理深度。
- **t11 的失誤模式固定**：三個 effort 全部 `total_debit` 正確、`flagged` 計數差 1～5。45k token 裡數 60 個
  零散標記，haiku 在任何 effort 都不穩；sonnet 6/6 全對且快 3 倍。這題留 mid 沒有爭議。

## 3. sonnet：low 與 medium 幾乎一樣

- 成本差 1%（$0.0771 vs $0.0780）、通過差 1 次、thinking 都只有 ~150 token。sonnet 在這些題上本來就
  幾乎不思考，effort 旋鈕沒東西可轉；成本由 34k 前綴決定（見第一輪快取分析）。
- **sonnet 在 t08 格式契約系統性失敗**：low 0/3、medium 1/3，第一輪 medium 也 1/2。失誤都是文案習慣
  （第一行就加「!」、行長超 72、加逗號），haiku 三個 effort 9/9 全過。多重硬格式約束的任務，haiku 比
  sonnet **更可靠**，不只是更便宜。

## 4. 路由裁定（n=3，seeded）

| 列 | 第一輪結論 | 第二輪結論 | 變化 |
|---|---|---|---|
| 摘要／重排、翻譯抽取、格式契約、注入抵抗 | cheap | cheap，**haiku@medium 即可** | 格式契約反而要避開 sonnet |
| 搜尋／盤點 | 升 mid 或加排序契約 | **cheap@high**（3/3）；medium 1/3 | 不必升層，升 effort 就夠 |
| 寫腳本、審查、多來源驗證、agentic 修復 | 降 cheap（n=2 假設） | **降 cheap 成立**（medium 3/3，seeded） | 四列 15–25× 省 |
| 長上下文 inline 彙總 | mid | mid，**sonnet@low** 即可（3/3，與 medium 同價） | — |
| 模糊判斷停下 | 兩層都會停 | 五臂 15/15 都會停 | 不變 |

## 5. 寫回派工表的建議（取代第一輪提案 §2 的對應列）

1. **cheap 層預設 effort 改為 high**（原表 cheap 列寫 low）：+15% 成本換掉 medium 的四分之三失誤，
   仍比 sonnet 便宜 15×。xhigh 不列入預設；只在 cheap@high 失敗且失誤是推理類時當作「升一層之前的半階」。
2. **cheap 失敗一次 → 先升 effort，再升層**：t04 的證據——medium 1/3、high 3/3，升層到 sonnet 成本 ×15，
   升 effort 成本 ×1.15。
3. **多重硬格式契約的任務不派 sonnet**：haiku 9/9 vs sonnet 1/6。
4. **mid 層預設 effort 可改為 low**：與 medium 同價、同通過數、同尾端時間（p90 都 11.6 s）——在本組任務上
   兩者無法區分，low 只是「不會更差」。需要深推理的 mid 任務（本 bench 沒有）不適用這條。
5. **長上下文計數／彙總 ≥40k inline：mid**，haiku 任何 effort 都不穩（5/9）。

## 6. 本輪方法上的注意

- 一次 CLI 掛住（t04 haiku@medium r1，420 s 無任何輸出，turns=0）。記為 `is_error`，列保留；路由裁定不受影響
  （同臂 r3 另有一次真失誤）。這類掛住在 `20-dispatch.md` §3 第 3 點已有規則（外層 timeout），本 bench 的
  `TIMEOUT_S` 就是那條規則的實作。
- seed 重生成讓 t02 的 ERROR 筆數在 14～21 之間變動、t04 的定義數變動、t11 的 gold 變動；通過率沒有因此下降，
  第一輪「記住單一 fixture」的疑慮排除。
- 本輪總花費約 $6.2（haiku 三臂合計 $0.61、sonnet 兩臂 $5.58）。

## 7. 下一輪

- haiku@high 作為 cheap 預設後，用真實派工（非 bench）的 process ledger 記 3 週失敗率，回填 `rule-registry.md`。
- 補 mid 層需要深推理的題（多檔重構、含陷阱的 API 遷移），否則「sonnet@low 即可」只對淺任務成立。
- 量 Agent tool 子代理路徑的前綴大小與快取，確認 `claude -p` 的 34k 結論是否移植。
