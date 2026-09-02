# Adopted config — merge-semantics adoption and how to audit it

Loaded by `SKILL.md` for its **adoption mode**. Also readable standalone as the
SOP for whoever is doing the copying, before any audit happens.

**Scope**: durable config — rules, skills, ops files, agent definitions — copied
from ANOTHER environment into this one, which already has its own. Same platform,
both sides Claude Code. Not cross-platform porting (`interop/`), not a
fresh-machine relocation (`OPERATOR-GUIDE.md` Part 3).

## Why this needs its own procedure

Four adoption paths exist here, and a merge is none of them:

| Path | Situation | Semantics |
|---|---|---|
| `OPERATOR-GUIDE.md` Part 3 | this config → a new machine | **replace** — the target is renamed away first, so conflict is impossible by construction |
| `interop/` | rules → another agent platform | one-way compile of a curated subset; triggers are known not to port |
| `skill-share-packaging` Mode B | ONE downloaded skill | single artifact, security-first |
| `config-self-audit` default mode | ONE rule/hook/skill you own | single artifact, cheap-by-design |
| **adoption mode (this file)** | **a rule LAYER into a populated environment** | **merge** |

All four are scoped to exclude RELATIONS between rules. A relocation guide
answers conflict with "there is no conflict — you replaced everything". Adoption
has no such luxury: two internally-consistent rule sets now share one namespace,
one precedence order, and one trigger surface.

## This is not hypothetical here

`~/.claude` models itself as a SOURCE (it publishes to `claude-share`), which is
exactly why its inbound paths are thin. It has already been a recipient, and it
went wrong:

- **The `agents/` case.** 22 subagent definitions arrived from a third-party kit
  (`ai-team-os`) and instructed every dispatched subagent to call tools that do
  not exist here. They sat in the gap between the two audit skills for 37 days
  (2026-07-06 → 2026-08-12) before being rewritten down to 8. That is AD4's
  failure mode, at full scale, in this environment. See `40-maintenance.md` §5.
- **The plugin surface.** Measured 2026-08-12: **50** plugin `SKILL.md` across
  two injection roots under `%APPDATA%/Claude/local-agent-mode-sessions/`
  (`*/*/rpm/plugin_*/skills/` = 35, `skills-plugin/` = 15), carrying **15,664
  chars of description (~3,900 tokens)** against **14 local skills at 8,551
  chars (~2,100 tokens)** — the injected surface is **1.8× local and 65% of the
  whole skill-listing budget**, and none of it went through any audit.
  `ops_health_nudge` checks 5 and 10 police `~/.claude/skills/` only, so the
  **2 plugin descriptions that exceed the 800-char cap are invisible** to them.
  (An earlier draft of this file said "31", counting
  `~/.claude/plugins/marketplaces/` — that is the marketplace CATALOG on disk,
  not what loads. Corrected 2026-08-12; see `ops/references/inbound-routing.md`.)
- **Zero provenance.** `grep -rn "adopted-from:\|reconciled:"` returns nothing.
  Neither of the above is recorded as an import anywhere.

## The failure signature

Two symptoms dominate, and both are produced BY the adoption, not inherited:

1. **Ordering conflicts.** Imported rules carry assumptions about what runs
   first and what supersedes what. Those were true in a tree where every
   referenced file existed. Here they become claims about a sequence nobody
   implements.

2. **Near-duplicate rules with slight differences — one condition, two
   triggers.** "Analyse and adapt" is a *generative* act: it rewrites each rule
   into local vocabulary. An upstream rule that already had a local counterpart
   now exists twice, as two paraphrases. Both fire. Where they differ in a
   detail, behaviour is whichever the model weighted that turn —
   non-deterministic and invisible in a diff.

Note the second one carefully: the adopted material typically CONTAINS the rules
forbidding exactly this (`40-maintenance.md` §2 "a rule lives in exactly one
file"; §3 Birth budgets "MERGE with any near-duplicate"). They arrive as text, in
the same shipment as the duplicates they were meant to prevent, with no gate
between. **Anti-duplication rules cannot police their own installation.**

## Why the default mode reports clean

Not a model-quality problem — a well-behaved model following the default
checklist will *correctly* decline this work. Five compounding reasons:

1. **Scope excludes the evidence.** `Scope of one run` says audit only what was
   named or just created. Adoption defects are relational, and the other half of
   each collision is a rule that was NOT just created.
2. **No ordering section.** §1–§9 cover claims, existence, security, trigger
   quality, cost, language, telemetry, subagents, external tools. The only
   overlap check (§4) reads skill *descriptions*, not rule bodies.
3. **The §2 gate inverts.** Normally a finding referencing a nonexistent path is
   void. After a transplant, a dangling reference is the *most* important
   finding: the rule shipped, its enforcement did not. Same evidence, opposite
   meaning — the gate actively voids the true findings.
4. **Telemetry is empty by construction.** §7 measures usage via
   `usage-window.py`; a fresh transplant has no history. The one check that
   reveals a never-firing rule is silent exactly when it is needed.
5. **Nothing records that an adoption happened.** No provenance marker, so no
   trigger condition. Note the asymmetry: `interop/` stamps outbound artifacts;
   the same-platform inbound copy path has no stamp at all.

## The provenance stamp (makes the mode self-triggering)

Every file arriving from another environment gets one comment line at the top, in
that file's own comment syntax:

```
<!-- adopted-from: <repo or source name> | source: <commit or date> | adopted: <YYYY-MM-DD> | reconciled: no -->
```

- `reconciled: no` is the trigger. One grep finds every unreconciled import.
- It flips to `reconciled: <YYYY-MM-DD>` only when an adoption pass has closed
  every finding, or recorded the open ones with an owner.
- An adopted file with NO stamp is itself finding AD1.

## Part 1 — At copy time (the SOP)

Seven steps. Each has a check producing an artifact, not a feeling.

1. **Quarantine before installing.** Keep the incoming tree outside `~/.claude`
   until steps 2–6 are done. An imported rule that is already loading is a rule
   you are debugging in production. *Check*: `git status` clean.
2. **Inventory both sides at RULE granularity**, not file granularity — a
   file-level diff hides the case this document is about, because the duplicate
   pair lives in two differently-named files. *Check*: two lists, every incoming
   rule has a row.
3. **Build the trigger table (AD2) BEFORE adapting the wording.** Adaptation
   destroys the lexical similarity that makes collisions visible. *Check*: table
   exists, every collision row classified.
4. **Adapt, but never adapt two things into a near-pair.** Legitimate outcomes:
   keep local / replace local / merge into one rule in one file / keep both WITH
   an explicit supersession statement naming which wins when. "Keep both and
   reword slightly" is not on the list. *Check*: each row records its outcome.
5. **Check what did not ship.** Rule text ships freely; hooks, scripts and
   `settings.json` entries usually do not. *Check*: every rule mentioning
   enforcement marked `mechanism present` or `DEGRADED to prose`.
6. **Separate the source author's preferences from portable method.** Caps,
   reply language, standing rulings, relaxation defaults, persona. Not defects —
   decisions belonging to someone else. *Check*: explicit keep / adjust / drop
   per row from this user.
7. **Stamp, install, then audit** — as the first act afterwards, not weeks later
   when something misbehaves. *Check*: `grep -rn "adopted-from:"` matches step 2.

## Part 2 — At audit time

AD1 first; the rest in any order. Every finding carries a verification method,
and fixes still require consent. AD1–AD5 are summarised in `SKILL.md`; the
additions below are the parts that do not fit there.

**AD2 classification table**

| Class | Meaning | Fix |
|---|---|---|
| `exact` | same trigger, same instruction | delete one, keep the better-placed |
| `refinement` | same trigger, one is narrower | merge into one rule in one file |
| `conflict` | same trigger, incompatible instructions | user decides; record the ruling |
| `layered` | both intended to fire, in order | keep, but write the order down explicitly |

Cover every surface that can carry a rule: `CLAUDE.md`, `rules/` path-scoped
files, `ops/*`, skill descriptions, plugin skills, project `CLAUDE.md`.
*Verification*: for a chosen collision, state the user sentence matching both
rows, and the two `file:line` locations.

**AD3** — the most common single cause of "one condition, two triggers" after an
adoption is a supersession tag imported without its consuming rule: tags are
inline markers that survive a copy, while the rule that consumes them lives in a
separate file that often does not. *Verification*: for each tag, cite the
`file:line` of the rule that consumes it, or record it inert.

**AD4** — *Verification*: the existence check for the named mechanism PLUS its
registration (a `settings.json` entry, a hook listing, a scheduler entry).
Presence of a file on disk is not registration (`40-maintenance.md` §4.2).

**AD5** — present as one list with a keep / adjust / drop column and get an
answer per row. Batch consent is not acceptable for anything that widens what
runs without asking.

*Distinguish two kinds of inherited value* (found in the 2026-08-12 pass): a
value that changes what the AGENT does regardless of the task — a size cap, a
reply language, a relaxation default, a model tier — is contamination and must
be ruled on. A value that ADVISES on the package's own domain — a motion
package saying "never exceed 1/3 screen without an intermediate keyframe" — is
the payload you adopted it for. Flag the second kind once, do not treat it as a
defect, and revisit only if it starts overriding an explicit user direction.

## Worked example — the first real AD2 run (2026-08-12)

Trigger condition: *"an instruction file names a tool or mechanism that may not
exist here."* Four rows, found while adding this very mode:

| # | file:line | operative verb | class |
|---|---|---|---|
| 1 | `SKILL.md` §2 | VOID the finding (mark `stale`) | baseline |
| 2 | `SKILL.md` §8 Phantom references | FLAG as defect | `layered` on 1 — declared inline as "§2 applied to bodies" |
| 3 | `ops/references/integrity-sweep.md` check 2 | grep → returns defect | `layered` on 2 — standing sweep vs on-demand audit |
| 4 | AD4 (proposed) | FLAG as `DEGRADED to prose` | **`refinement` on 2** |

Row 4's class dictated the fix: `refinement` → merge into one rule in one file.
So AD4 does not restate the method — it points at §8 and adds only what is
genuinely wider (scope beyond `agents/*.md`, plus the gate inversion). Rows 1–2
show the pattern to copy: when two rules must both fire on one trigger, declare
the relationship inline, and the collision stops being a defect.

**This is also the mode's first evidence about itself**: run on its own
installation, AD2 found a real `refinement` and changed the design. Had it found
nothing, that would have been a finding about the mode, not proof of quality
(`40-maintenance.md` §4.3).
