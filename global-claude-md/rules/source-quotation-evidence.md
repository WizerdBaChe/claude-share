---
paths:
  - "**/claims.json"
  - "**/*claim*registry*.json"
  - "**/verify_brief*.json"
  - "**/quote_match.py"
  - "**/tools/quote-evidence/**"
  - "**/source/images/**"
review-when: the API output filter changes what it blocks (a verbatim page passes, or a <=15-char quote starts being blocked); the Windows OCR engine or its zh-Hant-TW capability is removed or replaced (re-calibrate PASS_AT/UNDET_AT in tools/quote-evidence/qe.py); a source arrives under a licence that permits full reproduction (open-licence text is out of this rule's class)
---

# Source quotation evidence: a copyrighted page is pointed at, never transcribed

Written 2026-09-28 from the 當代中文 verb-section deck
(a private work folder on a non-system drive, not shared). The sources were four
photographed teacher's-manual pages. Two attempts to transcribe them verbatim —
the main loop, then a blind-transcription subagent — both died on
`API Error: 400 Output blocked by content filtering policy`. The user asked
whether it was the network or sensitive data; it was neither. The filter blocks
model OUTPUT that reproduces a copyrighted text at length. User ruling the same
day: the response below is the default practice, not a one-off workaround.
Sibling: `rules/literature-access.md` covers HOW a source is obtained; this file
covers how its content may travel afterwards.

## The property

**No artifact, dispatch prompt or model output carries a verbatim transcript of
a copyrighted source page. A claim drawn from such a page carries a locator plus
at most one short quote (≤ 15 CJK-equivalent units). The quote's presence is
proven by a LOCAL instrument, and an independent verifier returns verdicts, not
text.**

Class: book pages, scanned handouts, textbook or teacher's-manual photos,
paywalled PDFs, screenshots of any of these. Not in class: the user's own
writing, open-licence text, a text the user owns the rights to (say which when
relying on it).

## The route (default, in order)

1. **Evidence form.** Each claim = `{loc: "<source>·¶k", q: "<≤15 CJK-eq>"}`
   plus its kind (quote / paraphrase / judgment / data-insufficient /
   structure). Paraphrases and judgments carry anchors too; a judgment is
   visibly marked as ours.
2. **Instrument.** `python tools/quote-evidence/qe.py ocr <images> --out
   <build>/ocr` (Windows OCR, local, writes files only), then `qe.py check
   <registry> --text-dir <build>/ocr`. The OCR text is never printed, pasted or
   committed as a deliverable; it is build output (gitignore it).
3. **Verifier.** A subagent that did not write the claims opens the images and
   writes a verdict file: per quote `match | mismatch`, per table `match |
   mismatch`, per paraphrase any finding where the paraphrase says more than
   the page. Its brief says: do not transcribe; cite at most 15 chars when
   pointing at a problem. `qe.py check --verify <file>` consumes it.
4. **Deliverable gate** reads the EMITTED artifact and fails any text that
   maps to no registered claim (the anti-over-extension half; the verb-section
   gate G5 is the reference).

**Reading a page to understand it is fine and needed** — the model reads
images; what is blocked, and what this rule forbids, is WRITING the page back
out at length.

## On `Output blocked by content filtering policy`

It is a routing signal, never a transport fault. Do not retry the same request,
do not split the transcript into smaller chunks that add back up to the page
(the same act spread over calls, like the surface-escalation ladder in
`literature-access.md`), and do not ask a different model. Switch to the route
above, tell the user in one line what the filter blocked and why, and continue.

## Mechanisms

- `hooks/verbatim_dispatch_notice.py` — PreToolUse notice on Agent/Workflow
  when a dispatch prompt asks for a verbatim transcription of pages/images
  (the measured incident prompt is its positive control). Notice, never deny:
  the hook cannot tell a copyrighted page from the user's own notes.
- `tools/quote-evidence/` — the instrument, `controls.py` 18 two-sided cases
  including an end-to-end OCR pair and a pinned blind spot (a one-character
  negation flip still scores as present — presence is not support).
- Not mechanised, named: the MAIN loop's own output. No hook sees assistant
  text before it is sent; this file is the only control there, and the
  incident shows the main loop tried first.

## Extending

A new source kind (PDF page, slide image, audio) joins by adding a backend that
writes `<stem>.txt` for `qe.py check`; a new blocked-output message joins the
"On …" section with the date it was observed.
