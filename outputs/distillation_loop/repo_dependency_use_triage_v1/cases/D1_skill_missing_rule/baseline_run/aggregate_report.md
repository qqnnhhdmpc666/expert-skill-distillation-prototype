# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `0`
- fail_count: `4`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:7d7b6cb8fa8eb7913140f80fd631f8dbb51ad2ae97fa6fd3c28db438bd2f11cc`
- skill_digest: `sha256:643a1bac05f2cfd8ecd85338c0fb27aafa4560bf50fc9d469a2e9d80daed111c`
- skill_artifact_digest: `sha256:2e6d5a1a9edff162dd31f8eec4aec4fd6daaefc3cbf405848cb462ae24d1af11`
- knowledge_projection_digest: `sha256:f11bf2588d408abd8bd892a8cd7671c82c7abc64fa81318047c54167ac8348cd`
- knowledge_access_binding_digest: `sha256:b5890d14ac0c5a4083f20084bf50fd8dc64fc20d0c9622b6b15adac3a7880126`
- provider_policy_digest: `sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243`
- skill_family: `repo-dependency-use-triage`
- fixture_type_distribution: `{"local_public_like_demo": 3, "public_repo_excerpt": 1}`

## Failure Counters

- schema_fail_count: `0`
- verifier_fail_count: `4`
- runtime_failure_count: `0`
- evidence_resolution_failures: `3`
- hidden_gold_leakage_failures: `0`

## Claim Boundary

- This is a reproducible local repo-level evaluation harness.
- It does not prove compiler superiority.
- It does not claim general vulnerability discovery.
- It does not claim AgentHost, OpenHands, SWE-agent, Harbor, or production scanner effectiveness.

## Tasks

| task_id | fixture_type | verifier_pass | decision | failure_category | source |
|---|---|---:|---|---|---|
| `dependency_use_triage_requests_demo` | `local_public_like_demo` | `False` | `dependency_used_and_affected` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_requests_demo |
| `dependency_use_triage_declared_not_used` | `local_public_like_demo` | `False` | `dependency_used_and_affected` | `reason_code_error` | local://repo_security_tasks/dependency_use_triage_declared_not_used |
| `dependency_use_triage_version_not_affected` | `local_public_like_demo` | `False` | `dependency_used_not_affected` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_version_not_affected |
| `dependency_use_triage_the_gan_zoo_public` | `public_repo_excerpt` | `False` | `dependency_used_and_affected` | `evidence_error` | https://github.com/hindupuravinash/the-gan-zoo |
