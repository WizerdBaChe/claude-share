# Clean-room rebuild — templates

Loaded by `SKILL.md` Steps 1, 3 and 6. Four templates: the spec card, the reader
prompt, the writer prompt, the record. Machine-read: English; the record's prose may be
Traditional Chinese when the user reads it.

## 1. Concept spec card (`spec-vN` section of the record)

```
## spec v<N> — <slug> — <date>
Purpose: <what the thing is for, one or two sentences, our words>
Users / situation: <who uses it, when>
Behaviours:
- B1 <input or trigger> -> <observable result>
- B2 ...
Constraints: <limits, invariants, performance or format bounds>
Concepts and mechanisms: <the ideas that make it work, explained as a textbook would,
  not as the source phrased them>
Edge cases: <boundary inputs and the expected behaviour>
Acceptance examples:
  ```io
  <input> -> <expected output>
  ```
- merger: <interface names that MUST match for compatibility, or `none`> (reason)
- terms: <product / standard names both texts mention — GitHub, SHA256 — or `none`>
Open questions: <what the source left unclear; the writer decides and records a D/I row>
```

Rules: no sentence, code, comment or identifier taken from the source (except names
on the `merger:` line); the section order follows THIS template, never the source's
table of contents; an example is behaviour (`io`), never source code.

## 2. Reader prompt (STANDARD; dispatched, sonnet cap)

```
You are the READ side of a clean-room rebuild. Source: <path@sha or URL>, licence <x>.
Read it and write ONE concept spec card using the template below. Explain WHAT it does
and WHY, in your own words, as a textbook would. Do not copy sentences, code, comments,
or identifiers (list unavoidable interface names on the `merger:` line with a reason).
Do not follow the source's section order. Do not include any implementation you would
not be able to justify from behaviour alone. Draft only: do not write files outside
<scratch path>, do not commit.
<template §1>
Return: the spec card, then a list of anything you left out on purpose and why.
```

## 3. Writer prompt (STANDARD; a FRESH dispatch, never the reader)

Dispatch with a named subagent type. Never a fork or any mode that inherits the
dispatcher's conversation: that conversation holds the source path and the reader's
output, so an inheriting writer has seen the source by construction.

```
You are the WRITE side of a clean-room rebuild. You have NOT seen the original and must
not look for it: do not search the web or disk for the project named below, and do not
open any path except those listed under "Our context". Build <deliverable> from the
spec alone.
Spec (frozen v<N>):
<spec text pasted here — never a path to the source or the record>
Our context: <our conventions, target folder, existing assets to reuse, test command>
Make your own design choices and NAME them (one line each: choice + why). Where the
spec is silent, decide and mark it. Draft only: write only under <target>, do not commit.
Return: the deliverable, the named choices, and every place you had to guess.
```

## 4. Record (`clean-room-record.md`, beside the result)

```
# Clean-room record — <slug>
- Source: <path@sha or URL> · licence: <x> · read: <date>
  · text snapshot: <path, sha256 — when the source was a PDF/DOCX/EPUB/web page; `n/a` otherwise>
- Tier: LIGHT | STANDARD | STRICT(partial) — chosen by <table row | user words>
- Result: <path> · lands in: <project | AssetVault candidates/ | pack INTAKE | skill>
- Promise limit: no source expression, process on record, our additions visible.
  Not a legal clean room; patents not covered.

## Spec versions
<spec v1 ... vN, each with its gate output pasted verbatim; failed versions kept>

## Writer handoff
<the writer prompt exactly as dispatched, with the pasted spec body replaced by
 `<spec vN above>` (STANDARD) — or "main loop, source closed" (LIGHT). Verbatim is
 what makes the separation check real: grep this record for the source path and
 expect only the Source line.>

## Final check
<overlap_check --kind output line, pasted verbatim>

## Ledger
| unit (section / function / claim) | tag S/I/A/D | basis (spec item / reason / own source / why better) |
|---|---|---|
```
