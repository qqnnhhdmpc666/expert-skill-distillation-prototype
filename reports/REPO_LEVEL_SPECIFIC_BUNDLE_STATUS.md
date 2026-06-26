# Repo-Level-Specific Bundle Status

Date: 2026-06-27

## Summary

Status:

```text
repo_level_specific_bundle = pass
bundle_build = pass
active_binding = pass
harness_run = pass
task_aware_evidence_binding = pass_static_rule_based
compiler_superiority = not_evaluated
vulnerability_discovery_claim = not_claimed
```

This step upgrades the repo-level harness from consuming a reused
`python-advisory` bundle to consuming a repo-level-specific ReleaseBundle for
`dependency_use_triage`.

## Fresh Commands

```powershell
.\.tmp\clean-core-venv\Scripts\python.exe scripts\build_repo_level_bundle.py --state-dir .tmp\repo-level-specific-bundle-state --data-dir data\repo_level_bundle --skill-family repo-dependency-use-triage --promote
.\.tmp\clean-core-venv\Scripts\python.exe scripts\run_repo_level_eval.py --task-registry data\repo_security_tasks\registry.json --output outputs\repo_level_eval_runs\repo_level_bundle_smoke --state-dir .tmp\repo-level-specific-bundle-state --use-active-binding
```

The same build path is also available through:

```powershell
python -m expert_skill_system.cli --state-dir .tmp\repo-level-specific-bundle-state build-repo-level-bundle --data-dir data\repo_level_bundle --skill-family repo-dependency-use-triage --promote
```

## Bundle Identity

```text
skill_family = repo-dependency-use-triage
repo_level_bundle_digest = sha256:e51359a9edb0cf3d64d6d2954a0d70785bf35a2a00c2e5c1100bf5ef3db9bbda
skill_ir_digest = sha256:cd7654b5f6fa179fe15584134fbdc566823820894616c0e52e9c4246dd5ee54e
agent_skill_artifact_digest = sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d
knowledge_projection_digest = sha256:89f2cad11b8abfa7fa3b6ca05e729608e2c0a93f196903896eec078a3e0a022d
knowledge_access_binding_digest = sha256:a6837564627784861348c314666da818ebe6a6d97281b3a07f30cf1c9d654845
provider_policy_digest = sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243
dependency_manifest_digest = sha256:b7c7645c61a43091fed14193c85a956ad5bfd1b522a02457c06d17b5beca5370
active_binding_generation = 1
```

Previous python-advisory bundle used by `public_snapshot_smoke`:

```text
previous_python_advisory_bundle_digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
bundle_digest_changed = true
```

The new digest is not a rename of the old bundle. The new bundle manifest records
`skill_family=repo-dependency-use-triage` and repo-level evidence contracts.

## Source Artifacts

```text
data/repo_level_bundle/expert_material.md
data/repo_level_bundle/task_contract.json
data/repo_level_bundle/knowledge_contract.json
src/expert_skill_system/compiler/repo_level_bundle_builder.py
scripts/build_repo_level_bundle.py
tests/v1/test_repo_level_specific_bundle.py
```

## Evidence Requirements

The repo-level-specific bundle exposes task-aware evidence requirements through
an artifacted `evidence_binding_plan.v1`, not only prompt text:

```json
{
  "task_type": "dependency_use_triage",
  "required_evidence": [
    "dependency_declaration",
    "resolved_version",
    "import_use_site",
    "advisory_affected_range",
    "decision_evidence"
  ],
  "missing_evidence_policy": {
    "policy": "abstain_or_fail_safe",
    "runtime_decision": "unresolved",
    "reason_code": "REQUIRED_EVIDENCE_MISSING"
  }
}
```

Boundary checks:

```text
advisory_only_decision = invalid
missing_import_use_site = dependency_present_not_used or unresolved, not dependency_used_and_affected
```

## Harness Result

Fresh run:

```text
output_dir = outputs\repo_level_eval_runs\repo_level_bundle_smoke
task_count = 4
pass_count = 4
fail_count = 0
bundle_attachment_mode = real_release_bundle_pinned
skill_family = repo-dependency-use-triage
fixture_type_distribution = local_public_like_demo:3, public_repo_excerpt:1
public_excerpt_task_pass = true
```

Per-task trajectory evidence records:

```text
bundle_attachment_mode
bundle_digest
skill_digest
skill_artifact_digest
knowledge_projection_digest
knowledge_access_binding_digest
provider_policy_digest
skill_family
task_id
prediction_digest
verifier_result_digest
condition_manifest_digest
```

Example public excerpt provenance:

```text
task_id = dependency_use_triage_the_gan_zoo_public
source_url = https://github.com/hindupuravinash/the-gan-zoo
commit_digest = git-sha1:375f2be4a852ead8980c06b2a996893f0cb95713
repo_snapshot_content_digest = sha256:4fa32e652b51130309c78b9d4f52a3020bd5930b289a015e5dc6626c90286ccb
bundle_digest = sha256:e51359a9edb0cf3d64d6d2954a0d70785bf35a2a00c2e5c1100bf5ef3db9bbda
```

## Claim Boundary

Allowed:

> The project now builds and pins a repo-level-specific ReleaseBundle for
> dependency-use triage and runs it through the reproducible repo-level
> evaluation harness, including one traceable public repo excerpt task.

Not claimed:

```text
compiler_superiority = not_evaluated
mature_agenthost_effectiveness = not_evaluated
broad_public_benchmark = not_claimed
vulnerability_discovery = not_claimed
production_vulnerability_scanner = not_claimed
OSV_applicability_as_exploitability = not_claimed
```

## Remaining Gap

The evidence binding hook is static and rule-based in this step. It exposes
repo-level dependency-use triage requirements and prevents advisory-only
decision paths, but it is not yet an open-world repository reasoning agent or a
benchmark-scale vulnerability discovery system.

## Validation

Commands run:

```powershell
.\.tmp\clean-core-venv\Scripts\python.exe -m expert_skill_system.cli --state-dir .tmp\repo-level-specific-bundle-cli-smoke build-repo-level-bundle --data-dir data\repo_level_bundle --skill-family repo-dependency-use-triage --promote
.\.tmp\clean-core-venv\Scripts\python.exe -m pytest tests\v1 -q --basetemp .tmp\pytest-repo-level-v1
.\.tmp\clean-core-venv\Scripts\python.exe -m pytest -q --basetemp .tmp\pytest-repo-level-all
.\.tmp\clean-core-venv\Scripts\python.exe scripts\validate_task_cases.py
.\.tmp\clean-core-venv\Scripts\python.exe -m ruff check <new-or-touched files>
.\.tmp\clean-core-venv\Scripts\skill-deploy.exe validate-review-package
```

Observed:

```text
cli_build_repo_level_bundle = pass
tests_v1 = pass, 73 passed
full_pytest = pass, 127 passed
validate_task_cases = pass, 8 cases
new_or_touched_files_ruff = pass
validate_review_package = pass, 0 errors
full_ruff = failed_legacy_scripts
```

Full ruff still fails on pre-existing legacy scripts under `scripts/` and
`src/expert_skill_system/evaluation/__init__.py`; the new and touched files pass
the scoped ruff check.
