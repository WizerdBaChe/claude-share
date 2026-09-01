---
name: audience-fit
description: 'Post-production audience-adaptation pass (受眾調校) for anything a NON-BUILDER will read. Two jobs: (A) turn an engineering-voiced deliverable (audit/summary HTML, report, README, release notes) into a reader-facing version in a NEW file; (B) write or fix UI copy (設定頁、狀態列、錯誤訊息) from the USER''s stance instead of the engine''s. Trigger on 「使用者導向」「消費者導向」「寫給一般人/非工程師看」「白話版」「UI 文案」「設定頁文字」「這段太工程」「AI味」 "make this readable for stakeholders", "rewrite for end users" — and OFFER once, unprompted, right after any skill (diagram-authoring, code-review-deep-checklist, bench reports, …) produces a deliverable whose primary consumer is not its builder. NOT for machine-read docs (phase logs, decisions files, specs — the language policy already governs those), NOT visual layout/theming (→ artifact-design / dataviz), NOT authoring technical docs from code (→ engineering:documentation).'
---

# audience-fit — adapt finished output to the human who will actually read it

The environment's output taxonomy stops at machine / LLM / human. This skill
supplies the missing split inside "human": different readers need different
granularity AND a different stance, and a document that is correct for its
builder can be unusable for its consumer. Two observed failure shapes:

1. **Engineering-voiced deliverables shown to non-builders** — e.g. a
   diagram-authoring audit page whose main text is 「聚合表 (code 元件 → 圖上
   方塊)」「漂移表 (claim vs 量測)」, or a research summary that walks the
   reader through the author's debugging history before the answer.
2. **UI copy written from the builder's stance** — e.g. 「引擎已就緒」 and
   「還不能用」 true simultaneously on one screen (media-fetch-pipeline ASR
   settings, corrected by user ruling 2026-08-28: 文案要從開發者視角換成
   使用者視角).

This is a POST-production pass: it runs after another skill has produced its
artifact, and never weakens that artifact — the engineering version stays
canonical and untouched.

## Step 0 — decide whether to fire at all

Ask: **who acts on this text next?**

- Builder, maintainer, or an LLM/tool → do NOT fire. Phase logs, decisions
  files, specs, machine-read config are already governed by the global
  language policy; "improving" them for a general reader is a regression.
- A human who did not build it (stakeholder, evaluator, end user, 未來的
  自己-as-user) → candidate for **Mode A**.
- The text renders inside a product UI → candidate for **Mode B**.
- Unclear who consumes it → default by provenance and SAY SO: audit / eval /
  bench artifacts → evaluator; usage-facing artifacts (README, release
  notes, GUI copy) → end_user. Declare the choice in the companion's
  provenance block. Ask the one short question ONLY when two candidate
  audiences would change the document's CONTENT, not just its tone — a
  directed or offered run must not block on a question a default can
  answer (round-1 field data: the executor had to decide off-script).

When another skill has just produced a qualifying deliverable, OFFER this
pass in one line — never run it unprompted (it costs a document and the user
may want the engineering version only).

## Step 1 — pick the primary audience (Mode A)

One document, ONE primary audience; serving others gets reading paths and
appendices, never a blended voice. Granularity and description method per
audience:

| Audience | Their question | Granularity | Describe by | Drop from main text |
|---|---|---|---|---|
| end_user | 能做什麼、怎麼用、出問題找誰 | task-level steps | user actions & visible results | code paths, internals, commit history |
| power_user | 怎麼調、錯誤怎麼讀 | config/flow level | settings, flows, log reading | implementation detail |
| evaluator | 該不該採用、風險成本 | claims + evidence + limits | verified vs designed vs known-broken | mechanism detail, war stories |
| maintainer | 怎麼改 | full engineering | the original artifact | nothing — they get the canonical version, not a rewrite |

If the named audience is "maintainer", stop: Mode A has no work to do.

## Step 2 — route by mode

### Mode A — reader-facing companion document
Pick the FORM first (round-1 G-6, user correction — the old default was
the wrong output):

- **A1 same-spec re-render (同規格受眾版) — the DEFAULT.** Keep the
  original's genre, carrier, and spec: a diagram page stays a diagram
  page, a dashboard a dashboard. Same SPEC never means same CONTENT: a
  diagram original is REDRAWN presentationally — load
  `references/presentational-view.md` BEFORE choosing the form. The
  deliverable-doc-refs audience-edition pattern (add a guide layer, keep
  every slide and value) is the DECK/slide-edition rule and never
  substitutes for the redraw on a diagram original (round-2 rejection,
  2026-08-31: same-diagram + guide blocks was rejected as the wrong
  output). What changes is selection and rendering
  — content re-scoped to the audience and drawn presentationally as a
  real node-and-edge diagram (保留真實情況做展示性的描繪). What good
  public examples teach is the translation of concrete program behaviour
  into few readable nodes — never their layout (a copied card-grid reads
  as a classification table, G-7), and never prose ABOUT the original.
  Method + integrity rules (element→canonical mapping, truth
  markers survive aggregation, invent nothing):
  `references/presentational-view.md`. For diagram-carrier originals the
  precision drawing machinery is diagram-authoring territory; audience-fit
  supplies the audience profile and, until a presentational view type
  lands there, hand-renders a node-and-edge SVG page per that file's
  R1–R11 and says so — the card-grid form is a named user rejection
  (G-7), never a fallback (round-2 field proof: an owner-view render that
  passed user gate 2026-08-31).
- **A2 prose digest (整理性報告) — only when a summary/report is what was
  asked for,** or when the original is itself prose. Answer-first
  structure per the honest-data guide.

Naming: A1 `<basename>-<audience>-view.<ext>`; A2 `<basename>-digest.<ext>`.
Both are NEW files next to the original (file-hygiene rule), opening with
a provenance block: canonical link, declared audience, as-of anchor (date
+ commit or regeneration source), and one line saying the companion must
be revised when the canonical regenerates — without the anchor it lies
silently after the next rebuild. Load, per artifact type:

- Project/feature/usage docs (README, 功能說明, install, release notes) →
  `references/project-info-for-general-readers.md` — reader profiles,
  information layers (user_facing 正文 / architecture 附錄 / engineering
  技術附錄), per-section sentence templates, release checklist.
- Anything carrying numbers, comparisons, audit findings, or evaluation
  results → `references/honest-data-readability.md` — answer-first ordering,
  發現→證據→意義→界線→追溯 finding units, claim-strength matrix, number
  presentation (every number gets baseline + direction + scope; 1.336× is
  written as 比基準高 33.6%), corrections disclosure.
- Both apply to a typical audit/summary page; read both indexes, load the
  sections the artifact actually needs.

Core moves (A2 in full; A1 applies them to its text surfaces), in order:
before drafting, sample 1–2 accepted human-read
documents from the same environment and match their register (de-ai-flavor
B-4 — half of measured AI-ness is register mismatch; the symptom-triggered
load below cannot fire before a draft exists, so this one move is inlined
here); answer first (結論 before 證據 before 方法); reroute
engineering-only content to an appendix instead of deleting it; first-mention
terms as 白話名稱（術語）; keep limitations in the main text; translate every
number; never let the reader walk the author's debugging path to reach the
conclusion.

Delivery is a PAIR, never the companion alone: hand over the canonical
original in the same delivery, plus a 前後對照 of 3–6 verbatim excerpt
pairs (original → companion, one line naming the rule that fired, and a
fact-check note wherever a number moved). A rewrite delivered alone is an
unverifiable improvement claim — the acceptance judge needs the baseline
in the same field of view (round-1 acceptance data: the user could not
judge the rewrite without it). The claim the pair supports is "the
original serves a different audience", never "the original is badly
written". When no textual original exists (a born-reader-facing report),
say so and pair against the nearest REAL baseline — never fabricate a
strawman original. For an A1 diagram re-render the 對照 is the R5
aggregation mapping table plus the two renders side by side — verbatim
excerpt pairs apply to text surfaces (A2, and A1's prose blocks).

### Mode B — UI copy stance flip
Load `references/ui-copy-stance.md` (component/capability/inventory
vocabulary separation, distinct-states-look-distinct, the status-card trio,
mechanism-one-click-away). Deliver as a proposal table
(位置 | 現行 | 建議 | 對應程式狀態 | 理由) and confirm before applying —
UI wording is UX semantics, and 「讀不讀得懂」 items go to a UAT checklist
because only a human can judge them — into `B. 體驗` rung B1, not into
`A. 必驗` (`ops/references/uat.md`). The exception is wording that hides a
distinct state (R2): that is an observability failure and ranks in A.

### Mode C — review only
Diagnose without editing: audience verdict (who this text currently serves
vs who it should), defect list with quoted evidence, and stop. Use when the
user asks 「這份給一般人看行不行」 or wants the finding before paying for a
rewrite.

## Hard guardrails (all modes)

- **Truth before simplicity.** A rewrite may not change numbers, causal
  strength, scope, or uncertainty; 「觀察到」 never becomes 「證明」. Claim
  strength stays on the 可描述/可比較/可推因果/不可判定 ladder it was on.
- **Readability is layering, not deletion.** Unfavorable findings and
  limitations move UP into the main text, not out of it.
- **Add zero facts.** A translation pass invents nothing — no specifics,
  no promises the code doesn't check (UI strings included).
- **The canonical artifact survives.** Mode A output is a separate file;
  if asked to overwrite the engineering version, surface the file-hygiene
  rule and ask.
- **Restraint.** 3–5 targeted interventions per pass, deletion over
  addition; when output smells AI-written or the user says 「AI味」, load
  `references/de-ai-flavor.md` and run its checks one at a time.

## References

- `references/project-info-for-general-readers.md` — user-supplied guide
  (zh-TW): project-level info for general readers. Load in Mode A.
- `references/honest-data-readability.md` — user-supplied guide (zh-TW):
  honest data + readability for reports/audits. Load in Mode A when numbers
  or claims are present.
- `references/ui-copy-stance.md` — UI copy rules from the MFP correction.
  Load in Mode B.
- `references/de-ai-flavor.md` — sepia-derived (MIT, attributed) slop
  checks + borrow ledger. Load on AI-flavor symptoms, any mode.
