# Defensive Security Mini-Suite Status

Run id: `defensive_security_mini_suite_installed_runtime`
Generated at: `2026-06-12T10:24:50.481475+00:00`

## Claim Boundary

This is a local AutoPatchBench-style defensive approximation. It is not an official AutoPatchBench, CyberSecEval, or CVE-Bench run.
It uses installed Skill packages and records fresh runtime evidence, but it does not prove real-world vulnerability scanning effectiveness.

## Version Integrity

- `version_content_identical`: `False`
- `v1`: skill_hash=`9f498c16c81acf64979cfbce106c7615875cbb357441acc83124a1b2811858ca`, manifest_hash=`a11d823e0aca5a800b13ccd7d9a6d692922ffba487e0de02da926122303f7701`
- `v2`: skill_hash=`8e83be948f84f564e80b7f5554605e742ae17879088ef904337f11884b56d8d6`, manifest_hash=`1349cc35c9a1ad4b391c18ac4aaf4da85440cb0d2ba730c0eed50b97e50c5de8`

## Case Results

| Case | Task family | Status | Active group | Expected group | Group correct | FP count |
|---|---|---|---|---|---:|---:|
| mini_upload_magic_path_001 | upload_security | pass | upload_security | upload_security | True | 0 |
| mini_upload_public_storage_002 | upload_security | pass | upload_security | upload_security | True | 0 |
| mini_config_prod_audit_001 | config_security | pass | config_security | config_security | True | 0 |
| mini_config_env_guard_002 | config_security | pass | config_security | config_security | True | 0 |
| mini_auth_invoice_scope_001 | auth_access_control | pass | auth_access_control | auth_access_control | True | 0 |
| mini_auth_owner_boundary_002 | auth_access_control | pass | auth_access_control | auth_access_control | True | 0 |
| mini_api_schema_grounding_001 | api_or_code_review | pass | api_or_code_review | api_or_code_review | True | 0 |
| mini_dependency_version_risk_001 | dependency_version_risk | unsupported_limitation | out_of_scope_guard | out_of_scope_guard | True | 0 |
| mini_clean_out_of_scope_001 | clean_business_logic_review | false_positive_control_pass | out_of_scope_guard | out_of_scope_guard | True | 0 |

## Summary

- Fresh case count: `9`
- Positive security effective pass count: `7`
- False-positive control status: `pass`
- Unsupported limitation status: `retained`
- Package-level marginal utility artifact: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_security_mini_suite\package_marginal_utility.json`

## Oracle Leakage Guard

Runner inputs are built from agent-visible fields only. Verifier-only expected findings, evidence spans, capability groups, and clean labels are used only after execution.
