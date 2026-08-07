# CLAUDE_SHARE

Public-facing extracts from a personal `~/.claude` configuration environment,
shared piecemeal. Each subfolder is one self-contained share; content is
reviewed for local machine identifiers (usernames, absolute paths, emails)
before being copied here.

Licensed under [MIT](LICENSE).

## Shares

| Folder | Contents |
|---|---|
| `interop-layer/` | Cross-agent sync layer: compiles a portable rules subset into global instruction files for opencode / codex / Antigravity. See `interop-layer/README.md`. |
| `skill-toolkit/` | Portable AI-agent skills and bilingual trigger dictionary, reviewed for personal identifiers and local paths. See `skill-toolkit/README.md`. |
| `claude-ops/` | Anonymized snapshot of operational guidance for a Claude Code environment. See `claude-ops/README.md`. |
| `thinking-notes/` | Numbered design-thinking notes on one-shot delivery, debugging epistemology, delegation economics, and related topics. See `thinking-notes/README.md`. |
| `environment-guide/` | Human-facing philosophy, operator manual, and commit-message conventions for the source `~/.claude` environment, including a full migration checklist. See `environment-guide/README.md`. |
| `global-claude-md/` | The top-level global `CLAUDE.md` entry point itself — conditional working preferences for Git workflow, environment/shell syntax, interaction style, engineering judgement, frontend layering (FSD), skill routing, project-operations tiering, file hygiene, and reply language. See `global-claude-md/README.md`. |

### `claude-ops/` snapshot details

- Source: `~/.claude/ops/` (13 Markdown files, +1 since the last refresh), copied manually on 2026-07-11; refreshed 2026-07-31, 2026-08-02, 2026-08-06, 2026-08-07.
- Review scope: usernames, local paths, account or machine identifiers, and email-like strings.
- Result: one source username was removed (`ops/environment.md`); references between the operational documents were intentionally retained. 2026-08-02 refresh: `ops/40-maintenance.md` §3 trim-trigger line updated to match the source's raised global-`CLAUDE.md` cap (~12K → ~15K, with rationale) — the only file that had drifted since the prior refresh. 2026-08-06 refresh: premise-gate + refutability-statement rule-set synced across `05-authority.md`, `10-command-loop.md`, `30-judgment.md`, `60-bootstrap.md` (new §G Decision & Process Journal), `OPS.md`, `rules-usage-dict.md` (new §7 schema registry); new file `ops/60-record-templates.md` added (templates extracted from `60-bootstrap.md` in a same-day trim pass); `40-maintenance.md`'s ops-file size trigger raised ~10K→~12K; `lessons.md` gained L-009 (browser-pane screenshot timeout misdiagnosis). No personal identifiers found in the synced content. Full detail: `skill-toolkit/Global_skill_update.md`'s 2026-08-06 entry. 2026-08-07 refresh: `environment.md` restructured — per-block `as-of` dating replaces a single file-level verification date (which had already gone stale against a later fact recorded in the same file), the tier table is scoped explicitly to *subagent* dispatch, and the main-loop-model section became a read-it-don't-infer procedure (a config file's `model:` pin is a fallback marked "assumed", never proof of the running model — the prior wording made `05-authority.md` §2's automatic-L0 branch fire on a stale inference). Tier vocabulary corrected across `05-authority.md`, `30-judgment.md`, `60-bootstrap.md`: a *session* has no tier, the *main-loop model* it runs on does. `40-maintenance.md` gained an audit-trail entry schema (trigger / change before→after / result / rollback / open), registered in `rules-usage-dict.md` §7 and paid for by lossless trims to stay under the size cap. Same username removal as before in `environment.md`; no new identifiers.
- This is a point-in-time snapshot, not a synchronization target. Folder-level documentation is maintained separately.

### `skill-toolkit/` snapshot details

- Source: `~/.claude/skill-trigger-dict.md`, `~/.claude/skills/`, and `~/.claude/Global_skill_update.md`, copied manually on 2026-07-11; refreshed 2026-07-31, 2026-08-02.
- Contents: a bilingual trigger dictionary, 13 skill directories with their referenced material and evaluations, plus the append-only global skill update log.
- Review scope: usernames, email-like strings, absolute local paths, internal project or package names, runtime lock metadata, and (2026-08-02) third-party license completeness for vendored content.
- Result: non-skill paths and identifiers were replaced with portable placeholders; the runtime lock metadata was redacted.
- Exception: historical paths in `Global_skill_update.md` that point directly to skill files were intentionally retained verbatim to preserve the update log's traceability.
- 2026-08-02 refresh: added `skills/motion-design/` (animation/3D design methodology hub) plus its `skill-trigger-dict.md` section and disambiguation rows. Its vendored `vendor/threejs/` reference package was **excluded** — the source environment's own update log had recorded that upstream's license defect (no `LICENSE` file, no named copyright holder) as blocking redistribution, and this share honours that ruling; only the properly-licensed `vendor/lottiefiles/` package was carried over, with the excluded package's SKILL.md/NOTICE.md pointing to its upstream URL instead. One hardcoded local path (`local/env-bridge.md`, pointing at a sibling `asset-vault` skill not included in this share) was also generalized. `skills/asset-vault/` was deliberately **not** imported this round (tied to a separate in-progress project).
- 2026-08-06 refresh: `skills/scientific-research-guide/` synced to the source's 2026-08-03 domain-expansion pass — two new base domain profiles (`gan_power_device.md`, `microled.md`), one new TI method sub-profile (`bi2se3_plasmonic_photoresponse.md`), a new source-provenance citation inbox (`references/user-supplied-citations.md`), and a swappable-slot convention for optional external tools (`domain-expansion-guide.md` §3.1) that also fixed a hardcoded personal path in `domains/plasmonic_waveguide.md`. Leftover draft material from a prior editing-copy round (`material/`, `MATERIAL-INTEGRATION-VERIFICATION-REPORT.md` — the latter naming local machine paths) was moved to `scientific-research-guide/archive/` and excluded from git via `.gitignore`, fully superseded by the integrated domain files. `skills/workflow-checkpoint/SKILL.md` also synced (journal-sweep step, resume-time premise re-confirmation). See `skill-toolkit/Global_skill_update.md` for the full entries.
- 2026-08-07 refresh: `Global_skill_update.md` only — one appended entry covering the same-day `claude-ops/` round, and the first entry written to the newly-registered audit-entry schema. No skill directories changed.
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

## Conventions

- One git repo at this root (`CLAUDE_SHARE/.git`); each share is a subfolder,
  so future additions land as new folders/commits without touching prior
  shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
