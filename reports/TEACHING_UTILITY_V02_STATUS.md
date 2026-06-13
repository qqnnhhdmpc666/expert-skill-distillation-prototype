# Teaching Utility v0.2 Pilot Status

Generated at: `2026-06-13T11:57:05.205997+00:00`

This pilot separates immediate task utility from teaching utility.
It does not claim official external benchmark validity.

## Fresh Command

```powershell
skill-deploy teaching-utility-v02 --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## Pilot Design

- repeats: `3`
- methods: `random, top_reward_success_only, success_failure_contrast, diversity, active_discriminative_evidence`
- domains: `api_review`, `config_security`
- split per repeat: `source_generation`, `active_query_pool`, `promotion_validation`, `sealed_hidden_test`
- active budget: `1 query trajectory per method per repeat`

## Method Summary

| Method | Mean query score | Mean validation delta | Mean hidden delta | Hidden pass count |
|---|---:|---:|---:|---:|
| random | 0.3889 | -0.0333 | 0.1722 | 2 / 3 |
| top_reward_success_only | 0.3167 | -0.0333 | 0.2222 | 3 / 3 |
| success_failure_contrast | 0.8222 | 0.0 | 0.0333 | 1 / 3 |
| diversity | 0.65 | -0.0333 | 0.2 | 2 / 3 |
| active_discriminative_evidence | 0.8222 | 0.0 | 0.0 | 1 / 3 |

## Key Judgment

- `task_utility_vs_teaching_utility`: `rough_alignment`
- `active_selection_hypothesis`: `hypothesis_not_supported`
- `best_method_by_hidden_delta`: `top_reward_success_only`

## Boundary

- Query selection is budgeted and repeat-rotated across 8 local tasks over 2 domains.
- Hidden-test evaluation uses the live tool agent; validation remains local and bounded.
- If active discriminative selection does not beat contrast/diversity, the hypothesis is recorded as not supported or inconclusive.
