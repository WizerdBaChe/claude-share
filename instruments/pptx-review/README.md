# pptx-review

Read-only instruments for the deck review loop: which slide and shape the user
is looking at in PowerPoint, and what the user's PowerPoint comments point at.
The workflow that uses them is `skills/pptx-review/SKILL.md`.

Borrowed 2026-09-29 from open-slide (github.com/open-slide/open-slide, MIT).
There the inspector writes `@slide-comment` markers into the JSX source, and a
Vite plugin publishes the selection to `node_modules/.open-slide/current.json`.
Here the reviewer's surface is PowerPoint itself, so the anchors are OOXML
comment parts and COM selection. No UI is built, and no deck is written.

    python -X utf8 pptx_review.py comments <deck.pptx> [--out file.json]
    python -X utf8 pptx_review.py cursor [--out file.json]     # exit 3: PowerPoint not running
    python -X utf8 pptx_review.py selftest

## Comment → shape resolution

| order | method | confidence | how |
|---|---|---|---|
| 1 | `anchor` | high | any `*Mk` moniker in the comment (not `docMk`/`sldMk`), matched by `creationId` → `a16:creationId`, else by `id` → `cNvPr id` |
| 2 | `quote` | high | text in 「」/『』/“”/"" inside the comment found in exactly ONE shape (more than one → note, fall through) |
| 3 | `position` | medium (low if the pin sits in several boxes; smallest wins) | `p188:pos` (EMU) inside a shape box; group children mapped through `chOff/chExt`; placeholders with no slide `xfrm` take the layout's, then the master's box |
| 4 | `position-near` | low | pin ≤ 0.5 in outside the nearest box |
| — | `unresolved` | none | none of the above; reported, never guessed |

An anchor and a quote that disagree give `confidence: conflict`. That is
surfaced, not arbitrated.

## What is verified, and what is not

- Verified (2026-09-29, PowerPoint 16.0 COM): `Comments.Add2` writes
  `ppt/comments/modernComment_*.xml` with a slide moniker and `p188:pos` in EMU
  (110 pt → 1 397 000). No object anchor. Replies are nested in
  `p188:replyLst`. Authors live in `ppt/authors.xml`. A real PowerPoint-saved
  file resolves to the right shape by position.
- **Not verified**: what the PowerPoint UI writes when the user selects a shape
  and then adds a comment. The `ac:spMk` shape anchor in the fixture is modelled
  on the documented moniker pattern, not observed. **Also not verified**: the
  `status="resolved"` attribute name. Both become facts on the first real
  commented deck; check `summary.by_method` and one resolved comment.
- Legacy comments (`p:cm` in `commentAuthors`-era files): text and author only.
  Pin units unverified, so the pin is not used.

## selftest

A generated fixture: 2 slides, 3 textboxes, and an inherited title
placeholder, with 9 comments covering every method, the resolved skip, a
two-shape quote, and an anchor/quote conflict. A fake COM app covers the
cursor in 6 states: no presentation, shape selection, text selection, unsaved,
slideshow, and slide sorter. Negative controls: C3 (pin in empty space must
stay unresolved) and C7 (an ambiguous quote must not pick). The C9 control is
confirmed live: with placeholder inheritance disabled, it FAILs.
