# Task-Conditioned Installed Skill Status

Date: 2026-06-11

Scope: P0-F Task-Conditioned Installed Skill Validation only.

Boundary:

- No Harbor live work
- No external benchmark work
- No UI
- No database
- No service API
- No verifier relaxation
- No data-quality capability promotion into `secure_code_review`

## Summary

This sprint moved `secure_code_review` from upload-only installed behavior to task-conditioned installed behavior for controlled security tasks.

The active installed `v2` package now contains three runtime groups:

- `upload_security`
- `config_security`
- `out_of_scope_guard`

The installed runtime path now activates the matching capability group from manifest metadata, preserves upload pass behavior, passes a second security case on `config_security_001`, and records explicit out-of-scope evidence for `data_quality_review_001` without emitting upload false positives.

## Fresh Commands

```powershell
skill-deploy build-codex-skill
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v1
skill-deploy install --skill outputs/deployable_codex_skill/secure_code_review --version v2
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic
skill-deploy run-skill --installed secure_code_review --case data_quality_review_001 --backend offline_deterministic
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
python -m pytest -q
skill-deploy validate-review-package
python scripts/validate_task_cases.py
```

## Pass

### 1. Upload still passes on the installed runtime path

Fresh command:

```powershell
skill-deploy run-skill --installed secure_code_review --case upload_security_001 --backend offline_deterministic
```

Fresh artifacts:

- `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T155237925663Z_v2/evidence_bundle/summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review/upload_security_001/20260611T155237925663Z_v2/verifier_report.json`

Verified evidence fields:

- `runtime_source = installed_skill_package`
- `verifier_result = pass`
- `task_family = upload_security`
- `activated_capability_group = upload_security`
- `skill_version = v2`
- `skill_hash = 596b331593a25bdd92b781514f2ac2e4f5b2710fa4d2915ca9550885f928b355`
- `manifest_hash = 0dbe192a8b73a7f7b677c2f847593a7f142e5b9d04de95d85388632098caa1be`

### 2. Second security case selected as config and now passes

Selected second security case:

- `config_security_001`

Reason:

- `config_security_001` was not blocked after task-conditioned activation was added, so there was no need to fall back to API/code-review.

Fresh command:

```powershell
skill-deploy run-skill --installed secure_code_review --case config_security_001 --backend offline_deterministic
```

Fresh artifacts:

- `outputs/runtime_runs/installed_skills/secure_code_review/config_security_001/20260611T155238127374Z_v2/evidence_bundle/summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review/config_security_001/20260611T155238127374Z_v2/verifier_report.json`

Verified evidence fields:

- `runtime_source = installed_skill_package`
- `verifier_result = pass`
- `task_family = config_security`
- `activated_capability_group = config_security`
- `skill_hash = 596b331593a25bdd92b781514f2ac2e4f5b2710fa4d2915ca9550885f928b355`
- `manifest_hash = 0dbe192a8b73a7f7b677c2f847593a7f142e5b9d04de95d85388632098caa1be`

### 3. Non-applicable data-quality task no longer emits upload false positives

Fresh command:

```powershell
skill-deploy run-skill --installed secure_code_review --case data_quality_review_001 --backend offline_deterministic
```

Fresh artifacts:

- `outputs/runtime_runs/installed_skills/secure_code_review/data_quality_review_001/20260611T155238112577Z_v2/evidence_bundle/summary.json`
- `outputs/runtime_runs/installed_skills/secure_code_review/data_quality_review_001/20260611T155238112577Z_v2/verifier_report.json`

Observed behavior:

- `pass = false`
- `feedback_type = missing_capability`
- `false_positive_capabilities = []`
- `activated_capability_group = out_of_scope_guard`
- `out_of_scope = true`
- `unsupported_task_family = data_quality_review`

This is the intended bounded behavior for this sprint: the task is explicitly out of scope, no upload rules are incorrectly activated, and the failure evidence is preserved.

### 4. Installed-source compare-variants now records task-conditioned provenance

Fresh command:

```powershell
skill-deploy compare-variants --cases upload,config --backend offline_deterministic --source installed
```

Fresh summary artifact:

- `outputs/validation/skill_marginal_utility/installed_package_marginal_utility.json`

Fresh per-variant metadata examples:

- `outputs/validation/skill_marginal_utility/upload_security_001/active_installed/run_metadata.json`
- `outputs/validation/skill_marginal_utility/config_security_001/active_installed/run_metadata.json`

Verified metadata fields:

- `task_family`
- `activated_capability_group`
- `skill_hash`
- `manifest_hash`
- `active_pointer_snapshot`

Observed package-level marginal utility:

- `upload_security_001`: `installed_v2_over_installed_v1_gain = 0.3333`
- `config_security_001`: `installed_v2_over_installed_v1_gain = 0.4`

Observed real failure retention:

- `config_security_001` on `installed_v1` fails with `missing_capability`
- `config_security_001` on `installed_v1` has `false_positive_capabilities = []`
- `installed_v1` therefore fails honestly through out-of-scope guard behavior rather than by firing upload findings on config text

### 5. Package and runtime metadata are now task-conditioned

Fresh package artifacts:

- `outputs/deployable_codex_skill/secure_code_review/manifest.json`
- `outputs/deployable_codex_skill/secure_code_review/versions/v1/manifest.json`
- `outputs/deployable_codex_skill/secure_code_review/versions/v2/manifest.json`
- `outputs/deployable_codex_skill/secure_code_review/versions/v2/SKILL.md`

Current `v2` capability groups:

- `upload_security`
- `config_security`
- `out_of_scope_guard`

Current `v1` capability groups:

- `upload_security`
- `out_of_scope_guard`

## Fail

- None in the sense of "required command could not execute".

## Blocked

- None in this sprint.

## Remaining Gap

- This sprint chose `config_security` rather than `api_review` for the second security family. `secure_code_review` is now task-conditioned for upload plus config, but not yet for API/code-review.
- `data_quality_review_001` is intentionally out of scope, but the verifier still reports that state as `missing_capability`. The runtime evidence is explicit, yet there is no dedicated verifier label for `unsupported_task_family`.
- Installed-source compare can include `candidate_v3_package` for `config_security_001` because that candidate already exists, but upload still has no installed candidate package variant.
- Offline deterministic runs still report `cost = null` and estimated token counts only.

## Verification

- `python -m pytest -q` -> `45 passed`
- `skill-deploy validate-review-package` -> `0 errors`
- `python scripts/validate_task_cases.py` -> `7 controlled cases valid`
