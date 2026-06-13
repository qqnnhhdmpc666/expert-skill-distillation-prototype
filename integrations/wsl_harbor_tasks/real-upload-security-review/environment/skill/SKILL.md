# Harbor Upload Security Skill

Task family: `upload_security`

## Inspection Procedure

1. Read `/app/target/app.py` and `/app/target/config.yaml`.
2. Emit only findings grounded in concrete target spans.
3. Follow the verifier contract: `capability_id`, `evidence_span`, `recommended_fix`.

## Capabilities

### UPLOAD_TYPE_MAGIC

- Check whether upload validation relies only on filename extensions.
- Look for missing MIME type, magic-byte, size, and content validation.

### UPLOAD_PATH_ISOLATION

- Check whether user-controlled filenames are joined into public upload paths.
- Look for public/executable upload roots or returned internal paths.

### UPLOAD_AUDIT_RETENTION

- Check whether upload/download/delete events have audit logs and retention policy.
- Look for empty `audit_log_retention_days` or handlers without audit events.

## Boundary

This Skill is for a controlled Harbor upload-security task. It is not a general vulnerability scanner.
