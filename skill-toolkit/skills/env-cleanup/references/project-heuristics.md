# Mode B heuristics — project working tree

Classification data for env-cleanup Mode B. Projects cannot be whitelisted
centrally, so candidacy comes from heuristics + a mandatory reference check,
optionally overlaid by a per-project keep-list. Age threshold: 14 days unless
overridden.

Archive batch dir: `<project-root>/archive/<YYYY-MM-DD>-cleanup/`. Before
executing, ensure `archive/` matches a `.gitignore` pattern (add it with user
consent if absent — this is the one content edit Mode B may make, and only to
`.gitignore`).

## §1 Always excluded from scanning

- Anything matched by `.gitignore` that is build/dependency machinery:
  `node_modules/`, `dist/`, `build/`, `.venv/`, `__pycache__/`, `target/`,
  `.next/`, `coverage/` — the build system owns these; not our debris.
- `.git/`, existing `archive/`, `.claude/` project config.
- Git submodules (`git submodule status` paths) — separate repos; never
  scanned from the parent.
- Anything listed in the project keep-list (§4).

## §2 Heuristic signals → CANDIDATE (with the signal as the reason)

1. **Untracked strays**: files not tracked by git AND not matching any
   `.gitignore` pattern AND older than threshold — the classic
   externally-dropped file. (`git status --porcelain` + `git check-ignore`.)
2. **Editor/OS litter**: `*.tmp`, `*.swp`, `*.swo`, `~$*`, `*.bak`,
   `.DS_Store`, `Thumbs.db`, `*.orig`, `*.rej` — no age requirement.
3. **Duplicate-name debris**: `* (1).*`, `*copy*of*`, `*_old.*`, `*_backup.*`,
   `*-舊.*`, `*副本*` — case-insensitive, age requirement applies.
4. **Stale root one-offs**: root-level reports/screenshots/scratch scripts
   (`*.png`, `*.log`, `test_*.py`-style throwaways, `*-report.md`) older than
   threshold. Root only — deeper paths are presumed organized.

## §3 Reference check (mandatory before promotion)

For every candidate whose extension is code/config/doc (not §2 litter):
grep the project (tracked files only) for the filename stem — import, require,
include, href, path string, Makefile/CI mention. ANY hit → demote to KEEP with
the hit location noted in the report. This check is what keeps heuristics from
flagging fixtures, assets, and data files that code loads at runtime.
Runtime-glob caveat: if code references the candidate's PARENT directory
(glob/scandir/readdir of `fixtures/`, `assets/`, `migrations/`, …), every file
inside is effectively referenced → KEEP the directory's contents wholesale.

Quality is NOT a signal: ugly, unused-looking but referenced code is KEEP
(tech-debt is engineering:tech-debt's job, not cleanup's).

## §4 Optional per-project keep-list

`<project-root>/.claude/cleanup-keep.md` — plain list of globs/paths the
project declares as "looks like debris, is not" (fixtures, design assets,
legal docs). If present, apply after heuristics; keep-list always wins.
Absent = pure heuristics. Suggest creating one when the user marks ≥3 items
KEEP at the ask step.

## §5 Git etiquette

- Never `git rm`, never commit, never touch branches — file moves land in the
  working tree; the user's own git flow (per global CLAUDE.md) handles them.
- If the project is not a git repo at all, say so in the report and apply
  heuristics §2/§4 only (no untracked-stray signal without git), extra
  conservative: everything needs per-item confirmation.
