# Validation-Aware Compact Skill - candidate_B_preserve_covered_first

Preserve all previously covered R001-R004 and add failure-critical R005/R006 with original wording.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit.
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints.
- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors.
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses.
- [R005] Check consistent envelope fields: code, message, request_id, and data.
- [R006] Check whether mutation endpoints document idempotency or duplicate submission handling.

## Output Format

Return JSON only. Each finding must include `rule_id`, `severity`, `message`, and `evidence`.
