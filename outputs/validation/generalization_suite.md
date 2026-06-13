# Generalization Suite

- Backend: `offline_deterministic`
- Scenarios: `5`
- A2 pass: `5/5`

| Scenario | Family | A1 Feedback | Repair | Gate | A2 |
|---|---|---|---|---|---|
| api_review_001 | api_or_code_review | output_contract_error | rewrite_output_contract | accept | True |
| auth_access_control_001 | auth_access_control | ownership_boundary_missing | patch_boundary | accept | True |
| config_security_001 | config_security | false_positive_risk | reduce_false_positive_risk | accept | True |
| data_quality_review_001 | data_quality_review | target_context_missing | add_observation_step | accept | True |
| upload_security_001 | upload_security | missing_capability | patch_capability | accept | True |

## Boundary

This is controlled offline evidence that the same pipeline can run multiple task families. It is not a large-scale proof of arbitrary vulnerability discovery.
