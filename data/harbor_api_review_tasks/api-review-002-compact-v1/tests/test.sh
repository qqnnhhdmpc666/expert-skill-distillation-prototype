#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

if [ ! -f /app/review.json ]; then
  echo 0 > /logs/verifier/reward.txt
  echo "FAIL: /app/review.json was not created"
  exit 1
fi

required=(R001 R002 R003 R004 R005 R006)
missing=()

for rule_id in "${required[@]}"; do
  if ! grep -q "\"rule_id\"[[:space:]]*:[[:space:]]*\"${rule_id}\"" /app/review.json; then
    missing+=("${rule_id}")
  fi
done

if [ "${#missing[@]}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
  echo "PASS: review.json covers required rule ids R001-R006"
else
  echo 0 > /logs/verifier/reward.txt
  echo "FAIL: missing expected findings for ${missing[*]}"
  exit 1
fi
