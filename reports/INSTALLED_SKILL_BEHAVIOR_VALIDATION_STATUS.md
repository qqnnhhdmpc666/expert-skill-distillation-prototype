# Installed Skill Behavior Validation Status

Date: 2026-06-11

Scope: P0-E Installed Skill Behavior Validation Sprint only.

Boundary:

- No Harbor live work
- No external benchmark work
- No UI
- No database
- No service API
- No verifier relaxation

## Summary

This sprint validated behavior on the real installed runtime path rather than only the runtime connection path.

The main result is that `secure_code_review` now passes the strict verifier on `upload_security_001` when executed through the installed package path. The installed runtime path was also exercised on a second controlled case, and `compare-variants` now supports real installed package variants with package hashes and active pointer snapshots.

## Fresh Commands

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case data_quality_review_001 --backend offline_deterministic
skill-deploy compare-variants --cases upload --backend offline_deterministic --source installed
```

Verification commands:

```powershell
python -m py_compile src/skill_deployment/runner.py src/skill_deployment/evidence.py scripts/run_skill_marginal_utility.py src/skill_deployment/cli.py
python -m pytest -q
skill-deploy validate-review-package
```

## Completed

### 1. Installed upload run now passes the strict verifier

Fresh command:

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

Fresh runtime evidence:

- `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T151856771100Z_v2/evidence_bundle/summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T151856771100Z_v2/verifier_report.json`

Verified fields in the evidence bundle summary:

- `runtime_source = installed_skill_package`
- `skill_version = v2`
- `skill_hash = 6271a8d0e70e9a8dac6723a822caf24048cf719430181d1c0f1d56edf75574e6`
- `manifest_hash = dedfd677c50d662dae14e4f895a08a862dd8e267cee10c4a829058a52302475b`
- `skill_package_path = outputs/installed_skills/packages/secure_code_review/versions/v2`
- `verifier_result = pass`

Behavior note:

- No verifier rule was loosened.
- No fallback to `run_generalization_suite.py` was used.
- The fix came from target-bound evidence grounding in the installed runtime path.

### 2. Installed runtime path works on a second controlled case

Selected second case:

- `data_quality_review_001`

Fresh command:

```powershell
skill-deploy run-skill --installed secure_code_review --case data_quality_review_001 --backend offline_deterministic
```

Fresh artifacts:

- `outputs/runtime_runs/installed_skills/secure_code_review/data_quality_review_001/20260611T151913495878Z_v2/evidence_bundle/summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review/data_quality_review_001/20260611T151913495878Z_v2/verifier_report.json`

Verified runtime-traceable fields:

- `runtime_source = installed_skill_package`
- `skill_hash`
- `manifest_hash`
- `skill_package_path`

Observed verifier feedback:

- `verifier_result = fail`
- `feedback_type = missing_capability`
- Missing capabilities:
  - `DATA_LABEL_ENUM_ALIGNMENT`
  - `DATA_REQUIRED_FIELD_COVERAGE`
  - `DATA_TEMPORAL_SPLIT_GUARD`
- False positives:
  - `UPLOAD_AUDIT_RETENTION`
  - `UPLOAD_PATH_ISOLATION`
  - `UPLOAD_TYPE_MAGIC`

This satisfies the sprint requirement because the installed package path executed on a second case and produced real verifier feedback through the runtime path.

### 3. compare-variants now supports installed package variants

Fresh command:

```powershell
skill-deploy compare-variants --cases upload --backend offline_deterministic --source installed
```

Fresh package-level report:

- `outputs/validation/skill_marginal_utility/installed_package_marginal_utility.json`

Per-variant fresh metadata:

- `outputs/validation/skill_marginal_utility/upload_security_001/installed_v1/run_metadata.json`
- `outputs/validation/skill_marginal_utility/upload_security_001/installed_v2/run_metadata.json`
- `outputs/validation/skill_marginal_utility/upload_security_001/active_installed/run_metadata.json`

Verified metadata fields:

- `skill_package_path`
- `skill_hash`
- `manifest_hash`
- `active_pointer_snapshot`
- `run_id`
- `target_hash`
- `verifier_hash`
- `schema_version`
- `model`
- `cost/tokens` or explicit unavailable reason

Observed package-level gains:

- `installed_v2_over_installed_v1_gain = 0.3333`
- `active_installed_over_installed_v1_gain = 0.3333`
- `active_installed_over_installed_v2_gain = 0.0`

## Failed

- None in the sense of "required command could not execute".

## Blocked

- None in this sprint.

## Remaining Gap

- The installed `secure_code_review` package is still behaviorally specialized toward `upload_security_001`. It now passes that case in the real runtime path, but it is not yet a genuinely multi-case installed package.
- The second-case run on `data_quality_review_001` proves the installed runtime path works beyond one case, but the current installed package content is not appropriate for that case and therefore correctly fails the verifier.
- Installed-source compare currently reports `candidate_v3_package` as unavailable for `upload_security_001` because the existing candidate package is `config_security_001__v3_candidate_001`, not an upload-scoped candidate.
- Cost remains `null` for offline deterministic execution, by design; token counts are estimated from skill text only.

## Verification

- `python -m pytest -q` -> `42 passed`
- `skill-deploy validate-review-package` -> `0 errors`
