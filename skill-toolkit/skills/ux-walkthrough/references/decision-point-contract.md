# Decision-point contract — what must hold at every place a person chooses

> Loaded by ux-walkthrough Step 2. Principles only; every rule names the
> external source it rests on (read 2026-09-07) and the local case that
> made it bind. Sources are evaluation frameworks, not proof that a product
> passing them works — that proof is `usability-evidence.md` UE3.

## 1. The unit is the decision point, not the string

A decision point is any place the person must choose or interpret: an
entry, a control, a wait, a result, a return. It is served by several
strings together (title, help, button, inline hint). The question is
「在這裡他知道現在情況、可選動作、重要後果嗎」 — a 「取消」 button need not
restate the flow; a heading need not map to a probe. Add text only where
misreading is likely. (Correction of ui-copy-stance R3's per-string reading.)

**Exits count as decision points, and so do the paths that draw nothing.** A
refusal that only writes a log line, a background start that returns before
its own announcement, a command that exits 0 in silence — the person made no
choice there, which is exactly why nobody enumerates it, and it is where
「已經在跑」 and 「根本沒起來」 become indistinguishable. Ask 「走完這條路，
使用者面前多了什麼」 for every path including the ones that end early; the
answer 「什麼都沒有」 is a finding, not an omission (§6's tray row and §8's
empty states are the two shapes it usually takes). Measured, round-2: AWD's
`Face.TrayOnly` announces itself by invariant, but the shell returns when
another instance holds the installation lock — before the announcement —
and no gate reaches that path because every check compares the Face enum,
never a path (`ops/lessons.md` L-044, the same shape that let a logon face
open a full window for three weeks).

At each point ask the four cognitive-walkthrough questions (Wharton,
Rieman, Lewis, Polson 1994; Spencer 2000 collapses 1–3 into 「知道該做
什麼嗎」 and keeps 4 as 「做對了知道嗎」):

1. Will the person try to achieve the right effect here?
2. Will they notice the correct action is available?
3. Will they connect that action with the effect they want?
4. After acting, will they see progress was made?

## 2. Contract fields (one row per decision point)

| Field | Content |
|---|---|
| trigger state | the program state that puts the person here (field / selector / phase) |
| main message | what is true now, in their terms |
| actions | what they can do from here (incl. leave, cancel, go back) |
| consequence | per action: what happens next, what it costs, whether it is reversible |
| preserved | input, selection, position, context — kept or lost, per action |
| evidence | where the state and consequence are checked in code (path:line / probe) |
| parity | the same point on keyboard, narrow layout, assistive tech — reachable, operable, announced |

Short labels stay short; the ROW may not omit a consequence.

## 3. String roles — classify before applying any copy rule

navigation · action · input guidance · status · result · recovery ·
data content. Only STATUS statements take ui-copy-stance R1's
component / capability / inventory trio and R5's probe requirement.
「總覽」 needs no probe; 「已就緒」 does.

## 4. Show, disable, hide, or remove — a condition table, not one rule

Four projects ruled four different ways and all four were right for their
condition; the rule is the CONDITION, never the outcome:

| Condition | Ruling | Requirement | Measured case |
|---|---|---|---|
| a prior choice changes what the next step means | progressive disclosure — the next control appears after the choice | say what will appear; keep DOM order = reading order | DIT SessionLoadActions: second-level load entry not rendered until a source is chosen (product contract, outranks imported patterns) |
| the person expects the control to always exist, condition temporarily unmet | keep visible, disabled, with the reason | reason reachable by keyboard and assistive tech, not hover-only; NN/g: disabled buttons 「appear clickable but provide no response」, so use sparingly and explain | MFP's own ruling 「一個會消失的按鈕教不會使用者它在哪裡」; Prism: Universe selected, no Topic → 「存在但 disabled」 |
| the mode has no such capability (read-only snapshot, unentitled) | remove; explain the mode once | never a control that can never be pressed | Prism: no Universe → control absent; ui-copy-stance R2 |
| the action is valid but exhausted or pointless right now | hide the exhausted variant | 「不會出現按了沒用的按鈕」 | weekly-report-tool: sort arrows at the end of their range are hidden |
| the action is valid but costly / irreversible | keep; disclose the consequence before the decision (§7) | never prevent by hiding or by unexplained disabling | weekly-report-tool discard confirmations |

## 5. Technical detail — placed by decision use, not by 「技術／非技術」

Rule: information the NEXT decision needs stays at the point; information
that only serves diagnosis or audit goes one layer down (詳細資訊 / log /
failure bundle). The same path is noise in a stack trace and required in a
folder-picker hint. (Correction of ui-copy-stance R4's blanket demotion.)

- keep at the point: DIT source-folder path (the user has to find that folder)
- one layer down: MFP `asr.python`, `config.json`, `faster-whisper`, `pip
  install` — any of these on the settings surface fails the UAT gate
- never in a user message: local paths of the user's own files
  (KnowYourSing regression `worker_rejection_never_echoes_a_local_path`),
  raw `Error.message` / parser text (Prism UAT root-cause analysis: every
  failure reached the user as 「操作失敗（<raw JS message>）」), raw provider
  descriptions (NTUMail2TG TelegramSink), `ex.Message` concatenation
- provenance beats a bare adjective when several instances could be meant:
  「這台電腦上安裝的」 not 「已安裝」 (MFP's own ruling)

## 6. Waiting, cancel, recovery — the contract most often missing

Time bands (NN/g "Response Time Limits", Nielsen 1993, page reviewed
2024): under 0.1 s feels direct; under 1 s keeps the train of thought; past
~10 s attention is lost and a percent-done indicator is warranted.

| Moment | Must show | Must not | Measured case |
|---|---|---|---|
| > ~1 s | that work is happening and on what | a grey lock with nothing else — 「所有的等待狀態…只有灰屏（鎖選項）…看起來很恐怖」 (AnnouncementWatchDog user, 2026-08-18) | 3D-photo-engine: 「合成中…」 text, no spinner, seconds-long, 「無從判斷是否當機」 |
| > ~10 s | step name + elapsed or progress + cancel | a fabricated percentage — MFP refused a generic 「進度 40%」 for a non-transfer job | |
| cancel pressed | that cancel took effect, what was kept, where to continue | silence; a console warning as the only signal (DIT accepted this knowingly — record it as a known gap) | |
| failure | condition, what is preserved, next action (ui-copy-stance R3) | 「技術告知」 with no exit (MFP long-audio, user-reported) | |
| retry | whether retry has side effects (duplicate send, re-download) | | NTUMail2TG: repeated launch spawned zombie processes with no feedback |
| background / tray start | a self-announcing notice | tray-only silence — 「沉默不是中性的」 (AWD ruling 2026-09-05) | |

Elapsed time is honest when progress is unknowable; a percentage that is
not measured is a lie the honest-data rule forbids.

## 7. Destructive and discard actions

- Confirm only for serious consequences (destroying work, cost), describe
  the consequence in the person's words, verb-labelled buttons (「刪除檔案」
  / 「保留檔案」), no preset answer for risky operations, and prefer UNDO —
  NN/g "Confirmation Dialogs Can Prevent User Errors" (2018): 「do go to
  great lengths to provide undo」.
- Cancel abandons and loses unsaved work; Close dismisses and keeps it. An
  「×」 that does both is the named failure; default to keeping work on
  close and offer an explicit Cancel — NN/g "Cancel vs Close" (2017).
- Scope words map to distinct scopes: Prism's 「移除」 vs 「刪除」 had been
  conflated across two destructive scopes; DIT 「匯出」 twice → 「匯出閱讀
  頁面快照」 / 「匯出純對話紀錄」 (user ruling). See §13.
- Silent destructive defaults are wrong defaults: KnowYourSing's own ruling
  rejected auto-LRU eviction 「靜默刪掉使用者的歌是錯的預設」; weekly-report-tool
  fixed a repaint that silently discarded typed edits; its README rules that
  refetch-with-unsaved-edits, roster reset, and duplicate-name-on-add each
  confirm first, while a routine setting change clears silently — the
  boundary is 「使用者打過的字」.

## 8. Empty states — status, learning cue, path

NN/g "Designing Empty States in Complex Applications" (3 guidelines): say
whether the container is loading, unavailable, or genuinely empty; use the
space to teach what belongs there; offer the direct action that fills it.
Distinguish first use / user-cleared / no results / loading / error — they
need different copy. Measured: AWD 「為甚麼名稱、狀態等項目的那邊還是空的」
→ placeholder text required, hide-not-remove on clear; KnowYourSing
「尚未記錄歌曲。匯入後會出現在這裡。」 (good) — but the pre-fix library never
left that state after import, so the empty state also masked a defect;
3D-photo-engine's initial viewport was a black rectangle with no 「上傳後在
此預覽」; Prism released 「書庫中沒找到原詞」 vs 「整個書庫都沒有這個詞」 as
two different no-result states.

## 9. One seam for projected state

Two strings that answer one question from two fields read as a
contradiction even when both are true (ui-copy-stance founding case). The
fix is structural: the surface reads state through ONE seam. Measured:
AWD (shell read engine internals via two paths → one query/command seam);
NTUMail2TG (tray GUI believed tray mode while a headless process ran);
DIT `checkOllama()` probes the API, not whether the window is open —
engine-online ≠ user-visible-offline, and the copy must not merge them. A
walk that finds two paths reports a state-model finding, not a wording one.

## 10. Affordance is a claim

A label or style that says 「可操作」 promises an operation. AssetVault-GUI
labelled every card operable; a later finding (user): 「有些標了可操作但其實
只有hover，或者點下去畫面彈一下並失焦」 → 「過度承諾…那是辯解不是設計」;
retraction: 「一個承諾若需要靠註解解釋才成立，它在介面上就是假的」. Treat
affordance like copy under ui-copy-stance R5: it may claim only what the
handler does. Hover-only behaviour is not an operation; a click that flashes
and drops focus is a defect, not an interaction.

## 11. Layout-change semantics

When a breakpoint, DPI scale, or collapse removes or moves a region, every
instruction that names it by LOCATION fails. WCAG 2.2 SC 1.3.3 Sensory
Characteristics (Level A): instructions must not rely solely on visual
location (「左側」「下方的綠色按鈕」); name the element instead (「結構導覽」).
Reflow (SC 1.4.10) is the check basis for content at 320 CSS px width —
cited as a check, not as a compliance claim. Measured: DIT locales still say
「沿左側結構逐步閱讀」 while CSS hides the desktop sidebar under 719 px;
NTUMail2TG WelcomeForm clipped at 2560×1440 @150 % until DPI-aware sizing;
AssetVault-GUI breadcrumb wrapped to three lines and broke a fixed 60 px
header at 520 px; 3D-photo-engine's fixed 320 px panel had no media query.

Check after every layout change: direction words, entry hints, reading
order, and that DOM order still equals visual order (DIT 2026-09 kept them
equal deliberately — that is the positive control).

## 12. Core-path equivalence (engineering-checkable, never deferred to UAT)

The task's core path must be completable by keyboard, at narrow width, and
with assistive tech, or the finding is a blocker (uat.md A2, not B2). WCAG
2.2 criteria named as CHECKS, not as an audit:

- 2.1.1 Keyboard: a `div onClick` is not a control; `focus-visible` styling
  does not make it one. DIT's thinking-head and io-head expand controls —
  native `button`, `aria-expanded`, Enter/Space.
- 2.4.11 Focus Not Obscured (Minimum, new in 2.2): sticky headers, minimaps,
  floating bars must not fully cover the focused element.
- 4.1.3 Status Messages: async results announced without stealing focus
  (DIT SessionLoadStatus already has `role=status` + `aria-live=polite`;
  check timing and frequency — not every position change is a message).
- 2.5.8 Target Size (Minimum, 24×24 CSS px) and 2.5.7 Dragging Movements
  (a single-pointer alternative to drag): FlashGrab's shift-release tier and
  3D-photo-engine's drag mode both need a non-drag path or a declared
  exception.
- Touch access to truncated content: a `title` attribute is hover-only; a
  single-line ellipsised heading needs an operable full-text path (DIT
  reader-heading, 推論 until tested with two same-prefix titles).
- Keyboard equivalents for pointer-only controls are a positive control:
  PatentsGrabber `[` `]` beside ⟲ ⟳.

## 13. Label distinctness

Two controls whose names share a head word must differ in the CONSEQUENCE
word, and two names must not share a head word with a different section.
Measured: DIT 「匯出」×2 (user ruling); MFP extension menu renamed 「工具」
after 「擴充功能」 collided with 「擴充設定」; Prism 「移除」/「刪除」; NN/g
heuristic 4 (Consistency and Standards): 「users should not have to wonder
whether different words… mean the same thing」. Action names carry their
expectation: DIT 「開始示範」 implies from-the-beginning while `startReading`
only switches view and keeps `activeId` (已確認) — either the name changes
(「閱讀示範對話」) or the behaviour does, and which one is a user ruling.

## Sources (read 2026-09-07)

- Wharton, Rieman, Lewis, Polson (1994) "The Cognitive Walkthrough: a
  practitioner's guide", in Nielsen & Mack, *Usability Inspection Methods*;
  Spencer (2000) streamlined variant.
- NN/g: 10 Usability Heuristics (reviewed 2024-01-30); Error-Message
  Guidelines (2023-05-14, 12 guidelines in visibility / communication /
  efficiency); Response Time Limits; Confirmation Dialogs Can Prevent User
  Errors; Cancel vs Close; Designing Empty States (3 guidelines); Why
  Disabled Buttons Hurt UX (video).
- W3C WCAG 2.2 Understanding pages: 1.3.3, 1.4.10, 2.1.1, 2.4.11, 2.5.7,
  2.5.8, 4.1.3.
- GOV.UK Service Manual: Learning about users and their needs; Using
  moderated usability testing.
- Local: project decisions/UAT files cited inline as illustrative field
  evidence from the author's own private projects — not included in this
  share.
