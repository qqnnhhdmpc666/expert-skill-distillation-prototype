You are a non-oracle security-review agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: CONFIG_AUDIT_EXPORT, CONFIG_ENV_GUARD.
- Each finding must include capability_id, issue, evidence_span, and recommended_fix.
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- Return JSON only. No markdown fences.

Expected JSON shape:
{
  "findings": [
    {
      "capability_id": "CONFIG_AUDIT_EXPORT",
      "issue": "short issue title",
      "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible",
      "recommended_fix": "specific fix grounded in the target"
    }
  ]
}

# Skill Package

## manifest.json

```text
﻿{"version":"v1","capabilities":["CONFIG_AUDIT_EXPORT","CONFIG_ENV_GUARD"]}

```

## SKILL.md

```text
﻿# Config Security Skill

## Capabilities

### CONFIG_AUDIT_EXPORT
- Evidence: prod.audit enabled but retention_days/export_sink missing
- Fix: Require retention and export sink for production audit logs.

### CONFIG_ENV_GUARD
- Evidence: dev api_token/debug should not be production findings
- Fix: Bind findings to prod/dev/test path before flagging.

```

# Target Asset

## target.md

```text
config.yaml: prod.debug=false; prod.audit.enabled=true; prod.audit.retention_days=90; prod.audit.export_sink=siem; prod.secret_ref=vault://prod/api-token.
```
