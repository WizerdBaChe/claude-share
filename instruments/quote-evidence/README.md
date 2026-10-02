# quote-evidence

Pointer evidence for copyrighted source pages: a claim carries a locator and
one quote of at most 15 CJK-equivalent units. The tool proves the quote is on
the named page by fuzzy-matching it against a LOCAL OCR of the page. It never
prints the OCR text.

Rule it serves: `rules/source-quotation-evidence.md`. Born 2026-09-28 from the
當代中文 verb-section deck,
where verbatim transcription of four manual pages was blocked by the API
output filter (`Output blocked by content filtering policy`).

## Use

```git bash
python tools/quote-evidence/qe.py ocr source/images/*.jpg --out build/ocr
python tools/quote-evidence/qe.py check build/claims.json --text-dir build/ocr --verify build/verify.json
python tools/quote-evidence/controls.py
```

Registry: `{"sources": {"圖1": "<ocr-stem>"}, "claims": [{"id": "...",
"anchors": [{"loc": "圖1·¶3", "q": "..."}]}]}`. Verify file (from a
verdict-only verifier): `{"quotes": {"<id>|<quote>": "match"|"mismatch"}}`.

Verdicts, thresholds and the ruler: module docstring of `qe.py` (thresholds
live only there, `PASS_AT` / `UNDET_AT` / `MIN_Q` / `MAX_Q`).

## What it cannot see

Presence is not support. A quote can be on the page and still not back the
claim, and a one-character negation flip still scores as present (control C5
pins this). Paraphrase drift and table cells go to the verifier; the
deliverable's own gate checks that every emitted text maps to a registered
claim.

## Extending

A new source kind (PDF page, slide image) adds a backend that writes
`<dir>/<name>.txt` and leaves `check` unchanged; a new verdict row adds a
true + false control pair to `controls.py` in the same commit.

## Consulted before building (prior-art check)

`tools/recall/recall.py query "verbatim transcription content filter copyright
OCR quote"` (no instrument found); `references/claude-config-decisions.md`
D-030 (anchor existence, not position); `rules/literature-access.md`
(obtaining sources; its "one quote per claim" limit);
`skills/literature-search-extract/references/output-templates.md` §7 Quote
pack; `rules/verification-ladder.md` (presence vs support). The matcher is the
verb-section project's `tools/quote_match.py`, generalised.
