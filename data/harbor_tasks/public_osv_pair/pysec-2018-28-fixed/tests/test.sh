#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
expected='{"case_id":"PYSEC-2018-28__fixed_boundary","verdict":"advisory_not_applicable","reason_codes":["VERSION_OUT_OF_RANGE"]}'
actual="$(tr -d '\r\n' < /app/prediction.json)"
if [ "$actual" = "$expected" ]; then
  echo 1 > /logs/verifier/reward.txt
  printf '%s\n' '{"schema_version":"public_osv_harbor_verifier.v1","passed":true,"source_record_digest":"sha256:9e797ddf6daa453869b8d270676615145579f3bf5115e67dc5e69052974e034b"}' > /logs/verifier/result.json
else
  echo 0 > /logs/verifier/reward.txt
  printf '%s\n' '{"schema_version":"public_osv_harbor_verifier.v1","passed":false,"source_record_digest":"sha256:9e797ddf6daa453869b8d270676615145579f3bf5115e67dc5e69052974e034b"}' > /logs/verifier/result.json
  exit 1
fi
