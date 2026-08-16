# Project map — the read-time layer's schema, fingerprint, and diagram catalogue

Detail file for `60-bootstrap.md` §H. The RULE (when a map is derived, that the
two layers never merge, promote/demote, conflict arbitration) stays in §H; this
file holds the formats and the algorithms. Loaded on demand, never at session
start.

## 0. Why this layer exists (the asymmetry it encodes)

| | write-time (§C/§E/§G) | read-time (this file) |
|---|---|---|
| content | know-**why**: intent, rejected options, rulings | know-**what/where**: what exists, where, how connected |
| source | only in the session that produced it | the repo — code, git, filesystem |
| regenerable | **no** — missed is lost forever | **yes** — rerun any time |
| cost | discipline (remember to write it) | compute (tokens, attention) |
| timestamp means | event time — never expires | validity — expires on relevant change |
| failure mode | silent absence | **silent staleness** (looks authoritative, is wrong) |
| verification | none possible — trust the author | rerun and compare |

The consequence that drives every rule below: **a map with no fingerprint is
worse than no map**, because a reader will trust it instead of checking.

## 1. File and location

`~/.claude/references/<project>-map.md` — central, not inside the analysed repo.
Reasons: third-party and read-only repos must not be written into; the map
outlives the checkout; it sits beside the write-time ledgers §A already reads.
`map` is a registered `<kind>` (`LABEL-REGISTRY.md` §4). Gitignored with the
rest of `references/`; it is a derived view (`references/project-visibility-design.md`
INV-1: disposable, regenerable, gitignored).

## 2. Header — the fingerprint (mandatory, every field)

```markdown
<!-- GENERATED FILE. Only three writes are legal: generate / patch / prune (§9).
     Anything else is a hand edit and is lost on the next regeneration.
     Confirmed facts are PROMOTED to <project>-decisions.md, not edited in here. -->
map-schema: 1
project: <slug>
repo: <absolute path>
generated-at: <YYYY-MM-DD HH:MM>
generated-from: <full SHA from `git rev-parse HEAD`>   # or: no-git
fallback-fingerprint: <file-count>/<newest-mtime>      # ONLY when generated-from: no-git
covers: <glob>, <glob>          # what was actually scanned
excludes: <glob>, <glob>        # deliberately skipped (vendored, build output, archive)
budget: <N> files read, depth <D>, <T> truncated   # what the scan cost and what it dropped
```

Rules:
- **`covers` is a promise about silence**: anything outside it is "not looked
  at", never "not present". A reader who cannot tell those apart will conclude
  a subsystem does not exist. State it or the map lies by omission.
- **`budget` records truncation**: if the scan hit its ceiling and stopped, `T`
  is non-zero and the map says so at the top. A silently truncated map reads as
  a complete one.
- **`no-git` degradation**: without git, `fallback-fingerprint` answers "did
  anything change" but not "what". Every STALE decision then falls back to
  regenerate-on-any-change — correct, just more expensive. Say so in the header.

## 3. Provenance tags (every assertion carries exactly one)

| tag | meaning | required companion |
|---|---|---|
| `[git]` | derivable from git or the filesystem; a machine can re-check it | — |
| `[read]` | read the source and concluded it | a `file:line` locator |
| `[infer]` | inference; no direct evidence | what would confirm or refute it |

`[read]` without a locator and `[infer]` without a confirmation path are both
malformed — they are unverifiable claims wearing a verification badge. This is
the same origin-tagging the premises rule applies in conversation (global
CLAUDE.md, `30-judgment.md` R2), sunk to file level: `[git]`/`[read]` are
model-derived-but-checkable, `[infer]` is model-derived-and-unchecked, and a
PROMOTED fact becomes user-origin in `<project>-decisions.md`.

## 4. Body sections (in this order)

1. `## Entry & routing` — **the highest-value section; write it first.** A table
   `I want to <task>` → `start at <path>` → `<tag>`. This is what replaces the
   from-scratch hunt every session, and it is what a diagram cannot express.
2. `## Shape` — the diagrams from the catalogue in §5.
3. `## Facts` — tagged assertions that do not fit a diagram: build/test/run
   commands, external services, redlines, known-broken areas.
4. `## Open [infer]` — the promote queue. **Traditional Chinese** (this is the
   section the user rules on); everything above is English.

## 5. Diagram catalogue (the read-time replacement for hand-drawn diagrams)

A hand-drawn mermaid diagram is a write-time artifact: it drifts, and nothing
detects the drift. The same diagram DERIVED from the repo and carried under this
file's fingerprint keeps every advantage of mermaid — human- and LLM-readable,
diffable, zero dependencies, high token density — and gains regenerability. That
is the whole trade: **stop drawing them, start generating them.**

Six principles, then the closed catalogue.

- **P1 One diagram, one question.** Every diagram's heading IS the question it
  answers. If the question cannot be written, the diagram is decoration — omit it.
- **P2 Closed catalogue, not free-form.** Free-form drawing is not reproducible,
  and a non-reproducible artifact cannot be a read-time artifact. Each entry
  below fixes its derivation source, so two regenerations agree.
- **P3 Node caps are hard.** Over the cap, AGGREGATE to the next level up — never
  draw a bigger diagram. Both humans and LLMs lose a mermaid graph past ~15
  nodes (a force-directed graph fails the same way, just later). When a cap
  fires, the line under the diagram reads `aggregated: <N> items → <M> groups`
  so the folding is visible rather than silent.
- **P4 Nodes are locators.** Node ids are repo-relative paths. The diagram then
  doubles as a routing table, and every claim in it is checkable.
- **P5 A diagram inherits its source's tag.** Put the tag on the heading line.
  SHAPE-1..3 are structural (`[git]`/`[read]`); SHAPE-4..6 need semantics and are usually
  `[read]`, sometimes `[infer]` — an `[infer]` diagram is a hypothesis drawn in
  boxes, and must be labelled as one.
- **P6 Draw what IS, never what SHOULD BE.** The intended architecture is
  write-time and belongs in `<project>-decisions.md`. A read-time diagram that
  quietly draws the intent loses the only thing this layer is for: the gap
  between the two is the finding (§H conflict rule, row 3).

| id | question it answers | mermaid type | derived from | node cap | skip when |
|---|---|---|---|---|---|
| **SHAPE-1** | What parts is this made of? | `graph TD` | directory structure + package manifests | 15 | never — SHAPE-1 is mandatory |
| **SHAPE-2** | Which way does the flow go? | `flowchart LR` | import/require direction, aggregated to module level | 12 | single-module project |
| **SHAPE-3** | Where does the outside get in? | `flowchart LR` | entry points: `bin`, `main`, routes, handlers, CLI args | 10 | no external surface |
| **SHAPE-4** | How does the stateful part move? | `stateDiagram-v2` | state enums/constants + the functions that transition them | 8 states | **no real state machine — do not invent one** |
| **SHAPE-5** | What happens in one typical operation? | `sequenceDiagram` | trace one primary path from a SHAPE-3 entry point | 6 participants | non-interactive tool |
| **SHAPE-6** | Where does it touch the outside world? | `flowchart LR` | network, filesystem, DB, subprocess call sites | 10 | pure library |

Rendering rule: always a fenced ` ```mermaid ` block, never an exported image.
The text IS the artifact — that is what makes it diffable, LLM-readable, and
free of a render dependency.

SHAPE-4 carries the most common failure: a project with a few enum constants is not a
state machine, and drawing one produces a confident fiction. Skip it unless the
transitions are actually enforced somewhere in code, and cite that place.

## 6. STALE algorithm (accurate variant — scoped to `covers`)

```
1. recorded  := header generated-from
2. git merge-base --is-ancestor <recorded> HEAD   # exit 1 => rebased, force-pushed,
   non-zero exit                              -> STALE, unconditionally  # or wrong repo
3. changed   := git diff --name-only <recorded>..HEAD
4. relevant  := changed ∩ covers − excludes
5. verdict:
     relevant = 0                             -> FRESH    (trust it; no scan)
     1..5 and none structural                 -> DRIFT    (read the diff, patch
                                                           the map; do not rescan)
     >5, or any structural path touched       -> STALE    (regenerate)
```

`structural` = a package manifest (`package.json`, `pyproject.toml`, `go.mod`,
`Cargo.toml`, …), or any directory added or removed — these invalidate SHAPE-1, and a
SHAPE-1 that is wrong makes every other section unreadable.

**The threshold 5 and the structural list are provisional guesses (2026-08-13),
not measured** — the smallest thing that could work, shipped as a declared guess
rather than picked silently.

**If you just ran a cycle on any project, you are the measurement.** Append one
line to `ops/rule-registry.md`, key `map STALE thresholds`, in its `evidence:`
field: `<date> <project>: <N> relevant files → patch|regen was cheaper`. Three
agreeing lines replace `current` there and here. Do this from whatever project
you are in — the registry is project-independent precisely so the observation
has somewhere to land; the T-010 ticket in `claude-config` is the schedule, not
the destination, and is invisible from here.

Scoping to `covers` rather than "any commit" is the cheap accuracy win: a commit
touching only docs must not invalidate a code map.

## 7. Promote / demote (the only way the map improves)

- **Promote**: an `[infer]` confirmed by the user or by evidence is written into
  `<project>-decisions.md` as a `D-NNN` (or `<project>-context.md` if it is a
  term) **and deleted from the map**. It has become an unexpiring fact and must
  stop living in an expiring file. **The map shrinking over time is the system
  learning** — a map that never shrinks means promotion is not happening.
- **Demote**: a write-time record found stating something re-derivable (which
  files changed, what the structure is, which modules exist) has it removed
  there — the map covers it, and the write-time copy is an undetectable drift
  source. This is `60-bootstrap.md` §H's "never write what is regenerable".
- Never the reverse: a map is never edited to match a decision. Regenerate it
  and let the difference surface as a finding.

## 9. Write interface — the only three legal writes, and who fires them

A generated file that a promote step also deletes lines from is not "read-only";
saying so and then editing it is how the ban stops being obeyed. So the contract
is not "never write" but **"only these three writes, each with a defined effect
on the fingerprint"**:

| write | what it does | fingerprint | fired by |
|---|---|---|---|
| `generate` | full rewrite from a fresh scan | set to `HEAD` | cold start (§H trigger), or a STALE verdict |
| `patch` | targeted edit reflecting a small diff | **advanced to `HEAD`** | a DRIFT verdict |
| `prune` | delete one promoted `[infer]` line | **unchanged** | a promote (§7) |

The rule that makes those three consistent: **`generated-from` records what the
map's CONTENT reflects, not when the file was last touched.** A `patch` changes
what is reflected, so the fingerprint moves. A `prune` removes something that
moved to a write-time file — coverage is identical, so the fingerprint must NOT
move. Advancing it on a prune would silently launder unscanned commits into
FRESH, which is the one failure this whole layer exists to prevent.

Any other write is a hand edit. There is no fourth class and no "small fix"
exception: the moment a map is worth hand-editing, the content belongs in a
write-time file — promote it (§7).

### Mounts — which ritual keeps this alive

`60-bootstrap.md` §E and §G are kept alive by the checkpoint sweep. The map
cannot use the same mount for everything, because **its acts split across both
time semantics**, and hanging a read-time check on a phase-end ritual is the
category error this layer is about:

| act | time semantics | fires at | mounted in |
|---|---|---|---|
| verify (FRESH/DRIFT/STALE) | read-time | **session start**, before the map is read | `60-bootstrap.md` §A step 1; `workflow-checkpoint` §C step 1 |
| `generate` / `patch` | read-time | immediately on the verdict | same as verify — inline, not a ritual |
| `prune` (promote) | write-time | a fact got confirmed | `workflow-checkpoint` step 5c |
| demote | write-time | a regenerable fact is found in a write-time file | `workflow-checkpoint` step 5c |

**Verify strictly before read.** Reading a map and then checking it has already
spent the tokens on possibly-stale content — the check exists to avoid that read,
so an unverified map read is the mechanism running backwards.

The verdict is not a new ritual to remember: it is a **P-env premise**, and §G's
`## Now` block already requires re-confirming P-env at the start of every session
on a continuing task (global CLAUDE.md premises rule, `30-judgment.md` R2).
Report it in that same block — one line, beside the other premises.

## 10. Proof of life (`40-maintenance.md` §4.2)

```powershell
Get-ChildItem ~/.claude/references/*-map.md | Select-Object Name, LastWriteTime
```

Empty result after a cold-start session means §H did not fire — check its
trigger wording before assuming no project needed one.
