# Defensive Secure Review Skill upload_security_001 v2

Safety boundary: defensive review only. Do not generate exploits, attack chains, or real-target automation.

Task family: `upload_security`

## Capabilities

### UPLOAD_PATH_ISOLATION: Upload path isolation
- Evidence: UPLOAD_ROOT / filename writes a user name into /public/uploads
- Fix: Generate server-side names and store outside public executable roots.

### UPLOAD_AUDIT_RETENTION: Upload audit retention
- Evidence: audit_log_retention_days is empty and handlers write no audit event
- Fix: Record actor/object/action/result/timestamp with retention.

### UPLOAD_TYPE_MAGIC: Upload type and content validation
- Evidence: filename.endswith without MIME or magic-byte validation
- Fix: Validate MIME, signature, size, and extension together.
