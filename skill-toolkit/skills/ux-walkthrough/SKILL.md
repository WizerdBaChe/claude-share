---
name: ux-walkthrough
description: 'Task-level UX walkthrough (UX 走查／認知走查) of an existing or designed interactive surface: can a specific person, in a specific situation, find the entry, predict each action''s consequence, wait/cancel/recover, and continue next time — on keyboard, narrow layout, and assistive tech too. Output = executable findings (task · evidence mark · layer · fix · verification), show/disable/hide rulings, a wait-cancel-recovery contract, and on request a task-based usability test plan. Trigger on 「UX 走查」「這個流程使用者走得通嗎」「從入口到結果跑一遍」「使用者會不會誤以為」「停用還是隱藏」「等待/取消/失敗後怎麼辦」「鍵盤/窄版走得通嗎」「可用性測試怎麼設計」「使用者導向有沒有真的落地」 "walk the task", "usability review", "cognitive walkthrough", "heuristic evaluation". Principles only, never a component library. NOT pure wording (→ audience-fit Mode B; the two hand findings to each other), NOT mockups/theming (→ design, artifact-design), NOT tokens (→ design-system-suite), NOT motion (→ motion-design), NOT new-product design (→ product-design-thinking; this is the instrument behind its "UX semantics are user decisions" question), NOT implementing the fix (→ frontend-developer / testing agents).'
---

# ux-walkthrough — verify the stance as a task result

Born 2026-09-07 from a Mode C review of `audience-fit`'s own coverage, plus
a scan of twelve local projects. The founding gap: audience-fit keeps the
user's STANCE (honest states, capability vs component, no over-promise) but
organises work as 「盤點字串 → 對應狀態 → 改寫 → 人工判讀」. That improves
comprehension; it cannot say whether a person completes a task from the
entry, reads the result correctly, recovers from failure, and continues
next time. A flow treated as content to explain is not a flow that has been
walked. Every project scanned had a 「只有人能判斷」 UAT tier and none had
a task walkthrough BEFORE build — 3D-photo-engine rewrote its interaction
model three times from live feedback; AssetVault-GUI labelled cards
「可操作」 that only hovered. This skill is the missing instrument.
It evaluates and specifies; it never edits product code.

## Step 0 — fire test and scale

Fire when BOTH hold: (1) there is an interactive surface — GUI, CLI prompt
sequence, notification chain, settings page, a PIM state machine of one —
and (2) the question is whether a person can complete / understand /
recover / continue, not whether the text reads well. Wording-only asks go
to audience-fit Mode B; that skill hands back anything whose layer turns
out to be interaction, state, or flow.

Scale by the ask, never by a fixed ritual:

| Ask | Unit | Deliverable |
|---|---|---|
| one control / one label / one message | one decision point | a 5–8 line finding, or 「no finding」 with the checked questions |
| one flow (load, import, export, first run, recovery) | a task path | task card + decision-point table + findings + verification list |
| 「使用者導向有沒有落地」 / a release | 2–3 highest-value task paths | the above per path + priority order |
| 「可用性測試怎麼做」 | a test plan | `references/usability-evidence.md` §plan |

A rename request must not be answered with a research programme; a release
claim must not be answered with one rename.

## Inputs the walk needs

- The real surface: source (components, state store, i18n strings) and,
  when it runs, the running UI read through the DOM. Two instruments,
  same rule (structure/state claims take DOM reads, appearance takes
  out-of-process pixels — `ops/references/browser-pane-pixel-route.md`):
  the Browser pane when the server belongs to THIS session's project
  (`.claude/launch.json` is per cwd); the playwright-headless MCP against
  a dev server started in the background when the surface lives in
  another repo (round-1 field data: DIT from `~/.claude`). Stop what you
  started before delivering. There is no DOM outside a browser: a desktop,
  tray or CLI surface is read through its source, its state machine, and the
  checks that drive its REAL entry point (AWD's own launch check enumerates
  top-level windows), and a live observation of it belongs on the user's own machine
  (`ops/references/uat.md` human tier). **Observation must not change the
  user's world**: when a live run would take a lock, send a message, write
  the user's data or start a watcher, the walk stays on source + records and
  SAYS which decision points were therefore never seen (round-2: AWD was
  walked without starting it — starting it takes the installation lock,
  fetches real sites and pushes to a Telegram channel). Such a surface is
  not exempt from the walk; it is exempt from UE2. Narrower case, round-3:
  the surface runs safely but ONE exit writes the user's state (MFP's
  first-run dialog persists `guides.seen` into the user's real `%APPDATA%`
  config) — neutralise that exit in the instrument (hide the backdrop in
  the DOM, never press the button), keep walking, and record the deviation
  in the record's method section AND the process ledger; the dismissed
  state itself becomes 待測 with the fixture named. Neutralising is per
  decision point, never a licence to alter the page's own state machine.
- **Declare the data the walk ran on** — real, seeded (`seed_demo.py`-style
  fixture rows), or empty — in the record's status line, and name the
  decision points a fixture cannot exercise (transitions, transfers,
  anything the fixture only PICTURES). Round-3: MFP's twelve seed rows
  proved every state's controls and copy (UE2) while the download leg
  stayed 待測; a record that hides the fixture reads as a real run.
- **Narrow means the product's own declared floor** (Electron `minWidth`, a
  page-class registry, a CSS breakpoint), not an arbitrary width; anything
  below the floor is trimmed per the global [BC] enumeration rule or kept as
  a labelled guess (round-3: 900 px was MFP's `window-geometry.ts` floor, so
  700 px was dropped, not tested).
- The state model behind the surface (store selectors, state machine, probe
  fields). A walk on strings alone is audience-fit Mode C, not this skill.
- Task cards (Step 1). If none exist, write them and mark every line
  evidence or assumption — the walk is only as true as its cards.

## Step 1 — task cards

Load `references/task-context.md`. One card per task: who (by task,
knowledge, constraints — never a fixed 新手/專家 person), trigger, goal,
what they already have, limits, success criterion, and the evidence mark on
each line (已確認 from research/logs/rulings · 推論 from code/semantics ·
待測). Then the context variants that change the card: first run vs
returning, own data vs sample, shared read-only snapshot, after a failure,
alternative input (keyboard / narrow / assistive tech). Include the
「使用者實際在哪個視窗工作」 check: a surface nobody opens fails every card
(`review-guis-go-unused`).

## Step 2 — walk the path, one decision point at a time

Load `references/decision-point-contract.md`. **When the surface has more than
one destination** (a rail, a router, tabs, a mode switcher, a multi-view
shell), also load `references/navigation-ia-contract.md` and answer its three
orientation questions — how many destinations, whose world the division comes
from, where 「我在哪一個」 actually lives — BEFORE any pattern is named. A
one-destination surface says so and skips it. Enumerate the decision points
along the card's path (entry → choose → act → wait → result → return /
redo / exit). Blocking surfaces on the way — onboarding dialog, consent,
error banner, modal — are decision points on EVERY path: record who
dismisses them, the default choice, and whether every exit counts as
"seen" (round-1: DIT's first-run dialog intercepted the first click). A path
that ENDS without drawing anything is a decision point too — enumerate exits,
not only choices (reference §1; round-2: AWD's background face returns before
its own start announcement when another instance holds the lock). At
each point, ask the four cognitive-walkthrough questions
(Wharton et al. 1994): will they try the right effect; will they notice the
action is available; will they connect the action to the effect; will they
see progress after acting. Record the contract: trigger state · main
message · available actions · consequence of each · what is preserved ·
where the evidence lives (field / probe / handler) · parity on keyboard,
narrow layout, assistive tech. Apply the reference's rulings where they
bite: show / disable / hide / remove; technical detail by decision use;
wait–cancel–recovery; destructive & discard; empty states; single source of
truth for projected state; affordance is a claim; layout-change semantics;
label distinctness.

## Step 3 — findings, in the executable shape

One record per defect. Never report an inference as a user complaint.

```
Finding ID:
Task and context:            <card id + variant>
Evidence:                    已確認 <path:line / DOM read / the user's own report or ruling + where it is recorded> | 推論 <from what> | 待測 <observation + the environment or fixture it needs>
Current UI and copy:         <verbatim>
User consequence:            <what they do wrong / cannot do / lose>
Layer:                       wording | layout | interaction | IA/navigation | routing | state model | service | research
Proposed change:             <and the accepted behaviour it must preserve>
Verification:                <engineering check, or task + success condition>
Owner / unresolved decision: <engineering | audience-fit | user ruling: question + evidence>
```

「需要更友善」 is not a finding. 「鍵盤無法展開此步驟的工具輸出；控制是
`div onClick`（parts.tsx:49）；改原生 button，驗證 Enter/Space 展開、收合、
aria-expanded」 is.

## Step 4 — route by layer, never by who noticed

| Layer | Goes to | The finding travels as |
|---|---|---|
| wording, tone, promise beyond evidence | audience-fit Mode B | the row of its proposal table, with 對應程式狀態 filled |
| layout / fill / theming | design, artifact-design, `tools/page-fill-gate` | appearance item |
| interaction, keyboard, focus, race, parse | engineering (frontend-developer / testing-bug-fixer / testing-qa-engineer) | the work item, with its engineering check |
| state model (lossy field, two-path read) | engineering, via the state-model finding | model change + the copy that becomes possible after it |
| service / API contract (error taxonomy, message shape, missing cancel endpoint) | engineering (backend-architect / api-tester), then the front-end row above | the contract change first, then the copy or control it makes possible — never the copy alone (round-3: MFP mapped a user's mistyped path to `usage_error` → 「請求格式錯誤」; no wording fix reaches that) |
| IA — how the world is divided, the entry gate and its default, what an identity is allowed to see, data retention, entry order | **user ruling** (global Interaction-style rule) | a question that carries the finding as evidence — never a unilateral pick, never a bare question; the finding names its `NAV-n` (`navigation-ia-contract.md` §3) |
| routing and addressability — view state in the URL, Back, a shared link opening in a clean session, destinations that are not operable controls | engineering (frontend-developer / testing-qa-engineer) | the work item plus its check; **determinable, so it never goes to 「只有人能判斷」** — the two axes are independent, and a surface can route perfectly while none of its destinations can be reached by keyboard (`navigation-ia-contract.md` NAV-6 / NAV-8) |
| real needs unknown | task research (`usability-evidence.md` §plan) | a test plan, not a guess from code |

Wording findings are handed to audience-fit; audience-fit hands non-wording
findings back here. Neither skill re-runs the other.

## Step 5 — verification, engineering first

Load `references/usability-evidence.md`. Anything a program can determine
does NOT go to UAT: keyboard equivalence, focus return, cancel preserving
data, no path/engine name in a user message (regression test, KnowYourSing
pattern), status derived from one seam, aria-live timing, instructions
that name a region a breakpoint removes. That list is a FLOOR: derive the
checks from the surface's own state model and handlers, add what the
product's contracts imply, and drop an item with a stated reason when it
cannot apply (a CLI has no focus order). Human items enter the
manual-acceptance checklist at their rung (`ops/references/uat.md`): a
hidden state is A3 (observability), comprehension B1, steps/defaults B2,
appearance B3. A test PLAN is written only when the user asks for
observation; the walk itself is UE1–UE2 evidence and says so.

## Step 6 — priority

Order by blocking degree × reach × evidence confidence, stated in words
(NN/g severity vocabulary: catastrophe / major / minor / cosmetic). No
composite numeric score — a number invented to look precise is the
honest-data rule broken at the priority line. Confirmed core-operation
blockers first; wording that changes expectation next; homepage priority
and layout policy last, after task evidence.

## Guardrails

- **Evidence marks are load-bearing.** 已確認 / 推論 / 待測 on every finding;
  「使用者會困惑」 without a mark is deleted, not softened.
- **No invented research.** Task cards say what is assumption; a walk never
  claims what a moderated session would show.
- **No fixed personas.** The same author imports, rereads daily, debugs, and
  shares — density differs per task, not per person.
- **Affordance is a claim** (AssetVault-GUI's own ruling: 「一個承諾若需要靠
  註解解釋才成立，它在介面上就是假的」). A label that promises an operation the
  control does not perform is an over-promise, same rule as copy.
- **Silence is not neutral** (AnnouncementWatchDog ruling 「沉默不是中性的」):
  a grey screen, a tray-only start, an unlabeled empty pane are findings.
- **UX semantics are user decisions.** The walk produces the evidence behind
  the question; it does not settle navigation, defaults, or retention.
- **Preserve accepted behaviour.** A proposed change lists what it keeps;
  a product's own flow contract (DIT SessionLoadActions progressive
  disclosure) outranks a pattern imported from another product.
- **This skill does not edit product code.** It emits findings and checks.

## Delivery shape

Task cards (with marks) → decision-point table → findings (Step 3 records)
→ layer routing → verification list (engineering checks pasted or named;
human items at uat.md rungs) → priority order → open user rulings as their
own section at the top or bottom, never mid-text. The status line carries
the credibility bounds: evidence rungs reached, instrument, data origin
(real / seeded / empty), instrument deviations, and what was not run.

Location (naming over routing): a project surface's record goes into that
project's own round/record folder as `UX_WALKTHROUGH_<date>.md` (DIT:
`docs/rounds/<round>/`), opening with a status line and the open-rulings
table; a `~/.claude` surface's record goes to `outputs/`. The record is
the project's asset, not this skill's — never file it only here.

## References

- `references/task-context.md` — task card, evidence-vs-assumption rule,
  context variants, the 「哪個視窗」 check. Load in Step 1.
- `references/decision-point-contract.md` — the four questions, contract
  fields, string roles, show/disable/hide/remove table, technical detail by
  decision use, wait–cancel–recovery, destructive & discard, empty states,
  single source of truth, affordance claims, layout-change semantics,
  core-path equivalence, label distinctness. Load in Step 2.
- `references/navigation-ia-contract.md` — orientation questions `NAV-O1`–`NAV-O3` and the
  twelve discriminators `NAV-1`–`NAV-12` for any surface with more than one
  destination: whose world the division comes from, entry gates, funnel cost,
  contextual trimming, master–detail, addressability, operable destinations,
  persistence scope, progress honesty, legends. **Questions, not a pattern
  catalogue** — its founding measurement is a surface that passes the whole
  pattern checklist with 0 of 23 destinations reachable by keyboard. Load in
  Step 2 when `NAV-O1` > 1. It carries its own growth contract (§5) and is the model
  if another reference here starts to grow.
- `references/usability-evidence.md` — evidence ladder UE0–UE4 and the claim
  each rung permits, engineering-checkable list, uat.md mapping, task-based
  test plan, metric definitions, severity, small-sample caveats. Load in
  Step 5 and for any test plan.
- `references/calibration-2026-09-07.md` — **this share does not include
  it.** The source environment's copy is a dated calibration record tied to
  the author's own private projects (file:line evidence across a dozen
  local repos, one ruling ledger per project) — it has no portable content
  once those pointers are removed. The methodology it calibrated
  (`decision-point-contract.md`) does not depend on it: build your own
  known-true-positive record from a real surface you have access to, the
  same way this one was built, before doubting a rule on a first run.
