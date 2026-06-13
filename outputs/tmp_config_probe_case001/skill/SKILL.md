# Production Config Security Skill

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
