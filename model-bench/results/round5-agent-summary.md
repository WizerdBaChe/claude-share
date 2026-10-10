# model-bench summary

runs: 6 · arms (model@effort): haiku-5-5@medium/full/agent, haiku-5-5@high/full/agent · generated from `round5-agent-runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is runs per cell. Rep 1 uses the base fixture; rep 2+ regenerate seeded fixtures where the task has a generator (t02, t04, t11).

## Per task × arm — pass / median s / mean $

| task | expected | haiku-5-5@medium/full/agent | haiku-5-5@high/full/agent |
|---|---|---|---|
| t04_search_inventory | cheap | 2/3 · 14.1s · $0.0793 | 2/3 · 19.0s · $0.0663 |

## Per arm

| arm | runs | pass | med s | mean s | total $ | $ if uncached | mean thinking tok | mean output tok | cache hit |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5@medium/full/agent | 3 | 2/3 | 14.1 | 15.5 | 0.2379 | 0.3912 | 0 | 3097 | 0.73 |
| haiku-5-5@high/full/agent | 3 | 2/3 | 19.0 | 19.0 | 0.1990 | 0.3572 | 0 | 3963 | 0.77 |

## Effort sweep — claude-haiku-5-5

Same model, same tasks; only `--effort` differs. Thinking tokens are what effort buys; pass count is what it is for.

| task | medium/full/agent pass · s · $ · think | high/full/agent pass · s · $ · think |
|---|---|---|
| t04_search_inventory | 2/3 · 14.1 · 0.0793 · 0 | 2/3 · 19.0 · 0.0663 · 0 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST arm (tier, then effort) whose pass count is n/n takes the row. `not clean` = at least one failure. No clean arm → `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | cheapest clean arm | verdict vs expected | all arms (pass) |
|---|---|---|---|---|
| t04_search_inventory | cheap | — | escalate / redesign gate | haiku-5-5@medium/full/agent=2/3, haiku-5-5@high/full/agent=2/3 |

## Failures (2)

- `t04_search_inventory-haiku-medium-full-agent-r2` · set correct but not sorted
- `t04_search_inventory-haiku-high-full-agent-r3` · set correct but not sorted
