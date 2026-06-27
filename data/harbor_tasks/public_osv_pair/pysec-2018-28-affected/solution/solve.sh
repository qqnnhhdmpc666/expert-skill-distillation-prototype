#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"PYSEC-2018-28__affected","verdict":"advisory_applicable","reason_codes":["VERSION_IN_RANGE"]}
EOF
