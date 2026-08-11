# Sync history

Per-refresh detail for each share in this repo. Split out of `README.md` on
2026-08-07 — the README had become ~96% sync history, so a reader (human or agent)
who opened only the top-level file learned *when* things were copied rather than
*what is here*. Orientation lives in `README.md`; this file is the record.

For the source environment's own evolution log — the rule-by-rule narrative behind
these snapshots — see `Global_skill_update.md` at this repo's root (frozen 2026-08-11;
standing rationale moved to `claude-ops/ops/rule-registry.md`).

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
