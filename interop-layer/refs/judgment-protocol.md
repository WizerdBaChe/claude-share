<!--
  <URL> — curated, agent-neutral distillation of the deep
  judgment rubrics (canonical source: ~/.claude/ops/<URL>, R7/R8).

  Reference-compile class (<URL>): the enforcement/dispatch
  machinery around these rubrics does not migrate; this file carries the
  reasoning protocol CONTENT only. The quick-form judgment rules (evidence
  over claims, done definition, approach-wrong signals, volatile facts) are
  already in the generated <URL> — this file is the DEEP protocol for
  when those one-liners aren't enough.
-->

# Judgment Protocol — deep-analysis discipline

## When to reach for the web (and at what granularity)

Search BEFORE asserting (never answer from memory) when the fact is volatile
or environment-external: library/API versions and signatures, tool/CLI
flags, pricing, quotas, model ids, security advisories, "current best
practice" of a fast-moving ecosystem, anything post-cutoff. Test: if wrong
recall costs the requester more than a ~1-minute lookup → look up.

Do NOT search when the answer is verifiable locally at lower cost: facts
about THIS repo (grep it), behavior of an installed tool (run
`--help`/`--version`), stable fundamentals (algorithms, language semantics).

Reactive trigger: output conceptually wrong → compare the current approach
point-by-point against the canonical/industry method BEFORE editing again.

Granularity ladder — match effort to the question:
1. Quick lookup, ≤3 sources → do it inline.
2. Multi-source, comparative, or "survey the options" → a dedicated
   research pass with its own notes.
3. Decision-grade report the requester will act on → per-claim adversarial
   verification (each key claim independently checked against a source that
   could refute it).

## Two-pass depth protocol (think first, then targeted verification)

Trigger: the deliverable is a design/plan/evaluation document, or the
decision is hard to reverse, or the conclusion rests on volatile external
facts, or the user explicitly asks for depth. Never apply to trivial
factual lookups — protocol cost must not exceed the answer's value.

**Pass 1 — self-reliant.** Using only own knowledge plus already-loaded
instructions: restate the problem, collect constraints, choose a
decomposition axis, produce a first-pass conclusion PLUS a **gap list**.
Classify each key claim:
- (A) locally verifiable → verify immediately, never leave as assumption;
- (B) volatile external fact → mark "needs search", do NOT search yet;
- (C) judgment/value call → mark "user decision".
No external search during pass 1 — write the hypothesis first; searching
first anchors on early results.

**Clean-sheet extension (when improving an EXISTING artifact).** When
hardening / auditing / extending something that already exists (a rule
file, config, module), pass 1 adds ONE clean-sheet enumeration: from domain
knowledge, list what complete coverage of the artifact's problem class
would include, then diff against the artifact as it stands. Structural gaps
join the gap list as PROPOSALS — each must name a concrete failure scenario
or be discarded (hallucination gate). One round only, no recursive
redesign; "core need already met → recommend stopping" still overrides.

**Gate.** Route each gap: residual A → local check; B → one targeted search
per gap, never an open sweep; C → batch into ONE question to the requester.
If the gap list is empty, or the remaining gaps cannot change the
conclusion's direction, skip pass 2 and deliver with unverified items
labeled.

**Pass 2 — targeted only.** Resolve gaps item by item and DIFF each result
against the pass-1 belief; a refuted belief gets a one-line "was stale
because…" note (calibration evidence — keep it). Conclusions not on the gap
list are settled — do not reopen. Newly discovered aspects get at most one
level of expansion, each re-classified A/B/C first.

**Delivery.** Three visibly distinct claim classes: locally verified /
externally verified (with source) / assumption-or-user-decision. Budget
rule: width in pass 1, depth in pass 2 — the less reversible the decision,
the thicker pass 2 deserves to be.
