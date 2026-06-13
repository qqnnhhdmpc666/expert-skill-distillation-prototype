# Implementation Brief

## What The Prototype Does

The system runs a controlled Skill Package lifecycle:

```text
task case -> capability extraction -> Skill v1 -> A0/A1 -> verifier feedback -> typed repair -> gate -> Skill v2 -> A2 -> reports/traces
```

## Current Core Commands

```powershell
python scripts\validate_task_cases.py
python scripts\run_generalization_suite.py --scenarios upload,auth,config,api_review --backend offline_deterministic
python scripts\run_ablation_suite.py
python scripts\run_system_acceptance.py
```

## Key Design Choices

- Use capabilities rather than exposing internal rule IDs to the user.
- Keep verifier and gate deterministic for reproducibility.
- Allow LLM text generation only as candidate/interpretation input unless explicitly in live backend.
- Use typed feedback to choose repair action.
- Keep every claim linked to an artifact.

## Current Limits

- Controlled task suite, not open-world benchmark.
- WSL Harbor task uses oracle agent.
- Live LLM backend depends on environment variables and is not required for stable acceptance.
