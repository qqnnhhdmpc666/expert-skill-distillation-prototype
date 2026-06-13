You are a non-oracle security-review agent running in a Harbor container.

Read /app/target and /app/skill. Return only JSON for the deterministic verifier.

Rules:
- Use only these capability_id values from /app/skill: UPLOAD_AUDIT_RETENTION, UPLOAD_PATH_ISOLATION, UPLOAD_TYPE_MAGIC
- Each finding must include capability_id, issue, evidence_span, recommended_fix.
- Evidence must be grounded in /app/target files.
- Do not include markdown fences.

Expected JSON:
{
  "findings": [
    {
      "capability_id": "UPLOAD_TYPE_MAGIC",
      "issue": "...",
      "evidence_span": "...",
      "recommended_fix": "..."
    }
  ]
}

# Skill Package

## SKILL.md

```text
# Harbor Upload Security Skill

Task family: `upload_security`

## Inspection Procedure

1. Read `/app/target/app.py` and `/app/target/config.yaml`.
2. Emit only findings grounded in concrete target spans.
3. Follow the verifier contract: `capability_id`, `evidence_span`, `recommended_fix`.

## Capabilities

### UPLOAD_TYPE_MAGIC

- Check whether upload validation relies only on filename extensions.
- Look for missing MIME type, magic-byte, size, and content validation.

### UPLOAD_PATH_ISOLATION

- Check whether user-controlled filenames are joined into public upload paths.
- Look for public/executable upload roots or returned internal paths.

### UPLOAD_AUDIT_RETENTION

- Check whether upload/download/delete events have audit logs and retention policy.
- Look for empty `audit_log_retention_days` or handlers without audit events.

## Boundary

This Skill is for a controlled Harbor upload-security task. It is not a general vulnerability scanner.

```

## manifest.json

```text
{
  "version": "v2",
  "capabilities": [
    "UPLOAD_TYPE_MAGIC",
    "UPLOAD_PATH_ISOLATION",
    "UPLOAD_AUDIT_RETENTION"
  ]
}

```

# Target Asset

## app.py

```text
from pathlib import Path

UPLOAD_ROOT = Path("/public/uploads")


def save(path: str, data: bytes) -> None:
    Path(path).write_bytes(data)


def upload(filename: str, content_type: str, file_bytes: bytes) -> dict:
    if filename.endswith((".png", ".jpg")):
        save(str(UPLOAD_ROOT / filename), file_bytes)
    return {"ok": True, "debug_path": str(UPLOAD_ROOT / filename)}


def download(filename: str):
    return Path(UPLOAD_ROOT / filename).read_bytes()

```

## config.yaml

```text
debug: true
audit_log_retention_days:
upload_storage: /public/uploads

```
