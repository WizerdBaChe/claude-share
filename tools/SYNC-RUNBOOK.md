# SYNC-RUNBOOK — running a refresh round

Written for the agent that runs the next round. `COLLECTION-RULES.md` is the
decision procedure and wins on any conflict; this file is the ORCHESTRATION
around it — the part every round before 2026-09-12 rebuilt from memory: how to
sort the delta, how to split it into lanes, what a lane brief must carry, how
to merge, and what closing out means. Nothing here is a new rule; each step
points at the rule it serves.

## 0. Record the source state, then sort the delta

```git bash
git -C ~/.claude rev-parse --short HEAD
git -C ~/.claude status --porcelain
python tools/triage.py --source ~/.claude
python tools/share_gate.py --source ~/.claude
```

- The first two are COLLECTION-RULES Step 0. Keep the sha; closing out
  compares against it.
- `triage.py` sorts every changed or uncommitted source path into the
  procedure it needs, using only what the manifest already declares. Its
  baseline is `source_aligned` in `share-manifest.toml`. It reaches no verdict.
- The gate run with `--source` is the drift baseline: every `[V]` finding is
  a collected file the round must refresh.

| triage bucket | what the lane does |
|---|---|
| `refresh` | procedure B — the `edits` list is the specification; `dirty` means a `source_dirty_ack` |
| `source-gone` | report it; the lane does not delete the repo copy — main decides |
| `candidate` | the seven-row decision table; ship → procedure A, else a disposition |
| `recheck` | re-verify the covering `[[not_shipped]]` entry per FILE (hard rule 5) |
| `never` / `uncommitted` | nothing, unless its `cited` count is non-zero (decision row 2) |
| `deleted` | nothing |

## 1. Split into lanes

A lane is one worker over a disjoint set of SOURCE paths, in its own git
worktree. Split by coupling, not by directory:

- **A mechanism that spans roots is one lane.** 2026-09-12: the
  literature-access rule, its hook, the hook's policy table and the skill-side
  loader went to one worker, because deciding them separately can ship a hook
  whose policy file does not ship.
- **Each lane owns the authored docs its files make false** (`hooks/README.md`
  and the settings template with the hooks lane, a skill inventory with the
  skills lane, and so on). Name them in the lane prompt.
- **Main owns** the root `AGENTS.md`, `README.md`, `CHANGELOG.md`,
  `ADOPTERS.md`, and everything in `tools/` except the lanes' own manifest
  entries.
- **An excluded directory that grew gets a read-only adjudication lane**
  instead of a collecting one (2026-09-12: the source `tools/`). Its output is
  a per-file verdict table the round acts on after it lands.
- Roughly 25 shipped files per lane is where earlier rounds stayed readable.

The 2026-09-12 round used eight lanes: ops top-level, ops references plus the
record-directory dispositions, CLAUDE.md template plus rules plus interop,
hooks, agents plus skills, the literature mechanism, archdiag plus the
capability-set rebuild, and the `tools/` adjudication.

## 2. Brief every lane from one template

Appendix A is the template; copy it to the session scratchpad, fill the round's
two shas, and give every lane the same file plus a short lane prompt (paths,
maps, lane-owned docs). The template carries what `claude-ops/ops/20-dispatch.md`
§2 requires of a fan-out and of a worker that writes into a governed record:

- the decision procedure, exhaustive down to "this is not mine" — so eight
  workers meeting the same ambiguous shape resolve it the same way;
- hard rule 9 with its ✗/✓ pair — a worker never runs the merge-time gate, so
  the manifest's record-writing rule has to arrive in the brief or not at all
  (2026-09-07: 38 leaks, every one in the manifest);
- the manifest-editing protocol below, so lanes merge mechanically;
- the report contract — a worker that is not told what a report looks like
  fixes instead of reporting.

**Manifest-editing protocol.** A lane edits existing entries in place (only
its own) and appends every new entry at the end of the file inside a
`# === lane … BEGIN ===` / `END ===` block. Git then conflicts only where
two lanes both appended at the end, and that conflict has one resolution:
keep both blocks whole.

## 3. Merge

1. Merge lanes that share no file first; the hooks lane and any lane that adds
   a hook mount last. `git merge --no-ff <lane branch>`.
2. Manifest conflicts at the end of the file: keep every lane block whole.
   Settings template or hook table conflicts: take the union of mounts/rows.
3. **Cross-lane races.** For every verdict of the form "absent, so dropped" in a
   lane report, check whether another lane shipped that target. 2026-09-07 had
   two such reversals, each an honest verdict the parallel round made false
   before it landed. The reports' Cross-lane section is the input; the merge is
   the only place that sees both sides.
4. `git worktree remove` each lane worktree once its branch is merged.

## 4. Close out

```git bash
python tools/share_gate.py --source ~/.claude
python tools/test_share_gate.py
python tools/test_triage.py
```

- The gate must exit 0 with the source mounted. A `[V]` line saying "declared
  edited, but byte-identical to the source" means a lane dropped its edits.
- **Counts in prose.** Check S4 compares the two skill-inventory tables with
  the tree; nothing else is checked. Update by hand: hook count (`AGENTS.md`,
  `README.md`, `hooks/README.md`), agent count, rules count, skill count in
  README prose.
- **Source untouched**: `rev-parse` against the Step 0 sha; if it moved, say
  what moved and whether any collected path was in the delta.
- **`CHANGELOG.md`**: what came in, what was edited, what was excluded, what
  the audit disproved, what was deferred (COLLECTION-RULES step 9). In the
  same commit, set `source_aligned` to the sha the round aligned to — the
  baseline is a summary of that entry and must not move on its own.
- **Push only on an explicit yes from the owner.** The repo is public; a
  round that is green is ready to publish, not published.

## Appendix A — the lane brief template

Fill `<ROUND-DATE>`, `<OLD-SHA>`, `<NEW-SHA>`, then save it where the workers
can read it. Lane prompts add: the lane id, its source paths, the source →
repo maps they need, and the authored docs the lane owns.

> **Goal.** This repo publishes de-identified copies of a private source
> environment (`~/.claude`, "the source"). It was last aligned to source
> commit `<OLD-SHA>`; the source is now at `<NEW-SHA>`. Your lane is one
> disjoint slice of that delta. Every shipped file must match the source again
> except for DECLARED edits, every new source file your lane owns reaches a
> verdict, and nothing private is published — including in the manifest's own
> prose. The repo's rules win over this brief.
>
> **Read first**: `tools/COLLECTION-RULES.md` (all of it); the existing
> manifest entries for your paths; two or three entries to learn the field set.
>
> **Decision procedure — apply to every path in your lane list.**
> D0 not in your list → do not touch; note dependencies under Cross-lane.
> D1 has a `[[collected]]` entry → procedure B: recover the `edits` list,
> copy the source over, re-apply every edit anchored on re-read text, scan the
> new content for new scrub targets, diff with line endings normalised — the
> diff must equal the edits list; update the entry in place.
> D2 covered by a `[[not_shipped]]` entry → re-verify it against the current
> source per file; still right → append a dated per-file re-check note when a
> file is new under a directory entry; wrong → correct it and keep the history;
> renamed source path → fix the entry's `path`.
> D3 new file → the seven-row table; ship → procedure A (read every byte, copy,
> diff, new entry); not ship but cited by a shipped file → a `[[not_shipped]]`
> entry with a real `fallback` AND an edit to whatever routed to it.
> D4 the source deleted a collected file → report; do not delete.
> D5 a real defect in source content → report; never edit the source, never
> "fix" the copy beyond a declared edit.
> D6 untracked at the source → do not collect; a modified collected file →
> align to disk and add a dated `source_dirty_ack` with the numstat.
>
> **Scrub only**: account names; absolute home paths; absolute paths on a
> non-system drive; private hosts; credentials; pointers to private assets
> (session ids, scheduled-task names, named artifacts in non-shipping trees).
> **Never scrub** a path that resolves, a filename, a project name, a ruling
> id, a lesson id, a dated evidence line.
>
> **Hard rule 9.** The manifest is published. Record the CLASS and POSITION of
> what you removed, never the value:
> ✗ `"line 12: <the real private path, spelled out> -> <vault>"`
> ✓ `"line 12: the vault root, an absolute path on a non-system drive, -> <vault> (the tail resolves and is kept)"`
> The same holds for session ids, full commit shas, task names and account
> names, in prose about an exclusion as much as in `edits` arrays.
>
> **Manifest protocol**: edit your own existing entries in place; append new
> entries at the end of the file inside a `# === lane <ID> <ROUND-DATE> BEGIN ===`
> … `END ===` block; never reorder or touch anything else.
>
> **Main owns** the root docs and `tools/` (except your manifest entries).
>
> **Verify in your worktree**: the gate with `--source` — every finding on
> your lane's files must be gone; list only your-lane residue. Run any test
> that ships next to a file you changed. You check format and gate
> cleanliness; main checks acceptance.
>
> **Commit** once on your worktree branch, message via `git commit -F`; do
> not push, merge or touch `main`.
>
> **Redlines**: never write under the source; never edit outside your list;
> never push; never `--no-verify`; never send content to an external service.
>
> **Report** (≤ 70 lines, this order): summary; per-file table (source, repo,
> D-branch, verdict, edit count, note); counts for main; cross-lane; gate
> output for your lane; honesty clause (skipped, unreached, unsure — unsourced
> numbers labelled "unverified"); branch, commit, worktree, and the source
> HEAD at your start and end.
