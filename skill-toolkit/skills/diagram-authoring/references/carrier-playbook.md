# Carrier playbook — where a diagram lives, and what each carrier can promise

Load at diagram-authoring Step 3. A carrier is chosen by the deliverable's
consumer and by the precision the claim needs — never by drawing convenience.

## Decision table

| Need | Carrier | Precision ceiling | Verification path |
|---|---|---|---|
| In-chat explanation, disposable | mermaid fence / visualize widget | auto-layout — topology only | source review (Step 5.1); no geometry claims |
| Doc figure, topology is the message | mermaid in .md (artifacts render it natively) | auto-layout | source review + rendered glance |
| Figure where position/alignment carry meaning | inline SVG (script-generated coordinates) | full | geometry asserts (§4) + browser-pane DOM/pixels + user gate |
| Interactive deliverable (pan/zoom, layer toggles, hover detail, drill-down) | self-contained HTML + inline SVG/JS | full | as SVG + interaction checks via DOM-state asserts |
| Shareable page (teammates, later reference) | Artifact (publish the HTML) | full | as HTML; page mechanics per artifact-design / artifact-diagramming |
| Editable deck the user will present/annotate | PPTX via anthropic-skills:pptx | full (EMU coordinates) | script-data asserts + one thumbnail render + user gate |
| Print/export (PDF, PNG) | rendered FROM the HTML/SVG | inherits source | verify the source, then one export spot-check |

## Size presets (viewBox × type ramp) — declare one at Step 1, never resize text to fit

| preset | carrier | viewBox (grid 8) | type ramp (px) | body floor | calibration source |
|---|---|---|---|---|---|
| audit view (archdiag) | HTML, desktop | 1280 × 400–800 — 24 of the 26 accepted views are 1280 wide (two at 1288); height by content, snapped to 8 | title 13 bold / sub-line 11 / edge pill 11 / container title 12; page h1 18, h2 15, tables 12.5 | 11 (asserted in-page, check #7) | the archdiag library's `emit.mjs` (ships here as `architecture-diagramming/archdiag/emit.mjs`); F1–F5 accepted 2026-08-27 … 09-05 |
| owner view (audience-fit A1) | HTML, desktop | 960 × 470–800 (accepted: 540 / 660 / 800 / 470) | node name 15 bold / role 11.5 / edge label 11 / status marker 12–15 bold / legend 11.5 | 11 — the five 10.5 inline squeezes in mfp-f5's owner view are a recorded deviation, not a precedent (R3 forbids squeezing; R12 cuts instead) | the four accepted owner views (ccfg, claude-home, mfp-f3, mfp-f5) |
| deck (PPTX) | 16:9 slide | per `~/.claude/rules/office-deck-deliverables.md` | [assumed] name ≥ 18 pt / role ≥ 14 pt / label ≥ 12 pt; CJK body ≥ 12 pt is the borrowed diagram-design "presentation" guidance | 12 pt [assumed] | UNCALIBRATED here — calibrate at the first deck render that passes the user's gate, then drop the tag |

A preset fixes the canvas and the ramp together; a diagram that does not
fit changes its node set (presentational: R12 cut order; audit: split the
view at the Step 1 hierarchy rule), never its type size.

## Per-carrier notes

- **Mermaid**: the fastest honest sketch. Auto-layout means positions are
  the renderer's choice — never claim alignment/adjacency meaning. When a
  mermaid figure grows precision needs, port the structural model to SVG;
  the Step-2 model makes that a re-render, not a redraw. (Petri nets and
  signal timing have no mermaid type — labeled place/transition lists or
  SVG; `representation-models.md` says the analysis question matters more
  than the drawing.)
- **SVG**: the precision workhorse. Script-generate coordinates from the
  structural model wherever possible — layout code is reviewable, while
  hand-placed numbers drift. Keep the generation script/data next to the
  artifact (Step 6 regeneration rule).
  Defs discipline: emit ONE `<defs>` block per document and let the §4
  reference-resolution check prove every `url(#id)` resolves — a dangling
  marker renders as a silently missing arrowhead (F1 v1.0 incident,
  2026-08-28). Sequence views on this carrier (field-proven F2): lifelines
  = narrow full-height CONTAINER rects (through-node-exempt by class,
  borders anchorable), headers = separate nodes, messages = horizontal
  edges at distinct y — the block-diagram assert set then holds unchanged;
  activation bars may be declared-omitted.
- **HTML**: adds interaction; keep it self-contained (no external assets —
  required for Artifacts, healthy everywhere). Layer toggles and hover
  detail are how ONE deliverable serves both overview and depth without a
  mega-diagram — each toggleable layer still passes its own view checks.
  If it can fail at runtime (fonts, JS init), failures must announce
  themselves (global rule) — a silent blank canvas is a defect.
  **Containment measurement** (B-5): before delivery, assert at named
  desktop viewports (1440×900 and 1920×1080 minimum)
  `document.documentElement.scrollWidth <= window.innerWidth` and
  `scrollHeight <= window.innerHeight` — no horizontal page scroll, first
  screen holds the diagram. Repair by redistributing authored layout;
  never by `overflow:hidden`, clipping, an inner diagram scroller, or text
  below the notation-precision §2 minimum. **Lower bound (2026-09-04)**: the
  same delivery runs `~/.claude/tools/page-fill-gate/fill_gate.py` on the
  file with `<html data-page-class="diagram">` declared — a centred container
  with symmetric margins passes, a left-anchored cap (`max-width` without
  `margin:auto`, as in one of this environment's own delivered views) fails;
  containment says "not too wide", the fill-gate says "not left-hugging".
- **PPTX**: native shapes + **connectors bound to shape anchors** (they
  survive the user moving boxes — the point of an editable deck). One
  diagram per slide + legend; overflow → a hierarchy of slides with a
  locator, never shrink-to-fit below the font minimum. A baked-image slide
  is a delivery failure except as a locator thumbnail. File mechanics
  (templates, layouts, text frames): anthropic-skills:pptx skill.
- **draw.io / external editors**: only on explicit user request; export SVG
  for verification and note that round-trip fidelity is unverified here.

## Audit view-set toolchain (this machine): the archdiag library

For audit-drawing view sets (C4 / statechart / DFD / sequence panes with the
in-page §4 self-check), do NOT hand-author a per-file framework — that class
drifted within one day (F1↔F2 check-set divergence, the S1 motivating case).
Build through the archdiag library (ships here as
`architecture-diagramming/archdiag/`):

- `build()` (index.mjs): schema validation (`ev` evidence anchors required on
  every node/edge — Step 0 enforced mechanically) → build-time geometry
  asserts → marker closure → deterministic emission → sha256 receipt line.
  Byte-stable: identical model ⇒ identical bytes.
- `route(view, {grid})` (route.mjs): orthogonal corridors + pill placement
  behind the `RouterProvider` seam (default `'channel'`). Author node rects
  by hand (positions carry semantics — D-042); leave edges without `pts`,
  then `applyRoutes()`. Field-accepted F3 2026-08-29: 89/89 edges routed,
  0 corridor hand-fixes (F1/F2 baseline: 4–5 per round), first-render §4
  PASS, user visual gate passed incl. corridor aesthetics. The named
  alternative `'archify-adapted'` stays spec'd-not-built.
- `delta.mjs`: model differ (B-9 automation) — `stripOverlay()` recovers the
  base from an overlay-flagged view; diff the UNROUTED models (routed `pts`
  are geometry noise). Absent-type edges are counted apart by design.
- Verification: serve + navigate per the headless notes below, then read
  `window.__geometryReport` — `{pass, diagnostics, stats}`; the measuring
  pass runs once on load with every pane rendered (no tab-clicking needed).
- Invariants and the maintenance ritual (receipt regression after ANY library
  edit, selfcheck calibration, eol pins):
  `architecture-diagramming/archdiag/README.md` +
  `architecture-diagramming/archdiag/MAINTENANCE.md`; environment sweep
  item: integrity-sweep check 27.

Reference builds (mfp-audit-f3 routed — current pattern; dit-audit-f1 /
prism-audit-f2 hand-routed pts, frozen receipts) stay in the source
environment's deliverable tree. In this share the library itself ships as
`architecture-diagramming/archdiag/`; its README carries the `build()`
contract a build script is written against.

## Source-of-truth & regeneration

The structural text model (Step 2) plus the generation script IS the
diagram; carriers are outputs. Store model + script beside the deliverable
(repo: next to the doc; deck: a notes slide naming the path). Re-rendering
after a system change starts from the model — editing pixels/shapes directly
and back-porting later is the drift path. If the user hand-edits the PPTX,
the next regeneration DIFFS against the model and reports; it never silently
overwrites their edits (previously-accepted-work rule).

**Freeze + receipt** (B-3): the delivery note records SHA-256 + byte count
of the model/build script AND of each rendered artifact. A passing Step-5
run freezes the artifact; any later edit — appearance-review fixes
included — reopens Step 5 before the receipt is re-issued. An artifact
that no longer matches its receipt is not the delivered artifact.

## Deliverable location & verification environment (this machine)

Adopted from the first field test (FT-1/FT-3/FT-5; the gap ledger stays in
the source environment's review records):

- **Location**: work belonging to a project lives in that project's tree;
  environment-level or standalone runs deliver to
  `~/.claude/outputs/diagram-authoring/` (owner-first filenames). Derived
  renders (screenshots, exports) stay untracked — the HTML/model is the
  record and regenerates them.
- **Headless verification**: this environment's playwright-headless blocks
  `file://` — serve the folder briefly (`python -m http.server <port>
  --bind 127.0.0.1`), navigate to localhost, and expect one harmless
  favicon-404 console line from the bare server.
- **Screenshot paths**: a bare filename lands in the SESSION cwd, not
  beside the page — and playwright-headless only writes inside its allowed
  roots (measured 2026-08-27: `%TEMP%\claude-playwright-mcp` and `~/.claude`;
  a scratchpad absolute path is refused). Write into an allowed root, then
  move the file where it belongs.

## Provenance

2026-08-27, born with diagram-authoring. 2026-08-28: freeze/receipt and
containment measurement adopted from tt-a1i/archify (MIT); the borrow
ledger (B-3/B-5) stays in the source environment's review records.
2026-08-28 (F2 field round): SVG defs discipline + sequence-as-containers
pattern.
Review-when: a renderer in this
environment changes (mermaid version bump altering layout, a different PPTX
render path) — re-check the precision-ceiling column against it, and re-test
the three environment facts in the section above.
