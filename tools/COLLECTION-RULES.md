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
4. **Reverted decision.** 2026-08-16: a verbatim refresh overwrote six files
   whose repo copies were deliberately *different* — a domain manifest, a
   research fixture, a citation inbox, three sets of notes about a package this
   repo does not redistribute. Every mechanical check passed. The decisions
   existed in commit messages and nowhere a check could read, so re-running the
   default procedure silently undid them. Read rule 1 below before you read the
   word "verbatim" anywhere else in this file.

The lesson is the same in all four: **a judgement made once, in prose, at push
time, decays silently.** Anything durable has to be a declared entry a check can
read. Failure 4 adds the corollary that took longest to learn — **a decision NOT
to take the source's text is exactly as perishable as an edit, and needs the
same declaration.** Nothing distinguishes "we never looked at this" from "we
looked and chose otherwise" except a written entry.

## Hard rules

1. **Verbatim is the default for a FIRST collection, and never for a refresh.**
   Copy the bytes. Every deviation is an edit, and every edit is listed in
   `share-manifest.toml` `[[collected]] edits`. An unrecorded edit is
   indistinguishable from failure 1 above.

   A file that already exists here is not a first collection, and overwriting it
   with source bytes is not "the default" — it is a decision to discard whatever
   the previous round decided. Before overwriting **any** existing file:
   - if it has a `[[collected]]` entry, its `edits` list is the specification.
     Re-apply every line, then confirm the file still differs from the source.
     `share_gate.py --source <path>` (check V) reports "declared 'edited', but
     is byte-identical to the source" — that finding means you dropped one.
   - if it has **no** entry, stop and reconstruct the decision from history
     (`git log --follow -p -- <file>`) before touching it. An undeclared file is
     the case where the mechanism cannot help you, which makes it the case that
     needs the most care, not the least.
2. **Never scrub a path that resolves.** A repo-relative path, a `~/`-prefixed
   path, a filename — these are not identifiers. Replacing them destroys the
   document and protects nothing. Only these are scrub targets:
   - an **account name**, anywhere;
   - an **absolute home path** (`C:\Users\…`, `/home/…`, `/Users/…`);
   - an **absolute path on any non-system drive** — a second-drive work root, a
     private repo, an asset library. Added 2026-08-16, when nine of these
     entered in one refresh and three more turned out to have been published for
     months: the leak patterns knew about home directories and nothing else.
     System roots (`C:\Windows`, `C:\Program Files`) are not targets;
   - a **private host** or a **credential**;
   - a **pointer to a private asset the reader cannot open** — including a
     session id, a scheduled-task name, or a named artifact inside a tree that
     does not ship. Keep the capability description, drop the pointer.

   Project *names*, ruling ids (`D-033`), lesson ids and dated evidence lines
   are **not** scrub targets. They are how a claim stays checkable by the person
   who does have the source, and removing them is failure 1.
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
   Two entries were wrong on 2026-08-16 and both had been read past for weeks:
   `outputs/` was described as scratch when the source had begun tracking it as
   a rule surface, and a `[[collected]]` entry asserted two leak gates were
   identical when one was missing two key patterns.
6. **A file the rules cite must ship or carry a disposition.** This is the
   completeness criterion. Check R enforces it; do not silence it by deleting
   the citation.
7. **Reach a verdict this round.** The vocabulary has no "decide later". If you
   genuinely cannot decide, the entry must say *deferred*, name the question,
   and name what would answer it — and the next round must close it rather than
   restate it. A deferral that survives two rounds has become a decision made by
   nobody, which is failure 3 with better manners.
8. **The source's own words about sharing are evidence.** When a source file
   says which of its parts are personal, that is a first-hand statement and it
   outranks your reading of the file. 2026-08-16: the source's own packaging
   note listed `FUTURE-WORK` / `sample-run` / status files as strip-on-share,
   which settled four candidates in one line. Look for such a note before
   adjudicating a skill or a tool directory.

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

**Row 2 has an inverse that costs more.** If a shipped file *routes* to the
candidate — a manifest row, a load list, an install step — then excluding it
without amending the router leaves the reader following a pointer to nothing.
Excluding is a two-part act: the disposition, and the edit to whatever pointed
at it. On 2026-08-16 a refresh restored twelve real manifest rows for domain
profiles that do not ship, turning a working "no rows, author your own" file
into twelve load failures. Nothing detects this; it is on you.

## Never collect

Credentials of any kind · `projects/`, `memory/`, `sessions/`, `history*` ·
`telemetry/` and any runtime log · `backups/`, `archive/`, `audit-archive/`,
`drafts/`, `plans/` · dated internal reports quoting real work ·
`.credentials.json`, `settings.local.json` · anything under a `.claude/`
subdirectory of a skill · `__pycache__/` and build droppings.

Two of these are structural, not judgement calls: check S fails on a tracked
`.claude/`, `__pycache__/` or `archive/` path, and `.gitignore` covers them.

## Procedure

Two procedures, and picking the wrong one is failure 4. **A → the file is not
here yet. B → it is.** At any scale above a handful of files you will be doing
both at once; sort the candidate list by which procedure it needs *before* you
copy anything, because a bulk sweep silently runs A over B's files.

### Step 0, for both — record the source state

`git -C ~/.claude rev-parse HEAD` and `git -C ~/.claude status --porcelain`.
A dirty source tree means you are collecting something that is not committed
anywhere — stop and say so.

"Dirty" means the **content** differs. Check with `git diff --numstat <path>`:
a file can show `M` for line endings alone, which is not a reason to stop, and
treating it as one teaches you to skip the check. If some paths are dirty and
none of them is one you collect, say exactly that rather than "clean".

### A — first collection

1. **Read every byte you are about to publish.** Not the head, not a grep — the
   whole file. You cannot certify content you have not seen, and step 3 of the
   decision procedure is unanswerable otherwise. This applies to what you
   PUBLISH; a candidate you are excluding needs enough reading to justify the
   disposition, not all of it.
2. **Copy, then diff against the source, normalising line endings:**
   ```git bash
   diff <(tr -d '\r' < ~/.claude/<path>) <(tr -d '\r' < <repo-path>)
   ```
   The diff must contain exactly the edits you intended and nothing else. An
   empty diff means `status = "verbatim"`.
3. **Write the `[[collected]]` entry** with `source`, `status`, and one `edits`
   line per change, each saying *what* and *why*.

### B — refresh of a file already here

1. **Recover the existing decision first, before copying anything.** The
   `[[collected]] edits` list is the specification. No entry? Reconstruct from
   `git log --follow -p -- <file>` and write the entry as part of this round —
   an undeclared file is the one the mechanism cannot protect.
2. **Copy the source over it, then re-apply every recovered edit.** Anchor each
   one on text you have just re-read: the source moves, and an anchor that no
   longer matches is a signal to re-read, never to skip.
3. **Diff the result against the source.** It must differ by exactly the edit
   list and nothing else. Byte-identical means you dropped them all.
4. **Scan for what the gate cannot see**, over the new content specifically.
   The gate reads patterns; these four need a reader, and all four were live
   findings on 2026-08-16:
   - a private-tree pointer with no path in it — an asset name, a task name;
   - subject matter belonging to the source's owner (research topics, client
     work) arriving inside a file whose *structure* is what ships;
   - a pointer into a directory this repo excludes, which turns a routing table
     into a list of files the reader does not have;
   - a count or inventory claim in prose (`ships 13 of 14`, `seven hooks`) that
     the refresh has just made false.
5. **Update the `edits` list** if what you re-applied differs from what was
   declared, and say why it changed.

### Both — closing out

6. **Re-check every `[[not_shipped]]` entry your work touches.** Collecting a
   file usually means an old disposition is now wrong. Re-check per FILE; a
   disposition written for a directory keeps applying itself to files added
   later that it never examined.
7. **Run the gate, with the source mounted:**
   ```git bash
   python tools/share_gate.py --source ~/.claude
   ```
   Must exit 0. `--source` is not optional when you are collecting: without it
   check V does not run, and check V is the only thing that can see a reverted
   edit. Then `python tools/test_share_gate.py` — if you changed the gate, it
   ships with a case that fails without your change, and if you widened a
   pattern, it ships with a negative control too.
8. **Confirm the source is untouched**: the SHA from step 0, and a status you
   can account for line by line.
9. **Record it in `CHANGELOG.md`** — what came in, what was edited, what the
   audit disproved, and what you deferred.

## What the gate can and cannot do

Check C verifies that every collected file declares its source, a valid status,
and at least one edit reason when it is not verbatim; and that no entry points
at a file that is not there.

Check C alone cannot verify the copy still matches the source — the published
repo has no source to compare against. **Check V can, and you have one.** Run
`--source` whenever you are collecting; the difference between the two is the
difference between "the paperwork is complete" and "the paperwork is true", and
2026-08-16 is what the first one alone is worth.

Check D closes the other end: a declaration that no longer matches anything.
An `[[allow]]` outliving its finding is a standing permission nobody re-reads,
a `[[not_shipped]]` for a file that now ships is a published falsehood about
what an adopter gets, and a placeholder token declared with nothing using it is
the residue of a rule rewritten without checking what pointed at it. All three
were live on the day the check was written.

What no check can do: judge whether a `reason` is honest, notice that a
structurally-fine document now carries someone's research topics, or tell a
deferral from a decision. Step A1 and steps B1, B4 and 6 are human-or-model
work. The checks only make skipping them visible — and only for the classes
someone has already been burned by, which is why every one of them names its
incident in the code rather than in a comment somewhere else.
