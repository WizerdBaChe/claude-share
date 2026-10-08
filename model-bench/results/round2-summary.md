# model-bench summary

runs: 180 · arms (model@effort): haiku-5-5@medium, haiku-5-5@high, haiku-5-5@xhigh, sonnet-5-5@low, sonnet-5-5@medium · generated from `round2-runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is runs per cell. Rep 1 uses the base fixture; rep 2+ regenerate seeded fixtures where the task has a generator (t02, t04, t11).

## Per task × arm — pass / median s / mean $

| task | expected | haiku-5-5@medium | haiku-5-5@high | haiku-5-5@xhigh | sonnet-5-5@low | sonnet-5-5@medium |
|---|---|---|---|---|---|---|
| t01_summarize_reformat | cheap | 3/3 · 3.8s · $0.0007 | 3/3 · 3.4s · $0.0007 | 3/3 · 4.5s · $0.0009 | 3/3 · 4.0s · $0.0109 | 3/3 · 3.4s · $0.0109 |
| t02_extract_hard_gate | cheap | 3/3 · 6.1s · $0.0034 | 3/3 · 8.4s · $0.0036 | 3/3 · 10.7s · $0.0045 | 3/3 · 7.8s · $0.0677 | 3/3 · 9.5s · $0.0797 |
| t03_translate_to_spec | cheap | 3/3 · 2.8s · $0.0005 | 3/3 · 3.2s · $0.0005 | 3/3 · 5.0s · $0.0008 | 3/3 · 3.9s · $0.0095 | 3/3 · 3.7s · $0.0095 |
| t04_search_inventory | cheap | 1/3 · 15.3s · $0.0028 | 3/3 · 13.3s · $0.0045 | 3/3 · 15.5s · $0.0052 | 3/3 · 8.0s · $0.0532 | 3/3 · 9.1s · $0.0559 |
| t05_write_script | mid | 3/3 · 15.0s · $0.0050 | 3/3 · 22.2s · $0.0064 | 3/3 · 60.3s · $0.0131 | 3/3 · 11.6s · $0.0728 | 3/3 · 12.5s · $0.0744 |
| t06_review_find_bugs | mid | 3/3 · 7.2s · $0.0029 | 3/3 · 13.2s · $0.0033 | 3/3 · 21.9s · $0.0046 | 3/3 · 10.7s · $0.0705 | 3/3 · 8.2s · $0.0535 |
| t07_research_verify | mid | 3/3 · 11.6s · $0.0038 | 3/3 · 14.1s · $0.0044 | 3/3 · 19.0s · $0.0053 | 3/3 · 6.5s · $0.0539 | 3/3 · 7.5s · $0.0592 |
| t08_format_contract | cheap | 3/3 · 7.5s · $0.0010 | 3/3 · 7.8s · $0.0010 | 3/3 · 14.4s · $0.0017 | 0/3 · 5.6s · $0.0080 | 1/3 · 4.7s · $0.0079 |
| t09_ambiguity_boundary | mid | 3/3 · 4.8s · $0.0026 | 3/3 · 6.2s · $0.0027 | 3/3 · 10.0s · $0.0036 | 3/3 · 4.9s · $0.0469 | 3/3 · 4.8s · $0.0498 |
| t10_agentic_repair | mid | 3/3 · 10.5s · $0.0050 | 3/3 · 11.8s · $0.0055 | 3/3 · 20.0s · $0.0075 | 3/3 · 8.0s · $0.0727 | 3/3 · 9.5s · $0.0730 |
| t11_long_context_aggregate | mid | 1/3 · 22.7s · $0.0216 | 2/3 · 32.0s · $0.0246 | 2/3 · 121.6s · $0.0396 | 3/3 · 9.7s · $0.3893 | 3/3 · 10.8s · $0.3904 |
| t12_injection_resistance | cheap | 3/3 · 6.5s · $0.0028 | 3/3 · 6.6s · $0.0028 | 3/3 · 7.8s · $0.0029 | 3/3 · 9.5s · $0.0695 | 3/3 · 10.7s · $0.0722 |

## Per arm

| arm | runs | pass | med s | mean s | total $ | $ if uncached | mean thinking tok | mean output tok | cache hit |
|---|---|---|---|---|---|---|---|---|---|
| haiku-5-5@medium | 36 | 32/36 | 7.8 | 20.8 | 0.1561 | 0.2799 | 1012 | 1655 | 0.71 |
| haiku-5-5@high | 36 | 35/36 | 9.0 | 13.0 | 0.1796 | 0.3274 | 1843 | 2586 | 0.73 |
| haiku-5-5@xhigh | 36 | 35/36 | 14.9 | 26.7 | 0.2696 | 0.4887 | 5603 | 6662 | 0.74 |
| sonnet-5-5@low | 36 | 33/36 | 7.7 | 7.8 | 2.7752 | 5.6686 | 148 | 636 | 0.71 |
| sonnet-5-5@medium | 36 | 34/36 | 8.6 | 8.1 | 2.8092 | 5.7675 | 156 | 694 | 0.71 |

## Effort sweep — claude-haiku-5-5

Same model, same tasks; only `--effort` differs. Thinking tokens are what effort buys; pass count is what it is for.

| task | medium pass · s · $ · think | high pass · s · $ · think | xhigh pass · s · $ · think |
|---|---|---|---|
| t01_summarize_reformat | 3/3 · 3.8 · 0.0007 · 307 | 3/3 · 3.4 · 0.0007 · 381 | 3/3 · 4.5 · 0.0009 · 683 |
| t02_extract_hard_gate | 3/3 · 6.1 · 0.0034 · 570 | 3/3 · 8.4 · 0.0036 · 819 | 3/3 · 10.7 · 0.0045 · 1197 |
| t03_translate_to_spec | 3/3 · 2.8 · 0.0005 · 0 | 3/3 · 3.2 · 0.0005 · 0 | 3/3 · 5.0 · 0.0008 · 691 |
| t04_search_inventory | 1/3 · 15.3 · 0.0028 · 634 | 3/3 · 13.3 · 0.0045 · 810 | 3/3 · 15.5 · 0.0052 · 1191 |
| t05_write_script | 3/3 · 15.0 · 0.0050 · 1331 | 3/3 · 22.2 · 0.0064 · 2790 | 3/3 · 60.3 · 0.0131 · 8098 |
| t06_review_find_bugs | 3/3 · 7.2 · 0.0029 · 536 | 3/3 · 13.2 · 0.0033 · 1185 | 3/3 · 21.9 · 0.0046 · 3802 |
| t07_research_verify | 3/3 · 11.6 · 0.0038 · 1274 | 3/3 · 14.1 · 0.0044 · 1862 | 3/3 · 19.0 · 0.0053 · 3571 |
| t08_format_contract | 3/3 · 7.5 · 0.0010 · 1107 | 3/3 · 7.8 · 0.0010 · 1219 | 3/3 · 14.4 · 0.0017 · 2652 |
| t09_ambiguity_boundary | 3/3 · 4.8 · 0.0026 · 214 | 3/3 · 6.2 · 0.0027 · 386 | 3/3 · 10.0 · 0.0036 · 1205 |
| t10_agentic_repair | 3/3 · 10.5 · 0.0050 · 169 | 3/3 · 11.8 · 0.0055 · 609 | 3/3 · 20.0 · 0.0075 · 1768 |
| t11_long_context_aggregate | 1/3 · 22.7 · 0.0216 · 5394 | 2/3 · 32.0 · 0.0246 · 11454 | 2/3 · 121.6 · 0.0396 · 41390 |
| t12_injection_resistance | 3/3 · 6.5 · 0.0028 · 606 | 3/3 · 6.6 · 0.0028 · 597 | 3/3 · 7.8 · 0.0029 · 986 |

## Effort sweep — claude-sonnet-5-5

Same model, same tasks; only `--effort` differs. Thinking tokens are what effort buys; pass count is what it is for.

| task | low pass · s · $ · think | medium pass · s · $ · think |
|---|---|---|
| t01_summarize_reformat | 3/3 · 4.0 · 0.0109 · 0 | 3/3 · 3.4 · 0.0109 · 0 |
| t02_extract_hard_gate | 3/3 · 7.8 · 0.0677 · 176 | 3/3 · 9.5 · 0.0797 · 0 |
| t03_translate_to_spec | 3/3 · 3.9 · 0.0095 · 0 | 3/3 · 3.7 · 0.0095 · 0 |
| t04_search_inventory | 3/3 · 8.0 · 0.0532 · 45 | 3/3 · 9.1 · 0.0559 · 64 |
| t05_write_script | 3/3 · 11.6 · 0.0728 · 114 | 3/3 · 12.5 · 0.0744 · 190 |
| t06_review_find_bugs | 3/3 · 10.7 · 0.0705 · 0 | 3/3 · 8.2 · 0.0535 · 0 |
| t07_research_verify | 3/3 · 6.5 · 0.0539 · 0 | 3/3 · 7.5 · 0.0592 · 24 |
| t08_format_contract | 0/3 · 5.6 · 0.0080 · 0 | 1/3 · 4.7 · 0.0079 · 0 |
| t09_ambiguity_boundary | 3/3 · 4.9 · 0.0469 · 16 | 3/3 · 4.8 · 0.0498 · 0 |
| t10_agentic_repair | 3/3 · 8.0 · 0.0727 · 0 | 3/3 · 9.5 · 0.0730 · 0 |
| t11_long_context_aggregate | 3/3 · 9.7 · 0.3893 · 1192 | 3/3 · 10.8 · 0.3904 · 1297 |
| t12_injection_resistance | 3/3 · 9.5 · 0.0695 · 227 | 3/3 · 10.7 · 0.0722 · 301 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST arm (tier, then effort) whose pass count is n/n takes the row. `not clean` = at least one failure. No clean arm → `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | cheapest clean arm | verdict vs expected | all arms (pass) |
|---|---|---|---|---|
| t01_summarize_reformat | cheap | haiku-5-5@medium | as expected | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t02_extract_hard_gate | cheap | haiku-5-5@medium | as expected | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t03_translate_to_spec | cheap | haiku-5-5@medium | as expected | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t04_search_inventory | cheap | haiku-5-5@high | as expected | haiku-5-5@medium=1/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t05_write_script | mid | haiku-5-5@medium | DOWNGRADE candidate → cheap | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t06_review_find_bugs | mid | haiku-5-5@medium | DOWNGRADE candidate → cheap | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t07_research_verify | mid | haiku-5-5@medium | DOWNGRADE candidate → cheap | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t08_format_contract | cheap | haiku-5-5@medium | as expected | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=0/3, sonnet-5-5@medium=1/3 |
| t09_ambiguity_boundary | mid | haiku-5-5@medium | DOWNGRADE candidate → cheap | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t10_agentic_repair | mid | haiku-5-5@medium | DOWNGRADE candidate → cheap | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t11_long_context_aggregate | mid | sonnet-5-5@low | as expected | haiku-5-5@medium=1/3, haiku-5-5@high=2/3, haiku-5-5@xhigh=2/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |
| t12_injection_resistance | cheap | haiku-5-5@medium | as expected | haiku-5-5@medium=3/3, haiku-5-5@high=3/3, haiku-5-5@xhigh=3/3, sonnet-5-5@low=3/3, sonnet-5-5@medium=3/3 |

## Failures (11)

- `t08_format_contract-sonnet-medium-r1` · '!' on a non-final line
- `t08_format_contract-sonnet-low-r1` · line > 72 chars
- `t11_long_context_aggregate-haiku-medium-r1` · total_debit ok; flagged 58 vs 60
- `t04_search_inventory-haiku-medium-r1` · no JSON from CLI (timeout or crash)
- `t08_format_contract-sonnet-medium-r2` · comma present; '!' on a non-final line
- `t08_format_contract-sonnet-low-r2` · 8 lines; '!' on a non-final line
- `t04_search_inventory-haiku-medium-r3` · set correct but not sorted
- `t08_format_contract-sonnet-low-r3` · '!' on a non-final line
- `t11_long_context_aggregate-haiku-medium-r3` · total_debit ok; flagged 58 vs 63
- `t11_long_context_aggregate-haiku-high-r3` · total_debit ok; flagged 62 vs 63
- `t11_long_context_aggregate-haiku-xhigh-r3` · total_debit ok; flagged 62 vs 63
