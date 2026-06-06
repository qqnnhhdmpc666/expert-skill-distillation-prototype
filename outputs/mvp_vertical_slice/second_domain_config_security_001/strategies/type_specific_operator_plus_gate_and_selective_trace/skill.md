# type_specific_operator_plus_gate_and_selective_trace

## Rules
- [C001] No hardcoded secrets; require vault/env refs.
- [C002] Production external URLs must use https.
- [C003] Avoid admin/wildcard service-account roles.
- [C004] Production debug must be false.
- [C005] Define CPU/memory requests or limits.
- [C006] Enable audit logging with retention/export.

## Output Contract

Return JSON findings with rule_id, issue, severity, evidence, and config_path.

## Trace Contract

For traced rules, add rule_applications with rule_id, finding_id, trigger, evidence_span, config_path, confidence.
Traced rules: C006.
