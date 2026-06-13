# Harbor Runner Integration Status

Updated: 2026-06-09

## Result

Current status: **minimal read-existing Harbor BackendRunner adapter completed**.

This is intentionally small-scope. It does not replace the existing Harbor scripts. It makes the strongest Harbor repair-loop evidence readable through the shared runner interface.

## Implemented adapter

Shared modules:

- `src/skill_deployment/harbor_adapter.py`
- `src/skill_deployment/runner.py`

New backend names:

- `harbor_llm_repair_upload_replay`
- `harbor_llm_repair_config_replay`

## What the adapter does

For existing Harbor artifacts, it can read:

- `security_report.json`
- `verifier_report.json`
- `reward.json`
- `target_reads.json`
- `skill_manifest.json`
- `backend_metadata.json`
- `summary.json`

It maps those into:

- a normalized `ExecutionReport`
- a `RunnerResult`
- replay artifact path references for downstream summary/audit code

## What it does not do

- it does not rerun Harbor itself
- it does not absorb Docker/WSL job launching into the shared runner path
- it does not unify Harbor verifier logic with local verifier logic
- it does not make Harbor execution generic across all tasks

## Verification

- `python scripts/run_harbor_replay_summary.py --backend harbor_llm_repair_upload_replay --attempt A1` -> PASS
- `python scripts/run_harbor_replay_summary.py --backend harbor_llm_repair_config_replay --attempt A2` -> PASS
- `python -m pytest -q` -> PASS, Harbor replay tests included

## Why this matters

Before this step, Harbor evidence was strong but mostly script-local.

After this step:

- Harbor evidence still remains script-generated
- but the shared system can now consume that evidence through `BackendRunner`
- so Harbor is less of an isolated appendix and more of a connected backend surface

## Boundary

Safe claim:

> Harbor now has a minimal read-existing BackendRunner adapter.

Unsafe claim:

> Harbor is fully integrated into the shared execution skeleton.

## Artifact anchors

- upload replay source: `outputs/harbor_llm_repair_loop_upload_001/`
- config replay source: `outputs/harbor_llm_repair_loop_config_001/`
- replay CLI: `scripts/run_harbor_replay_summary.py`
- tests: `tests/test_harbor_runner_adapter.py`
