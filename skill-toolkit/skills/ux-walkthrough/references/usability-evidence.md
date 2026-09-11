# Usability evidence — what each kind of check may claim

> Loaded by ux-walkthrough Step 5 and for any test plan. The ladder is a
> claim-calibration device (same shape as the verification ladder in
> `rules/verification-ladder.md`): a rung licenses a sentence, never a
> stronger one. Sources read 2026-09-07 are listed at the end.

## 1. Evidence ladder (`UE0`–`UE4`; the U prefix keeps it apart from paper-distill's evidence KINDS `E1`–`E4`, a naming collision this environment already tracks)

| Rung | What was done | Sentence it licenses | Sentence it does NOT license |
|---|---|---|---|
| UE0 static read | copy and structure read as text | 「這段字回答了狀態／行動／後果」 | anything about finding, operating, completing |
| UE1 code check | handlers, selectors, CSS breakpoints, i18n keys traced | 「這個控制沒有鍵盤路徑」「這兩行讀不同欄位」 (已確認) | 「使用者會困惑」 |
| UE2 interface task run | the builder walks the task on the running UI — DOM reads for structure/state, out-of-process pixels for appearance, keyboard-only and narrow-width runs recorded separately | 「入口在窄版存在且可聚焦」「按取消後選取保留」 | 「使用者找得到」「更容易理解」 |
| UE3 observation | people who did not build it attempt task cards; behaviour and explanations recorded | 「n 位中 k 位獨立完成；失敗點在 X」 | statistical generalisation; 「使用者滿意」 from completion alone |
| UE4 comparative / quantitative | controlled comparison across versions or cohorts with defined metrics | effect claims with their scope | anything beyond the measured cohort and content |

**A user's own field report sits beside this ladder, not on it.** 「重開機後
會自己跳一份 GUI 上來」、「所有的等待狀態…只有灰屏…看起來很恐怖」 are 已確認
evidence for the state they name and license 「這在真實機器上發生過」 — stronger
than UE1 for that one fact, weaker than UE3 everywhere else: nobody attempted a
task card, so it says nothing about completion, about the paths nobody reported,
or about anyone but the reporter. Cite it as 已確認 with its record
(`decisions.md` / UAT file + line), never as UE3, and never let it stand in for
the observation a 待測 mark is waiting for. Measured: the two strongest pieces of
UX evidence in AnnouncementWatchDog are both of this kind, and neither is
UE0–UE4.

Calibrated example: DIT 2026-09 editorial round — UE1 + UE2 done, so 「風格
延續與入口整理完成」 holds; 「使用者導向已完整落地」 needs UE3 and was
correctly withdrawn. Tests green is UE1 at most: 3D-photo-
engine 「測試 100 passed，但肉眼品質 Gate 未過」; PatentsGrabber
「element count is not load success」 (DOM passed, images visibly broken);
MFP 2,033 green tests did not see the contradicting status cards.

## 2. Engineering-checkable — never sent to UAT

These have a determinable answer; a walk emits them as tests or commands
and the delivery pastes the output (uat.md §4 admission gate, question 1).
The list is a seed, not the definition: derive the actual checks from the
surface's state model, handlers, and contracts, and opt out of an item
with a one-line reason when the surface has no such thing.

Every item below is written in web vocabulary. On a non-web surface the floor
is not empty — it is TRANSLATED: name the mechanism that would have to hold,
then the platform's own instrument for it. Measured, round-2 (AWD, a WinForms
tray app): DOM order → UI-thread affinity, already gated by its own
thread-affinity check; `aria-live` → whether any operator-visible signal
exists away from the window at all; the breakpoint grep → minimum window
size and DPI scaling; and the strongest one, a check that drives the
product's REAL entry point and asks the OS what appeared. A walk that emits
no engineering check because there was no DOM has skipped this step, not
passed it.

- keyboard equivalence of every core-path control (native element or full
  ARIA pattern; Enter/Space; visible focus)
- focus returns to the invoker after a dialog / drawer closes
- cancel preserves the declared data (selection, input, position) — assert
  the state, not the pixel (`ops/lessons` L-010)
- no user-file path, engine name, exit code, raw exception, or provider
  description in a user-facing message — a regression test that feeds a
  path and asserts its absence (KnowYourSing
  `worker_rejection_never_echoes_a_local_path`; MFP UAT gate words)
- status strings derived from one seam (grep the surface for a second read
  path of the same fact)
- `aria-live` region exists for async results, and position/scroll changes
  are NOT announced
- every instruction that names a region has that region present at every
  breakpoint (grep i18n for 左側 / 右側 / 上方 / 下方 against the CSS that
  hides regions)
- every instruction that names a DESTINATION or a CONTROL resolves to a
  label the surface actually has: 「設定 → X」 against the settings category
  registry, 「按「Y」」 in a guide against the workspace's button text. The
  checkable twin of audience-fit R7 (no location-only instructions). Measured,
  round-3 (MFP): 「設定 → 相依工具」 ×4 and 「設定 → 語音辨識」 ×3 named
  categories that do not exist; a guide said 「選擇檔案」 above a button
  reading 「選檔案…」 — eight misses in three files, none caught by 2,000+
  green tests because no test compared copy to the navigation model
- disabled controls carry a reachable reason (`aria-describedby` or visible
  text), not a `title` alone
- DOM order equals visual order after grid/flex reordering
- target size ≥ 24 CSS px on core-path controls

Six more when the surface has more than one destination
(`navigation-ia-contract.md`; each is determinable, and the count is always
against NAV-O1's denominator — 「23 個中 0 個」, never 「導覽有問題」):

- **URL round-trip**: drive the surface to a view, read the address, reload, and
  assert the same view. Off the web the translation is a re-entry parameter —
  the command or argument that reproduces the state (`mfp ... --task X`)
- **Back** returns to the previous view rather than leaving the surface; and the
  view a person lands on from a link has a defined Back (NAV-5(d))
- **clean-session share**: open the link a person would send in a fresh context
  (new browser profile / cleared storage) and assert the same view AND the same
  identity — measured failure mode: the view is in the URL and the role is in
  `localStorage`, so the recipient gets the right page in the wrong world
- **destinations are operable controls**: count the navigation items reachable by
  Tab and openable in a new tab against NAV-O1. `data-*` + a click handler routes but
  affords nothing; the measured founding case is 0 of 23 (NAV-8)
- **selected state in the DOM**, not only in pixels: `aria-current` /
  `aria-selected` on the current destination (`ops/lessons` L-010 — assert the
  state, not the paint)
- **persistence scope is declared and true**: the copy that says how long a
  remembered thing lasts exists in the view that owns it, and matches the storage
  call (grep the sentence against the write site). Known-good, verbatim:
  「勾選進度僅儲存於本裝置，更換裝置或瀏覽器後將不會保留」
- **legend travels with the code**: a one-glyph encoding (必/選, ●/○, colour) has
  its legend in the same view as the encoded items, and colour is not the only
  carrier (WCAG 1.4.1)

A finding in this list that is sent to 「人工驗收」 instead is a deferral
the delivery must name (「不能用『只有人能判斷』把明確技術缺陷延後」).

## 3. Human items → manual-acceptance rungs

Map each remaining finding to `ops/references/uat.md`; never a third list:

| Finding kind | Rung |
|---|---|
| a state the person cannot see (silent cancel, hidden failure) | A3 observability |
| core path not completable in some input mode | A2 operation |
| comprehension: knows what happened, what next, which file this is | B1 看得懂 |
| steps, defaults, remembered choices, waiting feedback | B2 順手 |
| layout, alignment, density, type size | B3 觀感 |

Each item = action + expected observation, blind-executable, with a
non-destructive way to reach the state (fixture, flag, debug route).

## 4. Task-based test plan (write only when observation is asked for)

Method: moderated usability testing (GOV.UK Service Manual) — think-aloud,
one facilitator, a note-taker, at most ~6 one-hour sessions a day.

- **Task wording** sets a goal and never names a control or route:
  「找出這份對話裡第一次測試失敗的原因，並指出後來修正了什麼」, not 「按閱讀，
  再展開思考」. Relevant and believable; dummy data lowers engagement and
  hides contextual issues — use fixtures that resemble real content without
  private content.
- **Start condition** per task (first run / returning with a selection /
  after a failure), and a **control condition** (the normal path) beside
  each failure-injection condition, so the failure case is known to fail
  and the normal case known to pass — a test that cannot fail is not a
  test (`rules/verification-ladder.md`). Injected failure comes from a
  controlled environment (slow fixture, corrupt file), never from real
  data damage.
- **Per task record**: outcome (independent / assisted / failed / not run —
  separate columns), time to first effective action, completion time,
  wrong paths, backtracks (not automatically errors — exploration counts),
  prompts needed, the person's own explanation of what they are reading,
  what the position means, what happened after the action (never 「懂了
  嗎」).
- **Coverage**: first use, returning, and at least one alternative-input
  run (keyboard-only, narrow window) — recorded separately, one person
  may cover several tasks.

## 5. Metrics — defined before the run

- completion rate = independent completions ÷ valid attempts; report
  numerator, denominator, and exclusions; assisted completions never fold
  into independent.
- recovery cost = extra actions + lost context after a failure; a data
  misread or an unreachable core path is a blocker regardless of count.
- subjective feedback (difficulty, confidence, preference) sits beside the
  behavioural record and never replaces it — preference ≠ performance.

## 6. Severity — words, with three factors

NN/g severity scale (Nielsen): 0 not a problem · 1 cosmetic · 2 minor ·
3 major · 4 catastrophe (fix before release). Rate from frequency, impact,
persistence. The walk reports the three factors and the word; it never
multiplies them into a score.

## 7. Small-sample honesty

Small explorations locate friction; they do not estimate rates. Sample
size follows the contexts to cover and the uncertainty, not a target
number; no statistical significance from a handful. Comparing versions
needs the same content and a control for learning effects; a single author
trying the product repeatedly is not evidence about users (calibrated:
every 「作者驗收」 in the scanned projects is builder UE2, which is why they
keep a separate human tier). Usability itself is an OUTCOME of use in a
context (ISO 9241-11: effectiveness, efficiency, satisfaction for
specified users, goals, context) — not a property the product carries.

## Sources (read 2026-09-07)

- GOV.UK Service Manual — "Using moderated usability testing"; "Learning
  about users and their needs".
- NN/g — "How to Rate the Severity of Usability Problems"; "Ten Usability
  Heuristics" (reviewed 2024-01-30); "Progress Indicators Make a Slow
  System Less Insufferable".
- ISO 9241-11:2018 definition of usability (via MeasuringU summary).
- Local — `ops/references/uat.md`; `rules/verification-ladder.md`;
  `ops/lessons` L-010 / L-030 / L-037; project files cited inline are
  illustrative field evidence from the author's own private projects, not
  included in this share.
