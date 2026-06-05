# Platform Roadmap

This roadmap keeps the prototype lightweight for the demo. It describes module boundaries but does not require a large refactor now.

## Positioning

Current platform direction:

```text
risk-budgeted traceable skill deployment prototype
```

or:

```text
correctness-constrained expert skill deployment optimization
```

The platform should support this loop:

```text
expert material
-> evidence-grounded full skill
-> compact deployment skill
-> agent output
-> verifier feedback
-> patch proposal
-> validation gate
-> invocation protocol / selective trace
-> trace verifier
-> artifact store
```

## Module Boundaries

### TaskCase

Stores task input, expected rule IDs, negative/forbidden rule IDs, verifier contract, and scenario metadata.

Current examples:

- `data/harbor_api_review_tasks/api-review-001-*`
- `data/harbor_api_review_tasks/api-review-002-*`
- `data/api_review_holdout_cases/*`

### AgentRunner

Runs a skill-conditioned agent and writes agent output such as `review.json`.

Current examples:

- `agents/api_review_mock_agent.py`
- `agents/api_review_llm_agent.py`
- `scripts/run_real_effect_eval.py`

### VerifierRunner

Checks agent output against a task contract and returns pass/fail, missing rules, semantic errors, trace errors, and failure type.

Current examples:

- Harbor verifier tasks.
- `scripts/verify_api_review_json.py`
- `scripts/verify_api_review_semantic_json.py`
- `scripts/verify_api_review_trace_json.py`

### PatchCompiler

Maps verifier feedback and failure type into patch proposals.

Current examples:

- `integrations/spark/apply_spark_feedback.py`
- `scripts/run_counterfactual_patch_utility.py`
- `scripts/run_fixed_budget_compiler.py`
- `scripts/run_validation_aware_compiler.py`

### ValidationGate

Accepts, rejects, rolls back, or reports infeasible candidates based on:

- original failure resolution,
- regression detection,
- token budget,
- failure-critical preservation,
- semantic preservation,
- trace requirements.

Current examples:

- `outputs/mvp_vertical_slice/harbor_api_review_001/validation_gate.json`
- `outputs/mvp_vertical_slice/rollback_gate_001/validation_gate.json`
- `outputs/mvp_vertical_slice/traceable_compiler_integration_001`
- `outputs/mvp_vertical_slice/selective_trace_compiler_001`

### InvocationProtocol

Defines how compact skill should be invoked by an agent, including required output fields and optional rule-application trace.

Current examples:

- `docs/SKILL_TO_AGENT_LOOP.md`
- `outputs/mvp_vertical_slice/skill_to_agent_loop_001/skill_variants/protocolized_compressed_skill.md`

### TraceVerifier

Checks whether traced findings are supported by rule applications grounded in task evidence.

Current examples:

- `scripts/verify_api_review_trace_json.py`
- `outputs/mvp_vertical_slice/skill_to_agent_loop_001`
- `outputs/mvp_vertical_slice/selective_trace_compiler_001`

### ArtifactStore

Keeps each run reproducible with stable output directories, manifest files, summary JSON, and summary Markdown.

Current examples:

- `outputs/mvp_vertical_slice/*/manifest.json`
- `outputs/mvp_vertical_slice/*/summary.json`
- `outputs/demo_pipeline_check/summary.json`

## Near-Term Work

Do next:

- Keep demo core stable.
- Use `scripts/run_demo_pipeline.py --check-existing` before demos.
- Maintain `outputs/mvp_vertical_slice/artifact_claim_audit_001` as a claim guard.
- Add common schemas only when repeated fields become painful.
- If expanding real-effect evaluation, add diverse cases instead of repeating the same R005/R006 pattern.

Do not do yet:

- Do not rewrite all scripts into a framework before the demo.
- Do not hide deterministic slices behind abstractions.
- Do not call the current 4-case holdout a benchmark.
- Do not call selective trace a mature tracing strategy.
- Do not claim a universal compact skill compiler.
