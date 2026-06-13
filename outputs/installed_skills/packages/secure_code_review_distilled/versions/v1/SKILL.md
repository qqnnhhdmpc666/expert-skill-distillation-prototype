# secure_code_review_distilled Installed Runtime v1

This installed runtime was distilled from expert materials, not manually written as a one-off prompt.

## Distillation Metadata

- distillation_method: `keyword_projection_from_expert_materials`
- runtime_task_family: `multi_task_expert_distilled`
- source_cases: `api_review_001`, `auth_access_control_001`, `config_security_001`, `upload_security_001`

## Capability Groups

### api_or_code_review
- task_families: `api_or_code_review`
- distilled_from: `api_review_001`
- capabilities:
  - `API_SCHEMA_CONTRACT`: Strict report schema
  - `API_OVERBROAD_RISK`: Overbroad finding control

### auth_access_control
- task_families: `auth_access_control`
- distilled_from: `auth_access_control_001`
- capabilities:
  - `AUTH_SCOPE_MATRIX`: Role and scope authorization
  - `AUTH_OBJECT_OWNERSHIP`: Object ownership boundary
  - `AUTH_ERROR_ENVELOPE`: Non-leaking authorization error

### config_security
- task_families: `config_security`
- distilled_from: `config_security_001`
- capabilities:
  - `CONFIG_AUDIT_EXPORT`: Production audit retention/export
  - `CONFIG_ENV_GUARD`: Environment-aware config guard

### upload_security
- task_families: `upload_security`
- distilled_from: `upload_security_001`
- capabilities:
  - `UPLOAD_TYPE_MAGIC`: Upload type and content validation
  - `UPLOAD_PATH_ISOLATION`: Upload path isolation
  - `UPLOAD_AUDIT_RETENTION`: Upload audit retention

### out_of_scope_guard
- task_families: `none`
- capabilities:
  - none

## Output Contract

- `capability_id`
- `evidence_span`
- `recommended_fix`

## Safety Boundary

- Defensive review only.
- Unsupported task families must activate `out_of_scope_guard` and avoid unrelated findings.
