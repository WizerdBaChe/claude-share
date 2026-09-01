# Manual-acceptance (UAT) checklist — rank axis, admission gate, item budget

Owner of the `manual-acceptance checklist` record type (`rules-usage-dict.md`
§7). The binding short form is the global CLAUDE.md `[BC]` line; this file is
the axis it points at. Read it when WRITING a checklist, not at session start.

## §0 The failure this exists to stop

User ruling 2026-09-01: 「檢驗項目太容易膨脹，開一堆的檢驗項目等於沒驗」. Item
count is not coverage. A list long enough to be skipped is worse than no list,
because the delivery still reads as verified. The 2026-08 form of this rule
ordered items by SURFACE (UI / API / build) and enforced stress-path parity by
COUNT — a quota, which only ever pushes the count up — and it gave the reader
no safe place to stop. Rank replaces quota: if the list is ordered by
consequence, stopping early is a decision the reader can make correctly, and
the author is the one who has to say which item matters least.

## §1 Shape — properties of the artifact, not habits of the author

Exactly two sections, in this order, with these literal markers:

    A. 必驗（沒過就不能交）    ≤ 7 items
    B. 體驗（過了會更好）      ranked, no hard cap

- **P1** Both markers present, `A` before `B`. An empty section is written as
  the single word `無` — never dropped, so its emptiness is a claim someone made.
- **P2** Items numbered continuously across A and B, so "跑到第幾項" is one number.
- **P3** One item = one concrete action + the expected observation, in one
  numbered step, blind-executable by someone who did not build the thing.
  「檢查排版是否正常」 is not an item; 「視窗拉到 800×600 → 三個按鈕仍在同一列，沒有
  換行」 is.
- **P4** No heading, group, or ordering derived from a module, technology,
  layer, or feature area. Tech grouping is what makes an inflated list look
  organised, which is why it is banned rather than discouraged.
- **P5** A ≤ 7 items (PROVISIONAL, see §5). Overflow means the DELIVERY is too
  big for one acceptance pass → split the pass per milestone. Never raise A to
  fit; never demote a true blocker to B to fit.
- **P6** Descending consequence within each section, so that stopping at any
  line means the most important remaining item was the one just run.
- **P7** Anything only a human eye can judge ships a non-destructive way to be
  shown — a flag, a debug route, a fixture. A check that must mutate the
  artifact to run is not a check, because "再看一眼" then costs more than
  shipping unverified, and it will come back as a user bug report.

## §2 Rank axis for `A. 必驗` — by what breaks, highest first

| Rung | What is at stake | Question that places an item here |
|---|---|---|
| A1 | data & irreversible state | 失敗後能不能自己回到原狀？不能（遺失、覆寫、重複送出、寫壞外部系統）→ A1 |
| A2 | operation & use | 跑得起來嗎？主要流程走得完嗎？（崩潰、卡死、不會結束、主功能等於沒有）|
| A3 | observability | 失敗時看得見嗎？靜默失敗排在維護之上，因為它讓其他每一項的判讀都失效 |
| A4 | maintenance & reproduction | 換一次環境還活著嗎？（重開機、重裝、升級、設定遷移、rollback 路徑）|

Tie-breakers within a rung, in order: 不可逆 > 可逆 · 靜默 > 有聲 · 常走的路 >
罕見路徑 · 中斷／重入／極端輸入 > 同一表面的正路徑.

The last tie-breaker is where the retired stress-path quota now lives (§6).

## §3 Rank axis for `B. 體驗` — by what the user pays, highest first

| Rung | What is at stake |
|---|---|
| B1 | 看得懂 — 使用者知道現在發生什麼、失敗了下一步做什麼（訊息、狀態、空狀態、錯誤文案）|
| B2 | 順手 — 步驟數、預設值、記住上次的選擇、鍵盤與快捷、等待時的回饋 |
| B3 | 觀感 — 版面、對齊、間距、動態、字級 |

B is uncapped because rank already makes it safe to truncate: the reader stops
where they stop, and everything below the stop line was, by construction, the
part worth less than their remaining attention.

## §4 Admission gate — two questions, in this order

1. **機器驗得到嗎？** Yes → it does NOT enter the checklist. It becomes a test
   or a command, and the delivery pastes its output (`10-command-loop.md`
   Step 4: machine-checkable acceptance comes first and is not re-litigated by
   a human). Human lists inflate mostly by absorbing work a machine already did.
2. **失敗了會怎樣？** 不能交 → A（依 §2 定位）· 交得出去但使用者會不爽 → B ·
   兩者皆非 → **不寫**. The third branch is the one that does the actual
   shrinking: an observation nobody would act on is a note, not a check.

**Merge rule** (the shortening tool that is not deletion): two items observed
in the same operation become ONE item with two expected observations. Shorten
by merging, never by dropping a rung.

## §5 The item budget

`A ≤ 7` is PROVISIONAL — a first value, not a measurement. What settles it:
each round where the user reports back, record how many A items were actually
run before they stopped. Tail of A routinely unrun → lower it. A genuinely
needing more than 7 → the delivery was too big (P5), which is a scoping
finding, not a cap problem. Observations append to `rule-registry.md`
key `UAT_A_CAP`.

## §6 Retired: the stress-path count quota (regression case)

Retired form: 「壓力路徑項目數不少於正路徑」. It was a count quota, so it
inflated the list to satisfy itself.

What must still be caught, and how the rank form catches it — a checklist of
six happy-path items with no interruption, re-entry, or extreme-input item:

- If such a path exists in the change, the §2 tie-breaker ranks it ABOVE the
  happy-path item on the same surface, so its absence leaves an A-rung item
  missing → P6 violation.
- If no such path exists, the checklist says so in one line
  (「本次改動沒有可中斷路徑」). Silence is not the same claim as absence, and only
  the written claim can be wrong in a way a reader can catch.

Any future loosening of this rule ships with its own regression case, the same
way this one did.

## §7 Worked example — same delivery, both forms

Before (12 items, grouped by surface — the shape this rule bans):

    UI：1-3　API：4-7　DB：8-9　建置：10-12

After:

    A. 必驗（沒過就不能交）
    1. 匯入 500 筆的檔案 → 中途按取消 → 重開程式，資料庫筆數與匯入前相同（A1，不可逆）
    2. 雙擊 exe 三次 → 工作管理員只有一個行程，視窗被叫到前景（A2，常走的路）
    3. 拔網路 5 分鐘 → 期間送出一筆 → 插回網路 → 恰好收到一則，不重不漏（A1＋中斷路徑）
    4. 故意填錯的設定 → 存檔 → 畫面出現具體錯誤與欄位名，log 有一行 ERROR（A3，靜默失敗）
    5. 重開機 → 自動啟動，托盤圖示是「正常」不是「停止」（A4）
    B. 體驗（過了會更好）
    6. 第一次開啟、還沒有任何資料 → 畫面說明下一步要做什麼，不是空白（B1）
    7. 只在特定條件出現的視窗：用 --preview-dialog 直接叫出來看排版（B3；P7 的免破壞入口）

Twelve items became seven because four were already covered by automated tests
(§4 Q1) and two merged (§4 merge rule) — not because coverage was cut.

## §8 Carriers — every place this rule is written, update together

Grep before editing; do not work from this list alone (`40-maintenance.md` §2
dict-sync corollary).

| File | What it carries |
|---|---|
| `CLAUDE.md` `[BC]` line | the binding short form; the only always-loaded copy |
| `ops/05-authority.md` §4 sec 3 | boundary-contract Acceptance section (supersedes the `[BC]` line at L1/L2 — it must carry the rank or the rule is dead at the level most work runs at) |
| `interop/portable-core.md` `visual-acceptance` | the portable copy — self-contained, no `~/.claude` pointers |
| `agents/engineering-frontend-developer.md` Output | the subagent's output contract |
| `skills/code-review-deep-checklist/SKILL.md` | rendering caveat, own-checklist branch |
| `skills/product-design-thinking/references/document-ladder.md` §7 | handoff checklist |
| `skills/product-design-thinking/references/design-rules.md` | UNIT/SIT/UAT layer split vs item rank |
| `skills/motion-design/local/env-bridge.md` §1 | motion-specific stress paths |
| `skills/model3d-pipeline/SKILL.md` | drawing-sheet checklist template |
| `skills/audience-fit/SKILL.md` Mode B | where UI-copy findings land (B1, or A when a state is hidden) |
| `references/personal-agent-playbook.md` §6 | the zh-TW template people copy |
