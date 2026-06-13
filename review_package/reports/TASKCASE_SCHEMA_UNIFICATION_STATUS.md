# TaskCase Schema Unification Status

## Result

Current status: **partially unified, with one canonical forward path**.

What changed:

- `src/skill_deployment/task_cases.py` now owns the canonical controlled task-case loader and validator.
- `scripts/validate_task_cases.py` and `scripts/run_generalization_suite.py` both delegate to that shared module.
- `skill_deployment.TaskCase` now denotes the controlled task-case model used by `data/task_cases/<case>/`.
- the older API-review holdout format is preserved only as a compatibility layer:
  - `LegacyHoldoutTaskCase`
  - `load_legacy_holdout_task_cases(...)`

## Why this matters

Before this change, the controlled-suite truth lived mainly inside orchestration scripts. Now the main task schema for current work is owned by shared code.

That means a new controlled task can now be added by editing only:

- `data/task_cases/<case>/case.yaml`
- `source_materials/`
- `target_asset/`
- `verifier_contract.yaml`

without adding a new parser branch in the main suite script.

## What is still not fully unified

1. legacy holdout data under `data/api_review_holdout_cases/` still uses `case.md + expected.json`
2. some older scripts such as `run_multitask_closed_loop.py` still carry historical local dataclasses

## Verification

- `python scripts/validate_task_cases.py` -> PASS, 7 cases
- `python scripts/run_generalization_suite.py --backend offline_deterministic --scenarios upload,auth,config,api_review,data_quality` -> PASS
- `python scripts/run_generalization_suite.py --backend non_oracle_local_semantic --scenarios upload,auth,config,api_review,data_quality` -> PASS
