You are a non-oracle security-review agent running in a Harbor container.

Read /app/target and /app/skill. Return only JSON for the deterministic verifier.

Rules:
- Use only these capability_id values from /app/skill: UPLOAD_PATH_ISOLATION
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
# File upload security review Skill v1

Task family: `upload_security`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### UPLOAD_PATH_ISOLATION: Upload path isolation
- Evidence: UPLOAD_ROOT / filename writes a user name into /public/uploads
- Fix: Generate server-side names and store outside public executable roots.

```

## manifest.json

```text
{
  "version": "generated",
  "capabilities": [
    "UPLOAD_PATH_ISOLATION"
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
