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

The largest case: **the enforcement hooks are not here.** `hooks/model_cap_guard.py`,
`hooks/ops_health_nudge.py` and `hooks/ui_verify_guard.py` are cited across the ops
layer as the mechanism behind a rule. You get the rule as prose. Where a rule says
"mechanically enforced", read "mechanically enforced *in the source environment*" —
and treat the prose version as known-weak, because in at least one case the prose
form recurred unfixed for about a month before enforcement moved to a hook.

`tools/share_gate.py` check R makes this structural: a citation that neither
resolves inside the repo nor carries a disposition fails the build. Undisclosed
dependencies cannot ship again.

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
