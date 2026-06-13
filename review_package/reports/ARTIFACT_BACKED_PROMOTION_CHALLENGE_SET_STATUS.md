# Artifact-Backed Promotion Challenge Set Status

Best on artifact-backed challenge set: `qgse_protocol`

| Mechanism | False promotion | False rejection | Scope errors | Risk score |
|---|---:|---:|---:|---:|
| reward_delta_only | 0 | 0 | 1 | 3 |
| gate_only | 5 | 0 | 1 | 28 |
| weighted_validity_score | 0 | 0 | 1 | 3 |
| pareto_conservative | 0 | 0 | 1 | 3 |
| qgse_protocol | 0 | 0 | 0 | 0 |
| qgse_pareto_protocol | 0 | 0 | 0 | 0 |

## Cases

- `harbor_llm_upload_repair_loop` expected `promote_scoped` from `outputs/harbor_llm_repair_loop_upload_001/summary.json`
- `live_llm_config_security_repair_loop` expected `quarantine` from `outputs/live_llm_repair_loop_config_security_001/summary.json`
- `live_llm_api_review_repair_loop` expected `reject` from `outputs/live_llm_repair_loop_api_review_001/summary.json`
- `agent_upload_clean_target` expected `quarantine` from `outputs/validation/agent_level_metamorphic_stress_001/cases/agent_upload_clean_target/agent/agent_output.json`
- `agent_config_clean_target` expected `quarantine` from `outputs/validation/agent_level_metamorphic_stress_001/cases/agent_config_clean_target/agent/agent_output.json`
- `agent_data_quality_row_shuffle` expected `quarantine` from `outputs/validation/agent_level_metamorphic_stress_001/cases/agent_data_quality_row_shuffle/agent/agent_output.json`
- `negative_control_robustness_support` expected `support_only` from `outputs/validation/negative_controls.json`
