# CLAUDE_SHARE

Public-facing extracts from a personal `~/.claude` configuration environment,
shared piecemeal. Each subfolder is one self-contained share; content is
reviewed for local machine identifiers before being copied here, and since
2026-08-14 that review is a script, not a habit — see `tools/`.

Licensed under [MIT](LICENSE).

## Start here — pick your lane

**Never read this repo before?** → Lane A.
**Read it before and coming back?** → Lane B. Do not skip it. "I looked at this
already, it probably hasn't changed" is a documented failure mode in this
repo's own history, not a hypothetical.
**Going to copy files onto a machine?** → Lane C, and read
[`ADOPTERS.md`](ADOPTERS.md) first.

### Lane A — first read

| Order | Read | Why |
|---|---|---|
| 1 | [`environment-guide/PHILOSOPHY.md`](environment-guide/PHILOSOPHY.md) | Ten beliefs everything else hangs off. Skip it and the rules look arbitrary. |
| 2 | [`global-claude-md/CLAUDE.md`](global-claude-md/CLAUDE.md) | The always-loaded preferences file. Self-contained; every rule states its trigger. |
| 3 | [`claude-ops/ops/OPS.md`](claude-ops/ops/OPS.md) | Entry point and routing table for the rules layer. Read the table, not the whole layer. |
| 4 | [`AGENTS.md`](AGENTS.md) | One line per tracked file, when you want the map rather than the argument. |

`Global_skill_update.md` is the narrative of how this environment got its shape.
It is the most informative file here and also 67 KB and **frozen at 2026-08-11**.
Read it when you want history, not when you want current state.

### Lane B — you have read this before

The repo looks stable and is not. Three of the changes that mattered most were
small diffs that inverted a meaning:

- a target went **SYNC OFF** while its row stayed in the registry;
- the method layer was **retired entirely** (2026-08-11) — content that used to
  ship now does not, and the reason is that it never worked;
- a 2026-08-11 finding was "corrected" the same day and the correction was
  **wrong and is now retracted**. Reading either version alone misleads you.

So:

```git bash
git log --oneline <the-sha-you-last-read>..HEAD
```

Then check `CHANGELOG.md` for the dated entry, and re-read these four before
relying on anything you remember:

| File | What silently inverts in it |
|---|---|
| [`interop-layer/MIGRATION-MAP.md`](interop-layer/MIGRATION-MAP.md) | Target registry rows (on/off), portability classes (one is RETIRED), the inbound-dependency entry |
| [`tools/share-manifest.toml`](tools/share-manifest.toml) | Which dependencies are declared not-shipped, and what fallback you actually get. **2026-08-14: three hook entries here were wrong for a month** — classified "machine-bound" without re-checking. They ship now. **2026-08-16: the `outputs/` entry was wrong the same way** — called a scratch directory, actually the retrospective layer — and a `[[collected]]` entry claimed two leak gates were identical when they were not. Both corrected in place; neither history deleted. |
| [`claude-ops/ops/rule-registry.md`](claude-ops/ops/rule-registry.md) | The current value of every cap and standing ruling, plus its value history |
| [`claude-ops/ops/environment.md`](claude-ops/ops/environment.md) | Machine facts, per-block dated. Every one of them expires. |

If you are re-reading in order to answer a question, answer it from the file,
not from memory of the file. `claude-ops/ops/OPS.md` states the same rule for
the model: any mechanism name is an example, verify before relying on it.

### Lane C — you are going to install something

1. [`ADOPTERS.md`](ADOPTERS.md) — where to put this repo (and where not to),
   what it names but does not ship, and which symptoms are your platform rather
   than a defect here.
2. The `README.md` of the specific share you are copying — each carries its own
   install steps and de-identification notes.
3. [`interop-layer/acceptance-evals.md`](interop-layer/acceptance-evals.md) — a
   port with no eval run is not a finished port.

## Shares

| Folder | Contents |
|---|---|
| `global-claude-md/` | The top-level global `CLAUDE.md` entry point itself — conditional working preferences for Git workflow, environment/shell syntax, interaction style, engineering judgement, frontend layering (FSD), skill routing, project-operations tiering, file hygiene, and reply language. |
| `claude-ops/` | Anonymized snapshot of the operational rules layer: authority, command loop, dispatch, judgment, maintenance, bootstrap, evolution. |
| `skill-toolkit/` | Portable AI-agent skills and a bilingual trigger dictionary, reviewed for personal identifiers and local paths. |
| `interop-layer/` | Cross-agent sync layer: compiles a portable rules subset into global instruction files for other agents. Method depth is delegated, not shipped. |
| `environment-guide/` | Human-facing philosophy, operator manual, and commit-message conventions, including a full migration checklist. |
| `hooks/` | **New 2026-08-14, twelve hooks since 2026-08-16.** The mechanical enforcement layer the rules had been citing without shipping: destructive-command deny-list, subagent model cap, browser-pane measurement and scope guards, session health nudge, four shadow probes (delivery gate, context runway, fieldwork threshold, rule-load logger), and the compact-recovery trio (pre-compact bookmark, post-compact pointer card, transcript read-window guard) plus the mounting template. All fail-open. |
| `compact-recovery/` | **New 2026-08-16.** Post-compact recall as an operating mode: a PreCompact/SessionStart bookmark-and-pointer-card bridge over the three hooks above, plus the digest generator (`preserve.py`) their grep-first ladder leans on — what a `/compact` summary drops stays recoverable at on-demand token cost. Ships with a seven-item real-fire acceptance checklist. |
| `red-team/` | **New 2026-08-17.** Adversarial review made machine-checkable: a prompt shape that makes fabrication expensive, a mechanical anchor/scope gate that separates a citation slip from an invented quote, and an adversarial layer that sends each finding to a refuter which may not be its author. Layers 2–4 need no model at all. Ships with a blind-runnable acceptance checklist. |
| `architecture-diagramming/` | **New 2026-08-27.** The architecture-diagram capability set — theory (view selection + integrity instrument, two `product-design-thinking` references), production (`diagram-authoring`), audit (`code-review-deep-checklist` Mode B view layer) — packaged as one mechanism: integration map, install set, and a fourteen-item external acceptance checklist. The skills live in `skill-toolkit/skills/`; this folder is the loop and its verification. |
| `agents/` | **New 2026-08-14.** The eight subagent definitions `claude-ops/ops/20-dispatch.md` routes to, each with a `tools:` capability allowlist and a defined output contract. |
| `thinking-notes/` | Twelve numbered design-thinking notes. Argument, not policy — nothing there binds a reader. |
| `tools/` | The publishing gate — leak, placeholder, reference-disposition, structure, collection-provenance and dead-declaration checks, plus an opt-in source comparison — and `COLLECTION-RULES.md`, the procedure for deciding what may be collected in the first place. Its two procedures are worth reading even if you never collect: **A** for a file that is not here yet, **B** for one that is, because running A over B's files is what a 2026-08-16 refresh did to six deliberate decisions. |

## Where things are

| If you want | Read |
|---|---|
| A one-line map of every tracked file | `AGENTS.md` |
| To adopt any of this on a machine | `ADOPTERS.md` |
| How the source environment evolved, rule by rule (frozen 2026-08-11) | `Global_skill_update.md` |
| Why a rule holds its current value, going forward | `claude-ops/ops/rule-registry.md` |
| When each share was copied and what changed | `CHANGELOG.md` |
| The rules layer itself | `claude-ops/ops/` (start at `OPS.md`) |
| Installable skills | `skill-toolkit/skills/` (inventory in `skill-toolkit/README.md`) |
| Why any of this is shaped this way | `environment-guide/PHILOSOPHY.md` |
| What this repo names but does not ship | `tools/share-manifest.toml` |
| Where a collected file came from, and every edit made on the way | `tools/share-manifest.toml` `[[collected]]` |
| The rules for collecting anything else out of the source environment | `tools/COLLECTION-RULES.md` |

## Conventions

- One git repo at this root; each share is a subfolder, so future additions land
  as new folders/commits without touching prior shares.
- Nothing here is auto-synced from the source `~/.claude` — each share is a
  manual, reviewed snapshot as of its commit.
- No release tags, version numbers or content digests, on purpose. Pin a commit
  SHA on your side; see ADOPTERS.md for the reasoning.
- Before any push that touches shipped content: `python tools/share_gate.py`
  must exit 0. If you are COLLECTING rather than reading, add
  `--source <your ~/.claude>` — that enables the one check which can see a
  declared edit that a refresh quietly reverted.
