# Ablation Summary

## Conclusion

- This ablation is now executable: each strategy emits findings and is evaluated by the shared verifier/gate path.
- `typed_repair_plus_gate` passes both controlled scenarios with no false-positive regression.
- `always_append` can recover missing coverage but preserves existing false positives in the config case.
- `naive_regenerate` uses a global prior and is intentionally unstable across task families.
- Evidence remains controlled and small-scale; it supports design debugging, not a broad benchmark claim.

| Scenario | Strategy | Pass | Coverage | Evidence | Contract | Regression Safety | Gate | Feedback |
|---|---|---:|---:|---:|---:|---:|---|---|
| upload_security | A0_naive_baseline | False | 0.00 | 1.00 | 1.00 | 1.00 | n/a | missing_capability |
| upload_security | Skill_v1 | False | 0.33 | 1.00 | 1.00 | 1.00 | fail | missing_capability |
| upload_security | Skill_v1_plus_naive_regenerate | True | 1.00 | 1.00 | 1.00 | 1.00 | accept | pass |
| upload_security | Skill_v1_plus_always_append | True | 1.00 | 1.00 | 1.00 | 1.00 | accept | pass |
| upload_security | Skill_v1_plus_typed_repair_only | True | 1.00 | 1.00 | 1.00 | 1.00 | not_applied | pass |
| upload_security | Skill_v1_plus_typed_repair_plus_gate | True | 1.00 | 1.00 | 1.00 | 1.00 | accept | pass |
| upload_security | Skill_v2_final | True | 1.00 | 1.00 | 1.00 | 1.00 | accept | pass |
| config_security | A0_naive_baseline | False | 0.00 | 1.00 | 1.00 | 1.00 | n/a | missing_capability |
| config_security | Skill_v1 | False | 1.00 | 1.00 | 1.00 | 0.00 | fail | false_positive_risk |
| config_security | Skill_v1_plus_naive_regenerate | False | 0.00 | 1.00 | 1.00 | 0.00 | reject | missing_capability |
| config_security | Skill_v1_plus_always_append | False | 1.00 | 1.00 | 1.00 | 0.00 | reject | false_positive_risk |
| config_security | Skill_v1_plus_typed_repair_only | True | 1.00 | 1.00 | 1.00 | 1.00 | not_applied | pass |
| config_security | Skill_v1_plus_typed_repair_plus_gate | True | 1.00 | 1.00 | 1.00 | 1.00 | accept | pass |
| config_security | Skill_v2_final | True | 1.00 | 1.00 | 1.00 | 1.00 | accept | pass |

## Required Questions

1. typed repair + gate is more controllable than always append in this controlled slice because it uses verifier feedback and policy-selected repair before gate evaluation.
2. naive regenerate is executable but intentionally weak: it uses a global capability prior rather than task-specific verifier feedback.
3. gate blocks config false-positive regressions by rejecting outputs with non-expected capabilities.
4. feedback type determines repair action through `revision/repair_policy.json`.
5. Evidence is controlled, not large-scale.
