# Minimal Metamorphic Stress Status

Overall pass: `True`

| Case | Scenario | Transform | Expected pass | Actual pass | Feedback | Control passed |
|---|---|---|---|---|---|---|
| upload_clean_target_removes_findings | upload_security | remove upload type/audit weakness | False | False | false_positive_risk | True |
| config_clean_production_rejects_false_positive | config_security | clean production config | False | False | false_positive_risk | True |
| data_quality_row_shuffle_preserves_findings | data_quality | shuffle row/order presentation | True | True | pass | True |
| api_injected_overbroad_risk_appears | api_review | inject overbroad endpoint risk | True | True | pass | True |

These are minimal stress checks. They support the Robustness Gate, but they are not a full hidden-verifier benchmark.
