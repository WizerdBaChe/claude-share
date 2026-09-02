---
name: mechanism-share-packaging
description: >-
  Exporting a BEHAVIORAL MECHANISM — an operating mode spanning hooks, tools,
  wiring, and docs — from a live agent environment into a governed share repo,
  plus a self-sufficient hand-off bundle. Trigger on
  「把這個機制/運作模式打包分享」「這套機制輸出到 share repo」"export this
  mechanism", "package this operating mode". ONE skill crossing the machine
  boundary → skill-share-packaging. Auditing/adopting a foreign rules layer →
  config-self-audit adoption mode. This skill ORCHESTRATES; the target repo's
  own collection rules stay authoritative and are never restated here.
---

# Mechanism Share Packaging

A mechanism is not a file. It is a set of files that only works as a set — an
event pair bridged by a state file, a hook that shells out to a tool, a card
whose discipline a guard enforces — plus the doc that explains WHY and the
checklist that proves it works. Exporting one is therefore not "copy the
files": it is scoping the set, landing each file where the target repo's
structure says it belongs, and sweeping every ripple the arrival causes.

First live run: compact-recovery, 2026-08-16 (4 collected files, 2 authored
docs, 9 gate findings swept to 0 in three loops). The ripple checklist below
is that run's findings, generalized. Second run: red-team, 2026-08-17 (7
collected files, 2 authored docs, 1 gate finding, 1 disposition narrowed from
`excluded-by-decision` to `partial`) — its findings are in "Failure modes seen
live", and the checklist held without amendment. Third run:
architecture-diagramming, 2026-08-27 (5 collected + 8 in-scope refreshes +
2 authored, plus 23 source-drift refreshes forced by the gate's source
comparison; 34 findings to 0 in four loops; 1 previously-collected file
un-shipped) — findings below; the
checklist held, with one refinement to the counts item.

## Hard rules

1. **Delegation, not duplication.** The target repo's collection rules,
   de-identification boundaries, and publishing gate are AUTHORITATIVE. Read
   them first; never restate their content in this skill or in your head — a
   second copy of a rule is a fork that drifts (the sharelib incident: two
   leak-pattern lists, one missing two classes for a month). No governance at
   the target → seed it from `references/governance-starter.md`, then follow
   what you seeded.
2. **The source environment is read-only.** Record its SHA before, re-verify
   after. A source fix that would make something "shippable" is a separate,
   user-approved task — never a packaging side effect.
3. **Byte-verbatim first, then declared edits.** Copy exact bytes; apply
   de-identification as surgical edits; the per-file diff against the source
   must equal the declared edit list EXACTLY — no more, no less.
4. **The mechanism travels with its acceptance.** A mode that shipped without
   its real-fire checklist is a mode the adopter cannot verify. Carry the
   checklist the mechanism actually passed, genericized, marked with which
   items the source environment already verified and which remain open.
5. **Bundle ≠ publication.** The zip is a convenience artifact: built at the
   repo root, gitignored, mirroring repo layout so relative links survive.
   The repo publishes files and commits. Pushing is a user decision.

## Procedure

**M0 — Read the target's law.** Its collection rules, manifest format, gate
invocation, commit/merge conventions, and any structural invariants stated in
prose ("the template mounts every hook and nothing else"). List the invariants
you found — M5 checks against this list.

**M1 — Record source state.** SHA + dirty paths. Dirty paths that are not
collection candidates: name them and proceed. Dirty collection candidates:
stop — you would be collecting something committed nowhere.

**M2 — Scope the mechanism.** Walk it as a runtime, not a directory: which
event fires what, what each piece shells out to, what state bridges them,
which doc states the discipline. INCLUDE what the mechanism cannot run or be
verified without; EXCLUDE what merely lives nearby (compact-recovery shipped
preserve.py and left the other 278 files of its parent product behind — with
the parent's exclusion entry amended, not deleted). Write the scope list down
before copying anything.

**M3 — Place each file.** An existing layer that already homes this file
class beats a new folder (hooks went to `hooks/`); the mode's own docs and
its orphan dependencies get one self-contained share folder. Check placement
against every M0 invariant BEFORE copying — placement is what breaks them.

**M4 — Collect.** Byte-verbatim copy → surgical de-id edits per the target's
rules → per-file normalized diff == declared edit list, exactly. References
from shipped copies to things that do not ship (a private registry entry, a
memory note, a scheduled task) are re-pointed at the mode's own README — the
README then carries what the pointer carried (re-check recipes, policy).

**M5 — Author the mode docs.** README: problem shape, the mechanism as an
event/data-flow diagram, economics or invariants that justify it, install
steps incl. optional integrations, a tunables table (parameter → file →
shipped value → sane range), failure modes (what the adopter SEES when each
part is missing), platform-contract notes with re-check recipes, de-id notes.
ACCEPTANCE: the real-fire checklist (hard rule 4).

**M6 — Ripple sweep.** The checklist below, item by item, before running any
gate. Every item is a class that produced a real finding on the first run.

**M7 — Gate loop.** Run the target's full gate (with source comparison if it
has one) until exit 0; run its test suite. A mechanical finding is an
instruction, not an obstacle. A finding about the GATE itself (your new file
class confuses a check) → fix the gate per ITS OWN rules: the fix ships with
a case that fails without it, plus a negative control if you widened or
narrowed a pattern.

**M8 — Close.** Zip (repo-layout mirror, gitignored). Changelog entry in the
target's own voice: what came in, what was edited, which dispositions were
corrected (in place, never deleted), what was deferred. Re-verify source SHA.
Report; push only on the repo's release condition AND user approval.

## Ripple checklist (M6)

Arrival changes the ground it lands on. Check, in order:

- [ ] **Mounting/registration invariants** — templates or loaders claiming to
      carry "every X": add yours, and re-read the claim's wording.
- [ ] **Prose counts** — "nine hooks", "three omissions", "13 of 14" anywhere
      in READMEs, maps, manifest comments. Your arrival just falsified some.
- [ ] **Old dispositions** — every not-shipped/excluded entry that touches
      anything you now ship is now partly wrong. Amend in place with a dated
      correction; deleting history is the failure the entry exists to prevent.
- [ ] **Provenance registration** — a NEW directory of collected content must
      join the roots the collection check scans, on the day it is born.
- [ ] **Authored-vs-collected split** — repo-authored docs beside collected
      files must be whatever the target's checks treat as authored (naming
      convention, exemption list); if no convention fits, extend the check
      per M7, not the doc.
- [ ] **Placeholder tokens** — every `<token>` your docs put in a path or
      command position needs the target's declaration ritual.
- [ ] **Routing tables and indexes** — the repo map, share table, trigger
      dict, or any file whose job is "one line per thing" gains your line.

## Cross-environment adaptation (the 微調 points)

Porting this skill to another machine/repo pair changes exactly three things:
the delegation target (which rules file is law), the root list (what counts
as collected), and the placeholder vocabulary. The procedure and the ripple
classes do not change — they are properties of "arrival", not of any repo.

## Failure modes seen live

### 2026-08-16, first run (compact-recovery)

- Gate reads TRACKED files: a perfect copy that is not `git add`ed reads as
  "does not ship" — stage before gating, and expect provenance findings to
  clear on staging alone.
- A source that moved the same day: the source-comparison check caught the
  repo's copy of a rules file lagging entries added hours earlier — the
  refresh it forced brought identifier classes with it (session ids, a
  second-drive path), each needing the same de-id treatment as the mechanism
  files themselves.
- An authored acceptance doc under a brand-new collected root fired the
  provenance check — resolved by extending the gate's authored-name exemption
  WITH its negative-control test, not by renaming the doc.

### 2026-08-17, second run (red-team)

- **The changelog re-trips the gate that caught you.** M8 asks you to record
  what the gate found; quoting the offending path verbatim makes the record
  itself a live citation, and the same check fires again on prose written to
  document its own fix. The gate cannot tell a post-mortem from a pointer, and
  that is a thing it may not determine, so it may not rule on it — do not
  "fix" the check. Write the incident as description ("cited the reviewer
  subagent under a filename this repo does not carry"), name only the path
  that DOES resolve, and say in the entry why the wrong one is absent. Same
  class for any not-shipped path a disposition is explaining.
- **A hard import of the piece that cannot travel.** The mechanism's most
  load-bearing layer depended on the one file that is machine-bound, at module
  scope — copied verbatim it would `ImportError` on line 41, which is the
  "deny-hook pointing at a missing script" failure with different spelling.
  The fix that stays inside hard rule 3: swap the import for a load-by-name
  seam with a two-symbol contract, default it to the source's own module so
  the source's invocation is byte-unchanged, refuse before any cost is
  incurred, and declare it as the round's one behavioural edit. Verify the
  seam by writing a ~20-line stub — and report that the stub proves the
  WIRING, never that the mechanism works end to end. A mechanism whose live
  layer is prose-only is the `referenced-only` failure the target repo already
  keeps warning about.
- **The dated disposition that was right about the wrong scope.** The whole
  directory had been excluded on reasons that examined only its runtime half.
  Re-check per FILE before believing any `[[not_shipped]]` root, narrow it
  (`excluded-by-decision` → `partial`) with the original reasoning left in
  place, and re-read every entry that DEPENDS on the one you moved — recording
  "still holds, and here is why" rather than leaving it to be re-derived.
- **The count you are not touching may already be stale.** M6 says re-check
  prose counts your arrival falsified; this run found an "N of M skills" claim
  that three unrelated additions had falsified weeks earlier. Report it, do
  not fix it — what ships is the user's ruling, and a packaging round is the
  wrong place to make it.

### 2026-08-27, third run (architecture-diagramming)

- **`--source` makes the round repo-wide — budget for it at M1.** The
  source-comparison check reads EVERY collected file, not the mechanism's: a
  target not source-compared for ten days turned a 13-file round into a
  36-file one (23 lagging verbatim files, each a procedure-B refresh). The
  gate loop is the most expensive place to discover scope, so measure the lag
  at M1 (run the target's source comparison read-only, count the findings)
  and declare the sync as part of the round before collecting anything. The
  B4 read of THAT incoming content — not the mechanism's own files — is where
  the round's real leak findings lived: a session id in a rules file's new
  example, the work-root path in probe payloads and in a measurement
  sentence, and an eighth escaped UUID in a file whose declared edits already
  named seven of the same class. A declared edit list is a spec, and specs
  have escapees: grep the CLASS over the whole file, never just re-apply the
  enumerated instances.
- **The eval side door.** An eval suite is content, not fixture. The target's
  copy had shipped clean as a small generic suite; the source's current
  version had become the routing test harness for the exact knowledge the
  repo withholds — prompts, expected outputs and grading evidence quoting the
  withheld files at row level. Refresh-verbatim exports the withheld
  knowledge; keep-stale misdescribes the copy as verbatim; the verdict that
  stays inside the rules is UN-shipping — reverse the collected entry into a
  not-shipped disposition that narrates the reversal, keep history in git,
  and sweep the indexes that described the skill as shipping its evals.
- **The record re-trips the gate, manifest edition.** The second run's
  changelog lesson, one file over: manifest edit strings and an allow-entry's
  own match field quoted the literals they existed to remove (a path, a
  session id), making the paperwork a finding — or a leak — in its own right.
  The class is "any record OF a removal", not "the changelog": describe the
  removed value by class, write the allow match name-only (the target's
  email-allow carried this fix as a comment all along), and never quote the
  value in the record of removing it.
- **Counts item, one refinement.** "Report, do not fix" (second run) applies
  to sentences the round never touches. When the SAME sentence carries both a
  count your arrival falsifies and one that was already stale, fixing half a
  sentence publishes a false whole — rewrite the sentence true, and log the
  pre-existing half as an audit correction in the changelog entry.
