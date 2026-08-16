---
name: project-retrospective
description: >-
  Project-END lessons extraction — an experience guide plus a ready-to-paste
  CLAUDE.md rules snippet. Fires when a project or major milestone is FINISHED and
  nothing follows. Trigger on 「專案結束/收工/告一段落不再繼續」「這個專案學到什麼」
  「踩了什麼坑」「幫我寫 CLAUDE.md 規則」"retrospective", "summarize this project",
  "wrap up what we learned". Decide by 「後面還有沒有事」, NOT by how final the
  wording sounds: work CONTINUES → workflow-checkpoint; work ENDS → here. If a
  project merely SEEMS to be wrapping up, ask once — never scan unprompted. Do NOT
  fire mid-phase, on one delivered document, or to summarise a single conversation.
  Full disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Project Retrospective Skill

Extract reusable knowledge from a finished project. Output a human-readable experience guide and a Claude-readable CLAUDE.md instruction snippet.

## When to Trigger (natural hooks)

The description block governs firing (project ENDS, nothing follows). Two
natural hooks worth OFFERING at — ask once, never run unprompted: the
project's `~/.claude/references/PROJECTS.md` row is about to flip to
`done`/`archived` (offer BEFORE flipping; Step 6.3 updates that row anyway),
or a second project of the same KIND is about to start (Category 7, the clean
path, is at its most valuable right before reuse). Do NOT fire at phase
ends — that is `workflow-checkpoint`'s job.

## Overall Flow

```
1. Read durable records, then scan conversation → 2. Classify & extract →
2.4 Rule sibling scan (probes come from Step 2's output) →
2.5 Triage any LIVE defect the scans surfaced → 3. Reconcile the open list →
4. Draft + ONE consolidated check-in → 5. Output documents →
6. Write project-level rules (unless project CLAUDE.md IS global) → global
merge (only with the explicit yes from step 4) → close-out → mechanical
self-check → log
```

Before starting, read `references/extraction-taxonomy.md` (classification) and
`references/step1-source-reading.md` (Step 1's full source protocol).

## Step 1: Read the durable records FIRST, then scan the conversation

The conversation is the *supplement*, not the primary source — it may have been
compacted, and in a long project most of it is gone. Follow the FULL ordered
protocol in `references/step1-source-reading.md`: 9 sources cheapest-first
(phase-log → decisions journal → glossary → detail files → lessons grep → git
history → conversation scan → sibling scan for code → sibling scan for RULES,
which is planned here but RUNS as Step 2.4), the two-homes rule for in-repo
records, the one-glob check before ever declaring "no durable records", and
the compaction disclosure duty for the coverage header.

## Step 2: Classify & Extract

Map each flagged item to one of the seven categories in
`references/extraction-taxonomy.md` (authoritative definitions + signals +
output formats there): 1 Technical Decisions · 2 Pitfalls & Bugs (each with
cost, times hit, and status) · 3 Effective Workflows · 4 Project Constraints &
Context · 5 User Preferences · 6 Reusable Principles · 7 The Clean Path (only
when the project is an instance of a repeatable kind).

## Step 2.4: Rule sibling scan — after extraction, because it eats Step 2's output

For each MECHANISM in the Category-2/6 extraction, build one probe and grep the
other retrospectives' Document 2, every `global-rule-candidates-*.md` in the
output directory, and `~/.claude/ops/lessons.md` — match the MECHANISM, not the
wording; the second occurrence rarely shares vocabulary with the first. Probes
must span the languages actually in use: sibling documents may be in the user's
language while this project's records are in English, so a single-language
probe silently returns nothing and reads as "no cross-project evidence".

Two independent occurrences is the strongest input Step 6.2's gates take, and
the one thing neither gate can produce by reasoning. Bring forward any
PREVIOUSLY REJECTED candidate whose evidence this project strengthened — the
rejected-candidate history lives in `global-rule-candidates-*.md`, NOT in
Document 2, which by definition carries only adopted or proposed rules — and
any candidate whose SCOPE this project's evidence widened: a rule that was
right but too narrow is a rewrite, not a new rule.

## Step 2.5: If the extraction surfaced a LIVE defect, it is not a document item

A retrospective looks at code and records with fresh eyes and a question nobody
asks during the work ("was this written twice?"). That combination finds live
bugs, and a live bug written into an experience guide is a bug with better
prose. Decide explicitly, and say which you chose in the Step 4 check-in:

- Small, verified, and inside this project's scope → FIX IT NOW, with a test,
  in its own commit, and record it as a Category-2 pitfall with
  `Status: fixed during the retrospective`. The fix must not alter behaviour
  the user already accepted beyond removing the defect itself.
- Larger, out of scope, or touching accepted UX/interaction semantics → raise
  it as a task/ticket and reference it from Document 1, never as prose alone.

The distinguishing question is not size but exposure: is anything relying on
this right now?

## Step 3: Reconcile the open list before writing it

Take the `open:` line from `-decisions.md` `## Now` and the `## Open Questions`
of every phase-log section. For each item, mark it **still open / closed this
phase / closed and nobody updated the record / SUPERSEDED — the record now
states something that is no longer true**. The third bucket is a finding in its
own right — report it to the user and fix the source record (mark it closed),
not just the retrospective. The fourth bucket is fixed DIFFERENTLY: amend the
record in place with the supersession visible (what it used to say, what
replaced it, and what the old version cost), because a record that was correct
when written and is wrong now is the most instructive shape in the whole
journal, and overwriting it destroys exactly that. Also sweep the glossary
(`-context.md`) and any decision entries the project touched — a superseded
claim rarely sits in the open list, which is why the open-list buckets alone
miss it. Document 1's 「未解決的問題」 is the reconciled list, and any item
closed during the project's final stretch is listed separately under 「已關閉」,
with what closed it.

If no durable records exist, reconcile against the conversation's own loose ends
instead — never copy an open list from anywhere without checking it.

## Step 4: Draft, then ONE consolidated check-in

Draft everything BEFORE asking: Document 1, Document 2, the global-merge
candidate table (Step 6.2's four gates), and the README status check (Step 6.3).
Then ask the user **once**, covering every ruling in a single message — use the
check-in template in `references/output-templates.md` §"Step 4 check-in
template" (extracted items summary; the two probe questions; the global-merge
candidate table where **each rule needs an explicit yes — silence means no**;
the README question only if stale/missing). Only include a question when different answers lead to materially different work.
Do NOT ask who the audience is — the skill always produces both documents.
Incorporate the answers, then move to output.

## Step 5: Output Documents

Default output directory: `~/.claude/outputs/retrospectives/` (create if
missing). Retrospective documents live at the USER level, not inside the project
— their value crosses projects; the project-level artifact is the project
CLAUDE.md written in Step 6. Before writing, check whether the output directory
is version-controlled (`git check-ignore -v <path>`): if it is ignored, say so
in the check-in and ask — a retrospective with no history is a record that can
vanish without a trace, which is the opposite of what it is for. If a
retrospective for this project/milestone already exists at the SAME path, do
NOT overwrite and do NOT invent a new date: append a clearly-marked second-pass
section, and say what the second pass covers that the first did not (a
version-controlled output directory makes the revision diffable, which is
another reason the check above matters). If the project has ANY earlier
Document 1/2 under a DIFFERENT name (an earlier milestone, an old project
name), the new document's header must state `Supersedes <old file>`, naming
any rule of the old file this round REWROTE (not merely added to) — otherwise
a future Step 2.4 reads both versions side by side with no way to tell which
is current. Use the
templates from `references/output-templates.md`; both documents' AUTHORITATIVE
format specs also live there (§"Document 1 format" / §"Document 2 format"):

### Document 1: `retrospective-[project-name]-[date].md`
Human-readable experience guide, user's preferred language (default:
Traditional Chinese). **MUST open with a coverage header**: sources fed /
stretches unrecoverable / **what this retrospective CHANGED** (observed vs
caused) — full spec in the reference.

### Document 2: `claude-instructions-[project-name].md`
Compact CLAUDE.md-ready snippet. **MANDATORY format (full spec in the
reference, do not deviate)**: conditional triggers only ("When X, do Y" —
glossary entries exempt); concrete files/APIs/symbols; ~25-rule cap ordered by
trigger frequency (cut from the bottom, cut material stays in Document 1);
every rule tagged BOTH `[from: category]` AND `[dest: project | global |
lessons]` — two destinations only when the project has no rules layer.

## Step 6: Merge into CLAUDE.md + close out (MANDATORY)

After producing the documents, do ALL of the following in order (do not skip — this is the deliverable, not optional):

1. **Write the project-level rules first — unless the project CLAUDE.md IS the
   global one.** Resolve the project's CLAUDE.md path and compare it to
   `~/.claude/CLAUDE.md`. If they are the same file (a dotfiles or agent-config
   repository, where the project root and the configuration root coincide),
   STOP: this step's no-consent write would silently execute Step 6.2's gated
   write, and "zero-behaviour-change" is FALSE for the global rules file. In
   that case skip this step's CLAUDE.md write entirely, route every rule
   through Step 6.2's four gates and Step 4's explicit yes, and say so in the
   check-in; the `[dest: project]` rules then go to whatever rules layer the
   repo actually has (`ops/`, `rules/`), never the global file. Otherwise:
   merge Document 2's `[dest: project]` rules into the repo's rules layer if it
   has one — into the layer file whose scope already matches, else a new
   `<layer>/from-retrospective.md` — and REGISTER that file wherever the layer
   is loaded from (a CLAUDE.md index line, the layer's router file): a rules
   file nothing loads is a mechanism degraded to prose. Else merge into the
   project root `CLAUDE.md` (create it if absent; preserve existing content —
   append/merge, never overwrite; keep conditional-trigger phrasing intact).
   Before writing, scan the project root for OTHER agent-instruction files
   (`AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`,
   `.windsurfrules`): if one exists and duplicates the target file, deal with
   it — turn it into a pointer, or update it in the same pass — and say in the
   check-in which you did. Two instruction files kept in sync by hand are a
   control that rots silently, and updating only one of them is how this very
   step would CREATE the divergence. The target file holds all
   project-specific rules (file names, endpoints, this project's terms). Add
   at its top a one-line pointer to the retrospective documents' paths. Tell
   the user the exact path. **If the project is a git repo, commit the touched
   files** — a zero-behaviour-change documentation write (default branch is
   fine); do not leave a dirty working tree.

2. **Global merge — four gates, and only with Step 4's explicit yes.** A rule
   reaching global `~/.claude/CLAUDE.md` must pass ALL four:
   - (a) **Generalizable — and checked, not estimated.** Judge this on Step
     2.4's rule-sibling-scan results, never on reasoning alone. A rule that two
     projects arrived at independently is evidence-backed; a rule seen once is
     a hypothesis. Record which it is in the candidate table's "why" column.
   - (b) **Not already covered** — read the current `~/.claude/CLAUDE.md` AND the
     skill descriptions before proposing. A rule that duplicates an
     always-triggering skill is charged twice; the fix is that skill's trigger,
     not a new global line.
   - (c) **Not better merged** — if it is the *how* of an existing rule, propose
     it as an amendment to that rule, not a new one. Two rules competing for one
     situation is worse than one rule that is slightly longer.
   - (d) **Worth its rent** — global is charged to every session. Rank by
     observed occurrences across projects, not by how important it feels. A
     sharp rule that fires twice a year belongs in `~/.claude/ops/lessons.md`,
     not global. A rule whose occurrence count went UP because of this
     project's evidence should be re-proposed even if a previous retrospective
     rejected it — say so explicitly, with the old verdict and what changed.
     The rejected-candidate history lives in `global-rule-candidates-*.md`,
     not in Document 2.
   Present candidates as the Step-4 table (rule | verdict: adopt / merge into X /
   reject | why), recommend a MINIMAL set, and say how many lines it adds.
   Execute ONLY the rules that received an explicit yes in Step 4's check-in —
   NEVER write global without it; no answer means no global write. Match the
   existing conditional-section style (append/merge, never overwrite).
   **Persist the full candidate table** — including every rejection and its
   why — as `global-rule-candidates-[project-name]-[date].md` in the output
   directory. The file's header MUST state the batch's execution status
   (executed / rejected / judged-but-deferred / not yet ruled) with the user's
   ruling verbatim, and its tail MUST carry a section "Input for the next
   Step 2.4" saying, per candidate, what new evidence would re-open it. A
   candidate with no status is invisible to the next round — it cannot tell
   "judged and rejected" from "judged and parked" from "never ruled", and
   those three answer "re-propose?" differently. That file IS the
   rejected-candidate history a future Step 2.4 scans; if it is not written,
   the next project has no record that a candidate was ever judged.

3. **Close-out visibility gate.** Two checks:
   - Update the project's row in `~/.claude/references/PROJECTS.md` (status →
     `done`/`archived`/`maintenance`, next → resume pointer or "-"). Register the
     row if missing. **The row MUST carry the retrospective documents' paths** —
     PROJECTS.md is the browsable index; the Step-6.5 log entry is archaeology,
     not an index.
   - **Phase-log consistency**: if `references/<project>-phase-log.md` exists
     and its LAST section's `Status:` still reads in-progress while you have
     just marked the PROJECTS.md row closed, the two records now contradict
     each other — and the phase log is the one a resuming session reads FIRST.
     Append a closing checkpoint section (or, if the phase genuinely
     continues, do not close the PROJECTS.md row). Say in the check-in which
     of the two you did.
   - README per Step 4's ruling: if the user said yes, generate/refresh it from
     the retrospective content; never write it unprompted.

4. **Mechanical self-check (after all writes, before declaring done).** Verify:
   - Both documents exist and are non-empty at the paths reported.
   - The project CLAUDE.md exists AND its pre-existing content is still present
     (the merge did not overwrite).
   - Every file path mentioned in the two documents resolves.
   - The PROJECTS.md row actually changed and carries the document paths.
   - If Step 6.2 judged any candidates,
     `global-rule-candidates-[project-name]-[date].md` exists, records every
     rejection (not only the adopted set), and carries the batch's execution
     status in its header.
   Report any failure and fix it instead of declaring done.

5. **Record it where that kind of fact lives.** NOT `audit-archive/` — frozen 2026-08-11, it takes no new entries and must not be recreated. Route by fact type: the event (which files changed, how to undo) → the git commit message; a global CLAUDE.md rule that changed its standing value → replace that rule's entry in `~/.claude/ops/rule-registry.md`, compressing the old value into `history:`; a pitfall actually hit during the project → `~/.claude/ops/lessons.md` as a new `L-nnn`. Cover BOTH the project-CLAUDE.md write and (if it happened) the global merge; use the record-entry shape in `references/output-templates.md` §"Step 6.5 record-entry shape". Always convert relative dates to an absolute timestamp. Append, never overwrite.

## Output Principles

Six principles govern every output document — specific over abstract ·
conditional not blanket · rules with context (a "why" per rule) · layered
(project-only vs universal) · actionable · honest about coverage (state what
cannot be known). Full statements: `references/output-templates.md` §"Output
principles".

## Notes

- For long conversations, do a keyword scan first (errors, decisions, preferences) before reading fully
- Don't stuff in everything — only extract turning points, corrections, and explicit choices
- If the project has no clear name, ask the user or default to "this-project"
- (Document 2's format mandate and Step 6's non-optional close-out are stated in full at Steps 5–6; not repeated here.)
