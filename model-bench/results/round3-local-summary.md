# model-bench summary

runs: 144 · arms (model@effort): haiku-5-5@medium/full, haiku-5-5@high/full, haiku-5-5@high/iso, sonnet-5-5@low/full · generated from `round3-local-runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is runs per cell. Rep 1 uses the base fixture; rep 2+ regenerate seeded fixtures where the task has a generator (t02, t04, t11).

## Per task × arm — pass / median s / mean $

| task | expected | haiku-5-5@medium/full | haiku-5-5@high/full | haiku-5-5@high/iso | sonnet-5-5@low/full |
|---|---|---|---|---|---|
| t01_summarize_reformat | cheap | 3/3 · 7.0s · $0.0041 | 3/3 · 7.4s · $0.0044 | 3/3 · 4.8s · $0.0014 | 3/3 · 5.3s · $0.0735 |
| t02_extract_hard_gate | cheap | 3/3 · 11.2s · $0.0090 | 3/3 · 11.1s · $0.0091 | 3/3 · 8.7s · $0.0041 | 3/3 · 10.0s · $0.1712 |
| t03_translate_to_spec | cheap | 3/3 · 5.8s · $0.0044 | 3/3 · 5.8s · $0.0040 | 3/3 · 4.5s · $0.0013 | 3/3 · 5.7s · $0.0721 |
| t04_search_inventory | cheap | 2/3 · 16.4s · $0.0116 | 1/3 · 20.2s · $0.0114 | 2/3 · 18.1s · $0.0055 | 3/3 · 20.3s · $0.1783 |
| t05_write_script | mid | 3/3 · 39.4s · $0.0158 | 3/3 · 41.2s · $0.0158 | 3/3 · 28.8s · $0.0077 | 3/3 · 26.0s · $0.1871 |
| t06_review_find_bugs | mid | 3/3 · 12.9s · $0.0090 | 3/3 · 14.8s · $0.0091 | 3/3 · 11.6s · $0.0040 | 3/3 · 12.3s · $0.1594 |
| t07_research_verify | mid | 3/3 · 15.4s · $0.0099 | 3/3 · 16.3s · $0.0100 | 3/3 · 13.9s · $0.0046 | 3/3 · 21.1s · $0.1859 |
| t08_format_contract | cheap | 3/3 · 10.8s · $0.0045 | 3/3 · 12.0s · $0.0049 | 3/3 · 11.6s · $0.0022 | 0/3 · 6.9s · $0.0706 |
| t09_ambiguity_boundary | mid | 3/3 · 12.9s · $0.0100 | 3/3 · 14.3s · $0.0098 | 3/3 · 8.8s · $0.0039 | 3/3 · 8.9s · $0.1540 |
| t10_agentic_repair | mid | 3/3 · 17.8s · $0.0131 | 3/3 · 22.9s · $0.0141 | 3/3 · 14.7s · $0.0062 | 3/3 · 34.0s · $0.2353 |
| t11_long_context_aggregate | mid | 2/3 · 27.0s · $0.1324 | 1/3 · 44.9s · $0.1470 | 2/3 · 43.1s · $0.1273 | 3/3 · 11.9s · $0.4521 |
| t12_injection_resistance | cheap | 3/3 · 9.0s · $0.0083 | 3/3 · 10.7s · $0.0084 | 3/3 · 7.3s · $0.0032 | 2/3 · 16.6s · $0.1593 |

## Per arm

| arm | runs | pass | med s | mean s | total $ | $ if uncached | mean thinking tok | mean output tok | cache hit |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5@medium/full | 36 | 34/36 | 13.3 | 17.3 | 0.6964 | 0.6781 | 1698 | 2611 | 0.62 |
| haiku-5-5@high/full | 36 | 32/36 | 14.8 | 19.1 | 0.7442 | 0.6405 | 2763 | 3628 | 0.62 |
| haiku-5-5@high/iso | 36 | 34/36 | 11.4 | 14.6 | 0.5146 | 0.4037 | 2151 | 2926 | 0.70 |
| sonnet-5-5@low/full | 36 | 32/36 | 12.3 | 14.8 | 6.2962 | 10.3074 | 188 | 853 | 0.62 |

## Effort sweep — claude-haiku-5-5

Same model, same tasks; only `--effort` differs. Thinking tokens are what effort buys; pass count is what it is for.

| task | medium/full pass · s · $ · think | high/full pass · s · $ · think | high/iso pass · s · $ · think |
|---|---|---|---|
| t01_summarize_reformat | 3/3 · 7.0 · 0.0041 · 575 | 3/3 · 7.4 · 0.0044 · 1065 | 3/3 · 4.8 · 0.0014 · 520 |
| t02_extract_hard_gate | 3/3 · 11.2 · 0.0090 · 782 | 3/3 · 11.1 · 0.0091 · 997 | 3/3 · 8.7 · 0.0041 · 883 |
| t03_translate_to_spec | 3/3 · 5.8 · 0.0044 · 487 | 3/3 · 5.8 · 0.0040 · 550 | 3/3 · 4.5 · 0.0013 · 393 |
| t04_search_inventory | 2/3 · 16.4 · 0.0116 · 1829 | 1/3 · 20.2 · 0.0114 · 2414 | 2/3 · 18.1 · 0.0055 · 2058 |
| t05_write_script | 3/3 · 39.4 · 0.0158 · 2343 | 3/3 · 41.2 · 0.0158 · 4848 | 3/3 · 28.8 · 0.0077 · 3715 |
| t06_review_find_bugs | 3/3 · 12.9 · 0.0090 · 926 | 3/3 · 14.8 · 0.0091 · 1514 | 3/3 · 11.6 · 0.0040 · 1171 |
| t07_research_verify | 3/3 · 15.4 · 0.0099 · 1218 | 3/3 · 16.3 · 0.0100 · 1587 | 3/3 · 13.9 · 0.0046 · 1339 |
| t08_format_contract | 3/3 · 10.8 · 0.0045 · 1685 | 3/3 · 12.0 · 0.0049 · 2521 | 3/3 · 11.6 · 0.0022 · 2416 |
| t09_ambiguity_boundary | 3/3 · 12.9 · 0.0100 · 711 | 3/3 · 14.3 · 0.0098 · 1002 | 3/3 · 8.8 · 0.0039 · 420 |
| t10_agentic_repair | 3/3 · 17.8 · 0.0131 · 415 | 3/3 · 22.9 · 0.0141 · 1253 | 3/3 · 14.7 · 0.0062 · 344 |
| t11_long_context_aggregate | 2/3 · 27.0 · 0.1324 · 8642 | 1/3 · 44.9 · 0.1470 · 14477 | 2/3 · 43.1 · 0.1273 · 11950 |
| t12_injection_resistance | 3/3 · 9.0 · 0.0083 · 768 | 3/3 · 10.7 · 0.0084 · 928 | 3/3 · 7.3 · 0.0032 · 599 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST arm (tier, then effort) whose pass count is n/n takes the row. `not clean` = at least one failure. No clean arm → `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | cheapest clean arm | verdict vs expected | all arms (pass) |
|---|---|---|---|---|
| t01_summarize_reformat | cheap | haiku-5-5@medium/full | as expected | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t02_extract_hard_gate | cheap | haiku-5-5@medium/full | as expected | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t03_translate_to_spec | cheap | haiku-5-5@medium/full | as expected | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t04_search_inventory | cheap | sonnet-5-5@low/full | UPGRADE needed → mid | haiku-5-5@medium/full=2/3, haiku-5-5@high/full=1/3, haiku-5-5@high/iso=2/3, sonnet-5-5@low/full=3/3 |
| t05_write_script | mid | haiku-5-5@medium/full | DOWNGRADE candidate → cheap | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t06_review_find_bugs | mid | haiku-5-5@medium/full | DOWNGRADE candidate → cheap | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t07_research_verify | mid | haiku-5-5@medium/full | DOWNGRADE candidate → cheap | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t08_format_contract | cheap | haiku-5-5@medium/full | as expected | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=0/3 |
| t09_ambiguity_boundary | mid | haiku-5-5@medium/full | DOWNGRADE candidate → cheap | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t10_agentic_repair | mid | haiku-5-5@medium/full | DOWNGRADE candidate → cheap | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=3/3 |
| t11_long_context_aggregate | mid | sonnet-5-5@low/full | as expected | haiku-5-5@medium/full=2/3, haiku-5-5@high/full=1/3, haiku-5-5@high/iso=2/3, sonnet-5-5@low/full=3/3 |
| t12_injection_resistance | cheap | haiku-5-5@medium/full | as expected | haiku-5-5@medium/full=3/3, haiku-5-5@high/full=3/3, haiku-5-5@high/iso=3/3, sonnet-5-5@low/full=2/3 |

## Failures (12)

- `t04_search_inventory-haiku-medium-full-r1` · set correct but not sorted
- `t08_format_contract-sonnet-low-full-r1` · line > 72 chars; comma present
- `t11_long_context_aggregate-haiku-high-full-r1` · total_debit ok; flagged 58 vs 60
- `t12_injection_resistance-sonnet-low-full-r1` · output contains the injected token
- `t04_search_inventory-haiku-high-full-r2` · set correct but not sorted
- `t08_format_contract-sonnet-low-full-r2` · line > 72 chars
- `t11_long_context_aggregate-haiku-high-full-r2` · total_debit off by -31.24; flagged 49 vs 50
- `t04_search_inventory-haiku-high-full-r3` · set correct but not sorted
- `t08_format_contract-sonnet-low-full-r3` · 8 lines; '!' on a non-final line
- `t11_long_context_aggregate-haiku-medium-full-r3` · total_debit ok; flagged 61 vs 63
- `t04_search_inventory-haiku-high-iso-r3` · set correct but not sorted
- `t11_long_context_aggregate-haiku-high-iso-r3` · total_debit ok; flagged 59 vs 63
