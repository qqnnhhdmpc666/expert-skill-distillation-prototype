#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"GHSA-34jh-p97f-mpxf__fixed_boundary","verdict":"advisory_not_applicable","reason_codes":["VERSION_OUT_OF_RANGE"]}
EOF
