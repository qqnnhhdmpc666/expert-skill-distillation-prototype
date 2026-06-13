# Multi-Capability Generalization Status

Date: 2026-06-12

Scope: P0-G internal multi-security installed runtime and multi-skill registry readiness.

Boundary:

- No UI
- No database
- No service API
- No data-quality capability promotion into `secure_code_review`
- External SWE-bench evidence is reported separately

## Summary

The installed `secure_code_review` package now covers four security task families through task-conditioned capability groups:

- `upload_security`
- `config_security`
- `api_or_code_review`
- `auth_access_control`

The same installed runtime path passes all four security cases, while `data_quality_review_001` remains out of scope with no upload/config/API/auth false positives. A separate `software_patch_review` skill package was also built and installed to prove multi-skill runtime readiness.

## Fresh Commands

```powershell
skill-deploy build-codex-skill
skill-deploy build-software-patch-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy install --skill outputs/deployable_codex_skill/software_patch_review --version v1
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case api_review_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case auth_access_control_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case data_quality_review_001 --backend offline_deterministic
skill-deploy run-skill --installed software_patch_review --case software_patch_review_001 --backend offline_deterministic
skill-deploy compare-variants --cases upload,config,api_review,auth --backend offline_deterministic --source installed
```

## Pass

Security installed runtime:

| Case | Task family | Activated group | Verifier | Evidence |
|---|---|---|---|---|
| `upload_security_001` | `upload_security` | `upload_security` | `pass` | `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260612T042234560955Z_v2/evidence_bundle/summary.json` |
| `config_security_001` | `config_security` | `config_security` | `pass` | `outputs/runtime_runs/installed_skills/secure_code_review/config_security_001/20260612T042234664852Z_v2/evidence_bundle/summary.json` |
| `api_review_001` | `api_or_code_review` | `api_or_code_review` | `pass` | `outputs/runtime_runs/installed_skills/secure_code_review/api_review_001/20260612T042234665201Z_v2/evidence_bundle/summary.json` |
| `auth_access_control_001` | `auth_access_control` | `auth_access_control` | `pass` | `outputs/runtime_runs/installed_skills/secure_code_review/auth_access_control_001/20260612T042234686440Z_v2/evidence_bundle/summary.json` |

Out-of-scope guard:

| Case | Task family | Activated group | Verifier | False positives |
|---|---|---|---|---:|
| `data_quality_review_001` | `data_quality_review` | `out_of_scope_guard` | `fail` by missing data-quality capabilities | `0` |

Multi-skill runtime:

| Skill | Case | Activated group | Verifier | Evidence |
|---|---|---|---|---|
| `software_patch_review` | `software_patch_review_001` | `software_patch_review` | `pass` | `outputs/runtime_runs/installed_skills/software_patch_review/software_patch_review_001/20260612T042234701342Z_v1/evidence_bundle/summary.json` |

## Installed Compare

Fresh command:

```powershell
skill-deploy compare-variants --cases upload,config,api_review,auth --backend offline_deterministic --source installed
```

Fresh summary:

- `outputs/validation/skill_marginal_utility/installed_package_marginal_utility.json`

Observed gains:

- `upload_security_001`: `installed_v2_over_installed_v1_gain = 0.3333`
- `config_security_001`: `installed_v2_over_installed_v1_gain = 0.4`
- `api_review_001`: `installed_v2_over_installed_v1_gain = 0.4`
- `auth_access_control_001`: `installed_v2_over_installed_v1_gain = 0.4`

Required provenance is present in per-variant `run_metadata.json`:

- `task_family`
- `activated_capability_group`
- `skill_hash`
- `manifest_hash`
- `active_pointer_snapshot`

## Multi-Skill Registry

The runtime now writes per-skill active pointers:

- `outputs/installed_skills/active_skill_pointers/secure_code_review.json`
- `outputs/installed_skills/active_skill_pointers/software_patch_review.json`

The legacy pointer remains:

- `outputs/installed_skills/active_skill_pointer.json`

Runtime resolution now uses the per-skill pointer when a skill id is provided, so installing `software_patch_review` does not prevent `secure_code_review` from running.

## Remaining Gap

- The internal security evidence is still controlled/offline deterministic, not a broad real-world vulnerability benchmark.
- `data_quality_review_001` still reports verifier `missing_capability`, but runtime evidence correctly records `out_of_scope_guard` and avoids false positives.
- The `software_patch_review` package is only an internal patch-review smoke package until SWE-bench official evaluation completes.
