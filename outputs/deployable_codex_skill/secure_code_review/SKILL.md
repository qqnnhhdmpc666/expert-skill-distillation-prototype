# Secure Code Review Skill Package

This package contains installable runtime versions for the controlled secure-code-review prototype.

## Boundary

- Prototype runtime package only.
- Defensive detection, explanation, fix recommendation, and patch validation only.
- No exploit generation, attack-chain execution, or unauthorized target testing.

## Runtime Versions

- `v1`: upload-focused package with an out-of-scope guard for non-upload tasks.
- `v2`: task-conditioned security package with upload, config, API/code-review, auth/access-control, and out-of-scope guard groups.

Use `skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version <v>` to install one runtime version.
