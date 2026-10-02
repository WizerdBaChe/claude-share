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

## A fifth surface, found 2026-09-13: the plugin install cache

Same class as the fourth, one difference that matters: **nobody created it by
hand — the install path creates it.**

Installing a plugin from a LOCAL directory writes a version-pinned physical copy
to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, while
`known_marketplaces.json` records that marketplace's `installLocation` as **equal
to the source path**. Both trees then exist and both can execute. Measured on one
probe run: `${CLAUDE_PLUGIN_ROOT}` resolved to two different values inside 35
seconds — the source dir 12 times, the cache 3 times — and `pluginUsage` recorded
the same plugin under **two identities**, `<plugin>@<marketplace>` (4 uses) and
`<plugin>@inline` (1 use), the second being the namespace the desktop app uses
for its own bundled plugins.

Three consequences, in the order they bite:

1. **Editing the source takes effect without reinstalling**, so the cache copy
   goes stale silently and which copy runs depends on which root resolved.
2. **`ListPlugins` is not the instrument.** It returned `[]` while a 16-skill
   plugin was loaded. Neither is a model's own account of what is loaded: in the
   session whose model listed the local hooks and never mentioned the plugin, the
   plugin's hook had fired. Use the filesystem or `claude plugin list`.
3. **Uninstall does not fully undo it.** `claude plugin uninstall` cleared
   `enabledPlugins` and `extraKnownMarketplaces`, but the `@inline` entry in
   `pluginUsage` survived, and the cache tree survived carrying a platform
   `.orphaned_at` marker (leave that one alone — `plugins/.last_inuse_sweep`
   shows the platform GCs it).

Rule: **never anchor durable state to `${CLAUDE_PLUGIN_ROOT}`** — not because it
changes on update, but because it is *already not one value*. Drift check:
per-file sha256 between cache and source must match; a difference is a finding
(the `share_gate.py` check V shape with both ends swapped).

**The migration direction bites too, and it already has.** When something moves
the OTHER way — out of `~/.claude/skills/` and into a plugin — every path-based
reference to it breaks silently. Found the same day: `skill-share-packaging` A5
told the reader to run `skill-creator/scripts/quick_validate.py`, but there is no
local `skill-creator` any more; it is a plugin skill, and the validator now sits
under `plugins/marketplaces/.../skill-creator/skills/skill-creator/scripts/`
(plus a second copy in the desktop app's bundled skills-plugin). Nothing reported
the break — the instruction simply read as correct forever, the same shape as the
write-to-a-frozen-file failure recorded in that skill's A6.

Rule: **a reference to a skill's FILES is a reference to a location that can move
out from under it.** Locate by search (`find ~/.claude/plugins -name <file>`), or
cite the skill by name and let the reader resolve it.

Evidence and the full calibration chain:
the plugin-mechanism design's calibration record §6 and §6.2 (under the
source's outputs/ tree, not shipped here).

`review-when` **DISCHARGED 2026-09-17** — first `github`-source install measured
(`WizerdBaChe/wizerd-app-residue-sweep`, marketplace `wizerd-plugins`). The
answer: the two-root finding above **is specific to `directory` sources**, where
`installLocation` equals the source path so no separate install exists. A
`github` source behaves differently and makes **three** locations:

| location | what it is |
|---|---|
| the upstream repo | not on this machine |
| `~/.claude/plugins/marketplaces/<marketplace>/` | a clone; `installLocation` points here |
| `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` | the version-pinned copy |

Measured: all 15 payload files byte-identical across the clone, the cache and
the authoring tree. **But the version-pinned directory is not ours** — the
platform writes `.in_use/<pid>` inside it. That is worth knowing twice over:
it is a live counter-example to reading INV-3 ("no durable state under
`${CLAUDE_PLUGIN_ROOT}`") as a claim about the platform rather than about our
own code, and any drift check that diffs the two trees must skip `.in_use/`
or it cries wolf on every healthy install (fixed in `plugin_gate.py` check D,
control C11b).

Still unmeasured: `git-subdir` and `url` sources.
