# Open-World Distillation Validation Status

Generated at: `2026-06-13T08:04:54.092103+00:00`

This run evaluates a bounded public-material automatic distillation path. It does not claim universal open-world semantic induction.

## Fresh Commands

```powershell
skill-deploy open-world-distill-validation --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash
```

## Distillation

- Installed skill id: `secure_code_review_open_world_distilled`
- Distillation method: `keyword_projection_from_open_materials`
- Supported families: `upload_security, auth_access_control, config_security`
- Selected capabilities: `AUTH_ERROR_ENVELOPE, AUTH_OBJECT_OWNERSHIP, AUTH_SCOPE_MATRIX, CONFIG_AUDIT_EXPORT, CONFIG_ENV_GUARD, UPLOAD_AUDIT_RETENTION, UPLOAD_PATH_ISOLATION, UPLOAD_TYPE_MAGIC`

## Summary

- Distilled completed rows: `10` / `10`
- Distilled effective pass count: `8`
- Baseline effective pass count: `5`
- Distilled false positives: `0`
- Clean negative controls passed: `3`
- Unsupported limitations preserved: `3`

## Case Comparison

| Case | Family | Distilled | Baseline | Distilled group | Baseline group | Distilled FP | Note |
|---|---|---|---|---|---|---:|---|
| independent_auth_clean_001 | auth_access_control | completed:pass | completed:fail | auth_access_control | auth_access_control | 0 | ok |
| independent_auth_invoice_scope_001 | auth_access_control | completed:pass | completed:fail | auth_access_control | auth_access_control | 0 | ok |
| independent_config_clean_001 | config_security | completed:pass | completed:pass | config_security | config_security | 0 | ok |
| independent_config_prod_audit_001 | config_security | completed:fail | completed:fail | config_security | config_security | 0 | missing_capability |
| independent_dependency_unsupported_001 | dependency_version_risk | completed:pass | completed:pass | out_of_scope_guard | out_of_scope_guard | 0 | ok |
| independent_upload_clean_001 | upload_security | completed:pass | completed:fail | upload_security | upload_security | 0 | ok |
| independent_upload_mime_storage_001 | upload_security | completed:pass | completed:pass | upload_security | upload_security | 0 | ok |
| public_nodegoat_dev_config_001 | config_security | completed:fail | completed:fail | config_security | config_security | 0 | missing_capability |
| public_nodegoat_eval_unsupported_001 | server_side_js_injection_review | completed:pass | completed:pass | out_of_scope_guard | out_of_scope_guard | 0 | ok |
| public_nodegoat_regex_unsupported_001 | regex_dos_review | completed:pass | completed:pass | out_of_scope_guard | out_of_scope_guard | 0 | ok |

## Boundary

- Distillation source is public or independent material, not the controlled `expert_material.md` files.
- Validation labels are still local deterministic verifier labels, not official external benchmark labels.
- This is evidence for bounded open-material automatic distillation into the current capability registry.
- It is not proof of arbitrary open-world vulnerability discovery or unrestricted Skill induction.
