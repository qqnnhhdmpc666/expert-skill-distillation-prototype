# Repo-Level Evaluation Harness Status

Date: 2026-06-24

## Summary

Implemented a reproducible repo-level evaluation harness for dependency-use triage. The harness connects:

```text
real eskill ReleaseBundle
  -> repo-level security task registry
  -> traceable local repo snapshots
  -> Skill-Knowledge injection metadata
  -> repo evidence collection
  -> prediction.json
  -> deterministic verifier
  -> trajectory evidence package
  -> run-level aggregate report
```

This is an evaluation harness, not a new architecture layer or AgentHost integration.

## Status Fields

```text
core_local_system = pass / unchanged
repo_level_eval_harness = implemented
task_registry = implemented
repo_level_security_tasks = local_fixture_only_with_clear_boundary
dependency_use_triage_runner = pass
release_bundle_pinning = real_release_bundle_pinned
skill_knowledge_injection_protocol = pass
trajectory_evidence_package = pass
repo_evidence_collector = pass
deterministic_verifier = pass
openhands_agenthost = not_in_scope_this_step
swe_agent_host = not_in_scope_this_step
compiler_superiority = not_evaluated
vulnerability_discovery_claim = not_claimed
full_ruff = failed_legacy_scripts
new_or_touched_files_ruff = pass
```

## New Harness Files

- `src/expert_skill_system/evaluation/repo_eval_harness.py`
- `src/expert_skill_system/evaluation/repo_task_registry.py`
- `src/expert_skill_system/evaluation/repo_run_report.py`
- `src/expert_skill_system/runtime/release_bundle_resolver.py`
- `scripts/run_repo_level_eval.py`
- `data/repo_security_tasks/registry.json`
- `tests/v1/test_repo_eval_harness.py`
- `tests/v1/test_repo_task_registry.py`
- `tests/v1/test_release_bundle_resolver.py`
- `tests/v1/test_repo_run_report.py`

## Bundle Pinning

The harness supports:

```text
--state-dir <path>
--bundle-digest <digest>
--use-active-binding
--allow-local-manifest-only
--fail-on-partial-bundle
```

Resolution order:

1. Explicit `--bundle-digest`.
2. Active binding from `--state-dir` when `--use-active-binding` is set.
3. Failure with `bundle_not_available`, unless `--allow-local-manifest-only` is explicitly set.

Fresh real-bundle setup command:

```powershell
python -m expert_skill_system.cli --state-dir .tmp\repo-level-eval-state demo --data-dir data\v1_walking_skeleton
```

Observed active bundle:

```text
bundle_digest = sha256:a38606f2d57160fe556467261c790e1d2b8e4dbac19ca1001d6f7ddc55817457
bundle_attachment_mode = real_release_bundle_pinned
limitation = python-advisory bundle reused as initial system bundle for repo-level harness
```

## Task Registry

Registry:

```text
data/repo_security_tasks/registry.json
```

Runnable tasks:

```text
dependency_use_triage_requests_demo
dependency_use_triage_declared_not_used
dependency_use_triage_version_not_affected
```

Current task source boundary:

```text
repo_level_security_tasks = local_fixture_only_with_clear_boundary
public_repo_snapshot_small = deferred
```

Each task entry records `fixture_type`, `source_url`, `license`, `commit_digest`, `repo_snapshot_ref`, manifest paths, verifier path, and status.

## Run Command

Fresh command:

```powershell
python scripts\run_repo_level_eval.py --task-registry data\repo_security_tasks\registry.json --output outputs\repo_level_eval_runs\latest --state-dir .tmp\repo-level-eval-state --use-active-binding
```

Observed result:

```text
task_count = 3
pass_count = 3
fail_count = 0
bundle_attachment_mode = real_release_bundle_pinned
```

Output directory:

```text
outputs\repo_level_eval_runs\latest
```

Run-level outputs:

- `run_manifest.json`
- `run_provenance.json`
- `bundle_resolution.json`
- `task_results.jsonl`
- `aggregate_report.json`
- `aggregate_report.md`
- `run_summary.json`

Per-task outputs:

- `runtime_task_view.json`
- `condition_manifest.json`
- `skill_manifest.json`
- `knowledge_manifest.json`
- `bundle_manifest.json`
- `repo_evidence.json`
- `prediction.json`
- `verifier_result.json`
- `trajectory_evidence/`

## Report Counters

The aggregate report records:

- `task_count`
- `pass_count`
- `fail_count`
- `schema_fail_count`
- `verifier_fail_count`
- `runtime_failure_count`
- `partial_bundle_count`
- `real_bundle_count`
- `fixture_type_distribution`
- `evidence_resolution_failures`
- `hidden_gold_leakage_failures`

The report separates:

- system/harness result;
- task/verifier result;
- bundle attachment status;
- claim boundary.

## Validation

Commands run:

```powershell
python scripts\run_repo_level_eval.py --task-registry data\repo_security_tasks\registry.json --output outputs\repo_level_eval_runs\latest --state-dir .tmp\repo-level-eval-state --use-active-binding
python -m pytest tests\v1 -q
python -m pytest -q
```

Observed:

```text
repo-level eval = pass, 3/3 tasks
python -m pytest tests\v1 -q = pass, 64 passed
python -m pytest -q = pass, 118 passed
```

Ruff:

```text
full_ruff = failed_legacy_scripts
new_or_touched_files_ruff = pass
```

## Claim Boundary

Allowed claim:

> The project now has a reproducible repo-level evaluation harness that can run dependency-use triage tasks, collect repo evidence, inject Skill/Knowledge metadata, verify predictions deterministically, and emit run-level trajectory evidence and reports.

Not claimed:

- compiler superiority;
- mature AgentHost improvement;
- OpenHands/SWE-agent/Harbor execution;
- general vulnerability discovery;
- OSV applicability as exploitability or reachability proof;
- production scanner readiness.

## Remaining Blockers

- Replace or supplement local fixtures with a small true public repo snapshot.
- Attach a repo-level-specific ReleaseBundle rather than reusing the current `python-advisory` bundle.
- Add AgentHost/Harbor/OpenHands/SWE-agent execution only after the deterministic harness remains stable.
- Clean legacy `scripts/` ruff failures before marking full repository lint as pass.
