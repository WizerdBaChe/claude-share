---
name: diagram-authoring
description: >-
  Precision diagram PRODUCTION & gap finding — turn user data / design docs /
  code into visually verifiable diagrams: block/C4, FSM/statechart, sequence,
  DFD, timing, exploded-view product architectures（方塊圖、狀態機圖、時序圖、
  爆炸圖式架構、關聯圖）, incl. reconstructing an EXISTING system (e.g. CPO
  全架構) with an explicit gap report（找缺口）. Carriers: Mermaid sketch,
  precise SVG, self-contained HTML, editable PPTX. Trigger on 畫架構圖、精準繪製、
  把 X 畫成圖、從資料重建架構圖、圖要放進簡報/HTML. NOT data charts/plots
  (→ dataviz), NOT UI mockups (→ design), NOT which-view-selection theory
  (→ product-design-thinking representation-models). Full disambiguation:
  ~/.claude/skill-trigger-dict.md.
---

# Diagram Authoring

Rendering is the LAST step of a diagram, not the first. This skill turns
source material (design docs, code, user-supplied system data) into diagrams
that are precise enough to verify visually AND honest about what the source
cannot answer. Two deliverables every time: the picture, and the gap report.
It is the production counterpart of two theory files it never duplicates —
which view answers which question: `product-design-thinking/references/`
`representation-models.md`; whether a view is sound: `view-integrity-checks.md`
in the same directory.

## Mode router — settle this FIRST

| Ask | Mode | Carrier default |
|---|---|---|
| Explain/discuss with a quick visual, in-chat, disposable | Sketch | mermaid fence / visualize widget — declare "auto-layout, no precision claim" |
| Figure inside a doc (design doc, README, report) | Doc figure | mermaid if auto-layout suffices; inline SVG when position/alignment carry meaning |
| Standalone deliverable to view/share | Standalone | self-contained HTML (inline SVG + pan/zoom) or an Artifact |
| Editable slides humans will present/annotate | Deck | PPTX via anthropic-skills:pptx — native shapes + bound connectors, never baked images |
| Reconstruct an EXISTING system from data and find holes（體檢繪圖、找缺口） | Audit drawing | any of the above + mandatory gap report; precision view-set → `tools/archdiag` (carrier-playbook §archdiag) |

## Workflow

**Step 0 — Source-data gate (the fabrication firewall).** List the inputs
(files, code, user data, prior views). Every node, edge, state, and label
must trace to an input or carry an explicit `[assumed]` tag that lands in
the gap report. Domain diagrams (photonics, hardware, business flows …) are
drawn ONLY from user-supplied data or the environment's own knowledge packs
— never filled in from model memory (knowledge-base standing rule). If the
data cannot support the requested view, say so and draw the supportable
subset with visible holes — a plausible invented diagram is worse than none.

**Step 1 — Pick the representation.** One question, one primary view:
selection table + pairing rules in `representation-models.md`. If the user
asked for "one diagram of everything", split it there and say why.

**Step 2 — Build the structural model, then check it.** Write the diagram as
TEXT first: node/edge table, state×event matrix, participant list. This is
the source of truth and the greppable artifact; every picture is its
projection. Run `view-integrity-checks.md` §1 (per view) + §2 (across the
view set) on the text model, and start the gap report (§3 format) here —
BEFORE rendering, so a hole is never papered over by layout.

**Step 3 — Choose the carrier** per the mode table; precision ceilings and
per-carrier verification: [references/carrier-playbook.md](references/carrier-playbook.md).

**Step 4 — Render** per [references/notation-precision.md](references/notation-precision.md):
one symbol one meaning, legend, shape+color redundancy, grid/alignment
discipline, crossing minimization, hierarchy direction stated once.
**Precision fork**: claims where position carries meaning (alignment,
containment, layer order, adjacency) require explicit coordinates (SVG /
PPTX shapes) — auto-layout mermaid may never carry them.

**Step 5 — Verify in three rungs, in order.**
1. *Structure* (machine): the rendered artifact contains exactly the model's
   nodes/edges/states — DOM reads / parse the SVG / walk the PPTX shapes;
   never by eyeballing a screenshot.
2. *Geometry* (machine): overlap/containment/anchoring asserts — the
   self-check block in notation-precision.md §4 (label bboxes disjoint, edge
   endpoints anchored, everything inside the viewBox/slide). Run the asserts
   in the renderer that produces the delivered pixels; a second renderer is
   corroboration, not a substitute (font metrics differ).
3. *Appearance* (human): browser-pane protocol as hook-enforced (DOM for
   structure claims; out-of-process pixels via SendUserFile for appearance).
   The global visual gate applies unchanged: it "works" only after the USER
   confirms it in the real environment — passing asserts prove the data
   path, not the picture.

Report verification with fixed fields: `visual_review: passed | skipped
(reason) | failed (defect)` plus `correction_rounds: n` — automated
evidence reports as *pending* until the user confirms. Repairs stay inside
the bounded-repair budget (notation-precision.md §4); overruns are
reported, never absorbed.

**Step 6 — Deliver.** The diagram + legend + gap report + the regeneration
source (structural text model and the build script / mermaid source), so the
diagram is re-derivable when the system changes. A diagram whose source
model is lost is a screenshot, not a document. Precision carriers
(SVG/HTML/PPTX) add a receipt — SHA-256 + byte count of model/script and
artifact; a passing Step-5 run freezes the artifact, and any post-freeze
edit reopens Step 5 (freeze/receipt discipline: carrier-playbook.md).

## Handoffs (do not absorb neighboring skills' jobs)

- Charts/plots of DATA (axes, series, distributions, dashboards) → dataviz.
- UI mockups / marketing layouts / screen flows → design (canvas).
- Publishing mechanics of an Artifact page (theming, page structure) →
  artifact-design + artifact-diagramming; this skill owns the diagram's
  content and precision, those own the page.
- PPTX file mechanics (templates, layouts, text frames) →
  anthropic-skills:pptx; this skill owns shape geometry and diagram content.
- Which view answers which question / per-tier view sets →
  product-design-thinking `representation-models.md` (theory stays there).
- The 體檢 that DECIDES what to reconstruct → code-review-deep-checklist
  Mode B (its view audit calls back here for presentation-grade rendering).
- Motion/3D/animated-interactive deliverables → motion-design.

## Pitfalls this skill exists to prevent

- A domain diagram quietly filled from model memory — plausible, wrong,
  unfalsifiable → Step 0 makes every element traceable or `[assumed]`.
- One mega-diagram answering every question and none well → Step 1 split.
- Auto-layout output presented as if positions carry meaning → Step 4 fork.
- "Looks right to me" shipped without the user's visual gate → Step 5.3.
- The picture edited while the text model goes stale → Steps 2/6: the model
  is canonical, the picture is a projection.
- A gap smoothed over by an invented connector → gap report + dashed
  element; on real systems the diagram's job is to EXPOSE the hole.
- Color-only encoding, unreadable in grayscale or with color-vision
  deficiency → notation-precision.md dual coding.

## Reference files

- [references/notation-precision.md](references/notation-precision.md) —
  Physics-of-Notations-derived drawing rules, per-notation conventions,
  geometry self-check spec.
- [references/carrier-playbook.md](references/carrier-playbook.md) — carrier
  decision table, precision ceilings, per-carrier verification &
  regeneration story.
- `../product-design-thinking/references/representation-models.md` — view
  selection (owned there).
- `../product-design-thinking/references/view-integrity-checks.md` — view
  soundness + gap-report format (owned there).
