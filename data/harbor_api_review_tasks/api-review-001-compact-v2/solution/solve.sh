#!/bin/bash
set -euo pipefail

cat > /app/review.json <<'JSON'
{
  "findings": [
    {
      "rule_id": "R001",
      "issue": "The API only says login is required and does not document roles, scopes, or authorization failure behavior.",
      "severity": "high",
      "evidence": "Notes: The endpoint requires login."
    },
    {
      "rule_id": "R002",
      "issue": "Request fields lack required/optional markers and validation constraints.",
      "severity": "high",
      "evidence": "Request body lists display_name, phone, and avatar_url without constraints."
    },
    {
      "rule_id": "R003",
      "issue": "Error code coverage only includes success and server error.",
      "severity": "high",
      "evidence": "Error Codes table lists 0 and 500 only."
    },
    {
      "rule_id": "R004",
      "issue": "Response exposes access_token and full phone number.",
      "severity": "high",
      "evidence": "Response data includes access_token and phone."
    },
    {
      "rule_id": "R005",
      "issue": "Response envelope lacks request_id.",
      "severity": "medium",
      "evidence": "Response includes code, message, and data but no request_id."
    },
    {
      "rule_id": "R006",
      "issue": "Mutation endpoint does not explain idempotency or duplicate submission behavior.",
      "severity": "medium",
      "evidence": "Endpoint is POST /api/v1/users/{user_id}/profile."
    }
  ]
}
JSON
