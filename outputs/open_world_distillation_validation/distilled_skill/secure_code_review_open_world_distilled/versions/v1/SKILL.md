# secure_code_review_open_world_distilled Installed Runtime v1

This installed runtime was distilled from expert materials, not manually written as a one-off prompt.

## Distillation Metadata

- distillation_method: `keyword_projection_from_open_materials`
- runtime_task_family: `multi_task_open_material_distilled`
- source_cases: `public_upload_material_001`, `public_auth_material_001`, `public_config_material_001`

## Capability Groups

### upload_security
- task_families: `upload_security`
- distilled_from: `public_upload_material_001`
- capabilities:
  - `UPLOAD_TYPE_MAGIC`: Upload type and content validation
  - `UPLOAD_PATH_ISOLATION`: Upload path isolation

### auth_access_control
- task_families: `auth_access_control`
- distilled_from: `public_auth_material_001`
- capabilities:
  - `AUTH_SCOPE_MATRIX`: Role and scope authorization
  - `AUTH_OBJECT_OWNERSHIP`: Object ownership boundary
  - `AUTH_ERROR_ENVELOPE`: Non-leaking authorization error

### config_security
- task_families: `config_security`
- distilled_from: `public_config_material_001`
- capabilities:
  - `CONFIG_AUDIT_EXPORT`: Production audit retention/export
  - `CONFIG_ENV_GUARD`: Environment-aware config guard

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
