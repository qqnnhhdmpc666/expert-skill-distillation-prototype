# External Generalization Validation Status

Generated at: `2026-06-12T17:48:20.946156+00:00`

This is a bounded external/semiexternal validation lane. It combines public read-only source excerpts and independently authored holdout cases. It is not an official CyberSecEval, AutoPatchBench, CVE-Bench, or SWE-bench result.

## Source Acquisition

| Source | Status | URL | Hash | Artifact |
|---|---|---|---|---|
| nodegoat_contributions | downloaded | https://raw.githubusercontent.com/OWASP/NodeGoat/master/app/routes/contributions.js | 196bdeaa22da4cfe8a851b1b932710b2fcedd21f14ed75d70b739ba759a01003 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\source_downloads\nodegoat_contributions_196bdeaa22da.txt` |
| nodegoat_profile | downloaded | https://raw.githubusercontent.com/OWASP/NodeGoat/master/app/routes/profile.js | 18575bf3d3710906e57e09e6036e40fd3986bdcca436ed0e2a2875b41f0f2aca | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\source_downloads\nodegoat_profile_18575bf3d371.txt` |
| nodegoat_development_config | downloaded | https://raw.githubusercontent.com/OWASP/NodeGoat/master/config/env/development.js | 1829bc509dcc6a6eb58b0eee49901df530b9cceafa2ed37e855beacec4971f08 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\source_downloads\nodegoat_development_config_1829bc509dcc.txt` |

## Summary

- Backend: `live_llm_text`
- Cases: `12`
- Completed: `12`
- Effective pass count: `9`
- False positives: `0`
- Evidence exact match rate: `1.0`
- Unsupported retained count: `3`
- Ambiguous handled count: `1`
- Discrepancy count: `3`
- Live LLM pass rate: `0.75`
- `external_generalization`: `partial`

## Rows

| Case | Source | Family | Status | Group | Verifier | FP | Unsupported retained | Ambiguous handled | Artifacts |
|---|---|---|---|---|---|---:|---:|---:|---|
| public_nodegoat_dev_config_001 | public_repo_read_only | config_security | completed | config_security | pass:pass | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\public_nodegoat_dev_config_001\live_llm_text` |
| public_nodegoat_eval_unsupported_001 | public_repo_read_only | server_side_js_injection_review | completed | out_of_scope_guard | pass:pass | 0 | True | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\public_nodegoat_eval_unsupported_001\live_llm_text` |
| public_nodegoat_regex_unsupported_001 | public_repo_read_only | regex_dos_review | completed | out_of_scope_guard | pass:pass | 0 | True | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\public_nodegoat_regex_unsupported_001\live_llm_text` |
| independent_upload_mime_storage_001 | independent_authored_holdout | upload_security | completed | upload_security | pass:pass | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_upload_mime_storage_001\live_llm_text` |
| independent_upload_clean_001 | independent_authored_holdout | upload_security | completed | upload_security | pass:pass | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_upload_clean_001\live_llm_text` |
| independent_config_prod_audit_001 | independent_authored_holdout | config_security | completed | config_security | fail:missing_capability | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_config_prod_audit_001\live_llm_text` |
| independent_config_clean_001 | independent_authored_holdout | config_security | completed | config_security | pass:pass | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_config_clean_001\live_llm_text` |
| independent_auth_invoice_scope_001 | independent_authored_holdout | auth_access_control | completed | auth_access_control | fail:missing_capability | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_auth_invoice_scope_001\live_llm_text` |
| independent_auth_clean_001 | independent_authored_holdout | auth_access_control | completed | auth_access_control | pass:pass | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_auth_clean_001\live_llm_text` |
| independent_api_schema_001 | independent_authored_holdout | api_or_code_review | completed | api_or_code_review | fail:missing_capability | 0 | False | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_api_schema_001\live_llm_text` |
| independent_dependency_unsupported_001 | independent_authored_holdout | dependency_version_risk | completed | out_of_scope_guard | pass:pass | 0 | True | False | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_dependency_unsupported_001\live_llm_text` |
| independent_ambiguous_debug_001 | independent_authored_holdout | api_or_code_review | completed | api_or_code_review | pass:pass | 0 | False | True | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_ambiguous_debug_001\live_llm_text` |

## Boundary

- Public repo cases are read-only defensive review demos over source excerpts.
- Labels are local verifier labels; this is not a third-party benchmark score.
- Unsupported dependency, regex DoS, and code-execution review families remain limitations for `secure_code_review`.
- No exploit generation or attack-chain execution was performed.
