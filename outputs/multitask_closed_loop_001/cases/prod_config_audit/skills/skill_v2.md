# Production configuration security review Skill v2

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

## Output Contract

Return JSON with `findings`. Each finding must include `capability_id`, `issue`, `severity`, `evidence_span`, and `recommended_fix`.

## Negative Guard Patch

Do not flag dev/test placeholders or already-HTTPS production endpoints as production findings. First bind every finding to its environment block.
