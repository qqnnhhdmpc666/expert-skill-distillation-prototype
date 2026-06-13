# harbor_llm_upload_repair_loop

- Artifact: `outputs/harbor_llm_repair_loop_upload_001`
- Scope: Controlled repair loop for real-upload-security-review on backend harbor_llm_repair_upload_replay.
- Claim boundary: Controlled single-scenario Harbor LLM repair-loop evidence, not general Harbor LLM security capability.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | A1 pass=False, A2 pass=True, reward_delta=+1.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `missing_capability` triggered repair `patch_capability` and gate `accept`. |
| regression_safety | supported | After repair: missing=['none'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | Single Harbor upload slice only; cross-task transfer is evidenced separately and remains narrow. |
| repeatability | not_measured | Supported by the separate three-run upload repeatability smoke. |
| cost_budget | partially_supported | Prompt, response, usage, and Harbor job artifacts are stored, but no normalized cost table is computed here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['UPLOAD_AUDIT_RETENTION', 'UPLOAD_TYPE_MAGIC'], schema_errors=['none'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

## Summary

- Scenario: `real-upload-security-review`
- Backend: `harbor_llm_repair_upload_replay`
- A1 pass: `False`
- A2 pass: `True`
- Reward delta: `+1.0`
- Feedback type: `missing_capability`
- Repair action: `patch_capability`
- Gate decision: `accept`

- Sources: `outputs/harbor_llm_repair_loop_upload_001/A1/verifier_report.json`, `outputs/harbor_llm_repair_loop_upload_001/revision/patch_plan.json`, `outputs/harbor_llm_repair_loop_upload_001/revision/gate_decision.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/verifier_report.json`, `outputs/harbor_llm_repair_loop_upload_001/A1/security_report.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/security_report.json`, `outputs/harbor_llm_repair_loop_upload_001/A1/target_reads.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/target_reads.json`
