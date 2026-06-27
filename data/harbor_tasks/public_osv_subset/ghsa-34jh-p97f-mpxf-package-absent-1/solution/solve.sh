#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"GHSA-34jh-p97f-mpxf__package_absent_1","verdict":"advisory_not_applicable","reason_codes":["PACKAGE_NOT_PRESENT"]}
EOF
