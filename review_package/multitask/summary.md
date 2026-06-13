# Multi-Task Closed Loop 001

## What This Run Answers

| Question | Answer | Evidence |
|---|---|---|
| Same pipeline across multiple tasks? | yes | 3 tasks across 3 task families |
| Different tasks trigger different feedback? | yes | evidence_gap, false_positive, missing_capability |
| Feedback becomes different repairs? | yes | add_environment_negative_guard, add_missing_capability_modules, strengthen_evidence_protocol |
| Repaired skills pass verification? | yes | A2 pass 3 / 3 |
| Processes recorded and reproducible? | yes | each case has inputs, attempts, verifier feedback, patch plan, skills, trajectory |

## Case Results

| Case | Family | A0 | A1 | Feedback | Patch | A2 | Coverage A0/A1/A2 |
|---|---|---:|---:|---|---|---:|---|
| upload_api_vulnerability | api_security | False | False | missing_capability | add_missing_capability_modules | True | 0.00/0.33/1.00 |
| auth_object_access | access_control | False | False | evidence_gap | strengthen_evidence_protocol | True | 0.00/1.00/1.00 |
| prod_config_audit | config_security | False | False | false_positive | add_environment_negative_guard | True | 0.00/1.00/1.00 |

## Reproducibility

Run:

```powershell
python scripts\run_multitask_closed_loop.py
```

The run is deterministic and does not require a model endpoint. It is designed as a verifier-backed system probe rather than a broad benchmark.

## Boundary

This proves the closed-loop mechanics across several realistic security-review task families. It does not yet prove open-world vulnerability discovery on arbitrary repositories.
