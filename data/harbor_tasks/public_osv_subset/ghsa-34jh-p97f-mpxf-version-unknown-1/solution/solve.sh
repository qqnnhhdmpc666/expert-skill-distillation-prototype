#!/bin/bash
set -euo pipefail
cat > /app/prediction.json <<'EOF'
{"case_id":"GHSA-34jh-p97f-mpxf__version_unknown_1","verdict":"unresolved","reason_codes":["VERSION_UNKNOWN"]}
EOF
