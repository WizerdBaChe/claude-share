# Step 1 detail — the durable-record reading protocol

Extracted VERBATIM from SKILL.md Step 1 on 2026-08-16 (BODY_CAP trim; content
unchanged — this file is the full protocol, SKILL.md Step 1 keeps the rule and
points here).

Read in this order, cheapest first, **skipping any file that does not exist**:

1. `~/.claude/references/<project>-phase-log.md` — the phase index. This is what
   `workflow-checkpoint` writes so a later session need not replay history.
2. `~/.claude/references/<project>-decisions.md` — the D-/P- journal (decisions
   with rejected options; process pitfalls) plus the `## Now` block. Every D-
   entry is a Category-1 item already written; every P- entry is a Category-2
   item already written. Do not re-derive them from the conversation — carry them
   across and expand.
3. `~/.claude/references/<project>-context.md` — the domain glossary
   `workflow-checkpoint` maintains; feeds Category-4 term definitions directly.
4. Any `- Detail:` files the phase-log links to.
5. `~/.claude/ops/lessons.md` — grep the project name/keywords; any matching
   pitfall cards are retrospective input (and mark them folded-in afterward per
   `ops/40-maintenance.md` §2).
6. Git history — if the project (and/or `~/.claude`) is a git repo,
   `git log --oneline --since=<project start>`; commit subjects are a timeline of
   decisions and fixes worth cross-checking.
7. THEN scan the conversation for what none of the above captured: corrections,
   preferences, the reasoning behind a reversal — flag per the signal lists in
   `references/extraction-taxonomy.md` §"Conversation scan signals".
8. **Sibling scan (cheap, high value).** Ask "was any of this written twice?" —
   check the workspace roots already registered in
   `~/.claude/references/PROJECTS.md` (never scan the whole disk), then grep
   sibling projects for the distinctive API/symbol. A thing implemented
   independently in two projects is evidence-backed reuse; a thing implemented
   once is speculation. Record the verdict either way — "only one consumer" is a
   finding that PREVENTS a premature abstraction.
9. **Sibling scan for RULES** — planned here alongside item 8, but it RUNS
   later, as Step 2.4: its probes are the mechanism list that Step 2 produces,
   so it cannot execute during Step 1.

Items 1–4 have TWO possible homes: `~/.claude/references/` (workflow-checkpoint's
default) and inside the repo itself (`<project-root>/references/`, then
`<project-root>/docs/`) — check both, and remember the record slug may not
equal the directory name (a repo named `3D_Photo_Synthesis_Engine` kept its
records as `3D-photo-engine-*.md`). If they are in neither home, run one
`**/*.md` glob over the project root (excluding `node_modules`, `.venv`,
`archive`) BEFORE declaring "no durable records" — that declaration goes into
the coverage header, and a wrong one makes the whole retrospective lie
precisely on the projects whose records were best kept (records living in-repo
usually means someone maintained them carefully). Only after that glob comes
back empty, fall back to conversation + git history and say so in the coverage
header. **If the conversation has been compacted**, say so in the coverage
header and treat 1–4 as authoritative for everything before the current window.
