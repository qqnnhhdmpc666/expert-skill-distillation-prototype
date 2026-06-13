# Defensive Security Mini-Suite Extended Status

Generated at: `2026-06-12T11:40:16.070678+00:00`

This is a local defensive representative mini-suite, not official CyberSecEval/AutoPatchBench/CVE-Bench.

## Metrics

- case_count: `20`
- positive_pass_count: `12`
- negative_fp_count: `0`
- unsupported_retained_count: `3`
- ambiguous_handled_count: `1`
- scope_violation_count: `0`
- package_marginal_utility.average_active_score: `0.2`

## Case Results

| Case | Task family | Status | Active group | FP count | Ambiguous | Unsupported |
|---|---|---|---|---:|---:|---:|
| mini_upload_magic_path_001 | upload_security | pass | upload_security | 0 | False | False |
| mini_upload_public_storage_002 | upload_security | pass | upload_security | 0 | False | False |
| mini_config_prod_audit_001 | config_security | pass | config_security | 0 | False | False |
| mini_config_env_guard_002 | config_security | pass | config_security | 0 | False | False |
| mini_auth_invoice_scope_001 | auth_access_control | pass | auth_access_control | 0 | False | False |
| mini_auth_owner_boundary_002 | auth_access_control | pass | auth_access_control | 0 | False | False |
| mini_api_schema_grounding_001 | api_or_code_review | pass | api_or_code_review | 0 | False | False |
| mini_dependency_version_risk_001 | dependency_version_risk | unsupported_limitation | out_of_scope_guard | 0 | False | True |
| mini_clean_out_of_scope_001 | clean_business_logic_review | false_positive_control_pass | out_of_scope_guard | 0 | False | False |
| holdout_upload_double_extension_001 | upload_security | pass | upload_security | 0 | False | False |
| holdout_config_prod_secret_001 | config_security | pass | config_security | 0 | False | False |
| holdout_auth_project_ownership_001 | auth_access_control | pass | auth_access_control | 0 | False | False |
| holdout_api_overbroad_schema_001 | api_or_code_review | pass | api_or_code_review | 0 | False | False |
| holdout_clean_tax_math_001 | clean_business_logic_review | false_positive_control_pass | out_of_scope_guard | 0 | False | False |
| holdout_dependency_no_advisory_001 | dependency_version_risk | unsupported_limitation | out_of_scope_guard | 0 | False | True |
| extended_upload_public_exec_003 | upload_security | pass | upload_security | 0 | False | False |
| extended_input_validation_limitation_001 | input_validation_review | unsupported_limitation | out_of_scope_guard | 0 | False | True |
| extended_clean_reporting_002 | clean_business_logic_review | false_positive_control_pass | out_of_scope_guard | 0 | False | False |
| extended_clean_profile_003 | clean_business_logic_review | false_positive_control_pass | out_of_scope_guard | 0 | False | False |
| extended_ambiguous_low_confidence_001 | ambiguous_security_review | pass | out_of_scope_guard | 0 | True | False |
