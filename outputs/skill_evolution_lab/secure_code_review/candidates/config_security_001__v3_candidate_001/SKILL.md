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

## Candidate Constraint: config realization constraint

- Evidence-bound rationale: Mini-suite and internal evidence require config findings to express environment-aware audit/export reasoning without broadening scope.
- Scope note: No new task family is added; only config_security wording is constrained.
- Promotion requires strict score gain, no false-positive increase, no schema-error increase, and no scope violation.
