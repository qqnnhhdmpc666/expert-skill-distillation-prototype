#!/bin/bash
set -euo pipefail

cat > /app/compact_skill.md <<'MD'
# API Review Compact Skill v2

## Checklist

- [R001] Check whether authentication method, roles/scopes, and auth failure behavior are explicit.
- [R002] Check required fields, optional defaults, type, range, length, and enum constraints.
- [R003] Check error codes for validation, auth, permission, not found, duplicate, and server errors.
- [R004] Check for token, secret, stack trace, full phone or identity exposure in responses.
- [R005] Check consistent envelope fields: code, message, request_id, and data.
- [R006] Check whether mutation endpoints document idempotency or duplicate submission handling.
MD

cat > /app/case_openapi.md <<'MD'
# API Review Case 002

Endpoint: `POST /api/v1/orders/{order_id}/refund`

## Auth

The endpoint requires login.

## Request Body

```json
{
  "amount": 99.9,
  "reason": "customer_request",
  "notify_customer": true
}
```

## Response

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "refund_id": "rf_123",
    "status": "processing",
    "internal_trace": "refund-worker-7:stack-abc",
    "customer_phone": "+1-202-555-0101"
  }
}
```

## Error Codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 500 | System error |

## Notes

No idempotency key, duplicate refund handling, or request_id field is documented.
MD

cat > /app/api_review_mock_agent.py <<'PY'
from __future__ import annotations

import json
import re
from pathlib import Path


TEMPLATES = {
    "R001": ("high", "Authentication scope is underspecified.", "The endpoint only says login is required."),
    "R002": ("high", "Request validation is underspecified.", "Fields do not document required status or constraints."),
    "R003": ("high", "Error code coverage is incomplete.", "Only success and system error are listed."),
    "R004": ("high", "Response exposes sensitive or internal information.", "Response contains internal_trace and customer_phone."),
    "R005": ("medium", "Response envelope lacks request_id.", "Response includes code, message, and data but no request_id."),
    "R006": ("medium", "Mutation endpoint lacks idempotency guidance.", "POST refund endpoint does not document idempotency or duplicate handling."),
}


def main() -> None:
    compact_skill = Path("/app/compact_skill.md").read_text(encoding="utf-8")
    rule_ids = sorted(set(re.findall(r"\[(R00[1-6])\]", compact_skill)))
    findings = []
    for rule_id in rule_ids:
        severity, issue, evidence = TEMPLATES[rule_id]
        findings.append({"rule_id": rule_id, "issue": issue, "severity": severity, "evidence": evidence})
    Path("/app/review.json").write_text(json.dumps({"findings": findings}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
PY

python3 /app/api_review_mock_agent.py
