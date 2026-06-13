# Backend Maturity Status

Updated: 2026-06-08 next-phase hardening.

| Backend | Status | Evidence | Boundary |
|---|---|---|---|
| `offline_deterministic` | available, now includes one non-security family | `scripts/run_generalization_suite.py`, `src/skill_deployment/repair.py`, `outputs/validation/generalization_suite.json` | Controlled deterministic agent/verifier/compiler with typed repair operator selection; now covers 4 security-style tasks plus 1 non-security data-quality task. |
| `live_llm_text` | local upload run, upload A1/A2 loop, and one non-security data-quality A1/A2 loop passed; now under shared local runner | `agents/llm_security_agent.py`, `src/skill_deployment/runner.py`, `scripts/run_live_llm_upload.py`, `outputs/live_llm_upload_001/summary.md`, `outputs/live_llm_repair_loop_upload_001/summary.md`, `outputs/live_llm_repair_loop_data_quality_001/summary.md` | RightCode `gpt-5.5` generated controlled reports; verifier/gate remain deterministic; local evidence is still narrow and not broad multi-domain generalization. |
| `harbor_replay_adapter` | minimal read-existing adapter available | `src/skill_deployment/harbor_adapter.py`, `src/skill_deployment/runner.py`, `scripts/run_harbor_replay_summary.py`, `outputs/harbor_llm_repair_loop_upload_001/`, `outputs/harbor_llm_repair_loop_config_001/` | Reads existing Harbor repair-loop artifacts through `BackendRunner`; does not rerun Harbor or unify live Harbor execution. |
| `local_real_agent` | available smoke | `agents/local_security_review_agent.py`, `runs/local_agent_smoke/` | Reads target/skill from disk and writes output/trace/stdout/metadata, but output is capability-driven. |
| `non_oracle_local_semantic_agent` | five-family suite passed | `outputs/validation/non_oracle_local_suite.json`, `src/skill_deployment/capability_registry.py` | Reads target and skill, extracts evidence with deterministic heuristics across upload/auth/config/API-review/data-quality; not LLM and not Harbor. |
| `sandbox_agent` | live LLM upload pass plus two Harbor LLM repair loops | `outputs/wsl_harbor_real_upload_001/summary.md`, `outputs/harbor_non_oracle_upload_001/summary.md`, `outputs/harbor_non_oracle_cli_upload_001/summary.md`, `outputs/harbor_non_oracle_repair_loop_upload_001/summary.md`, `outputs/harbor_llm_upload_001/summary.md`, `outputs/harbor_llm_repair_loop_upload_001/summary.md`, `outputs/harbor_llm_repair_loop_config_001/summary.md`, `outputs/validation/harbor_llm_repeatability_upload.json` | Oracle task passes; non-oracle `nop` baseline fails; heuristic repair loop passes; live LLM agent reads target/skill in Harbor, passes one upload task, completes one upload A1/A2 repair loop, completes one config contract-repair loop, and shows small upload repeatability evidence. |

## What Comes From Page vs Scripts

- Page display: `demo/streamlit_app.py`.
- Command-line core evidence: `scripts/run_generalization_suite.py`, `scripts/run_ablation_suite.py`, `scripts/run_non_oracle_local_agent_smoke.py`, `scripts/run_live_llm_upload.py`, `scripts/run_system_acceptance.py`.
- Local deterministic runner artifact: `runs/local_agent_smoke/agent_output.json`, `trace.jsonl`, `stdout.log`, `backend_metadata.json`.
- Non-oracle local semantic artifacts: `outputs/validation/non_oracle_local_suite.json`, `outputs/non_oracle_local_agent_upload_001/`, `runs/generalization/data_quality_review_001/`.
- LLM artifacts: `outputs/live_llm_upload_001/`, `outputs/live_llm_repair_loop_upload_001/`, `outputs/live_llm_repair_loop_data_quality_001/`.
- Sandbox artifacts: `outputs/wsl_harbor_real_upload_001/`, `outputs/harbor_non_oracle_upload_001/`, `outputs/harbor_non_oracle_cli_upload_001/`, `outputs/harbor_non_oracle_repair_loop_upload_001/`, `outputs/harbor_llm_upload_001/`, `outputs/harbor_llm_repair_loop_upload_001/`, `outputs/harbor_llm_repair_loop_config_001/`, `outputs/validation/harbor_llm_repeatability_upload.json`.

## Current Real-Execution Boundary

The project now has seven non-UI execution paths: local file-IO runner, non-oracle local semantic suite, local live LLM upload loop, WSL2/Docker/Harbor oracle task, WSL2/Docker/Harbor non-oracle `nop` baseline, WSL2/Docker/Harbor non-oracle heuristic repair loop, and WSL2/Docker/Harbor live LLM upload plus two repair-loop runs. The shared offline suite now covers one non-security task family, and the local semantic backend now reads all five controlled task families through the same capability registry. It still does not prove broad Harbor vulnerability-task generalization.
