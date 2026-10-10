---
name: clean-room-rebuild
description: >-
  Clean-room rebuild (潔淨重建): turn an external source — repo, package,
  article, docs, dataset, prompt collection — into OUR OWN asset by
  concept, never by copying: reading and writing kept apart, an
  expression-free concept spec, every line tagged as source concept, our
  interpretation, added info or deviation. Trigger on 「乾淨分析」
  「潔淨開發」「clean room 重寫」「依概念重建」「重建成我們自己的資料」「不要抄、用我們的話寫」
  「參考這個 repo 做我們的版本」「借鏡 X 自己做一個」, AND whenever work is about to
  rebuild an external source as our own version (fires without those words).
  NOT for describing what a system is now (→ code-review-deep-checklist Mode B
  / diagram-authoring), copying a licensed asset as-is (→ asset-vault), or
  legal opinions.
---

# Clean-Room Rebuild

Promise, and its limit: the rebuilt asset carries **no source expression**, the
process is **on record**, and **what we added is visible**. It is NOT a legal clean
room — a model may have seen the source in training, and a clean room never covers
patents. No output of this skill says "clean", "safe" or "non-infringing".

Design record + prior art: a dated evaluation record that stays in the source
environment (not shipped in this copy) (user rulings R1–R5, ledger 2026-10-09). Templates: `references/templates.md`.

## Step 0 — Intake, tier, refusals

Name the source (path@sha or URL + date), its licence, and where the result lands.
The gate reads plain text only: a PDF, DOCX, EPUB, web page or book scan is first
saved as a text snapshot (the `pdf` skill / a document-to-text tool / the page's
extracted text) next to the scratch work, and the snapshot's sha256 goes on the
record's Source line. Every gate run gets the snapshot, never the original file.
Pick the tier from this table, announce it in ONE line, and record it:
`python -X utf8 ~/.claude/tools/process-ledger/ledger.py add --subject "clean-room tier <slug>" ...`.
The user's 「輕／標準／嚴格」 overrides; undecidable → STANDARD.

| source \ result goes to | only the user reads it | shared, published, vault, skill, code |
|---|---|---|
| permissive (MIT, Apache, BSD, CC-BY) | LIGHT — or just copy + attribute | copy + attribute via asset-vault; LIGHT/STANDARD only when our own interpretation is the point |
| copyleft (GPL, LGPL, CC-BY-SA) | LIGHT | STANDARD; publishable code → STRICT |
| no licence, proprietary, paywalled, book pages | LIGHT (quote rule binds) | STANDARD; publishable code → STRICT |
| facts / datasets | LIGHT (check ToS, database rights) | STANDARD + a ToS line in the record |

STRICT is a design draft only (`references/strict-tier-design.md`): run STANDARD, add
the user's spec review, and say STRICT's other controls were not available.

Refuse and hand back (one line each, no workaround offered): obtaining the source by
decompiling, DRM or paywall circumvention (how a source is obtained →
`rules/literature-access.md`); infringement, FTO or licence-compatibility opinions;
patent design-around; personal data (→ `tools/pii-membrane`).

## Step 1 — Read side: the concept spec card

- LIGHT: the main loop reads the source and writes the spec card itself.
- STANDARD: dispatch a READER subagent (sonnet cap; workers draft only) with the reader
  prompt in `references/templates.md`. Only the reader gets the source path.

The spec card says WHAT and WHY in our words: purpose, behaviours (inputs → outputs),
constraints, concepts and mechanisms, edge cases, acceptance examples in ```io fences.
It never holds source sentences, code, comments, source identifiers (except functionally
necessary interface names on a `merger:` line), or the source's section order. Product
and standard names both texts may mention (GitHub, SHA256, Python3) go on a `terms:`
line, never on `merger:` — merger means "must match for compatibility".

## Step 2 — Spec gate (before anything is written)

```
python -X utf8 ~/.claude/skills/clean-room-rebuild/scripts/overlap_check.py --source <src> --candidate <spec.md> --kind spec
```

- FAIL → the reader revises; the failed version is KEPT in the record (an intermediate
  version is evidence too). WARN → the main loop reads the flagged lines and decides.
- UNDET (exit 3) is not a pass: the gate could not see the source (no text, a document
  file, a file over 2 MB, or past the 20 MB cap — the skip counts say which). Fix the
  input (text snapshot, split the source, narrow `--source`) and re-run; if it cannot
  be fixed, the record says UNDET and why, and the spec is not called checked.
- The gate cannot see copied STRUCTURE (sequence, selection, arrangement in new words).
  The main loop reads the spec for that before handing it on, and the user does so at
  STRICT. Nothing here vetoes on a hunch; an over-specific item is rewritten one level
  more abstract.
- Freeze the spec: its text (not a path) is the only thing that crosses to Step 3.

## Step 3 — Write side: rebuild from the spec only

- STANDARD: dispatch a fresh WRITER subagent with the writer prompt in
  `references/templates.md`: the frozen spec text + OUR context (target conventions,
  existing assets to reuse). Never the source path, never the reader's transcript.
  Dispatch it as a NEW agent with a named subagent type — never a fork or any mode
  that inherits this conversation, which holds the source path and the reader's output.
- LIGHT: the main loop writes from the spec without reopening the source (prose-only
  discipline; nothing enforces it).
- The writer makes and NAMES its own design choices. A mechanical translation of the
  spec is a miss, not a rebuild.

## Step 4 — Interpretation and supplements (the "ours" part)

Tag every unit of the result (claim, section, function, rule) in the record's ledger:

| tag | meaning | must carry |
|---|---|---|
| S | a source concept, restated | the spec item it came from |
| I | our interpretation, or a judgement the source did not make | the reasoning in one line |
| A | added information | its own source (path, URL, paper), never the source under rebuild |
| D | a deliberate deviation from the source | why ours is better here |

A result that is almost all S is a restatement; say so in the record rather than
dressing it up.

## Step 5 — Final check

```
python -X utf8 ~/.claude/skills/clean-room-rebuild/scripts/overlap_check.py --source <src> --candidate <result> --kind output --merger <spec's merger names> --terms <spec's terms>
```

Merger names are masked on both sides before comparison, so a compatible interface
does not count as copied text. FAIL → rewrite the flagged lines from the spec, then
re-run. UNDET → as in Step 2. A WARN on shared
identifiers is the usual trace of recall from training data: rename every private
name, keep interface and library names (dry run 2026-10-09 caught `_compile_pattern`). For publishable code,
JPlag can be run as an extra lens if Java is present (not verified on this machine).
A low score means "no surface copy", nothing more.

## Step 6 — Record and land

Write ONE `clean-room-record.md` beside the result (template in `references/templates.md`;
a worked STANDARD example is the source environment's 2026-10-09 dry-run record, not shipped in this copy):
provenance, tier, every spec version, gate outputs pasted verbatim, the S/I/A/D ledger,
landing place. The result goes to its natural home: the project, AssetVault
`candidates/`, a knowledge pack's INTAKE (§6a: origin + evidence), or a skill. This
skill opens no store of its own.

## Verdicts and how each is verified

| verdict | verification |
|---|---|
| spec gate PASS / result NO-SURFACE-COPY | STATIC-VERIFY: the `overlap_check.py` line pasted in the record; expected `NO-SURFACE-COPY` or a WARN read and resolved; an UNDET line is never this verdict |
| STANDARD separation held | STATIC-VERIFY: the writer's dispatch prompt in the record contains no source path (grep the record for the source path → only the provenance line) |
| ledger complete | MANUAL-VERIFY: every unit of the result maps to one S/I/A/D row; expected no orphan units |
| gate calibrated | STATIC-VERIFY: `python -X utf8 ~/.claude/skills/clean-room-rebuild/scripts/controls.py` → `N/N controls hold` |

## Invariants vs scaffolding

- Invariants (bind at every relaxation level): no source text in the spec or result
  beyond a short attributed quote; at STANDARD the writer never receives the source
  path; the record states the promise's limit; no "clean/legal/safe" wording.
- Scaffolding (adjustable): thresholds in `overlap_check.py` (re-run `controls.py`
  after any change), template wording, the tier table's defaults.
- Enforcement: `overlap_check.py` is the only mechanical gate (end gate, run by the
  main loop); everything else in this file is prose-only.

## Manual acceptance (each run)

A. 必驗 — 1. Open `clean-room-record.md`: every unit tagged; A rows carry their own
sources. 2. Read the result once without the source: it stands on its own.
B. 體驗 — 3. The I and D rows say something the source did not.

## Machine-local dependencies

`tools/process-ledger/ledger.py` (Step 0), `rules/literature-access.md` and
`tools/pii-membrane` (refusals), and the source-environment records cited above live outside
this folder. A shared copy goes through `skill-share-packaging`, which marks them
optional; the gate and its controls (`scripts/`) are self-contained.

## Extensions (not scope)

The core need (separate read/write, an expression-free spec, a tagged ledger, a
calibrated surface gate) is met by this file. STRICT's isolation controls are drafted
in `references/strict-tier-design.md`; build them only when its named trigger fires.
