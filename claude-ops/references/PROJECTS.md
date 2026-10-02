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
- A new row's activity-map row in references/USER-PROFILE.md comes FIRST:
  hooks/registry_row_guard.py denies a Write/Edit that adds an unclassified
  project name (L-121; the SessionStart profile hook reads both files live).

Column semantics:
- project: slug used in references/<project>-*.md filenames (must match exactly).
- status: design | active | blocked | maintenance | done | archived  (+ free-text note)
- path: project root on disk ("-" if none yet).
- last-checkpoint: date + phase of the newest phase-log section ("-" if no log).
- next: one-line pointer to the next action or open gate.
- predecessor: slug(s) of the project(s) this one continues or was extracted
  from, comma-separated; "-" if none. A named predecessor's deliverables,
  conventions and review records are MANDATORY INPUTS to this project's
  deliverables — the series-continuation rule across a project boundary
  (ops/lessons.md L-039: twice a new root continuing a frozen predecessor did
  not read as "deliverable N of a series"). Set it when the row is born; the
  gist prints it beside the status. Never put a `|` inside any cell.
-->

| project | status | path | last-checkpoint | next | predecessor |
|---|---|---|---|---|---|
| example-project | active (ops-relaxation: L1) | `<project-root>` | 2026-01-01 (Phase 2 — parser rewrite) | Acceptance gate G3 is the user's to run; then wire the export path. Entry chain: `references/<project>-phase-log.md` → `-decisions.md` `## Now` → `-tickets.md` | - |

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
