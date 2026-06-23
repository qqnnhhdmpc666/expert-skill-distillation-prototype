# Repo-Level Security Vertical Slice Status

Date: 2026-06-23

## Summary

Implemented the first repo-level security vertical slice for `dependency_use_triage`. The path is:

```text
task package -> skill/knowledge injection manifests -> deterministic runtime -> prediction.json -> native verifier -> trajectory evidence package
```

## Implemented

- `data/repo_security_tasks/dependency_use_triage_requests_demo/`
  - `task.json`
  - `repo_snapshot_manifest.json`
  - `allowed_knowledge.json`
  - `expected_output_schema.json`
  - `verifier.py`
  - `repo_snapshot/`
- `src/expert_skill_system/evaluation/repo_security_task.py`
- `src/expert_skill_system/evaluation/repo_security_verifier.py`
- `src/expert_skill_system/runtime/skill_knowledge_injection.py`
- `src/expert_skill_system/runtime/trajectory_evidence.py`
- `src/expert_skill_system/compiler/evidence_binding.py`
- Tests under `tests/v1/`.

## Current Status Fields

```text
core_local_system = pass
repo_level_security_task = pass
dependency_use_triage_vertical_slice = pass
skill_knowledge_injection_protocol = pass
trajectory_evidence_package = pass
evidence_binding_algorithm = pass
deterministic_verifier = pass
openhands_agenthost = not_in_scope_this_step
swe_agent_host = not_in_scope_this_step
compiler_superiority = not_evaluated
vulnerability_discovery_claim = not_claimed
```

## Fresh Runnable Path

The tests run the current vertical slice end to end:

```powershell
python -m pytest tests/v1/test_repo_security_verifier.py -q
```

The runtime emits:

- `prediction.json`
- `verifier_result.json`
- `trajectory_evidence/outcome.json`
- `trajectory_evidence/provenance.json`

## Boundaries

This is a local deterministic repo-level security triage fixture. It is not:

- an exploit generator;
- a vulnerability discovery benchmark;
- a production dependency scanner;
- proof that compiler-distilled Skill beats direct generation;
- live OpenHands/SWE-agent/Harbor execution.

The point of this step is to make Skill-Knowledge separation testable on a repo-level task with verifier-grounded trajectory evidence.
