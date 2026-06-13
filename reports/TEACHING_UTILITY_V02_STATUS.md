# Teaching Utility v0.2 Pilot Status

Generated at: `2026-06-13T16:40:03.014975+00:00`

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
- sealed hidden cases are fixed globally and excluded from generation/query/validation roles
- hidden evaluation mode: `deferred_independent_script`
- active budget: `2 query trajectories per method per repeat`
- split integrity: `hidden_reused_outside_hidden=False`

## Method Summary

| Method | Mean query score | Mean validation delta | Mean hidden delta | Hidden pass count |
|---|---:|---:|---:|---:|
| random | 0.5 | 0.0 | 0.0 | 0 / 0 |
| top_reward_success_only | 0.3333 | 0.0 | 0.0 | 0 / 0 |
| success_failure_contrast | 0.3333 | 0.0 | 0.0 | 0 / 0 |
| diversity | 0.1667 | 0.0 | 0.0 | 0 / 0 |
| active_discriminative_evidence | 0.5 | 0.0 | 0.0 | 0 / 0 |

## Key Judgment

- `task_utility_vs_teaching_utility`: `pending_independent_hidden_eval`
- `active_selection_hypothesis`: `pending_independent_hidden_eval`
- `best_method_by_hidden_delta`: `pending_independent_hidden_eval`
- `active_hidden_delta_minus_contrast`: `0.0`
- `active_hidden_delta_minus_diversity`: `0.0`
- `global_sealed_hidden_cases`: `case005_transport_and_scope, case007_auth_sensitive_session`
- `interpretation`: `method skills are frozen; run the independent sealed-hidden evaluator once`

## Boundary

- Query selection is budgeted and repeat-rotated across 10 local tasks over 2 domains.
- Hidden-test evaluation uses the live tool agent; validation remains local and bounded.
- If active discriminative selection does not beat contrast/diversity, the hypothesis is recorded as not supported or inconclusive.
