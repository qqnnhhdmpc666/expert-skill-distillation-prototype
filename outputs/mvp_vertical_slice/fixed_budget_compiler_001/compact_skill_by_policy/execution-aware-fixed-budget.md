# API Review Compact Skill - execution-aware-fixed-budget

Use this budgeted compact skill to review an API specification.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit. Decision: selected by execution-aware fixed-budget compiler
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints. Decision: selected by execution-aware fixed-budget compiler
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses. Decision: selected by execution-aware fixed-budget compiler
- [R005] Check consistent envelope fields: code, message, request_id, and data. Decision: selected by execution-aware fixed-budget compiler
- [R006] Check whether mutation endpoints document idempotency or duplicate submission handling. Decision: selected by execution-aware fixed-budget compiler

## Output Format

Return JSON only with findings containing `rule_id`, `severity`, `message`, and `evidence`.
