# Harbor LLM Repair Loop Audit

Updated: 2026-06-08 Harbor LLM upload audit plus second-task extension.

## Scope

Primary audited artifact:

- `outputs/harbor_llm_repair_loop_upload_001`

Related strengthening artifacts:

- `outputs/harbor_llm_repair_loop_config_001`
- `outputs/validation/harbor_llm_repeatability_upload.json`

## Upload Audit Checklist

| Check | Result | Evidence |
|---|---|---|
| A1 and A2 are two generated Harbor task copies | PASS | `outputs/harbor_llm_repair_loop_upload_001/task_A1/` and `task_A2/` both exist with distinct `environment/skill/manifest.json` snapshots. |
| A1 `/app/skill/manifest.json` exposes only `UPLOAD_PATH_ISOLATION` | PASS | `outputs/harbor_llm_repair_loop_upload_001/A1/skill_manifest.json` |
| A2 `/app/skill/manifest.json` exposes all three upload capabilities | PASS | `outputs/harbor_llm_repair_loop_upload_001/A2/skill_manifest.json` |
| A1 verifier FAIL, A2 verifier PASS | PASS | `A1/verifier_report.json` shows missing `UPLOAD_AUDIT_RETENTION`, `UPLOAD_TYPE_MAGIC`; `A2/verifier_report.json` shows missing `[]`. |
| Patch plan comes from A1 verifier feedback | PASS | `revision/patch_plan.json` consumes `A1/failure_feedback.json` and maps `missing_capability -> patch_capability`. |
| A1 and A2 use the same verifier logic | PASS | `task_A1/tests/test.sh` and `task_A2/tests/test.sh` have identical SHA256: `21167CFFEB7BE3AD5A1D127FDA60ED88308A9A343C8E4868A5036B72FA0B6443`. |
| Prompt / model call does not inject verifier answer artifacts | PASS with caveat | `A1/prompt.md` and `A2/prompt.md` include only `/app/skill` and `/app/target` content, not verifier report, patch plan, or expected-final-answer file. Caveat: the static JSON example still uses `UPLOAD_TYPE_MAGIC` as an example string, but the rule line constrains output to enabled `/app/skill` capabilities and observed A1 output obeyed that restriction. |
| Target reads prove the Harbor LLM agent read target files | PASS | `A1/target_reads.json` and `A2/target_reads.json` show `/app/target/app.py` and `/app/target/config.yaml`, plus `/app/skill/*`. |
| `security_report.json` is generated inside Harbor execution | PASS | Harbor trial artifact copies exist under `A1/jobs/.../artifacts/security_report.json` and `A2/jobs/.../artifacts/security_report.json`, then are copied to top-level `A1/` and `A2/`. |
| API key not written into outputs / reports / review package | PASS | Exact-key scan over `outputs`, `reports`, and `review_package` returned no hits; `backend_metadata.json` records only `api_key_present: true`. |

## Upload Audit Conclusion

The upload Harbor LLM repair loop is valid controlled evidence for one scenario:

1. A1 and A2 really run as two Harbor task copies with different `/app/skill` manifests.
2. The same verifier logic grades both attempts.
3. A1 fails for the expected missing-capability reason.
4. The repair plan is artifact-backed.
5. A2 reruns inside Harbor and passes.

This is stronger than a hand-authored slideshow and stronger than a single Harbor pass, but it is still controlled single-family evidence.

## Second-Task Extension

`outputs/harbor_llm_repair_loop_config_001` adds a second Harbor LLM task family with a different repair mechanism:

- A1 uses a weaker output contract and fails with `output_contract_error`.
- `revision/patch_plan.json` maps that failure to `rewrite_output_contract`.
- A2 keeps the same target and expected capabilities, tightens the contract, reruns in Harbor, and passes.

This matters because the second task is not another copy of upload missing-capability repair. It exercises a different feedback type and repair action in the same Harbor LLM setting.

## Repeatability Smoke

`outputs/validation/harbor_llm_repeatability_upload.json` records three upload-loop observations:

- A1 all fail: `True`
- A2 all pass: `True`
- Reward pairs stable: `0.0 -> 1.0`
- Failure reason stable: missing `UPLOAD_AUDIT_RETENTION` and `UPLOAD_TYPE_MAGIC`

This is still small-sample evidence, but it reduces the risk that the Harbor upload loop result was a one-off lucky run.

## Boundary

Safe reading:

- one audited Harbor LLM upload repair loop,
- one controlled Harbor LLM config repair loop,
- small repeatability smoke on upload.

Unsafe reading:

- Harbor LLM generalizes broadly across security tasks,
- the system is a general vulnerability scanner,
- the LLM autonomously performs open-world vulnerability discovery,
- full SPARK-PDI reproduction is complete.
