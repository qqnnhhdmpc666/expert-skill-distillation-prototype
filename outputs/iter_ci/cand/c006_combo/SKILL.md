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

## Iterative Contract Candidate: Composed Low-Scope Contract Patch

Apply the following narrow live-output discipline:

1. Positive observations are notes, not findings. Existing checks, generated filenames, configured retention, tenant/owner filters, role scopes, and request-id denial envelopes should not be reported as problems.
2. Auth findings must be separated into `AUTH_SCOPE_MATRIX`, `AUTH_OBJECT_OWNERSHIP`, and `AUTH_ERROR_ENVELOPE` only when exact target lines support each one.
3. API findings must distinguish missing structured output fields from overbroad risk labels. Future or hypothetical debug notes without route/schema/caller evidence should produce no concrete finding.
4. Config findings must distinguish missing audit export/retention from environment profile guard issues. Dev-only tokens are not production findings when they are explicitly fenced.
5. Unsupported dependency/version, regex DoS, and server-side execution review remain out of scope for `secure_code_review`.
