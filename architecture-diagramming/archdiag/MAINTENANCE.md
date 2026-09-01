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
  second time anywhere — a second list is a fork that drifts.

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

## Review-when

- Playwright/headless-Chrome version change on this machine → `getBBox` font
  metrics may shift §4 label measurements: re-run the in-page check on
  F1/F2/F3 (report stays PASS/FAIL on the same bytes; receipts themselves are
  render-independent).
- Node major upgrade → M1 (emission is pure text; receipts should hold — the
  check is cheap, run it rather than assuming).
