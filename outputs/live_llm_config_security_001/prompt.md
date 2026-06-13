You are a non-oracle configuration security review agent.

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
{
  "skill_id": "config_security_001",
  "version": "v2",
  "task_family": "config_security",
  "capabilities": [
    "CONFIG_AUDIT_EXPORT",
    "CONFIG_ENV_GUARD"
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
  "metadata": {}
}

```

## SKILL.md

```text
# Production configuration security check Skill v2

Task family: `config_security`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### CONFIG_AUDIT_EXPORT: Production audit retention/export
- Evidence: prod.audit enabled but retention_days/export_sink missing
- Fix: Require retention and export sink for production audit logs.

### CONFIG_ENV_GUARD: Environment-aware config guard
- Evidence: dev api_token/debug should not be production findings
- Fix: Bind findings to prod/dev/test path before flagging.

```

# Target Asset

## target.md

```text
prod.audit.enabled=true but retention_days/export_sink empty. dev.api_token and dev.debug are present but dev-only.
```
