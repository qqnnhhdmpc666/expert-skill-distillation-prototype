# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `4`
- fail_count: `0`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:e51359a9edb0cf3d64d6d2954a0d70785bf35a2a00c2e5c1100bf5ef3db9bbda`
- skill_digest: `sha256:cd7654b5f6fa179fe15584134fbdc566823820894616c0e52e9c4246dd5ee54e`
- skill_artifact_digest: `sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d`
- knowledge_projection_digest: `sha256:89f2cad11b8abfa7fa3b6ca05e729608e2c0a93f196903896eec078a3e0a022d`
- knowledge_access_binding_digest: `sha256:a6837564627784861348c314666da818ebe6a6d97281b3a07f30cf1c9d654845`
- provider_policy_digest: `sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243`
- skill_family: `repo-dependency-use-triage`
- fixture_type_distribution: `{"local_public_like_demo": 3, "public_repo_excerpt": 1}`

## Failure Counters

- schema_fail_count: `0`
- verifier_fail_count: `0`
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
| `dependency_use_triage_requests_demo` | `local_public_like_demo` | `True` | `dependency_used_and_affected` | `None` | local://repo_security_tasks/dependency_use_triage_requests_demo |
| `dependency_use_triage_declared_not_used` | `local_public_like_demo` | `True` | `dependency_present_not_used` | `None` | local://repo_security_tasks/dependency_use_triage_declared_not_used |
| `dependency_use_triage_version_not_affected` | `local_public_like_demo` | `True` | `dependency_used_not_affected` | `None` | local://repo_security_tasks/dependency_use_triage_version_not_affected |
| `dependency_use_triage_the_gan_zoo_public` | `public_repo_excerpt` | `True` | `dependency_used_and_affected` | `None` | https://github.com/hindupuravinash/the-gan-zoo |
