# Platform Roadmap

This is a scoped maturation roadmap for the prototype. It is intentionally lightweight: the current code should not be heavily refactored before the two-week demo unless a module boundary directly improves reproducibility.

## Current Position

The project has moved from a single MVP run into a small artifact platform:

```text
expert material
-> skill artifacts
-> agent output
-> verifier report
-> patch proposal
-> validation gate
-> compact skill revision
```

The next platform work should make this flow reusable without turning the prototype into a large framework too early.

## Proposed Modules

### TaskCase

Stores the case input, expected rule IDs, verifier contract, and scenario metadata.

Current examples:

- `data/harbor_api_review_tasks/api-review-001-*`
- `data/harbor_api_review_tasks/api-review-002-*`

### AgentRunner

Runs a skill-conditioned agent and writes `review.json`.

Current examples:

- `agents/api_review_mock_agent.py`
- `agents/api_review_llm_agent.py`

### VerifierRunner

Checks `review.json` against the case contract and returns pass/fail, missing rules, and failure type.

Current examples:

- Harbor verifier tasks
- `scripts/verify_api_review_json.py`

### ExecutionReport

Normalizes verifier output into a common report that downstream patch logic can consume.

Current examples:

- `integrations/spark/convert_spark_artifacts.py`
- `integrations/spark/convert_harbor_result.py`

### PatchCompiler

Maps failure type and affected target into a patch proposal.

Current examples:

- `integrations/spark/apply_spark_feedback.py`
- `scripts/run_counterfactual_patch_utility.py`
- `scripts/run_fixed_budget_compiler.py`

### ValidationGate

Accepts, rejects, or rolls back a patch proposal based on original failure resolution, regressions, budget, and failure-critical preservation.

Current examples:

- `outputs/mvp_vertical_slice/harbor_api_review_001/validation_gate.json`
- `outputs/mvp_vertical_slice/rollback_gate_001/validation_gate.json`

### InvocationProtocol

Defines how a compact skill should be used by an agent, including rule-application traces and evidence spans.

Current examples:

- `docs/SKILL_TO_AGENT_LOOP.md`
- `outputs/mvp_vertical_slice/skill_to_agent_loop_001/skill_variants/protocolized_compressed_skill.md`

### TraceVerifier

Checks whether findings are supported by rule applications grounded in case evidence.

Current examples:

- `scripts/verify_api_review_trace_json.py`
- `outputs/mvp_vertical_slice/skill_to_agent_loop_001`

### ArtifactStore

Keeps each run reproducible with a stable output directory, manifest, summary JSON, and summary Markdown.

Current examples:

- `outputs/mvp_vertical_slice/*/manifest.json`
- `outputs/demo_pipeline_check/summary.json`

## What Not To Do Yet

- Do not rewrite all scripts into a framework before the demo.
- Do not hide simple deterministic steps behind unnecessary abstractions.
- Do not claim this roadmap is a mature open-source platform design.

## Near-Term Maturation

1. Keep adding new slices as isolated output directories.
2. Add common schemas only when two or more slices need the same field.
3. Use `scripts/run_demo_pipeline.py --check-existing` as the health check before demonstrations.
4. Promote repeated logic into `src/` only after the method direction stabilizes.

## Latest Maturation Slice

The validation-aware compiler slice adds a useful boundary between `PatchCompiler` and `ValidationGate`:

```text
PatchCompiler proposes multiple candidates.
ValidationGate checks hard constraints.
ArtifactStore records accepted, rejected, and infeasible candidates.
```

Current artifact:

```text
outputs/mvp_vertical_slice/validation_aware_compiler_001
```

Near-term platform implication:

- Candidate generation and validation results should remain explicit artifacts.
- Infeasible outcomes should be first-class outputs, not hidden errors.
- Compression should be labeled separately from ordinary selection success.

## Traceable Compiler Integration

The latest integration slice connects `PatchCompiler`, `ValidationGate`, `InvocationProtocol`, and `TraceVerifier` into one deployment loop.

Current artifact:

```text
outputs/mvp_vertical_slice/traceable_compiler_integration_001
```

Platform implication:

- A deployable compact skill should be represented as rules plus protocol plus verifier contract.
- Token accounting must include both rule tokens and protocol tokens.
- Validation should reject candidates that pass trace verification but exceed the deployment budget.
- Trace verification should remain separate from simple rule-id coverage, because it catches shallow outputs that simple coverage misses.

Current status:

```text
partially_supported_with_protocol_overhead
```

Near-term engineering direction:

- Compress the invocation protocol.
- Explore whether a stable protocol contract can be cached or amortized outside per-call prompt tokens.
- Keep over-budget rejection as a valid outcome rather than silently accepting an expensive artifact.
