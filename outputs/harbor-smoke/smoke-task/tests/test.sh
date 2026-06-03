#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

if [ -f /app/answer.txt ] && [ "$(cat /app/answer.txt)" = "spark-ok" ]; then
  echo 1 > /logs/verifier/reward.txt
  echo "PASS: answer.txt contains spark-ok"
else
  echo 0 > /logs/verifier/reward.txt
  echo "FAIL: /app/answer.txt missing or incorrect"
  exit 1
fi
