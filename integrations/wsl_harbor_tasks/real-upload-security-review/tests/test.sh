#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier

python3 - <<'PY'
import json
from pathlib import Path

report_path = Path("/app/security_report.json")
expected = {"UPLOAD_TYPE_MAGIC", "UPLOAD_PATH_ISOLATION", "UPLOAD_AUDIT_RETENTION"}

result = {
    "report_exists": report_path.exists(),
    "expected": sorted(expected),
    "seen": [],
    "missing": sorted(expected),
    "schema_errors": [],
}

if not report_path.exists():
    Path("/logs/verifier/reward.txt").write_text("0\n")
    Path("/logs/verifier/result.json").write_text(json.dumps(result, indent=2))
    raise SystemExit("FAIL: /app/security_report.json was not created")

try:
    payload = json.loads(report_path.read_text())
except json.JSONDecodeError as exc:
    result["schema_errors"].append(f"invalid json: {exc}")
    Path("/logs/verifier/reward.txt").write_text("0\n")
    Path("/logs/verifier/result.json").write_text(json.dumps(result, indent=2))
    raise SystemExit("FAIL: report is not valid JSON")

findings = payload.get("findings")
if not isinstance(findings, list):
    result["schema_errors"].append("findings must be a list")
    findings = []

seen = set()
for index, item in enumerate(findings):
    if not isinstance(item, dict):
        result["schema_errors"].append(f"finding {index} is not an object")
        continue
    capability_id = str(item.get("capability_id", ""))
    if capability_id:
        seen.add(capability_id)
    if capability_id in expected:
        if not str(item.get("evidence_span", "")).strip():
            result["schema_errors"].append(f"{capability_id} missing evidence_span")
        if not str(item.get("recommended_fix", "")).strip():
            result["schema_errors"].append(f"{capability_id} missing recommended_fix")

result["seen"] = sorted(seen)
result["missing"] = sorted(expected - seen)
passed = not result["missing"] and not result["schema_errors"]
Path("/logs/verifier/reward.txt").write_text("1\n" if passed else "0\n")
Path("/logs/verifier/result.json").write_text(json.dumps(result, indent=2) + "\n")
if not passed:
    raise SystemExit("FAIL: " + json.dumps(result))
print("PASS: report covers expected upload-security findings with evidence and fixes")
PY
