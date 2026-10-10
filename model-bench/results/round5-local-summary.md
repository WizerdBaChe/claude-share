# model-bench summary

runs: 27 · arms (model@effort): haiku-5-5@medium/full, haiku-5-5@high/full, sonnet-5-5@low/full · generated from `round5-local-runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is runs per cell. Rep 1 uses the base fixture; rep 2+ regenerate seeded fixtures where the task has a generator (t02, t04, t11).

## Per task × arm — pass / median s / mean $

| task | expected | haiku-5-5@medium/full | haiku-5-5@high/full | sonnet-5-5@low/full |
|---|---|---|---|---|
| t02_extract_hard_gate | cheap | 3/3 · 10.6s · $0.0109 | 3/3 · 10.7s · $0.0110 | 3/3 · 11.3s · $0.2089 |
| t04_search_inventory | cheap | 2/3 · 17.0s · $0.0125 | 2/3 · 22.6s · $0.0113 | 3/3 · 13.4s · $0.2077 |
| t11_long_context_aggregate | mid | 2/3 · 19.6s · $0.1325 | 0/3 · 45.0s · $0.1478 | 3/3 · 10.8s · $0.4625 |

## Per arm

| arm | runs | pass | med s | mean s | total $ | $ if uncached | mean thinking tok | mean output tok | cache hit |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5@medium/full | 9 | 7/9 | 17.0 | 18.6 | 0.4677 | 0.8135 | 3226 | 3905 | 0.50 |
| haiku-5-5@high/full | 9 | 5/9 | 22.6 | 28.0 | 0.5104 | 0.9372 | 5847 | 6522 | 0.53 |
| sonnet-5-5@low/full | 9 | 9/9 | 11.1 | 11.3 | 2.6371 | 2.5634 | 485 | 999 | 0.48 |

## Effort sweep — claude-haiku-5-5

Same model, same tasks; only `--effort` differs. Thinking tokens are what effort buys; pass count is what it is for.

| task | medium/full pass · s · $ · think | high/full pass · s · $ · think |
|---|---|---|
| t02_extract_hard_gate | 3/3 · 10.6 · 0.0109 · 767 | 3/3 · 10.7 · 0.0110 · 955 |
| t04_search_inventory | 2/3 · 17.0 · 0.0125 · 1377 | 2/3 · 22.6 · 0.0113 · 1744 |
| t11_long_context_aggregate | 2/3 · 19.6 · 0.1325 · 7533 | 0/3 · 45.0 · 0.1478 · 14841 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST arm (tier, then effort) whose pass count is n/n takes the row. `not clean` = at least one failure. No clean arm → `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | cheapest clean arm | verdict vs expected | all arms (pass) |
|---|---|---|---|---|
| t02_extract_hard_gate | cheap | haiku-5-5@medium/full | as expected | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, sonnet-5-5@low/full=3/3 |
| t04_search_inventory | cheap | sonnet-5-5@low/full | UPGRADE needed → mid | haiku-5-5@medium/full=2/3, haiku-5-5@high/full=2/3, sonnet-5-5@low/full=3/3 |
| t11_long_context_aggregate | mid | sonnet-5-5@low/full | as expected | haiku-5-5@medium/full=2/3, haiku-5-5@high/full=0/3, sonnet-5-5@low/full=3/3 |

## Failures (6)

- `t04_search_inventory-haiku-high-full-r1` · set correct but not sorted
- `t11_long_context_aggregate-haiku-high-full-r1` · total_debit ok; flagged 59 vs 60
- `t04_search_inventory-haiku-medium-full-r2` · set correct but not sorted
- `t11_long_context_aggregate-haiku-medium-full-r2` · total_debit ok; flagged 51 vs 50
- `t11_long_context_aggregate-haiku-high-full-r2` · total_debit off by -31.24; flagged ok
- `t11_long_context_aggregate-haiku-high-full-r3` · total_debit ok; flagged 60 vs 63
