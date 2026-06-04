# API Review Compact Skill v2 from SPARK Feedback

Use this skill to review an API specification. This version is generated from rule_ledger decisions after SPARK-compatible execution feedback.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit. Decision: keep; material: supported; execution: detected.
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints. Decision: keep; material: supported; execution: detected.
- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors. Decision: keep; material: supported; execution: detected.
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses. Decision: keep; material: supported; execution: detected.
- [R005] Check consistent envelope fields: code, message, request_id, and data. Decision: patch; material: supported; execution: failure_critical.
- [R006] Check whether mutation endpoints document idempotency or duplicate submission handling. Decision: patch; material: supported; execution: failure_critical.

## Output Format

Return JSON only with `passed`, `failed_rules`, `findings`, and `suggested_patch`.
