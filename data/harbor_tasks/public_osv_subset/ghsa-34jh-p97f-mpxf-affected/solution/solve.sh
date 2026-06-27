#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"GHSA-34jh-p97f-mpxf__affected","verdict":"advisory_applicable","reason_codes":["VERSION_IN_RANGE"]}
EOF
