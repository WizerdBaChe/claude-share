# UI copy from the user's stance

> Loaded by audience-fit Mode B. Rules distilled from the media-fetch-pipeline
> ASR-settings correction (user ruling 2026-08-28) — the decision records and
> UAT checklist behind it live in that project's own tree, not in this share —
> plus the status-card pattern in `project-info-for-general-readers.md`
> (視覺化分工 §status_explanation). Chinese examples are verbatim from the case.

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

### R1 — Three kinds of thing, one vocabulary each (the MFP correction)
A status surface holds at most three kinds of statement:
- **COMPONENT**: a thing is present/installed or not (引擎環境、模型資料夾).
- **CAPABILITY**: something the user can do right now, or not (語音辨識、翻譯).
- **INVENTORY**: what exists in a store (folder contents, installed models).

A capability is a *function of* components and is never one of them. Never
let the two share one green/orange vocabulary or alternate down a panel:
that is how two true statements about different objects read as a
contradiction. Group by kind, and label the kind.

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
over it with vaguer words is the failure, not the fix.

### R3 — Every string answers the status-card trio
For any state the UI can show, the copy must let the user answer:
1. what is true right now (in their terms),
2. what they can do about it from here,
3. what will happen next if they do.

「在{狀態}，你可以{行動}」 beats a bare adjective. A message that names a
state with no exit (「發生錯誤」) fails this even when technically true.

### R4 — Mechanism detail is one click away, never the first line
First line: condition → what the user sees → suggested action
(若{條件}，你會看到{現象}；建議{處置}). Paths, exit codes, engine names,
and stack traces go behind 詳細資訊/log — kept, because the power user and
the bug report need them; demoted, because they are not the answer to R3.

### R5 — Copy may only claim what the code checks
「已就緒」 must trace to a probe that actually ran; 「安全」「不會遺失」 must
trace to a mechanism. If the program cannot distinguish two states, the copy
must not pretend it can (that is R2's boolean trap from the other side).
This is the honesty rule of `honest-data-readability.md` applied at
string scale.

### R6 — Foolproofing reads as guidance, not as accusation
Disabled controls stay visible with the reason (a control that appears and
disappears teaches nobody where it lives — a finding from the same
correction). Error copy names the condition, not the user's mistake.

## Working method

1. Inventory the surface: every user-visible string with the program state
   it renders (field/probe, not just the current text). A string with no
   identifiable underlying state is already a finding (R5).
2. Classify each line COMPONENT / CAPABILITY / INVENTORY (R1); mark
   collapsed states (R2).
3. Rewrite from the user's question at that screen (R3/R4/R6).
4. Deliver as a proposal table — do not silently apply. UI wording is UX
   semantics; the direction gets confirmed (global Interaction-style rule):

   | 位置 | 現行 | 建議 | 對應程式狀態 | 理由 (Rn) |

5. Flag what only a human can judge (文案讀不讀得懂、外行人看不看得懂) as
   UAT items rather than claiming them verified — the MFP checklist marks
   these 「只有人能判斷」, and 2,033 green tests did not see the worst one.
