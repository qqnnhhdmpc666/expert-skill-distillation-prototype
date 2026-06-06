# Full Config Security Skill

## Rules
- [C001] No hardcoded secrets: Do not hardcode tokens, passwords, API keys, or private credentials in configuration files; use secret references. Severity: high. Config path: secrets or credential-like fields.
- [C002] TLS for production endpoints: Production external endpoints must use https/TLS; plain http endpoints are not acceptable. Severity: high. Config path: external_api_url.
- [C003] Least-privilege service accounts: Service accounts should avoid admin, wildcard, or broad write roles unless explicitly justified. Severity: high. Config path: service_account.roles.
- [C004] Disable production debug: Production deployments must set debug=false. Severity: high. Config path: debug.
- [C005] Runtime resource limits: Containers or services should define CPU and memory requests or limits. Severity: medium. Config path: resources.
- [C006] Audit logging and retention: Security-sensitive services should enable audit logging and define retention or export behavior. Severity: medium. Config path: audit.

## Output Contract

Return JSON findings with rule_id, issue, severity, evidence, and config_path.
