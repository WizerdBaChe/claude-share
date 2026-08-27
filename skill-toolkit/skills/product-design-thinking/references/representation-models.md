# Phase 2–3 detail — Behavior & architecture views (representation models)

Load whenever a design doc needs a view of order, state, interaction, or
concurrency — and at the Phase 0 tier call, for the per-tier default view set.

## The selection principle (一個問題一種主圖)

A view answers ONE question, and every view has blind spots by construction:
block/C4 = 空間與責任總覽 (who owns what), statechart = 局部行為契約 (what
states an entity may occupy), sequence/activity = 運行場景 (what one run does),
Petri net = 並發正確性 (can these overlap, deadlock, starve). Pick the
representation from the question the doc must answer — never one universal
diagram: forcing architecture + data + state + time + resources + exceptions
into one picture destroys both readability and auditability. Views are
projections of ONE design, so names shared across views come verbatim from the
PIM glossary.

**A single view never proves completeness.** A sequence diagram is one
scenario (情境局部性), not the behavior space; a completeness claim rides on
the statechart + decision table, with sequence pairs as scenario evidence.

## Selection table (question → primary view)

| 要回答的問題 | Primary view | Blind spot（這張圖看不到什麼） |
|---|---|---|
| 這個 entity 有哪些狀態、什麼事件/guard 能轉換 | FSM / state machine | multi-actor interaction; data transforms; parallel sub-processes explode a flat FSM |
| 狀態有巢狀、平行區域、暫停後恢復 | Statechart (hierarchical FSM) | cross-component messaging; history/region semantics need prose notes |
| 一次工作如何分支/合流/迴圈/並行、誰負責哪段 | Activity diagram / flowchart (+ swimlanes) | long-lived entity states; message timing |
| 誰先呼叫誰、同步/非同步邊界 (API、agent tool loop、queue) | Sequence diagram | ONE scenario per diagram; global state invisible |
| 執行期哪些元件彼此協作 | Communication diagram | time order weaker than sequence |
| 訊號/狀態在精確時間軸上怎麼變 (HW、protocol、debounce) | Timing diagram | decision logic and data flow; large flows unreadable |
| 多件事能否同時發生；deadlock/資源競爭/starvation | Petri net (slice) | reading threshold high; reachability space blows up — keep slices minimal |
| 人/系統/部門跨泳道完成業務流程、補償 | BPMN | technical detail; object state |
| 資料從哪來、經過哪些轉換、存到哪 | Data-flow diagram | control order; error handling; state machinery |
| 條件組合很多時，規則到底輸出什麼 | Decision table (/tree) | no time dimension — pair with an FSM or activity view |
| 系統發生過什麼 domain event、誰觸發誰反應 | Event storming / event model | exploratory aid, not an executable spec |
| 系統由哪些責任單元構成、部署在哪、依賴方向 | C4 / component / deployment | says nothing about behavior order or state |

## Pairing rules (blind-spot compensation)

- A flat FSM starts sprouting sub-processes inside one state → promote that
  state to a statechart composite; don't add sibling states.
- Transition guards become rule-dense (權限/重試/路由/驗證 combinations) →
  move the guard logic into a decision table beside the INV-n it enforces; a
  table is checkable for uncovered/conflicting combinations, a diagram is not.
- Shared resources or async fan-out (GPU, lock, queue, producer-consumer,
  multi-agent) → ONE minimal Petri-net slice for that subsystem, asking a
  named question (deadlock? starvation? reachability?); the rest of the system
  stays statechart + sequence.
- Hard timing against hardware or a protocol → timing diagram + FSM; a
  sequence diagram covers only the init handshake.
- Business workflow with human roles → activity + swimlanes (or BPMN if an
  outside stakeholder reads it); keep object lifecycles in statecharts.

## Soundness & gap instrument (sibling file)

Selection lives here; whether a CHOSEN view is sound lives in
`view-integrity-checks.md` (same directory, 2026-08-27 second-round intake):
per-view integrity (state×event completeness, boundary reconciliation, …),
cross-view correspondence (ISO/IEC/IEEE 42010:2022-style), and the gap-report
format. Rendering precision and carriers (SVG/HTML/PPTX) live one skill over,
in `diagram-authoring`.

## Where views live in the ladder (views ≠ new document types)

Views are SECTIONS of ladder docs, never a parallel document set: statecharts
and decision tables sit in the PIM beside the invariants they guard; the
C4/block overview is the PIM architecture section; sequence/activity paths and
timing constraints are PSM behavior sections; Petri slices belong to the
Verification concurrency/gap analysis. Mermaid natively renders flowchart,
stateDiagram, sequenceDiagram, and C4-ish block views in .md; Petri nets and
signal timing have no mermaid type — ASCII or a labeled place/transition list
is fine; the analysis question matters more than the drawing.

## Per-tier default view set (tier table: SKILL.md)

- 速寫 Sketch — primary flow (activity/flowchart); a lifecycle statechart only
  if a real lifecycle exists. Two views max.
- 標準 Standard — block/C4-component overview; statechart per lifecycle
  entity; ONE sequence pair (success + failure/retry); decision tables where
  guard-dense.
- 全梯 Full-ladder — the Standard set per subsystem; Petri slices only for
  flagged concurrency questions; timing diagrams only for HW/protocol timing.

## Provenance & status

Intake 2026-08-27 from a user-supplied research memo (Perplexity export with
sources); stable-concept anchors: UML 2.5 behavioral-diagram taxonomy
(uml-diagrams.org; sparxsystems.com), Petri-net analysis (ENS Paris-Saclay
verification notes; arXiv 2212.02754). SDD alignment went to
`document-ladder.md` (intro + §8), not here — one lesson, one destination.
Review-when: only if this file ever starts prescribing tool-specific syntax
(it deliberately doesn't).

**PROMOTED (user ruling 2026-08-27)**: the selection principle + pairing
rules now bind globally via a conditional global CLAUDE.md rule (Engineering
judgement section) pointing at this file; this file remains the owner of the
selection table and pairing detail.
