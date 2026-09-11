---
xi: 1
what: 全域原則落到小型物件時必須滿足的資產屬性與偵測法 (per-principle asset properties + detection for the small artifacts an author builds)
tags: [ops, principles, asset-property, detection, guide, design]
aliases: [原則細節設計指南, principle design guide, 細節設計指南, AP-]
date: 2026-09-08
status: live
---

# Principle design guide — what each global principle requires of a small artifact

Detail file for `ops/40-maintenance.md` §2a (pointer there). Loaded on demand, never at
session start. Sibling: `entry-schema.md` (the fields every classification/routing entry
carries). Enforced subset: `tools/entry-schema-lint/` (integrity-sweep check 29). Standing
reason: `ops/rule-registry.md` key `ENTRY_SCHEMA`.

**Why this file exists.** `PHILOSOPHY.md` §一 states eleven beliefs and global `CLAUDE.md`
states the engineering-judgement rules; neither says what a HOOK, a SKILL, a `rules/*.md`,
a project `CLAUDE.md`, a routing entry, a registry row or a page builder must look like to
honour them. So the principle is remembered at the layer where it was written and forgotten
at the layer where the artifact is built (`ops/lessons/L-059.md`: three failures, one shape;
seven page builders with no shared shell the same day). This file closes that gap per
principle, per artifact class.

**Form (INV-3 of `entry-schema.md`).** Every line is an ASSET PROPERTY with a detection,
never advice:

    AP-nn [class …] <the artifact carries / never carries …> — detect: <P1 hook | P2 marker via
    sweep check | P3 end gate | audit <where> | none (candidate: …)>

`detect: audit …` means a named checklist item reads it; `detect: none (candidate: …)` is an
explicit gap (INV-2) that the sweep can count. Classes: `hook` (`hooks/*.py`), `skill`
(`skills/*/SKILL.md` + its routing surface), `rule-file` (`rules/*.md`), `project-claude-md`,
`routing-entry` (dict section, trigger-class block, OPS/inbound/§2a row), `registry-row`
(LABEL-REGISTRY, rule-registry, `rules-usage-dict.md` §七), `page-builder` (a script that
emits an `<html` shell), `tool` (`tools/*` instruments — sweeps, lints, gates). Sources are
cited as `PHILOSOPHY §一.n` (label `PH-n`) and as `CLAUDE.md` followed by the bullet's bold
trigger phrase in «…», verbatim, so ES-6 can prove every citation still resolves.

---

## PH-1 規則是判斷力的替代品 — source: PHILOSOPHY §一.1

- **AP-01** [project-claude-md] carries an `ops-relaxation:` line with its direction qualifier
  (`L2 (fully relaxed)`), or the project runs at L0 by default — detect: P2 grep
  `^ops-relaxation:`; absence = the gate asks each session (`ops/05-authority.md` §2).
- **AP-02** [hook] the module docstring names the rule it enforces (a `rule-registry.md` key,
  a CLAUDE.md trigger phrase, or an `L-nnn`) so the denial and the prose cannot drift apart
  (`40-maintenance.md` §2a condition 1) — detect: none (candidate ES-9: docstring contains a
  registry key or `L-nnn`).
- **AP-03** [skill] a step the skill marks non-negotiable says whether it is an invariant
  (binds at every level) or scaffolding (advisory at L1/L2) — detect: audit
  (`config-self-audit` §4 trigger quality).

## PH-2 證據優先於宣稱 — source: PHILOSOPHY §一.2

- **AP-04** [hook, tool] ships a proof-of-life the sweep can run: a hook's basename is named in
  `ops/references/integrity-sweep.md`; a lint ships `controls.py` or `--selftest` — detect:
  ES-2 (hooks); audit (tools: the controls file exists and is cited by the sweep).
- **AP-05** [registry-row] a rule-registry entry carries `evidence:`; a guessed value starts
  with `PROVISIONAL` — detect: sweep check 11; ES-5 (field presence).
- **AP-06** [page-builder] the gate reads the BUILT page, never the template: the builder emits
  `data-page-class` so `tools/page-fill-gate/fill_gate.py` can rule on its output — detect:
  ES-7 (source emits the attribute); `fill_gate.py` on the output.
- **AP-07** [skill] every verdict the skill can emit carries its verification method
  (`STATIC-VERIFY: <cmd> + expected` or `MANUAL-VERIFY: <action> + expected`) — detect: audit
  (`config-self-audit` Output format is the reference shape).

## PH-3 事後問責優於事前審批 — source: PHILOSOPHY §一.3

- **AP-08** [hook] every fire leaves a trace — a telemetry row, or a receipted deny; a hook that
  never logs is indistinguishable from a dead one — detect: audit (sweep checks 13 / 21–23 are
  the pattern; a new hook adds its own row there in the same commit).
- **AP-09** [skill] a skill that writes files names the destination and the record type
  (`ops/rules-usage-dict.md` §七 row) — detect: audit (`config-self-audit` §3 write scope).
- **AP-10** [routing-entry] a ruling that changed an entry carries its date (`裁定 YYYY-MM-DD`,
  `since <date>`) — detect: none (candidate: a dict section touched by a diff without a date).

## PH-4 機械強制優於文字期望 — source: PHILOSOPHY §一.4

- **AP-11** [rule-file, skill] a mechanism the text claims enforces it (lint, hook, scheduled
  task) exists on disk and is registered — detect: ES-5 (`tools/` and `hooks/` paths named in
  `rules/*.md` resolve); `config-self-audit` §2 for skills.
- **AP-12** [hook] the module docstring carries `STATUS: LIVE|SHADOW|RETIRED since <date>` —
  detect: ES-1 (FAIL when first committed after 2026-09-08; WARN legacy).
- **AP-13** [project-claude-md] a redline about a PATH ("never touch X") is also a mechanism (a
  hook, a permission `ask` rule, `.gitattributes`) or is marked `prose-only` — detect: audit
  (`60-bootstrap.md` §B environment-facts block, redlines row).
- **AP-14** [skill] "must / never" text whose trigger is a tool call names the hook that
  enforces it, or says `prose-only` — detect: audit (`40-maintenance.md` §2a table, row 1).

## PH-5 索引→按需載入 — source: PHILOSOPHY §一.5

- **AP-15** [skill] the description is routing vocabulary within `DESC_CAP`; procedure
  sentences live in the body — detect: `hooks/ops_health_nudge.py` check 5;
  `tools/skill-routing-audit.py --surface` proc% (sweep check 18b).
- **AP-16** [rule-file] `paths:` globs name the narrowest set that covers the asset class, and
  the file's stem appears in the CLAUDE.md `**Path-scoped rules**` line — detect: ES-3.
- **AP-17** [routing-entry] an `ops/references/*` file never gets an `OPS.md` routing row; it
  loads from its owner § — detect: P2 grep `ops/references/` in `OPS.md` returns nothing.
- **AP-18** [registry-row, routing-entry] a new entry adds no prose to global `CLAUDE.md`; if a
  pointer there is needed, a byte sink is named first — detect: `ops_health_nudge.py`
  `CLAUDE_MD_CAP`; sweep check 15 (saturation).

## PH-6 預防優於修剪 — source: PHILOSOPHY §一.6

- **AP-19** [skill] born within budget: description ≤ 700 chars, body ≤ 150 lines soft — detect:
  `ops_health_nudge.py` check 5; `config-self-audit` §5.
- **AP-20** [registry-row, routing-entry, rule-file] a new bare-citable label clears
  `LABEL-REGISTRY.md` §5 and is registered in §2 in the same commit — detect: §5 grep; sweep
  check 8 (filenames that mint a label).
- **AP-21** [registry-row] a new record type declares its minimum fields and lands in
  `rules-usage-dict.md` §七 in the same commit — detect: ES-5 (owner path resolves); audit.
- **AP-22** [hook, tool] a threshold exists once, in the mechanism; every other site names the
  constant, never restates the value — detect: sweep checks 7 / 7b / 10.

## PH-7 永不刪除，只封存 — source: PHILOSOPHY §一.7

- **AP-23** [tool] a tool that moves or renames offers `--plan` (dry run) and moves with
  `git mv`; it never deletes — detect: audit (grep the tool for `os.remove|unlink|rmtree`
  with no archive destination).
- **AP-24** [registry-row, routing-entry] a retired entry stays on its surface with
  `status: retired` or `superseded:<successor>`; it is never removed — detect: schema status
  set (`entry-schema.md` §3); git diff review.
- **AP-25** [routing-entry] a dead dict section is tombstoned in place (`幻影條目 — 查證：…`),
  not deleted — detect: `tools/skill-routing-audit.py` DEAD list.

## PH-8 三層角色 — source: PHILOSOPHY §一.8

- **AP-26** [hook] a deny surfaces the decision to the user or teaches the escape; the text obeys
  `rules/hook-deny-message.md` — detect: `tools/hook-deny-lint/lint.py` (P1–P4, R1–R3 on the
  block surface; P1–P4, R1, R2n, R3n on the notice surface — `additionalContext` /
  `systemMessage`, ruled on since 2026-09-09).
- **AP-27** [skill] a skill that dispatches says workers draft only (OPS hard rule 6) and never
  names a model above the cap — detect: `hooks/model_cap_guard.py` (P1); audit.
- **AP-28** [tool] a sweep or lint reports; it never writes rule-tier files — detect: audit (grep
  the tool for writes under `ops/`, `skills/`, `rules/`, `hooks/`, `CLAUDE.md`).

## PH-9 可反駁性分層 — source: PHILOSOPHY §一.9

- **AP-29** [registry-row] `review-when:` names an observable EVENT whenever the value rests on
  a fact outside this repo — detect: sweep check 12.
- **AP-30** [rule-file] carries `review-when` (frontmatter key or `## review-when` section), or
  the literal `none` — detect: ES-3 (WARN).
- **AP-31** [tool] a verdict prints its ruler — what the check can and cannot see (a "not
  covered" line) — and, where covers exist, a known-EXCLUDED calibration case — detect: audit
  (`gsnap.py` footer and `entry-schema-lint` docstring are the reference shapes).
- **AP-32** [hook] a `SHADOW` hook names its graduation criterion beside its `STATUS:` line —
  detect: ES-1 (WARN).

## PH-10 Know-why 是資產，schema 是傳遞下限 — source: PHILOSOPHY §一.10

- **AP-33** [registry-row] a rule-registry entry carries the full set key / current / why /
  evidence / history / review-when / rollback — detect: ES-5 (current / why / evidence,
  WARN); sweep check 12 (review-when).
- **AP-34** [skill] a skill that emits a record type refuses to emit one missing the type's
  minimum fields; narrative relaxes, fields never do — detect: the type's own checker
  (`intake.py check`, `runs.py check`); audit for types that have none.
- **AP-35** [project-claude-md] points at the project's decision journal and glossary
  (`references/<project>-decisions.md`, `-context.md`) — detect: P2 grep.
- **AP-36** [routing-entry] carries the entry-schema core (`id` / `owner` / `status` / `trigger`
  / `detect`) in the surface's own spelling, or the adapter table names the carrier that does
  — detect: ES-4 (trigger-class blocks); documented-only elsewhere (`entry-schema.md` §4).

## PH-11 機制要能被擴充而不靜默失效 — source: PHILOSOPHY §一.11

PH-11 is about SURVIVAL, where PH-2 is about BIRTH. AP-43 makes two-sided calibration ship
with a gate; these four make the gate still true a month later, when the corpus has grown
classes its author never saw. The four are the belief's four clauses in order.

- **AP-61** [tool, hook, rule-file, routing-entry] carries its own EXTENSION CLAUSE — one
  sentence, in the artifact's own text, saying what a new member must carry (a new check, a
  new class, a new row). An artifact whose growth rule lives only in its author's head grows
  ad hoc — detect: none (candidate ES-9: an `## Extending` section in a `tools/*/README.md`
  or the same statement in a hook docstring / `rules/*.md`).
- **AP-62** [tool, hook] its OBJECT CLASSES ARE ENUMERATED AND CLOSED over its own corpus: an
  input matching no declared class is reported `undetermined` and excluded from every verdict
  count, never folded into the nearest class. Folding is how a false positive is born, and it
  is silent because the count stays plausible (2026-09-08: `L-nnn.md` folded into broken-link,
  9/9 false; PNG folded into mixed-line-endings, 31/31 false) — detect: sweep check 33 /
  `tools/class-closure/closure.py` for the unclassifiable-input half (every control suite —
  `tools/*/controls.py`, `hooks/tests/*.py`, each hook's declared suite — must name the
  `undetermined` verdict; FAIL for any suite lacking it, no exemption set, promoted
  2026-09-09 the day the 28-name legacy backlog was drained to 0 — 31/31 carry; word-level
  proxy, the line is printed); the one-specimen-PER-declared-class half stays audit (reads
  the case list against the instrument's own class vocabulary). The drain is this property's
  own strongest evidence: writing the 28 missing specimens found five hooks folding an
  unclassifiable input into a real verdict (a non-string url RECORDED AS a navigation that
  happened; a non-string path COUNTED AS a read file) and ten crashing on a payload that
  parses but is not an object while their docstrings claimed fail-open — none of it visible
  from any count, which is the clause.
- **AP-63** [tool, hook] has a RECURRING proof-of-life, not only a birth one: a named event
  (`integrity-sweep.md` check, watchdog task, `ops_health_nudge` check) that EXECUTES its
  control suite. Being NAMED in the sweep is not being RUN by it; a mechanism nothing re-runs
  is indistinguishable from a dead one (`hooks/unattended_run.py`, silently fail-open on a
  missing import until a manual audit found it) — detect: sweep check 31 /
  `tools/hook-proof-of-life/pol.py`, which EXECUTES every registered hook's declared suite and
  **FAILS on a hook that declares nothing** (promoted from WARN 2026-09-08, the day the
  fleet reached 29 executable / 0 uncovered — the trigger the check had recorded in advance);
  `manual` (a sweep check named instead of a command) stays WARN, because named-but-not-run
  is a weaker finding than nothing at all. ES-2 rules on the DECLARATION, check 31 on the RUN.
- **AP-63a** [tool, hook, gate] the same clause one level in: a control suite EXERCISES every
  escalation LEVER the artifact documents — a promotion set, a severity flag, a shadow/live
  switch, a `[marker]` escape. A lever nothing pulls is indistinguishable from a wired one,
  and it is worse than an undocumented one because three files cite it and every reader
  trusts it. Measured 2026-09-08: `SEVERITY_PROMOTED` was named in `lint.py`'s docstring, the
  README and `integrity-sweep.md` check 29, while four findings hardcoded `"WARN"` instead of
  calling `severity_for` — so for three of the five classes the documented promotion could
  not fire, and no control would ever have said so — detect: for each lever named in the
  artifact's own docs, a control that flips it and asserts the verdict CHANGES
  (`tools/entry-schema-lint/controls.py` C-05/C-05b, with C-05c pinning what may never enter
  the set). A lever with no such pair is a claim, not a mechanism.
- **AP-64** [tool, hook] a FAILING verdict prints the REPAIR SITE — `file:line`, or a command
  that fixes or re-measures it — not only the symptom. A verdict a reader cannot act on
  without re-deriving the cause is a maintenance cost charged to every future reader —
  detect: `tools/hook-deny-lint/` R-rules for hooks; audit for sweeps and lints.

---

## CLAUDE.md «When the change renders something a human looks at»

- **AP-37** [page-builder, tool] a renderer's green tests are labelled data-path evidence and the
  delivery names the human gate still pending — detect: audit (BC-1 checklist present,
  `ops/references/uat.md`).

## CLAUDE.md «When authoring or generating an HTML page a human will read on this machine»

- **AP-38** [page-builder] emits `<html data-page-class="…">` and its build step runs
  `tools/page-fill-gate/fill_gate.py` on the BUILT file — detect: ES-7 (source emits the
  attribute); `fill_gate.py` on the output.
- **AP-39** [page-builder] one shell module per repo: a second builder that emits its own `<html`
  without importing the shared shell is the T44 defect (seven builders, no shared shell, three
  SVG-embedding helpers) — detect: ES-7 (heuristic).

## CLAUDE.md «Browser-pane UI verification is hook-enforced»

- **AP-40** [tool] a UI verifier proves content / structure / state by DOM read; pixels travel
  only through `SendUserFile` — detect: `hooks/ui_verify_guard.py` (P1).

## CLAUDE.md «When an output looks wrong and the cause is conceptual (not a typo)»

- **AP-41** [skill] a repair loop inside a skill names its canonical-method comparison step
  BEFORE the second patch — detect: audit.

## CLAUDE.md «When an assertion depends on a volatile external fact»

- **AP-42** [registry-row, rule-file, skill] a value copied from a vendor or harness fact carries
  its verification date and a `review-when` — detect: sweep check 12; ES-3.

## CLAUDE.md «When you design, modify, or read the output of an automated gate»

- **AP-43** [tool, hook] two-sided calibration ships WITH the gate (known-bad caught AND
  known-good passed) before its verdict is trusted — detect: ES-2 (hooks named in the sweep);
  audit (`controls.py` / `--selftest` present and cited).
- **AP-44** [tool] severity is declared by consumer in the docstring — WARN plus a named
  promotion trigger when a human/LLM reads the output, FAIL for a hard downstream reference —
  detect: audit (grep the docstring for `WARN` / `FAIL`).
- **AP-45** [tool] the gate reads the EMITTED artifact and its predicates are position-free (no
  offsets, regions, dense ids) — detect: audit; `L-047` recurrence.
- **AP-46** [tool] a new checker's first n ≥ 3 identical verdicts count as an instrument fault
  until a positive control has failed — detect: `controls.py` includes a known-bad that the
  check catches (audit reads the case list).

## CLAUDE.md «When authoring an invariant, checklist item, gate or ops rule»

- **AP-47** [rule-file, project-claude-md, skill, routing-entry] every ruling sentence's subject
  is an asset class ("any page…", "a hook file…"), never a tool or a moment ("whenever the
  pipeline emits", "when editing foo.ts") — detect: ES-8 (WARN; lines that quote the
  anti-pattern are excluded).
- **AP-48** [rule-file] opens with the property it binds (a "The asset property" / "The
  property, not the reminder" section) — detect: audit (3 of 8 files carry it on 2026-09-08).

## CLAUDE.md «Before creating any output item (file, folder, page, figure, record, rule): classify it on two axes FIRST»

- **AP-49** [page-builder] emits `data-audience` on the HTML root — detect: ES-7 (WARN).
- **AP-50** [project-claude-md] names the LEVEL folders — round-first containers
  `T<nn>_<theme>_<YYYYMMDD>`, frozen typed folders — detect: audit
  (`rules/naming-and-placement.md` PL-1 / PL-2).
- **AP-51** [rule-file, registry-row] declares `layer:` / `audience:` only where the path does
  not fix them; inside `~/.claude` rule directories the value is derivable and may be omitted
  — detect: documented (`entry-schema.md` §3 conditional fields).

## CLAUDE.md «Four deliverable-shape rules»

- **AP-52** [skill] a skill whose deliverable a human must run or see ends in the `A 必驗` /
  `B 體驗` shape (`ops/references/uat.md`) — detect: audit (grep the SKILL.md for `必驗` when it
  names a visual deliverable).

## CLAUDE.md «When fixing a bug in code that already passed user acceptance»

- **AP-53** [tool, hook] loosening a gate ships a regression case reproducing what it used to
  catch; the controls' case count never decreases — detect: audit (git diff of `controls.py`).

## CLAUDE.md «When proposing extensions, refactors, or "next steps"»

- **AP-54** [skill] an extensions / next-steps section is labelled extension, not scope, and
  states the core-met test first — detect: audit.

## CLAUDE.md «Prior-art check»

- **AP-55** [tool, skill] a new tool's or skill's README or design record names the consulted
  list by name (registry gist, `references/PROJECTS.md`, `xi.py query`, `gsnap.py query`) —
  detect: audit (`config-self-audit` §4; product-design-thinking Phase 1).

## CLAUDE.md «When a deliverable can fail at runtime»

- **AP-56** [page-builder] the emitted page announces load failures — a visible notice plus
  `console.error` — detect: audit (DOM read of the built page).
- **AP-57** [hook] declares fail-open or fail-closed in its docstring; a deny hook whose imports
  fail must fail CLOSED (`L-058`: one missing import turned two guards fail-open) — detect:
  two-sided suite (`tools/compact-loss-audit/hook_controls.py` pattern); audit.

## CLAUDE.md «When a deliverable includes an architecture/behavior diagram or view»

- **AP-58** [skill] a completeness claim rides on a state machine or decision table; one view
  per question — detect: audit (`skills/product-design-thinking/references/view-integrity-checks.md`).

## CLAUDE.md «Decision charter»

- **AP-59** [skill] a skill step that decides mid-task names `tools/process-ledger/ledger.py
  add` at that step — detect: P2 grep `ledger.py` in the SKILL.md (WARN candidate for skills
  with a decide step).

## CLAUDE.md «When starting a Tier-2 IMPLEMENTATION task at ops-relaxation L1/L2»

- covered by **AP-01** (the relaxation line is what makes the contract trigger decidable).

## CLAUDE.md «Premises & refutability»

- covered by **AP-31** (a verdict prints its ruler) and **AP-29** / **AP-30** (review-when).

## CLAUDE.md «Depth-tier triage»

- **AP-60** [skill] a heavyweight skill states that it supersedes the two-pass protocol (never
  stacked on top of it) — detect: audit.

---

## Index by artifact class (what to check when you build one)

| class | properties |
|---|---|
| hook | AP-02 AP-04 AP-08 AP-12 AP-22 AP-26 AP-32 AP-43 AP-53 AP-57 AP-61 AP-62 AP-63 AP-63a AP-64 |
| skill | AP-03 AP-07 AP-09 AP-11 AP-14 AP-15 AP-19 AP-27 AP-34 AP-41 AP-42 AP-47 AP-52 AP-54 AP-55 AP-58 AP-59 AP-60 |
| rule-file | AP-11 AP-16 AP-20 AP-30 AP-42 AP-47 AP-48 AP-51 |
| project-claude-md | AP-01 AP-13 AP-35 AP-47 AP-50 |
| routing-entry | AP-10 AP-17 AP-18 AP-20 AP-24 AP-25 AP-36 AP-47 |
| registry-row | AP-05 AP-18 AP-20 AP-21 AP-24 AP-29 AP-33 AP-42 AP-51 |
| page-builder | AP-06 AP-37 AP-38 AP-39 AP-49 AP-56 |
| tool | AP-04 AP-22 AP-23 AP-28 AP-31 AP-37 AP-40 AP-43 AP-44 AP-45 AP-46 AP-53 AP-55 AP-61 AP-62 AP-63 AP-63a AP-64 |

Mechanically detected today (ES-1..ES-8): AP-04 AP-06 AP-11 AP-12 AP-16 AP-30 AP-32 AP-33
AP-36 AP-38 AP-39 AP-47 AP-49 (+ AP-05 AP-15 AP-22 AP-26 AP-27 AP-29 AP-40 through existing
sweeps and hooks). Everything else is `audit` or an explicit `none (candidate: …)` — the
count of those lines is the guide's own debt figure.

## review-when

- `PHILOSOPHY.md` §一 gains, drops or renumbers a belief → ES-6 fails on the heading; add or
  retire the `PH-n` block, never renumber the others.
- Global `CLAUDE.md` rewords a bold trigger phrase → ES-6 fails on the phrase; update the
  citation in the same commit (a phrase is the anchor; a bullet position never is).
- A `detect: none (candidate: …)` line gains a mechanism → move it to the lint or the sweep
  and cite the check id here; a candidate that stays `none` for three sweeps is either
  built or the property is demoted to `audit`.
- A new artifact class appears in the environment (a scheduled task, an MCP config) → add a
  class token and its column in the index before the second instance exists.
