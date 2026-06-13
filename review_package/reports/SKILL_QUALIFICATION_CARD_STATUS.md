# Skill Qualification Card Status

Generated: 2026-06-11T11:25:53.257168+00:00

Method: Qualification-Guided Skill Evolution

Principle: feedback proposes revision; qualification decides promotion

These cards do not replace verifier reports. They decide whether a revised Skill can be promoted, quarantined, or rejected after verifier feedback has proposed a repair.

| Card | Type | Decision | Level/Support | Integrity | Behavior | Robustness |
|---|---|---|---|---|---|---|
| live_llm_upload_repair_loop | RevisionQualificationCard | promote_with_scope_limit | L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT | pass | pass | partial |
| live_llm_data_quality_repair_loop | RevisionQualificationCard | promote_with_scope_limit | L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT | pass | pass | partial |
| live_llm_config_security_repair_loop | RevisionQualificationCard | quarantine | L0_NON_PROMOTABLE | pass | fail | not_measured |
| live_llm_api_review_repair_loop | RevisionQualificationCard | reject | L0_NON_PROMOTABLE | fail | fail | not_measured |
| harbor_llm_upload_repair_loop | RevisionQualificationCard | promote_with_scope_limit | L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT | pass | pass | pass |
| harbor_llm_config_repair_loop | RevisionQualificationCard | promote_with_scope_limit | L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT | pass | pass | partial |
| offline_generalization_qualification_support | EvidenceSupportCard | supporting_evidence | supports_L3_PROMOTE_CONTROLLED | pass | partial | partial |
| negative_control_robustness_support | EvidenceSupportCard | supporting_evidence | supports_L3_PROMOTE_CONTROLLED | pass | partial | partial |
| harbor_upload_repeatability_support | EvidenceSupportCard | supporting_evidence | supports_L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT | pass | partial | partial |

## live_llm_upload_repair_loop

- Card type: `RevisionQualificationCard`
- Artifact: `outputs/live_llm_repair_loop_upload_001`
- Decision: `promote_with_scope_limit`
- Level/support: `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT`
- Claim scope: Controlled local repair-loop evidence for upload_security_001 only; no broad local LLM/general task generalization.

- integrity_gate: `pass`. A1 missing capabilities are represented in the revised capability manifest.
- behavior_gate: `pass`. A2 passes the deterministic verifier after the revision.
- robustness_gate: `partial`. The loop passes locally, but sandbox/holdout/metamorphic evidence is not attached.

Next required evidence:
- Run the same loop in Harbor/Docker or a comparable sandbox.
- Add negative, swapped-target, fake-evidence, and metamorphic controls.
- Attach human or external review before broad deployment claims.

Sources: `outputs/live_llm_repair_loop_upload_001/summary.json`, `outputs/live_llm_repair_loop_upload_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_upload_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_upload_001/A2/verifier_report.json`

## live_llm_data_quality_repair_loop

- Card type: `RevisionQualificationCard`
- Artifact: `outputs/live_llm_repair_loop_data_quality_001`
- Decision: `promote_with_scope_limit`
- Level/support: `L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT`
- Claim scope: Controlled local repair-loop evidence for data_quality_review_001 only; no broad local LLM/general task generalization.

- integrity_gate: `pass`. The contract repair removed A1 schema errors under an accepted gate decision.
- behavior_gate: `pass`. A2 passes the deterministic verifier after the revision.
- robustness_gate: `partial`. The loop passes locally, but sandbox/holdout/metamorphic evidence is not attached.

Next required evidence:
- Run the same loop in Harbor/Docker or a comparable sandbox.
- Add negative, swapped-target, fake-evidence, and metamorphic controls.
- Attach human or external review before broad deployment claims.

Sources: `outputs/live_llm_repair_loop_data_quality_001/summary.json`, `outputs/live_llm_repair_loop_data_quality_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_data_quality_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_data_quality_001/A2/verifier_report.json`

## live_llm_config_security_repair_loop

- Card type: `RevisionQualificationCard`
- Artifact: `outputs/live_llm_repair_loop_config_security_001`
- Decision: `quarantine`
- Level/support: `L0_NON_PROMOTABLE`
- Claim scope: Controlled local repair-loop evidence for config_security_001 only; no broad local LLM/general task generalization.

- integrity_gate: `pass`. A1 missing capabilities are represented in the revised capability manifest.
- behavior_gate: `fail`. A2 still misses the same capability set: ['CONFIG_ENV_GUARD']. Failure origin: `skill_to_execution_gap`.
- robustness_gate: `not_measured`. Robustness is not meaningful until behavior improvement is demonstrated.

Next required evidence:
- Diagnose why the agent did not express the revised Skill in A2 output.

Sources: `outputs/live_llm_repair_loop_config_security_001/summary.json`, `outputs/live_llm_repair_loop_config_security_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_config_security_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_config_security_001/A2/verifier_report.json`

## live_llm_api_review_repair_loop

- Card type: `RevisionQualificationCard`
- Artifact: `outputs/live_llm_repair_loop_api_review_001`
- Decision: `reject`
- Level/support: `L0_NON_PROMOTABLE`
- Claim scope: Controlled local repair-loop evidence for api_review_001 only; no broad local LLM/general task generalization.

- integrity_gate: `fail`. patch_capability was selected, but the capability manifest did not add a new capability. Failure origin: `repair_operator_noop_or_patch_application_failure`.
- behavior_gate: `fail`. A2 still misses the same capability set: ['API_OVERBROAD_RISK']. Failure origin: `skill_to_execution_gap`.
- robustness_gate: `not_measured`. Robustness is not meaningful until behavior improvement is demonstrated.

Next required evidence:
- Fix repair integrity before collecting more outcome evidence.

Sources: `outputs/live_llm_repair_loop_api_review_001/summary.json`, `outputs/live_llm_repair_loop_api_review_001/A1/verifier_report.json`, `outputs/live_llm_repair_loop_api_review_001/revision/patch_plan.json`, `outputs/live_llm_repair_loop_api_review_001/A2/verifier_report.json`

## harbor_llm_upload_repair_loop

- Card type: `RevisionQualificationCard`
- Artifact: `outputs/harbor_llm_repair_loop_upload_001`
- Decision: `promote_with_scope_limit`
- Level/support: `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`
- Claim scope: Controlled sandboxed repair-loop evidence for real-upload-security-review only; no broad Harbor/backend generalization.

- integrity_gate: `pass`. A1 missing capabilities are represented in the revised capability manifest.
- behavior_gate: `pass`. A2 passes the deterministic verifier after the revision.
- robustness_gate: `pass`. A small repeatability smoke and negative controls exist for this slice.

Next required evidence:
- Attach human or external review before broad deployment claims.

Sources: `outputs/harbor_llm_repair_loop_upload_001/summary.json`, `outputs/harbor_llm_repair_loop_upload_001/A1/verifier_report.json`, `outputs/harbor_llm_repair_loop_upload_001/revision/patch_plan.json`, `outputs/harbor_llm_repair_loop_upload_001/A2/verifier_report.json`

## harbor_llm_config_repair_loop

- Card type: `RevisionQualificationCard`
- Artifact: `outputs/harbor_llm_repair_loop_config_001`
- Decision: `promote_with_scope_limit`
- Level/support: `L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`
- Claim scope: Controlled sandboxed repair-loop evidence for controlled-config-security-review only; no broad Harbor/backend generalization.

- integrity_gate: `pass`. The output contract changed after verifier feedback.
- behavior_gate: `pass`. A2 passes the deterministic verifier after the revision.
- robustness_gate: `partial`. The loop closes in Harbor, but repeatability/metamorphic evidence is still narrow.

Next required evidence:
- Add negative, swapped-target, fake-evidence, and metamorphic controls.
- Attach human or external review before broad deployment claims.

Sources: `outputs/harbor_llm_repair_loop_config_001/summary.json`, `outputs/harbor_llm_repair_loop_config_001/A1/verifier_report.json`, `outputs/harbor_llm_repair_loop_config_001/revision/patch_plan.json`, `outputs/harbor_llm_repair_loop_config_001/A2/verifier_report.json`

## offline_generalization_qualification_support

- Card type: `EvidenceSupportCard`
- Artifact: `outputs/validation/generalization_suite.json`
- Decision: `supporting_evidence`
- Level/support: `supports_L3_PROMOTE_CONTROLLED`
- Claim scope: Strong controlled evidence that one offline pipeline can cover the stored task cases.

- integrity_gate: `pass`. A2 passes 5/5 controlled cases.
- behavior_gate: `partial`. This is suite-level behavior evidence, not a single deployable Skill promotion.
- robustness_gate: `partial`. Negative controls and verifier stress checks are separate and must remain attached.

Next required evidence:
- Use this card as support for a repair-loop qualification card, not as a standalone deployment claim.

Sources: `outputs/validation/generalization_suite.json`

## negative_control_robustness_support

- Card type: `EvidenceSupportCard`
- Artifact: `outputs/validation/negative_controls.json`
- Decision: `supporting_evidence`
- Level/support: `supports_L3_PROMOTE_CONTROLLED`
- Claim scope: Narrow robustness support against unsupported evidence and clean-target false positives.

- integrity_gate: `pass`. Unsupported evidence and append-style false positives are rejected in two controlled cases.
- behavior_gate: `partial`. This does not demonstrate task-solving behavior by itself.
- robustness_gate: `partial`. The control set is useful but still small.

Next required evidence:
- Use this card as support for a repair-loop qualification card, not as a standalone deployment claim.

Sources: `outputs/validation/negative_controls.json`

## harbor_upload_repeatability_support

- Card type: `EvidenceSupportCard`
- Artifact: `outputs/validation/harbor_llm_repeatability_upload.json`
- Decision: `supporting_evidence`
- Level/support: `supports_L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT`
- Claim scope: Small repeatability support for the controlled Harbor upload repair loop.

- integrity_gate: `pass`. 3 Harbor upload repeats show stable A1 fail and A2 pass.
- behavior_gate: `partial`. This supports one Harbor upload loop, not broad prompt robustness.
- robustness_gate: `partial`. low_in_this_slice

Next required evidence:
- Use this card as support for a repair-loop qualification card, not as a standalone deployment claim.

Sources: `outputs/validation/harbor_llm_repeatability_upload.json`

