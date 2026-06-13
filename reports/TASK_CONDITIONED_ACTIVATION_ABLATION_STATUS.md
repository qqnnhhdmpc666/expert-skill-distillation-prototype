# Task-Conditioned Activation Ablation Status

Generated at: `2026-06-12T11:39:00.111764+00:00`

Ablation variants are temporary experiment packages. They do not overwrite the installed active package.

## Summary

- Sample count: `6`
- Mechanism status: `supports_mechanism`

| Variant | Case | Expected group | Activated group | Score delta | FP count | Scope violation |
|---|---|---|---|---:|---:|---:|
| active_installed | holdout_upload_double_extension_001 | upload_security | upload_security | 0.0 | 0 | False |
| ablated_no_out_of_scope_guard | holdout_upload_double_extension_001 | upload_security | upload_security | 0.0 | 0 | False |
| ablated_all_capabilities_always_on | holdout_upload_double_extension_001 | upload_security | all_capabilities_always_on | -0.2 | 7 | True |
| ablated_no_task_router | holdout_upload_double_extension_001 | upload_security | out_of_scope_guard | -0.2 | 0 | True |
| active_installed | holdout_config_prod_secret_001 | config_security | config_security | 0.0 | 0 | False |
| ablated_no_out_of_scope_guard | holdout_config_prod_secret_001 | config_security | config_security | 0.0 | 0 | False |
| ablated_all_capabilities_always_on | holdout_config_prod_secret_001 | config_security | all_capabilities_always_on | -0.2 | 8 | True |
| ablated_no_task_router | holdout_config_prod_secret_001 | config_security | out_of_scope_guard | -0.2 | 0 | True |
| active_installed | holdout_auth_project_ownership_001 | auth_access_control | auth_access_control | 0.0 | 0 | False |
| ablated_no_out_of_scope_guard | holdout_auth_project_ownership_001 | auth_access_control | auth_access_control | 0.0 | 0 | False |
| ablated_all_capabilities_always_on | holdout_auth_project_ownership_001 | auth_access_control | all_capabilities_always_on | -0.2 | 7 | True |
| ablated_no_task_router | holdout_auth_project_ownership_001 | auth_access_control | out_of_scope_guard | -0.2 | 0 | True |
| active_installed | holdout_api_overbroad_schema_001 | api_or_code_review | api_or_code_review | 0.0 | 0 | False |
| ablated_no_out_of_scope_guard | holdout_api_overbroad_schema_001 | api_or_code_review | api_or_code_review | 0.0 | 0 | False |
| ablated_all_capabilities_always_on | holdout_api_overbroad_schema_001 | api_or_code_review | all_capabilities_always_on | -0.2 | 8 | True |
| ablated_no_task_router | holdout_api_overbroad_schema_001 | api_or_code_review | out_of_scope_guard | -0.2 | 0 | True |
| active_installed | holdout_clean_tax_math_001 | out_of_scope_guard | out_of_scope_guard | 0.0 | 0 | False |
| ablated_no_out_of_scope_guard | holdout_clean_tax_math_001 | out_of_scope_guard | upload_security | -0.2 | 3 | True |
| ablated_all_capabilities_always_on | holdout_clean_tax_math_001 | out_of_scope_guard | all_capabilities_always_on | -0.2 | 10 | True |
| ablated_no_task_router | holdout_clean_tax_math_001 | out_of_scope_guard | out_of_scope_guard | 0.0 | 0 | False |
| active_installed | holdout_dependency_no_advisory_001 | out_of_scope_guard | out_of_scope_guard | 0.0 | 0 | False |
| ablated_no_out_of_scope_guard | holdout_dependency_no_advisory_001 | out_of_scope_guard | upload_security | -0.2 | 3 | True |
| ablated_all_capabilities_always_on | holdout_dependency_no_advisory_001 | out_of_scope_guard | all_capabilities_always_on | -0.2 | 10 | True |
| ablated_no_task_router | holdout_dependency_no_advisory_001 | out_of_scope_guard | out_of_scope_guard | 0.0 | 0 | False |
