# Output Contract — machine-readable findings & coverage (Mode A/B/C)

Adapted from openai/codex-security's sealed-bundle contract — the LIGHT version.
This skill borrows only two hard assets: (1) stable finding identity so re-reviews
can be diffed, and (2) inventory-first coverage so "reviewed everything" is a
verdict list, not a closing sentence. The heavier security machinery
(three-stage evidence receipts, attack-path narratives, policy layer) belongs to
security-deep-checklist's scan-contract.md and is deliberately NOT duplicated here.

## 1. Deliverables per review

Alongside the human report (Traditional Chinese, NEW file), emit two JSON files
next to it (machine-read → English content, per global language rules):

- `<report-basename>.findings.json`
- `<report-basename>.coverage.json`

**Source-of-truth rule:** the manifests are canonical; the report body is a
projection. Never change a verdict/severity in the report without updating the
manifest first. If they disagree, the manifest wins.

## 2. findings.json

```json
{
  "documentType": "code-review-deep-checklist.findings",
  "schemaVersion": "1.0",
  "scanId": "<report-basename>",
  "target": { "type": "git_revision|git_diff|directory", "id": "<commit sha, diff range, or path>" },
  "findings": [ { ... } ]
}
```

Each finding object:

| Field | Req | Content |
|---|---|---|
| `findingId` | yes | `crd_` + 6+ hex chars, unique within this review |
| `ruleId` | yes | family slug, namespace `review.` — e.g. `review.correctness.off-by-one`, `review.smell.god-class`, `review.traceability.spec-mismatch`, `review.fitness.license`, `review.arch.boundary-erosion`, `review.state.undefined-transition` (stateful-logic family, single-review.md §10), `review.state.substrate-unmodelled` (the machine has no state for its own apparatus being unavailable, §10), `review.state.calibration-expiry` (a measured constant with no named invalidating event, §6), `review.metric.instrument-shared-defect` and `review.metric.population-mismatch` (SKILL.md Part 0.7), `review.contract.ungated-twin` (cross-boundary contract family, single-review.md §11 / project-review.md), `review.arch.view-gap` (a reconstructed view fails a view-integrity check, or a tier-required view cannot honestly be built — project-review.md view audit), `review.arch.view-inconsistency` (cross-view correspondence break, incl. code-vs-doc diagram drift) |
| `identity.anchor` | yes | semantic owner of the issue — function/class/module name (stable across line drift), e.g. `src/cart.ts:applyDiscount` |
| `identity.instance` | no | disambiguates siblings under one anchor |
| `fingerprint` | yes | `crd/v1:sha256:` + sha256 of `target.id\|ruleId\|anchor\|instance` — compute via `printf '%s' '...' \| sha256sum`, never hand-derive |
| `severity.level` | yes | `blocker` / `should-fix` / `consider` / `nit` (SKILL.md definitions) |
| `severity.changeConditions` | yes | what evidence would upgrade/downgrade it (e.g. "upgrade to blocker if this path is reachable with user input; downgrade to nit if module is slated for deletion") |
| `confidence.level` + `confidence.rationale` | yes | `high`/`medium`/`low`; one line on how verified. `low` = labeled suspicion in the report |
| `dimension` | yes | one of the six: `correctness` / `completeness` / `performance` / `readability` / `maintainability` / `extensibility` |
| `preExisting` | yes | boolean. Mode A: findings on code this change didn't touch MUST be `true` and stay out of the change's verdict. Mode B/C: there is no "this change", so the field answers "did this predate the round of work under review?" — `true` for standing debt, `false` for what that round introduced or first made reachable. Name the reference point in `target.id` so the answer is checkable |
| `title`, `summary`, `recommendation` | yes | recommendation states cost/benefit/why-now for any refactor proposal |
| `locations[]` | yes | `{path, startLine, role}` |
| `evidence` | yes | the observation that grounds it: quoted lines, tool output, metric value — one concrete item minimum; no receipts pipeline beyond this |

## 3. Re-review diffing

On re-review of the same target lineage, if a previous findings.json is
available, diff by fingerprint and mark each finding **new** / **persisting** /
**resolved** / **reopened** in the report. This is how "修沒修" becomes
answerable. Fingerprint match is a reconciliation signal, not proof of
equivalence — spot-check before claiming "persisting". This also serves the
regression rule for previously-accepted code: accepted behaviours that
re-appear as findings are `reopened` and called out first.

## 4. coverage.json — inventory first

**Before reading any code**, write the inventory at the granularity you can already
see — Mode A: the changed-file list; Mode B: the module/package tree plus the entry
points (what can start work — routes, CLI commands, event handlers, UI actions);
Mode C: the dependency list. That first pass is mechanical and cheap, and its job is
to fix the DENOMINATOR before reading can bias it. Units discovered later (an
unregistered state machine, a dead code path, a second writer) are APPENDED with
`"discoveredDuringReview": true` — never used to quietly re-draw the boundary. Then
judge each. "Review complete" requires every unit dispositioned.

```json
{
  "documentType": "code-review-deep-checklist.coverage",
  "schemaVersion": "1.0",
  "scanId": "<report-basename>",
  "mode": "A|B|C",
  "completeness": "complete|partial",
  "units": [
    { "id": "src/cart.ts", "label": "changed file", "disposition": "reported", "findingRefs": ["crd_0a1b2c"] }
  ],
  "explicitExclusions": [ { "pattern": "dist/**", "reason": "generated" } ],
  "deferred": [ { "id": "d1", "reason": "test suite too slow to run locally; correctness dimension unverified for src/sync/", "unitIds": ["src/sync/"] } ]
}
```

- Unit granularity: Mode A = each changed file (plus directly-depended files
  pulled in); Mode B = each module/package + each of the six dimensions at
  project scope; Mode C = each dependency under audit.
- `disposition`: `reported` → `needs_follow_up` (has deferred entry) →
  `not_applicable` → `no_issue_found` (actually read, clean — never a default).
- A **focused** review (Mode B through one lens) declares `"scope"` next to `mode` —
  one sentence naming the lens and what it deliberately does not cover. Units outside
  the declared scope go in `explicitExclusions` with
  `reason: "outside declared scope: <lens>"`, NOT in `deferred`; `deferred` stays for
  things inside the scope that could not be finished. With that split a focused review
  can honestly reach `completeness: "complete"` — complete against its declared scope
  — while a reader still sees the whole boundary in one file. A review with no
  `scope` field is claiming full breadth.
- **Hard invariant:** `completeness: "complete"` requires `deferred` empty and
  no `needs_follow_up`. Otherwise `"partial"`. The report's "what was NOT
  covered" section is generated FROM these entries — the old habit of recalling
  omissions from memory at the end is retired.

## 5. Boundary with security-deep-checklist

A security issue noticed during review gets a finding here with ruleId in the
`sec.` namespace, `confidence: low`, and a note "discovery-stage candidate —
needs security-deep-checklist validation"; it carries NO three-receipt evidence
and its severity does not gate the merge verdict alone. Recommend the handoff
in the report. Conversely, quality findings never adopt the receipts pipeline —
one grounded observation (§2 `evidence`) is this skill's standard.
