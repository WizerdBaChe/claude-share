# archdiag — shared library for audit-drawing deliverables

Single-source framework for the diagram-authoring skill's precision SVG/HTML
deliverables (C4 / statechart / DFD / sequence audit view-sets). Extracted
2026-08-29 as **S1** of
`outputs/diagram-authoring/selfbuild-scope-eval-2026-08-28.md` from the union
of `dit-audit-f1.build.mjs` v1.1 and `prism-audit-f2.build.mjs`.

**Why it exists**: per-file copies of the assert/self-check framework drifted
within ONE day (F1 v1.1 carried check #8, the frozen F2 script did not —
false-confidence risk). This library is the single source; the drift class is
dead only while the invariants below hold.

## Invariants (properties of the asset)

- `selfcheck.mjs` is the ONLY source of the in-page §4 check script. A build
  script that embeds its own copy of any check reintroduces the drift defect.
- `pageHtml` is deterministic: identical input (views + doc strings + notes)
  ⇒ identical bytes (receipt-friendly). Anything nondeterministic (dates,
  randomness) must come in via the input, never be generated here.
- `schema.mjs` rules only on what it can determine (types, enums, id
  resolution, declaration shape); every problem it reports is a build FAIL
  (determinable ⇒ FAIL). Semantics — aggregation, view choice, node
  positions — stay human and are never validated.
- Enum sources: node kinds derive from `FILL` keys, edge types from `EDGE`
  keys (both in `emit.mjs`). Never enumerate them a second time.
- Marker closure: every `EDGE[*].marker` (and `mFill` for init arrows) must
  resolve inside `DEFS` — checked at build time in `index.mjs` (the
  determinable face of in-page check #8).

## Modules

| file | contents |
|---|---|
| `index.mjs` | `build(opts)` — schema → build-time asserts → marker closure → emit → write + sha256 receipt line. Throws on any problem (B-1-style list in the message). |
| `schema.mjs` | `validateViews(views)` structural validation (B-7); `NODE_KINDS`, `EDGE_TYPES`. |
| `asserts.mjs` | `buildAsserts(views, grid)` — grid snap, anchor-on-border, orthogonality (pre-write, on model data). |
| `selfcheck.mjs` | `inPageScript({grid, viewCount, notes})` — in-page §4 checks #1–#8 (label overlap, anchors, viewBox clip, grid, edge-through-node, crossings-vs-declared, font floor, url(#id) reference resolution) + instrument preconditions (no transform in scene; scene must render) + tab handler (the measuring pass depends on it). B-1 diagnostic objects; `window.__geometryReport`. |
| `emit.mjs` | `FILL/STROKE/OVL/EDGE` styling, `esc/cjkW`, `nodeSvg/viewSvg` (ov overlay + 未驗收 badge, absent ✕ edges, multi-inits, lifeline containers), `DEFS`, `pageHtml`. |
| `tables.mjs` | `table(headers, rows)` HTML table emitter. |
| `route.mjs` | S2 — `route(view, {provider, grid})` orthogonal edge router + pill placer behind the `RouterProvider` seam (default `'channel'`); `applyRoutes(view, result)` splices results back. Node positions are inputs, never outputs (D-042). Never silently exceeds `declaredCrossings` — returns B-1 diagnostics proposing declarations/hints instead; a failed edge is named for hand authoring (assist-mode degradation is the same path). Named alternative provider `'archify-adapted'` is spec'd, not built — one interface, one implementation until field trial F3 demands the second. |
| `delta.mjs` | S3 — `diffViews(base, head)` model differ (added/removed/changed, geometry-vs-semantic classes, absent edges counted apart, overlay suggestions); `stripOverlay(views)` recovers a base model from an overlay-flagged one; `deltaTableRows`/`deltaMarkdown` emitters. Replaces F2's measured ~12-min hand B-9 procedure. |
| `vendor/archify-geometry.mjs` | Geometry primitives vendored verbatim from tt-a1i/archify (MIT, clone `12106be` 2026-08-28; consent 2026-08-29 eval §8 Q3). Upstream rect shape `{x,y,width,height}` — adapt at call sites, never edit in place. |

## build() contract

```js
import { build } from '../../tools/archdiag/index.mjs';
import { table } from '../../tools/archdiag/tables.mjs';

build({
  outPath,            // absolute output path
  grid: 8,            // grid unit (asserts + in-page GRIDU)
  doc: { lang, title, h1, legendbar, footerNote },  // trusted raw text/HTML
  views,              // the structural model (IS the diagram; SVG is a projection)
  sections: [{ h2, html }],  // tables between the panes and the geo report
  selfcheckNotes: { precond2, check8 },  // OPTIONAL provenance comments —
  // artifact content, not logic. F1 passes its v1.1 history verbatim to stay
  // byte-identical; omit for new artifacts (generic defaults).
});
// => { html, bytes, sha256 }  (also written to outPath + receipt line logged)
```

View-model strings are escaped; `doc` strings and `sections[].html` are
trusted raw (legendbar carries markup by design).

## Extraction acceptance (2026-08-29, S1)

- F1 v1.1 regenerated through the library **byte-identical**: sha256
  `172fda6b…54e` unchanged, first run — receipt unchanged, no version bump.
- F2 regenerated as v1.1 (sha256 `dea22b65…bde`): diff-scope audit proved
  every change ∈ {script upgraded to union (== F1's accepted script with two
  provenance comments genericized), footer v1.1 sentence, 40 non-ov node-rect
  `" />"`→`"/>"` normalizations}; layout geometry untouched.
- In-page self-check PASS on both (headless DOM read); view stats equal the
  frozen values. Positive control: renaming `#mOpen` out of DEFS produced
  exactly 30 `dangling-reference` diagnostics (the counted references) and
  restoring produced 0 — the instrument discriminates in both directions.
- Union checklist verified mechanically at extraction: all 10 diagnostic
  codes present; the five shared blocks (helpers, DEFS, CSS, table helper,
  build-time asserts) were byte-identical across F1/F2 before extraction —
  the only drift was the self-check set, as diagnosed.

## S2 acceptance (2026-08-29, automated half)

Re-routed F2's l2b view from its model minus pts/pillAt through the
`'channel'` provider: 15/15 edges routed, 0 through-node, crossings 0/0
(= declared budget), every pill placed, ~35 ms; candidate page built through
the full pipeline and the in-page §4 run PASSED with 0 diagnostics (real
getBBox, 1128 label pairs). Bend total 15 = the hand layout's 15 (two edges
beat the hand route by one bend; one spread-slot edge pays two). elkjs
targeted search (kickoff pre-work): ELK's edge-routing-only mode exists as
the libavoid module; the elkjs-side wrapper is third-party
`@mr_mint/elkjs-libavoid` 0.5.x (wasm) — not a mature thin-wrap fit for this
zero-dependency, byte-deterministic pipeline, so the self-built provider
stands (eval §7(c) condition not met).

## F3 field acceptance (2026-08-29) — S1+S2 joint, COMPLETE

Fresh target (media-fetch-pipeline, user-chosen) drawn end-to-end through the
library + `'channel'` router: 5 views, 79 nodes + 8 containers / 89 edges,
node positions hand-authored, every edge path and pill anchor machine-routed.
Measured vs the F1/F2 baselines (pre-registered:
`outputs/diagram-authoring/mfp-audit-f3-measurement.md`):

- corridor hand-fixes **0** (F1: 4, F2: 5) — target met; pill fixes 0;
  router diagnostics → declarations 0.
- §4 fail rounds: build 1 (model typo, caught by B-7 schema) + render **0**
  (first-pass PASS, 0 diagnostics, 4,748 label pairs).
- crossings within declared budgets everywhere (tsm 1/2, txd 1/1, rest 0/0);
  ~35–60 ms per view.
- delta.mjs field use: `stripOverlay(txd)` = main state, cross-checked
  against `git ls-tree main`; +11 nodes/+19 edges/+1 absent, 0 spurious.
- **User visual gate PASSED** (2026-08-29), incl. machine-corridor
  aesthetics — `'channel'` is the standing provider; eval §7(b)/(c) overturn
  conditions both closed. `'archify-adapted'` stays spec'd-not-built (build
  trigger: a field round where `'channel'` misses its targets).

## Maintenance

Event-driven ritual (receipt regression, selfcheck calibration, LF pins,
router acceptance, provider swap): [MAINTENANCE.md](MAINTENANCE.md).
Environment sweep item: `ops/references/integrity-sweep.md` check 27.

## S3 acceptance (2026-08-29)

`diffViews(stripOverlay(F2), F2)` reproduces the hand B-9 row exactly:
nodes +8 (RTE/RTA/EVD/ATL/PRS/ESV/EATL/RELP), edges +9
(r2/r3/s1/s5/s6/f8/f9/f10/f11), contractual non-edges +1 (s7), zero spurious
deltas. Calibration: four injected mutations (node removal w/ its 3 edges,
semantic retitle, geometry-only move, pill reword) each reported in the
right class, untouched views quiet — the differ demonstrably fires in both
directions.
