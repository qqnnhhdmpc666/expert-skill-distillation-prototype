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

## Iterative Contract Candidate: Auth Scope Matrix Precision

For `auth_access_control`, evaluate the three auth capabilities separately:

- Emit `AUTH_SCOPE_MATRIX` when the target only checks authentication, but does not bind the operation to a role, scope, tenant, or permission matrix.
- Emit `AUTH_OBJECT_OWNERSHIP` when an object is loaded by id without tenant_id, owner_id, account_id, or equivalent ownership filtering.
- Emit `AUTH_ERROR_ENVELOPE` when denial or error output includes stable object identifiers or business ids instead of a neutral request id.

Do not apply this rule to clean targets that already include required role scope, tenant/owner filtering, and request-id-only denial output. Do not expand into dependency, regex, or server-side execution review.
