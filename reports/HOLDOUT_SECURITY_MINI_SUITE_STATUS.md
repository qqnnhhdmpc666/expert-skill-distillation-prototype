# Holdout Security Mini-Suite Status

Generated at: `2026-06-12T11:38:43.701740+00:00`

This is local holdout defensive evidence. It is not an official CyberSecEval, AutoPatchBench, or CVE-Bench run.

## Summary

- Fresh holdout cases: `6`
- Positive effective pass count: `4`
- Clean negative false-positive control: `pass`
- Unsupported limitation: `retained`
- Oracle leakage status: `pass`

## Case Results

| Case | Task family | Status | Active group | Expected group | Group correct | FP count |
|---|---|---|---|---|---:|---:|
| holdout_upload_double_extension_001 | upload_security | pass | upload_security | upload_security | True | 0 |
| holdout_config_prod_secret_001 | config_security | pass | config_security | config_security | True | 0 |
| holdout_auth_project_ownership_001 | auth_access_control | pass | auth_access_control | auth_access_control | True | 0 |
| holdout_api_overbroad_schema_001 | api_or_code_review | pass | api_or_code_review | api_or_code_review | True | 0 |
| holdout_clean_tax_math_001 | clean_business_logic_review | false_positive_control_pass | out_of_scope_guard | out_of_scope_guard | True | 0 |
| holdout_dependency_no_advisory_001 | dependency_version_risk | unsupported_limitation | out_of_scope_guard | out_of_scope_guard | True | 0 |
