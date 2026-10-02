---
paths:
  - "**/figs/**"
  - "**/*pptx*.py"
  - "**/*.pptx"
  - "**/draw_*.py"
  - "**/build_fig*.py"
  - "**/specs_*.py"
  - "**/instruments/assembly_figure/**"
review-when: a generator gains a real obstacle-aware router (orthogonal or spline leaders around every drawn object) — tier C then becomes the instrument's default and §2 rows 1–2 shrink to its gate; or the user reclassifies a deck class in rules/office-deck-deliverables.md
---

# Layout convergence: fixed tiers, flexible routing, a counted stop

Written 2026-09-15 from the user's ruling on SSLD T04 (a crowded three-view figure whose
labels and leaders collided; three layout patches, one representation change, a full
22-figure rebuild after each): 「確保資料重要層級，要優先提供以及和其他元素一起搭配展示的保持
不動，線段改由曲線或多直角折線來達成，避免很多無意義反覆改動」「簡報出圖速度不應該慢，主要慢在
驗證跟重試」「嘗試無效且各種解法都試過也達到一定數量（要明定）就停止重試並選擇表示呈現問題」.
Index line lives in `CLAUDE.md`. Builds on `ops/30-judgment.md` R4 (change approach after two
same-category repairs) and `ops/lessons.md` L-044 / L-095; does not loosen any gate tolerance
(`references/claude-config-decisions.md` D-053): a stop DECLARES a defect, it never re-measures
it away.

## §1 Tiers — what may move to resolve a layout conflict (asset property of a figure/slide)

| tier | objects | on conflict |
|---|---|---|
| **A fixed** | the drawing / data geometry and its scale; title; primary values; elements presented TOGETHER (a view and its legend band, a figure and its table) | never moved, resized or reordered to make room |
| **B banded** | labels, dimension texts | move only inside their own band (above / below / side lane), never into tier A |
| **C routed** | leaders, connector lines | reshape freely: orthogonal (multi right-angle) or curved route around obstacles, any length, any number of bends |
| **D degradable** | secondary text, basis notes, long explanations | shorten ONCE, then move to a callout number (①) with a key, to speaker notes, or to the foot note |

Resolution order for any overlap / crowding finding: **C → B → D**, and A is not on the list.
A fix that moves a tier-A object to clear a label is the named defect this rule exists for.

## §2 Known futile-adjustment classes and the move that replaces them

| # | futile loop (measured instance) | replacement |
|---|---|---|
| 1 | nudging label positions / row caps to clear a leader (T04: 3 patches, each moved the crossing) | route the leader (tier C) first; then band move; then callout number |
| 2 | fitting a key/legend beside a labelled drawing (T04, L-095) | key in its own band outside the view (tier A pair with the view) |
| 3 | 0.5 pt font steps / box widening for text in a fixed band | carrier change (rules/office-deck-deliverables.md "fixed-height band"); conclusion decks: WARN |
| 4 | edge, footer-band, orphan-wrap findings on a conclusion-class deck | WARN line, no rebuild (office-deck-deliverables class table) |
| 5 | rewording a label repeatedly to fit | one shortening; the rest goes to tier D |
| 6 | full rebuild of every figure to test a one-figure fix (T04: 22 figures, >10 min each run) | iterate on the affected figures + one untouched control; ONE full build at the end |
| 7 | re-reading every raster after every iteration | iterations read only changed / flagged figures; the full read record (rules/figure-self-read.md) is written once, on the final build |
| 8 | a long build in the foreground that times out, or a background build started before the spec edit (T04 stale run) | run long builds in the background from the start, regenerating their inputs in the SAME command |
| 9 | chasing pixel parity between two emitters (PNG vs editable PPTX measure text differently) | parity only for overlap / wrong text; appearance differences between emitters are accepted |
| 10 | adjusting a gate threshold until the finding disappears | forbidden (D-053); fix by §1 or stop by §3 |

A new loop joins this table only with its measured instance.

## §3 The counted stop (per symptom, per deliverable)

A **cycle** = one layout change for one symptom followed by a rebuild + verification. A
diagnostic that changes nothing is not a cycle. Two findings are the same symptom when they
name the same object pair class (e.g. leader × label), wherever they relocate.

| deck / figure class | tweaks (same representation) | representation changes | cycle cap |
|---|---|---|---|
| **conclusion** (結論式) | 1 | 1 | **2** |
| **presentation** (展示用) | 2 | 2 | **4** |

- After the tweak allowance is used, the next cycle MUST be a representation change (R4).
- At the cap: **stop retrying.** Ship the best attempt (fewest blocking findings, tier A intact),
  and declare the residue: a `WARN residual-layout <symptom> after <n> cycles` line in the build
  output, one row in the verify record naming what was tried, and — when the defect is visible
  to the audience — a one-line note in the slide notes or foot. If the class will recur, register
  it as an instrument candidate (e.g. a router) instead of spending another cycle.
- A blocking class (obvious overlap that hides content, wrong text, skew) that is still present at
  the cap is surfaced to the user in the delivery with the tried list, not retried silently.
