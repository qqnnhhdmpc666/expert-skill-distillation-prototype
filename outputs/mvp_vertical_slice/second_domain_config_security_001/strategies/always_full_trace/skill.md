# always_full_trace

## Rules
- [C001] Do not hardcode tokens, passwords, API keys, or private credentials in configuration files; use secret references.
- [C002] Production external endpoints must use https/TLS; plain http endpoints are not acceptable.
- [C003] Service accounts should avoid admin, wildcard, or broad write roles unless explicitly justified.
- [C004] Production deployments must set debug=false.
- [C005] Containers or services should define CPU and memory requests or limits.
- [C006] Security-sensitive services should enable audit logging and define retention or export behavior.

## Output Contract

Return JSON findings with rule_id, issue, severity, evidence, and config_path.

## Trace Contract

For traced rules, add rule_applications with rule_id, finding_id, trigger, evidence_span, config_path, confidence.
Traced rules: C001, C002, C003, C004, C005, C006.
