# UI copy from the user's stance

> Loaded by audience-fit Mode B. Rules distilled from the media-fetch-pipeline
> ASR-settings correction (user ruling 2026-08-28) — the decision records and
> UAT checklist behind it live in that project's own tree, not in this share —
> plus the status-card pattern in `project-info-for-general-readers.md`
> (視覺化分工 §status_explanation). Chinese examples are verbatim from the case.
>
> Revised 2026-09-07 after a codex Mode C review — its own record lives in
> the source's `references/` tree, not in this share — and
> the `ux-walkthrough` split: R3, R4, R6 are now CONDITIONAL instead of
> blanket; R0, R7, R8 are new. The interaction half of every rule
> (show/disable/hide conditions, wait–cancel–recovery, single seam for
> state, core-path parity) lives in
> `skills/ux-walkthrough/references/decision-point-contract.md` — this file
> only decides words.

## The stance flip (why this file exists)

Builder-stance copy prints internal state outward: the engine is ready, the
flag is unset, the probe returned 404. User-stance copy starts from the
question the person has at that screen — *can I do the thing I came for, and
if not, what do I do next* — and maps that question BACK onto real program
state. The direction of derivation is the whole rule: screen text is derived
from the user's question, constrained by program truth; never a rendering of
the data model in whatever vocabulary the code uses.

The founding failure: 「引擎已就緒」 and 「還不能用」 visible in one
viewport. Reported as a state-sync bug; it was not — the backend had one
consistent judge. Every defect was in the PROJECTION: lines answering one
question from different fields, with no cue that some lines describe a
component and others a capability.

## Rules

### R0 — Classify the string's role before applying any rule
navigation · action · input guidance · status · result · recovery · data
content. Only STATUS statements take R1's trio and R5's probe requirement;
a heading (「總覽」) needs no probe, a navigation label is not a capability
claim. The 2026-08 working method classified every line as
component/capability/inventory and forced task titles and field labels
into a status taxonomy (codex review §4.2) — that was the misuse this rule
removes.

### R1 — Three kinds of STATUS statement, one vocabulary each (the MFP correction)
A status surface holds at most three kinds of statement:
- **COMPONENT**: a thing is present/installed or not (引擎環境、模型資料夾).
- **CAPABILITY**: something the user can do right now, or not (語音辨識、翻譯).
- **INVENTORY**: what exists in a store (folder contents, installed models).

A capability is a *function of* components and is never one of them. Never
let the two share one green/orange vocabulary or alternate down a panel:
that is how two true statements about different objects read as a
contradiction. Group by kind, and label the kind. When several instances
could be meant, carry provenance: 「這台電腦上安裝的」, not a bare 「已安裝」
(a finding from the MFP correction; three Chrome copies possible).

### R2 — Distinct underlying states must look distinct (the MFP correction's UAT findings)
Three states that copy routinely collapses:
- not configured (使用者還沒做設定)
- configured but broken (有設定，但東西壞了)
- not entitled / not enabled (沒開通這個能力)

「引擎有設定但壞掉」 rendered as 「尚未設定」 sends the user to redo a step
they already did; 「沒開通」 styled like 「壞掉」 sends them to debug a
non-fault. If the underlying field is a boolean over a three-state thing
(the MFP case: `engine.present` hiding `path`+`problem`), the fix is in the
model or projection — copy alone cannot repair a lossy field, and papering
over it with vaguer words is the failure, not the fix. Such a row leaves
this table as a ux-walkthrough state-model finding.

### R3 — Every DECISION POINT answers the status-card trio
For any state the UI can show, the person at that point must be able to
answer, from the title, hint, button, and inline text TOGETHER:
1. what is true right now (in their terms),
2. what they can do about it from here,
3. what will happen next if they do.

The unit is the decision point, not the string (codex review §4.1): 「取消」
need not restate the flow, a heading need not map to a probe, and text is
added only where misreading is likely. What may never be omitted is a
CONSEQUENCE that matters: 「在{狀態}，你可以{行動}」 beats a bare adjective,
and a message that names a state with no exit (「發生錯誤」) fails this even
when technically true. A warning that is only 「技術告知」 with no next step
fails it too (a finding from the MFP correction, user answer).

### R4 — Mechanism detail is placed by DECISION USE, not by 「技術／非技術」
Information the next decision needs stays at the point; information that
only serves diagnosis or audit goes one layer down (詳細資訊 / log /
failure bundle) — kept, because the power user and the bug report need it;
demoted, because it is not the answer to R3. The same path is noise in a
stack trace and required in a folder-picker hint: DIT's source-folder path
stays on the load panel (the user must find that folder); MFP's
`asr.python` / `config.json` / `faster-whisper` / `pip install` on the
settings surface fail the UAT gate. First line stays: condition → what the
user sees → suggested action (若{條件}，你會看到{現象}；建議{處置}).

### R5 — Copy may only claim what the code checks
「已就緒」 must trace to a probe that actually ran; 「安全」「不會遺失」 must
trace to a mechanism. If the program cannot distinguish two states, the copy
must not pretend it can (that is R2's boolean trap from the other side).
This is the honesty rule of `honest-data-readability.md` applied at
string scale. The same rule covers AFFORDANCE labels: 「可操作」 on a card
that only hovers is an over-promise (a finding from AssetVault-GUI's own
review; 「一個承諾若需要靠註解解釋才成立，它在介面上就是假的」).

### R6 — Foolproofing reads as guidance, not as accusation; disable-vs-hide is conditional
Error copy names the condition, not the user's mistake. For an unavailable
control, the WORDING rule is: whatever is shown carries its reason, and the
reason is reachable without hover (keyboard, assistive tech). WHETHER the
control is shown disabled, revealed progressively, hidden, or removed is a
condition ruling, not a copy rule — four projects ruled four ways, all
correct for their condition (the MFP correction keeps a control visible
with its reason when the user expects it to always exist; weekly-report-tool hides exhausted sort arrows;
Prism removes the control when no Universe exists; DIT reveals the second
load step only after a source is chosen). The table is
`skills/ux-walkthrough/references/decision-point-contract.md` §4; a
product's own flow contract outranks a pattern imported from another
product.

### R7 — Instructions never rely on location alone
「沿左側結構逐步閱讀」 fails the moment a breakpoint hides the sidebar (DIT
< 719 px, i18n still says 左側) and fails always for a screen-reader user.
Name the element (「結構導覽」), not its place (WCAG 2.2 SC 1.3.3 Sensory
Characteristics). 「上方／下方」 is acceptable only when it matches reading
order. After any layout change, grep the i18n table for direction words.

### R8 — Labels that share a head word differ in the consequence word
Two controls named 「匯出」 were indistinguishable → 「匯出閱讀頁面快照」 /
「匯出純對話紀錄」 (DIT user ruling); a 「擴充功能」 menu collided with
「擴充設定」 → renamed 「工具」 (the MFP correction); 「移除」 and 「刪除」 had been used
for two different destructive scopes (Prism). An action name also carries an
expectation: 「開始示範」 implies from-the-beginning; if the code only
switches view and keeps the position, either the name or the behaviour
changes — which one is a user ruling (類別 語意), never a silent pick.

## Working method

1. Inventory the surface: every user-visible string with the program state
   it renders (field/probe, not just the current text). A STATUS string
   with no identifiable underlying state is already a finding (R5).
2. Classify each string's ROLE (R0). For status statements only, classify
   COMPONENT / CAPABILITY / INVENTORY (R1) and mark collapsed states (R2).
3. Group strings by DECISION POINT and rewrite from the user's question at
   that point (R3/R4/R6/R7/R8) — the point answers the trio, not each label.
4. Deliver as a proposal table; rows tagged 純措辭 are applied directly and
   recorded, rows tagged 語意 wait for the ruling (audience-fit SKILL.md
   Mode B; global Interaction-style rule):

   | 位置 | 現行 | 建議 | 對應程式狀態 | 理由 (Rn) | 類別 |

5. Flag what only a human can judge (文案讀不讀得懂、外行人看不看得懂) as
   UAT items rather than claiming them verified — the MFP checklist marks
   these 「只有人能判斷」, and 2,033 green tests did not see the worst one.
6. Emit the machine half as a test, never as a UAT item: a regression that
   feeds an engine name / local path / raw exception into the message
   pipeline and asserts its absence on the surface (KnowYourSing
   `worker_rejection_never_echoes_a_local_path`; MFP gate words).
7. Hand off every row whose layer is not wording (state model, interaction,
   flow, layout-change, keyboard/narrow parity) to `ux-walkthrough` as a
   Step 3 finding record; take its wording rows back into this table.
