# harbor_llm_config_repair_loop

- Artifact: `outputs/harbor_llm_repair_loop_config_001`
- Scope: Controlled repair loop for controlled-config-security-review on backend harbor_llm_repair_config_replay.
- Claim boundary: Second-task Harbor LLM evidence, still controlled and narrow.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | A1 pass=False, A2 pass=True, reward_delta=+1.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `output_contract_error` triggered repair `rewrite_output_contract` and gate `accept`. |
| regression_safety | supported | After repair: missing=['none'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | Second distinct Harbor task family, but still narrow controlled evidence. |
| repeatability | not_measured | Not measured for this single loop artifact. |
| cost_budget | partially_supported | Harbor prompt/response/job artifacts exist, but no normalized cost table is computed here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['none'], schema_errors=['CONFIG_PROD_DEBUG missing recommended_fix', 'CONFIG_INSECURE_HTTP missing recommended_fix', 'CONFIG_HARDCODED_SECRET missing recommended_fix'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

## Summary

- Scenario: `controlled-config-security-review`
- Backend: `harbor_llm_repair_config_replay`
- A1 pass: `False`
- A2 pass: `True`
- Reward delta: `+1.0`
- Feedback type: `output_contract_error`
- Repair action: `rewrite_output_contract`
- Gate decision: `accept`

- Sources: `outputs/harbor_llm_repair_loop_config_001/A1/verifier_report.json`, `outputs/harbor_llm_repair_loop_config_001/revision/patch_plan.json`, `outputs/harbor_llm_repair_loop_config_001/revision/gate_decision.json`, `outputs/harbor_llm_repair_loop_config_001/A2/verifier_report.json`, `outputs/harbor_llm_repair_loop_config_001/A1/security_report.json`, `outputs/harbor_llm_repair_loop_config_001/A2/security_report.json`, `outputs/harbor_llm_repair_loop_config_001/A1/target_reads.json`, `outputs/harbor_llm_repair_loop_config_001/A2/target_reads.json`
