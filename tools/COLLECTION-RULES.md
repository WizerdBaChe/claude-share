# COLLECTION-RULES

**Read this before adding, refreshing, or removing anything in this repo that
came from the source `~/.claude` environment.** It is the decision procedure;
`share_gate.py` is its enforcement. Written for an agent, so it is imperative:
follow the steps, do not improvise a de-identification policy per task.

## Why this exists

De-identification here was specified verbally, per push. Three failures
followed, all of them found by someone else:

1. **Over-scrub.** `interop-layer/README.md` had 23 real repo-relative paths —
   six distinct filenames — collapsed onto one `<URL>` token, four inside the
   runnable-command fence. The manual could no longer be followed.
2. **Under-declare.** 20+ rule files cited `hooks/*.py` and `settings.json` as
   the mechanism enforcing a rule, while the repo shipped none of them.
3. **Wrong disposition, never re-checked.** Those hooks were then written off as
   "machine-bound" for a month. A 2026-08-14 source audit disproved it: every
   one resolves its paths through `Path.home()` / `expanduser` /
   `CLAUDE_CONFIG_DIR` and contains no machine-bound value at all. They had
   simply never been collected. The largest gap in the repo was a guess nobody
   re-tested.

The lesson is the same in all three: **a judgement made once, in prose, at push
time, decays silently.** Anything durable has to be a declared entry a check can
read.

## Hard rules

1. **Verbatim is the default.** Copy the bytes. Every deviation is an edit, and
   every edit is listed in `share-manifest.toml` `[[collected]] edits`. An
   unrecorded edit is indistinguishable from failure 1 above.
2. **Never scrub a path that resolves.** A repo-relative path, a `~/`-prefixed
   path, a filename — these are not identifiers. Replacing them destroys the
   document and protects nothing. Only an *account name*, an *absolute home
   path*, a *private host*, a *credential*, or a *pointer to a private asset the
   reader cannot open* is a scrub target.
3. **Never invent a placeholder to avoid a decision.** If you cannot say what a
   token stands for, you have not de-identified it — you have deleted content.
   A placeholder in a path or command position must be declared under
   `[placeholders]`, and declaring it asserts a human confirmed the reader can
   fill it in.
4. **Never fix the source to make it shippable.** The source environment is
   canonical and read-only from here. Changes flow source → repo, never back.
   Confirm the source SHA is unchanged when you finish.
5. **A disposition is a claim about the source, and claims expire.** Before
   relying on any `[[not_shipped]]` entry, re-verify it against the source. If
   it is wrong, correct it and say so in the entry — do not delete the history.
6. **A file the rules cite must ship or carry a disposition.** This is the
   completeness criterion. Check R enforces it; do not silence it by deleting
   the citation.

## Decision procedure

Run per candidate asset. Stop at the first verdict that fits.

| # | Ask | If yes |
|---|---|---|
| 1 | Is it in the **never-collect** list below? | STOP — `excluded-by-decision`, record the reason |
| 2 | Does a **shipped** file cite it as a mechanism, rule, or record? | It must reach a verdict below; "leave it out silently" is not available |
| 3 | Does it contain an account name, absolute home path, credential, private host, real project/customer data, or a pointer into a private tree? | Go to 4. Otherwise → **ship verbatim** |
| 4 | Is the sensitive part **incidental** (a comment, one evidence id, one dead pointer)? | **ship edited** — remove only that, list every removal |
| 5 | Is the sensitive part the **rows/values**, while the **structure** is generic? | **ship template** — keep the structure, substitute the values, declare the tokens |
| 6 | Is the whole artifact only meaningful inside that private context? | `excluded-by-decision`, with the fallback the adopter actually gets |
| 7 | Does the source not have it at all? | `upstream-absent` — do not write it here to fill a gap |

Verdict vocabulary is closed: `verbatim` / `edited` / `template` for what ships
(`[[collected]] status`), and `upstream-absent` / `referenced-only` /
`excluded-by-decision` / `partial` for what does not (`[[not_shipped]]
disposition`). Do not invent a sixth or a fifth.

## Never collect

Credentials of any kind · `projects/`, `memory/`, `sessions/`, `history*` ·
`telemetry/` and any runtime log · `backups/`, `archive/`, `audit-archive/`,
`drafts/`, `plans/` · dated internal reports quoting real work ·
`.credentials.json`, `settings.local.json` · anything under a `.claude/`
subdirectory of a skill · `__pycache__/` and build droppings.

Two of these are structural, not judgement calls: check S fails on a tracked
`.claude/`, `__pycache__/` or `archive/` path, and `.gitignore` covers them.

## Procedure

1. **Record the source state first.** `git -C ~/.claude rev-parse HEAD` and
   `git -C ~/.claude status --porcelain`. A dirty source tree means you are
   collecting something that is not committed anywhere — stop and say so.
2. **Read every byte you are about to publish.** Not the head, not a grep — the
   whole file. You cannot certify content you have not seen, and step 3 of the
   decision procedure is unanswerable otherwise.
3. **Copy, then diff against the source, normalising line endings:**
   ```git bash
   diff <(tr -d '\r' < ~/.claude/<path>) <(tr -d '\r' < <repo-path>)
   ```
   The diff must contain exactly the edits you intended and nothing else. An
   empty diff means `status = "verbatim"`.
4. **Write the `[[collected]]` entry** with `source`, `status`, and one `edits`
   line per change, each saying *what* and *why*.
5. **Re-check every `[[not_shipped]]` entry your work touches.** Collecting a
   file usually means an old disposition is now wrong.
6. **Run the gate.** `python tools/share_gate.py` must exit 0.
7. **Confirm the source is untouched**: the SHA from step 1, and a clean status.
8. **Record it in `CHANGELOG.md`** — what came in, what was edited, what the
   audit disproved.

## What the gate can and cannot do

Check C verifies that every collected file declares its source, a valid status,
and at least one edit reason when it is not verbatim; and that no entry points
at a file that is not there.

It cannot verify the copy still matches the source — the source lives on one
machine and this repo does not. That is what the recorded edit list is for: it
makes the diff reproducible by whoever has both. It also cannot judge whether a
`reason` is honest. Steps 2 and 5 above are human-or-model work that no check
replaces; the checks only make skipping them visible.
