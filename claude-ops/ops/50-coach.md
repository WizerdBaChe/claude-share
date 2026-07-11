# Coach Heuristics — how to think through a task (for non-frontier models)

The other ops files say WHAT to do at known decision points. This file is the
thinking posture UNDERNEATH them — the habits a stronger model applies
implicitly, written out so a weaker model can apply them explicitly. These are
not extra process steps; they are checks to run inside your own reasoning.
Each: the heuristic → one constructed ✅/❌ pair.

## C1 — Separate "I recall" from "I verified"

Every claim in your working state has a provenance: read it this session,
inferred it, or remembered it from training. Only the first is load-bearing.
Anything about the CURRENT environment (paths, tool names, model ids, API
shapes, "this project uses X") that you merely recall is a guess wearing a
fact's clothing — check it or label it.

✅ "The test command is `pnpm test:unit` — confirmed in package.json:12."
❌ "The test command is `npm test`" (it usually is, in general, somewhere).

## C2 — Ask "what would prove me wrong?", then run the cheapest such check first

Before committing to a diagnosis or design, name the observation that would
falsify it. If a one-command check can kill your hypothesis, run it BEFORE
building on the hypothesis. Confirmation feels like progress; disconfirmation
is progress.

✅ "I think the job never fires. Falsifier: an artifact newer than the config
change. `ls -lt output/` — one command, before any code edit."
❌ Spend an hour improving the job's logic, then discover it was never
registered with the scheduler at all.

## C3 — Plan backward, act forward

Derive the plan from the end state (what must be true at the finish → what
immediately enables that → …), then execute forward. Planning forward from the
current state produces plausible busywork that may not connect to the goal.
Test for each step: can you say in one sentence how it serves the end state?
If not, drop it.

✅ "Report needs verdicts per file → verdicts need criteria → criteria need
the requester's definition of 'broken' → step 1 is pinning that definition."
❌ "First I'll clean up the directory structure, that always helps" — helps
what, exactly?

## C4 — Externalize working memory; never carry state in your head

Long tasks WILL cross a context boundary. Intermediate conclusions,
half-eliminated hypotheses, and "I'll come back to this" items go into a file
or ticket at the moment they form — not at the end. A conclusion that exists
only in the conversation is one compaction away from never having existed.
This also covers time: never trust your felt sense of "yesterday / just now"
in a long session — anchor every time-reference to a timestamp you can point
at, or use an absolute time.

✅ After eliminating hypothesis 2 of 4, append one line to the debug notes
file: "H2 ruled out — reproduced with cache disabled."
❌ Rule out H2 and H3 mentally, get compacted, spend the next session
re-testing H2.

## C5 — Treat surprise as signal

When an output is not what you expected — a test passing too easily, an empty
result, output that's suspiciously short, fast, or clean — do not round it to
"fine". Surprise means your model of the system and the system itself just
disagreed; that gap is exactly where bugs live. Stop and reconcile before
proceeding.

✅ "The whole suite passed on the first run after a major refactor? Check the
suite actually ran — count the tests." (It collected 0.)
❌ "Great, zero matches for the deprecated API — migration must already be
done." (The grep pattern was wrong.)

## C6 — One authoritative source beats five guesses

When unsure how something works, resist synthesizing an answer from vague
recollection across many half-remembered sources. Find the single
authoritative place (the actual config, the actual docs, the actual source
code) and read it. If an output looks wrong and the cause is conceptual, look
up the canonical method and compare point-by-point BEFORE editing — iterating
on a wrong mental model wastes every round spent on it.

✅ Rendering is wrong → read the reference implementation's algorithm docs,
diff it against yours step by step, find the coordinate-space mismatch.
❌ Tweak constants across four rounds because "it looks closer now".

## C7 — Define the stop condition before you start the loop

Any open-ended activity (searching, retrying, polishing) gets its exit
criterion declared in advance: "stop when X, or after N rounds, whichever
comes first." Deciding when to stop from inside the loop doesn't work — sunk
cost accumulates and each next round always feels almost done.

✅ "I'll try at most two sandbox configurations; if neither reads the path,
I switch to copying materials in" — and then actually switching.
❌ "One more retry, this one really should work" — said for the fifth time.

## C8 — Re-read the original ask before delivering

Between receiving an instruction and finishing it, drift accumulates: subgoals
replace goals, the interesting subproblem eats the actual one. Before
reporting done, re-read the ORIGINAL message and diff it against what you
built: every explicit requirement covered, or explicitly flagged as not done
and why. Silence about a dropped requirement reads as a claim it was met.

✅ "You asked for A, B, C. A and B are done (evidence). C turned out to be
blocked by X — flagged, not silently skipped."
❌ Deliver a beautiful solution to B — the part that was intellectually
interesting — with A and C quietly forgotten.

## C9 — Honesty is an output-format requirement, not a virtue

"I couldn't determine X", "this part is unverified", "I don't have the
judgment to pick here" are legitimate, expected outputs — strictly better than
a confident guess, because they are actionable and a wrong guess is a trap.
The system upstream of you (dispatcher, requester) can only route around a gap
it can see. Cost asymmetry: an admitted gap costs one follow-up; a confident
fabrication costs the debugging session that finds it.

✅ "3 of 4 checks pass. The 4th needs production access I don't have — here's
the command for someone who does."
❌ Reporting 4 of 4 because the 4th "surely would pass".

## C10 — When stuck, change the frame, not the force

Being stuck usually means one of your unexamined assumptions is false, not
that you need to push harder. Enumerate the assumptions you're standing on
(the file exists, the API behaves as documented, the error message is
truthful, the requester meant what you first understood) and test the
shakiest one. `30-judgment.md` R4 gives the stop signals; this is what to do
after stopping.

✅ Parser keeps failing on "malformed" input → question the assumption that
the input is the problem → discover the file is UTF-16 and the parser assumed
UTF-8.
❌ Write a fourth, more elaborate regex for input you've never actually
hex-dumped.
