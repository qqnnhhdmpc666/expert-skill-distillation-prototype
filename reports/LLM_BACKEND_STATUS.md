# LLM Backend Status

Updated: 2026-06-08 LLM-backed non-oracle pass.

## Summary

The project now has a real OpenAI-compatible non-oracle LLM agent path using RightCode `gpt-5.5`.

The local path is also less ad hoc than before: `scripts/run_live_llm_upload.py` now executes through `src/skill_deployment/runner.py::LiveLLMSecurityRunner`, and the local A1/A2 loop now emits `outputs/live_llm_repair_loop_upload_001/validity_card.json`.

Two local LLM runs, two Harbor/Docker LLM repair loops, and one small Harbor upload repeatability smoke were completed:

| Run | Environment | Agent | Reads Target | Reads Skill | Verifier | Result |
|---|---|---|---:|---:|---|---|
| `outputs/live_llm_upload_001` | local CLI | `agents/llm_security_agent.py` | yes | yes | deterministic local verifier | PASS |
| `outputs/live_llm_repair_loop_upload_001/A1` | local CLI | `agents/llm_security_agent.py` | yes | yes | deterministic local verifier | FAIL, missing two capabilities |
| `outputs/live_llm_repair_loop_upload_001/A2` | local CLI | `agents/llm_security_agent.py` | yes | yes | deterministic local verifier | PASS |
| `outputs/harbor_llm_upload_001` | WSL2/Docker/Harbor | `upload-security-llm-agent` | yes | yes | Harbor verifier | PASS, reward 1.0 |
| `outputs/harbor_llm_repair_loop_upload_001/A1` | WSL2/Docker/Harbor | `upload-security-llm-agent` | yes | yes | Harbor verifier | FAIL, missing two capabilities |
| `outputs/harbor_llm_repair_loop_upload_001/A2` | WSL2/Docker/Harbor | `upload-security-llm-agent` | yes | yes | Harbor verifier | PASS, reward 1.0 |
| `outputs/harbor_llm_repair_loop_config_001/A1` | WSL2/Docker/Harbor | `controlled-security-llm-agent` | yes | yes | Harbor verifier | FAIL, output contract missing `recommended_fix` |
| `outputs/harbor_llm_repair_loop_config_001/A2` | WSL2/Docker/Harbor | `controlled-security-llm-agent` | yes | yes | Harbor verifier | PASS, reward 1.0 |

## Local LLM Upload Smoke

`outputs/live_llm_upload_001`:

- Model: `gpt-5.5`
- Verifier pass: `true`
- Coverage: `1.0`
- Missing capabilities: `[]`
- Artifacts: `prompt.md`, `raw_response.txt`, `security_report.json`, `verifier_report.json`, `model_calls.json`, `backend_metadata.json`

## Local LLM Repair Loop

`outputs/live_llm_repair_loop_upload_001`:

- A1 Skill v1 exposed only `UPLOAD_PATH_ISOLATION`.
- A1 LLM output covered one finding and verifier returned `missing_capability`.
- Repair policy mapped `missing_capability -> patch_capability`.
- A2 Skill v2 exposed `UPLOAD_PATH_ISOLATION`, `UPLOAD_AUDIT_RETENTION`, and `UPLOAD_TYPE_MAGIC`.
- A2 verifier passed with coverage `1.0`.

## Harbor LLM Upload

`outputs/harbor_llm_upload_001`:

- Agent ran inside Harbor/Docker.
- Target reads: `/app/target/app.py`, `/app/target/config.yaml`.
- Skill reads: `/app/skill/SKILL.md`, `/app/skill/manifest.json`.
- The LLM generated `/app/security_report.json`.
- Harbor verifier returned reward `1.0` with no missing capabilities or schema errors.

## Harbor LLM Repair Loop

`outputs/harbor_llm_repair_loop_upload_001`:

- A1 used a generated Harbor task copy whose `/app/skill` exposed only `UPLOAD_PATH_ISOLATION`.
- A1 Harbor verifier returned reward `0.0` with missing `UPLOAD_AUDIT_RETENTION` and `UPLOAD_TYPE_MAGIC`.
- Repair policy mapped `missing_capability -> patch_capability`.
- A2 used a second generated Harbor task copy whose `/app/skill` exposed all three upload capabilities.
- A2 Harbor verifier returned reward `1.0`.
- `A1/target_reads.json` and `A2/target_reads.json` confirm the container read both `/app/target/*` and `/app/skill/*` in both attempts.

## Harbor LLM Config Repair Loop

`outputs/harbor_llm_repair_loop_config_001`:

- A1 used a generated Harbor task copy with a weaker output contract.
- The LLM agent still read `/app/target/config.md` and `/app/skill/*`, but omitted `recommended_fix` fields by following the weaker contract.
- Harbor verifier returned reward `0.0` with `output_contract_error`.
- `revision/patch_plan.json` applied `output_contract_error -> rewrite_output_contract`.
- A2 reran in Harbor with the same target and capability set, but a strict output contract.
- A2 Harbor verifier returned reward `1.0`.

This second task matters because it is not another missing-capability loop. It exercises a different verifier failure mode and a different repair action.

## Harbor Upload Repeatability Smoke

`outputs/validation/harbor_llm_repeatability_upload.json`:

- runs observed: `3`
- A1 all fail: `true`
- A2 all pass: `true`
- reward stable: `true`
- failure reason stable: `missing_capability`, missing `UPLOAD_AUDIT_RETENTION` and `UPLOAD_TYPE_MAGIC`

This is still small-sample evidence, but it reduces the chance that the Harbor upload repair loop was a one-off lucky run.

## Security / Secret Handling

- API key is injected via process/container environment.
- Artifacts record `api_key_present: true`, but do not store the key.
- `model_calls.json` records prompt/response and usage, not authorization headers.

## Boundary

This is now a real LLM-backed non-oracle path for one local upload task, one Harbor upload task, one Harbor config task, and a small Harbor upload repeatability smoke. It still does not prove broad Harbor LLM generalization, broad autonomous vulnerability discovery, or full SPARK-PDI reproduction. The LLM is the agent; deterministic verifier/gate remains the judge.
