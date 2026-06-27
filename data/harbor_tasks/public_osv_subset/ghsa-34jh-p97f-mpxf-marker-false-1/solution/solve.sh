#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"GHSA-34jh-p97f-mpxf__marker_false_1","verdict":"advisory_not_applicable","reason_codes":["MARKER_FALSE"]}
EOF
