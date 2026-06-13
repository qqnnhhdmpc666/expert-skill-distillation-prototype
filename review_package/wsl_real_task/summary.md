# WSL2 Harbor Real Upload Security Task

## Result

PASS, reward `1.0`.

This run used WSL2 `Ubuntu-24.04-Codex`, Docker, and Harbor to execute a real upload-security review task inside a container. The target contained vulnerable upload code and config. The agent produced `/app/security_report.json`, and the verifier checked concrete capability coverage plus evidence and fix fields.

## Verified Capabilities

| Capability | Status |
|---|---|
| `UPLOAD_TYPE_MAGIC` | seen |
| `UPLOAD_PATH_ISOLATION` | seen |
| `UPLOAD_AUDIT_RETENTION` | seen |

Verifier result:

```json
{
  "report_exists": true,
  "missing": [],
  "schema_errors": []
}
```

## Evidence Files

- `result.json`
- `real-upload-security-review__dCxSUn5/result.json`
- `real-upload-security-review__dCxSUn5/artifacts/security_report.json`
- `real-upload-security-review__dCxSUn5/artifacts/result.json`
- `real-upload-security-review__dCxSUn5/verifier/test-stdout.txt`

## Boundary

This proves the real WSL2/Docker/Harbor sandbox and verifier path on a security task. The agent is still Harbor `oracle`, so this is not yet evidence that a real CLI coding agent independently solved arbitrary vulnerabilities.
