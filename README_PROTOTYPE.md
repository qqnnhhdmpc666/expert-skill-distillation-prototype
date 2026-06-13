# Evidence-Grounded Skill Evolution Runtime Prototype

This repository is a deployable research prototype for evidence-grounded agent Skill evolution.

## What This Is

- An Evidence-Grounded Skill Evolution Runtime.
- A Codex Skill + CLI delivery shape.
- A controlled installed-Skill runtime with registry, active pointers, rollback, evidence bundles, marginal utility comparison, and bounded candidate evolution.
- `secure_code_review` is the first application lane.
- `software_patch_review` is an auxiliary software patch-review lane.

## What This Is Not

- Not a production vulnerability scanner.
- Not a full SPARK reproduction.
- Not a SWE-bench agent.
- Not an exploit automation tool.
- Not a production package manager.

## Current Evidence Boundary

The strongest evidence is controlled/internal and local defensive representative evidence:

- installed package runtime path
- task-conditioned secure review groups
- local defensive mini-suite
- small candidate evolution with rejected edits
- SWE-bench official harness readiness, currently allowed to remain infra-blocked

Do not use internal deterministic results to claim broad real-world security effectiveness.

## Start Here

See:

- `docs/QUICKSTART.md`
- `docs/RUNNING_VALIDATION.md`
- `docs/ADDING_A_NEW_SKILL.md`
- `docs/TROUBLESHOOTING.md`
- `docs/CLAIM_BOUNDARY.md`
- `docs/ARTIFACT_TYPES.md`
- `reports/REPRESENTATIVE_VALIDATION_MATRIX.md`
- `reports/RAPID_ADVANCEMENT_SPRINT_STATUS.md`

## Research-Grade Validation Lanes

The mature prototype evidence is expected to cover:

- holdout security cases that were not used for candidate generation tuning
- non-oracle local semantic backend attempts, with live LLM runs marked blocked if model/API configuration is unavailable
- task-conditioned activation ablation
- advanced candidate evolution with rejected buffers and staged promotion proposals only
- extended local defensive mini-suite evidence
- open-source readiness and review-package integrity checks

These lanes strengthen the prototype but do not turn it into a production scanner or official benchmark result.
