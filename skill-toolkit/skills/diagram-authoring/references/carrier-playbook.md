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
  below the notation-precision §2 minimum.
- **PPTX**: native shapes + **connectors bound to shape anchors** (they
  survive the user moving boxes — the point of an editable deck). One
  diagram per slide + legend; overflow → a hierarchy of slides with a
  locator, never shrink-to-fit below the font minimum. A baked-image slide
  is a delivery failure except as a locator thumbnail. File mechanics
  (templates, layouts, text frames): anthropic-skills:pptx skill.
- **draw.io / external editors**: only on explicit user request; export SVG
  for verification and note that round-trip fidelity is unverified here.

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
Review-when: a renderer in this
environment changes (mermaid version bump altering layout, a different PPTX
render path) — re-check the precision-ceiling column against it, and re-test
the three environment facts in the section above.
