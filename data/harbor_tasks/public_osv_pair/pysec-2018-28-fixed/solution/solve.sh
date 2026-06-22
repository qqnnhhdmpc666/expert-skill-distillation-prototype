#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"PYSEC-2018-28__fixed_boundary","verdict":"advisory_not_applicable","reason_codes":["VERSION_OUT_OF_RANGE"]}
EOF
