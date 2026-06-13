You are a non-oracle security-review agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: CONFIG_HARDCODED_SECRET, CONFIG_INSECURE_HTTP, CONFIG_PROD_DEBUG.
- Each finding must include capability_id, issue, evidence_span, and recommended_fix.
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- Return JSON only. No markdown fences.

Expected JSON shape:
{
  "findings": [
    {
      "capability_id": "CONFIG_HARDCODED_SECRET",
      "issue": "short issue title",
      "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible",
      "recommended_fix": "specific fix grounded in the target"
    }
  ]
}

# Skill Package

## manifest.json

```text
﻿{"version":"v2","capabilities":["CONFIG_HARDCODED_SECRET","CONFIG_INSECURE_HTTP","CONFIG_PROD_DEBUG"]}

```

## SKILL.md

```text
﻿# Production Config Security Skill

## Capabilities

### CONFIG_HARDCODED_SECRET
- Evidence: payment_token, api_key, secret, or password is stored directly in the config.
- Fix: Replace inline secrets with vault or environment-secret references.

### CONFIG_INSECURE_HTTP
- Evidence: production external_api_url uses http:// instead of https://.
- Fix: Require TLS/https for production external endpoints.

### CONFIG_PROD_DEBUG
- Evidence: production config sets debug: true.
- Fix: Disable debug in production.

```

# Target Asset

## config.md

```text
service: billing-worker
environment: production
debug: true
external_api_url: http://partner.example.com/v1
payment_token: "sk_live_demo_value"
service_account:
  name: billing-admin
  roles:
    - admin
audit:
  enabled: false
  retention_days:

```
