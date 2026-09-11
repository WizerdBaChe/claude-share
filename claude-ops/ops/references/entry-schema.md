---
xi: 1
what: 分類／路由條目的統一 meta-schema 與 14 面適配表 (one meta-schema for every classification/routing entry, with the 14-surface adapter table)
tags: [ops, schema, routing, classification, adapter, protocol]
aliases: [entry schema, 條目 schema, 統一路由欄位, adapter table, 適配表, ES-]
date: 2026-09-08
status: live
---

# Entry schema — one meta-schema for classification and routing entries

Detail file for `ops/40-maintenance.md` §2a (pointer there) and the record type
"routing/definition entry" in `ops/rules-usage-dict.md` §七. Loaded on demand, never at
session start. Sibling: `principle-design-guide.md` (which asset properties each artifact
class must carry). Enforced subset: `tools/entry-schema-lint/` (integrity-sweep check 29;
`config-self-audit` §4 `--path` mode). Standing reason: `ops/rule-registry.md` key
`ENTRY_SCHEMA`.

## §1 What this fixes, and what it leaves alone

Fourteen surfaces in this environment classify or route — each with its own field
vocabulary (the survey is in the design record; the list is §4 below). The protocol does
NOT replace any surface's grammar and changes NO parser. It fixes three things:

1. the canonical NAME and value set of each field, so an author knows what to fill and a
   reader knows where to look, whatever the surface;
2. for every surface, how each field is SPELLED there — or that it is not representable,
   and then which CARRIER holds it instead (the honest column);
3. which absences a lint enumerates (P2 of `40-maintenance.md` §2a: an omission fires no
   event, so the absence must be greppable).

Design invariants (`INV-n`, cite as `entry-schema.md INV-n`):

- **INV-1 adapters, never rewrites** — no existing parser's accepted grammar changes; where
  a field already has a spelling on some surface, the schema adopts that spelling.
- **INV-2 explicit none** — an applicable field with no value is the literal `none`, never
  an omission (the omission is what cannot be enumerated).
- **INV-3 property, not advice** — every guide entry (AP-nn) has an asset class as its
  grammatical subject and a `detect:` line.
- **INV-4 two-sided calibration** — every lint check ships with a known-bad AND a known-good
  control before its verdict is trusted; a one-sided check is not shipped.
- **INV-5 born-after strictness** — an artifact first committed after 2026-09-08 FAILS on a
  missing core field; legacy artifacts WARN, with a count that must not rise.
- **INV-6 no new always-on cost** — nothing here loads at session start: no CLAUDE.md prose,
  no new hook; a CLAUDE.md pointer, if the user accepts one, is byte-neutral (sink first).
- **INV-7 labels registered at birth** — `AP-nn`, `ES-n`, `PH-n` land in `LABEL-REGISTRY.md`
  §2 in the same commit as their first use.

## §2 Entry kinds

| kind | what the entry does | `trigger`/`on-fire` | examples |
|---|---|---|---|
| **routing** | selects behaviour when something happens | required | skill (description + dict section + trigger-class block); hook (+ settings.json matcher); `rules/*.md` (`paths:`); OPS.md row; inbound-routing row; §2a row |
| **definition** | fixes the meaning or value of a name | n/a — omit | LABEL-REGISTRY family; rule-registry entry; §七 record-type row; page class; layer-map row |
| **record** | one dated fact or event | n/a — omit | intake lesson `L-nnn`; xi card (file identity); decision `D-nnn` |

## §3 Fields

**Core — every entry of every kind.**

| field | value set | lineage (spelling kept from) | absence enumerated by |
|---|---|---|---|
| `id` | stable key, unique inside its owner; an id cited WITHOUT its owner's filename must be a `LABEL-REGISTRY.md` §2 family | LABEL-REGISTRY `家族`; rule-registry `key`; intake `id:`; skill dir name; hook basename | ES-4 (ghost names); LABEL-REGISTRY §5 grep |
| `owner` | the ONE file (+§) that defines the entry; for a file-entry the file itself (derivable) | LABEL-REGISTRY / §七 `owner` | ES-5 (owner path resolves) |
| `status` | `draft` · `shadow` · `live` · `spent` · `retired` · `superseded:<id>` | xi `status:` (live / spent / draft / superseded); hook `STATUS:` (LIVE / SHADOW / RETIRED); intake `status:` projection | ES-1 (hooks); `xi.py` / `intake.py` (their stores) |
| `kind` | `routing` · `definition` · `record` | this file | derivable from the surface (§4) |
| `detect` | how a violation or the death of THIS entry is enumerated: `P1 <hook>` · `P2 <marker> via <sweep check>` · `P3 <end gate>` · `audit <tool or skill §>` · `none (candidate: …)` | `40-maintenance.md` §2a P1–P3; intake `## Detection`; sweep check ids | ES-2 (hooks declare a RUNNABLE proof-of-life, executed by sweep check 31); ES-6 (guide entries carry it) |

**Core for `kind: routing` only.**

| field | value set | lineage | absence enumerated by |
|---|---|---|---|
| `trigger` | `utterance` · `artifact-context` · `omission` · `sub-service` · `tool-call` · `path-read` · `schedule` · `sweep` | `skill-trigger-classes.md` `source:` (first four verbatim); the rest name the other carriers (settings.json event, `paths:` glob, scheduled task, sweep item) | ES-4 (skills); settings.json (hooks); `paths:` (rules) |
| `on-fire` | `execute` · `ask-first` · `deny` · `warn` · `annotate` · `log-only` | `skill-trigger-classes.md` `on-fire:` (first two); hook verdicts | ES-4 (skills); audit reads hook code |

**Conditional — required when the condition holds, else omitted (or `none` when the field
applies but is empty).**

| field | required when | lineage |
|---|---|---|
| `layer` | the LEVEL is not fixed by the path — project artifacts, round folders, an HTML root; inside `~/.claude` rule directories it is derivable and may be omitted | `rules/naming-and-placement.md` §1 `layer:` |
| `audience` | the fire produces text a reader consumes (deny text, sweep line, page) and that reader is not the directory default; HTML roots always (`data-audience`) | naming-and-placement §1 `audience:` / `data-audience` |
| `why` | `kind: definition` on a rule-tier value (a pointer to the rule-registry key suffices) | rule-registry `why:` |
| `evidence` | any entry born after 2026-09-08: `session <id> \| digest <path> \| locator <…> \| captured <date>`, or the literal `unrecorded` | `70-evolution.md` §2 evidence block; intake `locator:` |
| `review-when` | the entry rests on a fact outside this repo (harness default, vendor doc, an unmeasured rate); else the literal `none` | rule-registry `review-when:`; `rules/*.md` `## review-when` |
| `rollback` | the entry is a mechanism (hook, scheduled task, guard, lint) | rule-registry `rollback:`; `70-evolution.md` §2 |
| `since` | the entry can be legacy-vs-new (hooks, families) | xi `date:`; hook `since <date>` |
| `aliases` | a human may search under another name | xi `aliases:` |
| `fires` (skills) | `always-on` · `conditional` · `phase-gated` · `user-manual` · `sub-service` · `second-order` | `skill-trigger-classes.md` `class:` |
| `zero-means` (skills) | free text printed beside an unexplained zero | `skill-trigger-classes.md` `zero-means:` |

The birth-schema minimum of `40-maintenance.md` §3 (an id-or-date anchor, a status, a why,
an evidence-or-link) is covered by `id`/`since`, `status`, `why`, `evidence`/`owner`; the
two fields this schema ADDS for routing surfaces are `trigger` and `detect`.

## §4 Adapter table — the 14 surfaces

Read: **entry unit** = what one entry is on that surface; a field cell gives the surface's
own spelling, `—` means not representable there; **carrier** = where the missing field lives
instead; **parser** = the reader that must keep working (none of them changes).

| # | surface | entry unit | `id` | `owner` | `status` | `trigger` / `on-fire` | `detect` | not representable → carrier | parser (unchanged) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `skill-trigger-dict.md` | per-skill `###` section | heading (skill name) | `skills/<name>/SKILL.md` (implicit) | — (tombstone note `幻影條目` is the only lifecycle mark) | utterance — `關鍵詞` / `精準句型`; `避免說法` = negative vocabulary / — | `tools/skill-routing-audit.py` (fires vs vocabulary) | status, on-fire, detect → surface 2 block | `skill-routing-audit.py load_entries()` reads `關鍵詞`, `避免說法` only |
| 2 | `ops/references/skill-trigger-classes.md` | `## <skill>` block | heading | implicit (skill dir) | — (a retired skill is archived; status = live by existence) | `source:` (utterance / artifact-context / omission / sub-service) + `class:` = `fires` / `on-fire:` | `zero-means:` explains expected silence; `proc:` staleness → audit prints STALE | per-entry review-when (header comment only) → `rule-registry.md` key `skill trigger class registry` | `load_classes()` — matches only the five keys, so an added key is ignored, never fatal |
| 3 | `ops/rules-usage-dict.md` §一 / §七 | table row | — (row text) | `檔案` / `owner` column | 🔴🟡🟢 = write authority, not lifecycle | 判別法 sentence (§一) / `何時必用` (§七) / — | ES-5 (owner path resolves) | id, status, review-when, evidence → the owner file's own entry | none (human-read) |
| 4 | `ops/OPS.md` routing table | row | — | `Read` column (target file) | — | Situation text (task-shaped judgement) / — | `ops_health_nudge.py` ghost-rule check (target exists) | id, status, on-fire, review-when → the target file | none |
| 5 | `LABEL-REGISTRY.md` §2 | row | `家族` (the label prefix) | `owner` column | collision sub-table = the only state | n/a (definition) | §5 grep; ES-5 (owner path resolves) | per-family status, review-when → owner file | none (manual §5 grep) |
| 6 | `ops/rule-registry.md` | `### <key>` entry | key | the file (🟡) | `PROVISIONAL` in `evidence:` (value settledness); SUPERSEDED / RETIRED in the heading | n/a (definition) | sweep checks 11 / 12; ES-5 (current / why / evidence present) | lifecycle enum → heading suffix by convention | none (grep-based sweeps) |
| 7 | `ops/40-maintenance.md` §2a | row | `P1` / `P2` / `P3` (bare-cited → LABEL-REGISTRY §2 collision note) | file §2a | — | the "trigger is…" column IS the trigger taxonomy / — | none (this row DEFINES the `detect` shapes) | status, review-when → the conditions paragraph (prose) | none |
| 8 | xi cards (`tools/cross-index/`) | file frontmatter | `xi:` int (per store) + `what` | the file | `status:` live / spent / draft / superseded | n/a (record) | `xi.py freshness` / `coverage`; `hooks/xi_card_guard.py` (shadow) | trigger, on-fire, detect → n/a by kind | `xi_cards.py extract_card()` `AUTHORED_KEYS` |
| 9 | intake lessons (`ops/lessons/L-nnn.md`) | one record file | `id:` `L-nnn` | `## Fix` names the rule's home | `status:` projection of `## Events` | pre-task grep on `tags` (utterance-shaped) / — | `## Detection` (the entry's own detect field) + `intake.py check` INV-1..6 | review-when, on-fire → n/a by kind | `intake_core.py parse_record()` D1–D9 |
| 10 | `tools/page-fill-gate/page_classes.json` + `rules/deliverable-doc-refs.md` | class object | class name | `owner` (top-level) + the rules file | `severity` fields (WARN / FAIL) | artifact-context — `data-page-class` on the page / — | `fill_gate.py` on the BUILT file; `unknown_policy.promotion_trigger` = review-when | per-class status, evidence → the rules file body | `fill_gate.py` |
| 11 | `ops/references/inbound-routing.md` | table row | — | target skill / mode column | prose ("retired 2026-08-12") | "what arrives" (artifact-context by granularity) / — | sweep check 9 (tier-3 count) | id, status, review-when → `rules-usage-dict.md` §三 | none |
| 12 | `rules/*.md` | file | stem (must appear in the CLAUDE.md index line) | the file | — (retirement = archive) | path-read — `paths:` globs / — | ES-3 (frontmatter, index sync, review-when); ES-5 (named mechanism exists) | status, on-fire → the CLAUDE.md index-line gloss; layer / audience derivable (rule-tier, machine) | Claude Code loader (`paths:` only) |
| 13 | `hooks/*.py` | file (module docstring header) | basename | the file + its rule-registry key | `STATUS: LIVE\|SHADOW\|RETIRED since <date>` (4 of the 28 registered in settings.json on 2026-09-08) | tool-call — settings.json event + matcher / verdict kind lives in code | `Proof-of-life: \`python <suite>\`` in the hook's OWN docstring, executed by sweep check 31 (ES-2; being named in the sweep is not being run by it); two-sided suite in `tools/*-test/` | on-fire is not declared; `config-self-audit` §1 reads the code | Claude Code (settings.json); `tools/hook-deny-lint` reads deny text |
| 14 | `skills/*/SKILL.md` | frontmatter (`name`, `description`) + body | `name` | the directory | — (retired = archived) | utterance — description trigger phrases / — | `ops_health_nudge.py` checks 5 / 10; `skill-routing-audit.py` 18 / 18b | ANY extra frontmatter key (loader-fixed) → surface 2 block carries fires / source / on-fire / zero-means | Claude Code loader; `skill-routing-audit.py description()` |

Coverage: 14 / 14 surfaces mapped; 5 have no per-entry `id` (3, 4, 7, 11 by design — row
text is the identity; 12 by stem); 7 have no lifecycle `status` (2, 4, 7, 11, 12, 14 by
existence-or-archive; 3 carries write authority instead); every surface has a `detect`
column entry, 3 of them `none` by kind (7 defines the shapes; 4 and 11 rely on the target).

## §5 Birth procedure (an author adding an entry to ANY surface)

1. Name the **kind** (routing / definition / record) and the **surface** (§4 row).
2. Fill the **core** in that surface's spelling; a field the surface cannot hold goes to the
   **carrier** named in the row (a skill's class/source/on-fire → the trigger-class block; a
   hook's status → its docstring `STATUS:` line; a rule file's identity → the CLAUDE.md
   index line).
3. If the `id` will be cited bare, run `LABEL-REGISTRY.md` §5 and register the family in
   §2 in the same commit.
4. Write `detect:` — or the literal `none (candidate: …)`; for a hook that means a
   proof-of-life line in `integrity-sweep.md` in the same commit (`40-maintenance.md` §2a
   condition 3).
5. If this is a NEW record type, add its §七 row (`40-maintenance.md` §3 birth schema).
6. Run `python -X utf8 tools/entry-schema-lint/lint.py --path <artifact>`; no FAIL.
7. Look up the artifact's class section in `principle-design-guide.md` and check each AP
   listed there.

## §6 What the lint enforces today vs documented-only

Enforced (ES-1..ES-8 — the docstring of `tools/entry-schema-lint/lint.py` is the owner of
the numbering; this file names them, never restates their predicates): hook `STATUS:`
(ES-1), hook proof-of-life (ES-2), rule-file frontmatter / index sync / review-when (ES-3),
trigger-class value sets and ghost blocks (ES-4), owner and mechanism pointers + registry
field presence (ES-5), guide citation integrity (ES-6), page-builder declarations and shared
shell — project trees, heuristic (ES-7), tool-bound ruling sentences — heuristic (ES-8).

Documented-only (no mechanical detection yet; the adapter table says so per row): OPS.md
rows, inbound-routing rows, §2a rows, per-entry `evidence` on surfaces 1–7, and the hook
`on-fire` kind versus its docstring.

## §7 review-when

- A 15th classification/routing surface appears (a new registry, a new dict, a new per-file
  marker vocabulary) → add its row BEFORE it ships; a surface without a row is the defect
  this file exists to name.
- `skill-trigger-classes.md` gains a key → extend the value table here and ES-4 together
  with `tools/skill-routing-audit.py load_classes()`.
- Claude Code's SKILL.md loader accepts more frontmatter keys → surface 14's carrier moves
  back into the frontmatter; re-evaluate whether surface 2 still needs to exist.
- Three consecutive sweeps show born-after hooks still missing `STATUS:` → the P2/P3
  carriers are not reaching authors; add a path-scoped stub (`rules/`) — that is the named
  upgrade, not a default.
