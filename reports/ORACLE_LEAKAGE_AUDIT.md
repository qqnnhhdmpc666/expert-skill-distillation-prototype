# Oracle Leakage Audit

Generated at: `2026-06-12T11:46:25.698371+00:00`

Scope: local defensive security mini-suite, mini-suite runner artifacts, installed Skill packages, evidence bundles, and candidate-generation inputs.

## Case-Level Result

| suite | case_id | agent_visible_fields | verifier_only_fields | leakage_found | affected_artifact | decision |
|---|---|---|---|---|---|---|
| cases.json | mini_upload_magic_path_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_upload_public_storage_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_config_prod_audit_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_config_env_guard_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_auth_invoice_scope_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_auth_owner_boundary_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_api_schema_grounding_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases.json | mini_dependency_version_risk_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding<br>unsupported_limitation | False | none | valid |
| cases.json | mini_clean_out_of_scope_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| holdout_cases.json | holdout_upload_double_extension_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| holdout_cases.json | holdout_config_prod_secret_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| holdout_cases.json | holdout_auth_project_ownership_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| holdout_cases.json | holdout_api_overbroad_schema_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| holdout_cases.json | holdout_clean_tax_math_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| holdout_cases.json | holdout_dependency_no_advisory_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding<br>unsupported_limitation | False | none | valid |
| cases_extended.json | mini_upload_magic_path_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_upload_public_storage_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_config_prod_audit_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_config_env_guard_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_auth_invoice_scope_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_auth_owner_boundary_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_api_schema_grounding_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | mini_dependency_version_risk_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding<br>unsupported_limitation | False | none | valid |
| cases_extended.json | mini_clean_out_of_scope_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | holdout_upload_double_extension_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | holdout_config_prod_secret_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | holdout_auth_project_ownership_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | holdout_api_overbroad_schema_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | holdout_clean_tax_math_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | holdout_dependency_no_advisory_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding<br>unsupported_limitation | False | none | valid |
| cases_extended.json | extended_upload_public_exec_003 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | extended_input_validation_limitation_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding<br>unsupported_limitation | False | none | valid |
| cases_extended.json | extended_clean_reporting_002 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | extended_clean_profile_003 | requested_output_schema<br>snippet<br>task_family<br>task_text | clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |
| cases_extended.json | extended_ambiguous_low_confidence_001 | requested_output_schema<br>snippet<br>task_family<br>task_text | ambiguous<br>clean_or_negative<br>expected_capabilities<br>expected_capability_group<br>expected_evidence_span<br>expected_security_finding | False | none | valid |

## Candidate Generation Inputs

| artifact | leakage_found | forbidden_key_mentions | oracle_value_hits |
|---|---:|---|---|
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\candidates\clean_false_positive_guard__v3_candidate_002\candidate_generation_inputs.json | False | none | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\candidates\config_security_001__v3_candidate_001\candidate_generation_inputs.json | False | none | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\candidates\dependency_version_risk__v3_candidate_003\candidate_generation_inputs.json | False | none | none |

## Evidence Bundle Runtime Flag

- Evidence bundle rows checked: `80`
- Any runtime oracle visibility issue: `False`

## Decision

- Overall status: `pass`
- No case is excluded from security_depth if overall status is `pass`.
