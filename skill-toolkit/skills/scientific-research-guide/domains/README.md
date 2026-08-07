# `domains/` — what ships here, and what deliberately does not

This share carries the **machinery** for domain profiles, not the profiles.

| File | What it is |
|---|---|
| `_template.md` | The 7-node profile skeleton. Start every new domain from it. |
| `_routing.md` | The load manifest — shipped with its format and four template rows, no real rows. |
| `domain-expansion-guide.md` | The authoring spec: the two-gate decision tree for base vs sub-profile vs reference vs boundary, node-by-node quality bars, and the pre-merge checklist. |

## What was excluded, and why

The source environment's `domains/` held filled profiles for its author's own
research fields (condensed-matter and semiconductor-device topics). Those files are
**subject-matter knowledge, not agent methodology** — they would be wrong for your
field, they are the largest content in the tree, and their presence misrepresents
what this skill is. They were removed from this share; the same applies to the
citation inventory under `../references/user-supplied-citations.md`, which now ships
as an empty template.

`domain-expansion-guide.md` still names some of those files in its illustrative
directory tree. Read those as **example filenames**, not as files you should expect
to find here.

## Consequence for the skill's evals

`../evals/evals.json` retains assertions written against the excluded profiles (for
example, one checks that a material sub-profile loads in preference to its generic
parent). Those evals are kept as **worked examples of what a good domain-routing
assertion looks like** — they are not runnable against this share as-is. Rewrite
them against your own first domain, or treat their `passed`/`evidence` fields as a
record from the source environment rather than a claim about this copy.

## Building your first domain

1. Read `domain-expansion-guide.md` §2 first — most authoring mistakes are a topic
   put at the wrong level, not bad content.
2. Copy `_template.md` to `<your_domain>.md` and fill all seven nodes. Node 6
   (pitfalls) and Node 8 (decision triggers) are what actually fire as standing
   rules during a session; a profile weak there is decorative.
3. Add one `base` row to `_routing.md` and delete the template rows.
4. Run the guide's pre-merge checklist before relying on it.
