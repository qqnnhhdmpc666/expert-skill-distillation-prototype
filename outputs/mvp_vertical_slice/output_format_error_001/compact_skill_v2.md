# API Review Compact Skill v1

Use this skill to review an API specification. The checklist is selected from rule_ledger decisions.

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit. Decision: keep; material: supported; execution: not_observed.
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints. Decision: keep; material: supported; execution: not_observed.
- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors. Decision: keep; material: supported; execution: not_observed.
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses. Decision: keep; material: supported; execution: not_observed.

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

## Output Contract Patch

This patch addresses `output_format_error`, not `missing_rule`.

Return valid JSON only. Each item in `findings` must include all required fields:

```json
{
  "findings": [
    {
      "rule_id": "R001",
      "issue": "Concise issue description",
      "severity": "high|medium|low",
      "evidence": "Exact API spec excerpt or field name"
    }
  ]
}
```

Do not omit `severity` or `evidence`. Do not return markdown fences, prose, or partial objects.
