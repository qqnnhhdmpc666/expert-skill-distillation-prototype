# Secure Code Review Installed Runtime v2

This installed runtime uses task-conditioned capability activation inside the controlled secure-review prototype.

## Safety Boundary

- Allowed: defensive detection, explanation, fix recommendation, patch validation.
- Forbidden: exploit generation, attack-chain execution, unauthorized target testing.

## Capability Groups

### upload_security
- task_families: `upload_security`
- capabilities:
  - `UPLOAD_PATH_ISOLATION`
  - `UPLOAD_TYPE_MAGIC`
  - `UPLOAD_AUDIT_RETENTION`

### config_security
- task_families: `config_security`
- capabilities:
  - `CONFIG_AUDIT_EXPORT`
  - `CONFIG_ENV_GUARD`

### api_or_code_review
- task_families: `api_or_code_review`
- capabilities:
  - `API_SCHEMA_CONTRACT`
  - `API_OVERBROAD_RISK`

### auth_access_control
- task_families: `auth_access_control`
- capabilities:
  - `AUTH_SCOPE_MATRIX`
  - `AUTH_OBJECT_OWNERSHIP`
  - `AUTH_ERROR_ENVELOPE`

### out_of_scope_guard
- task_families: `none`
- capabilities:
  - none

## Output Contract

- `capability_id`
- `evidence_span`
- `recommended_fix`

## Contract-Grounded Improvement Candidate

This candidate is generated only from verifier feedback, evidence summaries, and normalization traces. It does not expand secure_code_review scope.

### Live Checklist Strengthening

- Treat active capabilities as independent checklist items, not as a menu of optional examples.
- For `AUTH_SCOPE_MATRIX`, report when the target says access checks only authentication or lacks role/scope authorization. Keep this separate from object ownership.
- For `API_OVERBROAD_RISK`, report when the target says a risk such as debug_path is generic, ungrounded, or lacks a target evidence span. Keep this separate from the JSON schema contract.
- Positive observations are not findings: if upload validation, server filename generation, storage isolation, or audit retention are already present, emit no finding for that capability.
- For unsupported dependency, regex DoS, server-side code execution, and other task families outside the manifest, keep `out_of_scope_guard` behavior and emit no findings.

### Boundaries

- Do not add dependency/version-risk, regex DoS, or code execution review to core capabilities.
- Do not generate exploit steps or attack chains.
- Use exact complete target lines as evidence spans; if exact evidence is absent, prefer no finding or needs_review/low_confidence trace.

### Failure Evidence Used

- `independent_upload_clean_001` from `external_generalization`: feedback=`false_positive_risk`, false_positive_count=`1`, artifact=`C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_upload_clean_001\live_llm_text`
- `independent_config_prod_audit_001` from `external_generalization`: feedback=`missing_capability`, false_positive_count=`0`, artifact=`C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_config_prod_audit_001\live_llm_text`
- `independent_auth_invoice_scope_001` from `external_generalization`: feedback=`missing_capability`, false_positive_count=`0`, artifact=`C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_auth_invoice_scope_001\live_llm_text`
- `independent_api_schema_001` from `external_generalization`: feedback=`missing_capability`, false_positive_count=`0`, artifact=`C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_generalization_validation\cases\independent_api_schema_001\live_llm_text`
- `holdout_auth_project_ownership_001` from `live_contract_validation`: feedback=`missing_capability`, false_positive_count=`0`, artifact=`C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\live_contract_validation\cases\holdout_auth_project_ownership_001\live_llm_contract`
