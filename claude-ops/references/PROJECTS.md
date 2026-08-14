# Projects Index

<!--
TEMPLATE. The source environment's live copy of this file is the operator's own
project inventory — real names, real paths, real status. Only the FORMAT ships.
Copy this to ~/.claude/references/PROJECTS.md and add your own rows.

Registry of all known projects — one table row per project. Machine-parseable;
a dashboard tool can read this table as its project list.

Maintainers (who updates this file):
- workflow-checkpoint skill: refresh the project's row at every phase checkpoint.
- project-retrospective skill: set status to done/archived at project end.
- ops/60-bootstrap.md §A: register a new project's row on first session.

Column semantics:
- project: slug used in references/<project>-*.md filenames (must match exactly).
- status: design | active | blocked | maintenance | done | archived  (+ free-text note)
- path: project root on disk ("-" if none yet).
- last-checkpoint: date + phase of the newest phase-log section ("-" if no log).
- next: one-line pointer to the next action or open gate.
-->

| project | status | path | last-checkpoint | next |
|---|---|---|---|---|
| example-project | active (ops-relaxation: L1) | `<project-root>` | 2026-01-01 (Phase 2 — parser rewrite) | Acceptance gate G3 is the user's to run; then wire the export path. Entry chain: `references/<project>-phase-log.md` → `-decisions.md` `## Now` → `-tickets.md` |

<!--
Two conventions the example row is carrying, both load-bearing:

1. The `status` cell records the project's ops-relaxation level, so the gate in
   ops/05-authority.md §2 is answered once per project rather than per session.
2. The `next` cell ends with an ENTRY CHAIN — the ordered list of files a cold
   session reads to rebuild state. Without it, "next" tells a returning session
   what to do but not where to look, and it re-derives the project from scratch.

Keep rows to one line each. This file is read in full; it is an index, and an
index that needs its own index has failed.
-->
