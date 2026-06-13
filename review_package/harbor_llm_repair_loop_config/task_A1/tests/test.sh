#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier

python3 - <<'PY'
import json
from pathlib import Path

report_path = Path('/app/security_report.json')
expected = ["CONFIG_HARDCODED_SECRET", "CONFIG_INSECURE_HTTP", "CONFIG_PROD_DEBUG"]
expected_set = set(expected)
result = {
    'report_exists': report_path.exists(),
    'expected': expected,
    'seen': [],
    'missing': expected,
    'false_positive': [],
    'schema_errors': [],
}

if not report_path.exists():
    Path('/logs/verifier/reward.txt').write_text('0\n')
    Path('/logs/verifier/result.json').write_text(json.dumps(result, indent=2) + '\n')
    raise SystemExit('FAIL: /app/security_report.json was not created')

try:
    payload = json.loads(report_path.read_text())
except json.JSONDecodeError as exc:
    result['schema_errors'].append(f'invalid json: {exc}')
    Path('/logs/verifier/reward.txt').write_text('0\n')
    Path('/logs/verifier/result.json').write_text(json.dumps(result, indent=2) + '\n')
    raise SystemExit('FAIL: report is not valid JSON')

findings = payload.get('findings')
if not isinstance(findings, list):
    result['schema_errors'].append('findings must be a list')
    findings = []

seen = set()
for index, item in enumerate(findings):
    if not isinstance(item, dict):
        result['schema_errors'].append(f'finding {index} is not an object')
        continue
    capability_id = str(item.get('capability_id', '')).strip()
    if capability_id:
        seen.add(capability_id)
    if capability_id in expected_set:
        if not str(item.get('evidence_span', '')).strip():
            result['schema_errors'].append(f'{capability_id} missing evidence_span')
        if not str(item.get('recommended_fix', '')).strip():
            result['schema_errors'].append(f'{capability_id} missing recommended_fix')

result['seen'] = sorted(seen)
result['missing'] = sorted(expected_set - seen)
result['false_positive'] = sorted(seen - expected_set)
passed = not result['missing'] and not result['false_positive'] and not result['schema_errors']
Path('/logs/verifier/reward.txt').write_text('1\n' if passed else '0\n')
Path('/logs/verifier/result.json').write_text(json.dumps(result, indent=2) + '\n')
if not passed:
    raise SystemExit('FAIL: ' + json.dumps(result))
print('PASS: config report covers expected findings with evidence and fixes')
PY
