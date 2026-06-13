# Failure Origin Taxonomy

## Purpose

When A2 fails, the system should not immediately say "the Skill is bad." Failure can originate from multiple layers. Qualification-Guided Skill Evolution needs failure-origin attribution so that repair, evaluation, and external claims stay honest.

## Taxonomy

| Failure origin | Meaning | Typical evidence | Action |
|---|---|---|---|
| `expert_material_gap` | Expert material did not contain the needed capability or evidence requirement. | Missing source-to-skill mapping, weak provenance. | Add or clarify expert material. |
| `candidate_extraction_gap` | Material contained the concept, but the candidate extractor did not surface it. | Candidate capability absent before normalization. | Improve extractor or provenance mapping. |
| `normalization_gap` | Natural-language capability was mapped to the wrong controlled capability. | Rule ID/capability mismatch. | Fix capability registry mapping. |
| `repair_operator_noop_or_patch_application_failure` | The repair action was selected but did not change the Skill in the required place. | Before/after manifest unchanged after `patch_capability`. | Reject and fix repair compiler. |
| `repair_scope_mismatch` | The Skill changed, but not enough to cover the verifier feedback. | A1 missing capability not present in Skill v2. | Patch missing capability or contract. |
| `skill_rendering_failure` | The internal patch exists but the rendered Skill prompt/manifest omits it. | Manifest changed but `SKILL.md` does not. | Fix renderer/exporter. |
| `runner_input_gap` | The agent did not receive the right target, Skill, or contract. | Missing target reads or skill reads. | Fix runner/Harbor mount path. |
| `llm_instruction_following_failure` | The Skill is present, but the LLM ignores it. | Skill v2 contains capability, A2 output still misses same capability. | Improve prompt structure, examples, or execution protocol. |
| `skill_to_execution_gap` | The revision lands, but observed behavior does not improve. | A2 still has same missing capability. | Quarantine and run behavior autopsy. |
| `verifier_contract_mismatch` | Verifier expects a schema or field that the Skill did not instruct. | Schema errors dominate despite coverage. | Rewrite output contract and align Skill. |
| `evidence_grounding_failure` | Finding exists but evidence does not bind to target text. | Unsupported/fabricated evidence spans. | Reject finding; add target binding. |
| `false_positive_risk` | The agent reports issues on a clean or irrelevant target. | Clean config negative control fails. | Gate rejection and regression control. |
| `prompt_leakage_or_answer_leakage` | Prompt or artifacts reveal expected answers. | Expected final capability list appears as answer target. | Reject and sanitize. |
| `verifier_relaxation` | A2 passes because verifier/gate was weakened. | Contract or expected set silently relaxed. | Reject and restore verifier. |
| `sandbox_substrate_failure` | Harbor/Docker/WSL task cannot execute reliably. | Env missing, network fail, artifact missing. | Treat as backend maturity issue, not Skill failure. |

## Current Failure Autopsy

### Local live LLM config

Artifact: `outputs/live_llm_repair_loop_config_security_001/summary.json`

Observation:

- A1 missing: `CONFIG_ENV_GUARD`
- Repair action: `patch_capability`
- Skill v2 capability list adds `CONFIG_ENV_GUARD`
- A2 still misses `CONFIG_ENV_GUARD`

Attribution:

- Primary: `skill_to_execution_gap`
- Secondary: `llm_instruction_following_failure`

Qualification result:

- Integrity is supported.
- Behavior fails.
- The revision should be quarantined, not promoted.

### Local live LLM API review

Artifact: `outputs/live_llm_repair_loop_api_review_001/summary.json`

Observation:

- A1 missing: `API_OVERBROAD_RISK`
- Repair action: `patch_capability`
- Before capabilities already include `API_OVERBROAD_RISK`
- After capabilities are unchanged
- A2 still misses `API_OVERBROAD_RISK`

Attribution:

- Primary: `repair_operator_noop_or_patch_application_failure`
- Secondary: `skill_to_execution_gap`

Qualification result:

- Integrity fails.
- The revision should be rejected before behavior claims are made.

### Harbor live LLM upload

Artifact: `outputs/harbor_llm_repair_loop_upload_001/summary.json`

Observation:

- A1 misses upload audit/type capabilities.
- Repair action adds missing capabilities.
- A2 passes in Harbor.
- Repeatability smoke exists for upload.

Attribution:

- No blocking failure origin in the current controlled slice.
- Remaining risk: narrow scope and limited metamorphic controls.

Qualification result:

- `L4_PROMOTE_SANDBOXED` for controlled upload scope only.

### Harbor live LLM config

Artifact: `outputs/harbor_llm_repair_loop_config_001/summary.json`

Observation:

- A1 covers issues but fails schema/evidence contract.
- Repair action rewrites output contract.
- A2 passes in Harbor.

Attribution:

- A1 failure origin: `verifier_contract_mismatch`
- A2 qualification risk: no repeatability smoke yet.

Qualification result:

- `L4_PROMOTE_SANDBOXED` for controlled config scope only, with narrower robustness than upload.

## How To Use This Taxonomy

Every failed or partial qualification card should record at least one failure origin. The goal is to avoid vague conclusions like "Skill failed" and instead route the next action:

- Repair compiler bug -> fix repair/operator.
- Agent ignored Skill -> adjust prompt/execution protocol.
- Verifier mismatch -> rewrite contract.
- False positive -> strengthen gate and negative controls.
- Sandbox failure -> improve backend substrate.

This makes failures useful evidence rather than embarrassing artifacts.
