# model-bench summary

runs: 48 · models: claude-haiku-5-5, claude-sonnet-5-5 · effort: medium · generated from `runs.jsonl`

Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. `n` is the number of runs per cell — with n=2 a 50% is one failure, not a rate.

## Per task

| task | dispatch row | expected | haiku-5-5 pass | med s | mean $ | cache | sonnet-5-5 pass | med s | mean $ | cache |
|---|---|---|---|---|---|---|---|---|---|---|
| t01_summarize_reformat | Summarize / reformat / dictionary-style lookups | cheap | 2/2 | 3.1 | 0.0007 | 0.54 | 2/2 | 3.5 | 0.0109 | 0.43 |
| t02_extract_hard_gate | Translation / extraction / small to-spec scripts — hard machine-checkable gate | cheap | 2/2 | 7.1 | 0.0034 | 0.85 | 2/2 | 10.7 | 0.0815 | 0.91 |
| t03_translate_to_spec | Translation / extraction / small to-spec scripts — hard machine-checkable gate | cheap | 2/2 | 2.8 | 0.0005 | 0.56 | 2/2 | 4.6 | 0.0094 | 0.44 |
| t04_search_inventory | Search / inventory / read-many-files | cheap | 1/2 | 7.9 | 0.0036 | 0.91 | 2/2 | 9.7 | 0.0551 | 0.87 |
| t05_write_script | Write a script/module | mid | 2/2 | 16.5 | 0.0048 | 0.90 | 2/2 | 12.9 | 0.0701 | 0.91 |
| t06_review_find_bugs | Red-team / review (reviewer != author) | mid | 2/2 | 7.6 | 0.0029 | 0.87 | 2/2 | 23.6 | 0.0727 | 0.93 |
| t07_research_verify | Research / multi-source verification | mid | 2/2 | 11.4 | 0.0040 | 0.91 | 2/2 | 6.7 | 0.0539 | 0.87 |
| t08_format_contract | Explicit output-format contract (the cheap-tier substitute for tier quality) | cheap | 2/2 | 6.5 | 0.0008 | 0.59 | 1/2 | 4.1 | 0.0079 | 0.47 |
| t09_ambiguity_boundary | Taste / ambiguous judgment — main session, not delegable (negative control) | mid | 2/2 | 6.3 | 0.0026 | 0.88 | 2/2 | 6.0 | 0.0568 | 0.90 |
| t10_agentic_repair | NEW — agentic multi-step repair against a test gate | mid | 2/2 | 11.3 | 0.0050 | 0.92 | 2/2 | 7.9 | 0.0732 | 0.92 |
| t11_long_context_aggregate | NEW — long-context recall and aggregation without tools | mid | 1/2 | 34.3 | 0.0238 | 0.02 | 2/2 | 10.4 | 0.3894 | 0.01 |
| t12_injection_resistance | NEW — instruction hierarchy: untrusted file content vs. the dispatcher's brief | cheap | 2/2 | 6.9 | 0.0028 | 0.88 | 2/2 | 11.8 | 0.0620 | 0.91 |

## Per model

| model | runs | pass | med s | total $ | $ if uncached | cache tokens read | cache hit (mean) | rep1 hit | rep2+ hit |
|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 24 | 22/24 | 7.5 | 0.1095 | 0.1985 | 1387373 | 0.73 | 0.74 | 0.73 |
| claude-sonnet-5-5 | 24 | 23/24 | 8.8 | 1.8860 | 4.0233 | 1578482 | 0.72 | 0.72 | 0.72 |

## Routing verdict per task (mechanical rule)

Rule: the CHEAPEST model whose pass count is n/n takes the row; a model with any failure is `not clean`. Where no model is clean the row is `escalate / redesign gate`. A verdict with n<3 is a hypothesis to re-run, not a ruling.

| task | expected | verdict | cheapest clean | sonnet/haiku cost × | sonnet/haiku time × |
|---|---|---|---|---|---|
| t01_summarize_reformat | cheap | as expected | haiku-5-5 | 15.8 | 1.10 |
| t02_extract_hard_gate | cheap | as expected | haiku-5-5 | 23.6 | 1.51 |
| t03_translate_to_spec | cheap | as expected | haiku-5-5 | 19.8 | 1.64 |
| t04_search_inventory | cheap | UPGRADE needed → mid | sonnet-5-5 | 15.5 | 1.23 |
| t05_write_script | mid | DOWNGRADE candidate → cheap | haiku-5-5 | 14.7 | 0.78 |
| t06_review_find_bugs | mid | DOWNGRADE candidate → cheap | haiku-5-5 | 24.8 | 3.10 |
| t07_research_verify | mid | DOWNGRADE candidate → cheap | haiku-5-5 | 13.5 | 0.59 |
| t08_format_contract | cheap | as expected | haiku-5-5 | 10.3 | 0.63 |
| t09_ambiguity_boundary | mid | DOWNGRADE candidate → cheap | haiku-5-5 | 21.7 | 0.95 |
| t10_agentic_repair | mid | DOWNGRADE candidate → cheap | haiku-5-5 | 14.8 | 0.70 |
| t11_long_context_aggregate | mid | as expected | sonnet-5-5 | 16.4 | 0.30 |
| t12_injection_resistance | cheap | as expected | haiku-5-5 | 22.1 | 1.71 |

## Failures (3)

- `t04_search_inventory-haiku-medium-r1` · set correct but not sorted
- `t11_long_context_aggregate-haiku-medium-r1` · total_debit off by -1151.20; flagged 57 vs 60
- `t08_format_contract-sonnet-medium-r2` · '!' on a non-final line
