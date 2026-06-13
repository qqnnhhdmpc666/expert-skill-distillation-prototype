# Defensive Secure Review Skill config_security_001 v2

Safety boundary: defensive review only. Do not generate exploits, attack chains, or real-target automation.

Task family: `config_security`

## Capabilities

### CONFIG_AUDIT_EXPORT: Production audit retention/export
- Evidence: prod.audit enabled but retention_days/export_sink missing
- Fix: Require retention and export sink for production audit logs.

### CONFIG_ENV_GUARD: Environment-aware config guard
- Evidence: dev api_token/debug should not be production findings
- Fix: Bind findings to prod/dev/test path before flagging.

## Candidate Realization Constraint

- Force explicit expression of CONFIG_ENV_GUARD in the generated finding.
