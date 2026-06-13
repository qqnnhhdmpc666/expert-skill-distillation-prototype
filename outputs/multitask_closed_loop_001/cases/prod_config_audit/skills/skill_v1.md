# Production configuration security review Skill v1

## Scenario

- Task family: `config_security`
- Purpose: turn expert knowledge into executable, verifier-checkable review behavior.

## Expert Material

Configuration review must separate production from dev/test blocks, avoid false positives, and verify secrets, TLS, least privilege, debug state, audit retention, and export sinks.

## Capabilities

### CONFIG_AUDIT_EXPORT: Security audit logs need retention and export sink
- Severity: medium
- Evidence to look for: prod.audit.enabled is true but retention_days and export_sink are missing
- Recommended fix pattern: Require retention_days and export_sink for production audit logs.

### CONFIG_SECRET_REF: Production config must use secret references rather than literals
- Severity: high
- Evidence to look for: api_token is a test placeholder in a dev-only block, not production
- Recommended fix pattern: Gate findings on environment and ignore explicitly dev/test-only placeholders.

### CONFIG_TLS: Production external endpoints must use TLS
- Severity: high
- Evidence to look for: prod.external_url uses https, so this should not be flagged
- Recommended fix pattern: Check scheme only in production endpoints and avoid flagging compliant https values.

## Output Contract

Return JSON with `findings`. Each finding must include `capability_id`, `issue`, `severity`, `evidence_span`, and `recommended_fix`.
