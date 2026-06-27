# Multi-Skill-Family Lifecycle Status

Date: 2026-06-27

## Summary

The multi-skill-family lifecycle runner now builds and evaluates two separate skill families through one orchestration entrypoint:

- `python-advisory`
- `repo-dependency-use-triage`

Fresh command:

```powershell
python scripts\run_skill_family_lifecycle.py --family-registry data\skill_families\registry.json --families python-advisory,repo-dependency-use-triage --output outputs\multi_skill_family_lifecycle\latest
```

Result:

- `multi_skill_family_lifecycle`: `pass`
- `family_registry`: `pass`
- `family_count`: `2`
- `python_advisory_bundle`: `pass`
- `repo_dependency_use_triage_bundle`: `pass`
- `repo_level_eval`: `pass`
- `cross_family_bundle_matrix`: `pass`
- `claim_boundary_matrix`: `pass`

## Evidence

Primary lifecycle artifacts:

- `outputs/multi_skill_family_lifecycle/latest/lifecycle_manifest.json`
- `outputs/multi_skill_family_lifecycle/latest/family_builds.json`
- `outputs/multi_skill_family_lifecycle/latest/active_bindings.json`
- `outputs/multi_skill_family_lifecycle/latest/eval_runs.jsonl`
- `outputs/multi_skill_family_lifecycle/latest/bundle_matrix.json`
- `outputs/multi_skill_family_lifecycle/latest/claim_boundary_matrix.json`
- `outputs/multi_skill_family_lifecycle/latest/aggregate_lifecycle_report.json`
- `outputs/multi_skill_family_lifecycle/latest/aggregate_lifecycle_report.md`

## Families

| skill_family | build_status | evaluation_status | bundle_digest | binding_key |
|---|---|---|---|---|
| `python-advisory` | `pass` | `partial_no_family_eval_harness` | `sha256:a458b8005fd99e26820231a21c411fdcb1b9d195d571fd60dbe4e168afbb89f4` | `python-advisory` |
| `repo-dependency-use-triage` | `pass` | `pass` | `sha256:e51359a9edb0cf3d64d6d2954a0d70785bf35a2a00c2e5c1100bf5ef3db9bbda` | `repo-dependency-use-triage` |

## Bundle Matrix

The bundle matrix passed these boundary checks:

- `repo_bundle_digest_differs_from_python_advisory`
- `repo_family_contains_repo_evidence_requirements`
- `python_advisory_not_masquerading_as_repo_bundle`
- `active_binding_keys_are_family_specific`

The repo-level family requires these evidence types:

- `dependency_declaration`
- `resolved_version`
- `import_use_site`
- `advisory_affected_range`
- `decision_evidence`

The python advisory family remains a separate OSV applicability bundle and is not treated as a repo-level dependency-use triage bundle.

## Claim Boundary

This run does not claim:

- `compiler_superiority`
- `mature_agenthost_effectiveness`
- `general_vulnerability_discovery`
- `production_scanner_readiness`
- `official_public_benchmark_performance`
- `exploitability_or_reachability`

The repo-level harness result is deterministic local evidence over the current repo-level task registry, including local fixtures and one traceable public excerpt. It is not an official public benchmark result.

## Remaining Gap

- `python-advisory` currently has a deterministic runtime smoke but no comparable family-level evaluation harness in this orchestration step.
- AgentHost/OpenHands/SWE-agent integration is intentionally out of scope for this step.
- This run proves multi-family lifecycle orchestration, bundle separation, family-specific active bindings, and conservative claim boundaries; it does not prove compiler superiority or general vulnerability discovery.
