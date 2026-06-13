# File upload security review Skill v2

Task family: `upload_security`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### UPLOAD_TYPE_MAGIC: Upload type and content validation
- Evidence: filename.endswith without MIME or magic-byte validation
- Fix: Validate MIME, signature, size, and extension together.

### UPLOAD_PATH_ISOLATION: Upload path isolation
- Evidence: UPLOAD_ROOT / filename writes a user name into /public/uploads
- Fix: Generate server-side names and store outside public executable roots.

### UPLOAD_AUDIT_RETENTION: Upload audit retention
- Evidence: audit_log_retention_days is empty and handlers write no audit event
- Fix: Record actor/object/action/result/timestamp with retention.
