# Sync history

Per-refresh detail for each share in this repo. Split out of `README.md` on
2026-08-07 — the README had become ~96% sync history, so a reader (human or agent)
who opened only the top-level file learned *when* things were copied rather than
*what is here*. Orientation lives in `README.md`; this file is the record.

For the source environment's own evolution log — the rule-by-rule narrative behind
these snapshots — see `Global_skill_update.md` at this repo's root (frozen 2026-08-11;
standing rationale moved to `claude-ops/ops/rule-registry.md`).

## 2026-09-02 (second entry) — the repo becomes the source of a cloud environment

Until today this repo described an environment; from today it can also
*install* one. Opened in Claude Code on the web, where every session starts in
an ephemeral container with an empty `~/.claude`, the repo now puts the source
environment back before the first turn — "LikeLocal".

**What landed.** A tracked project-scope `.claude/settings.json` whose
SessionStart hook runs `cloud-bootstrap/bootstrap.py install`: 180 files into
the container's `~/.claude` — the global CLAUDE.md with its four machine
placeholders rendered (Linux / bash / no secondary shell / LF) and the adopter
notes dropped, `rules/`, the 22-file ops layer with a measured cloud
`environment.md` overlaid on the Windows one, `references/PROJECTS.md`, the
trigger dict and all 17 skills, all 16 hooks and both JSON lists, the 8
agents, the three environment-guide documents, `preserve.py` at the path
`compact_bookmark.py` calls, `archdiag/` at the path `diagram-authoring`
routes to, the thinking notes, and a user-scope `settings.json` carrying the
template's permissions/env/`disableWorkflows` but neither `model` nor
`effortLevel` (host-managed). The same settings file mounts every hook
matcher-for-matcher with `hooks/settings.example.json`, through
`.claude/hooks/run-hook.sh` — a shim that execs the repo copy and exits 0 when
it cannot, so a missing hook can never become the blocking python exit 2 that
`branch_commit_guard.py` incident #3 records. Both shell hooks are inert unless
`CLAUDE_CODE_REMOTE=true`, so on the operator's own machine nothing runs twice.

**Verified in the container.** `bootstrap.py verify`: all 16 hooks exit 0 on
an empty payload; `model_cap_guard.py` denies `model: opus` and allows
`sonnet`; `dangerous_command_guard.py` denies `git push --force` and allows
`git status`; 16 mount sites over 15 hooks plus the chained nudge cover all 16.
Installing the skills was observed to register them in the running session
without a restart. The one thing NOT measured — whether a fresh container's
first system prompt sees the CLAUDE.md the same session's SessionStart hook
wrote — is acceptance item A1 in `cloud-bootstrap/README.md`.

**Gate changes.** Check S1 refused any tracked `.claude/` path; it now admits
paths declared in a new `[structure] tracked_exceptions` table (path-exact,
reasoned), and a new D4 fails a declaration whose path is no longer tracked.
Test case 13 proves both directions. Check V and the test's case 10 refuse a
`--source` that carries `cloud-bootstrap.json`: that tree is a copy of this
repo, and comparing the repo with itself would pass every `edited` entry as
byte-identical for the wrong reason. One regression the suite caught before
it shipped: tracking `.claude/settings.json` made check R's suffix match
resolve every rule file's citation of the SOURCE `settings.json` to it, and
case 2 went red — the resolver now ignores the repo's own `.claude/` files. A
root `CLAUDE.md` records the repo's own working rules and the
`ops-relaxation: L2` standing ruling.

Gate: CLEAN over 229 tracked files; 12/12 gate tests run, case 10 (check V)
skipped loudly because the container's `~/.claude` is this repo's own copy.

## 2026-09-02 — the first outside run comes back, and the whole repo is re-aligned behind it

Two refreshes in one day, both forced by evidence rather than by a calendar.

**The external run (commit `4052285`).** The first verifier outside the source
environment ran `architecture-diagramming` at `46be565` on macOS Codex
Chromium: the build was deterministic (sha match), the `mFill` positive control
added exactly 25 `dangling-reference`, and the baseline reported **44
`label-overlap`** on bytes the source environment had passed. The source
reproduced all 44 by forcing `font-family:"Noto Sans TC"` — every pair was a
node's 13px title against its 11px subtitle at 18px baseline distance, a
2.63px bbox gap under Segoe UI (0.63px of margin over PAD=2) that tall-leading
CJK fallbacks cross. The fix went into the layout, not the tolerance:
`emit.mjs` `NODE_TEXT` (subtitle baseline +3px, shared with `route.mjs`'s
offline estimate — whose stale copy of the old number placed two pills into
the subtitle's real rect on the first rebuild), `selfcheck.mjs` gains a
`receipt` (engine, DPR, computed family, bbox/size ratio) so a PASS names the
font that measured, `MAINTENANCE.md` M6 is a five-font substitution sweep.
`ACCEPTANCE.md` #16 now asks the verifier for the receipt; the shipped
`capability-set.html` was rebuilt (`6bf15797…4688`). The owner refused the
verifier's suggestions to exempt title/subtitle pairs or make the tolerance
renderer-configurable: both make the instrument pass by measuring less.

**The alignment (five branches, merged `a47c55e`).** Check V with the source
mounted found 28 findings across 20 files; a per-file drift measurement over
the 47 `edited`/`template` entries (which V cannot see) found the same lag
class the 2026-08-29 entry described. Five parallel workers, one worktree
each, ran procedure B over everything:

- **Refreshed**: 30 files across `claude-ops/ops/` (`lessons.md` +381 lines,
  `rule-registry.md`, `environment.md`, `05-authority.md`, `10-command-loop.md`,
  `60-bootstrap.md`, `rules-usage-dict.md`, `integrity-sweep.md`), the global
  CLAUDE.md template, `interop-layer/portable-core.md`, four hooks
  (`ops_health_nudge.py` gains check 17 with its private mirror path turned into
  an env var, `compact_pointer.py`, `transcript_read_guard.py`,
  `ui_verify_guard.py`), the trigger dict (full source rewrite since 08-27;
  six declared edits re-applied, two new ones for skills that do not ship),
  and twelve skill files (`product-design-thinking/SKILL.md`'s Mode A/B split,
  the review family, `scientific-research-guide`, `motion-design`,
  `workflow-checkpoint`, `design-system-suite`). 17 files verified FRESH and
  left alone. Three previously declared scrub edits in `rule-registry.md` /
  `lessons.md` were found silently reverted in the last-shipped copy — the
  exact blind spot check V's docstring names — and re-applied.
- **Source working-copy state carried, with acks**: ten files (`agents/`
  frontend developer, `05-authority.md`, `rule-registry.md`,
  `rules-usage-dict.md`, global CLAUDE.md, `portable-core.md`,
  `code-review-deep-checklist/SKILL.md`, `motion-design/local/env-bridge.md`,
  `product-design-thinking/references/design-rules.md` and
  `document-ladder.md`) were content-dirty at the source (other sessions'
  in-flight edits). Owner ruling: align to what is on disk; each entry carries
  a dated `source_dirty_ack` with the numstat and "re-collect and drop the ack
  when it lands".
- **Collected (procedure A)**: `audience-fit` (six files — the post-production
  audience-adaptation skill; two references are the owner's own guides carried
  verbatim, `ui-copy-stance.md` and `SKILL.md` scrubbed of deliverable
  pointers), three path-scoped rules (`deliverable-doc-refs.md`,
  `office-deck-deliverables.md`, `visual-gate-scope.md` — reference
  implementations in the owner's private asset library became prose; a
  safety/fitness read found nothing machine-only beyond illustrative Windows
  examples and nothing harmful to follow elsewhere), `ops/references/uat.md`
  (the manual-acceptance checklist axis the CLAUDE.md `[BC]` line points at —
  untracked at the source, acked as such), and
  `literature-search-extract/scripts/zotero_ris_export.py`.
- **Not shipped, newly declared**: `hooks/xi_card_guard.py` + its test (a
  shadow hook over `tools/cross-index` and `telemetry/`, both excluded; also
  added to the settings template's omissions list), `skills/post-brief` (the
  loop over two excluded tools), `skills/model3d-pipeline` (owner ruling: later,
  through the mechanism-packaging route). The `tools/` and
  `media-fetch-pipeline` directory dispositions gained dated per-file re-check
  notes for what arrived beneath them.
- **Counts**: skill-toolkit 16 → 17 skills; `global-claude-md/rules/` 2 → 5.

Gate with the source mounted: CLEAN, 192 collected files compared, 12/12 gate
tests. Source state for the round: `d06708c` (2026-09-02).

## 2026-08-29 — full source sync: the M1 lag class swept, and the diagram set ships its executable half

The round the previous two entries kept predicting. Both of them recorded the
same lag note — an `edited`-status file ages invisibly, because check V's only
question ("does it still differ from the source?") stays true while the copy
rots — and both refreshed only the files the round happened to be about. This
one swept all 43 of them by comparing each source file's last-commit date
against its repo copy's. **Twenty were behind, and check V could see exactly
two.** The oldest had been stale since 2026-08-21.

### What came in

**Refreshed (procedure B, 20 files).** `lessons.md` had missed the source's
2026-08-21 restructure into card + detail; `rule-registry.md`, `20-dispatch.md`,
`ops_health_nudge.py`, `settings.example.json`, `global-claude-md/CLAUDE.md`,
`PHILOSOPHY.md`, `MIGRATION-MAP.md`, `workflow-checkpoint/SKILL.md`,
`browser_pane_scope_guard.py`, the whole `scientific-research-guide` set and the
two `diagram-authoring` files followed. Every declared edit re-applied and
re-diffed; three edit lists changed and say why (below).

**Four shell/git enforcement hooks**, each cited by a rule file this repo
already ships, which is what forced the verdict — check R does not accept
silence. `shell_transport_guard.py` (the Bash tool's three SILENT transport
defects: backslash-run collapse, the ~7.7 KB ceiling, MSYS `/flag` rewriting),
`ps_errorpref_guard.py` and `ps_pipeline_close_guard.py` (two Windows-PowerShell
traps that each fail in the direction the author does not expect), and
`branch_commit_guard.py` (the compensating control for two incidents where the
prose ritual RAN and did not gate — it was a non-gating spectator in a `&&`
chain). All four portability-scanned before collection, which is the 2026-08-14
lesson applied rather than recited. Three of the four ANNOTATE and never deny,
because their own backtests proved the gate cannot determine intent — the
backslash branch flagged 112 commands of which 89 had SUCCEEDED, most of them
the author already compensating.

**`hooks/tests/test_transcript_read_guard.py`** — the regression matrix that
guard's docstring names twice, 22 cases including every alias form and every
accepted bypass. Check S had to be narrowed for it (direct children of `hooks/`
only): mounting a test as a hook would put a test harness on every matched tool
call. The narrowing ships with its negative control, case 12, and `case()` grew
an `expect_absent` parameter — until now a control could only assert that the
gate said SOMETHING, including the very finding it was meant to prove absent.

**`architecture-diagramming/archdiag/`, eleven files** — the diagram capability
set's executable half, and the third folder to follow the `red-team/` pattern of
shipping the running code behind a method already published as prose. The
library's motivating defect is the reason it exists: two copies of a self-check
framework drifted apart within ONE day and both reports still printed PASS.
`selfcheck.mjs` is now the single source of that script, and the shape of that
invariant is visible in view 5 of the page below. `vendor/archify-geometry.mjs`
is third-party (tt-a1i/archify, MIT), verbatim.

**Two `ops/references/` detail files** — `dispatch-templates.md` and
`shared-tree-git.md`. These are the class this round was watching for: the
refresh REPLACED shipped prose with pointers to them (20-dispatch.md's worked
contract example and five template field lists; lessons.md's L-023 detail).
Taking the refresh without the pointees would have been a net content LOSS
disguised as a sync.

### What this repo authored

`.gitattributes`, pinning `architecture-diagramming/archdiag/**` to LF. Not a
formatting preference: the html that library emits carries a sha256 freeze
receipt, and a CRLF checkout would invalidate every one of them with all tests
green and no content change behind it. Shipping the library without the pin
would have shipped an asset whose stated invariant this repo breaks.

`architecture-diagramming/capability-set.build.mjs` + `capability-set.html` —
the capability set drawn with its own toolchain, through the copy of the library
that ships here. Five views (structure / design entry / audit entry /
verification ladder as a STATE MACHINE, because completeness claims cannot ride
on a sequence view / module graph), each with an evidence anchor on every node
and edge. Measured: build-time checks passed first run; 49/49 edges
machine-routed with 0 hand fixes and 0 actual crossings; in-page self-check PASS
with 0 diagnostics over 1,493 label pairs, read from a real browser on a
loopback server; positive control produced exactly 25 `dangling-reference`
diagnostics (the exact reference count) and restoring returned 0; the rebuild
reproduced sha256 `aaeaf9d0…4a4d` byte for byte (60,232 bytes on disk; `build()`'s printed `bytes` is `html.length`, i.e. UTF-16 units, so it reads smaller on a CJK page — the receipt is the sha256 and is unaffected). **The third rung — human
appearance review — is open**, and is the cell the page's own gap report marks
`inherent`. `ACCEPTANCE.md` gained section E: four items that need no skill
installed, only Node, and the README gained the promo section this scan fed.

### Corrections found while sweeping

- `domain-expansion-guide.md` carried its share note **twice**, back to back —
  a duplication from an earlier re-application that no mechanical check could
  see. Re-applied once.
- `hooks/browser_pane_scope_guard.py` went `edited` → `verbatim`: the source
  rewrote the denial text this round and the private pointer the edit existed to
  remove is gone upstream. Keeping the status would have made check V assert a
  difference that no longer exists, which is exactly the finding that catches a
  DROPPED edit — it has to stay meaningful.
- `transcript_read_guard.py`'s third edit narrowed to docstring-only: the source
  rewrote its deny message into a constraint-only form whose new contract
  forbids precisely the read-elsewhere pointer the edit was rewriting. Recorded
  rather than dropped — a vanished anchor is a signal to re-read, and the
  re-read said the source had fixed it upstream.
- `_routing.md` and `user-supplied-citations.md` needed their template edits
  re-established for the second and third time. Both grew: the source had added
  five domain-specific routing sections and a dated-observation discipline
  respectively, so the round kept every generic addition and dropped only the
  rows and rulings that are about files this share does not carry. Restoring a
  template must not silently discard the format work done since.
- `<card>` retired from the placeholder vocabulary by check D — lessons.md's
  Evidence schema line was rewritten upstream and nothing used the token any more.

Six real leaks caught by check L on the way in (four work-root paths in
`lessons.md`, six in `rule-registry.md`, the settings template's interpreter
paths), plus 38 session ids scrubbed by hand — the class no pattern catches.
Four illustrative paths got narrow `[[allow]]` entries instead, each one an
example inside a defect explanation rather than a location.

Gate CLEAN with `--source` (181 collected files compared), tests 12/12, the hook
matrix 22/22, interop 14/14, red-team 10/10 + 8/8.

## 2026-08-28 — F1/F2 field-round hardenings: reference-resolution + artifact-skill techniques

Second refresh the same day: the morning round predates the source's two
audit-drawing field rounds, so three files lagged. What came in:
`notation-precision.md` §4 gained the display:none instrument precondition
(987 false overlaps from hidden tab panes), the count-only-diagnostic
completeness rule, and — found by the second round's framework reuse — a
`url(#id)` reference-resolution assert with a positive-control calibration
rule (the first round's ACCEPTED deliverable had shipped 56 dangling
arrowhead-marker references through both machine rungs and the human gate);
its §3 sequence bullet now states whole-deliverable symbol consistency
outranks the notation's own arrowhead convention. `carrier-playbook.md`
gained single-defs discipline and the lifelines-as-containers sequence
pattern. `skill-co-upgrade/SKILL.md` (verbatim) gained an artifact-skill
techniques section: the consumer-position round (reuse-as-audit) and the
post-acceptance defect protocol. Procedure B throughout — the three
declared pointer→prose edits re-applied exactly, diffs equal to the edit
lists. Ripple: ACCEPTANCE's verified-evidence section gained the
third/fourth-round bullet. M1 lag note, same class the previous entry
recorded: only the verbatim file fired check V — both edited-status files
aged invisibly and were refreshed by sweep, not by a check.
Gate CLEAN with `--source` (163 compared), tests green.

## 2026-08-28 — architecture-diagramming: verification discipline refresh (B-1..B-6)

Refresh round, one day after the set first shipped. The source ran a second
field test (the set drawn against itself) and adopted six verification
disciplines from tt-a1i/archify (MIT) into the skill body: diagnostic objects
with stable codes and suggested fixes, a fixed repair order with bounded
repair and a label-preservation rule, freeze + SHA-256 receipts, a
`visual_review` tri-state with correction-round counts, viewport containment
measurement for the HTML carrier, and instrument preconditions for the
geometry assert set. The three set files came over per procedure B:
`SKILL.md` still verbatim; `notation-precision.md` verbatim → edited (one
edit — the new borrow-ledger pointer, a dated analysis file under the
source's non-shipping outputs/ tree, replaced with prose; the B-ids stay);
`carrier-playbook.md` re-applied its 2026-08-27 edit and gained a second of
the same class. Audit correction, recorded in place: that 2026-08-27 edit
was declared against the Provenance section, but the pointer it removed
lives in the Deliverable-location section — the declaration now names the
right section.

M1 lag measurement: four V findings — the two in-scope files plus both
packaging skills (`mechanism-share-packaging`, `skill-share-packaging`),
whose sources had gained their own 2026-08-27 third-run findings; both
refreshed verbatim after a clean B4 read. One lag the gate cannot see:
`carrier-playbook.md` is status `edited`, so check V's only question
("still differs from source?") stays true while the copy ages — its refresh
happened because the round swept the set, not because a check fired.
Ripples: the README's de-identification note gained a dated bullet (its
"one content edit" count was about to become false), and ACCEPTANCE gained
the second field run's evidence — including the instrument blind spot the
run caught (transformed-group bbox misreads) that became the new
precondition assert. Gate CLEAN with `--source` (163 compared), tests 11/11.

## 2026-08-27 — architecture-diagramming: the diagram capability set ships as one loop

Third mechanism export (after `compact-recovery/`, `red-team/`), and the first
whose parts ship inside `skill-toolkit/` rather than beside the map. What came
in: `skills/diagram-authoring/` (three files, first collection — one declared
edit, a field-test ledger pointer into the source's private review records
replaced with prose; the FT-ids stay), the two theory references
`product-design-thinking/references/representation-models.md` and
`view-integrity-checks.md` (verbatim, with two considered keeps recorded in
their entries: a same-day global-rule promotion note, and a CPO example that is
industry vocabulary rather than withheld profile knowledge), and the authored
pair `architecture-diagramming/README.md` + `ACCEPTANCE.md` — the integration
map and a fourteen-item blind-runnable external checklist whose open evidence
cells (PPTX carrier, BPMN branch, two never-live-fired probes) are stated
rather than implied. `code-review-deep-checklist` was refreshed current, which
is what brings its Mode B view-audit layer (體檢視圖層) — the audit third of
the set — into this repo at all.

The trigger dictionary went through procedure B: the three 2026-08-17 edits
re-applied cleanly, and three new ones joined them — the `graph-query` and
`media-fetch-pipeline` sections removed (machine-bound wrappers, new
`[[not_shipped]]` entries; the row-2-inverse two-part act each time) and the
scientific-research-guide domain block condensed to a share note, since its
expanded source text had begun enumerating the withheld profiles in detail.
Counts moved 15-of-18 to 16-of-21 in the four places that state them.

Running the gate `--source` surfaced 23 verbatim files lagging a source that
had moved for ten days; all refreshed per procedure B. The B4 read of the
incoming content caught what the gate cannot: a session id arriving inside
30-judgment's new incident example; the second-drive work root in two
integrity-sweep probe payloads and in shader-failure-modes' corpus sentence;
`environment.md` citing a measurement ledger that does not ship (new
`[[not_shipped]]` with the re-measure fallback); three new placeholder tokens;
and one deliberately fictional probe path allowed with its match written
name-only, per the email-allow's own comment about not making the manifest a
finding. The same sweep found an EIGHTH session UUID surviving in
`lessons.md` L-013's evidence locator — the seven-UUID edit had scrubbed the
line's first field and missed its locator; the declared class, applied.

One reversal: `scientific-research-guide/evals/evals.json` is UN-shipped. The
v1 suite tested the generic framework; the current suite is the withheld
domain profiles' routing harness — quoting trigger strings, pitfall rows and
standards traps at row level — so a verbatim refresh would have exported the
withheld knowledge through the eval side door, and keeping the stale copy
would misdescribe it as verbatim. The `[[not_shipped]]` entry carries the
reversal; the v1 copy stays in git history.

Deferred, named: `global-claude-md/CLAUDE.md` gained a representation-selection
rule at the source the same day this round ran; re-applying that file's
template edits is its own procedure-B round, so the snapshot ships one rule
behind, the manifest comment on `representation-models.md` says so, and
`architecture-diagramming/README.md` carries the interim note. Reported, not
fixed: the `tools/` disposition's per-file recheck (2026-08-16, nine entries)
predates several tools the source has since grown; nothing this round ships
from there, so that re-examination belongs to its own round.

Gate: exit 0 with `--source` (163 collected files verified), suite 11/11.

## 2026-08-17 (third) — a sync/doc-accuracy pass, not a refresh

Not a share from the source environment — the user asked for a plain audit:
is local in sync with remote, and does every layer's documentation still
match what's actually in the repo. It was (clean, `origin/main` even), but
the doc side had four stale spots, three of them left behind by the very
refresh logged above.

**`skill-toolkit/README.md`'s own inventory sentence never got the count fix.**
The prior entry corrected `ADOPTERS.md`, `CHANGELOG.md`, and
`tools/share-manifest.toml` to "15 of 18," but the prose in
`skill-toolkit/README.md` — the file a reader actually opens first — still
read "14 個…來源環境共有 15 顆；未收錄的是 `asset-vault`." Fixed to name all
three withheld skills (`asset-vault`, `render-perf`, `system-design`) and the
18/15 split. The inventory table beneath it already had the
`mechanism-share-packaging` row; only the summary paragraph above it was
behind.

**`claude-ops/README.md`'s path-mapping table still said "7 支" hooks.**
`hooks/` has grown to 12 since the 2026-08-14 note was written (3 from
`compact-recovery`, more from later rounds) and neither `hooks/README.md`
nor the top-level `README.md` was wrong — only this one cross-reference
table. Reworded to name both the historical count and the current one, and
pointed at `hooks/README.md` as the number's source of truth so this doesn't
drift again the same way.

**`hooks/README.md` misquoted the file it was citing.** Its own note about
`environment-guide/`'s hook count being a stale snapshot claimed the snapshot
said "hooks/（2 檔）" — that phrase does not exist anywhere in
`environment-guide/`; the actual text there is "7 個 .py + 1 資料檔" /
"7 支," dated 2026-08-14, not 2026-07-31. Corrected the quote and the date.

**`skill-toolkit/skill-trigger-dict.md` carried one router entry for a skill
that has never existed in this environment.** The `[ops-health]` hook that
fires on this file every session start (25.1K, over its 24K review-trigger
size) names the fix procedure explicitly: run the routing-coverage script
and correct what it flags as fiction before considering a cap raise. Ran it
against the live `~/.claude` transcript history (the script is a live-ops
tool, not part of this repo — it reads real session turns, so it cannot run
against a packaged snapshot in isolation). Cross-checked its verdicts
against this session's actual available-skill list rather than trusting the
tool's own "not a local skill" tag at face value (that tag only scans
`~/.claude/skills/*/SKILL.md` and misses built-ins and marketplace plugins —
several of its flags, e.g. `run`, `security-review`, `loop`, were false
positives once checked that way). One flag held up under both checks:
`product-management:write-spec` — no such plugin exists in the installed
marketplace catalog, in this session's skill list, or anywhere in `~/.claude`
outside old archived backups; `git log -S` shows it was present since the
initial anonymized snapshot commit and never corresponded to anything real.
Removed the entry and its one cross-reference (was routing "寫 PRD" to it from
the `scientific-research-guide` avoid-list). No replacement skill covers that
gap; the honest state is that this toolkit has no dedicated PRD-writing
router, not a silent respell to something adjacent. The byte-budget trigger
was a symptom here, not the target — deleting the one fictitious entry does
not clear the file's 24K review threshold on its own, and per the hook's own
instruction that is fine: raising the cap after a real review is the
intended outcome, extraction for its own sake is not.

## 2026-08-17 (second) — the packer packs itself, and a count nobody was checking comes due

Follow-on to the red-team round, on the user's ruling: ship the skill that did
the packing, withhold the two knowledge packs, and write the withholding down.

**What came in.** `skill-toolkit/skills/mechanism-share-packaging/` — `SKILL.md`
and `references/governance-starter.md` verbatim, `evals/evals.json` with the
share repo's own absolute path replaced by `<share-repo>` in two places. The
skill is the procedure behind both `compact-recovery/` and `red-team/`, and its
first hard rule is delegation: the target repo's collection rules are
authoritative and are never restated inside it, because a second copy of a rule
is a fork that drifts. This repo IS that target, which makes shipping it a
mildly recursive act and changes nothing about the procedure.

**What stayed out, with the reason written down.** `render-perf` and
`system-design`, the two knowledge packs, `excluded-by-decision`. The reason is
about STATE, not content: both are unfinished at the source. A knowledge pack's
own posture rule is that a covered branch must cite pack files and an uncovered
branch must say so out loud — ship one half-stocked and you export a trigger
surface whose honest answer to most questions is "no stock here". Both entries
carry a REVIEW-WHEN naming the event that would reopen them, because a
disposition resting on a fact outside this repo is exactly the kind that rots
quietly.

**The count that had been wrong for weeks.** This repo said `skill-toolkit/`
ships "14 of the source's 15 skills". The source had 18. Three additions —
`mechanism-share-packaging`, `render-perf`, `system-design` — had arrived with
no `[[collected]]` and no `[[not_shipped]]` entry between them, so the sentence
naming `asset-vault` as *the* withheld skill was false in a way no check could
see: a count is a claim about a tree the gate cannot read. Now 15 of 18, with
all three declared, and `ADOPTERS.md` says plainly that counts here need a human
to re-derive them.

**The stale router, and the second half of the same edit.**
`skill-toolkit/skill-trigger-dict.md` was three skill sections behind its
source. Check V had been reporting it healthy every round and was right to: for
an `edited` file it can only assert the copy DIFFERS, never that it differs by
exactly the declared edits — its own docstring calls that the known limit.
Refreshed via procedure B, with a second declared edit removing the whole
`## 知識包` section so the dictionary stops routing to skills this repo does not
have. That edit then had to be finished twice: the file's quick-routing table
near the end carried its own two rows for the same pair. **A router is not one
place** — grep the skill name, not the section heading.

**What the gate forced.** Two findings, both mechanical: `<source path>` in a
path position inside the seeded governance template (declared under
`[placeholders]` path_position_ok — it is a genuine parameter, and substituting
a real value would defeat a file whose premise is that the reader's source is
elsewhere), and check S catching `skill-toolkit/README.md`'s inventory table one
row short of the tree. Gate: exit 0 with `--source`, 184 tracked, 159 collected
compared; suite 11/11; `interop-layer/test_interop.py` 14/14.

## 2026-08-17 — the red team ships its ruler, not just its verdict

New share: `red-team/` — adversarial review made machine-checkable. The second
mechanism export, and the second time a `[[not_shipped]]` root turned out to be
hiding something transferable inside it.

**What came in.** Seven files from `~/.claude/tools/extdispatch/` at source
commit `d500be3`, first collection: `score_redteam.py` (acceptance layers 2–4 —
structure, anchor, scope, spot-check), `jsonspan.py` (the one JSON-span
extractor, extracted after the same scanner was found written three times with
the *structure* gate holding the copy nobody had fixed), `redteam_verify.py`
(layer 5 — one refuter per finding, verifier ≠ author enforced),
`test_score_anchor.py` (ten cases), `test_parser_rulers.py` (eight cases), and
two prompt templates. `README.md` (the mode: ladder diagram, the measurement
behind each design choice, three wirings, dispatcher contract, tunables,
per-part failure modes) and `ACCEPTANCE.md` (section A blind-runnable with no
model, section B needing one) authored here.

**One behavioural edit, declared as such.** `redteam_verify.py` opened with
`import extdispatch as ed` at module scope — a hard dependency on the
dispatcher this repo does not ship, which would have made the shipped file
ImportError on line 41. It now loads a dispatcher by NAME (`--dispatcher`,
defaulting to `extdispatch`, so the source's own invocation is unchanged) and
refuses against a two-symbol contract before a single grant is spent.
`--author`/`--verifier` lost their argparse `choices=` for the same reason and
gained an explicit membership check: same rejection, same exit code, four lines
later. Everything else is the usual de-identification class — two second-drive
`--repo` examples, one pointer into a private report tree, one commit sha and
one private project's four file paths (both templated, with the SCOPE block
kept as four lines, because collapsing it onto one token is the over-scrub
failure this repo is named after).

**The disposition that was wrong about its own scope.** `tools/extdispatch/`
was `excluded-by-decision` as of 2026-08-16, and its three disqualifying
classes — a policy allowlist of local project paths, telemetry carrying home
paths in every row, 53 files of raw model output from real work — are all still
true and all still not shipped. What was wrong was applying them to the whole
directory: the same root also held the acceptance layer, which touches none of
the three. Narrowed to `partial`, with the per-file split written out and the
2026-08-16 reasoning kept in place rather than replaced. This is the `tools/`
entry's own 2026-08-15 lesson recurring one level down — *a disposition written
for a root keeps applying itself to files it never examined* — and it is now
the second time this repo has made that exact mistake, which is worth more than
the correction itself.

`prompts/redteam-v2.1-kys.txt` is the one file withheld for redundancy rather
than content: templated, it is byte-identical to the version that ships, and
publishing it would only disclose a second private project's tree shape.

**Dispositions re-checked, not assumed.** Both external-dispatch hook entries
were re-read the same day because the entry beneath them moved: each depends on
a file that stayed out (`extdispatch.py`, `allowlist.txt`), so both hold
unchanged — recorded in the entries rather than left to be re-derived. The
`settings.example.json` omission list is untouched: still three omissions, two
of them these hooks.

**Counts.** Collected roots eight -> nine, and `red-team/` was declared a root
on its creation day rather than joining the "had never looked" list. Tracked
files: 181, as the gate reports them.

**What ran.** Gate exit 0 with `--source` (156 collected files compared);
`tools/test_share_gate.py` 11/11; `interop-layer/test_interop.py` 14/14. The
shipped copies themselves: `test_score_anchor.py` 10/10 and
`test_parser_rulers.py` 8 cases / 4 disagreements / no stale-boundary warning,
both run from `red-team/` rather than from the source. Layer 5's four refusal
paths and one full chain were exercised against a stub dispatcher — which
proves the wiring and explicitly does not prove that a real model refutes
anything; `ACCEPTANCE.md` records that split rather than blurring it. The
round's only gate finding was the new `AGENTS.md` section citing the reviewer
subagent under an `agents/` filename this repo does not carry — the shipped one
is `agents/engineering-code-reviewer.md` — check R catching a broken pointer in
prose written minutes earlier. Writing the wrong path out again here would
re-trip it, which is check R declining to tell a post-mortem from a pointer;
the entry says what happened instead.

**Zip.** `red-team-2026-08-17.zip` at the repo root, gitignored like the last
one: the repo publishes files and commits, not archives.

## 2026-08-16 (fourth) — the compaction learns the way back, and the share learns to carry it

New share: `compact-recovery/` — the post-compact recall operating mode, shared
the same day it passed a full-chain LIVE acceptance at the source (a real
`/compact`: bookmark written, pointer card injected naming the exact pre-compact
region, recall ladder walked for a fact the summary dropped, and the read guard
still firing POST-compact).

**What came in.** Three hooks into `hooks/` (`compact_bookmark.py`,
`compact_pointer.py`, `transcript_read_guard.py`) and the digest generator
`preserve.py` into `compact-recovery/`, collected at source commit `519342c`;
`README.md` (operating mode: event-pair bridge, recall ladder, token economics,
install incl. the optional SessionEnd mount, tunables, platform-contract
re-check recipes) and `ACCEPTANCE.md` (seven-item real-fire checklist) authored
here. Every edit is the usual de-identification class, declared per file: one
project name + session id, one scheduled-task name, one second-drive mirror
root, and pointers into trees that do not ship (memory/, the source's rule
registry, PIM design docs). Measurements, dates and ruling ids all kept.

**Dispositions corrected, not deleted.** `tools/memory-pipeline/` ("a separate
product… that decision has not been made") is now PARTIALLY superseded: the
user made the decision for exactly one of its 279 files — `preserve.py` ships,
the vendored search stack stays out. The settings.example.json entry's
"SessionEnd script is not part of this share" reason is amended the same way:
the script now ships, and the mount still stays out of the template because it
would point outside hooks/ — the optional block lives in
`compact-recovery/README.md`, keeping the template's "mounts hooks/ and nothing
else" invariant intact.

**Counts.** `hooks/` went nine -> twelve; the mounting template gained a
PreCompact event and its omission list went three -> two.

**What the gate forced, and what it got.** The round's first gate run caught
the shipped `claude-ops/ops/rule-registry.md` lagging the source it mirrors —
check V doing its job, the source having gained two entries the same day
('compact recovery' and 'browser-pane pixel route'). Refreshed via procedure
B, verbatim -> edited with four declared de-identification edits, all inside
the compact-recovery entry. The same run caught `ACCEPTANCE.md` as an
undeclared file under the brand-new collected root: repo-authored acceptance
checklists are now the third authored-name exemption beside README/NOTICE in
`share_gate.py`, with test case 11 as the negative control keeping the
exemption narrow — and case 9 (current tree) doubling as the
fails-without-the-change half, since the live tree now holds one.
`<sid>`/`<session-id>` joined `[placeholders]` path_position_ok. Gate: exit 0
with `--source`; suite 11/11.

**Zip.** This share doubles as a hand-off bundle: a `compact-recovery-*.zip`
is built at the repo root for physically handing the mechanism to someone, and
`*.zip` is now gitignored — the repo publishes files and commits, not archives.

Source tree re-checked unchanged at `519342c` after collection; the dirty
paths there (four references/ files, two outputs/ files) are the source's own
pending pool and none is a file this round collected.

## 2026-08-16 (third) — the twin gets fixed upstream, and the sweep breaks again

Two things closed the day: the sibling gap the co-upgrade sweep found was fixed
at the source, and a second re-collection round tested the morning's rules
against real drift. The rules held. The TOOLING did not, which is the finding.

**The twin, fixed at the source.** `skill-share-packaging` had the same shape as
the morning's failure and sharper: hard rule 1 says fixes flow canonical → copy
and never back, so the canonical skill by construction never learns what an
export decided; A6 wrote those decisions to a share-notes file, and nothing read
it. A re-export re-derived everything from the canonical and dropped every
judgement the canonical cannot carry. New A0 globs for a previous
`SHARE-NOTES.md` and refuses to start from scratch on a hit; A6 now fixes the
file's NAME (A0 depends on it) and requires each entry to say whether it must
survive the next export. Fixed in the source environment at `88490bc`, then
collected here — which is the correct direction, and the reason the share repo's
copy was not edited in place.

**The sweep broke the same six decisions a second time, hours after the rule
against it was written.** The rewritten `COLLECTION-RULES.md` says sort the
candidate list into A and B before copying. The script did not know that, so it
ran A over B's files again — same four excluded files re-introduced, same share
edits reverted. The round's own disposition had predicted exactly this
("if V fires on a real reverted edit, procedure B did not work — the answer is
mechanical, not editorial"), and it did. The refresh script now reads the
manifest and REFUSES by default: it touches a file only when the declared status
is `verbatim`, names every `edited`/`template` file it skipped, and names every
file with no entry at all. Procedure B's sorting step, mechanised.

**Two declared edits ended because upstream fixed them.** The source removed the
private asset-library pointers from `hooks/ui_verify_guard.py` and
`ops/environment.md` itself, so both are `verbatim` again. Check V is what
surfaced it — "declared 'edited', but is byte-identical to the source" is the
same finding whether an edit was dropped by accident or retired by upstream, and
V cannot tell them apart. Both entries keep their superseded edit text under a
comment saying which of the two happened, because that distinction is exactly
what a later reader cannot reconstruct.

**Check S5 was wrong about duplicates.** It required every hook to appear in the
mounting template exactly once. The source turned `ui_verify_guard.py` into a
PreToolUse/PostToolUse router — one file, two events, entirely correct — and S5
would have reported the correct wiring as a defect. Duplicates are now judged per
(event, matcher, hook), and the template gained the PostToolUse mount it had been
missing, which is a half-wired hook the check existed to catch and nearly
prevented itself from catching.

**One new source reference excluded.** `ops/references/browser-pane-pixel-route.md`
is normally exactly the class this repo ships. Its payload is runnable recipes
carrying an absolute home path, a private asset's source path, an npx-cache
directory keyed by a content hash, and three private project names. Step 4 of the
decision procedure does not apply — the machine-specific part is not incidental
to the recipes, it IS the recipes — and a template with the measurements removed
would be a shape with no measurement in it. The portable half already ships in
`environment.md` and `global-claude-md/CLAUDE.md`, both refreshed the same day.

**Two dirty-source acks cleared by their own review-when.** Both said "that work
lands at the source"; it landed mid-round, the files were re-collected, and the
acks are gone. The third (`references/PROJECTS.md`) has no review-when on
purpose — a live project index is dirty as its normal state — and remains.

## 2026-08-16 (later) — the round's own findings become checks

Same day, second pass. Everything below exists because the morning's collection
found it by hand, and a finding that stays a story is a finding that recurs.

**Two new checks, one of them opt-in.**
`D` (dead declaration) removes entries that no longer match anything: an
`[[allow]]` outliving its finding, a `[[not_shipped]]` for a file that now
ships, a placeholder token nothing uses. All three classes were live when it was
written — including two `[[allow]]` entries added that same morning and made
dead by a restore four hours later, which is now recorded in the manifest as the
clearest small example of the pattern.
`V` (source-verify) needs `--source <path>` and does the one thing check C's own
docstring says it cannot: compares every collected file against the real source.
The finding that has no other detector is **"declared 'edited', but is
byte-identical to the source"** — a declared edit that a refresh reverted, which
is exactly what happened to six files this morning while every repo-local check
passed. It is opt-in because an adopter has no source to point at, and it is
never silently skipped.

**Check S gained mount parity.** Every `.py` under `hooks/` appears in
`settings.example.json` exactly once, and nothing else does. The template had
been mounting 7 of 9.

**Both new checks were wrong on their first run, and that is recorded because it
is the lesson.** D reported the two `partial` dispositions as findings — a
`partial` entry MEANS part of it ships, so "it resolves" is what the entry
already says. S reported `ops_health_nudge.py` as mounted twice; the second
"mount" was the `_README` line telling the reader how to smoke-test it by hand.
Both were instruments ruling on something they could not determine, on the first
output of checks written to enforce exactly that rule. D now exempts `partial`;
S parses the JSON instead of grepping the file.

**The test suite went from 5 cases to 10, two of them negative controls.** A
system path on a drive letter must NOT fire; the current tree must pass. A gate
calibrated only on what it should catch scores 100% by rejecting everything.

**`COLLECTION-RULES.md` was rewritten where it was imprecise enough to cause the
damage.** The morning's failure was procedural, not careless: the file said
"verbatim is the default" and said nothing about a file that is already here.
- Rule 1 now splits: verbatim is the default for a FIRST collection and **never**
  for a refresh, and the procedure splits with it — **A** for a file not here
  yet, **B** for one that is, with sorting the candidate list by which procedure
  it needs made an explicit step, because a bulk sweep runs A over B's files.
- B carries the scan the gate cannot do, named as four concrete classes, all
  four of which were live findings this morning: a private-tree pointer with no
  path in it, subject matter arriving inside a file whose structure is what
  ships, a pointer into an excluded directory, and a count claim in prose that
  the refresh has just falsified.
- Rule 2's scrub-target list is now enumerated rather than inferred, including
  the non-system-drive class, and states what is NOT a target — project names,
  ruling ids, evidence lines.
- New rule 7: reach a verdict this round. A deferral that survives two rounds is
  a decision made by nobody. New rule 8: the source's own words about sharing
  are first-hand evidence and outrank your reading of the file.
- Step 0 now defines "dirty" as a CONTENT difference: a file showing `M` for
  line endings alone is not a reason to stop, and treating it as one teaches you
  to skip the check.
- The decision procedure gained the inverse of its row 2: excluding something a
  shipped file ROUTES to is a two-part act — the disposition, and the edit to
  whatever pointed at it. Nothing detects the half you forget.

**One disposition closed rather than rolled forward.** The three source-side
tests for hooks this repo ships were recorded this morning as an explicit
deferral. User ruling: not collected. The entry now decides instead of deferring
— per the new rule 7, and because the entry itself was the first thing that rule
would have caught.

## 2026-08-16 — the other five roots, and what a verbatim sweep costs

Full re-collection against source commit `f8605e4`. Two things happened: the
repo caught up with three days of source drift, and the mechanism that was
supposed to make that safe turned out to cover three of its eight roots.

**Check C was watching 3/8 of what it should have been.** `collected_roots` was
`hooks/`, `agents/`, `interop-layer/`. Everything under `claude-ops/`,
`global-claude-md/`, `environment-guide/`, `skill-toolkit/` and `thinking-notes/`
— 118 files — had been collected since the day each folder was created and
declared nowhere. That is the same finding as 2026-08-15's, one level wider: the
2026-08-15 entry fixed the one directory whose incident wrote `COLLECTION-RULES.md`
and did not ask which others were in the same position. All eight roots are
declared now, 99 `verbatim` / 14 `edited` / 5 `template`, with `verbatim` computed
by byte comparison rather than asserted. Positive control run before believing
it: deleting one entry and flipping one `verbatim` to `edited` both produce the
expected finding, so the check is looking at the new roots rather than passing
them by.

**What the undeclared roots were hiding, found the hard way.** The refresh was
run as a verbatim sweep first. It silently reverted six de-identification
decisions across two skills — `scientific-research-guide`'s domain manifest, its
research-state fixture and its citation inbox came back carrying the author's
actual research topics, and `motion-design`'s notes came back pointing at a
vendored Three.js package this repo deliberately does not redistribute. Nothing
flagged it. The decisions had been made in commits (`fde9ae3`, `81dfe82`) and
nowhere a check could read, which is exactly the failure `COLLECTION-RULES.md`
opens with, reproduced from the other direction: not an unrecorded edit, but an
unrecorded DECISION NOT to take the source's text. All six are restored and all
six are now `[[collected]]` entries with their reasoning.

**A leak class the gate could not see.** The same sweep brought in nine absolute
paths on a second drive — a private asset library, real project roots, the
operator's own publication tree. Every one scanned clean: the leak patterns knew
about home directories and nothing else. Three more had been sitting in
`Global_skill_update.md` since long before this round, published. `sharelib.py`
gained an `absolute local path (non-system drive)` pattern; system roots and
`Users` are excluded, and four narrow `[[allow]]` entries cover the two files
where such a path is the worked example rather than a location.

**The gate's own leak patterns were weaker than the source's.** Running
`interop-layer/test_interop.py` — collected this round — against this repo's
`sharelib.py` failed two of its known-TRUE samples: `sk_live_`/`sk_test_` and
`AIza` key shapes were in the source's inline list and were dropped when
`interop.py` was refactored to import from here on 2026-08-11. The manifest
entry claimed "behaviour is identical — same patterns"; it was not, and for the
gate's whole life a Stripe-shaped or Google API key would have published cleanly.
Both patterns are added, the false claim is corrected in place rather than
deleted, and the calibration set that caught it now ships and runs here. This is
the argument for two-sided calibration, from the repo's own rules, landing on
the repo itself.

**New content.** Four hooks and one test join the mechanism layer:
`context_runway_shadow.py` (context runway vs an unwritten checkpoint),
`fieldwork_threshold_notice.py` (main-session fieldwork vs the delegation
threshold), `browser-pane-allowlist.json` (the pane guard was rewritten from
blocklist to allowlist at the source, so the second file is now load-bearing),
and `interop-layer/test_interop.py`. Two ops references —
`external-dispatch.md` and `skill-trigger-classes.md` — and one skill,
`skill-co-upgrade`, bringing the toolkit to 14 of the source's 15.

**`hooks/settings.example.json` had been quietly short.** It mounted 7 hooks
while 9 shipped. Re-derived against the source's committed `settings.json`; the
invariant to check after any hook change is now stated in its manifest entry —
every `.py` under `hooks/` appears exactly once, and nothing else does.

**Dispositions re-checked, two of them wrong.** `outputs/` was described as a
scratch directory whose contents are personal, with a fallback saying it is "not
a rule surface". The source began tracking it on 2026-08-16 precisely because it
is one — the retrospective layer, and two shipped files cite into it by name. It
stays excluded, for the reason that survived (every artifact is a finding about a
specific real project) rather than the reason that did not. `tools/` was
re-checked per file as its own 2026-08-15 correction demanded: nine entries,
three of which are tests for hooks this repo ships and are deferred rather than
judged — recorded as a deferral so the next round does not read it as settled.
New entries for `references/` (the source's project-memory layer, 15 files),
`tools/extdispatch/`, and the two external-dispatch hooks, which are portable and
would still be harmful to mount without the dispatcher they gate.

**One gate change worth naming.** `[placeholders] literal` was added to
`share-manifest.toml`, for tokens that are not placeholders at all — a harness
tag quoted in prose. The alternative was declaring `<browser_surfaces>` under
`path_position_ok`, which asserts that a human confirmed a reader can fill it in.
Recording a false claim to silence a finding is the decay this file exists to
prevent, so the vocabulary grew instead.

## 2026-08-15 (later) — the caveat is cleared, and two frozen rows come out

The morning's collection ran against an uncommitted source tree and said so. The
commits have now landed — eight of them, split by theme — and every collected
file was re-collected against `df21070`. `tools/share-manifest.toml` names the
commits; `git show <sha>:<path>` reproduces the bytes.

**Four agent definitions were declaring `verbatim` falsely.** Not drift here —
drift at the SOURCE: `engineering-backend-architect`, `engineering-frontend-
developer`, `testing-api-tester` and `testing-qa-engineer` had uncommitted local
edits when they were last collected. Check C cannot see this (it says outright
that it cannot compare against a source it does not have), which is exactly the
"a judgement made once, in prose, decays silently" failure `COLLECTION-RULES.md`
opens with. The edits turned out to be publishable — `effort: medium` completing
the roster's cost declarations, and a `file:line` + "label unverified claims"
output contract for the two testing definitions — so they were committed at the
source and re-collected. All four are `verbatim` again, and now truthfully.

**Two targets left the registry.** codex and Antigravity had been sync-off since
2026-08-11 and their rows were still frozen at a 2026-07-10 verification — sitting
directly under a heading that says those locations are volatile facts requiring
re-verification. One of the two applications had since been uninstalled, so its
row could not be re-verified at all. The reason for keeping them ("the path +
profile + cross-tool caveat are verified facts worth keeping") had quietly
inverted into its opposite. Both rows are gone; the `disabled` mechanism stays in
`interop.py` with no target using it, so a future sync-off ruling does not have to
re-invent it. **The portable half:** a registry row reads as a fact sheet even
when its cells are quotations, and annotating one does not fix that — removing it
does. Re-adding a target now has to walk the checklist that re-derives the paths
from the platform's current docs.

**The rule-registry entry was 60 lines and carrying three narratives that were
not standing reasons.** A `config-self-audit` pass (owed for a rule-layer change
and skipped that morning) cut it to 30, dropped a field that was not in the
schema, and moved the check-11 material to the relaxation-gate entry where
someone looking for it would actually grep. What came out became
`claude-ops/ops/lessons.md` **L-016** — *a check that cannot fail is
indistinguishable from a check that passes*, with the day's three instances
(predicate satisfied by prose; report nobody invokes; eval whose subject was
retired) and a three-part fix. **L-005** goes to `hits: 3`: the frozen registry
rows are its "carried claim reads as an established fact" mechanism again, in its
highest-risk carrier.

**One declared exception.** Three statements in this repo's frozen records still
say `light`, or describe the profile as an open question: the `At a glance` table
in the 2026-08-11 entry below, that entry's `interop-layer/` bullet, and
`Global_skill_update.md`'s `open:` field. They were correct on the day they were
written, and rewriting a dated record to match today is tampering — which is why
the earlier pass deliberately left them alone and added a new entry instead. On
the requester's instruction they now carry a **forward pointer**, marked inline as
a later annotation, with the original sentence untouched in every case. The rule
is unchanged: a frozen record is appended to, never edited. This is the narrow
exception — a reader landing on a stale row from a search result had no way to
know a newer entry existed.

## 2026-08-15 — interop-layer joins the provenance regime, and the drift it hid

`interop-layer/` had been collected since 2026-07-10 and declared nowhere. It
was in no `collected_roots`, so check C never looked at it — and in that gap the
copy drifted **in both directions at once**: failure 1 (over-scrub) and failure
2 (under-declare) of `tools/COLLECTION-RULES.md` happening simultaneously, in
the one directory whose own over-scrub incident (2026-08-07, recorded below) is
the reason that file exists. Six files re-collected; all six now declared.

**What this repo had that the source did not.** Two things, both kept, both now
declared as edits so the next diff does not have to re-derive them: `interop.py`
imports the leak patterns from `tools/sharelib.py` instead of defining them
inline (one definition, two callers — the source has one caller and no second
gate to keep in step, so importing there would buy nothing), and
`MIGRATION-MAP.md` carries a share-repo-only section on disposition classes (it
documents this repo's manifest and gate; the source has no publication layer and
would receive four dangling citations). That section now states its own backflow
exemption inline.

**What this repo had that was simply wrong.** `README.md` carried four
undeclared edits, all reverted to source. The instructive one is a deleted
pointer to `OPERATOR-GUIDE.md` — a citation that *resolves in this repo*
(`source_map` sends it to `environment-guide/OPERATOR-GUIDE.md`), removed for no
stated reason. That is the same failure in miniature, committed after the rule
against it was written. Also reverted: `Claude 專屬` generalised to `平台專屬`
when the specificity was the point; the `archive/interop-refs-2026-08-11/` path
replaced by a vague phrase while this very file names it openly two entries
down; and a reordered list carrying no information either way.

**What the source had that never flowed back** — fixed at the source first, then
re-collected: the `scan` subcommand was missing from the manual's command list
though it has existed since 2026-08-11; `status` was described as covering
"three targets" when two are `[off]`; the leak gate was absent from the
operating invariants; and "known boundaries" still offered reference-compile as
a live migration path for method content, a claim the same file retires four
paragraphs earlier.

**Neither side had the block count right.** The manual said 6-of-13 `full`-only
blocks, this copy said 8-of-15; `parse_blocks()` reports **15 blocks, 8 `light`,
7 `full`-only**. Both figures were hand-maintained restatements of something
derivable, so both rotted. Corrected, with a note to re-derive rather than copy
the sentence.

**opencode moved `light` → `full`** (ruling 2026-08-15). The reasoning is worth
more than the setting: the birth-budget argument that picked `light` inverted
once someone measured it. No instruction file had ever been deployed, so the
target fell back to reading the source's `CLAUDE.md` — ~16.5 KB of
Claude-Code-specific mechanism a non-Claude worker cannot act on. `full` is
~11 KB, so the "heavier" profile costs the worker *less* context than the status
quo it replaced. Port the shape of that argument, not the number: it turns on
what YOUR target falls back to when nothing is deployed.

**And nothing was watching.** `interop.py status` had been printing `[missing]`
and exiting 1 since 2026-08-11 — the target was never deployed at all — and
no one saw it, because nothing ran it. `hooks/ops_health_nudge.py` gains
**check 12**: a stat()-only session-start screen (artifact absent, not ours, or
older than its source; curation stamp absent or behind `CLAUDE.md`) whose only
remedy is "run `status`". It routes to the authority instead of impersonating
it — mtime is not the commit comparison `status` makes — so a false positive
costs one cheap command. It reads the target registry out of `interop.py`
rather than re-declaring it. One synthetic-tree case caught a real bug in the
check's first draft: a machine with no interop layer at all got a permanent,
unfixable nudge.

**Check 11 had never once fired correctly.** Found while testing the above. It
asked `"ops-relaxation:" not in text` — and the global `CLAUDE.md` contains that
token in prose ("offer to record `ops-relaxation:` in project CLAUDE.md"), so
every project `CLAUDE.md` derived from it passed vacuously. A source-wide grep
that day found *no* occurrence of the token anywhere that was a real
declaration; the check had been silently green since birth. The lesson is
portable and cheap: **a mention is not a declaration — require the value, not
the key.** It now demands a level (`ops-relaxation: L1`), accepting a bullet or
bold wrapper but not the backtick-quoted form that `05-authority.md`'s own
example uses.

This repo's copy of the hook now carries **one declared specialization**, its
first: check 11 runs only when `ops/05-authority.md` is present. Taking the
hooks lane without the ops lane is a supported outcome here — the lanes are
independent — and such an adopter would otherwise be nagged every session about
a key defined nowhere they can read and satisfiable by no file they own. A
permanently-on alarm is the kind nobody reads, and it would train them past the
other eleven checks. It is not back-flowed: on the source machine the ops layer
is always present, so the same gate could only mask a real ghost-rule failure,
which is check 4's job. `hooks/ops_health_nudge.py` moves from `verbatim` to
`edited` accordingly.

The test suite runs against **either** copy and asserts the opposite outcome per
edition — 21/21 on both.

`acceptance-evals.md` eval 8 was replaced. It required reading
`interop-refs/design-protocol.md` — a directory retired 2026-08-11 that exists
at no target — so it could neither pass nor fail: coverage on paper, measuring
nothing. It now tests what `delegation_block()` actually promises.

**One gate change.** Check C skipped any file named `README.md` under a
collected root — a name heuristic for the lane guides written here, which
misfires on `interop-layer/README.md`, a genuinely collected file that happens
to share the name. A declared `[[collected]]` entry now overrides the heuristic;
undeclared READMEs behave exactly as before. Gate clean; 5/5
`test_share_gate.py` cases unchanged.

**Recorded caveat — CLEARED the same day, see the entry above.** The source
working tree was dirty at collection time: the edits above were applied but not
committed, on the requester's instruction, so the bytes here matched a working
tree rather than commit `86c6b39`. Left standing rather than deleted, because a
retracted caveat is evidence the record works. The commits landed and everything
was re-collected against `df21070`.

## 2026-08-14 (later) — the source audit: most of it was never collected

The gate above made the repo honest about what it did not ship. The obvious next
question was whether those absences were decisions. A read-only audit of the
source environment at commit `182d9793` says mostly not.

**The hooks were never machine-bound.** Three of them sat in the manifest as
`referenced-only` with the reasoning "machine-bound: settings.json wires them
with absolute interpreter paths". Checking instead of reasoning: the source has
**seven** hooks, not the two the environment-guide snapshot names, and every one
resolves its paths through `Path.home()` / `os.path.expanduser` /
`CLAUDE_CONFIG_DIR` / `os.environ["TEMP"]`. Zero hardcoded accounts, zero
absolute paths. They were not withheld; they were never collected. All seven now
ship under **`hooks/`** — destructive-command deny-list, subagent model cap, the
two browser-pane guards with their blocklist, the session health nudge, the
shadow delivery gate, and the rule-load logger — each fail-open, each carrying
the incident record that produced it.

That flips the outside adopter's headline finding. "Command policy and Lifecycle
are upstream-referenced-only" was true of the repo and false of the source.

**`settings.json` was half right.** Its permission block is generic and its
`ask` entries are the interesting half; only the hook-mount paths are
machine-bound, because Claude Code expands neither `~` nor environment variables
in a hook command. It ships as `hooks/settings.example.json` with `<PYTHON_EXE>`
and `<CLAUDE_HOME>` to substitute, the memory-pipeline mount removed rather than
left pointing at a script this share does not carry, and a `_README` saying
plainly that a permission list is one operator's threat model, not a
recommendation.

**`agents/` had never been mentioned at all**, while `claude-ops/ops/20-dispatch.md`
routes to all eight by name. They ship byte-verbatim. Their bodies were rewritten
from CLAUDE.md and `ops/` on 2026-08-12 — the third-party lineage in the
`adopted-from` comment is provenance, not remaining content, which is why the
threejs-skills standard (no verifiable licence → do not ship) reaches the
opposite conclusion here.

**`references/PROJECTS.md` was `partial`, not private.** Header and column
semantics are a generic format spec; the rows are real projects. The format
ships as `claude-ops/references/PROJECTS.md`, so the two skills and the ops rule
that cite it finally resolve.

Confirmed genuinely out: `skills/asset-vault` (hardcoded private library —
`skill-toolkit/` ships 13 of 14, now stated rather than left to be noticed),
`reports/`, `LABEL-REGISTRY.md`, `telemetry/`, the source environment's own
`tools/`.

**`tools/COLLECTION-RULES.md`** (new) is the rule this audit earned: a seven-question
decision table, the closed verdict vocabulary, a never-collect list, and the
mandatory procedure — record the source SHA, read every byte, diff against the
source with line endings normalised, declare every edit, run the gate, confirm
the source is untouched. **Check C** enforces the declarable half: every file
under a collected root carries its source, a valid status, and one recorded
reason per edit; an entry pointing at a file that is not there fails too.

Nine files were collected verbatim and four edited — two local session ids and
three pointers into a private asset library, each listed individually in
`[[collected]] edits`. Source SHA `182d9793` unchanged, working tree clean; the
audit was read-only throughout.

The lesson worth keeping is not about hooks. **A disposition is a claim about
the source, and a claim nobody re-tests decays into a fact.** That one sat
unexamined for a month and was the largest gap in the repo.

## 2026-08-14 — the publishing gate, and the two failures that forced it

Not a sync from the source environment. This entry is about the repo's own
share machinery, prompted by an outside adopter's review of commit `23af48b`.

De-identification here had always been decided verbally, per push. That produced
two opposite failures at once, neither of which we found ourselves:

- **Over-scrub.** `interop-layer/README.md` had 23 real, harmless,
  repo-relative paths — six distinct filenames — collapsed onto a single
  `<URL>` token, four of them inside the runnable-command fence. The operator
  manual could not be followed. Restored from `a8e1b29`, which predates the
  damage.
- **Under-declare.** 20+ rule files cite `hooks/model_cap_guard.py`,
  `hooks/ops_health_nudge.py` and `settings.json` as the MECHANISM enforcing a
  rule, while the repo ships none of them. An adopter reads "mechanically
  enforced" and receives prose, with nothing marking the difference. The
  *Translate per target* rule in `MIGRATION-MAP.md` — "the loss must be visible,
  not silent" — already forbade this; nothing was checking.

**`tools/`** (new) makes both mechanical. `share_gate.py` runs four fail-closed
checks over every tracked file and exits 1 on any finding: **L** leak, **P**
placeholder position, **R** reference disposition, **S** packaging structure.
It never edits anything, because automatic scrubbing is the failure it exists to
catch. `sharelib.py` holds the leak patterns as one definition shared with
`interop-layer/interop.py`, so the two gates cannot drift; the email pattern now
requires an alphabetic TLD (`three@0.185.1` is an npm specifier) and two
repo-scope patterns are added — any account's home path, and private network
hosts. `share-manifest.toml` is the only way past a finding, every entry
carrying a reason. `test_share_gate.py` replays both incidents plus planted
personal data against the live gate: 4/4.

Check P is positional rather than a vocabulary: free prose templates
(`<project name>`, `<title>` — about 160 of them) are none of the gate's
business, but a token adjacent to a `/`, a token on a runnable line, and a token
used as a standalone value four or more times in one file each fail. The `<URL>`
incident trips all three.

**What the gate then found on its own**: `~/.claude/references/PROJECTS.md` and
`~/.claude/LABEL-REGISTRY.md`, cited by the ops layer and two skills, ship
nowhere and had never been disclosed. Both now carry a disposition.

**Four disposition classes** replace the single "do not migrate" bucket —
`upstream-absent`, `referenced-only`, `excluded-by-decision`, `partial` — each
with the fallback the adopter actually gets. Written into `MIGRATION-MAP.md`
(prose) and `share-manifest.toml` (machine-readable). The distinction came from
the adopter's review; naming it here saves the next adopter from re-deriving it.

**Routing.** `README.md` now opens with three lanes instead of a folder table:
first read, returning read, installing. The returning lane exists because "I
read this already, it probably hasn't changed" is a documented failure in this
repo's own history — a target flipped to SYNC OFF inside an unchanged-looking
registry, the whole method layer was retired, and one same-day "correction" was
itself wrong and is retracted. It names the four files whose meaning inverts on
small diffs. **`ADOPTERS.md`** (new) covers where not to clone this repo, what it
names but does not ship, and the symptom table separating platform permission
and cache problems from defects here — deliberately without trying to solve
them. `claude-ops/README.md` gains the source-path → repo-path map that
`global-claude-md/README.md` already had.

No release tags or digests were added, on purpose: adopters pin a SHA on their
side, and a version number from here would imply a compatibility promise that
does not exist. Recorded in `ADOPTERS.md` rather than left unstated.

## 2026-08-13 — the read-time map layer, ops cap raise, provisional values

One thread from the source, plus two corrections it forced.

- **`claude-ops/ops/references/project-map.md`** (new) + **`60-bootstrap.md` §H**
  — a second record layer, split from the existing one by REGENERABILITY rather
  than by content. Everything the ops layer had was write-time: know-why,
  produced while doing the work, unreproducible, never expiring. A repo with no
  such records — unfamiliar, third-party, or predating the system — hit an empty
  §A step 1 and no derive procedure, so every session re-derived the project from
  scratch. The map is the read-time half: machine-generated know-what/where,
  carrying a `generated-from` git SHA as its fingerprint, expiring on any commit
  inside its declared `covers` globs. The detail file holds the header schema,
  the `[git]`/`[read]`/`[infer]` provenance tags, a closed six-diagram catalogue
  (**derived** mermaid, not hand-drawn — a hand-drawn diagram is a write-time
  artifact and drifts with nothing to detect it), the FRESH/DRIFT/STALE
  algorithm, and a three-write interface (`generate`/`patch`/`prune`) with
  defined fingerprint effects. Concept borrowed from a knowledge-graph tool's
  fingerprint-and-cache mechanism, minus its graph engine — that tool's own
  benchmark puts token reduction near 1× on small codebases, so the engine does
  not earn its dependency weight at this scale.
  **`skill-toolkit/skills/workflow-checkpoint/`** gained the two mounts, and
  they are deliberately NOT the same mount: freshness is read-time and fires at
  session start (§C step 1), promote/demote are write-time and fire at the
  checkpoint sweep (step 5c). Hanging a read-time check on a phase-end ritual
  would be the exact category error the layer exists to name.
- **`40-maintenance.md` §3 + `rule-registry.md` — ops file cap 12K → 15K**, with
  `lessons.md` and `rule-registry.md` newly exempt. The trigger was that six
  files sat over the old cap at once and the nudge fired every session with no
  pass able to clear it; a permanently-on alarm has stopped measuring anything.
  The two exempt files' size tracks the CORPUS, not bloat, so an over-cap
  reading on them has no extract remedy at all. **This entry also catches up a
  correction this repo missed on 2026-08-12**: the §3 table still read "~12K
  **chars**" while the source had already resolved the unit to BYTES — and
  `references/integrity-sweep.md` shipped here carrying the *rationale* for that
  correction without the correction itself. All four file-cap rows now say
  bytes.
- **`rule-registry.md` header — PROVISIONAL values.** A threshold shipped as a
  guess must now be registered with `evidence:` opening on the literal token
  `PROVISIONAL`, plus what would settle it and the instruction that observations
  are appended to that entry. Without a registered home the correcting data has
  nowhere to land, is never collected, and the guess silently becomes permanent
  — indistinguishable from a measured value to every later reader. The new
  `map STALE thresholds` entry is the first user of the convention, and
  `integrity-sweep.md` gained check 11 (`grep -n PROVISIONAL`) so unsettled
  values are enumerable rather than remembered. Check 10 was added the same day
  for cap VALUE drift across mechanisms — check 7 compares the unit only, and
  the value class had by then recurred three times.
- **Deliberately not synced**: the source's hook and tooling changes behind
  these rules — the nudge hook's size constant and exemption set, and a
  dashboard renderer that now derives its caps from that hook instead of holding
  a third copy. This repo has never shipped `hooks/` or `tools/`, so those stay
  described-but-absent, as `40-maintenance.md` §3 already does when it names the
  nudge hook. Check 10's rationale names the renderer for the same reason. Also
  not synced: the source's label-family registry (never part of this share), so
  the `SHAPE-1..6` diagram ids in `project-map.md` §5 arrive without the family
  table that reserves them; and the source's own project ledgers, which schedule
  the `map STALE thresholds` measurement — the registry entry carries the
  authority and the write target, which is the portable half.

## 2026-08-12 — inbound-dependency correction, config-self-audit adoption mode

Two independent threads from the source's same-day work, both landing here:

- **`interop-layer/MIGRATION-MAP.md`** — the 2026-08-11 entry recording an
  "opencode reads `~/.claude/skills/` unadapted" dependency was itself wrong:
  measured, opencode read a stale **second physical copy** of the skill corpus
  at `~/.agents/skills/` (frozen weeks earlier, one skill 7KB behind live) and
  never touched `~/.claude/` at all. The source retired that second copy and set
  a kill-switch env var so opencode now supplies itself from the share repo
  instead; the file's inbound-dependency section carries the full measurement
  trail (why the first read inverted, why removing the shadow was part of the
  fix rather than a separate step) because the source flagged the shape as
  reusable. Nothing here changes what this repo publishes — `~/.agents/` is
  entirely local machine state — only the prose explaining the target registry.
- **`skill-toolkit/skills/config-self-audit/`** — gained a second mode (adoption:
  for config copied in wholesale from another environment, auditing relations
  between rules rather than one artifact) plus a §8 subagent-definition
  checklist and a §9 renumber; two new files, `references/imported-config.md`
  and `evals/evals.json`. `skill-share-packaging/SKILL.md` gained one
  disambiguation clause pointing single-skill imports at Mode B and whole-layer
  imports at the new adoption mode. `claude-ops/ops/` gained `references/` (new
  subfolder — landing zone for size-cap-driven extraction of examples/command
  blocks out of the rule files themselves) and `rules-usage-dict.md` picked up
  the routing pointer and three new schema-registry rows.
- **Deliberately not synced**: `skills/motion-design/NOTICE.md`. The source
  file now assumes its `vendor/threejs/` package is present (a local-only
  decision made after the 2026-08-02 exclusion recorded below), which this
  share still doesn't carry — syncing the text would describe content that
  isn't here. Per-file rationale in the `skill-toolkit/` section below.

See the `claude-ops/` and `skill-toolkit/` snapshot-detail sections below for
the file-by-file breakdown.

## 2026-08-11 — structural pass: rule-registry, path-scoped rules, interop redesign

**At a glance** (full detail in the prose below and per-share sections):

| Area | Before this refresh | After this refresh |
|---|---|---|
| Rule rationale | `Global_skill_update.md` — one growing chronological log, rotated when it hit its size cap | `Global_skill_update.md` frozen (historical only) + new **`claude-ops/ops/rule-registry.md`**, keyed by rule, no rotation needed |
| CLAUDE.md architecture rule (FSD) | Inline `## Architecture` section in `global-claude-md/CLAUDE.md`, loaded every session | Moved to new **`global-claude-md/rules/frontend-layering.md`**, loaded only when a matching file is read |
| CLAUDE.md GLSL rule | Inline parenthetical on the runtime-failure bullet | Moved to new **`global-claude-md/rules/shader-failure-modes.md`** |
| Browser-pane UI-verification rule | Rules-layer text only (CLAUDE.md + `lessons.md` L-009) | Hook-enforced where the environment supports it; CLAUDE.md bullet reworded to point at the enforcement, `lessons.md` gained L-010 (the pitfall) and L-011 (why a hook, not just a rule) |
| ops-relaxation for an Opus-tier main-loop model | Always ask, default L0 | **Standing ruling**: Opus-tier → L1 automatically (`CLAUDE.md`, `05-authority.md`) |
| Agent-roster routing table | Lived in `rules-usage-dict.md` §5 | Moved to `20-dispatch.md`; `rules-usage-dict.md` keeps a one-line pointer |
| `40-maintenance.md` size-trigger table | Listed cap values inline, mixed with rationale | Split: table stays, rationale moved to `rule-registry.md`; new "extract, not delete" rule added |
| `lessons.md` schema | 4 fields (Context/Pitfall/Fix) | +required **Evidence** line (session/digest/locator/captured), from 2026-08-11 entries on |
| `70-evolution.md` Problem field | Free-text "cite evidence" | Structured evidence block, same schema as `lessons.md` |
| interop-layer method content | `refs/` folder — 3 curated playbooks compiled into every target's `interop-refs/` | **Retired.** Replaced by `delegation_block()` — target agent reads its own current docs instead |
| interop-layer leak protection | None described | New **leak gate**: every build payload scanned before write; `scan` subcommand added |
| interop-layer targets | opencode (light), codex (full), Antigravity (full) — all live | opencode (light) only; **codex and Antigravity both sync-off** by user ruling |
| Root `archive/` | Did not exist | New, gitignored — holds the retired `refs/` playbooks for local traceability, never published |
| E2 (delivery-gate shadow hook) / E3 (its enforcement phase) | n/a | **Deliberately excluded** — unfinished, user-flagged out of scope; zero mentions anywhere in this repo |

> *Annotation added 2026-08-15, by exception — the row above is left exactly as
> written.* The `interop-layer targets` row froze a state that has since changed
> twice: the profile moved `light` → `full`, and codex and Antigravity were
> removed from the registry outright. The row remains correct **as a record of
> 2026-08-11**; it is not correct as a description of today. See the 2026-08-15
> entries at the top of this file.

Prompted by a matching structural pass in the source environment over 2026-08-08
through 2026-08-11: a chronological audit log that needed permanent-maintenance
rotation was replaced by a rule-keyed registry, two CLAUDE.md rules were sunk into
path-scoped files, and the interop layer's method-content class was retired for a
delegation model. This refresh mirrors that redesign, not just the content diff.

**Deliberately excluded from this refresh**: an in-progress "delivery gate" shadow
hook and its test harness (source-side shorthand: E2), and the enforcement phase
that depends on it (E3, not yet started in the source environment). Both are
unfinished, user-flagged as out of scope for this share, and unverified — nothing
about them appears anywhere in this repo, including in `Global_skill_update.md`'s
otherwise-comprehensive entries for the same date range. If asked, the honest
answer is "excluded on request, not merely omitted."

- **Root `Global_skill_update.md`** — gained a frozen-header banner (mirroring the
  source's own freeze) and six new entries covering 2026-08-08 through 2026-08-11:
  a new browser-pane UI-verification hook, context-budget instrumentation +
  evidence-block schema, a CLAUDE.md trim + the Opus→L1 standing ruling + the new
  `rules/` sink, the audit-trail-to-registry structural change itself, a SKILL.md
  cap raise + codex sync-off ruling, and the interop method-layer redesign. Each
  entry is a rewritten, de-identified summary of the source event — not a verbatim
  copy (the source entries cite internal file paths, personal tool names, and a
  specific machine's session statistics that don't belong in a public share).
- **`claude-ops/ops/`** — new `rule-registry.md` (why each size cap, standing
  ruling, and mechanism holds its current value — the size-and-budget entries and
  the "delivery gate" mechanism entry from the source were reviewed individually;
  the delivery-gate one was excluded per the note above). `40-maintenance.md`
  restructured to point at the registry instead of restating an audit-trail
  schema, plus a new version-control-boundary section and an "extract, not
  delete" rule for size triggers. `05-authority.md` gained the Opus→L1 standing
  ruling. `30-judgment.md` gained a proxy-promotion example (L-012). `70-evolution.md`
  gained the evidence-block requirement. `20-dispatch.md` gained the agent-roster
  table (moved from `rules-usage-dict.md`, which now carries only a pointer).
  `environment.md` gained browser-pane UI-verification and instruction-loading-
  mechanics sections — de-identified: the source blocks name a personal asset-vault
  tool and cite this machine's own session statistics, both dropped in favour of
  the general mechanism description. `lessons.md` gained L-010/L-011/L-012 and the
  required Evidence-line schema note.
- **`global-claude-md/`** — new `rules/` subfolder (`frontend-layering.md`,
  `shader-failure-modes.md`): two rules the source sunk out of CLAUDE.md's
  always-loaded body into path-scoped files that cost nothing until a matching
  file is actually read. `CLAUDE.md` gained the path-scoped-rules index line, the
  Opus→L1 standing ruling (flagged inline as the original author's own grant, not
  a general recommendation), and a reworded browser-pane bullet (hook-enforced
  where the environment provides one, with an inline note that the original names
  a specific hook this share doesn't ship). The `## Architecture` (FSD) section
  and the GLSL parenthetical were removed from the body — their content now lives
  in `rules/`, matching the source's own move.
- **`interop-layer/`** — the `refs/` method-playbook folder and its compile step
  retired (moved to a local, gitignored `archive/interop-refs-2026-08-11/` for
  traceability, not published); `interop.py`, `portable-core.md`,
  `MIGRATION-MAP.md`, and `README.md` updated to the delegation model: preferences
  still transplant verbatim, method depth is now delegated to the target agent's
  own official docs via `delegation_block()`, and every build payload is
  leak-scanned before any write (new `scan` subcommand). Target registry updated:
  codex and Antigravity both now sync-off by user ruling; opencode is the sole
  live target, `light` profile, with new notes on its CLI verification and an
  inbound skill-loading dependency this repo does not control.
  *(Annotation added 2026-08-15, by exception; the sentence above is unchanged.
  `light` became `full`, and the two sync-off targets were later removed from
  the registry entirely — see the 2026-08-15 entries.)*
- **New root `archive/`** (gitignored, mirrors the `scientific-research-guide/archive/`
  convention already in this repo): holds the retired interop `refs/` playbooks,
  kept on disk for traceability, never published.

## 2026-08-07 — structural pass (this repo's own layout)

Prompted by a simple observation: agents reading this repo stop at the top level,
so the most informative material was the least likely to be read.

- **Root `Global_skill_update.md`** — moved up from `skill-toolkit/`. At 52 KB it is
  the single largest and most informative file here, and it logs the whole source
  environment (`ops/`, global `CLAUDE.md`, hooks), not just skills. Filename kept so
  the ~15 references to it across the other documents still read correctly.
- **`AGENTS.md`** — new flat, one-line-per-file map of the repo. The nesting under
  `skill-toolkit/skills/*/references/` is *correct* (a skill must keep its directory
  shape to stay installable), so the fix for "nobody reads that deep" is an index,
  not a reshuffle.
- **`README.md` / `CHANGELOG.md` split** — see above.
- **Domain knowledge removed from `scientific-research-guide/`** — the source
  environment's filled `domains/` profiles were its author's own research fields
  (~165 KB, 27% of the repo). Subject-matter knowledge, wrong for any other reader's
  field, and large enough to misrepresent what this repo is about. The machinery
  stayed: `_template.md`, the `_routing.md` manifest format, and
  `domain-expansion-guide.md`. `references/user-supplied-citations.md` was reduced to
  its storage rules, table shapes, and delegation contract; the citation inventory
  itself is gone. New `domains/README.md` states what was excluded and how to build
  your own first profile. Same rule applied to the sibling skill:
  `literature-search-extract` lost its worked sample run on the same research topic.
- **Personal working-state files removed** — `STATUS.md` / `FUTURE-WORK.md` from both
  research skills. They tracked the author's in-progress work on those skills and
  pointed at local archive paths; they were never useful to a reader of this share.
- **`scheduled_tasks.lock` untracked** — a runtime lock file carrying a session id and
  pid had been committed, while this README claimed runtime lock metadata was
  redacted. The claim is now true. `.gitignore` gained `*.lock` and `.claude/`.

### `claude-ops/` snapshot details

- Source: `~/.claude/ops/` (13 Markdown files, +1 since the last refresh), copied manually on 2026-07-11; refreshed 2026-07-31, 2026-08-02, 2026-08-06, 2026-08-07, 2026-08-12.
- Review scope: usernames, local paths, account or machine identifiers, and email-like strings.
- Result: one source username was removed (`ops/environment.md`); references between the operational documents were intentionally retained. 2026-08-02 refresh: `ops/40-maintenance.md` §3 trim-trigger line updated to match the source's raised global-`CLAUDE.md` cap (~12K → ~15K, with rationale) — the only file that had drifted since the prior refresh. 2026-08-06 refresh: premise-gate + refutability-statement rule-set synced across `05-authority.md`, `10-command-loop.md`, `30-judgment.md`, `60-bootstrap.md` (new §G Decision & Process Journal), `OPS.md`, `rules-usage-dict.md` (new §7 schema registry); new file `ops/60-record-templates.md` added (templates extracted from `60-bootstrap.md` in a same-day trim pass); `40-maintenance.md`'s ops-file size trigger raised ~10K→~12K; `lessons.md` gained L-009 (browser-pane screenshot timeout misdiagnosis). No personal identifiers found in the synced content. Full detail: `skill-toolkit/Global_skill_update.md`'s 2026-08-06 entry. 2026-08-07 refresh: `environment.md` restructured — per-block `as-of` dating replaces a single file-level verification date (which had already gone stale against a later fact recorded in the same file), the tier table is scoped explicitly to *subagent* dispatch, and the main-loop-model section became a read-it-don't-infer procedure (a config file's `model:` pin is a fallback marked "assumed", never proof of the running model — the prior wording made `05-authority.md` §2's automatic-L0 branch fire on a stale inference). Tier vocabulary corrected across `05-authority.md`, `30-judgment.md`, `60-bootstrap.md`: a *session* has no tier, the *main-loop model* it runs on does. `40-maintenance.md` gained an audit-trail entry schema (trigger / change before→after / result / rollback / open), registered in `rules-usage-dict.md` §7 and paid for by lossless trims to stay under the size cap. Same username removal as before in `environment.md`; no new identifiers. 2026-08-12 refresh: new subfolder `ops/references/` added (`inbound-routing.md`, `integrity-sweep.md`) — the size-cap landing zone for concrete examples/command blocks that `40-maintenance.md` §3 now points at instead of inlining them in the rule files; `rules-usage-dict.md` gained the pointer convention plus an inbound-routing row (grain-of-import routing: one skill → `skill-share-packaging` Mode B, a whole rules layer → `config-self-audit` adoption mode, plugin/marketplace content → detection-only) and its §7 schema table gained `rule-registry entry` / `change event` / `adoption stamp` / `reconciliation ledger` / `label family entry` / `list-generation entry` rows (the old single `audit-trail entry` row split into two — a rule-value change now updates `rule-registry.md` in place, a one-off event goes to the git commit message, neither is a `Global_skill_update.md` append). No personal identifiers in any of the new or changed content.
- This is a point-in-time snapshot, not a synchronization target. Folder-level documentation is maintained separately.

### `skill-toolkit/` snapshot details

- Source: `~/.claude/skill-trigger-dict.md`, `~/.claude/skills/`, and `~/.claude/Global_skill_update.md`, copied manually on 2026-07-11; refreshed 2026-07-31, 2026-08-02, 2026-08-12.
- Contents: a bilingual trigger dictionary, 13 skill directories with their referenced material and evaluations, plus the append-only global skill update log.
- Review scope: usernames, email-like strings, absolute local paths, internal project or package names, runtime lock metadata, and (2026-08-02) third-party license completeness for vendored content.
- Result: non-skill paths and identifiers were replaced with portable placeholders; the runtime lock metadata was redacted.
- Exception: historical paths in `Global_skill_update.md` that point directly to skill files were intentionally retained verbatim to preserve the update log's traceability.
- 2026-08-02 refresh: added `skills/motion-design/` (animation/3D design methodology hub) plus its `skill-trigger-dict.md` section and disambiguation rows. Its vendored `vendor/threejs/` reference package was **excluded** — the source environment's own update log had recorded that upstream's license defect (no `LICENSE` file, no named copyright holder) as blocking redistribution, and this share honours that ruling; only the properly-licensed `vendor/lottiefiles/` package was carried over, with the excluded package's SKILL.md/NOTICE.md pointing to its upstream URL instead. One hardcoded local path (`local/env-bridge.md`, pointing at a sibling `asset-vault` skill not included in this share) was also generalized. `skills/asset-vault/` was deliberately **not** imported this round (tied to a separate in-progress project).
- 2026-08-06 refresh: `skills/scientific-research-guide/` synced to the source's 2026-08-03 domain-expansion pass — two new base domain profiles (`gan_power_device.md`, `microled.md`), one new TI method sub-profile (`bi2se3_plasmonic_photoresponse.md`), a new source-provenance citation inbox (`references/user-supplied-citations.md`), and a swappable-slot convention for optional external tools (`domain-expansion-guide.md` §3.1) that also fixed a hardcoded personal path in `domains/plasmonic_waveguide.md`. Leftover draft material from a prior editing-copy round (`material/`, `MATERIAL-INTEGRATION-VERIFICATION-REPORT.md` — the latter naming local machine paths) was moved to `scientific-research-guide/archive/` and excluded from git via `.gitignore`, fully superseded by the integrated domain files. `skills/workflow-checkpoint/SKILL.md` also synced (journal-sweep step, resume-time premise re-confirmation). See `skill-toolkit/Global_skill_update.md` for the full entries.
- 2026-08-07 refresh: `Global_skill_update.md` only — one appended entry covering the same-day `claude-ops/` round, and the first entry written to the newly-registered audit-entry schema. No skill directories changed.
- 2026-08-12 refresh: `skills/config-self-audit/` gained its ADOPTION mode (AD1–AD5, a reconciliation-ledger output format, a §8 subagent-definition (`agents/*.md`) checklist, and a §9 renumber) plus two new files, `references/imported-config.md` (the mode's procedure and the `adopted-from:`/`reconciled:` stamp format) and `evals/evals.json` (routing evals against `skill-share-packaging` Mode B and `env-cleanup`). `skills/skill-share-packaging/SKILL.md` gained one disambiguation clause (Mode B is one skill; a whole rules layer routes to the new adoption mode instead). **`skills/motion-design/NOTICE.md` was deliberately NOT synced this round** — the source now documents `vendor/threejs/` as present with an accepted (not blocking) license-defect ruling, because the source machine kept a local-only copy of that vendor package after the 2026-08-02 exclusion above. This share still does not carry `vendor/threejs/`, so syncing the source's current NOTICE.md verbatim would describe content this repo doesn't have; the exclusion ruling and the pre-2026-08-12 NOTICE.md text stand until (if ever) `vendor/threejs/` itself is deliberately imported here under its own audit pass. See `skill-toolkit/Global_skill_update.md` for full entries where they exist.
- This is a point-in-time snapshot, not a synchronization target. Installation guidance and the complete skill inventory live in `skill-toolkit/README.md`.

### `environment-guide/` snapshot details (new 2026-07-31)

- Source: `~/.claude/PHILOSOPHY.md`, `~/.claude/OPERATOR-GUIDE.md`, `~/.claude/COMMIT-TEMPLATES.md`, copied manually on 2026-07-31; refreshed 2026-08-06.
- Review scope: usernames, local paths, account or machine identifiers.
- Result: two username occurrences in path examples were replaced with generic `<user>` placeholders. 2026-08-06 refresh: added beliefs 9 (stratified refutability) and 10 (know-why as asset, schema as transfer floor) to the philosophy section; synced the system-map's `CLAUDE.md` budget note (~12K → ~15K). No new personal identifiers introduced.
- This is a point-in-time snapshot, not a synchronization target. See `environment-guide/README.md`.

### `global-claude-md/` snapshot details (new 2026-08-02)

- Source: `~/.claude/CLAUDE.md`, copied manually on 2026-08-02 (captures the 2026-08-01 update that added the Windows/PowerShell environment rule and the Feature-Sliced Design architecture rule, and the 2026-08-02 fix that reconciled its `claude-ops/` cross-references with an ops rewording landed the same period); refreshed 2026-08-06.
- Review scope: usernames, local paths, account or machine identifiers, machine-bound environment facts.
- Result: the file carried no personal identifiers. Its "Environment" section pinned a specific OS/shell/line-ending combination (Windows 11, PowerShell 5.1, CRLF) and was replaced with `<OS_NAME>` / `<SHELL_NAME_AND_VERSION>` / `<LINE_ENDING_CONVENTION>` placeholders. Its `~/.claude/ops/*.md` and `~/.claude/skill-trigger-dict.md` cross-references were kept verbatim (deliberately **not** genericized — `~` is already portable and carries no username) with a mapping table added in `global-claude-md/README.md` pointing them at `claude-ops/ops/` and `skill-toolkit/skill-trigger-dict.md` in this same repo, since this share is meant to be used as a matched bundle with those two. 2026-08-06 refresh: the Environment rule reworded (default vs. secondary shell, explicit fence labeling — placeholders widened to `<DEFAULT_SHELL_NAME>` / `<SECONDARY_SHELL_NAME>`), Engineering-judgement gained a new bullet (screenshot-tool timeout on an occluded/hidden page is a display-state fault, not a permission one — generalized, no specific tool names, matching this file's existing portability convention), and the boundary-contract line synced to 5 sections/18 lines with a new premises&refutability bullet. 2026-08-07 refresh: the relaxation-gate bullet's skip condition now names the *main-loop model* (the model the session actually runs on, observed rather than read off a config pin) instead of "the main model"; applied as an in-place patch so this file's existing de-environment placeholders survive.
- This is a point-in-time snapshot, not a synchronization target. See `global-claude-md/README.md`.
