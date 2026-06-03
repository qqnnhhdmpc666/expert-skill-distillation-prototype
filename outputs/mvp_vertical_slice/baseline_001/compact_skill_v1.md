# API Review Compact Skill v1

Use this skill to review an API specification. Focus on actionable findings, not long explanations.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit. Status: supported.
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints. Status: supported.
- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors. Status: supported.
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses. Status: supported.

## Output Format

Return JSON only:

```json
{
  "passed": false,
  "failed_rules": ["R001"],
  "findings": [
    {"rule_id": "R001", "severity": "high", "message": "Finding text", "evidence": "Spec excerpt"}
  ],
  "suggested_patch": ["Concrete API spec improvement"]
}
```
