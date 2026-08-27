# Notation precision — drawing rules & geometry self-checks

Load at diagram-authoring Step 4. Theory anchor: D. Moody, "The 'Physics' of
Notations" (IEEE Trans. Software Engineering, 2009) — nine evidence-based
principles for cognitively effective visual notations; principle names appear
in parentheses so the source stays traceable (list verified by web search
2026-08-27).

## 1. Symbol discipline

- One symbol = one meaning across the WHOLE deliverable, and one meaning =
  one symbol (semiotic clarity). No symbol overload between figures of the
  same doc — if a rounded box is "state" in one figure it is not "process"
  in the next.
- A legend becomes mandatory the moment a second node or edge type exists;
  it lists every type actually used, no more. Keep distinct symbol count
  ≤ ~6 per diagram (graphic economy); over that, split the view or encode
  with labels instead of new shapes.
- Never encode by color alone — pair color with shape, line style, or an
  icon (dual coding); grayscale printing and color-vision deficiency both
  break color-only. Text labels complement, never replace, the visual
  variable.
- Distinct types differ on ≥2 visual variables (shape+color, shape+border)
  so they stay tellable at small size (perceptual discriminability, visual
  expressiveness).
- Prefer shapes that hint their meaning — cylinder = store, slotted bar =
  queue, stick figure = actor (semantic transparency) — but the hint never
  substitutes for the legend.

## 2. Layout discipline

- One axis, one meaning, stated once per figure: "time flows left→right",
  "dependencies point downward", "layers stack top→down". Never two
  meanings on one axis (cognitive fit).
- ≤ 7±2 primary elements per view level; over that, promote to a hierarchy
  level with boundary reconciliation (complexity management — the
  reconciliation CHECK lives in view-integrity-checks.md §1).
- Multi-view deliverables carry navigation cues: identical element names,
  plus a locator ("this figure zooms block X of fig. 1") (cognitive
  integration).
- Grid snap — pick one unit (8px SVG / 0.125in PPTX) for positions AND
  sizes; siblings share dimensions unless a size difference carries
  meaning.
- Orthogonal edge routing for block/architecture diagrams; crossing target
  0, declare when >3 are forced; an edge never passes THROUGH a node;
  parallel edges keep uniform spacing.
- Labels horizontal; never overlapping edges or other labels (asserted in
  §4); edge labels sit at the midpoint or at the owning port.
- Minimum rendered font ≥ 11px at 100% zoom for body labels; text contrast
  ≥ 4.5:1 against the actual fill behind it (WCAG AA).

## 3. Per-notation conventions

- **Block / C4 / exploded**: ports drawn ON the boundary; when interface
  identity matters, edges attach to ports, not to arbitrary box points.
  Exploded product views: numbered callouts, ONE level of explosion per
  figure, parent silhouette/locator kept visible.
- **FSM / statechart**: initial marker + terminal ring; transition labels
  `event [guard] / action`; self-transitions loop outside the node;
  history/parallel notation only together with the prose semantics note
  (view-integrity-checks §1).
- **Sequence**: lifelines equally spaced; activation bars shown; async
  arrows open-headed vs sync filled — and the legend says so; the scenario
  name is in the title.
- **DFD / pipeline**: uniform flow direction; stores/externals visually
  distinct from processes; error flows dashed AND colored (dual coded).
- **Timing**: shared time axis with units and tick marks; every constraint
  arrow carries value + tolerance.
- **Dense diagrams — numbered-chip labels** (adopted from field test FT-2):
  when on-canvas edge labels would collide (a §4 label assert fails, or
  clearly will), replace edge text with small numbered chips colored per
  edge type, placed at collision-free points, and carry the full contracts
  in a numbered table beside the diagram. The canvas stays clean, the
  contract stays complete, and chips stay checkable (§4).

## 4. Geometry self-checks (machine rung — run before any pixel claim)

For SVG/HTML carriers, run in-page JS (browser-pane protocol: these are DOM
reads, no screenshots involved):

- every label `getBBox()` disjoint from every other label bbox (padding ≥2px);
- every edge endpoint within ε (2px) of its declared node/port anchor;
- union of all element bboxes ⊆ viewBox (nothing clipped);
- declared grid honored: snapped x/y ≡ 0 (mod grid unit);
- no edge segment passes THROUGH a solid node it does not terminate on —
  segment×rect intersection test, containers and the edge's own endpoints
  exempt (added 2026-08-27: endpoint anchoring alone missed a pass-through
  that only the appearance rung caught — the assert set itself needs the
  calibration the §2 rule implies);
- font-size ≥ the §2 minimum; text/fill contrast ≥ 4.5:1;
- numbered chips (when used, §3) disjoint from every non-container node rect.

For PPTX: shape coordinates are deterministic EMU values from the build
script — assert the same invariants on the script's data BEFORE writing the
file, then one rendered-thumbnail check for appearance.

A failed assert is a layout bug to fix, not a note to ship. These asserts
prove geometry only — the human appearance gate (SKILL.md Step 5.3) still
applies after them.

## Provenance

Distilled 2026-08-27 from Moody 2009 — nine principles: semiotic clarity,
perceptual discriminability, semantic transparency, complexity management,
cognitive integration, visual expressiveness, dual coding, graphic economy,
cognitive fit (verified via web search 2026-08-27) — plus standard UML/C4
drawing practice. Review-when: a carrier appears whose geometry cannot be
asserted (e.g. hand-drawn import) — add its verification story there or
refuse precision claims on it.
