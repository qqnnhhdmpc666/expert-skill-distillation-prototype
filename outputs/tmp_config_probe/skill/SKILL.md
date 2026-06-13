# Config Security Skill

## Capabilities

### CONFIG_AUDIT_EXPORT
- Evidence: prod.audit enabled but retention_days/export_sink missing
- Fix: Require retention and export sink for production audit logs.

### CONFIG_ENV_GUARD
- Evidence: dev api_token/debug should not be production findings
- Fix: Bind findings to prod/dev/test path before flagging.
