# Lessons — append-only pitfall log

Routing and fold-in rules: `40-maintenance.md` §2. Before starting any task,
grep this file for relevant keywords. Trim trigger: ~30 unfolded entries.

Entry format:
```
## L-NNN <YYYY-MM-DD> tags: <env|dispatch|verify|...> hits: 1
Context: <what was being done>
Pitfall: <what went wrong>
Fix: <the durable fix, and where it now lives if folded in>
```
Recurs? Bump `hits:` instead of adding a duplicate. Replaced? Mark
`SUPERSEDED by L-XXX`, don't delete.

## L-001 2026-07-10 tags: dispatch|cost-cap|hooks hits: 1
Context: eval-5 subagent (spawned sonnet) was killed by a usage limit and
resumed via SendMessage; transcript showed cache_miss_reason model_changed
(claude-sonnet-5 -> claude-fable-5) — resume inherits the MAIN session model.
Pitfall: model_cap_guard.py cannot intercept the resume path. Verified vs
official hooks docs 2026-07-10: PreToolUse fires on SendMessage but the
payload ({to, summary, message}) has no model/resume info; SubagentStart has
no model field and cannot block; no AgentResume event exists.
Fix: rules-side mitigation folded into `ops/environment.md` (Enforcement,
known gap 2): prefer re-spawning a fresh capped agent over SendMessage-resume
for cost-capped work; disclose to the user if a resume is unavoidable. Hook
header documents the hole. Re-check when the hooks API adds resume events.

---
## Archived (folded into another file, or retired)
(none yet)
