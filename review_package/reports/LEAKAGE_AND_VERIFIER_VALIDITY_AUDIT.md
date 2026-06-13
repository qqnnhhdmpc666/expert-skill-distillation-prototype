# Leakage And Verifier Validity Audit

Updated: 2026-06-09

## Bottom line

Current status: **moderate controlled trust**, not strong semantic trust.

The current verifier stack is good enough to support controlled A1/A2 evidence, negative controls, and typed repair attribution. It is not strong enough to prove open-world usefulness, adversarial robustness, or human-level semantic completeness.

## 1. Do prompts leak the expected final answer?

### Local upload live LLM

Artifact:

- `outputs/live_llm_repair_loop_upload_001/A1/prompt.md`

Finding:

- the prompt exposes only the capability ids present in the current Skill Package
- for A1 upload, the prompt allows only `UPLOAD_PATH_ISOLATION`
- it does not expose the missing final A2 capability set

Assessment:

- no direct final-answer leakage detected in the upload A1 prompt

### Harbor upload live LLM

Artifact:

- `outputs/harbor_llm_repair_loop_upload_001/A1/prompt.md`

Finding:

- same pattern as local upload
- only the v1 capability set is exposed
- the missing A2 capabilities are not listed in the A1 prompt

Assessment:

- no direct final-answer leakage detected in the upload Harbor A1 prompt

### Harbor config live LLM

Artifact:

- `outputs/harbor_llm_repair_loop_config_001/A1/prompt.md`

Finding:

- this prompt intentionally relaxes the output contract so `recommended_fix` may be omitted
- that is a controlled intervention, not silent leakage
- however, the prompt addendum string is awkwardly rendered and should be cleaned up later

Assessment:

- no direct final-answer leakage
- but there is explicit prompt-side contract steering, so this result should be described as controlled contract-repair evidence, not natural failure discovery

### Local data-quality live LLM

Artifact:

- `outputs/live_llm_repair_loop_data_quality_001/A1/prompt.md`

Finding:

- same controlled contract-relaxation pattern as Harbor config
- this is an honest manufactured failure mode, not hidden leakage

Assessment:

- acceptable for controlled repair evidence
- not evidence of spontaneous weakness discovery

## 2. Does the patch plan come from verifier feedback rather than the final answer?

Artifacts:

- `outputs/live_llm_repair_loop_upload_001/revision/patch_plan.json`
- `outputs/live_llm_repair_loop_data_quality_001/revision/patch_plan.json`
- `outputs/harbor_llm_repair_loop_upload_001/revision/patch_plan.json`
- `outputs/harbor_llm_repair_loop_config_001/revision/patch_plan.json`

Finding:

- all four patch plans consume A1 failure feedback
- repair action selection is mediated by `revision/repair_policy.json` plus `src/skill_deployment/repair.py`
- there is no separate gold-answer file being read by the local repair path

Assessment:

- repair attribution is reasonably clean in the controlled setting

## 3. Is the verifier only checking keywords?

### Shared local verifier

Artifact:

- `src/skill_deployment/verifier.py`

Finding:

- checks capability coverage
- checks non-empty `recommended_fix`
- checks non-empty `evidence_span`
- does not verify deep semantic adequacy of the fix text

Assessment:

- stronger than pure keyword presence
- still shallow compared with semantic or human evaluation

### Harbor upload verifier

Artifacts:

- `outputs/harbor_llm_repair_loop_upload_001/task_A1/tests/test.sh`
- `outputs/harbor_llm_repair_loop_upload_001/task_A2/tests/test.sh`

Finding:

- A1 and A2 use the same verifier script hash:
  - `21167CFFEB7BE3AD5A1D127FDA60ED88308A9A343C8E4868A5036B72FA0B6443`
- it checks expected capabilities and schema errors
- it does **not** check unsupported evidence / false positives

Assessment:

- stable within-scenario verifier logic
- incomplete robustness because false-positive pressure is absent

### Harbor config verifier

Artifacts:

- `outputs/harbor_llm_repair_loop_config_001/task_A1/tests/test.sh`
- `outputs/harbor_llm_repair_loop_config_001/task_A2/tests/test.sh`

Finding:

- A1 and A2 use the same verifier script hash:
  - `7AAED197AF816AB1128E4E34A1B16468FDA22EB143D0921FFD180F86A296C387`
- it checks coverage, false positives, and missing `recommended_fix`

Assessment:

- stronger contract checking than the upload Harbor verifier

## 4. Is evidence_span actually bound to the target?

Positive evidence:

- local negative control rejects unsupported evidence:
  - `outputs/validation/negative_controls.json`
- local/Harbor agent artifacts record target reads:
  - `target_reads.json` in Harbor loops
  - prompt and target content in local loops

Limitation:

- the shared local verifier only checks that `evidence_span` is non-empty
- true substring binding is covered only in narrow negative controls, not in every path

Assessment:

- evidence binding is partially supported, not universally enforced

## 5. Do negative controls still reject unsupported evidence / false positives?

Artifact:

- `outputs/validation/negative_controls.json`

Finding:

- `upload_security_negative` rejects unsupported evidence
- `config_security_false_positive_control` rejects append-style false positives on a clean target

Assessment:

- this is the strongest direct evidence that verifier/gate are not blindly permissive

## 6. Does A2 pass because Skill changed, not because verifier got looser?

Upload Harbor:

- A1 and A2 verifier hash is identical
- A1 skill manifest has one capability
- A2 skill manifest has three capabilities
- reward changes `0.0 -> 1.0`

Config Harbor:

- A1 and A2 verifier hash is identical
- capability set stays fixed
- output contract changes from relaxed to strict
- reward changes `0.0 -> 1.0`

Local data-quality:

- deterministic local verifier is the same function
- capability set stays fixed
- output contract changes
- A1 schema errors disappear in A2

Assessment:

- current A1/A2 improvements are attributable to Skill/contract changes, not verifier relaxation

## 7. Are model call artifacts redacted?

Checked artifacts:

- `outputs/live_llm_repair_loop_upload_001/A1/model_calls.json`
- `outputs/live_llm_repair_loop_data_quality_001/A1/model_calls.json`
- `outputs/harbor_llm_repair_loop_upload_001/A1/model_calls.json`
- `outputs/harbor_llm_repair_loop_config_001/A1/model_calls.json`

Finding:

- endpoint, prompt messages, response, and usage are stored
- authorization header / raw API key is not stored in these model-call artifacts

Residual risk:

- prompts can contain target literals such as fake example secrets inside the reviewed target
- that is task content, not credential leakage

## 8. What the current verifier cannot prove

The current verifier stack does not prove:

1. human usefulness
2. semantic completeness
3. open-world transfer
4. broad prompt stability
5. adversarial robustness
6. absence of subtle false positives in every backend

## 9. Required claim boundary

Safe claim:

> The verifier/gate stack provides controlled structural validity and some narrow robustness checks.

Unsafe claim:

> Verifier PASS means the report is semantically complete or broadly trustworthy in the open world.

## 10. Next verifier stress tests

1. substring-grounding checks on every local live-LLM loop, not only negative controls
2. Harbor upload false-positive control, since current upload verifier does not check unsupported evidence
3. paraphrase adversarial examples where evidence is semantically wrong but non-empty
4. prompt-format perturbation tests across standard vs concise prompts
5. swapped-target tests where the same report is evaluated against the wrong target
6. repair-plan audit ensuring no hidden gold labels enter the patch path
7. human plausibility review on A1 vs A2 reports for at least one security and one non-security slice
