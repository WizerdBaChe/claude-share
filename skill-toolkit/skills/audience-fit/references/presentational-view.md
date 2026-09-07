# Presentational view — the A1 rendering profile

> Loaded by audience-fit Mode A1 (same-spec audience re-render). Born from
> round-1 G-6 (2026-08-30); rewritten the same day after G-7 — the first
> A1 render copied the WRONG feature of its archetype and was rejected.

## What the archetypes teach — and what they must not

The user-supplied examples (a paper's classification figure; a public
"Life OS"-style architecture map) teach exactly one thing: **turning
concrete program behaviour into few, reader-named, truthful nodes** —
每個節點是讀者語言的名字＋一行角色，元素數量極少，內容全部為真。

They are NOT layout templates. Copying the layered card-grid produced
「完全平級」rows that read as grade-classification — a summary table, and
harder to read than a diagram (user rejection, 2026-08-30). Re-analyse
layout per artifact; never transplant it.

## Rules

- **R1 One page, one reader question** — usually 「這系統是什麼、現在
  健康嗎」. Anything answering a different question goes elsewhere.
- **R2 Nodes AND edges — a diagram, not a card grid — on a counted
  budget.** An architecture view keeps node 感: boxes joined by drawn
  flows, where every arrow states a real call/feed relationship and
  position encodes flow in one consistent direction. A layout where
  adjacency substitutes for connection is a table wearing a diagram's
  clothes. Aggregate the engineering model to capability-level nodes, then
  draw the edges that actually exist between them. Two dials, declared
  before drawing (diagram-authoring Step 1 close-line):
  - *Count dial* — the ladder is calibrated from the accepted A1 renders,
    not borrowed: 「全景」 one page = the standing tier — the four accepted
    owner views produced between 2026-08-30 and 09-05
    hold 11–24 named nodes, 12–27 connectors, 4–14 edge labels; target
    ≤ 18 nodes / ≤ 24 connectors, hard ceiling 24 / 27 (the largest
    accepted instance sits there and reads as the limit, not the norm).
    「精簡」 inset / slide panel = ≤ 9 nodes [assumed — no accepted
    instance yet; calibrate at the first one]. Over the ceiling → cut in
    the R12 order, never squeeze type (R3) or spacing (R10).
  - *Wording dial* — who reads: 「owner」 = 白話名稱 + one-line role, no
    file names or paths (R3 as written); 「operator／同事」 = the same, plus
    the canonical name in parentheses on at most one line per node. The
    dial changes text, never the node set.
- **R3 Author-controlled text.** Node text = 白話名稱 (+ English term
  where needed) + at most one sub-line role. Line breaks are chosen by
  the author — fixed canvas / explicit tspans — never left to auto-wrap:
  meaningless CJK mid-word breaks are a named defect. No file names, no
  module paths, no evidence codes.
- **R4 Status is first-class and honest**: 未驗收 / 已知缺陷 / 等裁決 as
  markers anchored ON the affected nodes (footnote style ①② with a
  caption list is fine). Truth markers may MERGE under aggregation, never
  disappear — an aggregated node is as unverified as its most-unverified
  member.
- **R5 Aggregation carries its mapping**: a collapsed table (node →
  canonical elements → **cut**: what R12 removed at which rung, or 「—」)
  lives in the page. The presentational view carries NO completeness
  claim — the canonical model does; the footer says so. The cut column is
  how a reader learns what the page does not show without opening the
  canonical page.
- **R6 Flows show the happy path plus NAMED side-states.** Never draw a
  transition or edge the system does not have; simplification is
  omission, never invention (whitelist truth).
- **R7 No imported chrome.** No icon ornaments, no decorative metrics,
  and no SaaS/Tailwind card aesthetic — uniform rounded-corner cards in
  soft-bordered grids are a named user rejection. The reference look is
  the plainness of a paper figure.
- **R8 Carrier parity**: same carrier as the original (HTML → HTML,
  PPTX → PPTX); the reader gets the same KIND of artifact.
- **R9 Visual venue sampling** (B-4 applied to the visual register):
  before importing any external style, inherit the CANONICAL artifact's
  already-accepted visual vocabulary — its color and shape semantics,
  simplified (e.g. keep 藍＝模組/膠囊＝外部/琥珀＝資料/綠＝狀態/橘虛框＝
  未驗收 from the source audit page). The canonical is usually the one
  visual venue the user has already accepted.
- **R10 Snap or separate — the near-coincidence band is forbidden.** The
  eye reads exact coincidence as structure, clear difference as intent,
  and near-coincidence as ERROR. This governs every geometric relation,
  not just one: parallel runs are either bundled on one shared path or
  ≥ ~20px apart (measured failure: 2px, read as one smudged line);
  centers are either on the same anchor line or a whole column apart
  (measured failure: child 40px off its parent's centerline, and the two
  edges touching it turned almost-but-not-vertical); an edge is
  axis-straight, an orthogonal elbow, or clearly diagonal (≈30° or more)
  — never almost-straight; an endpoint touches the border it points at or
  keeps a uniform marker gap — never a stray 2px short. Both round-1
  visual defects (G-8, G-9) were instances of this one band.
- **R11 Positions derive from named anchors — no per-element numbers.**
  Declare the column centerlines, row baselines, and border ports ONCE
  (a comment block inside the artifact) and derive every node center and
  edge endpoint from them; alignment then holds by construction, and an
  edit moves a column, not a box. Hand-picked local coordinates are how
  the near-coincidence band gets entered by accident — each raw number is
  an unchecked collision bet (270/334 happened to be clean; that was
  luck, not design). Before delivery, run the closing sweep as a
  checklist, not a glance: every edge's dx/dy classified against R10's
  three allowed kinds, every parallel pair's gap, every endpoint's border
  contact, every label's clearance.
- **R12 Fixed cut order — when the R2 ceiling is exceeded, cut in this
  order and nowhere else** (borrowed as structure from diagram-design's
  degrade ladder, 2026-09-05; rungs re-derived from R3–R6): (1) role
  sub-lines on leaf nodes → (2) edge labels that carry no status and
  resolve no direction ambiguity → (3) merge sibling leaves into their
  parent (truth markers merge, R4) → (4) drop leaf nodes with one edge and
  no marker → (5) split into a second page with its own reader question
  (R1). NEVER cut: a status marker (R4), an edge between surviving nodes
  (R6), the mapping table (R5). Every cut is a row in the R5 cut column
  with its rung number; a cut nobody can find in the table is an
  invention by omission.

## Boundary note (standing until ruled otherwise)

Precision drawing machinery — corridor routing, geometry self-checks, gap
tables — is diagram-authoring territory and is deliberately NOT reproduced
here: a presentational view does not carry the completeness claim, so it
does not need the instrument that proves one. If diagram-authoring later
gains a presentational view type, this file becomes the audience PROFILE
handed to it (who, what survives, what aggregates, what stays visible),
and the rendering moves there.
