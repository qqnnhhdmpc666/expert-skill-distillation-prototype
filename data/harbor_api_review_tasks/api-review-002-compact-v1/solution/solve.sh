#!/bin/bash
set -euo pipefail

cat > /app/review.json <<'JSON'
{
  "findings": [
    {
      "rule_id": "R001",
      "issue": "The API only says login is required and does not document refund roles, scopes, or authorization failure behavior.",
      "severity": "high",
      "evidence": "Notes: The endpoint requires login."
    },
    {
      "rule_id": "R002",
      "issue": "Request fields lack required/optional markers and amount/range/enum constraints.",
      "severity": "high",
      "evidence": "Request body lists amount, reason, and notify_customer without constraints."
    },
    {
      "rule_id": "R003",
      "issue": "Error code coverage only includes success and system error.",
      "severity": "high",
      "evidence": "Error Codes table lists 0 and 500 only."
    },
    {
      "rule_id": "R004",
      "issue": "Response exposes internal_trace and full customer phone.",
      "severity": "high",
      "evidence": "Response data includes internal_trace and customer_phone."
    }
  ]
}
JSON
