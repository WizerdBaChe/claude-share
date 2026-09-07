# Task context — the card the walk is only as true as

> Loaded by ux-walkthrough Step 1. Template borrows the GOV.UK Service
> Manual user-need form ("Learning about users and their needs", read
> 2026-09-07) and its evidence rule; variants and the 「哪個視窗」 check are
> this environment's own measured cases.

## The evidence rule (GOV.UK, applied as written)

「Treat any opinions or suggestions that do not come from users as
assumptions that have to be proven by doing research.」 A card line the
builder wrote from the code is an assumption until a log, a ruling, an
observed session, or the user's own words backs it. Mark every line:

- **已確認** — user ruling, UAT answer, log/analytics, observed session,
  or the user's verbatim statement of intent (e.g. weekly-report-tool's own
  ruling 「不要那麼複雜」, KnowYourSing's own ruling 「音訊是你的、留在本機」).
- **推論** — derived from code, semantics, or a comparable product.
- **待測** — needs an observation nobody has made yet.

An unmarked line is a defect of the card, not a fact about the user.

## Card template (3 lines for a one-control ask, ~10 for a flow)

```
Card <id>: <task name>
Who (by task, not person):  <what they are doing; what they already know; what limits them>
Trigger:                    <what just happened that starts this task>
Goal:                       I need to <do what> so that <why>          [mark]
Already has:                <data, selection, prior knowledge, files>   [mark]
Limits:                     <device, input mode, time, privacy, mode (read-only snapshot?)> [mark]
Success criterion:          <the observable end state the person can confirm themselves> [mark]
Refuted by:                 <what observation would show this card is wrong>
```

The GOV.UK form 「As a… I need/want/expect to… so that…」 is kept because it
forces the WHY; 「when…」 (trigger) and 「because…」 (constraints) are the
optional fields this environment makes mandatory — most measured failures
were trigger or constraint mistakes, not goal mistakes.

## Persona rule — no fixed 新手／專家

The same author, on one product, first imports, then rereads daily, then
debugs a parse failure, then shares an export. Information density differs
per TASK; a label like 「新手」 only offers a hint. Cards name the task, the
knowledge in hand, and the limit — never a stereotype that then licenses
「新手不會用鍵盤」 or 「專家不需要說明」.

## Context variants that change the card

Write a separate card, or a variant line, whenever one of these differs —
the projects scanned kept finding that the "same" task was two tasks:

| Variant | Why it is a different card | Measured case |
|---|---|---|
| first run vs returning | first run wants orientation and a sample; returning wants their own data fastest | DIT lands on the built-in sample by default; the 2026-09 round moved 「開始示範」 first with no frequency data (待測 for returning users) — MFP ran a whole UAT round as 「一台什麼都沒裝的機器，第一次打開」 |
| own data vs sample / demo | a sample carries no attribution and can be mistaken for the user's own file | DIT Session Origin distinguishes built-in sample from user-loaded |
| shared read-only snapshot | actions that write do not exist in this mode; the card's action set shrinks | DIT snapshot mode does not render the load container |
| after a failure | goal becomes 「知道失敗了什麼、保留了什麼、從哪裡繼續」 | MFP long-audio: the warning was 「技術告知」, no next step (user answer, unresolved) |
| alternative input | keyboard, narrow window, DPI scaling, assistive tech — the entry may not exist | NTUMail2TG WelcomeForm clipped at 150 % DPI; DIT copy still says 左側 below 719 px; MFP columns collapse below 1242 px |
| mode that removes a capability | read-only, offline, unentitled — the control should not promise a path | ui-copy-stance R2 states; Prism 「無 Universe → 控制不存在」 |

## The 「哪個視窗」 check (review-guis-go-unused, 2026-09-03)

Before a card is written for a viewer, dashboard, navigator, or report page:
ask which window the user actually opens for this task. Measured: the
~/.claude navigator passed UAT and was never opened again (「完全沒開過，
基本上等於用不到了」); DIT's review rounds were not viewed; the user works
in Obsidian. A surface that is not on the user's path fails every card no
matter how well each decision point reads. The finding in that case is
「錯的載體」, routed as a user ruling, not a polish item.

## Success criterion — written before the walk

The criterion is what the PERSON can observe (「匯出檔在資料夾裡，檔名是我
打的」), never an internal state (「store.exported === true」). If the person
cannot confirm success from the surface, that is the first finding of the
walk (cognitive-walkthrough question 4) before any wording is touched.

## Refutability line

Every card ends with 「Refuted by」: the observation that would show the
card wrong (e.g. 「回訪使用者在首頁的第一個動作不是開示範」). A card without
this line cannot lose, and a walk built on it cannot be trusted.
