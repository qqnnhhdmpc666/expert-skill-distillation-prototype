# Protocolized Compressed Skill

Use the compact rules below and expose how each rule was applied to the case.

## Checklist

- [R001] Auth method, roles/scopes, and auth-failure behavior.
- [R002] Request fields: required/default, type, range, length, enum.
- [R003] Stable error codes for validation, auth, permission, not found, duplicate, server.
- [R004] No tokens, secrets, stack traces, identity, or unnecessary personal data.
- [R005] Response envelope: code, message, request_id, data.
- [R006] Mutation idempotency or duplicate-submission handling.

## Skill Invocation Protocol

Return JSON only with both `rule_applications` and `findings`.
Each finding must be supported by exactly one rule_application through `finding_id`.

```json
{
  "rule_applications": [
    {
      "rule_id": "R005",
      "applicable": true,
      "trigger_condition_found": "response envelope missing request_id",
      "evidence_span": "Response JSON has code, message, data",
      "finding_id": "F5",
      "confidence": "medium"
    }
  ],
  "findings": [
    {
      "id": "F5",
      "rule_id": "R005",
      "issue": "...",
      "severity": "high|medium|low",
      "evidence": "..."
    }
  ]
}
```
