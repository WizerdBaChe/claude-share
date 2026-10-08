# model-bench summary

runs: 12 · arms (model@effort): haiku-5-5@inherit/full/agent · generated from `round3-agent-runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is runs per cell. Rep 1 uses the base fixture; rep 2+ regenerate seeded fixtures where the task has a generator (t02, t04, t11).

## Per task × arm — pass / median s / mean $

| task | expected | haiku-5-5@inherit/full/agent |
|---|---|---|
| t04_search_inventory | cheap | 1/3 · 11.8s · $0.0333 |
| t06_review_find_bugs | mid | 3/3 · 10.0s · $0.0156 |
| t08_format_contract | cheap | 3/3 · 8.3s · $0.0054 |
| t10_agentic_repair | mid | 3/3 · 12.7s · $0.0208 |

## Per arm

| arm | runs | pass | med s | mean s | total $ | $ if uncached | mean thinking tok | mean output tok | cache hit |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5@inherit/full/agent | 12 | 10/12 | 10.5 | 11.1 | 0.2254 | 0.4212 | 1526 | 2331 | 0.77 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST arm (tier, then effort) whose pass count is n/n takes the row. `not clean` = at least one failure. No clean arm → `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | cheapest clean arm | verdict vs expected | all arms (pass) |
|---|---|---|---|---|
| t04_search_inventory | cheap | — | escalate / redesign gate | haiku-5-5@inherit/full/agent=1/3 |
| t06_review_find_bugs | mid | haiku-5-5@inherit/full/agent | DOWNGRADE candidate → cheap | haiku-5-5@inherit/full/agent=3/3 |
| t08_format_contract | cheap | haiku-5-5@inherit/full/agent | as expected | haiku-5-5@inherit/full/agent=3/3 |
| t10_agentic_repair | mid | haiku-5-5@inherit/full/agent | DOWNGRADE candidate → cheap | haiku-5-5@inherit/full/agent=3/3 |

## Failures (2)

- `t04_search_inventory-haiku-inherit-full-agent-r1` · set correct but not sorted
- `t04_search_inventory-haiku-inherit-full-agent-r2` · set correct but not sorted
