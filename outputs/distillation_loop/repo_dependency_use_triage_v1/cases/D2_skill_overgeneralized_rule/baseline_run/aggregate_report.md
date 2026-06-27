# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `1`
- fail_count: `3`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:76c52d01c3128cbbd33b58b9fab6e2dd38931a663c5b28ff6f26670a0c0d1fd0`
- skill_digest: `sha256:b124b81e4c97a5ea87caf38b56c420499c90f0864cf23caf5d9c816e48f2fc83`
- skill_artifact_digest: `sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d`
- knowledge_projection_digest: `sha256:08b541c1abe585c215273ebc9bb6a89b2b52ea38a588dc48d20f1d67b10d1af7`
- knowledge_access_binding_digest: `sha256:497ecd7de9a0143ce4caeda3adbf2fc0132cce069242b25ebe02c002841ee1ba`
- provider_policy_digest: `sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243`
- skill_family: `repo-dependency-use-triage`
- fixture_type_distribution: `{"local_public_like_demo": 3, "public_repo_excerpt": 1}`

## Failure Counters

- schema_fail_count: `0`
- verifier_fail_count: `3`
- runtime_failure_count: `0`
- evidence_resolution_failures: `0`
- hidden_gold_leakage_failures: `0`

## Claim Boundary

- This is a reproducible local repo-level evaluation harness.
- It does not prove compiler superiority.
- It does not claim general vulnerability discovery.
- It does not claim AgentHost, OpenHands, SWE-agent, Harbor, or production scanner effectiveness.

## Tasks

| task_id | fixture_type | verifier_pass | decision | failure_category | source |
|---|---|---:|---|---|---|
| `dependency_use_triage_requests_demo` | `local_public_like_demo` | `False` | `dependency_used_and_affected` | `reason_code_error` | local://repo_security_tasks/dependency_use_triage_requests_demo |
| `dependency_use_triage_declared_not_used` | `local_public_like_demo` | `True` | `dependency_present_not_used` | `None` | local://repo_security_tasks/dependency_use_triage_declared_not_used |
| `dependency_use_triage_version_not_affected` | `local_public_like_demo` | `False` | `dependency_used_and_affected` | `reason_code_error` | local://repo_security_tasks/dependency_use_triage_version_not_affected |
| `dependency_use_triage_the_gan_zoo_public` | `public_repo_excerpt` | `False` | `dependency_used_and_affected` | `reason_code_error` | https://github.com/hindupuravinash/the-gan-zoo |
