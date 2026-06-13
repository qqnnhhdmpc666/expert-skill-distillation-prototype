# Authorization and object access review Skill v2

Task family: `auth_access_control`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### AUTH_SCOPE_MATRIX: Role and scope authorization
- Evidence: delete_invoice checks only is_authenticated
- Fix: Check required role/scope before mutation.

### AUTH_OBJECT_OWNERSHIP: Object ownership boundary
- Evidence: invoice loaded without tenant_id or owner_id check
- Fix: Bind resource access to tenant and owner.

### AUTH_ERROR_ENVELOPE: Non-leaking authorization error
- Evidence: permission errors reveal object existence
- Fix: Use consistent 403/404 envelope with request id.

## Revision Policy

Applied repair action: `patch_boundary`.
