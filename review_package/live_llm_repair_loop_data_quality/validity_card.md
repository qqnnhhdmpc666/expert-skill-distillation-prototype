# live_llm_data_quality_repair_loop_validity_card

- Artifact: `outputs/live_llm_repair_loop_data_quality_001`
- Scope: Controlled repair loop for data_quality_review_001 on backend live_llm_text.
- Claim boundary: Single local live-LLM repair-loop evidence on one controlled non-security data-quality task; verifier and gate remain deterministic.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | A1 pass=False, A2 pass=True, reward_delta=+1.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `output_contract_error` triggered repair `rewrite_output_contract` and gate `accept`. |
| regression_safety | supported | After repair: missing=['none'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | One controlled non-security slice only; not broad multi-domain generalization. |
| repeatability | not_measured | Not measured for this single loop artifact. |
| cost_budget | partially_supported | Latency and token usage are available in backend metadata/model_calls but not normalized here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['none'], schema_errors=['DATA_REQUIRED_FIELD_COVERAGE.recommended_fix', 'DATA_TEMPORAL_SPLIT_GUARD.recommended_fix', 'DATA_LABEL_ENUM_ALIGNMENT.recommended_fix'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

## Summary

- Scenario: `data_quality_review_001`
- Backend: `live_llm_text`
- A1 pass: `False`
- A2 pass: `True`
- Reward delta: `+1.0`
- Feedback type: `output_contract_error`
- Repair action: `rewrite_output_contract`
- Gate decision: `accept`

- Sources: `outputs/live_llm_repair_loop_data_quality_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_data_quality_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_data_quality_001/revision/gate_decision.json`, `outputs/live_llm_repair_loop_data_quality_001/A2/verifier_report.json`, `outputs/live_llm_repair_loop_data_quality_001/A1/security_report.json`, `outputs/live_llm_repair_loop_data_quality_001/A2/security_report.json`
