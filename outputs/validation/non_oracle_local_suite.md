# Generalization Suite

- Backend: `non_oracle_local_semantic`
- Scenarios: `5`
- A2 pass: `5/5`

| Scenario | Family | A1 Feedback | Repair | Gate | A2 |
|---|---|---|---|---|---|
| api_review_001 | api_or_code_review | pass | no_op | accept_no_change | True |
| auth_access_control_001 | auth_access_control | pass | no_op | accept_no_change | True |
| config_security_001 | config_security | pass | no_op | accept_no_change | True |
| data_quality_review_001 | data_quality_review | pass | no_op | accept_no_change | True |
| upload_security_001 | upload_security | missing_capability | patch_capability | accept | True |

## Boundary

This is controlled offline evidence that the same pipeline can run multiple task families. It is not a large-scale proof of arbitrary vulnerability discovery.
