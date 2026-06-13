You are a non-oracle file upload security review agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: UPLOAD_PATH_ISOLATION, UPLOAD_AUDIT_RETENTION, UPLOAD_TYPE_MAGIC.
- Each finding must include capability_id, issue, evidence_span, and recommended_fix.
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- Return JSON only. No markdown fences.


Expected JSON shape:
{
  "findings": [
    {
      "capability_id": "UPLOAD_PATH_ISOLATION",
      "issue": "short issue title",
      "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible",
      "recommended_fix": "specific fix grounded in the target"
    }
  ]
}

# Skill Package

## manifest.json

```text
{
  "skill_id": "upload_security_001",
  "version": "v2",
  "task_family": "upload_security",
  "capabilities": [
    "UPLOAD_PATH_ISOLATION",
    "UPLOAD_AUDIT_RETENTION",
    "UPLOAD_TYPE_MAGIC"
  ],
  "output_contract": [
    "capability_id",
    "evidence_span",
    "recommended_fix"
  ],
  "trace_contract": [
    "event",
    "capability_id",
    "evidence_span"
  ],
  "metadata": {
    "repair_action": "patch_capability"
  }
}

```

## SKILL.md

```text
# File upload security review Skill v2

Task family: `upload_security`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### UPLOAD_PATH_ISOLATION: Upload path isolation
- Evidence: UPLOAD_ROOT / filename writes a user name into /public/uploads
- Fix: Generate server-side names and store outside public executable roots.

### UPLOAD_AUDIT_RETENTION: Upload audit retention
- Evidence: audit_log_retention_days is empty and handlers write no audit event
- Fix: Record actor/object/action/result/timestamp with retention.

### UPLOAD_TYPE_MAGIC: Upload type and content validation
- Evidence: filename.endswith without MIME or magic-byte validation
- Fix: Validate MIME, signature, size, and extension together.

## Revision Policy

Applied repair action: `patch_capability`.

```

# Target Asset

## target.md

```text
app.py: upload() checks filename.endswith, writes UPLOAD_ROOT / filename, returns debug_path. config.yaml: audit_log_retention_days is empty.
```
