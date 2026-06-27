# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `1`
- fail_count: `3`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:c7206312e35fbae03be5e4c3ea90c6323e4421ba757b611b744af99b631adf8b`
- skill_digest: `sha256:4eebaefd22fd610acacdf50781ce3c7a36ef2b3eefeb18a1828685db98663500`
- skill_artifact_digest: `sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d`
- knowledge_projection_digest: `sha256:6b970e333f03091ca5cb2df6a3911247d3074365187ebe957d4a2c749d60b2ee`
- knowledge_access_binding_digest: `sha256:bafeb71cbab3d48b02b426d267c8fad8afcf0a5bb25d1856960f927a90032940`
- provider_policy_digest: `sha256:77b91a75a18e435d752c51fc8633264b3cd9dd0224007a4b4c6862bbc6288243`
- skill_family: `repo-dependency-use-triage`
- fixture_type_distribution: `{"local_public_like_demo": 3, "public_repo_excerpt": 1}`

## Failure Counters

- schema_fail_count: `0`
- verifier_fail_count: `3`
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
| `dependency_use_triage_requests_demo` | `local_public_like_demo` | `False` | `dependency_present_not_used` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_requests_demo |
| `dependency_use_triage_declared_not_used` | `local_public_like_demo` | `True` | `dependency_present_not_used` | `None` | local://repo_security_tasks/dependency_use_triage_declared_not_used |
| `dependency_use_triage_version_not_affected` | `local_public_like_demo` | `False` | `dependency_present_not_used` | `evidence_error` | local://repo_security_tasks/dependency_use_triage_version_not_affected |
| `dependency_use_triage_the_gan_zoo_public` | `public_repo_excerpt` | `False` | `dependency_present_not_used` | `evidence_error` | https://github.com/hindupuravinash/the-gan-zoo |
