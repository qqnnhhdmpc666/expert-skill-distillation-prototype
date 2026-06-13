# Mini-Suite Rerun Stability Status

Generated at: `2026-06-12T11:06:56.002253+00:00`
Rerun id: `20260612T110655960119Z`
Output root: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_security_mini_suite\rerun_stability\20260612T110655960119Z`

## Fresh Rerun Command

```powershell
python scripts\run_mini_suite_rerun_stability.py
```

## Results

| Case | Original status | Rerun status | Stable | Active group | FP count | Note |
|---|---|---|---:|---|---:|---|
| mini_upload_magic_path_001 | pass | pass | True | upload_security | 0 | ok |
| mini_config_prod_audit_001 | pass | pass | True | config_security | 0 | ok |
| mini_clean_out_of_scope_001 | false_positive_control_pass | false_positive_control_pass | True | out_of_scope_guard | 0 | ok |
| mini_dependency_version_risk_001 | unsupported_limitation | unsupported_limitation | True | out_of_scope_guard | 0 | ok |

## Decision

- Overall status: `pass`
- Clean negative false-positive control: `pass`
- Unsupported limitation retained: `retained`
