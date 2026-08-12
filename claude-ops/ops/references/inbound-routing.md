# Inbound routing — what arrives from outside, and which procedure it gets

Detail file for `rules-usage-dict.md` §三. **Granularity determines the failure
mode**, so granularity is what routes.

## The asymmetry this exists to close

| Direction | Machinery |
|---|---|
| **Outbound** | `interop.py` leak gate (build aborts and writes nothing on a hit), `skill-share-packaging` Mode A de-coupling, genesis stamps, curation loop, acceptance evals |
| **Inbound** | one skill (`skill-share-packaging` Mode B), then nothing until 2026-08-12 |

Common root: **the environment models itself as a SOURCE**, so every inbound
path is discovered only after it breaks something. Both inbound gaps found so
far were found by accident.

## The three tiers

| What arrives | Procedure | Characteristic failure | Can it be stamped? |
|---|---|---|---|
| ONE skill | `skill-share-packaging` Mode B | malicious instructions, environment coupling | yes |
| a rule LAYER / ops tree / interacting artifacts | `config-self-audit` adoption mode (AD1–AD5) | RELATIONS: trigger collision, ordering, mechanism did not ship | yes |
| **plugin / marketplace bundle / MCP server** | **detection only — see below** | **opaque trigger surface** | **no** |

Tier 3 is different in kind, not just in size: those files are **managed,
ephemeral, and outside `~/.claude`**. They are re-materialised per session under
`%APPDATA%/Claude/local-agent-mode-sessions/`, so a stamp written into one is
gone next session and an edit is an edit to someone else's artifact. Adoption
mode does not apply. What is left is measurement and collision detection.

## Tier 3, measured (2026-08-12)

| source | n | description chars | median | >800 cap |
|---|---|---|---|---|
| `*/*/rpm/plugin_*/skills/` | 35 | 9,814 | 271 | 0 |
| `skills-plugin/` | 15 | 5,850 | 319 | **2** |
| **plugin total** | **50** | **15,664 (~3,900 tok)** | | **2** |
| `~/.claude/skills/` (local) | 14 | 8,551 (~2,100 tok) | 617 | 0 |

Three findings, all mechanical:

1. **The injected surface is 1.8× local and 65% of the whole skill-listing
   budget**, charged every session, never audited. This confirms the hypothesis
   that motivated the tier; it was previously assumed, not measured.
2. **Plugin descriptions are individually leaner than local ones** (median
   271/319 vs 617). The local corpus is the fat-per-skill one. Any trimming
   effort aimed at the listing budget should start at home, not at the plugins.
3. **`ops_health_nudge` checks 5 and 10 are blind here** — they walk
   `~/.claude/skills/` only, so the 2 over-cap plugin descriptions never nudge,
   and a plugin skill colliding with a local trigger never shows as dict drift.

**Do not "fix" tier 3 by editing plugin files.** The available moves are: drop
the plugin, accept it, or add a local disambiguation line to the LOCAL skill it
collides with (`config-self-audit` §4 Cross-surface duplicates, which now names
both roots).

## Outbound divergence marking

The mirror-image problem, same root. `~/.claude` is the SOURCE for
`WizerdBaChe/claude-share`, so the shared copy legitimately and permanently
differs from local — the share version carries stranger-facing wording that
would be pure cost here (bilingual trigger phrasing, format enumerations,
generic path names instead of real ones).

Rule: **a deliberate local/share divergence is recorded once, at the artifact,
so the next sync does not "repair" it.** The record names what differs and why,
not the diff itself. Worked example: `config-self-audit`'s description
deliberately drops the share version's `「搬進來的設定」` and its "shared
repo/zip" enumeration, because recipients there are strangers and the user here
is not. Absent that note, the next sync reads the difference as drift and undoes
it.

## A fourth surface, found 2026-08-12: `~/.agents/skills/`

Not a tier — a second SOURCE OF TRUTH, which is worse than any inbound tier.

`~/.agents/skills/` holds a full physical copy of all 14 skills (real
directories, not symlinks), frozen 2026-08-03. Measured against live:

| | count | note |
|---|---|---|
| identical | 0 | — |
| differ by 1–7 B | 10 | line-ending artefacts of the copy |
| **substantively stale** | **4** | `config-self-audit` −7,235 B (no adoption mode), `workflow-checkpoint` −912, `scientific-research-guide` −626, `project-retrospective` −406 |

`40-maintenance.md` §2 forbids this at rule scale ("a rule lives in exactly one
file") and nothing watched for it at corpus scale — `ops_health_nudge` check 10
walks `~/.claude/skills/` only.

**Resolved 2026-08-12 (user decision): retired.** Moved intact to
`archive/2026-08-12-agents-skills-retired/` with a note; opencode is now
supplied from the share repo, which has the machinery this copy bypassed.
`OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` is set in the user environment.

**The measurement trap, worth keeping.** With the copy in place,
`opencode debug skill` returned 3 entries — 1 built-in + 2 from
`~/.agents/skills/`, zero from `~/.claude/`. That reading said "opencode does
not see the live corpus; the wall already stands". **It was measuring the
shadow.** `~/.agents/skills/` was shadowing the `~/.claude/` scan; retiring it
took the count 3 → 15, all 14 live skills now visible — briefly MORE exposure,
during a change intended to reduce it.

Rule: **an observation taken while a shadowing artifact is present measures the
shadow, not the system.** Removing the shadow is part of the measurement. The
same shape as AD4's inverted gate — the same evidence means the opposite thing
depending on what else is in the tree.

Verified switch behaviour (each value from a real run): no flag → 15 entries;
`OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` → 1; `OPENCODE_DISABLE_EXTERNAL_SKILLS=1`
→ 1. opencode's built-in skill documents both as skipping "the external skill
scans under `~/.claude/` and `~/.agents/`".
