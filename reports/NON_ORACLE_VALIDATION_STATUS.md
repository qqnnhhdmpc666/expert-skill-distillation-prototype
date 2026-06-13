# Non-Oracle Validation Status

Generated at: `2026-06-12T12:42:27.861732+00:00`

This validation checks whether installed secure_code_review behavior is merely offline-deterministic/verifier aligned or also observable through a non-oracle backend. Live LLM unavailability is reported as blocked, not as model failure.

## Summary

- Selected cases: `6`
- Non-oracle completed rows: `6`
- Live LLM status: `blocked`
- Non-oracle execution: `pass`
- Non-oracle effectiveness: `pass`
- Non-oracle behavior: `pass`
- Overall status: `pass`

Execution success means the backend ran. Effectiveness requires verifier pass with no discrepancy against the offline deterministic reference. These are intentionally separated.

## Rows

| Case | Task family | Backend | Status | Activated group | Verifier | FP count | Discrepancy | Blocked/failure reason |
|---|---|---|---|---|---|---:|---|---|
| holdout_upload_double_extension_001 | upload_security | non_oracle_local_semantic | completed | upload_security | pass | 0 | none | none |
| holdout_config_prod_secret_001 | config_security | non_oracle_local_semantic | completed | config_security | pass | 0 | none | none |
| holdout_auth_project_ownership_001 | auth_access_control | non_oracle_local_semantic | completed | auth_access_control | pass | 0 | none | none |
| holdout_api_overbroad_schema_001 | api_or_code_review | non_oracle_local_semantic | completed | api_or_code_review | pass | 0 | none | none |
| holdout_clean_tax_math_001 | clean_business_logic_review | non_oracle_local_semantic | completed | out_of_scope_guard | pass | 0 | none | none |
| holdout_dependency_no_advisory_001 | dependency_version_risk | non_oracle_local_semantic | completed | out_of_scope_guard | pass | 0 | none | none |
| holdout_upload_double_extension_001 | upload_security | live_llm_text | blocked | None | None | None | not_run | missing_env:OPENAI_BASE_URL,MODEL_or_OPENAI_MODEL |
| holdout_config_prod_secret_001 | config_security | live_llm_text | blocked | None | None | None | not_run | missing_env:OPENAI_BASE_URL,MODEL_or_OPENAI_MODEL |
| holdout_auth_project_ownership_001 | auth_access_control | live_llm_text | blocked | None | None | None | not_run | missing_env:OPENAI_BASE_URL,MODEL_or_OPENAI_MODEL |
| holdout_api_overbroad_schema_001 | api_or_code_review | live_llm_text | blocked | None | None | None | not_run | missing_env:OPENAI_BASE_URL,MODEL_or_OPENAI_MODEL |
| holdout_clean_tax_math_001 | clean_business_logic_review | live_llm_text | blocked | None | None | None | not_run | missing_env:OPENAI_BASE_URL,MODEL_or_OPENAI_MODEL |
| holdout_dependency_no_advisory_001 | dependency_version_risk | live_llm_text | blocked | None | None | None | not_run | missing_env:OPENAI_BASE_URL,MODEL_or_OPENAI_MODEL |
