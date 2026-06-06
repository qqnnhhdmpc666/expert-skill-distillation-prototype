# compact_v1_no_revision

## Rules
- [C001] Do not hardcode tokens, passwords, API keys, or private credentials in configuration files; use secret references.
- [C002] Production external endpoints must use https/TLS; plain http endpoints are not acceptable.
- [C003] Service accounts should avoid admin, wildcard, or broad write roles unless explicitly justified.
- [C004] Production deployments must set debug=false.
- [C005] Containers or services should define CPU and memory requests or limits.

## Output Contract

Return JSON findings with rule_id, issue, severity, evidence, and config_path.
