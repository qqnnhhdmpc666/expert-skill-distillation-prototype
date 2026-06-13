# Non-Oracle Local Agent Status

- Backend: `non_oracle_local_semantic`
- Scenarios: `5`
- A2 pass: `5/5`
- Families: `api_or_code_review, auth_access_control, config_security, data_quality_review, upload_security`
- Includes non-security family: `True`

| Scenario | Family | A1 Feedback | Repair | Gate | A2 | Artifact Dir |
|---|---|---|---|---|---:|---|
| api_review_001 | api_or_code_review | pass | no_op | accept_no_change | True | `runs\generalization\api_review_001` |
| auth_access_control_001 | auth_access_control | pass | no_op | accept_no_change | True | `runs\generalization\auth_access_control_001` |
| config_security_001 | config_security | pass | no_op | accept_no_change | True | `runs\generalization\config_security_001` |
| data_quality_review_001 | data_quality_review | pass | no_op | accept_no_change | True | `runs\generalization\data_quality_review_001` |
| upload_security_001 | upload_security | missing_capability | patch_capability | accept | True | `runs\generalization\upload_security_001` |

## Required Questions

1. Where can the non-oracle local agent produce target-grounded evidence? See per-scenario A1/A2 outputs under the artifact dirs; this backend now reads upload, auth, config, API-review, and one non-security data-quality target family.
2. Which tasks fail? `none in this smoke`.
3. Which tasks still exercise repair? `upload_security_001`.
4. Failure attribution: current failures should be treated as detector/target-observation gaps unless verifier output shows schema or regression errors.
5. Can feedback/repair catch failures? The same verifier report and repair policy path is used; failures are written instead of hidden.

## Boundary

This is a deterministic non-oracle local semantic backend. It reads target files and Skill packages and writes agent_output.json, trace.jsonl, stdout.log, and metadata. It is broader than the original upload/config smoke, but it is still not an LLM agent and not a Harbor sandbox agent.
