---
paths:
  - "**/00_INDEX.md"
  - "**/INDEX.md"
  - "**/README.md"
  - "**/manifest.json"
  - "**/CLAUDE.md"
  - "**/*施工卡*.md"
  - "**/workpack_*.md"
  - "**/build_pack.py"
  - "**/T[0-9][0-9]_*/*.md"
---

# Naming and placement — level and consumer are classified before an item exists

Raised 2026-09-08 from a global-rule-candidate note in the source environment's
own `references/` tree (dated 2026-09-04, not shipped here)
(user ruling 2026-09-04: "命名和擺放…沒有原則…路由系統對人類認知負擔太大，不如名稱簡單明瞭")
after the SSLD T46 diagnosis showed the same shape three ways (embedded-figure contract that
stopped at the file, a ruling bound to a tool instead of the asset class, a placement ruling
with two readings executed twice). Index line lives in `CLAUDE.md`. Review-when: see §7.

## §1 The two axes (asset property: every item carries a value on both)

| LEVEL | What it decides | Examples |
|---|---|---|
| rule-tier | who may write it (40-maintenance §1 tiers), always in git | CLAUDE.md, ops/, skills/, rules/, hooks/ |
| cross-round instrument / register | frozen typed folder; a round never writes NEW outputs there; consumed by every round | instruments (`*_audit.py/.json`), registries, procedure + round register, literature evidence |
| round output | lives in THAT round's container, nowhere else | records, figures, 3D, pages, gate evidence of one round |
| audience entry | one persistent, undated entry that takes COPIES (or links) of accepted round outputs with round tags; its layout follows the audience's flow, not storage | discussion pack, dossier index, formal deck |
| record | cross-session memory; append-only; never the primary home of a rule | phase-log, session digest, ledger, memory |

| CONSUMER | Language (CLAUDE.md Language section) | Vocabulary | The artifact a gate must read |
|---|---|---|---|
| machine / agent | English | ids, paths, counts allowed | the file itself |
| builder (next session, executor) | English spec body; Chinese only for user-ruled sections | commands, gate numbers allowed | the file + its verify JSON |
| audience (non-builder) | Traditional Chinese, inline English terms | NO file names, paths, PASS counts, run-ids, gate/invariant ids; every figure caption says what it shows and what is not drawn | **the document the audience opens** (host DOM for embedded figures, the PPTX for a deck) |

Both values are DECLARED on the item so their absence is greppable (40-maintenance §2a P2):
markdown front-matter `layer:` and `audience:`; HTML root `data-page-class` (existing) plus
`data-audience`; a round folder is declared by its round manifest (or a pointer to it) at
the folder root. A missing declaration is a defect an integrity sweep can enumerate.

## §2 Placement clauses

- **PL-1 Round-first containers.** One round → one parent folder `T<nn>_<theme>_<YYYYMMDD>`
  (theme = what the round IS; date = its first day). Everything the round produces lives
  inside, sub-foldered by type (`record/ figs/ 3d/ pages/ verify/` or similar). No numeric
  root prefixes for rounds; no round sub-folders inside typed folders (`06_3D/t44` is the
  named anti-pattern).
- **PL-2 Typed layers are frozen for rounds.** Instruments, registers, procedure, evidence
  waves and cross-session records keep their typed folders; a round may READ and may fix a
  bug in an instrument, but never files a new round output there. Freezing is declared in
  the project index and the project CLAUDE.md, not by marker files inside the folder.
- **PL-3 Audience entry ≠ storage.** The persistent entry is rebuilt from a manifest that
  points INTO round folders; every item carries its round tag; internal layout follows the
  presentation flow. A dated pack that keeps receiving later rounds is the named defect.
- **PL-4 Canonical vs copies.** Accepted item once, at the canonical path; comparison,
  calibration, previous and rejected versions in a labelled sub-area (`archive/`,
  `_previous/`, `_calibration/`), never at the canonical item's level, named by what kind
  of copy they are.
- **PL-5 Indexes are regenerated, not accumulated.** README/INDEX/registry tables are derived
  from manifests by a script; a human must be able to find the canonical item WITHOUT the
  index (the index is a machine convenience, not the fix).
- **PL-6 A view page is reachable from the machine's ONE outermost entry — decided first,
  not after the page exists** (user ruling 2026-09-21). Any subsystem or project that
  produces a page a human is meant to LOOK at (overview, dashboard, viewer, 3D page, deck)
  answers "how does it reach the source environment's single view-launcher page (source-only, does not ship here)" as part of its placement, before its
  internal layout: either it lands where xi's `deliverables` globs cover it (then it is
  picked up automatically, grouped by project and round, the next day), or — for a page no
  index reaches (gitignored `out/`, an unregistered root) — it gets an entry PROPOSED in that
  launcher's page registry (a source-only tool, does not ship here). A per-project index page is fine INSIDE its project and
  never a substitute: measured 2026-09-21, the user did not know a finished projects
  dashboard existed, and named "no entry layer, so I forgot" as the cause; SSLD adds a case
  or round every few days, which is the growth this clause exists for. The launcher points
  AT pages and never takes copies (PL-3/PL-4 still decide where the page itself lives).

## §3 Naming clauses

- **NM-1** A folder or file a human comes back for is named by what it IS, never by when /
  by whom / which attempt produced it; event data (date, model, run id) goes in metadata.
  A round folder is the one exception where the date is part of identity (and it comes
  AFTER the round id and theme).
- **NM-2** One code, one namespace, one meaning across the project (`D1`, `Q3`, `T44` may
  not mean a figure, a test structure and a round at once).
- **NM-3** Same file name never twice in one vault; a per-folder same-role file carries the
  folder identity in its name.
- **NM-4** Old names survive as `previous_paths` / aliases; a rename is recorded where the
  new name is defined.

## §4 Ruling discipline

- **RD-1 Rulings bind the asset class, not the tool.** "Any physical cross-section in this
  repo is cut from a solid by the paper-figure engine" fires for every producer; "whenever
  the pipeline emits a figure" fires only for producers that already called the pipeline.
  Enforce on the class: a scan over the asset class for a generator stamp, not a hook on
  the tool.
- **RD-2 Two readings of one ruling is a defect.** Before executing a ruling a second time in
  a different reading (pack = per-round deliverable vs pack = persistent entry), reconcile
  in writing and log which reading holds; executing both is the failure mode this clause
  names.

## §4a Promotion — where a node's learning goes when the node closes

Added 2026-09-13 from the SSLD T00 three-document set (retrospective + playbook +
beginner field manual, all three hand-built after the round closed). §1 classifies an
item the moment it is CREATED; these clauses classify a piece of LEARNING the moment
its round ends, which is the point at which it otherwise stops moving. The gap that
paid for them is statable in this environment's own vocabulary: `workflow-checkpoint`
fires when work continues but archives STATE only; `project-retrospective` distils
METHOD but is gated on "nothing follows" — so a finished NODE of a continuing
pipeline has no owner for its method, and the distillation gets hand-built outside
every mechanism. The axis is not "is the project over" but **"will this node's
process recur"**.

- **PR-1 Every piece of learning is assigned a layer at node close.** The layers are
  §1's LEVEL values read as half-lives: rule-tier (binds an asset CLASS, any project)
  → `~/.claude/rules/`; owning skill (binds the NODE — whichever skill already owns
  that pipeline stage) → that skill's `references/`; project CLAUDE.md (binds this
  project only); round record (binds only that round). **"Stays in the round record"
  is a legal and the DEFAULT answer** — and if every piece lands there, the node
  produces no playbook and no manual, only its checkpoint. Writing a portable
  document because the round was large is the failure mode this clause names.
- **PR-2 A staging document has an expiry event.** A portable rule parked in a
  project-level playbook rather than promoted is a DEBT, and its `review-when` event
  is *the next node of the same kind opening* — that node's kickoff lists the
  outstanding clauses by id. Without the event the playbook becomes the permanent
  home of a cross-project rule, which §1 forbids for a record. (Measured at the
  instance: 2 of 20 rules promoted, 18 still parked.)
- **PR-3 A teaching carrier is a REBUILT artifact, never the origin of a rule.** The
  audience edition is generated from the rule layer (or from one content module
  shared with every other carrier); it may not be the only place a rule exists, and
  two hand-written carriers of one body of material are drift with a delay, not two
  deliverables. The instance: an MD and a deck written separately drifted in 24 hours
  (a column renamed in one), and one wrong worked example reached three carriers
  because each was copied rather than generated.
- **PR-4 A promotion ends by rebuilding the index that answers the next prior-art
  question.** Depositing into `~/.claude` invalidates the derived graph, and
  `gsnap.py query` then REFUSES (INV-3, stale corpus) — so the next session cannot
  find what was just deposited and re-derives it by hand, which is how the same
  correction gets paid for twice. Run the layer's index build in the same action as
  the deposit. Measured: this round's two rule deposits were part of the 9 changed
  files that made the graph refuse.

The promotion ACT already has precedent (`references/claude-config-decisions.md`
D-026 "External dispatch enters the rules layer"); what these clauses add is the
TRIGGER, so it stops depending on someone noticing.

## §5 Gate object for embedded items

- **GO-1** The emitted artifact of an embedded item (inline SVG, iframe, image, slide) is the
  host document. The ruler that judges the item runs on the host (DOM read), with the host
  itself as the known-bad / known-good pair; the item's own file-level gate stays but does
  not certify the host.
- **GO-2** Counting embedded items or console errors in the host is a position/count
  predicate (CLAUDE.md gate rule) and certifies nothing about rendered content.

## §6 Migration discipline (when placement changes)

`--plan` (dry run, printed) → move never delete (`git mv`; history preserved) → old names
kept (§3 NM-4) → every existing verifier rerun from the new locations; a PASS count that drops
is a rollback, not a note → frozen folders gain no file (`git status` check). Reference
implementations: PaperSurvey `library.py migrate --plan/--apply`; SSLD's own
T46-round migration script (internal path, not shared) (snapshot / plan / apply / sweep / verify-links).

## §7 review-when

- When a second project (not SSLD) runs a round under PL-1–PL-3: check whether "round-first"
  fits a non-research repo or needs a per-project-class variant.
- When `ops/references/integrity-sweep.md` gains the declaration check (§1 last paragraph):
  drop the "not enumerated yet" caveat in `rule-registry.md`.
- ~~When a SECOND node closes under §4a~~ **FIRED 2026-09-13 (SSLD T01, a coding /
  analysis node, not a sweep). Three findings, and §4a no longer rests on one instance:**
  1. **PR-1's four layers fit** — the learning split cleanly (7 clauses to rule-tier, 2 to
     project CLAUDE.md, the rest stayed in the round record as the default intends).
  2. **The "owning skill" layer was EMPTY at both nodes.** No skill owns this pipeline
     stage, so the layer has never once been used. It stays in the list (the next node may
     belong to `paper-distill` or `product-design-thinking`), but a third empty node makes
     it a layer that exists only in this document — check again then.
  3. **PR-2's expiry event needs a SECOND SHAPE, and this is the amendment.** PR-2 assumes
     a parked clause expires when *the next node of the same kind opens*. T01 parked three
     items that do not expire that way: they wait for **a second INSTANCE of the defect**
     (a second deliverable that publishes a relation; a second corpus-coding round; a
     second project where an outside opinion is offered in place of a verifier pass) — an
     event that may never arrive, which is the correct outcome for a tool built for one
     caller. So a parked item declares which shape its trigger has, and an
     instance-triggered item carries the trigger **in the artifact itself** (there: the
     gate's own docstring) as well as in the round record, because no future kickoff note
     will be reading this round's JSON. Live instance: SSLD's own T01 round record
     (internal path, not shared) `parked_promotions_T01`.
  PR-3 was not exercised (no teaching carrier was produced). PR-4 was exercised twice and
  held: `gsnap.py build` re-run in the same action as each deposit.
- When `workflow-checkpoint` or `project-retrospective` changes its trigger to cover a
  recurring node: §4a's opening paragraph names a gap that would then be closed — rewrite
  it to cite the skill instead of describing the gap.
- When `model3d-pipeline` ships its host-embed contract (R-HOST-EMBED): §5 GO-1 cites it.
