# API Review Compact Skill - risk-cost

Use this budgeted compact skill to review an API specification.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit. Decision: selected by risk-cost
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints. Decision: selected by risk-cost
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses. Decision: selected by risk-cost
- [R005] Check consistent envelope fields: code, message, request_id, and data. Decision: selected by risk-cost
- [R007] Check request_id, trace metadata, and audit logging expectations. Decision: selected by risk-cost

## Output Format

Return JSON only with findings containing `rule_id`, `severity`, `message`, and `evidence`.
