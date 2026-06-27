# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `0`
- fail_count: `4`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:f1995e2b77b431ad1e388c4a815c1f4fe2aa7b1e8e25bf145315feec54344c84`
- skill_digest: `sha256:a15dcab47f70308d41ada62e1c3487a0418a2cbd5afedd8aacd1f05c8deb7fb7`
- skill_artifact_digest: `sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d`
- knowledge_projection_digest: `sha256:48fc70269d99b124327797227a1095095f20286dd29a2cf46ed2945d9ecd97fe`
- knowledge_access_binding_digest: `sha256:0af18b84dccdd88791c7518df94d1769d337be4d9c86fa90a9ab8ce3cf8f3368`
- provider_policy_digest: `sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243`
- skill_family: `repo-dependency-use-triage`
- fixture_type_distribution: `{"local_public_like_demo": 3, "public_repo_excerpt": 1}`

## Failure Counters

- schema_fail_count: `0`
- verifier_fail_count: `4`
- runtime_failure_count: `0`
- evidence_resolution_failures: `4`
- hidden_gold_leakage_failures: `0`

## Claim Boundary

- This is a reproducible local repo-level evaluation harness.
- It does not prove compiler superiority.
- It does not claim general vulnerability discovery.
- It does not claim AgentHost, OpenHands, SWE-agent, Harbor, or production scanner effectiveness.

## Tasks

| task_id | fixture_type | verifier_pass | decision | failure_category | source |
|---|---|---:|---|---|---|
| `dependency_use_triage_requests_demo` | `local_public_like_demo` | `False` | `unresolved` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_requests_demo |
| `dependency_use_triage_declared_not_used` | `local_public_like_demo` | `False` | `unresolved` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_declared_not_used |
| `dependency_use_triage_version_not_affected` | `local_public_like_demo` | `False` | `unresolved` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_version_not_affected |
| `dependency_use_triage_the_gan_zoo_public` | `public_repo_excerpt` | `False` | `unresolved` | `evidence_error` | https://github.com/hindupuravinash/the-gan-zoo |
