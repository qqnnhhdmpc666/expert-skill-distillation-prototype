#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"GHSA-34jh-p97f-mpxf__advisory_missing_1","verdict":"unresolved","reason_codes":["ADVISORY_NOT_FOUND"]}
EOF
