# Governance starter — for a target repo with no collection rules

Seed ONLY when the target repo has no collection/publishing governance at
all. If it has any, that layer is authoritative and this file stays unused
(SKILL.md hard rule 1). Seed the minimum, then follow what you seeded.

## Minimum viable governance (three files)

**1. `COLLECTION-RULES.md`** — the decision procedure. Minimum content:

- Verbatim is the default for a first collection; every deviation is an edit,
  every edit is declared. A refresh re-applies declared edits, never blind-copies.
- Scrub targets: account names; absolute home paths; absolute paths on
  non-system drives; credentials; private hosts; pointers to private assets
  the reader cannot open (session ids, scheduled-task names, artifacts inside
  trees that do not ship). NOT scrub targets: repo-relative paths, project
  names, ruling ids, dates, measurements — removing those destroys
  verifiability and protects nothing.
- The source environment is canonical and read-only from here.
- A file the shipped content cites must ship or carry a disposition.

**2. `share-manifest.toml`** — the declarations a check can read:

```toml
collected_roots = ["<dir>/"]          # dirs whose files must declare provenance

[[collected]]
path = "<repo path>"
source = "~/<source path>"
status = "verbatim"                   # or "edited" (then edits = [...] required)

[[not_shipped]]
path = "<source path>"
disposition = "excluded-by-decision"  # or referenced-only / upstream-absent / partial
reason = "..."
fallback = "what the adopter gets instead"
```

**3. A gate script** — fail-closed checks over tracked files, run before any
push: leak patterns (the scrub-target classes above), provenance completeness
(every file under a collected root has an entry; every entry points at a
tracked file), citation completeness (shipped text citing an unshipped path
without a disposition). Never auto-fix; findings are instructions to a human
or model. Each check names the incident that created it, in the code.

## What NOT to seed

Do not seed checks for incidents the target has not had — a gate calibrated
only on hypotheticals rejects everything and gets switched off. Start with
the leak classes (those are universal) and let the rest accrete per real
finding, each shipping with a test case that fails without it.
