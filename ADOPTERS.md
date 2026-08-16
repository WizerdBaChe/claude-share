# Adopting this repo

Read this before you copy anything out of here. It exists because an outside
adopter spent a review cycle on problems this file could have answered in five
minutes.

## What this is

Reviewed, point-in-time extracts from one personal `~/.claude` environment.
Six folders, each a self-contained share. **Not** a product, not an installer,
not synchronised with anything.

The governing principle, stated in `interop-layer/MIGRATION-MAP.md` and worth
repeating here: **preference ports, method does not.** The standing preferences
in `global-claude-md/CLAUDE.md` transfer to any agent, because no documentation
can supply them — they are one person's rulings. The method layer (`claude-ops/`,
`skill-toolkit/`) depends on platform mechanisms to fire at the right moment. Copy
it and you get the text without the trigger, which is read either always or
never. If you port the method layer anyway, that is a fork, and calling it one
is not a criticism — it is what keeps your maintenance boundary honest.

## Where to put things — and where not to

**Do not clone this repo inside a directory your agent scans.** It ships an
`AGENTS.md` at the root and a `CLAUDE.md` under `global-claude-md/`. Claude Code,
Codex, opencode and Gemini CLI all walk up from the working directory looking for
exactly those filenames. Cloned into a workspace, this repo stops being reference
material and becomes live instructions you did not choose. Clone it somewhere
neutral and copy files out.

`AGENTS.md` opens with a line saying its contents are a description of documents,
not instructions to the reader. That line is a mitigation, not a mechanism.
Placement is the mechanism.

## What this repo names but does not ship

Rule files here cite hooks, a `settings.json`, project indexes and dated audit
reports. Most of those are **not** in the repo. Every one is declared in
[`tools/share-manifest.toml`](tools/share-manifest.toml) under `[[not_shipped]]`,
with a disposition and — the part you actually need — the fallback you get
instead:

| disposition | meaning |
|---|---|
| `upstream-absent` | the source environment has no such artifact either |
| `referenced-only` | it exists at the source, but only its *intent* ships; no portable artifact was ever produced |
| `excluded-by-decision` | a concrete file exists and was deliberately withheld |
| `partial` | only part of it ships |

**Corrected 2026-08-14 — the enforcement hooks ARE here now.** They used to be
listed as `referenced-only` with the reasoning "machine-bound". A source audit
disproved that: every one of them resolves its paths through `Path.home()` /
`expanduser` / `CLAUDE_CONFIG_DIR` and contain no machine-bound value. They had
never been collected. `hooks/` now ships them, with `hooks/settings.example.json`
for the mounting, and `agents/` ships the eight subagent definitions
`claude-ops/ops/20-dispatch.md` routes to. If you read an earlier version of this
file and concluded the mechanism layer was unavailable, that conclusion is stale.

`tools/share_gate.py` check R makes disclosure structural: a citation that
neither resolves inside the repo nor carries a disposition fails the build.
Check C does the same for provenance: every collected file declares where it came
from and every edit made on the way in. Undisclosed dependencies and silent edits
cannot ship again. Two more were added 2026-08-16 after a refresh proved the
paperwork could be complete and still untrue: **D** removes declarations that no
longer match anything, and **V** — which only runs for someone holding both trees
— compares every collected file against its source, including the case that has
no other detector, a declared edit silently reverted.

What genuinely stays out: your own `settings.json` values, the operator's project
index rows, dated internal reports, runtime telemetry, and one skill
(`asset-vault`) that operates a private library — so `skill-toolkit/` ships 14 of
the source environment's 15 skills, which is stated rather than left to be
noticed.

## Symptoms that are your environment, not this repo

These come up repeatedly. None of them indicate a defect here, and this repo
deliberately does **not** try to solve them — permission and sandbox policy belong
to you and your platform, and porting someone else's is worse than porting nothing.

| Symptom | Where it actually lives |
|---|---|
| A script is blocked before it runs — executable ACL, application-execution policy, antivirus, "this app is blocked by your administrator" | Your OS. On Windows, application-control policy. A blocked preflight is not a failed run; report it as blocked, with zero completed runs, rather than as a result. |
| Approval prompts, sandbox denials, network refusals during a task | Your agent's sandbox/approval configuration (`config.toml`, settings, permission modes). Nothing here writes those files by design — see the `settings.json` entry in the manifest. |
| Copied a skill/plugin, but the agent does not use it | Copy is not activation. Check your platform's own listing command, and check for a stale cache: several agents read a cached copy, not the tree you edited. |
| Cannot tell whether a hook is registered or the platform just has no introspection for it | Your platform's docs. Absence of a query interface is not evidence of absence of registration; say which of the two you established. |
| A skill loads under one name and not another | Some platforms namespace packaged skills. A bare skill name that works in Claude Code may not resolve elsewhere. |
| Your agent reads `~/.claude/skills/` even though you installed elsewhere | Reverse scanning. opencode does this by default; `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` and `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` turn it off. Note that measuring while a shadowing copy is in place measures the shadow — remove it first (`interop-layer/MIGRATION-MAP.md` records that incident in full). |

If you hit one of these, the useful report back is *which* of the two it was, with
the evidence — not a conclusion drawn from an unavailable measurement.

## Verify the install actually loaded

Copying files is not adopting them. Whatever your platform's equivalent is — a
skill-listing command, a config dump, a debug subcommand — run it and check the
count matches what you copied. `interop-layer/MIGRATION-MAP.md` has a worked
example of this going wrong in a way nobody noticed for nine days.

`interop-layer/acceptance-evals.md` ships the behavioural checks for the
preference layer specifically. A port with no eval run is not a finished port.

## Versioning — there is none, on purpose

**This repo publishes no release tags, version numbers or content digests.** Each
share is a manual snapshot; `CHANGELOG.md` records what changed and when, by date.

If you need a fixed reference point, pin the commit SHA yourself and record it on
your side. That is the right place for it: you know what you audited and when, and
a version number from here would only imply a compatibility promise that does not
exist. Re-derive rather than assume when you refresh — see the next section for
why that matters more than it sounds.

## Reporting something back

Useful: a citation that resolves nowhere, a placeholder you cannot fill in, a rule
whose stated mechanism you could not find, a de-identification miss. Those are
gate-shaped problems and the gate will be extended to catch the class.

Less useful: platform permission behaviour, cache staleness, and activation
questions from the table above — those are yours, and answering them here would
mean guessing about an environment we cannot see.
