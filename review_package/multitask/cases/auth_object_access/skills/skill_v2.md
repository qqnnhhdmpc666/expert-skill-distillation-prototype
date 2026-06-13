# Authorization and object ownership review Skill v2

## Scenario

- Task family: `access_control`
- Purpose: turn expert knowledge into executable, verifier-checkable review behavior.

## Expert Material

Authorization review must distinguish authentication, role/scope authorization, object ownership, tenant boundary, and non-leaking error behavior.

## Capabilities

### AUTH_SCOPE_MATRIX: Privileged endpoints need explicit role and scope matrix
- Severity: high
- Evidence to look for: delete_invoice() accepts user_id but checks only is_authenticated
- Recommended fix pattern: Define required roles/scopes per operation and verify them before mutation.

### AUTH_OBJECT_OWNERSHIP: Object access must bind the resource owner or tenant boundary
- Severity: high
- Evidence to look for: invoice_id is loaded without checking tenant_id or owner_id against the caller
- Recommended fix pattern: Check tenant/resource ownership before returning or mutating objects.

### AUTH_ERROR_ENVELOPE: Authorization failures need non-leaking error envelope
- Severity: medium
- Evidence to look for: raw permission details can reveal whether an invoice id exists
- Recommended fix pattern: Return consistent 403/404 style envelopes with request_id and no internal policy details.

## Output Contract

Return JSON with `findings`. Each finding must include `capability_id`, `issue`, `severity`, `evidence_span`, and `recommended_fix`.

## Evidence Protocol Patch

For access-control findings, evidence must name the exact unchecked boundary: role/scope, object owner, tenant id, or error envelope.
