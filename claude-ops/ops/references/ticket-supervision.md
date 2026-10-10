# Supervising a dispatched ticket — registration fields, board authority, shared-tree lines

Extracted 2026-10-08 from `ops/20-dispatch.md` §7a (size cap). The rule and
its conditions stay in §7a; this file holds the field-by-field detail, the
authority table and the shared-tree lines with their incidents.

## Why registration happens AT dispatch time

A dispatched session cannot be identified after the fact — two id namespaces
nothing on disk joins, and transcripts contaminated by cross-session messages
so only the OPENING user turn binds cleanly (measured 2026-08-21; evidence in
`tools/session-board/README.md`).

Registration is mechanised: `hooks/session_board_register.py` writes the
entry on PostToolUse of `spawn_task`, taking `task_id` from the response and
`title`, `cwd` and `match` from the call — the only real dispatch surface
(measured counts and why `Agent` is not one: the source's own dispatch-surface
sweep script under its session-board tooling, not shipped here). Steps 2 and 3 below used to
be prose in §7a, and prose is what this repo measured failing (L-011 hit 3,
L-023 hit 2).

> **Share note.** Neither half of that mechanism ships here: the registering
> hook (`hooks/session_board_register.py`) and the ticket board it writes into
> (`tools/session-board/`) are both declared in `tools/share-manifest.toml`
> under `[[not_shipped]]`. In this share the registration steps below are done
> BY HAND — which is what the source did before 2026-08-21. Only the question
> of who writes the row changes; every field, and the reason each one exists,
> is unchanged.

## The three things still owed by the dispatcher

1. **Open the prompt with a sentence that appears nowhere else**, and never
   quote another ticket's opening sentence in a message. The hook copies that
   first line verbatim into `match`; it is still yours to make distinctive.
   (It cuts the phrase before any character JSON escapes, and writes
   `match: null` rather than a weak one — the board then says UNBOUND, which
   is correct.)
2. **Fill in `deliverables` — the one field a machine cannot infer.** The hook
   writes `null`, which the board prints as `NOT DECLARED` in magenta with
   the edit to make. Replace it with the paths the ticket must produce, or
   with `[]` if it deliberately has none (e.g. "commit these paths") and put
   the verification command in `note`. `[]` and `null` are different states
   on purpose: `[]` says you decided, `null` says nobody has. Inventing a path
   to watch is still worse than watching nothing.
3. **Check the cwd if the ticket is started in a worktree.** The hook records
   the cwd passed to `spawn_task`, or the dispatching session's if none was
   passed; a worktree session's real cwd differs and the board will report
   UNBOUND until you correct it.

If the board says `UNBOUND` for a ticket you just dispatched, the hook did not
run — check `telemetry/session-board-register.jsonl` and
`ops/references/integrity-sweep.md` check 22; do not re-add the entry by hand
and leave the cause in place.

## Division of authority while supervising

Run `tools/session-board/session-board.ps1 -TicketFile ...` twice a few
minutes apart. Neither side can answer the other's half:

| question | authority |
|---|---|
| is it still running? title? `local_` id? | `ccd_session_mgmt list_sessions` |
| which transcript is which ticket? quiet for how long? what did it produce? | the board |

**Never read completion from silence.** A quiet transcript cannot be told
apart from stuck, waiting-on-permission, or thinking; raising the threshold
only moves the misjudgement later. Judge by the deliverable — `ops/lessons.md`
L-025 (B4), where a monitor that trusted silence harvested an empty
deliverable. `QUIET + deliverable ABSENT` is a session to go and look at, not
a finished one.

## A tree with a peer in it shares HEAD, `.git/index` AND the working tree

Each line measured on a real incident (2026-08-17, 2026-08-21 ×2):

- Do not `git checkout -b` while a peer session is live (it moves their next
  commit onto your branch); additive work goes onto the current branch.
- A ref move (`git update-ref`, `git branch -f`) WITHOUT a following
  `checkout` leaves the shared index stale: the next commit anywhere records
  unknown paths as DELETIONS. Ancestry and content are different questions.
- After ANY commit in a shared tree: **`git show --stat HEAD`, read for what
  you did NOT write** — deletions, and the quiet case, ABSORPTION of a peer's
  uncommitted edit. A path a peer has dirty is committed with their
  provenance.
- Verify SOMEONE ELSE'S publish by content (`git cat-file -e <sha>:<path>`),
  not `--is-ancestor`.

The incidents behind each line, routing by coupling class, the commit ritual,
attribution (by what a commit TOUCHES) and the recovery recipes:
`ops/references/shared-tree-git.md` (the canonical home of `lessons.md`
L-023).
