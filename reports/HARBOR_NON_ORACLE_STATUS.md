# Harbor Non-Oracle Status

## Summary

A real Harbor/Docker non-oracle baseline, a custom non-oracle heuristic solving attempt, a Harbor-in-the-loop heuristic A1/A2 repair loop, a live LLM-backed Harbor non-oracle upload run, a live LLM-backed Harbor upload A1/A2 repair loop, and a live LLM-backed Harbor config A1/A2 repair loop were completed.

| Run | Agent | Oracle | LLM | Reads Target | Reads Skill | Generates Report | Reward | Passed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `harbor_non_oracle_upload_001` | `nop` | false | false | false | false | false | 0.0 | false |
| `harbor_non_oracle_cli_upload_001` | `upload-security-heuristic-agent` | false | false | true | false | true | 1.0 | true |
| `harbor_non_oracle_repair_loop_upload_001/A1` | `upload-security-heuristic-agent` with restricted capability config | false | false | true | false | true | 0.0 | false |
| `harbor_non_oracle_repair_loop_upload_001/A2` | `upload-security-heuristic-agent` with repaired capability config | false | false | true | false | true | 1.0 | true |
| `harbor_llm_upload_001` | `upload-security-llm-agent` | false | true | true | true | true | 1.0 | true |
| `harbor_llm_repair_loop_upload_001/A1` | `upload-security-llm-agent` with generated v1 skill | false | true | true | true | true | 0.0 | false |
| `harbor_llm_repair_loop_upload_001/A2` | `upload-security-llm-agent` with generated v2 skill | false | true | true | true | true | 1.0 | true |
| `harbor_llm_repair_loop_config_001/A1` | `controlled-security-llm-agent` with weaker v1 contract | false | true | true | true | true | 0.0 | false |
| `harbor_llm_repair_loop_config_001/A2` | `controlled-security-llm-agent` with strict v2 contract | false | true | true | true | true | 1.0 | true |

## A1/A2 Repair Loop

The repair loop is the strongest current Harbor evidence because it does not only show a single successful run:

1. A1 entered Harbor/Docker, read `/app/target/app.py` and `/app/target/config.yaml`, and wrote `/app/security_report.json`.
2. A1 used a deliberately restricted capability config: `UPLOAD_PATH_ISOLATION`.
3. The Harbor verifier rejected A1 with missing capabilities: `UPLOAD_AUDIT_RETENTION`, `UPLOAD_TYPE_MAGIC`.
4. `A1/failure_feedback.json` was consumed by `revision/patch_plan.json` using `revision/repair_policy.json` action `patch_capability`.
5. A2 reran in Harbor with the repaired capability config and passed with reward `1.0`.

Primary artifacts:

- `outputs/harbor_non_oracle_repair_loop_upload_001/A1/security_report.json`
- `outputs/harbor_non_oracle_repair_loop_upload_001/A1/failure_feedback.json`
- `outputs/harbor_non_oracle_repair_loop_upload_001/revision/patch_plan.json`
- `outputs/harbor_non_oracle_repair_loop_upload_001/revision/gate_decision.json`
- `outputs/harbor_non_oracle_repair_loop_upload_001/A2/verifier_report.json`
- `outputs/harbor_non_oracle_repair_loop_upload_001/summary.md`

## Harbor LLM Upload Run

`outputs/harbor_llm_upload_001` is the first live LLM-backed Harbor non-oracle run:

1. `upload-security-llm-agent` ran inside the Harbor non-oracle path.
2. It read `/app/target/app.py`, `/app/target/config.yaml`, `/app/skill/SKILL.md`, and `/app/skill/manifest.json`.
3. It called an OpenAI-compatible endpoint using RightCode `gpt-5.5`.
4. It wrote `/app/security_report.json`.
5. The deterministic Harbor verifier returned reward `1.0`.

Primary artifacts:

- `outputs/harbor_llm_upload_001/prompt.md`
- `outputs/harbor_llm_upload_001/raw_response.txt`
- `outputs/harbor_llm_upload_001/security_report.json`
- `outputs/harbor_llm_upload_001/verifier_report.json`
- `outputs/harbor_llm_upload_001/model_calls.json`
- `outputs/harbor_llm_upload_001/backend_metadata.json`
- `outputs/harbor_llm_upload_001/summary.md`

## Harbor LLM A1/A2 Repair Loop

`outputs/harbor_llm_repair_loop_upload_001` closes the same failure -> feedback -> repair -> rerun loop inside Harbor with a live LLM agent:

1. A1 used a generated Harbor task copy whose `/app/skill` exposed only `UPLOAD_PATH_ISOLATION`.
2. The LLM agent read `/app/target/*` and `/app/skill/*`, wrote `/app/security_report.json`, and Harbor verifier returned reward `0.0`.
3. `A1/failure_feedback.json` recorded missing `UPLOAD_AUDIT_RETENTION` and `UPLOAD_TYPE_MAGIC`.
4. `revision/patch_plan.json` applied `missing_capability -> patch_capability`.
5. A2 used a second generated Harbor task copy whose `/app/skill` exposed all three upload capabilities.
6. The LLM agent reran in Harbor and verifier returned reward `1.0`.

Primary artifacts:

- `outputs/harbor_llm_repair_loop_upload_001/A1/verifier_report.json`
- `outputs/harbor_llm_repair_loop_upload_001/A1/target_reads.json`
- `outputs/harbor_llm_repair_loop_upload_001/A1/skill_manifest.json`
- `outputs/harbor_llm_repair_loop_upload_001/revision/patch_plan.json`
- `outputs/harbor_llm_repair_loop_upload_001/A2/verifier_report.json`
- `outputs/harbor_llm_repair_loop_upload_001/A2/skill_manifest.json`
- `outputs/harbor_llm_repair_loop_upload_001/summary.md`

## Harbor LLM Config A1/A2 Repair Loop

`outputs/harbor_llm_repair_loop_config_001` closes a second, different Harbor LLM loop:

1. A1 used the same config target and capability set as A2, but a weaker output contract.
2. The LLM agent read `/app/target/config.md` and `/app/skill/*`, wrote `/app/security_report.json`, and Harbor verifier returned reward `0.0`.
3. `A1/failure_feedback.json` recorded `output_contract_error` because `recommended_fix` was missing for all three findings.
4. `revision/patch_plan.json` applied `output_contract_error -> rewrite_output_contract`.
5. A2 reran in Harbor with the strict contract and passed with reward `1.0`.

Primary artifacts:

- `outputs/harbor_llm_repair_loop_config_001/A1/verifier_report.json`
- `outputs/harbor_llm_repair_loop_config_001/A1/raw_response.txt`
- `outputs/harbor_llm_repair_loop_config_001/A1/target_reads.json`
- `outputs/harbor_llm_repair_loop_config_001/revision/patch_plan.json`
- `outputs/harbor_llm_repair_loop_config_001/A2/verifier_report.json`
- `outputs/harbor_llm_repair_loop_config_001/summary.md`

## Harbor LLM Upload Repeatability

`outputs/validation/harbor_llm_repeatability_upload.json` records three upload-loop observations:

- A1 all fail: `true`
- A2 all pass: `true`
- reward stable: `0.0 -> 1.0`
- failure reason stable: missing `UPLOAD_AUDIT_RETENTION` and `UPLOAD_TYPE_MAGIC`

## Required Questions

1. Did it truly enter Harbor container execution?
   Yes. Harbor wrote job and trial results under both non-oracle output directories.

2. Did it read target files?
   `nop` did not. The custom heuristic agent did read `/app/target/app.py` and `/app/target/config.yaml`; see `outputs/harbor_non_oracle_cli_upload_001/target_reads.json`.

3. Did it generate a report?
   `nop` did not. The custom heuristic agent generated `/app/security_report.json`; see `outputs/harbor_non_oracle_cli_upload_001/security_report.json`.

4. What was verifier reward?
   `nop`: `0.0`. Custom heuristic agent: `1.0`.

5. Where did it fail?
   `nop` failed before producing the required security report. Repair-loop A1 failed because the report omitted two expected capabilities. The single-pass custom heuristic agent and repair-loop A2 passed this controlled upload task.

6. Can it form feedback?
   Yes. The `nop` failure is converted to `failure_feedback.json` with feedback type `missing_report`; repair-loop A1 is converted to `failure_feedback.json` with feedback type `missing_capability`.

## Boundary

This proves non-oracle Harbor execution, failure feedback plumbing, one controlled non-oracle heuristic solving attempt, one controlled Harbor heuristic A1/A2 repair loop, one live LLM-backed Harbor upload-security run, one live LLM-backed Harbor upload repair loop, one live LLM-backed Harbor config repair loop, and a small repeatability smoke on the upload loop. It does not prove broad Harbor LLM generalization, a general scanner, open-world vulnerability discovery, or full SPARK-PDI reproduction.
