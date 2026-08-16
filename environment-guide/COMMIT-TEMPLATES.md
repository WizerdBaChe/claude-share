# COMMIT-TEMPLATES — 本倉庫的 commit 訊息模板

> 依 2026-07-14 為止的實際使用史整理（docs 32 / feat 28 / chore 9 /
> merge 7 / test 2 / fix 2 / refactor 1）。目的：手動 commit 時照抄
> 模板即可，語意與歷史保持一致。
> 基本格式（Conventional Commits）：`type(scope): subject` —
> subject 用祈使句、小寫開頭、結尾不加句點、全英文。
>
> **每個 commit 結尾加 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`**
> —— 使用者裁定 2026-08-15。此前本檔對它保持沉默、而 harness 一直在要求，
> 等於每次 commit 都有一邊被忽略；現在往「保留」這側收斂。裁定之前的 commit
> 混雜有無，**不要回頭改寫歷史**——那會抹掉這個慣例何時開始的唯一紀錄。

---

## 1. Type 選擇表（這個 repo 的語意，不是通用定義）

這是設定倉庫，不是程式專案——「行為」指的是規則/機制對模型行為的
影響。先問：**這個改動會改變模型或 hook 的行為嗎？**

| type | 什麼時候用 | 判斷句 |
|---|---|---|
| `feat` | 新機制、新能力：新 skill、hook 新檢查、新規則機制（如 boundary contract）、skill 新功能段 | 「以前做不到的事，現在做得到了」 |
| `docs` | 規則層**文字**調整、audit trail 條目、thinking-notes、lessons、報告、README、指南 | 「知識/規則的記載變了，機制沒變」（本 repo 大宗） |
| `fix` | 修壞掉的行為：路徑錯誤、hook 誤觸發/漏觸發、規則互相矛盾 | 「之前是錯的，現在對了」 |
| `chore` | 歸檔、退役、搬移、rotate、格式整理 | 「內容沒變，位置/狀態變了」 |
| `test` | eval 執行與結果記錄（skill 評測） | 「跑了驗證並記下證據」 |
| `refactor` | 結構重整、語意不變（拆檔、合併、改編排） | 「讀者看到的規則相同，組織方式變了」 |
| `merge` | 分支收合（特殊格式，見 §3） | — |

邊界案例裁決：
- 規則**新增一條** → 看性質：引入新機制 = `feat`；補充既有機制的文字
  = `docs`。（歷史例：`feat(hooks): add dict-sync drift check` vs
  `docs(ops): add tracer-bullet slicing ... conventions`。）
- skill 的 SKILL.md 改觸發描述 → `docs(skill)`；加新的執行段/reference
  → `feat(skill)`。
- 同批多主題 → **拆成多個語意 commit**，不要塞一顆。

## 2. Scope 慣例（歷史上用過的）

`ops`（ops/ 規則層）、`hooks`、`skill` / `skills`（單一 skill 時
scope 用 `skill`，skill 名字寫進 subject）、`claude-md`（全域
CLAUDE.md）、`notes`（thinking-notes/）、`interop`、`guide`（根目錄
指南類文件）。不確定就省略 scope，subject 講清楚即可。

## 3. 模板（照抄填空）

```
feat(<scope>): add <mechanism> to <where>
docs(<scope>): <verb> <what> [- <one-phrase why>]
docs: audit trail entry for <batch name>
fix(<scope>): <what was broken> <how corrected>
chore(<scope>): archive/retire <what> to <where>
test(skill): run <skill> evals (<N>/<N> pass) and record status
refactor(<scope>): restructure <what>, no behaviour change
merge: <branch-name> - <one-phrase summary>
```

真實範例（取自 git log，可直接模仿）：

```
feat(hooks): add dict-sync drift check to ops health nudge
feat(skill): add cross-session research-state mechanism to scientific-research-guide
docs(ops): trim 30-judgment under size cap + R2 claim-location rules
docs(claude-md): fold thinking-notes/11 principles into engineering-judgement rules (user-approved diff)
docs: audit trail entry for mattpocock/skills fold-in
chore(skill): retire literature-search-extract TODO.md to archive; open items move to FUTURE-WORK.md
test(skill): run scientific-research-guide evals (4/4 pass) and record status
merge: docs/tickets-context-foldin - tracer-bullet + domain glossary fold-in
```

反例（歷史上的違例，不要模仿）：`bug fixed: path adjust` —
沒有 type 前綴、非祈使句，應為 `fix(<scope>): adjust <which> path`。

## 4. 搭配規則（commit 之外的配套動作）

1. **規則層變更必附理由紀錄**：改到 CLAUDE.md / ops/ / skills/ / agents/ /
   hooks/ / settings.json 時，理由要有歸宿 —— 但**不是** `audit-archive/`
   （2026-08-11 凍結，不再接受新條目）。分流：事件本身（哪些檔案何時改、怎麼回滾）
   寫進 commit message；規則的**現行理由**改寫 `ops/rule-registry.md` 的對應條目
   （就地取代，舊值壓進 `history:`）；真的踩到的坑寫 `ops/lessons.md` L-nnn。
2. **Body 何時寫**：subject 永遠必填；body 只在「為什麼」不明顯時加
   （例如 user ruling、取捨理由、驗證證據摘要）。
3. **分支慣例**：一批相關的規則層變更走
   `<type>/<short-name>` 分支（如 `docs/tickets-context-foldin`），
   完成後 `merge --no-ff` 收合，merge commit 用 §3 的 merge 格式。
   單檔零行為變更的小修可直接上 main。
4. **手動使用（可選）**：想讓 git 在編輯器裡預填模板，可建一個
   `.gitmessage` 精簡版並 `git config commit.template ~/.claude/.gitmessage`
   （本機設定，不進版控）。
