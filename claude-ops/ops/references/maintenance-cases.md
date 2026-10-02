# Maintenance protocol — cases, examples and evidence

Detail file for `ops/40-maintenance.md`. The RULES, their conditions and the
routing stay there; this file holds the concrete that motivated them — worked
✅/❌ examples, incident narratives, measured evidence. Each section names the
owning § (and anchor, where the owner has one). Loaded on demand from the
owning pointer, never at session start. Extracted 2026-09-23 under §3 "a size
trigger means EXTRACT" (the owner stood at 27,829 B against the 26K cap); the
text below is moved verbatim, not reworded.

## audit-entry-schema — why `change` is read off the tool

Owner: `40-maintenance.md` §"Where a rule change gets recorded" (anchor:
audit-entry-schema), item 1.

Added 2026-09-06 after three of these in one session
(`ops/lessons.md` L-012 hit 4). The failure is not carelessness: the tool
prints at one grain and the sentence claims another (a COUNT "1 of 8 files
rewritten" becomes a NAME; a test TAIL becomes a TOTAL; the list of files
EDITED becomes the list COMMITTED, which differs whenever one is
gitignored). The wrong half always sits beside a true half, so re-reading
the message confirms it.

## vc-boundary — evidence for the no-force-add rule, and the `references/` ruling

Owner: `40-maintenance.md` §Version-control boundary (anchor: vc-boundary).

**Check 28 born RED.** Evidence: the check was born RED on 2026-09-06 — five
files, three distinct causes (an unanchored pattern eating a test fixture, an
archive subtree six tracked files cite, and the archive NOTEs the blanket
ignore was guaranteed to drop). All three, with the fixes, are in check 28
itself.

**The `references/` ruling lagging its text.** (The "flagged, unruled" wording
stood here for 26 days after the ruling — a rule text and its registry entry
disagreeing is exactly the rot `review-when` exists to stop.)

## §1 — tiering example

✅ A worker drafts an improved dispatch template → main session reviews the
draft, makes the edit itself, backs up, logs it.
❌ A batch-cleanup worker "helpfully" rewrites `OPS.md` while it's in the
directory — a rule-tier write from a sandbox, unreviewed.

## §2 — one lesson, one destination example

✅ Discover a CLI needs a trust flag → one lesson card in `ops/lessons.md`,
and `20-dispatch.md` §3 already covers the class — bump nothing else.
❌ Paste the same pitfall paragraph into lessons.md, dispatch, AND CLAUDE.md —
three copies that will drift apart and contradict each other.

## §2a condition (3) — why Proof-of-life lives in the hook's own docstring

(rewritten 2026-09-08: the old wording said "a line in
`ops/references/integrity-sweep.md`", which made the rule a POSITION in a file
that grows, AP-45; ES-2 read it literally and flagged 11 hooks the sweep already
runs while missing all 5 that declared nothing).

## §3 — cap-value drift found 2026-08-27

Owner: `40-maintenance.md` §3 Triggers bullet and the Constant-binding bullet.

**Triggers bullet.** Check 7 alone never covered the number, which is how the
two rows below sat at 15K and 20K while the hook enforced 19,968 and 28K,
found 2026-08-27. ("The two rows below" = the §3(b) table rows for `ops/*.md`
and `skill-trigger-dict.md` as they stood that day.)

**Constant binding.** That is not a hypothesis: this bullet named sweep check 7
(a `grep` for `getsize`/`len(...)`, which can only see the unit) as *the* drift
check, and under it three cap values drifted across four sites for up to 12
days, including inside the enforcing hook's own docstring (2026-08-27).

## §3 — owner-in-basename: the measured case

Owner: `40-maintenance.md` §3 "A file that exists once PER OWNER carries its
owner in the BASENAME".

Measured 2026-08-27: 14 files named `FUTURE-WORK.md` existed under `~/.claude`
(2 live, 12 in worktrees, archives and backups) and the user could not tell
from a search which skill any of them belonged to. Both live ones were renamed
owner-first that day; the frozen copies were left alone, because renaming
inside `archive/` and `backups/` falsifies a record of what the file was called
at the time.

## §4 — degradation-check example

✅ Quarterly check finds `30-judgment.md` uncited for months → investigate the
routing table first; discover the trigger description is too vague to fire.
❌ "Our red-team has passed everything clean five times running — quality must
be excellent now."
