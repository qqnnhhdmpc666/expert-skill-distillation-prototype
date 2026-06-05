# Validation-Aware Compact Skill - candidate_C_compressed_required_rules

Preserve R001-R006 by using compressed checklist wording. This is success with compressed wording, not natural success of the original selector.

## Checklist

- [R001] Auth method, roles/scopes, and auth-failure behavior.
- [R002] Request fields: required/default, type, range, length, enum.
- [R003] Stable error codes for validation, auth, permission, not found, duplicate, server.
- [R004] No tokens, secrets, stack traces, identity, or unnecessary personal data.
- [R005] Response envelope: code, message, request_id, data.
- [R006] Mutation idempotency or duplicate-submission handling.

## Output Format

Return JSON only. Each finding must include `rule_id`, `severity`, `message`, and `evidence`.
