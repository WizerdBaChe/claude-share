---
name: env-cleanup
description: >-
  File-level environment cleanup ("環境自清潔"). Mode A: the ~/.claude environment (whitelist
  manifest); Mode B: a project working tree (heuristics + reference checks). Trigger on
  "清理環境", "掃描無關檔案", "clean up my .claude", "find files that no longer belong". Writes a
  candidate report, ALWAYS asks per category, then ARCHIVES — never deletes, never edits
  file content. NOT for auditing one artifact's content (→ config-self-audit). Full
  disambiguation: ~/.claude/skill-trigger-dict.md.
---

# Environment Cleanup (env-cleanup)

Shared engine + per-mode data. The engine below is identical for both modes;
everything mode-specific lives in `references/` and is loaded on demand:

- Mode A (`~/.claude` self-clean): `references/manifest-claude.md`
- Mode B (project tree): `references/project-heuristics.md`

Mode selection: explicit user request wins; otherwise cwd inside `~/.claude`
→ Mode A, any other project → Mode B. Never run both in one pass.

## Hard invariants (apply to every run)

1. **Archive, never delete.** Candidates move to an archive dir (per mode, see
   references). Deletion only if the user explicitly chooses it per item/category
   during the ask step (e.g. regenerable caches).
2. **Report is a new file, never overwritten.** The report doubles as the
   archive note: `<archive-batch-dir>/CLEANUP-REPORT.md`, Traditional Chinese.
   If the day's batch dir already exists (second run same day), suffix `-2`,
   `-3`, … — never write into an already-populated batch dir.
3. **No content edits** (sole exception: Mode B may add `archive/` to the
   project `.gitignore`, with consent). If a finding requires editing a file
   (orphan hook entry
   in settings.json, oversized ops file, stale rule text), REPORT it and route:
   settings/hooks changes → update-config skill (🔴 tier, user confirms);
   rule-content trimming → ops/40-maintenance.md §3; unused-rule investigation
   → ops/40-maintenance.md §4.
4. **Tier respect (ops/40-maintenance.md §1).** A candidate that is itself a
   🔴/🟡-tier file (CLAUDE.md, settings, hooks/, ops/, skills/, trigger dict)
   is never moved without an explicit per-item user confirmation, and the move
   is logged in `~/.claude/Global_skill_update.md`.
5. **Main session executes.** Subagents may scan and draft the candidate list;
   only the main session performs moves (⛔ rule, 40-maintenance §1).
6. **Age threshold: 14 days** (last-modified) for all age-based candidacy,
   unless the user sets another value for the run.
7. **Consent granularity: per category**, with the full item list visible in
   the report first. Options per category: archive / keep / skip; "delete" only
   when the user says so unprompted or the category is marked regenerable.
8. **Live-environment guard (Mode A).** Other sessions may run concurrently;
   before moving runtime-adjacent categories (`file-history/`,
   `shell-snapshots/`, session state), check for files touched within the
   last hour — if found, defer THOSE items to a later run and say so.

## Engine (both modes)

1. **Scan** the target scope (respect per-mode exclusions in references).
2. **Classify** each item: `KNOWN-KEEP` / `CANDIDATE (reason)` / `UNKNOWN
   ORIGIN`. Mode A classifies against the whitelist manifest; Mode B applies
   heuristics then MUST run the reference check (grep for imports/mentions)
   before promoting any code-like file to CANDIDATE — any hit demotes to KEEP.
3. **Report**: write `CLEANUP-REPORT.md` in the (not yet populated) archive
   batch dir. Per item: path, size, mtime, classification reason, proposed
   action. Also list what was skipped as protected, and any route-out findings
   (invariant 3). End with: per-category totals; the archive root's current
   total size (retention visibility — archive/ grows forever otherwise); and
   an informational list of size outliers (>50 MB regardless of age —
   report-only, never auto-candidates).
4. **Ask** the user per category (invariant 7). No response = no action.
   Mode A: an UNKNOWN ORIGIN item the user rules KEEP is manifest drift —
   offer to add it to the manifest in the same run (🟡 edit: backup +
   audit-log entry).
5. **Execute + record**: Mode A precondition — `git status --porcelain` must
   show no unrelated STAGED changes; if it does, ask before proceeding. Move
   approved items into the batch dir preserving relative paths; remove
   now-emptied source directories and note them. If any single move fails
   (locked file, permission), STOP the batch and record exactly what moved
   vs. didn't — never leave partial state undocumented. Append to the report:
   the executed decisions + a per-category RESTORE command. Mode A only:
   stage ONLY the paths this run touched (explicit `git add <paths>` — NEVER
   `git add -A`; it sweeps unrelated work into the commit, confirmed misfire
   2026-07-07) and commit (`chore(env): ...`). Mode B: ensure `archive/` is
   gitignored; never commit project changes without the user's git flow.

Last-run time = mtime of the newest `CLEANUP-REPORT.md` under the mode's
archive root; no separate stamp file. If asked "when was the last cleanup",
check that, not `~/.claude/.last-cleanup` (that file is Claude Code CLI's own
transcript-cleanup stamp, unrelated to this skill).

## Boundaries (do not re-implement; route)

| Overlap risk | Resolution |
|---|---|
| config-self-audit | That skill audits content of ONE named artifact; this skill audits existence/staleness of MANY files and never reads deeply. A finding like "this hook file is unsafe" → route there. |
| ops/40-maintenance.md §3 trim | Oversized rule files are reported as route-outs, never trimmed here. |
| ops/40-maintenance.md §4 ghost checks | Mode A's orphan detection (see manifest §4) is the file-existence half of §4; content-level "rule exists but is never used" stays with §4 at retrospectives. |
| Claude Code built-in transcript cleanup | `projects/` is protected; this skill never duplicates the CLI's transcript pruning. |
| workflow-checkpoint / project-retrospective | Those archive knowledge (phase logs, lessons); this skill archives files. A finished project wanting lessons → retrospective, not cleanup. |
| engineering:tech-debt / deep-checklist | Never judge code quality here; "ugly but referenced" = KEEP. |
