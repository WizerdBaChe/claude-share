# Shared-tree git — one tree, several sessions (owner: `20-dispatch.md` §7a)

Detail file for `20-dispatch.md` §7a and the canonical home of the discipline
`ops/lessons.md` L-023 (hits 1-3) was written about. The RULE lines stay in §7a;
this file holds the routing ruling, the commit ritual in full, the checks, the
recovery recipes and the measured incidents. Loaded on demand. Every recipe
below was used on a real incident in `~/.claude` (2026-08-17, 2026-08-21 ×2).

## 0. What is shared, and what each kind of damage looks like

HEAD, `.git/index` and the working tree are SHARED MUTABLE STATE between every
session in one working tree. No git command errors when another session moves
them; the damage is visible only in a later commit's branch name or file list.

| shared state | what one session does | what the other session sees | loud or silent |
|---|---|---|---|
| HEAD | `git checkout -b` / `checkout` | its next commits land on the peer's branch | loud — the branch name in the commit's output line (hit 1, hit 2) |
| `.git/index` | `git update-ref` / `git branch -f` WITHOUT a following checkout | its next commit serializes the stale index: every path HEAD has and the index does not is recorded as a DELETION — 52 files, no error, ancestry checks still pass (hit 3) | silent |
| working tree | leaves an edit uncommitted | whoever stages that path next ABSORBS the edit under their own commit message — content correct, provenance gone, every check green | silent |

The general form of hit 3 is worth more than the git detail: hit 2's fix
removed a LOUD failure (wrong branch) and replaced it with a SILENT one
(content deleted while ancestry reports health). A mitigation that moves a fault
from visible to invisible is a downgrade even when it removes the original
symptom. Ask of any concurrency fix: what shared state does this NOT
synchronise, and how would I see it?

## 1. Routing ruling — concurrency in `~/.claude` is routed by COUPLING CLASS

User ruling 2026-08-17. Not a blanket worktree-vs-shared choice.

- **Same workstream split into two tickets** (the hit-1 incident: both edited
  skill descriptions, both refit calibration.json, both wrote the same
  PROJECTS.md row): **SERIALIZE.** Baton-pass — ticket N merges to main and
  syncs instruments BEFORE ticket N+1 branches from fresh main. Latency, not
  correctness, is the cost.
- **Same repo, disjoint domain, no live verification needed** (ops docs,
  retrospectives, tool code whose tests use fixture trees): the second session
  takes a worktree (`git worktree add`, convention `.claude/worktrees/`); the
  canonical tree stays with whoever needs live reads.
- **Work that must verify against the LIVE environment** (description
  metrology, hook behaviour): canonical tree only, at most ONE writing session.
  Worktrees cannot verify it — `trigger_probe.py ProbeEnv.default()` and
  `skill-routing-audit.py` read `Path.home()/.claude`, and the runtime loads
  skills/hooks from the canonical path, never from a worktree.
- **True parallelism**: split by TREE (one session in a project tree elsewhere,
  one in `~/.claude`), never by ticket within one workstream.

Standing conventions either way: `calibration.json` refit+commit is a
POST-MERGE step on main, never a per-branch commit (the hit-1 branch-side fits
serialized only by luck); before mutating a possibly-shared tree, glance
`git reflog -3` — foreign movement within minutes means the tree is shared, so
downgrade to serialize-or-worktree.

**Finding and hailing the peer** needs no user relay: `ccd_session_mgmt
list_sessions` finds live sessions (filter by cwd — but CWD DOES NOT TELL YOU
WHO WRITES TO A GIVEN GIT TREE, see §4), `send_message` delivers a labelled user
turn into one ("From {sender title}", with a backlink) — use it to declare
presence or baton-pass. It cannot reach unattended (scheduled/remote) sessions;
an idle session reads it on resume.

**Do not stop and report "another session is blocking progress".** A session
that finds a peer live in this tree reads this file and runs the checks below;
concurrency here is NORMAL. That hand-back stalls the user on a condition this
file already answers, and it has happened. Waiting is valid only when the
coupling class actually calls for serialization; it is never the default, and
never something to ask the user to resolve.

## 2. The commit ritual (every commit in a possibly-shared tree)

1. `git branch --show-current` — NOT `git status --porcelain` (prints no branch
   at all) and NOT `git log --oneline -1` (answers WHETHER a commit landed,
   never WHERE: a bare tip hash is identical for "I am on main" and "my branch
   points where main points", which is exactly the moment a peer branches off;
   hit 2 ran both neighbours of the right command and not the command).
2. Stage explicit paths. Never `-A`. `git add <path>` refreshes only the paths
   named, so a `git status` SCOPED to those paths reports clean even when the
   rest of the index is stale — run `git status --porcelain` UNSCOPED if you
   want the index's true state (a stale index shows the missing paths as staged
   deletions).
3. `git commit -F <msgfile>`, never `-m` with a message that may contain `"`
   (L-021; PS 5.1 does not escape embedded quotes and the commit silently does
   not happen).
4. **`git show --stat HEAD` and read the file list for what you did NOT write,
   not for what you did.** 52 deletions in a two-file commit is unmissable;
   a peer's absorbed edit is the quieter case — "my files are all here" passes
   straight through it, only "nothing here is unaccounted for" catches it.
5. `git log --oneline -1 <the branch you intended>` — name the branch in the
   verification rather than reading a bare tip.

**Merging two branches that both APPEND to an ID-bearing ledger**
(`ops/lessons.md` L-nnn, ticket ids, label families): the merge can succeed
textually while both sides minted the same next-free ID — no conflict marker,
two entries share a number (2026-08-27: two different `L-033`s, one per
branch, discovered only by a full read during the trim pass). After any merge
that touches such a ledger, grep it for duplicate ids
(`[regex]::Matches($raw,'(?m)^## (L-\d+) ')` grouped, count >1) and renumber
the side nothing cites by number — the citation graph, not entry age, decides
who keeps the id.

**Do not `git checkout -b` while a peer is live in the tree.** Additive,
zero-behaviour-change work goes straight onto the current branch; anything
larger waits for the baton-pass in §1. If you must publish by moving a ref
(`git update-ref`, `git branch -f`), FOLLOW IT WITH `git checkout <branch>`,
which refreshes the shared index — or accept that step 4 is the only thing
between the next session and 52 silent deletions.

## 3. Verifying SOMEONE ELSE'S publish — ancestry and content are different questions

`git merge-base --is-ancestor <sha> HEAD` proves the commits are reachable. It
says NOTHING about whether their content is present in HEAD's tree — hit 3's
nine commits stayed ancestors throughout while 52 of their files were gone.

The executable form of the content question:

```powershell
git cat-file -e <sha>:<path>                 # a file you know should be there
git ls-tree -r --name-only HEAD | Measure-Object -Line   # against a known count
```

Used 2026-08-21 to clear the five commits that landed during the incident
window: 0 file deletions recorded, all 52 paths `9d56150` restored present in
HEAD, tracked count 660 → 663 accounting exactly for three added files. Note the
52: the first pass counted 47, having measured only the ADDED paths and reported
the number as though it covered the whole restore — 5 modified paths went
unchecked. Scope the filter to the question, and say which filter the number
came from.

## 4. Attribution — identify a commit by what it TOUCHES

`list_sessions` reports a session's cwd, and cwd does not tell you who writes
to a given git tree: commit `2957b25` came from a session whose cwd was
a project work root elsewhere; its `git show --stat` was the tell (it touched `ops/lessons.md`
beside the bench-claude-arms retrospective files). The attribution ticket of
2026-08-21 got this wrong THREE times in one night, twice by cwd inference and
once a message AFTER writing the corrected rule down — a mis-addressed
all-clear is worse than none, because it reads to the recipient as "someone
checked".

Scope limit: "by what it touches" works on COMMITS. An uncommitted working-tree
edit touches nothing yet; there is no object to inspect. A dirty file in a
shared tree is genuinely unidentifiable from outside — so the attribution of
uncommitted work can only be carried by WHOEVER COMMITS IT:

**If you must commit a path a peer has dirty, carry their provenance in the
commit message and stage nothing else of theirs.** Do NOT write the rule as
"never commit a file a peer has dirty" — that MAXIMISES absorption: the edit
sits there until the next session stages the path blind and cannot attribute
what it never knew was there. Worked example `05a1b95` (2026-08-21): a session
needing to edit `ops/lessons.md` found 57 lines of a third party's uncommitted
work already in the file, committed anyway, and spent a PROVENANCE paragraph
naming those 57 lines against its own 40 — identifying them by the artifact
they belonged to, not by guessing the session — and deliberately did not stage
that party's other dirty paths. Nothing was lost.

A two-party baton does not settle a tree with three parties in it: two sessions
each declared "I am done writing to git here" while a third was actively
writing. They had asked each other, not the tree. `git status --porcelain`
(unscoped) is the tree's answer; the session-start nudge (`ops_health_nudge.py`
check 14) prints the stale part of it.

## 5. Recovery recipes (pick by detection lag)

- **Caught within ONE commit, peer holds zero commits of its own** (hit 2):
  `git branch -f main <sha>` is sufficient and complete — main fast-forwards
  over the stranded commit, the peer's branch is left level and ready, HEAD is
  NOT moved (moving it would redirect the peer's next commit, i.e. commit the
  same fault against them), and the working tree never changes. Assert both
  preconditions immediately before: `git merge-base --is-ancestor main <sha>`
  and `git log main..<peer-branch>` contains ONLY your own commit.
- **Peer has already committed on the redirected branch** (hit 1): a plumbing
  merge — `git commit-tree` + atomic `git update-ref` — lands the stranded
  commits into main without touching the other session's HEAD or uncommitted
  files; the later normal `merge --no-ff` is then clean (criss-cross graph, no
  duplication). Never rebase/cherry-pick the foreign commits out.
- **Stale-index deletions** (hit 3): restore from the working tree, which was
  never touched, as an ADDITIVE commit (`9d56150`) — never by reverting the
  peer's commit, which also carried their real work.
- After ANY recovery: run §3 on the result, not just `--is-ancestor`.

## 6. Incident record (pointers, not narrative)

- hit 1, 2026-08-17: `ops/lessons.md` L-023 (detail: `lessons-detail.md` §L-023).
- hit 2, 2026-08-21: commit `3121530`; the two neighbouring commands that looked
  like diligence.
- hit 3, 2026-08-21: the 52-file deletion and its additive restore `9d56150`;
  provenance of the write-up in `lessons-detail.md` §L-023; the content check
  that cleared the window, §3 above.
- absorption, 2026-08-21: commit `05a1b95` (the worked example in §4); the
  attribution ticket `task_406a32d8`.
