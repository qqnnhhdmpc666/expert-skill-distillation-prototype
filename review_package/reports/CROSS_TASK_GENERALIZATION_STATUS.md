# Cross-Task Generalization Status

Updated: 2026-06-08 next-phase hardening plus non-security transfer.

## Verdict

The prototype now has stronger controlled cross-task evidence. The generalization runner loads positive scenarios from `data/task_cases/<case>/` as source of truth, applies the same lifecycle, chooses repair actions through a typed operator registry in `src/skill_deployment/repair.py`, and writes comparable artifacts.

This is still controlled evidence, not open-world vulnerability-discovery proof.

## Results

```powershell
python scripts\validate_task_cases.py
python scripts\run_generalization_suite.py --scenarios upload,auth,config,api_review,data_quality --backend offline_deterministic
```

| Scenario | Family | A1 Feedback | Repair Action | Gate | A2 |
|---|---|---|---|---|---|
| `upload_security_001` | upload_security | missing_capability | patch_capability | accept | PASS |
| `auth_access_control_001` | auth_access_control | ownership_boundary_missing | patch_boundary | accept | PASS |
| `config_security_001` | config_security | false_positive_risk | reduce_false_positive_risk | accept | PASS |
| `api_review_001` | api_or_code_review | output_contract_error | rewrite_output_contract | accept | PASS |
| `data_quality_review_001` | data_quality_review | target_context_missing | add_observation_step | accept | PASS |

## Answers

- Same pipeline across tasks: yes, implemented in `scripts/run_generalization_suite.py`.
- Scenario source of truth: `data/task_cases/<case>/`.
- Shared repair layer: `src/skill_deployment/repair.py` now selects typed repair operators instead of keeping repair dispatch inline inside the suite script.
- Negative controls: stored in `data/task_cases/` with `negative_control: true` and excluded from positive A2 pass counting.
- Feedback to repair: verifier feedback type -> `revision/repair_policy.json` -> repair action.
- Not merely skin-changing: feedback/repair/verifier surfaces differ per task, and the fifth task is a non-security `data_quality_review` family.
- Generic modules: task schema loader, skill package layout, attempt contract, verifier report, repair dispatch, gate, trace writer, summary export.
- Task-specific inputs: expert material, target asset, expected capability set, v1 compact capability set, verifier contract.
- Evidence strength: stronger controlled multi-task evidence, not large-scale proof.

## Remaining Gap

The attempt generator is still deterministic and task-conditioned. The next step is connecting a non-oracle semantic/LLM/CLI agent path to multiple task families, including at least one non-security family.
