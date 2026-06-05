# API Review Compact Skill - priority-only

Use this budgeted compact skill to review an API specification.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit. Decision: selected by priority-only
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints. Decision: selected by priority-only
- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors. Decision: selected by priority-only
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses. Decision: selected by priority-only

## Output Format

Return JSON only with findings containing `rule_id`, `severity`, `message`, and `evidence`.
