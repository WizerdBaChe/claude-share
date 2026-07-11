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
| `telemetry/` | files > threshold | yes |
| `downloads/`, `outputs/` | files > threshold | no — user content, archive only |
| `backups/<date>/` | date-dir > threshold AND every file in it has a newer backup or is unchanged vs git HEAD | no — archive only |

## §3 CURATED — judged item-by-item, conservative

Working documents; only clearly-superseded items become candidates, each with
an explicit reason. When in doubt → KEEP.

- `drafts/`, `plans/`: > threshold AND the work is verifiably landed
  (referenced by a Global_skill_update.md entry or a git commit) → CANDIDATE.
- `agents/`, `skills/`, `ops/`: 🟡 tier — a folder here is CANDIDATE only via
  orphan detection (§4), and moving it requires per-item confirmation
  (SKILL.md invariant 4). Never age-based.
- `reports/`: user audit-trail documents (system-change remediation reports,
  new file per report) — KNOWN-KEEP, never age-based. Added 2026-07-07.
- `archive/` itself: never rescanned.

## §4 ROOT WHITELIST + ORPHAN DETECTION

Known root files: `CLAUDE.md`, `settings.json`, `settings.local.json`,
`.gitignore`, `.credentials.json`, `.oauth_refresh.lock`, `.last-cleanup`,
`mcp-needs-auth-cache.json`, `Global_skill_update.md`, `skill-trigger-dict.md`,
`keybindings.json`, `history.jsonl`. Any other root-level file → UNKNOWN ORIGIN.

Orphan checks (bidirectional; every finding is a REPORT line — route-outs or
confirmed-per-item moves, never silent):

1. Hook commands in `settings.json` ↔ files under `hooks/`
   (missing file = broken hook → route to update-config;
   unregistered file = dead script → CANDIDATE, per-item confirm).
2. Entries in `skill-trigger-dict.md` ↔ folders under `skills/`
   (missing folder = dead routing line → route-out;
   unlisted folder = unreachable-by-dict skill → report only, plugin/builtin
   skills legitimately live elsewhere).
3. Files referenced by `ops/OPS.md` routing table ↔ files under `ops/`
   (this is the file-existence half of 40-maintenance §4 ghost-rules — cite
   it, don't duplicate its content checks).
4. `SessionStart`/other hook interpreter paths still exist (Test-Path the
   python.exe etc.) — failure = route to update-config.
