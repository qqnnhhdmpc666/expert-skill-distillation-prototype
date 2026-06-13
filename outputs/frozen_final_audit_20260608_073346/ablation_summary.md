# Ablation Summary

## Conclusion

- `typed_repair_plus_gate` passes both controlled scenarios with no regression.
- `always_append` can recover coverage but introduces or preserves false positives/regression risk.
- `naive_regenerate` may pass upload but is less stable and fails the config case in this controlled slice.
- Evidence strength is controlled and small-scale; it supports a design choice, not a large empirical claim.

| Scenario | Strategy | Pass | Coverage | Evidence | Contract | Regression Safety | Gate |
|---|---|---:|---:|---:|---:|---:|---|
| upload_security | A0_naive_baseline | False | 0.00 | 0.00 | 0.50 | 1.00 | n/a |
| upload_security | Skill_v1 | False | 0.33 | 1.00 | 1.00 | 1.00 | fail |
| upload_security | Skill_v1_plus_naive_regenerate | True | 1.00 | 0.80 | 0.80 | 0.80 | accept_with_risk |
| upload_security | Skill_v1_plus_always_append | True | 1.00 | 0.90 | 1.00 | 0.70 | accept_with_risk |
| upload_security | Skill_v1_plus_typed_repair_only | True | 1.00 | 1.00 | 1.00 | 0.90 | not_applied |
| upload_security | Skill_v1_plus_typed_repair_plus_gate | True | 1.00 | 1.00 | 1.00 | 1.00 | accept |
| upload_security | Skill_v2_final | True | 1.00 | 1.00 | 1.00 | 1.00 | accept |
| config_security | A0_naive_baseline | False | 0.00 | 0.00 | 0.50 | 1.00 | n/a |
| config_security | Skill_v1 | False | 1.00 | 1.00 | 1.00 | 0.00 | fail |
| config_security | Skill_v1_plus_naive_regenerate | False | 0.50 | 0.80 | 0.80 | 0.50 | reject |
| config_security | Skill_v1_plus_always_append | False | 1.00 | 0.90 | 1.00 | 0.00 | reject |
| config_security | Skill_v1_plus_typed_repair_only | True | 1.00 | 1.00 | 1.00 | 0.80 | not_applied |
| config_security | Skill_v1_plus_typed_repair_plus_gate | True | 1.00 | 1.00 | 1.00 | 1.00 | accept |
| config_security | Skill_v2_final | True | 1.00 | 1.00 | 1.00 | 1.00 | accept |

## Required Questions

1. typed repair + gate is more controllable than always append in this controlled slice because it reaches pass while preserving regression safety.
2. naive regenerate can solve some cases, but it is not stable across scenarios here.
3. gate prevents accepting config false-positive regressions.
4. feedback type determines repair action through `revision/repair_policy.json`.
5. Evidence is controlled, not large-scale.
