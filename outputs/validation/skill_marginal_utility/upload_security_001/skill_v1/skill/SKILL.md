# Defensive Secure Review Skill upload_security_001 v1

Safety boundary: defensive review only. Do not generate exploits, attack chains, or real-target automation.

Task family: `upload_security`

## Capabilities

### UPLOAD_PATH_ISOLATION: Upload path isolation
- Evidence: UPLOAD_ROOT / filename writes a user name into /public/uploads
- Fix: Generate server-side names and store outside public executable roots.
