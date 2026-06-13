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

## Iterative Contract Candidate: API Contract Precision

For `api_or_code_review`, keep the two capabilities separate:

- Emit `API_SCHEMA_CONTRACT` when the target says a report builder emits prose or otherwise lacks required structured fields such as `capability_id`, `evidence_span`, or `recommended_fix`.
- Emit `API_OVERBROAD_RISK` when a risk label such as `debug_path` is asserted without a concrete target line, route, production caller, response field, or evidence span.

If a note says something *might* happen in the future but no route, caller, response schema, production path, or emitted field is shown, do not emit a concrete finding. Use no findings or low-confidence notes.
