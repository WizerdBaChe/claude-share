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
- Calibration expiry: for every constant justified by a MEASUREMENT (window sizes,
  thresholds, timeouts, batch caps, sampling rates — grep the file for "measured",
  "實測", "we sampled", or a recorded n), ask what EVENT would invalidate it, not
  when it was last checked. A justification comment is evidence the value was once
  right, and it is the reason nobody re-questions it. Two findings live here: the
  constant has no named invalidating event (`review.state.calibration-expiry`), and
  — the expensive one — that event has already happened. Constants calibrated
  against an EXTERNAL artifact (another tool's file format, a third-party API shape,
  a corpus you do not control) expire by default; treat "no expiry trigger" as a
  finding there even when the current value still holds.
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

## 10. Stateful-Logic Consistency (FSM Reconstruction)

**Trigger gate — run this section ONLY when the unit under review owns lifecycle
state**: a status/enum field that drives behavior, a multi-step flow (order,
payment, session, job, connection, workflow), or persisted state consumed across
requests. Stateless code: skip, and record the skip in coverage.json (`deferred`
with reason "stateless"). This keeps the section from taxing every review.

Why it exists: state bugs are design-semantic bugs — each individual transition
can look correct in the diff while the MACHINE is wrong (undefined transitions,
broken invariants, trap states). They cannot be verified from code alone; the
intended machine must be reconstructed first, then the code checked against it.

**Method — lightweight explicit modeling, not formal verification:**

1. **Reconstruct the intended machine** from design semantics first (spec, PR
   description, domain docs — §6 traceability sources), then from code. A
   divergence between the two IS a finding (`review.state.spec-divergence`),
   before any code-level check.
2. **Emit a state-transition table** into the report: rows = states, columns =
   events/triggers, each cell = next state / explicitly rejected / **undefined**.
   The table is the review artifact all §10 findings anchor to. Depth cap: model
   the top 1–3 stateful units by risk; list the rest as `deferred` in coverage.
3. **Run these checks against the table + code** (ruleId namespace `review.state.*`):
   - **Completeness**: every state×event cell is a defined transition or an
     explicit rejection. Undefined cells (event silently ignored, partial field
     update, fall-through) → `should-fix`.
   - **Per-state invariants (internal self-consistency)**: for each state, write
     the one-line invariant ("in `SHIPPED`, `tracking_id` is non-null"). Verify
     every inbound transition establishes it and no code path mutates fields in
     ways the current state forbids. Fields valid only in some states = Temporary
     Field smell (§7), escalated here because the invariant makes it checkable.
   - **Illegal-transition rejection at the write site**: transitions enforced
     where state is WRITTEN, not by UI flow or caller convention. A setter any
     module can call with any value = no machine at all.
   - **Single writer / ownership**: which module(s) mutate the state field?
     More than one writer outside the owning module = coupling finding; feeds
     Mode B cross-module state ownership (project-review.md).
   - **Observability (external verifiability)**: each transition must be
     externally distinguishable — return value, emitted event, log line, or
     persisted timestamp — so a test can ASSERT the state, not infer it from
     side effects. An unobservable transition is untestable → `should-fix`.
   - **Restart & trap states**: process death mid-transition — is persisted
     state re-entrant? Does every non-terminal state have an exit (timeout,
     retry, compensation)? A reachable state with no exit is a trap → finding.
   - **Substrate liveness (the machine's own apparatus can be absent)**: the table
     above enumerates what the ANSWER can be. Ask separately what happens when the
     thing that computes the answer cannot start — a worker/thread that fails to
     construct, a subprocess that is not installed, a browser capability that is
     absent, a remote service that never accepts the connection. Restart & trap
     states above assumes the machine ran; this asks about a machine that never
     began. Three questions, each a finding if unanswered: (a) is "apparatus
     unavailable" a NAMED state, distinct from every content-level failure? (b) does
     the failure carry enough to act on — which apparatus, why, where — or does it
     collapse into one generic code? (c) is there a degraded path, and if an
     alternative implementation already exists in the codebase, why is it not wired
     to this one? Compare against any sibling machine in the same project that DOES
     model unavailability: a codebase that models it for one apparatus and not
     another is showing you the gap, not a limitation.
   - **Concurrent transitions**: two events racing on the same entity — is the
     transition atomic (transaction, versioned/compare-and-swap update), or is
     lost-update/double-transition possible?
4. **Security handoff**: any transition an ATTACKER could force, skip, replay,
   or race is recorded as a `sec.state.*` discovery-stage candidate
   (output-contract.md §5) and handed to security-deep-checklist — do not run
   its attack-path pipeline here.

## 11. Cross-Boundary Contract Consistency

**Trigger gate — run this section ONLY when the diff touches a boundary
contract**: an API request/response shape, a shared or mirrored enum, a
validation rule that also exists on the other side of a frontend/backend (or
service/service) boundary, an event/message schema, or an error shape. Purely
one-side-internal changes: skip, record in coverage (`deferred`, reason
"no boundary contract touched").

The failure mode: each side compiles, each side's tests pass, and the SEAM is
wrong — because the contract lives in two hand-maintained copies. Per-unit
review cannot see it unless it explicitly looks at both sides. Checks
(ruleId namespace `review.contract.*`):

- **Both sides in the change set**: if this diff changes one side of a mirrored
  contract (type, enum value, validation bound, error shape), where is the
  matching change — same PR, linked PR, or codegen output? "Other side will
  follow later" with no tracked link → `should-fix`.
- **Canonical source question**: for each touched contract, which artifact is
  authoritative (OpenAPI/GraphQL schema, protobuf, shared schema package) —
  and is the code DERIVED from it (codegen, shared import) or hand-mirrored?
  Hand-mirrored with no drift gate (contract test, schema diff in CI) →
  finding; the remediation is the derivation mechanism, not "be careful".
- **Compatibility window**: during a rolling deploy, old client + new server
  (and the reverse) coexist. Is the change additive/tolerant (optional field,
  unknown-value handling), or does it break one direction? Renaming or
  repurposing a field in place is the classic miss.
- **Error-shape contract**: does the consumer branch on error codes/shapes this
  change alters? Error responses are contract too — verify the consumer's
  error handling against the new shape, not just the happy path.
- **Sequencing assumptions**: does the consumer rely on call order or
  freshness the provider doesn't enforce? Note it as temporal coupling; the
  server-side enforcement question is §10 / security-deep-checklist territory.
