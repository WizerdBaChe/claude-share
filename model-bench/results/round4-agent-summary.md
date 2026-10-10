# model-bench summary

runs: 24 · arms (model@effort): haiku-5-5@medium/full/agent, haiku-5-5@high/full/agent · generated from `round4-agent-runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is runs per cell. Rep 1 uses the base fixture; rep 2+ regenerate seeded fixtures where the task has a generator (t02, t04, t11).

## Per task × arm — pass / median s / mean $

| task | expected | haiku-5-5@medium/full/agent | haiku-5-5@high/full/agent |
|---|---|---|---|
| t04_search_inventory | cheap | 0/3 · 13.2s · $0.0648 | 1/3 · 21.8s · $0.0887 |
| t06_review_find_bugs | mid | 3/3 · 9.0s · $0.0496 | 3/3 · 10.4s · $0.0521 |
| t08_format_contract | cheap | 3/3 · 9.4s · $0.0079 | 3/3 · 10.2s · $0.0082 |
| t10_agentic_repair | mid | 3/3 · 16.6s · $0.0645 | 3/3 · 18.2s · $0.0666 |

## Per arm

| arm | runs | pass | med s | mean s | total $ | $ if uncached | mean thinking tok | mean output tok | cache hit |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5@medium/full/agent | 12 | 9/12 | 10.9 | 11.9 | 0.5606 | 1.1512 | 0 | 1953 | 0.73 |
| haiku-5-5@high/full/agent | 12 | 10/12 | 14.4 | 15.6 | 0.6466 | 1.3849 | 0 | 2527 | 0.74 |

## Effort sweep — claude-haiku-5-5

Same model, same tasks; only `--effort` differs. Thinking tokens are what effort buys; pass count is what it is for.

| task | medium/full/agent pass · s · $ · think | high/full/agent pass · s · $ · think |
|---|---|---|
| t04_search_inventory | 0/3 · 13.2 · 0.0648 · 0 | 1/3 · 21.8 · 0.0887 · 0 |
| t06_review_find_bugs | 3/3 · 9.0 · 0.0496 · 0 | 3/3 · 10.4 · 0.0521 · 0 |
| t08_format_contract | 3/3 · 9.4 · 0.0079 · 0 | 3/3 · 10.2 · 0.0082 · 0 |
| t10_agentic_repair | 3/3 · 16.6 · 0.0645 · 0 | 3/3 · 18.2 · 0.0666 · 0 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST arm (tier, then effort) whose pass count is n/n takes the row. `not clean` = at least one failure. No clean arm → `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | cheapest clean arm | verdict vs expected | all arms (pass) |
|---|---|---|---|---|
| t04_search_inventory | cheap | — | escalate / redesign gate | haiku-5-5@medium/full/agent=0/3, haiku-5-5@high/full/agent=1/3 |
| t06_review_find_bugs | mid | haiku-5-5@medium/full/agent | DOWNGRADE candidate → cheap | haiku-5-5@medium/full/agent=3/3, haiku-5-5@high/full/agent=3/3 |
| t08_format_contract | cheap | haiku-5-5@medium/full/agent | as expected | haiku-5-5@medium/full/agent=3/3, haiku-5-5@high/full/agent=3/3 |
| t10_agentic_repair | mid | haiku-5-5@medium/full/agent | DOWNGRADE candidate → cheap | haiku-5-5@medium/full/agent=3/3, haiku-5-5@high/full/agent=3/3 |

## Failures (5)

- `t04_search_inventory-haiku-high-full-agent-r2` · set correct but not sorted
- `t04_search_inventory-haiku-high-full-agent-r3` · set correct but not sorted
- `t04_search_inventory-haiku-medium-full-agent-r1` · set correct but not sorted
- `t04_search_inventory-haiku-medium-full-agent-r2` · set correct but not sorted
- `t04_search_inventory-haiku-medium-full-agent-r3` · set correct but not sorted
