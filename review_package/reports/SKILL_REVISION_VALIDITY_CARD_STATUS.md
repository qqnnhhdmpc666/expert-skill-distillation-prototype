# Skill Revision Validity Card Status

Generated: 2026-06-09T06:34:16.339837+00:00

This file does not collapse everything into one score. It records which parts of the current evidence are genuinely supported, only partially supported, not measured, or still waiting on human review.

## live_llm_upload_repair_loop

- Artifact: `outputs/live_llm_repair_loop_upload_001`
- Scope: Controlled repair loop for upload_security_001 on backend live_llm_text.
- Claim boundary: Single local live-LLM repair-loop evidence on one controlled upload task; verifier and gate remain deterministic.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | A1 pass=False, A2 pass=True, reward_delta=+1.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `missing_capability` triggered repair `patch_capability` and gate `accept`. |
| regression_safety | supported | After repair: missing=['none'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | Single controlled security slice only. |
| repeatability | not_measured | Not measured for this single loop artifact. |
| cost_budget | partially_supported | Latency and token usage are available in backend metadata/model_calls but not normalized here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['UPLOAD_AUDIT_RETENTION', 'UPLOAD_TYPE_MAGIC'], schema_errors=['none'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

- Sources: `outputs/live_llm_repair_loop_upload_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_upload_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_upload_001/revision/gate_decision.json`, `outputs/live_llm_repair_loop_upload_001/A2/verifier_report.json`, `outputs/live_llm_repair_loop_upload_001/A1/security_report.json`, `outputs/live_llm_repair_loop_upload_001/A2/security_report.json`

## live_llm_data_quality_repair_loop

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

- Sources: `outputs/live_llm_repair_loop_data_quality_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_data_quality_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_data_quality_001/revision/gate_decision.json`, `outputs/live_llm_repair_loop_data_quality_001/A2/verifier_report.json`, `outputs/live_llm_repair_loop_data_quality_001/A1/security_report.json`, `outputs/live_llm_repair_loop_data_quality_001/A2/security_report.json`

## live_llm_config_security_repair_loop

- Artifact: `outputs/live_llm_repair_loop_config_security_001`
- Scope: Controlled repair loop for config_security_001 on backend live_llm_text.
- Claim boundary: Single local live-LLM repair-loop evidence on one controlled configuration-security task; verifier and gate remain deterministic.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | partially_supported | A1 pass=False, A2 pass=False, reward_delta=+0.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `missing_capability` triggered repair `patch_capability` and gate `accept`. |
| regression_safety | partially_supported | After repair: missing=['CONFIG_ENV_GUARD'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | Second local controlled security slice only; not broad live-LLM security-task generalization. |
| repeatability | not_measured | Not measured for this single loop artifact. |
| cost_budget | partially_supported | Latency and token usage are available in backend metadata/model_calls but not normalized here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['CONFIG_ENV_GUARD'], schema_errors=['none'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

- Sources: `outputs/live_llm_repair_loop_config_security_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_config_security_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_config_security_001/revision/gate_decision.json`, `outputs/live_llm_repair_loop_config_security_001/A2/verifier_report.json`, `outputs/live_llm_repair_loop_config_security_001/A1/security_report.json`, `outputs/live_llm_repair_loop_config_security_001/A2/security_report.json`

## live_llm_api_review_repair_loop

- Artifact: `outputs/live_llm_repair_loop_api_review_001`
- Scope: Controlled repair loop for api_review_001 on backend live_llm_text.
- Claim boundary: Single local live-LLM repair-loop evidence on one controlled API/code-review task; verifier and gate remain deterministic.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | partially_supported | A1 pass=False, A2 pass=False, reward_delta=+0.0. |
| evidence_grounding | supported | Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them. |
| repair_attribution | supported | A1 feedback `missing_capability` triggered repair `patch_capability` and gate `accept`. |
| regression_safety | partially_supported | After repair: missing=['API_OVERBROAD_RISK'], schema_errors=['none'], weak_evidence=['none']. |
| transferability | partially_supported | Third local controlled slice only; not broad live-LLM task generalization. |
| repeatability | not_measured | Not measured for this single loop artifact. |
| cost_budget | partially_supported | Latency and token usage are available in backend metadata/model_calls but not normalized here. |
| verifier_robustness | partially_supported | Verifier distinguished A1 vs A2; before repair missing=['API_OVERBROAD_RISK'], schema_errors=['API_SCHEMA_CONTRACT.recommended_fix'], weak_evidence=['none']. |
| human_plausibility | manual_review_pending | No human usefulness review is attached to this loop artifact. |

- Sources: `outputs/live_llm_repair_loop_api_review_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_api_review_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_api_review_001/revision/gate_decision.json`, `outputs/live_llm_repair_loop_api_review_001/A2/verifier_report.json`, `outputs/live_llm_repair_loop_api_review_001/A1/security_report.json`, `outputs/live_llm_repair_loop_api_review_001/A2/security_report.json`

## offline_generalization_suite

- Artifact: `outputs/validation/generalization_suite.json`
- Scope: Five controlled task families through one offline_deterministic lifecycle.
- Claim boundary: Strong controlled lifecycle evidence, not open-world semantic quality evidence.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | A2 passes 5/5 controlled tasks. |
| evidence_grounding | partially_supported | Verifier checks evidence fields, but the offline agent path still emits deterministic capability/evidence hints rather than target-grounded reads. |
| repair_attribution | supported | Each scenario records A1 feedback type and a distinct repair action before A2. |
| regression_safety | partially_supported | Regression is measured by verifier score and strengthened by separate negative controls, not by a broad held-out clean-target suite. |
| transferability | supported | The same offline suite spans upload, auth, config, API review, and one non-security data-quality task. |
| repeatability | supported | The offline path is deterministic and artifact-backed; reruns should be stable modulo timestamps. |
| cost_budget | partially_supported | Per-scenario summaries include latency; cost_budget_score is synthetic rather than measured from real model/token usage. |
| verifier_robustness | partially_supported | Robustness is supported only indirectly here; explicit unsupported-evidence/false-positive checks live in negative_controls.json. |
| human_plausibility | manual_review_pending | No systematic human rating is stored for whether A2 reports are materially more useful than A1. |

- Sources: `outputs/validation/generalization_suite.json`, `runs/generalization/*/verifier/A1_report.json`, `runs/generalization/*/revision/repair_decision.json`

## non_oracle_local_semantic_suite

- Artifact: `outputs/validation/non_oracle_local_suite.json`
- Scope: Deterministic non-oracle local semantic backend over five controlled task families.
- Claim boundary: Backend-interface and target-grounding evidence, not proof of autonomous semantic reasoning.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | partially_supported | A2 passes 5/5, but only upload shows a repair loop; four tasks already pass at A1. |
| evidence_grounding | supported | The backend reads target text, emits trace.jsonl read events, and grounds findings with detector hits. |
| repair_attribution | partially_supported | Only upload currently demonstrates verifier-triggered capability repair on this backend. |
| regression_safety | partially_supported | No dedicated clean-target local-semantic regression suite is stored yet. |
| transferability | partially_supported | The interface spans five families, but feedback diversity is low: only pass/no_op and one missing_capability case. |
| repeatability | supported | This path is deterministic heuristic code with stable target reads. |
| cost_budget | supported | Latency is small and there is no external token cost. |
| verifier_robustness | partially_supported | Verifier remains deterministic; robustness against semantic-but-wrong heuristics is only lightly tested. |
| human_plausibility | manual_review_pending | No manual review card exists for whether the heuristic reports are meaningfully useful beyond contract compliance. |

- Sources: `outputs/validation/non_oracle_local_suite.json`, `agents/non_oracle_local_security_agent.py`

## negative_controls

- Artifact: `outputs/validation/negative_controls.json`
- Scope: Controlled checks for unsupported evidence and false-positive rejection.
- Claim boundary: Narrow robustness evidence for two adversarial patterns, not a broad adversarial verification benchmark.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | not_measured | This slice is about verifier refusal behavior, not task improvement. |
| evidence_grounding | supported | Unsupported evidence is explicitly rejected when evidence_span is absent from the target. |
| repair_attribution | partially_supported | The clean-config control demonstrates gate behavior after a false-positive style repair, but not a full A1/A2 loop. |
| regression_safety | supported | Always-append findings are rejected on a clean config; empty typed output can pass when expected issue set is empty. |
| transferability | partially_supported | Only two negative controls exist so far. |
| repeatability | supported | These controls are deterministic and should be exactly reproducible. |
| cost_budget | supported | No external model cost is involved. |
| verifier_robustness | supported | This is the strongest direct evidence that verifier/gate can reject unsupported evidence and false positives. |
| human_plausibility | manual_review_pending | No human audit artifacts accompany the negative controls. |

- Sources: `outputs/validation/negative_controls.json`

## ablation_summary

- Artifact: `outputs/validation/ablation_summary.json`
- Scope: Controlled strategy comparison across upload and config tasks.
- Claim boundary: Useful controlled attribution evidence, not a benchmark-scale ablation.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | Typed repair plus gate reaches PASS on both scenarios; naive strategies fail or incur regressions on config. |
| evidence_grounding | partially_supported | Ablation reuses the same controlled verifier path; it does not independently validate semantic grounding. |
| repair_attribution | supported | Different repair choices produce measurably different outcomes under the same inputs. |
| regression_safety | supported | Always-append and naive-regenerate show regression_count > 0 on config; gate rejects those paths. |
| transferability | partially_supported | Only two scenarios are included in the executable ablation. |
| repeatability | supported | The ablation is deterministic. |
| cost_budget | partially_supported | Synthetic cost_budget_score differentiates strategies, but it is not calibrated to true runtime or token spend. |
| verifier_robustness | partially_supported | The verifier distinguishes regressions here, but broader adversarial checks remain outside this table. |
| human_plausibility | manual_review_pending | No human comparison of strategy outputs is recorded. |

- Sources: `outputs/validation/ablation_summary.json`

## harbor_llm_upload_repair_loop

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

- Sources: `outputs/harbor_llm_repair_loop_upload_001/A1/verifier_report.json`, `outputs/harbor_llm_repair_loop_upload_001/revision/patch_plan.json`, `outputs/harbor_llm_repair_loop_upload_001/revision/gate_decision.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/verifier_report.json`, `outputs/harbor_llm_repair_loop_upload_001/A1/security_report.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/security_report.json`, `outputs/harbor_llm_repair_loop_upload_001/A1/target_reads.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/target_reads.json`

## harbor_llm_config_repair_loop

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

- Sources: `outputs/harbor_llm_repair_loop_config_001/A1/verifier_report.json`, `outputs/harbor_llm_repair_loop_config_001/revision/patch_plan.json`, `outputs/harbor_llm_repair_loop_config_001/revision/gate_decision.json`, `outputs/harbor_llm_repair_loop_config_001/A2/verifier_report.json`, `outputs/harbor_llm_repair_loop_config_001/A1/security_report.json`, `outputs/harbor_llm_repair_loop_config_001/A2/security_report.json`, `outputs/harbor_llm_repair_loop_config_001/A1/target_reads.json`, `outputs/harbor_llm_repair_loop_config_001/A2/target_reads.json`

## harbor_llm_upload_repeatability

- Artifact: `outputs/validation/harbor_llm_repeatability_upload.json`
- Scope: Three-run repeatability smoke for the Harbor upload LLM repair loop.
- Claim boundary: Small repeatability smoke for one Harbor upload loop, not a broad prompt-sensitivity study.

| Dimension | Status | Note |
|---|---|---|
| outcome_delta | supported | All three runs show A1 fail and A2 pass with reward delta +1.0. |
| evidence_grounding | partially_supported | Repeatability summarizes verifier outcomes and model usage; grounding remains delegated to the underlying run artifacts. |
| repair_attribution | supported | Failure reason and missing-capability set are stable across repeats. |
| regression_safety | partially_supported | This slice checks stability of the same loop, not regression on unrelated clean tasks. |
| transferability | not_measured | Repeatability is measured only on upload. |
| repeatability | supported | A1 all fail, A2 all pass, reward stable, failure reason stable across three runs. |
| cost_budget | supported | average total tokens per loop=2191.33, average combined latency ms per loop=24702.33 |
| verifier_robustness | partially_supported | Stable failure types reduce the chance of arbitrary verifier drift, but do not exhaust robustness concerns. |
| human_plausibility | manual_review_pending | No repeated human evaluation accompanies the loop repeats. |

- Sources: `outputs/validation/harbor_llm_repeatability_upload.json`

