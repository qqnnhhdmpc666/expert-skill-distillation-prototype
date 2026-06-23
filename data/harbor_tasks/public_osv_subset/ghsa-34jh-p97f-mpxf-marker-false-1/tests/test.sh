#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
expected='{"case_id":"GHSA-34jh-p97f-mpxf__marker_false_1","verdict":"advisory_not_applicable","reason_codes":["MARKER_FALSE"]}'
actual="$(tr -d '\r\n' < /app/prediction.json)"
if [ "$actual" = "$expected" ]; then
  echo 1 > /logs/verifier/reward.txt
  printf '%s\n' '{"schema_version":"public_osv_harbor_verifier.v1","passed":true,"source_record_digest":"sha256:d6b539e34df7634dafff91de0990e178df1d0592f2b568eac0a5e602443856e8","case_kind":"marker_false_1_control"}' > /logs/verifier/result.json
else
  echo 0 > /logs/verifier/reward.txt
  printf '%s\n' '{"schema_version":"public_osv_harbor_verifier.v1","passed":false,"source_record_digest":"sha256:d6b539e34df7634dafff91de0990e178df1d0592f2b568eac0a5e602443856e8","case_kind":"marker_false_1_control"}' > /logs/verifier/result.json
  exit 1
fi
