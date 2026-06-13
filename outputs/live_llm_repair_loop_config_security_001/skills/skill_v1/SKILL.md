# Production configuration security check Skill v1

Task family: `config_security`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### CONFIG_AUDIT_EXPORT: Production audit retention/export
- Evidence: prod.audit enabled but retention_days/export_sink missing
- Fix: Require retention and export sink for production audit logs.
