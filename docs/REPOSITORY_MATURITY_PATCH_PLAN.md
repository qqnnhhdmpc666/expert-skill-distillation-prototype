# Repository Maturity Patch Plan

Date: 2026-06-06

## Purpose

This patch adds the smallest engineering skeleton needed to reduce the most visible maturity gap with SPARK-PDI and COLLEAGUE.SKILL.

It does not claim that the repository is now a mature open-source platform.

## What This Patch Adds

Minimal package/config skeleton:

```text
pyproject.toml
src/skill_deployment/
tests/
scripts/validate_task_cases.py
scripts/skill_deploy.py
```

Reusable helpers:

- `schemas.py`: `TaskCase` schema and loader.
- `artifacts.py`: artifact manifest checker.
- `token_budget.py`: deterministic token proxy and budget check.
- `gate.py`: validation gate result structure and gate helper.
- `trace.py`: partial rule-application trace helper.
- `cli.py`: lightweight command router.

Fast tests:

- `test_task_case_schema.py`
- `test_validation_gate.py`
- `test_trace_verifier.py`
- `test_token_budget.py`
- `test_artifact_manifest.py`

CLI commands:

```text
python scripts/skill_deploy.py check-existing
python scripts/skill_deploy.py audit-claims
python scripts/skill_deploy.py validate-cases
python scripts/skill_deploy.py run-holdout
```

## What This Patch Does Not Do

It does not:

- move all scripts into `src/`;
- rewrite the demo pipeline;
- change existing experimental outputs;
- add external LLM/model integrations;
- introduce heavyweight dependencies;
- add CI yet;
- claim mature platform status.

## Why This Is Enough For This Round

The biggest visible maturity gap was that the repository looked purely script-first. This patch gives it:

- project metadata;
- importable package namespace;
- shared schemas/helpers;
- fast tests;
- a lightweight CLI wrapper;
- task-case validation.

That is enough to show movement toward engineering maturity without risking the stable demo.

## Remaining Gaps

Still missing:

- full schema validation for every artifact type;
- centralized runner abstraction;
- CI workflow;
- dependency lock strategy;
- typed model classes for every report;
- packaging/install docs;
- broader unit and integration tests.

Safe statement:

```text
The repository has moved from pure script-first demo code toward a minimal package/schema/test skeleton, but it remains a research/demo prototype rather than a mature open-source platform.
```
