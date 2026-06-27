# Teaching Utility v0.2 Independent Sealed Hidden Evaluation

Generated at: `2026-06-13T16:40:36.460986+00:00`

This report is produced by the independent hidden evaluator after method Skill hashes were frozen.
It should not be used to modify candidate generation or query selection.

## Fresh Command

```powershell
skill-deploy teaching-utility-v02-hidden-eval --manifest outputs/teaching_utility_v02/frozen_method_manifest.json
```

## Split Integrity

- manifest: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\teaching_utility_v02\frozen_method_manifest.json`
- first hidden access: `2026-06-13T16:40:14.510556+00:00`
- repeated run allowed: `False`
- hidden reused outside hidden: `False`
- global sealed hidden cases: `case005_transport_and_scope, case007_auth_sensitive_session`

## Method Summary

| Method | Mean hidden delta | Hidden pass count | Rows |
|---|---:|---:|---:|
| active_discriminative_evidence | 0.0 | 0 | 6 |
| diversity | 0.0 | 0 | 6 |
| random | 0.0 | 0 | 6 |
| success_failure_contrast | 0.0 | 0 | 6 |
| top_reward_success_only | 0.0 | 0 | 6 |

## Key Judgment

- `task_utility_vs_teaching_utility`: `flat_sealed_hidden_signal`
- `active_selection_hypothesis`: `inconclusive`
- `best_method_by_hidden_delta`: `tie_all_methods`
- `active_hidden_delta_minus_contrast`: `0.0`
- `active_hidden_delta_minus_diversity`: `0.0`
- `interpretation`: `independent sealed hidden utility is flat across frozen methods`

## Boundary

- This evaluator reads sealed hidden cases after frozen Skill paths and hashes already exist.
- It does not regenerate methods, alter Skill text, or feed hidden results back into the pilot.
- It is still a local bounded pilot, not official external benchmark evidence.
