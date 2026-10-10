# platform-search：外部平台聯合查詢

一次查詢多個外部平台：程式碼、模型庫、實務社群。每個平台各列一區，不混在一起排序。

## 定位

本工具查的是**線索 (leads)**：有沒有人做過、實務上大家怎麼說、該用哪個模型或 LoRA。

論文、預印本、引用關係這類**可引用的證據**不歸這裡，一律交給 `skills/literature-search-extract`。理由是兩邊產出的契約不同（2026-10-04 的決定），同一個平台不該在兩張查詢表裡各寫一份。

各平台的查詢方式、授權、速率限制，以及 robots.txt 對自動存取的態度，都寫在 `ops/references/platform-source-registry.json`。本工具每次執行都會讀它，並把每個平台的狀態印在該區標題上。

## 用法

```git bash
python -X utf8 tools/platform-search/psearch.py query "wan 2.2 low vram" --per-leg 5
python -X utf8 tools/platform-search/psearch.py query "edge coupler" --legs se --se-sites physics,electronics
python -X utf8 tools/platform-search/psearch.py query "lightx2v" --legs reddit --subs comfyui+StableDiffusion
python -X utf8 tools/platform-search/psearch.py reddit-thread <討論串網址>
python -X utf8 tools/platform-search/psearch.py civitai-hash path/to/model.safetensors
python -X utf8 tools/platform-search/psearch.py legs
```

- **預設會查的平台**：github、gh_issues、hf、reddit、hn、se、discourse。
- **要用 `--legs` 指定才查**：civitai（只跟 ComfyUI 素材有關）、qiita（日文）、agy。

## agy 的兩種用法

agy 是 Gemini 加 Google 搜尋的查詢 worker，透過 extdispatch 的 `query` 模式呼叫。Google 有授權索引 Reddit，所以它找得到我們自己連不上的討論串。

| 用法 | 什麼時候觸發 | 怎麼觸發 |
|---|---|---|
| 備援 | Reddit 直接查詢被擋、被限速或達到每日上限 | 自動，不必另外指定；用 `--no-fallback` 關掉 |
| 擴大搜尋 | 使用者說「盡可能更多搜尋」這類話 | `--wide`：預設平台再加 qiita 和 agy，每個平台至少 8 筆 |

使用時要注意：

- agy 回報的網址一律標「unverified」。它是線索，用之前要打開確認。
- 每次呼叫要 1 到 3 分鐘，並佔用 extdispatch 當天的 agy 次數。
- agy 的回答裡如果找不到 JSON 清單，會標成「無法判定」，不會當成 0 筆。

**主要使用者**：本機和其他 session 的 agent。全域 CLAUDE.md 和子代理啟動時的提示 (`hooks/subagent_retrieval_brief.py`) 都指到這個工具。

## 怎麼讀結果

| 顯示 | 意思 |
|---|---|
| `available(0)` | 平台有回應，但這個查詢比對不到。GitHub 和 HF 是逐字比對，長句子常查不到，改用短關鍵字 |
| `unavailable(...)` | **沒問到這個平台**，可能被擋、被限速或網路錯誤。這不代表沒有人討論過 |
| `undetermined(...)` | 程式回傳了不認得的結果，已排除，不會當成查詢結果 |

## 用量限制

使用者裁定 2026-10-04：Reddit RSS 只能**低量、由使用者發起**時使用，不排程、不大量抓取。

每個網站有最短請求間隔和每日上限，紀錄在 `state/hosts.json`（不進 git）：

- 收到 HTTP 429 就停，不重試。
- 正常回應裡如果顯示額度已用完，也會先停，等額度重置再查。

## 驗證

```git bash
python -X utf8 tools/platform-search/controls.py
```

這是離線對照組 (controls)：每個解析器都有一筆正常回應的陽性對照，和一筆封鎖頁或挑戰頁的陰性對照，另外有「無法判定」的情況。第一次執行時，陰性對照就抓到一個缺陷：格式合法的 HTML 封鎖頁原本會被讀成「0 筆」。
