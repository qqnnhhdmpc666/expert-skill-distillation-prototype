# live_llm_config_security_repair_loop_validity_card

- Artifact: `outputs/live_llm_repair_loop_config_security_001`
- Scope: Controlled repair loop for config_security_001 on backend live_llm_text.
- Claim boundary: Single local live-LLM repair-loop evidence on one controlled configuration-security task; verifier and gate remain deterministic.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | partially_supported | A1 pass=False, A2 pass=False, reward_delta=+0.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `missing_capability` triggered repair `patch_capability` and gate `accept`. |
| regression_safety | partially_supported | After repair: missing=['CONFIG_ENV_GUARD'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | Second local controlled security slice only; not broad multi-task live-LLM generalization. |
| repeatability | not_measured | Not measured for this single loop artifact. |
| cost_budget | partially_supported | Latency and token usage are available in backend metadata/model_calls but not normalized here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['CONFIG_ENV_GUARD'], schema_errors=['none'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

## Summary

- Scenario: `config_security_001`
- Backend: `live_llm_text`
- A1 pass: `False`
- A2 pass: `False`
- Reward delta: `+0.0`
- Feedback type: `missing_capability`
- Repair action: `patch_capability`
- Gate decision: `accept`

- Sources: `outputs/live_llm_repair_loop_config_security_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_config_security_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_config_security_001/revision/gate_decision.json`, `outputs/live_llm_repair_loop_config_security_001/A2/verifier_report.json`, `outputs/live_llm_repair_loop_config_security_001/A1/security_report.json`, `outputs/live_llm_repair_loop_config_security_001/A2/security_report.json`
