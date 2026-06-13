# Multi-Skill Isolation Status

Generated at: `2026-06-12T11:07:41.959245+00:00`

## Fresh Commands

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy run-skill --installed software_patch_review --case software_patch_review_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic
```

## Isolation Checks

| Skill | Case | Decision | Pointer ok | Forbidden package not read | Hash ok | Manifest ok | Evidence |
|---|---|---|---:|---:|---:|---:|---|
| secure_code_review | upload_security_001 | pass | True | True | True | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\runtime_runs\installed_skills\secure_code_review\upload_security_001\20260612T110716307349Z_v2 |
| software_patch_review | software_patch_review_001 | pass | True | True | True | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\runtime_runs\installed_skills\software_patch_review\software_patch_review_001\20260612T110716289753Z_v1 |
| secure_code_review | config_security_001 | pass | True | True | True | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\runtime_runs\installed_skills\secure_code_review\config_security_001\20260612T110716287515Z_v2 |

## Decision

- Overall status: `pass`
