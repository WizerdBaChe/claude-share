---
name: pptx-review
description: Deck review loop in PowerPoint — (A) resolve 「這頁」「這個表格」「目前這張」「我選的這個框」 to the slide and shape the user has open in the running PowerPoint; (B) apply the comments the user left in PowerPoint's own comment pane (「我在 PowerPoint 留了註解」「套用註解」「照註解改」「處理簡報上的意見」) to the deck's BUILD SOURCE, rebuild, and report applied / skipped / general rulings. Fires on any deictic reference to deck content while a .pptx is in play. NOT for building a deck from scratch (→ paper-story or the project's builder), NOT for checking layout (→ the office-deck gates), NOT for HTML decks.
---

# pptx-review — 在 PowerPoint 裡看、留註解、我來套用

Borrowed 2026-09-29 from open-slide (`/current-slide` + `/apply-comments`), re-cut
for this machine: the reviewer's surface is **PowerPoint itself** — no new UI, no
server. The instrument is `~/.claude/tools/pptx-review/pptx_review.py`
(read-only; its README has the resolution model and its limits).

## A. Where is the user? (`cursor`)

    python -X utf8 ~/.claude/tools/pptx-review/pptx_review.py cursor

Run it **fresh on every turn that uses a deictic reference** — the user moves
between slides while you work, so a value read earlier in the conversation is
stale by default (open-slide's hardest-won rule). Compare the new `deck` /
`slide` / `shapes` with what you used last time and act on the new values.

- `state: no-powerpoint` / `no-presentation` → ask which deck and page; never guess.
- `saved: false` → what is on screen is not on disk. For a read ("what does this
  table say"), use the cursor's `text`; before any edit or comment read, ask the
  user to save.
- The cursor names a shape by `shape_name` + `shape_id`. Builders here name their
  shapes; map the name to the builder's content key the same way section B does.

## B. Apply the user's PowerPoint comments

1. **Persist first.** Read the comments into the deck project's review folder
   before you act on them. That is the record, and the commented .pptx is
   never overwritten.

       python -X utf8 ~/.claude/tools/pptx-review/pptx_review.py comments <deck.pptx> --out <project>/build/review/comments-<YYYYMMDD-HHMM>.json

2. **Find the source.** The project's CLAUDE.md or README names its builder:
   `build_*.py`, a `claims.json`, a paper-story `story.json`, or a lab-template
   edit script. The edit goes THERE, and the deck is rebuilt from it.
   - A deck with no builder (the user's hand-made deck): edit a COPY with
     python-pptx, `<name>_applied_<date>.pptx`, and never the commented file
     (paper-story R6-14 generalised).
3. **Decide each open comment by `target.confidence`.**
   - `high` (an anchor, or a unique quoted text): apply.
   - `medium` / `low` (a pin position): apply only if the comment text fits the
     resolved shape's text. Otherwise, collect it for the question in step 5.
   - `conflict` / `unresolved`: skip, and report it with its `notes`. **Never
     guess the target.**
   - `status: resolved`: the user closed it in PowerPoint. Ignore it.
   - Replies are part of the comment. Read the whole thread; the last word wins.
4. **Classify each applied comment: local or general.**
   - `local`: this deck only ("this number is wrong", "move this figure").
   - `general`: a ruling that would bind the next deck ("標題不要超過一行",
     "表格字不要小於 14").
   - For a general comment, record it with `ledger.py add --origin user` and
     name where it should land: project CLAUDE.md, the shared builder in
     AssetVault, or `rules/office-deck-deliverables.md`. Landing a GLOBAL rule
     still goes through the user. A comment is not a rule-change authorisation.
5. **One question round, not a drip.** Ask all low-confidence and ambiguous
   comments in one `AskUserQuestion`. Give each option the slide number, the
   shape's text snippet and your reading of the comment.
6. **Rebuild and gate.** Run the project's build and its gates (office-deck
   rule: text, fit, headroom and presentation gates as the project runs them).
   A comment that makes a gate fail is reported with the gate's line. It is
   not silently reverted.
7. **Record and report.** Write the record, then report in one block.
   - Record: `build/review/applied-<same stamp>.json`, with `{id, slide,
     target, action: applied|skipped|asked, class: local|general, change}`
     for each comment.
   - Report: `N applied · M skipped · K general rulings`, plus one line per
     change. The next round of comments goes on the NEW build; the old
     commented file stays as the record of this round.

## Limits (say them when they matter)

- PowerPoint's COM `Comments.Add2` writes a slide-level pin with no object
  anchor. The anchor a comment gets when the user selects a shape first in the
  UI is **not yet verified** on this machine. Until then, most comments
  resolve by pin position (`medium`) or by quoted text. Ask the user to quote
  the text in 「」 when it matters.
- Legacy (pre-2021) comments carry no verified pin units. They resolve by
  quote only.
