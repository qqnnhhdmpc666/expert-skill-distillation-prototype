# Validation-Aware Compact Skill - candidate_A_naive_execution_aware

Naive execution-aware fixed-budget selection from fixed_budget_compiler_001. It recovers R005/R006 but drops R003.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit.
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints.
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses.
- [R005] Check consistent envelope fields: code, message, request_id, and data.
- [R006] Check whether mutation endpoints document idempotency or duplicate submission handling.

## Output Format

Return JSON only. Each finding must include `rule_id`, `severity`, `message`, and `evidence`.
