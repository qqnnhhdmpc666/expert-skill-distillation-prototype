# Repo-Level Evaluation Run Report

## Summary

- task_count: `4`
- pass_count: `4`
- fail_count: `0`
- bundle_attachment_mode: `real_release_bundle_pinned`
- bundle_digest: `sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457`
- skill_digest: `sha256:8a1738b57cee10f88b0827c515fe3cb02e7d2894a91a0258696812989b01f045`
- skill_artifact_digest: `sha256:b1e0d32349fe46049d4655d89c87e425d593bdf4a54bf4aee5efea83853cbbdb`
- knowledge_projection_digest: `sha256:0c1919fc0b30afe07c89310ef0e9c220d7f70b9cd3d0c70f1e6bf47722428e1a`
- knowledge_access_binding_digest: `sha256:605312802a2ed4523dd493114fa53f690963ee1dc58a74aea4d6d8dd290022e9`
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
