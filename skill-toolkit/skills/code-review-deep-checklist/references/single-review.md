# Mode A — Single File / Single PR Deep Review

License reminder: everything below applies to code THIS change touches or directly
depends on. Pre-existing issues → separate "Pre-existing" report section, clearly
labeled, no verdict impact. See Scope Rules in SKILL.md.

## 1. Design & Correctness

- Is the design reasonable, or is there a simpler way to achieve the same result
  without this level of complexity?
- Are all input scenarios handled, including edge cases (null, oversized,
  malformed, unexpected type)?
- Unintended side effects — shared state changed in ways nobody expects?
- Backward compatibility (e.g. a new API parameter that could break existing
  callers)?

## 2. Complexity & Readability

- Does this function/class carry too many responsibilities that should be split?
- Do names clearly express intent, readable without deep prior context?
- Comments explain "why", not restate the code, and don't compensate for code that
  should have been made self-explanatory.
- Speculative over-engineering — abstraction built for a future need that doesn't
  exist yet?

## 3. Error Handling & Tests

- All realistic failure points explicitly handled, not silently assumed to succeed.
- Tests cover this change's core logic, not just the happy path.
- Tactic: read the tests FIRST — they often reveal true intent faster than the
  implementation.

## 4. Security (for code touching input/auth/data)

- Injection: SQL injection, XSS, command injection, path traversal.
- Authentication/authorization bypass introduced by this change.
- Hardcoded secrets, credentials, API keys.
- Missing validation at a trust boundary for untrusted input.

## 5. Style Consistency

- Follows the project's established convention (naming, formatting, file
  structure)? This is a readability/maintainability check, not aesthetics — and it
  is pass-3 material, never a blocker.

## 6. Requirement–Data Consistency (統整資料與需求)

Precondition: a spec/requirement source must exist — otherwise ask the user for a
one-line intent statement or mark items "untraceable" (Scope Rules).

- Bidirectional traceability: code → specific requirement item, and requirement →
  this implementation + a corresponding test.
- Deletion test: if this function were deleted, would a specific requirement item
  visibly go unimplemented? If unclear, the link was never recorded.
- Three-way alignment: requirement ID ↔ code change ↔ test case, same item.
- Plain-language test: can you explain what this code does AND why this approach,
  not just whether it's correct? Failure = intent not expressed (common in
  AI-generated code) → should-fix.
- External-dependency assumptions: is the behavior being relied on (data format,
  units, boundary conditions) actually understood, or used because "it looked like
  it would work"?
- Data consistency: formats / units / timezones / precision consistent across the
  whole code path.
- Upstream input-shape assumptions explicitly validated, or silently relied upon
  (an upstream change would fail silently instead of erroring)?
- Does the embedded business rule match the CURRENT version in requirement docs,
  or is it quietly running on a stale rule version?

## 7. Full Code-Smell Taxonomy (Fowler / Refactoring.Guru)

Flag as `consider` with remediation-cost estimate; escalate to `should-fix` only
when the smell demonstrably blocks this change's correctness or the next known
change.

**Bloaters**
- Long Method — doing too much; unseparated responsibilities.
- Large Class — too many fields/methods, blurred responsibility boundary.
- Primitive Obsession — primitives where a small value object belongs (money,
  phone number, date as raw string).
- Long Parameter List — parameters that should be grouped into an object.
- Data Clumps — data always passed together but never encapsulated.

**Object-Orientation Abusers**
- Switch Statements — same switch/case duplicated in multiple places; missing
  polymorphism/strategy.
- Temporary Field — field only set/used in some circumstances, object partially
  empty otherwise.
- Refused Bequest — subclass uses only part of parent, or nulls out inherited
  behavior instead of honoring the contract.
- Alternative Classes with Different Interfaces — identical function, different
  method names/signatures, similarity hidden.

**Change Preventers**
- Divergent Change — ONE class keeps changing for MANY unrelated reasons.
- Shotgun Surgery — ONE conceptual change forces edits across MANY classes; easy
  to miss a spot.
- Parallel Inheritance Hierarchies — subclassing one hierarchy always requires a
  matching subclass in another.

**Dispensables**
- Comments compensating for confusing code (vs genuine "why" context).
- Duplicated Code — DRY violation; also detectable via copy/paste static analysis.
- Lazy Class — near-zero functionality, still costs cognition.
- Data Class — only getters/setters; its logic lives (wrongly) elsewhere.
- Dead Code — unreachable functions/branches misleading future readers.
- Speculative Generality — "for future use" abstraction never actually used.

**Couplers**
- Feature Envy — method uses another class's data more than its own.
- Inappropriate Intimacy — two classes deep in each other's internals.
- Message Chains — `a.getB().getC().getD()`, coupling caller to navigation.
- Middle Man — pure forwarding class, no added value.
- Incomplete Library Class — missing behavior in an unmodifiable library tempting
  awkward local workarounds.

**Practical heuristic**: if the same block requires re-understanding from scratch
every time (or the team must re-ask an AI/colleague to re-grasp it), that alone is
a strong smell → refactor candidate.

## 8. Quantifiable Technical-Debt Metrics (十項檢查)

Each is independently measurable — when reviewing locally, approximate with quick
scripts/grep (line counts, nesting depth, parameter counts, duplicate-block scan)
rather than eyeballing. Use the project's existing thresholds if configured
(lint/sonar config); otherwise report raw numbers, not verdicts.

**Size**: method length · file length · argument count (often signals data clumps /
primitive obsession; fix is usually a grouping abstraction) · method count per
class.

**Control flow**: nested control flow depth · number of return points per function.

**Complexity**: complex boolean logic (operator count per conditional) ·
method cognitive complexity (size + control flow + branching combined).

**Copy/paste**: identical blocks (formatting may differ — invisible in a diff) ·
similar blocks (only variable names differ — subtler, missed by the previous).

**Scoring & prioritization**
- Estimate remediation time per issue → aggregate to a file grade → repo-wide debt
  ratio (debt time / implementation time) as a TREND line, not a snapshot.
- Bug-prone hotspots: a file with a history of repeated bug-fix commits is a
  debt-concentration signal — check `git log` for fix-commit density on touched
  files; prioritize attention there.
- Prioritize by change-frequency × poor-quality ("hotspot"), not raw quality score
  — rarely-touched bad code may not be worth fixing.
- Deprecated dependencies: does this file rely on deprecated/unmaintained library
  APIs?

Want the full backlog as a deliverable? Hand off to engineering:tech-debt with
these findings as input.

## 9. AI-Generated Code Extra Checks

Pass criterion is "the team actually owns it", NOT "it appears to work":

- Could at least two team members confidently modify this code?
- Does a clear debugging strategy exist for it?
- Does an exit strategy exist if this logic must be replaced or simplified?
- If the answer pattern here is systemic (every AI PR fails these), that's a
  process problem → hand off to ai-coding-guardrails.
