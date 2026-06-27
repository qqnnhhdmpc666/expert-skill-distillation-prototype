# Quickstart

This quickstart exercises the current V1 `eskill` path. The older `skill-deploy` commands belong to the legacy controlled Skill deployment lane and are not the main V1 entry point.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Run The End-To-End Demo

```powershell
eskill --state-dir .eskill demo --data-dir data/v1_walking_skeleton
```

Expected result: a JSON object with `status=pass`, a `bundle_digest`, a `session_id`, a decision verdict, and OSV evidence digests.

## Build And Run Manually

```powershell
eskill --state-dir .eskill init
eskill --state-dir .eskill source add data/v1_walking_skeleton/expert_spec/python_advisory_review.md --adapter expert-document
eskill --state-dir .eskill source add data/v1_walking_skeleton/osv/PYSEC-2018-28.json --adapter osv-snapshot
eskill --state-dir .eskill build python-advisory
eskill --state-dir .eskill run python-advisory --requirements data/v1_walking_skeleton/runtime_inputs/requirements.txt --environment data/v1_walking_skeleton/runtime_inputs/environment.json --advisory PYSEC-2018-28
```

## Public OSV Reference Runtime

```powershell
python scripts\run_public_osv_pilot.py --data-dir data\public_osv_pilot --output outputs\public_osv_pilot\reference_runtime_results_v2.json
```

Current recorded result: 33/33 cases passed with false-safe count 0.

## Compiler-vs-Direct Preparation

```powershell
eskill --state-dir .tmp\public-comparison-state prepare-public-comparison --data-dir data\public_osv_pilot --direct-base-url https://api.deepseek.com --direct-model deepseek-chat
```

This prepares distinct `direct_to_skill_ir` and `compiler_distilled_skill` artifacts. It does not evaluate compiler superiority unless a mature AgentHost is available.

## AgentHost Qualification

```powershell
eskill --state-dir .tmp\judge-pass-state qualify-agent-host --executable "$env:APPDATA\npm\codex.cmd" --task-id codex-agent-host-qualification --timeout 90
```

Current status: `hard_blocked_no_compatible_mature_host`. DeepSeek Chat Completions is not compatible with Codex 0.137's Responses provider protocol, and the local OpenAI Responses attempt is not usable with the current endpoint/credential state.

## Harbor Public OSV Subset

```powershell
python scripts\build_harbor_public_osv_subset.py --data-dir data\public_osv_pilot --output data\harbor_tasks\public_osv_subset
wsl.exe -d Ubuntu-24.04-Codex -- /opt/spark/harbor-src-locked/.venv/bin/harbor run --path '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/data/harbor_tasks/public_osv_subset' --agent oracle --env docker --n-concurrent 1 --jobs-dir '/mnt/c/Users/31552/Documents/New project/expert-skill-distillation-prototype-main/outputs/harbor_public_osv_subset' --job-name public-osv-subset-20260623-lf --force-build --export-traces --export-verifier-metadata
```

Current recorded result: 6/6 oracle/verifier parity, 0 errors, mean reward 1.0. This is not Agent effectiveness evidence.

## Validation

```powershell
python -m pytest -q
python -m ruff check src/expert_skill_system tests/v1
python scripts\validate_task_cases.py
python -m skill_deployment.cli validate-review-package
```

For a clean environment smoke:

```powershell
python -m venv .tmp\clean-doc-agent-venv
.\.tmp\clean-doc-agent-venv\Scripts\python.exe -m pip install -e .[dev]
.\.tmp\clean-doc-agent-venv\Scripts\eskill.exe --state-dir .tmp\clean-doc-agent-state demo --data-dir data\v1_walking_skeleton
.\.tmp\clean-doc-agent-venv\Scripts\python.exe -m pytest tests\v1 -q
```
