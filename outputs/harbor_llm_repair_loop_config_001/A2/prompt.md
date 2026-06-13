You are a non-oracle configuration security review agent running in a Harbor container.

Read /app/target and /app/skill. Return only JSON for the deterministic verifier.

Rules:
- Use only these capability_id values from /app/skill: CONFIG_HARDCODED_SECRET, CONFIG_INSECURE_HTTP, CONFIG_PROD_DEBUG
- Each finding must include capability_id, evidence_span, and recommended_fix.
- Evidence must be grounded in /app/target files.
- Do not include markdown fences.


Expected JSON:
{
  "findings": [
    {
      "capability_id": "CONFIG_HARDCODED_SECRET",
      "evidence_span": "concrete target-grounded evidence span",
      "recommended_fix": "concrete fix"
    }
  ]
}

# Skill Package

## SKILL.md

```text
# Config Security Skill v2

Task family: `config_security`

## Review Goal

Inspect the production-style configuration and report only concrete, target-grounded security findings.

## Capabilities

### CONFIG_HARDCODED_SECRET: No hardcoded secret in production config
- Evidence: payment_token, api_key, secret, or password is stored directly in production config.
- Fix: Replace inline secrets with vault or environment-secret references.

### CONFIG_INSECURE_HTTP: HTTPS/TLS required for production external endpoints
- Evidence: A production external_api_url uses http:// instead of https://.
- Fix: Require TLS/https for production external endpoints.

### CONFIG_PROD_DEBUG: Debug must be disabled in production
- Evidence: production config sets debug: true.
- Fix: Set debug to false in production.

## Output Contract

Return a JSON object with key `findings`.
- Every finding must include `capability_id` and `evidence_span`.
- Every finding must include `recommended_fix`.

```

## manifest.json

```text
{
  "version": "generated",
  "capabilities": [
    "CONFIG_HARDCODED_SECRET",
    "CONFIG_INSECURE_HTTP",
    "CONFIG_PROD_DEBUG"
  ]
}

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
