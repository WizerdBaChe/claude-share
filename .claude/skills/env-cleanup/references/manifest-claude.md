# Mode A manifest — expected structure of ~/.claude

Classification data for env-cleanup Mode A. Update this file (🟡 tier: backup +
config-self-audit + audit-log entry) when the environment gains/loses a
permanent directory or root file. Age threshold: 14 days unless overridden —
strictly older than the cutoff timestamp; boundary cases (mtime equal to the
cutoff day) = KEEP. Note: mtime is the only staleness signal, and mass-touch
events (checkout/restore) reset it — this errs toward KEEP, which is the safe
direction; do not compensate by guessing.

Archive batch dir: `~/.claude/archive/<YYYY-MM-DD>-env-cleanup/`
(`archive/` is gitignored; the CLEANUP-REPORT.md inside is the note file).

## §1 PROTECTED — never candidates, never listed item-by-item

Report one line "skipped as protected" per entry. Rationale in parentheses.

- `.credentials.json`, `.oauth_refresh.lock`, `.env*`, any `*credentials*` (secrets)
- `settings.json`, `settings.local.json`, `CLAUDE.md`, `.gitignore` (🔴 tier)
- `hooks/` (🔴 tier — broken mounts are route-outs; unregistered dead scripts
  MAY move, but only via §4 orphan detection with per-item confirmation)
- `plugins/`, `ide/`, `mcp-needs-auth-cache.json`, `.last-cleanup` (machine-managed)
- `projects/` (session transcripts + harness MEMORY — CLI manages its own pruning)
- `sessions/`, `session-env/`, `tasks/`, `data/` (live runtime state)
- `.git/` (history IS the safety net)

## §2 AGE-BASED CANDIDATES — regenerable or superseded machine output

Items older than the threshold become CANDIDATE. All are gitignored runtime
data; `regenerable: yes` means the user may reasonably pick "delete" at the
ask step (default action is still archive).

| Path | Candidate rule | Regenerable |
|---|---|---|
| `shell-snapshots/` | files > threshold | yes |
| `debug/` | files > threshold | yes |
| `cache/` | entries > threshold | yes |
| `file-history/` | entries > threshold (breaks file-restore for those old sessions — say so in the report) | yes |
| `telemetry/` | files > threshold | **no — snapshot series**: past states cannot be regenerated, and trend readers (`skill-routing-audit.py --snapshot`, T-020) consume the history. Archive only, and say the trend breaks |
| `downloads/` | files > threshold | no — user content, archive only |
| `backups/<date>/` | date-dir > threshold AND every file in it has a newer backup or is unchanged vs git HEAD | no — archive only |

## §3 CURATED — judged item-by-item, conservative

Working documents; only clearly-superseded items become candidates, each with
an explicit reason. When in doubt → KEEP.

- `drafts/`, `plans/`: > threshold AND the work is verifiably landed
  (referenced by a audit-archive/ entry or a git commit) → CANDIDATE.
- `agents/`, `skills/`, `ops/`: 🟡 tier — a folder here is CANDIDATE only via
  orphan detection (§4), and moving it requires per-item confirmation
  (SKILL.md invariant 4). Never age-based.
- `reports/`: user audit-trail documents (system-change remediation reports,
  new file per report) — KNOWN-KEEP, never age-based. Added 2026-07-07.
- `outputs/`: KNOWN-KEEP as of 2026-08-16 — `outputs/retrospectives/` and
  `outputs/skill-reviews/` are a CONSULTED CORPUS (project-retrospective
  Step 2.4 greps them for cross-project rule evidence) and are git-tracked;
  moving them into gitignored `archive/` severs both. Standing rule: when a
  skill starts CONSUMING a directory, the change that adds the consumer must
  also update this manifest — a consumer the manifest doesn't know about
  turns cleanup into corpus destruction.
  `outputs/experiments/` added same day: EVIDENCE CORPUS — each dir is the
  printable evidence behind a published comparison/premise (cited by D-entries
  and ops rules), so age-based candidacy never applies; the only retirement
  path is a newer artifact declaring `Supersedes`. Advisory outputs carry a
  greppable status line (`rules-usage-dict.md` §7 "advisory-output status
  line"): an OPEN one is never a cleanup candidate, and a SPENT one is still
  KEEP for the evidence reason above.
- `archive/` itself: never rescanned.

## §4 ROOT WHITELIST + ORPHAN DETECTION

Known root files: `CLAUDE.md`, `settings.json`, `settings.local.json`,
`.gitignore`, `.credentials.json`, `.oauth_refresh.lock`, `.last-cleanup`,
`mcp-needs-auth-cache.json`, `audit-archive/`, `skill-trigger-dict.md`,
`keybindings.json`, `history.jsonl`, `AGENTS.md` (interop profile),
`COMMIT-TEMPLATES.md`, `LABEL-REGISTRY.md`, `OPERATOR-GUIDE.md`,
`PHILOSOPHY.md` (all five confirmed live 2026-08-16). Any other root-level
file → UNKNOWN ORIGIN.

Known root DIRECTORIES (added 2026-08-16 — before this list, whole trees were
invisible to classification; a 726 MB `memory-archive/` went unclassified):
every §1/§2/§3 directory above, plus `agents/`, `ops/`, `skills/`, `rules/`,
`references/`, `reports/`, `tools/` (project workspaces incl. their
node_modules — size outliers are report-only), `interop/`, `thinking-notes/`,
`memory-archive/` (memory-pipeline project assets: model caches + raw
transcripts; report-only outliers), `audit-archive/` (frozen), and the nested
`.claude/` (harness worktree bookkeeping + scheduler lock — machine-managed,
protect like §1). Any other root-level DIRECTORY → UNKNOWN ORIGIN, same
handling as unknown files.

Orphan checks (bidirectional; every finding is a REPORT line — route-outs or
confirmed-per-item moves, never silent):

1. Hook commands in `settings.json` ↔ files under `hooks/`
   (missing file = broken hook → route to update-config;
   unregistered SCRIPT (`.py`/`.ps1`/`.cmd`/`.js`) = dead script → CANDIDATE,
   per-item confirm. Non-script files (`.json`, `.txt`) are hook DATA, not
   orphans: grep the hook scripts for the filename — referenced = KEEP,
   unreferenced = CANDIDATE. Measured false positive 2026-08-16:
   `browser-pane-allowlist.json` flagged as dead script).
2. Entries in `skill-trigger-dict.md` ↔ folders under `skills/`
   (missing folder = dead routing line → route-out;
   unlisted folder = unreachable-by-dict skill → report only, plugin/builtin
   skills legitimately live elsewhere).
3. Files referenced by `ops/OPS.md` routing table ↔ files under `ops/`
   (this is the file-existence half of 40-maintenance §4 ghost-rules — cite
   it, don't duplicate its content checks).
4. `SessionStart`/other hook interpreter paths still exist (Test-Path the
   python.exe etc.) — failure = route to update-config.
