# tree-noise

Classifies a git working tree's uncommitted paths as noise (content-neutral) or real
work, with git alone — no model call. Feeds the SessionStart notice
`hooks/tree_noise_gist.py`; registry key `TREE_NOISE` in `ops/rule-registry.md`.

```
python tools/tree-noise/noise.py --repo <path> [--json]
python tools/tree-noise/controls.py          # two-sided controls, 24 cases
```

Classes, ruler and extension clause: the docstring of `noise.py` (single source).

To mark a file a tool rewrites on routine use, add `<path> tool-appended` to that
repo's `.gitattributes` (same attribute system-hmi's reconcile emitter reads).

## Prior art consulted (2026-09-23)

- `~/.claude/.gitattributes` class `tool-appended` + `tools/system-hmi/emitters/reconcile.py`
  — reused as the `generated` class vocabulary; it judges by commit age, not content,
  and covers ~/.claude only.
- `hooks/ops_health_nudge.py` check 14 (stale uncommitted work) — time-based, ~/.claude only.
- `hooks/worktree_scope_guard.py` — dirty COUNT per linked worktree, no classification.
- vault `AGENTS.md` §2 (Properties-panel re-serialisation) — why `.md` is never
  parse-compared.
- project-registry gist, `references/PROJECTS.md`: no existing tree-noise tool.
