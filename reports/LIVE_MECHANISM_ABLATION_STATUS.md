# Live Mechanism Ablation Status

Generated at: `2026-06-12T18:19:12.016139+00:00`

This ablation compares the active contract-grounded runtime against bounded live variants. It is local live evidence, not an official benchmark.

## Summary

- Cases: `7`
- Variants: `active_contract_system, no_evidence_normalizer, no_out_of_scope_guard, all_capabilities_always_on, no_task_router, simple_prompt_baseline`
- `mechanism_ablation`: `supports_mechanism`

## Variant Metrics

| Variant | Completed | Pass | FP | Scope violations | Unsupported evidence | Schema errors | Avg score |
|---|---:|---:|---:|---:|---:|---:|---:|
| active_contract_system | 7 | 3 | 0 | 0 | 0 | 0 | 0.8381 |
| no_evidence_normalizer | 7 | 3 | 0 | 0 | 0 | 0 | 0.8238 |
| no_out_of_scope_guard | 7 | 6 | 0 | 2 | 0 | 0 | 0.9571 |
| all_capabilities_always_on | 7 | 3 | 0 | 7 | 0 | 0 | 0.8238 |
| no_task_router | 7 | 3 | 0 | 5 | 0 | 0 | 0.7714 |
| simple_prompt_baseline | 7 | 4 | 0 | 7 | 0 | 0 | 0.8619 |

## Rows

| Variant | Case | Status | Verifier | FP | Scope violation | Score | Artifacts |
|---|---|---|---|---:|---:|---:|---|
| active_contract_system | holdout_upload_double_extension_001 | completed | fail:missing_capability | 0 | False | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_upload_double_extension_001\active_contract_system` |
| no_evidence_normalizer | holdout_upload_double_extension_001 | completed | fail:missing_capability | 0 | False | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_upload_double_extension_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_upload_double_extension_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_upload_double_extension_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_upload_double_extension_001 | completed | fail:missing_capability | 0 | True | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_upload_double_extension_001\all_capabilities_always_on` |
| no_task_router | holdout_upload_double_extension_001 | completed | fail:missing_capability | 0 | True | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_upload_double_extension_001\no_task_router` |
| simple_prompt_baseline | holdout_upload_double_extension_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_upload_double_extension_001\simple_prompt_baseline` |
| active_contract_system | holdout_config_prod_secret_001 | completed | fail:missing_capability | 0 | False | 0.7 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_config_prod_secret_001\active_contract_system` |
| no_evidence_normalizer | holdout_config_prod_secret_001 | completed | fail:missing_capability | 0 | False | 0.7 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_config_prod_secret_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_config_prod_secret_001 | completed | fail:missing_capability | 0 | False | 0.7 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_config_prod_secret_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_config_prod_secret_001 | completed | fail:missing_capability | 0 | True | 0.7 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_config_prod_secret_001\all_capabilities_always_on` |
| no_task_router | holdout_config_prod_secret_001 | completed | fail:missing_capability | 0 | True | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_config_prod_secret_001\no_task_router` |
| simple_prompt_baseline | holdout_config_prod_secret_001 | completed | fail:missing_capability | 0 | True | 0.7 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_config_prod_secret_001\simple_prompt_baseline` |
| active_contract_system | holdout_auth_project_ownership_001 | completed | fail:missing_capability | 0 | False | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_auth_project_ownership_001\active_contract_system` |
| no_evidence_normalizer | holdout_auth_project_ownership_001 | completed | fail:missing_capability | 0 | False | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_auth_project_ownership_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_auth_project_ownership_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_auth_project_ownership_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_auth_project_ownership_001 | completed | fail:missing_capability | 0 | True | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_auth_project_ownership_001\all_capabilities_always_on` |
| no_task_router | holdout_auth_project_ownership_001 | completed | fail:missing_capability | 0 | True | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_auth_project_ownership_001\no_task_router` |
| simple_prompt_baseline | holdout_auth_project_ownership_001 | completed | fail:missing_capability | 0 | True | 0.7333 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_auth_project_ownership_001\simple_prompt_baseline` |
| active_contract_system | holdout_api_overbroad_schema_001 | completed | fail:missing_capability | 0 | False | 0.7 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_api_overbroad_schema_001\active_contract_system` |
| no_evidence_normalizer | holdout_api_overbroad_schema_001 | completed | fail:missing_capability | 0 | False | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_api_overbroad_schema_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_api_overbroad_schema_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_api_overbroad_schema_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_api_overbroad_schema_001 | completed | fail:missing_capability | 0 | True | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_api_overbroad_schema_001\all_capabilities_always_on` |
| no_task_router | holdout_api_overbroad_schema_001 | completed | fail:missing_capability | 0 | True | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_api_overbroad_schema_001\no_task_router` |
| simple_prompt_baseline | holdout_api_overbroad_schema_001 | completed | fail:missing_capability | 0 | True | 0.6 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_api_overbroad_schema_001\simple_prompt_baseline` |
| active_contract_system | holdout_clean_tax_math_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_clean_tax_math_001\active_contract_system` |
| no_evidence_normalizer | holdout_clean_tax_math_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_clean_tax_math_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_clean_tax_math_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_clean_tax_math_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_clean_tax_math_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_clean_tax_math_001\all_capabilities_always_on` |
| no_task_router | holdout_clean_tax_math_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_clean_tax_math_001\no_task_router` |
| simple_prompt_baseline | holdout_clean_tax_math_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_clean_tax_math_001\simple_prompt_baseline` |
| active_contract_system | holdout_dependency_no_advisory_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_dependency_no_advisory_001\active_contract_system` |
| no_evidence_normalizer | holdout_dependency_no_advisory_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_dependency_no_advisory_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_dependency_no_advisory_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_dependency_no_advisory_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_dependency_no_advisory_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_dependency_no_advisory_001\all_capabilities_always_on` |
| no_task_router | holdout_dependency_no_advisory_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_dependency_no_advisory_001\no_task_router` |
| simple_prompt_baseline | holdout_dependency_no_advisory_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_dependency_no_advisory_001\simple_prompt_baseline` |
| active_contract_system | holdout_ambiguous_debug_path_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_ambiguous_debug_path_001\active_contract_system` |
| no_evidence_normalizer | holdout_ambiguous_debug_path_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_ambiguous_debug_path_001\no_evidence_normalizer` |
| no_out_of_scope_guard | holdout_ambiguous_debug_path_001 | completed | pass:pass | 0 | False | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_ambiguous_debug_path_001\no_out_of_scope_guard` |
| all_capabilities_always_on | holdout_ambiguous_debug_path_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_ambiguous_debug_path_001\all_capabilities_always_on` |
| no_task_router | holdout_ambiguous_debug_path_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_ambiguous_debug_path_001\no_task_router` |
| simple_prompt_baseline | holdout_ambiguous_debug_path_001 | completed | pass:pass | 0 | True | 1.0 | `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\mechanism_ablation\live_contract\cases\holdout_ambiguous_debug_path_001\simple_prompt_baseline` |
