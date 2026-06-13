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
