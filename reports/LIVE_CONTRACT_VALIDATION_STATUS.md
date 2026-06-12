# Live Contract Validation Status

Generated at: `2026-06-12T18:12:04.814813+00:00`

This run evaluates a contract-grounded live LLM path with strict verifier behavior unchanged. The normalizer only uses agent-visible target text, model output, Skill metadata, and the contract schema.

## Summary

- Cases: `7`
- Completed: `7`
- Blocked: `0`
- Before-normalizer pass count: `7`
- After-normalizer pass count: `7`
- Normalizer improvement count: `0`
- Evidence exact match rate: `1.0`
- Unsupported evidence before/after: `0 / 0`
- False positives: `0`
- `live_contract_effectiveness`: `pass`

## Rows

| Case | Family | Status | Group | Before | After | Unsupported before/after | FP | Exact rate | Artifacts |
|---|---|---|---|---|---|---:|---:|---:|---|
| holdout_upload_double_extension_001 | upload_security | completed | upload_security | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_upload_double_extension_001\live_llm_contract` |
| holdout_config_prod_secret_001 | config_security | completed | config_security | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_config_prod_secret_001\live_llm_contract` |
| holdout_auth_project_ownership_001 | auth_access_control | completed | auth_access_control | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_auth_project_ownership_001\live_llm_contract` |
| holdout_api_overbroad_schema_001 | api_or_code_review | completed | api_or_code_review | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_api_overbroad_schema_001\live_llm_contract` |
| holdout_clean_tax_math_001 | clean_business_logic_review | completed | out_of_scope_guard | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_clean_tax_math_001\live_llm_contract` |
| holdout_dependency_no_advisory_001 | dependency_version_risk | completed | out_of_scope_guard | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_dependency_no_advisory_001\live_llm_contract` |
| holdout_ambiguous_debug_path_001 | api_or_code_review | completed | api_or_code_review | pass:pass | pass:pass | 0 / 0 | 0 | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_ambiguous_debug_path_001\live_llm_contract` |

## Boundary

- Verifier logic was not relaxed.
- Verifier-only oracle fields were not exposed to the model or normalizer.
- The ambiguous case is a local holdout stress probe, not an official benchmark.
- API keys are not written to artifacts.
