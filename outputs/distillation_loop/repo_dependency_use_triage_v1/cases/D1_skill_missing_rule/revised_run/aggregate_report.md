# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `4`
- fail_count: `0`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:84e886640c688afe35ccdd2cf215e684ee726998bc93a5bb6fb110556c19b816`
- skill_digest: `sha256:25dd2c5f07cbbcd9e4bbcd3b124be79d6542c29f2c973a5a5fe6305395b96284`
- skill_artifact_digest: `sha256:78d6d907ecb8a4cfcd333d23cec8312b82eda815026b45966940d8417707729d`
- knowledge_projection_digest: `sha256:56c6bb6ba4dbf523691e2a18a7dd73242ff67a317917ac6dc882d084f557c566`
- knowledge_access_binding_digest: `sha256:eaf50af4acdb094a6619773a1f325f75b7c3e6e0315d50faaaa7c1fc0b6f51ae`
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
