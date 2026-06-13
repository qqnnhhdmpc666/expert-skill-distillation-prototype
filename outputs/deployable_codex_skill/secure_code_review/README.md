# Deployable Codex Skill Package

This package now contains real installable runtime versions used by `skill-deploy install` and `skill-deploy run-skill --installed ...`.

Smoke commands:

```powershell
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v1
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case api_review_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case auth_access_control_001 --backend offline_deterministic
skill-deploy rollback --installed secure_code_review --to-version v1
```
