# Genesis prompt — mechanism-layer translation (run INSIDE the target agent)

Copy the prompt below into a session of the TARGET agent (opencode / codex /
Antigravity), filling the placeholders. Run it once per target, and again
whenever `interop.py status` reports the mechanism layer stale (i.e. the
canonical hooks/permission policies changed in ways the map says are
portable).

---

You are running inside {TARGET_AGENT}. Your task is to translate the
mechanism layer of a canonical agent environment into THIS platform's
native extension points. You know your own platform best — that is why the
translation happens here rather than being copied in.

## Inputs (read all before acting)

1. `~/.claude/interop/MIGRATION-MAP.md` — layer model, portability classes,
   sync invariants. The invariants are binding.
2. `~/.claude/hooks/model_cap_guard.py` and
   `~/.claude/hooks/ops_health_nudge.py` — the two enforcement mechanisms
   to translate (intent matters, not implementation).
3. `~/.claude/settings.json` — permission shape only; ignore machine-bound
   paths.
4. Your OWN platform's current documentation for config / permissions /
   plugins / hooks. Do not rely on memory for file formats or extension
   points — verify against docs or `--help`.

## Rules

- **Translate intent, not code.** Example: model_cap_guard's intent is
  "subagent/background work is cost-capped; expensive tiers need explicit
  per-instance user approval". Implement that with whatever this platform
  offers (permission config, plugin, hook). Only if NO enforcement point
  exists, degrade to a prose rule appended to this platform's global rules
  file — and record the degradation explicitly in your output.
- **Do not touch the canonical source.** `~/.claude` is read-only to you.
  One-way flow: nothing writes back.
- **Do not import Claude-specific machinery**: skills, skill routing,
  ops/ dispatch framework, memory files. They are out of scope by design.
- **Stamp your outputs.** Every file you create or modify gets a comment:
  `managed-by: claude-interop-genesis | source: {GIT_HASH} | date: {DATE}`.
- **Living proof.** After translating, demonstrate each mechanism with one
  real trigger (e.g. attempt an action the permission policy should block,
  show it blocked). A mechanism without a demonstrated firing does not
  count as translated.

## Deliverable

A short report (English, saved as
`~/.claude/interop/genesis-report-{TARGET_AGENT}-{DATE}.md` — a NEW file,
never overwrite a previous report):

1. Mechanism-by-mechanism table: canonical intent → this platform's
   implementation (file + setting) → proof of firing → or "DEGRADED to
   prose" with reason.
2. Anything in the map's translate-list this platform cannot express at
   all.
3. Files created/modified on this platform, with paths.

Then run the acceptance evals in `~/.claude/interop/acceptance-evals.md`
and append the results to the report.
