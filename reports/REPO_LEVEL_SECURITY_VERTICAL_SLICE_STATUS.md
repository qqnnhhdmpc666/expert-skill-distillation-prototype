# Repo-Level Security Vertical Slice Status

Date: 2026-06-23

## Summary

This follow-up upgrades the prior repo-level security smoke into a more evidence-grounded local vertical slice, but it remains conservative:

```text
fixture_type = local_public_like_demo
non_toy_status = partial
bundle_attachment = partial_local_manifest_only
```

The implemented task family is `dependency_use_triage`: combine repo dependency declaration, version evidence, import/use evidence, and an allowed advisory snapshot to produce `prediction.json`, then evaluate it with a deterministic verifier and trajectory evidence package.

## Current Status Fields

```text
core_local_system = pass / unchanged
repo_level_security_task = partial
dependency_use_triage_vertical_slice = partial
skill_knowledge_injection_protocol = pass
trajectory_evidence_package = pass
evidence_binding_algorithm = partial
repo_evidence_collector = pass
deterministic_verifier = pass
bundle_attachment = partial_local_manifest_only
full_ruff = failed_legacy_scripts
new_files_ruff = pass
openhands_agenthost = not_in_scope_this_step
swe_agent_host = not_in_scope_this_step
compiler_superiority = not_evaluated
vulnerability_discovery_claim = not_claimed
```

## Implemented Artifacts

- `src/expert_skill_system/evaluation/repo_evidence_collector.py`
- `src/expert_skill_system/evaluation/repo_security_task.py`
- `src/expert_skill_system/evaluation/repo_security_verifier.py`
- `src/expert_skill_system/runtime/skill_knowledge_injection.py`
- `src/expert_skill_system/runtime/trajectory_evidence.py`
- `src/expert_skill_system/compiler/evidence_binding.py`
- `scripts/run_repo_security_vertical_slice.py`
- `data/repo_security_tasks/dependency_use_triage_requests_demo/`
- `data/repo_security_tasks/dependency_use_triage_declared_not_used/`
- `data/repo_security_tasks/dependency_use_triage_version_not_affected/`

## Runnable Command

```powershell
python scripts\run_repo_security_vertical_slice.py --task data\repo_security_tasks --output outputs\repo_security_vertical_slice_followup
```

Fresh observed result:

```text
task_count = 3
pass_count = 3
```

Each task output contains:

- `prediction.json`
- `verifier_result.json`
- `trajectory_evidence/`

## Acceptance Criteria Audit

| criterion | status | evidence path | remaining gap |
|---|---:|---|---|
| At least one repo-level dependency-use triage task exists | pass | `data/repo_security_tasks/dependency_use_triage_requests_demo/` | Still local fixture, not public repo benchmark |
| Runtime/evaluator fields separated | pass | `load_runtime_task_view(...)`, `tests/v1/test_repo_security_task_schema.py` | `task.json` still stores hidden gold, but runtime APIs expose sanitized view only |
| Skill-Knowledge bundle can attach to task | partial | `skill_knowledge_injection.py`, generated `condition_manifest.json` | Attachment is local manifests, not a compiled `ReleaseBundle` digest |
| Runtime can produce `prediction.json` | pass | `scripts/run_repo_security_vertical_slice.py`, output run summary | Deterministic local runtime only |
| Deterministic verifier evaluates prediction | pass | `repo_security_verifier.py`, `tests/v1/test_repo_security_verifier.py` | Does not replace external benchmark evaluator |
| Trajectory evidence package generated | pass | `trajectory_evidence.py`, generated `trajectory_evidence/` directories | Cost/timing remains local deterministic placeholder |
| Evidence binding explicit interface | partial | `evidence_binding.py`, `tests/v1/test_evidence_binding.py` | Rule-based static plan, not learned or optimized binding |
| Tests for schema, injection, evidence package, verifier, evidence binding | pass | `tests/v1/` | Full ruff still blocked by legacy scripts |
| Status report explains implemented/partial/nonclaims | pass | this file | Must stay conservative until public repo benchmark and real bundle attachment exist |

## Task Fixture Audit

The three fixtures include:

- `public_source`
- `license`
- `commit_digest`
- `repo_snapshot_ref`
- `source_url`
- `snapshot_id`
- file-level SHA-256 manifest
- file paths and line counts
- dependency declaration evidence
- resolved version evidence
- import/use evidence where present
- advisory affected-range evidence

They are intentionally small and deterministic. They are not official public benchmark instances.

## Verifier Coverage

The verifier checks:

- prediction schema;
- hidden gold absence from prediction;
- final decision;
- required reason codes;
- required evidence types;
- evidence refs resolving to runtime-visible repo files or allowed knowledge;
- dependency declaration evidence;
- resolved version evidence;
- import/use evidence when verdict claims use;
- advisory range evidence.

Negative tests cover:

- correct decision with missing import/use evidence;
- non-existent file/path refs;
- hidden-gold-like field leakage;
- advisory-only prediction with no repo evidence;
- wrong version-range reason code.

## Bundle Attachment Audit

Current state:

```text
bundle_attachment = partial_local_manifest_only
skill_digest = digest of sanitized runtime task view
knowledge_projection_digest = digest of allowed_knowledge.json
bundle_digest = local manifest digest
```

This is enough for local protocol testing, but not enough to claim full compiled `ReleaseBundle` attachment. A future step must pin a real `eskill build` bundle digest and route this vertical slice through it before claiming complete Skill-Knowledge bundle integration.

## Validation Commands

```powershell
python -m ruff check src\expert_skill_system\compiler\evidence_binding.py src\expert_skill_system\evaluation\repo_evidence_collector.py src\expert_skill_system\evaluation\repo_security_task.py src\expert_skill_system\evaluation\repo_security_verifier.py src\expert_skill_system\runtime\skill_knowledge_injection.py src\expert_skill_system\runtime\trajectory_evidence.py scripts\run_repo_security_vertical_slice.py tests\v1\test_evidence_binding.py tests\v1\test_repo_evidence_collector.py tests\v1\test_repo_security_task_schema.py tests\v1\test_repo_security_verifier.py tests\v1\test_skill_knowledge_injection_protocol.py tests\v1\test_trajectory_evidence_package.py
python -m pytest tests\v1 -q
python -m pytest -q
```

Full ruff command:

```powershell
python -m ruff check src\expert_skill_system tests\v1 scripts
```

Current full ruff remains `failed_legacy_scripts` due to pre-existing script lint/syntax issues outside this slice.

Observed pytest results:

```text
python -m pytest tests\v1 -q = 57 passed
python -m pytest -q = 111 passed
```

## Nonclaims

This step does not claim:

- vulnerability discovery;
- exploit generation;
- production dependency scanning;
- OpenHands/SWE-agent/Harbor execution;
- compiler superiority over direct generation;
- real public benchmark performance;
- full compiled ReleaseBundle attachment.
