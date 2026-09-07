# archdiag — instrument maintenance (環境級維護/檢查)

> status: active maintenance doc | born 2026-08-29 (F3 close-out, user directive) | consumer: any session editing this library or auditing the environment
> 導讀（中文）：本檔是儀器的維護契約——「必備 (mandatory)」是事件驅動的硬性步驟，漏做即儀器漂移；「參考 (reference)」是做法備忘。環境級掃描入口在 `ops/references/integrity-sweep.md` check 27。

The library's receipts make frozen deliverables byte-verifiable; the price is
that ANY silent change to emitted bytes is instrument drift. Every item below
is a property of these assets, event-triggered — not a schedule.

> **Share note (this copy).** The commands below name the source environment's
> own deliverable tree (`~/.claude/outputs/diagram-authoring/`), which does not
> ship — it holds one operator's audit drawings. Your equivalent is wherever
> your own `*.build.mjs` scripts and their emitted `*.html` live: the two
> commands are unchanged, only the directory is yours. They are kept verbatim
> rather than rewritten into a shape nobody has run.

## Mandatory (必備) — event-driven, hard requirements

- **M1 — Receipt regression after ANY edit under `tools/archdiag/`.**
  Regenerate every committed deliverable and require a byte-level no-op:

  ```git bash
  for b in ~/.claude/outputs/diagram-authoring/*.build.mjs; do node "$b" >/dev/null || echo "BUILD FAILED: $b"; done; git -C ~/.claude status --porcelain outputs/diagram-authoring/*.html
  ```

  Must print nothing. Any diff = receipts of ACCEPTED artifacts changed →
  either revert the library edit, or it is a version bump under the
  post-acceptance protocol (D-043: report + user-ruled bump; never silent).
  Motivating case: the eol hazard (commit 6fbe14c) — a CRLF checkout would
  have changed every emitted byte with all tests green.

- **M2 — Two-sided calibration after ANY `selfcheck.mjs` edit.** Break one
  known instance (e.g. rename a marker out of DEFS → expect exactly the
  counted `dangling-reference` diagnostics) and restore (→ expect 0). A
  check-set edit shipped without firing its positive control is the
  first-run-green failure class (a checker that has never gone red is
  uncalibrated).

- **M3 — LF pin for every NEW receipt asset, the day it is born.** Any new
  `*.build.mjs` / emitted `*.html` outside the pinned globs must join the
  `.gitattributes` `text eol=lf` block. Template literals inherit SOURCE file
  endings; an unpinned receipt asset corrupts on the next CRLF checkout.

- **M4 — Router acceptance after ANY `route.mjs` / provider edit.** Re-run
  the S2 acceptance (l2b re-route: 15/15 edges, 0 through-node, crossings
  0/0, bend total 15) and M1. Determinism is part of the contract: same model
  ⇒ same routed pts (no randomness, fixed iteration orders).

- **M5 — Enums stay derived.** `NODE_KINDS`/`EDGE_TYPES` derive from
  `emit.mjs` FILL/EDGE keys (schema.mjs imports them). Never enumerate them a
  second time anywhere — a second list is a fork that drifts. Same property
  for the palette (2026-09-05): README's style-token table is the OUTPUT of
  `node tools/archdiag/tokens.mjs` — after any FILL/STROKE/OVL/EDGE edit,
  regenerate it and run `tokens.mjs --check` (text/fill AA 4.5:1 = FAIL;
  edge-vs-page 3:1 = WARN) before M1.

- **M6 — Font-substitution sweep after ANY `emit.mjs` layout edit or
  `selfcheck.mjs` #1 edit (born 2026-09-02, external validation intake).**
  `getBBox()` height includes leading and varies by family (~7% between
  Segoe UI and Noto Sans TC); a PASS measured under one font is a
  source-environment fact, not a portability claim — an external macOS run
  reported 44 `label-overlap` on the same bytes this machine passed. Serve
  every committed deliverable (R1), then in-page force
  `text{font-family:<F>!important}` for each of Segoe UI / Noto Sans TC /
  Microsoft JhengHei / Yu Gothic / Arial, re-run the pair scan with the
  shipped PAD, and require 0 under all five. Noto Sans TC is the tallest
  metric available locally and reproduced the macOS count exactly (44,
  per-view 9/9/7/8/11) — it is the local proxy for the CJK fallback class.
  Do NOT widen PAD or exempt title/subtitle pairs to pass this sweep (user
  ruling 2026-09-02, Q2): fix the layout so the gap has headroom. The
  `receipt` block in `window.__geometryReport` records which font actually
  measured (see selfcheck.mjs) — a report without it is not comparable
  across environments.

## Reference (參考) — procedures

- **R1 — Render-verify recipe**: serve the folder
  (`python -m http.server <port> --bind 127.0.0.1` from a copy dir), navigate
  with playwright-headless (`file://` is blocked), read
  `window.__geometryReport` (`{pass, diagnostics, stats}` — measuring pass
  runs once on load, all panes). Expect one favicon-404 console line from the
  bare server. Screenshots: bare filenames land in the session cwd and only
  the allowed roots are writable — write there, then move
  (carrier-playbook, measured 2026-08-27).

- **R2 — Provider swap (`'archify-adapted'`)**: requires a fresh archify
  clone (scratchpad clones evaporate; the durable copy is only
  `vendor/archify-geometry.mjs`). Build behind the `providers{}` seam; accept
  via the same S2 suite plus an F3-class field round. Trigger to build it at
  all: a field round where `'channel'` fails its targets (eval §7(b)) — do
  not build it speculatively (one interface, one implementation).

- **R3 — Delta discipline**: diff UNROUTED models (`pts` are geometry noise);
  `stripOverlay` recovers a base only when overlay flags are the delta axis —
  cross-check the stripped base against an independent fact (F3 used
  `git ls-tree` of the target's main branch) before trusting the table.

- **R4 — Environment-level check classes this arc surfaced** (apply to any
  instrument, not just archdiag):
  - *Receipt regression* — frozen-artifact byte-stability is silent-failure
    class; executable home: integrity-sweep check 27.
  - *Trigger-carrying metrics* — a recorded trigger condition living only in
    a dated report rots; land it in an executable home
    (code-review-deep-checklist Mode B, Trend-framing rule, 2026-08-29).
  - *UAT debt visibility* — machine-green/human-unverified surfaces
    accumulate silently; count unrun manual gates at checkpoint time and say
    the number out loud (the F3 target had six).

## Log — 2026-09-05: checks #9/#10 + a11y contract; receipts re-issued (diagram-design borrow review P-2)

- **Changed**: `selfcheck.mjs` gained #9 `label-over-node` (a pill's CENTRE inside
  a node) and #10 `shared-anchor` (two different edges' anchors on one border
  side with 0 < gap < grid; gap 0 = deliberate bundle). `asserts.mjs` gained the
  build-time faces of both (pill centre on `pillAt`; shared anchor on model pts)
  and `a11yAsserts(html)` — `role="img"` + `aria-labelledby` → first-child
  `<title id="t-<view>">` + `<desc id="d-<view>">`, ids unique, read from the
  EMITTED page. `emit.mjs` emits the title/desc pair per `svg.dia`; `index.mjs`
  throws `A11Y FAILED` before writing. Record + ledger: the source
  environment's own skill-review record (outputs/, not shipped in this copy)
  §六 B-1/B-2/B-3.
- **M2 calibration, both ways**: build-time 20/20 controls (scratch script —
  gap = grid → 0, gap 0 → 0, gap 4 → exactly 1 naming both edges; pill centre
  in corridor / on the border → 0, inside → 1 naming edge + node; a11y clean
  page → 0, and no-role / title-not-first / duplicate id / labelledby mismatch
  / empty title / no svg each → its named problem; `data-id` is not an id).
  In-page (headless Chromium, a same-origin harness of 1400×900 iframes): the
  7 accepted artifacts PASS with 0 diagnostics; a synthetic positive page fires
  exactly `label-over-node` + `shared-anchor`; its negative twin and a clean
  `build()` page PASS.
- **Threshold decision (ledger, model, reversible)**: the first form of #9
  (pill bbox ∩ node rect) fired 70× across all 7 accepted artifacts — depth
  3–18 px, every pill centre OUTSIDE the node — i.e. border straddles the
  user's visual gates had already accepted, while #1 already forbids a pill
  over node text. The reader-visible defect that remains is a label attributed
  to the wrong object, so the rule is: centre inside ⇒ error. A checker that
  fails every accepted artifact on first run is the instrument's threshold
  being wrong, not seven accepted deliverables being wrong.
- **M6 not triggered**: no layout edit in `emit.mjs` (title/desc do not
  render), #1 untouched; #9's centre is font-immune by construction
  (`text-anchor="middle"` at `pillAt`), #10 reads model pts.
- **M1**: `archdiag-capability-set-v1.html` (not on the library) byte-identical.
  The 7 library artifacts changed bytes by exactly the a11y pair + the in-page
  script — pre-ruled (R-2, record §七 P-2: "a11y 屬性會改 bytes，需重發收據並
  記錄"). Footers untouched; nothing drawn changed. Receipts re-issued:

| artifact | bytes before → after |
|---|---|
| ccfg-retrieval-audit-f1 | 42687 → 46813 |
| claude-home-audit-f1 | 117065 → 122096 |
| dit-audit-f1 | 66789 → 71502 |
| mfp-audit-f3 | 101296 → 106393 |
| mfp-audit-f4 | 40583 → 44530 |
| mfp-audit-f5 | 67800 → 72655 |
| prism-audit-f2 | 76705 → 81752 |

The before/after sha256 pair for each row was recorded at the source, against
the commit the artifacts were frozen at. It is not reproduced here: these seven
pages live in the source environment's own output tree and do not ship with
this copy, so the receipts would be fourteen hashes a reader has nothing to
check them against. What is portable is the ruling above them and the growth
column — an a11y attribute pair plus the in-page script costs roughly 4–5 KB
per artifact, which is what tells you a re-freeze is a byte change and not a
drawing change.

- **R1 addendum**: to read every artifact's report in one evaluate, serve a
  copy dir holding the pages plus a harness page that loads them in
  same-origin 1400×900 iframes and collects `contentWindow.__geometryReport`
  once all are ready (the pattern used above).

## Log — 2026-09-07: the palette's other half stops being a transcription

`tokens.mjs` claimed in its own header to be DERIVED from `emit.mjs` (M5: the
palette is never listed a second time). It was — for `FILL`, `STROKE`, `OVL`
and `EDGE`. Its `TEXT` and `SURFACE` tables were a hand copy carrying a
`grep-verified 2026-09-05` receipt, so `--check` graded seven foreground and
surface values against a snapshot of themselves.

- **How it was found**: writing the acceptance item for the share copy, not by
  reading. The first control reached for — mutate the node title colour in
  `emit.mjs`, expect red — came back **0 fail, exit 0**. A second control on
  `FILL.block` turned it red as expected. One instrument, two halves, only one
  of them wired.
- **Fix**: `emit.mjs` now defines and exports `TEXT` (title / sub / container /
  badge) and `SURFACE` (pill + stroke, container + stroke, page) and uses them
  at every emission site; `tokens.mjs` imports them and states no colour of its
  own. Both controls now fire: title colour → 7 fail / exit 2, `FILL.block` →
  2 fail / exit 2.
- **M1 — receipts**: one emitted byte changed, `background: #fff` →
  `background: #ffffff`, because the page background is now written from
  `SURFACE.page` (it has to be: it is the surface every edge stroke is graded
  against, and a gate may not read a copy of its own subject). Same class as
  the 2026-09-05 a11y change and the same R-2 ruling applies — **the source
  environment's 7 library artifacts' receipts are due for re-issue**; nothing
  drawn changed. In THIS copy the one shipped artifact,
  `architecture-diagramming/capability-set.html`, was rebuilt in the same
  commit; its sha256 starts `b86bc0ae382f`.
- **Generalised**: a file whose header says "derived from X" is making a claim,
  and the only thing that tests it is a control that changes X. This one was
  half-true for two days inside the file that exists to enforce M5.

## Review-when

- A text or surface colour is added to `emit.mjs` → add it to `TEXT`/`SURFACE`
  rather than inline, or `tokens.mjs` silently stops covering it. The tell is a
  hex literal appearing in `nodeSvg`/`viewSvg`/the page CSS again (2026-09-07).
- Playwright/headless-Chrome version change on this machine → `getBBox` font
  metrics may shift §4 label measurements: re-run the in-page check on
  F1/F2/F3 (report stays PASS/FAIL on the same bytes; receipts themselves are
  render-independent).
- Node major upgrade → M1 (emission is pure text; receipts should hold — the
  check is cheap, run it rather than assuming).
