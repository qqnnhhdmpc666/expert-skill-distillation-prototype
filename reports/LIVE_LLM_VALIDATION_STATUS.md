# Live LLM Validation Status

Generated at: `2026-06-12T14:59:35.827320+00:00`

This run checks the installed secure_code_review package through the OpenAI-compatible `live_llm_text` backend. API keys are not written to artifacts.

## Configuration

- Base URL configured: `True`
- Model: `deepseek-v4-flash`
- API key present: `True`

## Summary

- Selected cases: `6`
- `live_llm_execution`: `pass`
- `live_llm_effectiveness`: `partial`
- `live_llm_behavior`: `partial`
- Verifier pass rows: `5`
- Verifier fail rows: `1`
- Discrepancy rows: `1`

## Rows

| Case | Task family | Status | Activated group | Verifier | FP count | Discrepancy | Blocked/failure reason |
|---|---|---|---|---|---:|---|---|
| holdout_upload_double_extension_001 | upload_security | completed | upload_security | pass | 0 | none | none |
| holdout_config_prod_secret_001 | config_security | completed | config_security | pass | 0 | none | none |
| holdout_auth_project_ownership_001 | auth_access_control | completed | auth_access_control | pass | 0 | none | none |
| holdout_api_overbroad_schema_001 | api_or_code_review | completed | api_or_code_review | fail | 0 | pass_mismatch,feedback_type_mismatch | unsupported_evidence |
| holdout_clean_tax_math_001 | clean_business_logic_review | completed | out_of_scope_guard | pass | 0 | none | none |
| holdout_dependency_no_advisory_001 | dependency_version_risk | completed | out_of_scope_guard | pass | 0 | none | none |

## Boundary

- Verifier was not relaxed.
- Verifier-only expected findings, evidence spans, and clean labels were not exposed to the runner.
- Malformed JSON, schema errors, unsupported evidence, and false positives remain failures.
- API/network/model blocks are infrastructure/configuration blocks, not model success.
