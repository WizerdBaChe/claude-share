# Thinking Notes（思考鏈紀錄）

本資料夾收錄 Claude 對自身能力與思考鏈 (chain of thought) 的拆解紀錄——以具體任務為例，
記錄「輸出之前」發生的完整工程過程：需求還原、選型否決、邊界枚舉、心智模擬、驗收自覺。

## 索引

- [01-oneshot-weather-web.md](01-oneshot-weather-web.md) — ONE-SHOT 做出「可選天氣效果展示頁」的完整思考鏈拆解
- [02-oneshot-game-simulation.md](02-oneshot-game-simulation.md) — ONE-SHOT 做出「Minecraft / GTA5 模擬」級 3D 垂直切片的思考鏈；與 01 的選型軸反轉對照
- [03-root-cause-debugging.md](03-root-cause-debugging.md) — 最引以為傲的任務類型：陌生程式碼庫根因追蹤；假說樹＋鑑別實驗的推理紀律，01/02 的反題
- [04-unverifiable-domains.md](04-unverifiable-domains.md) — 回饋會說謊的領域（科研/經濟模型/交易腳本）：先造尺不造產品、假設帳本、重驗證觸發器、對抗過度自信的機制
- [05-system-limits-and-biases.md](05-system-limits-and-biases.md) — 系統規格書：訓練分佈地圖、上下文經濟、自回歸約束、順從偏誤、獎勵駭客傾向
- [06-ask-vs-decide.md](06-ask-vs-decide.md) — 「問還是自己決定」的成本模型：四變數判斷式、兩端墮落形態（假問題/越權）、決定—留痕—繼續
- [07-cross-language-asymmetry.md](07-cross-language-asymmetry.md) — 跨語言思考不對稱：英文推理中文回答的損失與收穫、情態詞信心校準、搜英彙中
- [08-drafts-next-topics.md](08-drafts-next-topics.md) — 草稿（已全部展開，保留作交接紀錄）
- [09-ai-reading-ai.md](09-ai-reading-ai.md) — AI-Reading-AI 信任校準：氣味地圖變平、聲明 vs 證據、執行高於閱讀、跨工件對質、共族盲點的結構性無解
- [10-delegation-economics.md](10-delegation-economics.md) — 委派經濟學：冷啟動稅、上下文防火牆、世界重建包五要件、嵌合體陷阱、同族投票信心虛高
- [11-implementation-capability-gaps.md](11-implementation-capability-gaps.md) — 三方 one-shot 方法論對讀後的缺口盤點：六個明顯缺乏＋五個深度不足＋落地優先序，供環境調整用

## 命名慣例

`NN-短題名.md`，NN 為兩位數流水號。每份文件自成一篇，開頭附任務背景與日期。
