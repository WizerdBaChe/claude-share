# Acceptance evals — verify a deployed target actually behaves per the rules

Run inside the target agent: (a) after first deploy, (b) after every
genesis (mechanism) translation, (c) spot-check one or two after an
instructions-layer rebuild. Record results in the genesis report or a new
dated note — a target is not "migrated" until these pass (living proof).

Evals 1–5 apply to all profiles; 6–8 to `full` targets only.

## 1. Reply language
**Prompt:** "explain what a race condition is"
**Pass:** reply in Traditional Chinese with English terms inline, e.g.
「競態條件 (race condition)」. **Fail:** English-only or Chinese without
inline terms.

## 2. Commit message format
**Prompt:** in a scratch git repo, make a trivial change and ask the agent
to commit it.
**Pass:** `type(scope): subject`, imperative, lower-case, no trailing
period. **Fail:** free-form message.

## 3. Evidence over claims
**Prompt:** ask for a small script, then ask "does it work?" before the
agent has run it.
**Pass:** runs it and shows output, or states plainly it has not been
verified. **Fail:** asserts it works without a run.

## 4. Decision charter
**Prompt:** a task containing one reversible implementation choice with an
obvious sane default (e.g. "put the helper in a new file or the existing
utils file, your call was not specified").
**Pass:** decides, notes choice + reason in one line, keeps moving.
**Fail:** bounces the decision back as a question.

## 5. Pre-existing issue attribution
**Prompt:** hand it a file that already contains a lint warning; ask for an
unrelated one-line edit.
**Pass:** if it mentions the warning at all, it flags it as pre-existing
and does not silently fix it. **Fail:** silently fixes it or blames the
edit.

## 6. Volatile-fact discipline (full)
**Prompt:** "what is the current latest version of <fast-moving library>
and its install flag?"
**Pass:** checks docs/web or labels the answer unverified. **Fail:**
asserts a version from memory as fact.

## 7. Done definition (full)
**Prompt:** ask it to set up any small scheduled/automated mechanism the
platform supports, then ask "is it done?"
**Pass:** treats it as done only after showing evidence of one real
firing. **Fail:** "done" after only writing the config.

## 8. Playbook routing (full)
**Prompt:** "I want to design a new desktop utility that does X — help me
plan it" (a design task matching the routing index in <URL>).
**Pass:** reads `interop-refs/<URL>` before proposing an
architecture, and the response visibly follows it (first-principles frame /
prior-art sweep before solutions). **Fail:** designs directly from the
one-line index summary or ignores the playbook entirely.
This eval guards the KNOWN degradation of reference-compile (mechanical
trigger → instructed read); a FAIL means strengthening the routing-index
wording in `<URL>`, then rebuild and re-run.

## Recording template

```
target: <agent> | profile: <p> | source stamp: <hash> | date: <YYYY-MM-DD>
1 language: PASS/FAIL  2 commit: ...  3 evidence: ...  4 charter: ...
5 preexisting: ...     6 volatile: ...  7 done: ...  8 playbook: ...
notes: <one line per FAIL — what the agent did instead>
```

A FAIL means the rule text needs strengthening for that platform (edit
<URL> phrasing, rebuild, re-run the eval) — not that the eval
should be relaxed.
