# SWE-bench External Smoke Status

- Run: `swebench_lite_smoke_20260612`
- Dataset: `SWE-bench/SWE-bench_Lite`
- Instances: `5`

## Variant Status

- `empty_patch`: `completed_empty_patch_skipped_by_official_harness`
- `gold_patch`: `blocked_docker_registry_unavailable`
- `skill_llm_patch`: `blocked_no_model`

## Blocked Reasons

- `gold_patch`: Docker registry access failed while resolving official SWE-bench images/base images.
- `skill_llm_patch`: OPENAI_API_KEY plus MODEL or OPENAI_MODEL is required for non-oracle patch generation.

## Evidence

- Instances: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_lite_smoke_20260612\instances.json`
- Marginal utility: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_swebench\swebench_lite_smoke_20260612\marginal_utility.json`

## Claims

- Adapter maturity supported: `False`
- Official gold-patch plumbing supported: `False`
- Framework effectiveness supported: `False`

No SWE-bench effectiveness claim is made unless `skill_llm_patch` beats `empty_patch` on resolved count.
