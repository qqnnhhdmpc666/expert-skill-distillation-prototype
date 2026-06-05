# Method Hypothesis

This document is a method-exploration note, not a final method claim. The stable demo pipeline remains unchanged. The goal here is to identify which mechanism may grow into a stronger contribution.

## H1: Execution-feedback-driven Compact Skill Compiler

Core chain:

```text
failure report
-> failure type
-> affected target
-> patch action
-> compact skill diff
-> validation gate
```

Problem it addresses:

Generated or compacted skills can fail during execution. A naive system either logs the failure or regenerates the whole skill. H1 asks whether failure attribution can drive a targeted compact-skill patch.

Current supporting artifacts:

- `outputs/mvp_vertical_slice/harbor_api_review_001`
- `outputs/mvp_vertical_slice/harbor_api_review_002`
- `outputs/mvp_vertical_slice/agent_mock_api_review_001`
- `outputs/mvp_vertical_slice/output_format_error_001`
- `outputs/mvp_vertical_slice/counterfactual_patch_utility_001`

Missing evidence:

- Counterfactual comparison against no patch, random patch, and wrong-type patch.
- More failure types beyond `missing_rule` and `output_format_error`.
- A stronger validation gate per patch type.

Minimum next experiment:

```text
outputs/mvp_vertical_slice/counterfactual_patch_utility_001
```

Compare, for the same failure, whether the compiler patch resolves the failure more reliably than no patch, random patch, or wrong-type patch.

Current conclusion:

```text
partially_supported
```

The missing-rule slice supports H1 in a toy setting: no/random/wrong-type patches fail, while the compiler patch restores R005/R006. The output-format slice adds nuance: the type-correct contract patch resolves the format failure, but full verifier pass can still require separate business-rule coverage.

Failure condition:

If random or wrong-type patches resolve the same failures as reliably as the compiler patch under similar token budgets, H1 is weak. The system may be benefiting from prompt length or verifier simplicity rather than correct failure-to-patch mapping.

## H2: Evidence-grounded Expert Skill Distillation

Core chain:

```text
expert material
-> evidence chunk
-> rule atom
-> evidence map
-> full skill
```

Problem it addresses:

Skill generation can hallucinate expert rules or over-generalize from sparse material. H2 asks whether evidence mapping makes expert-material-first distillation more auditable.

Current supporting artifacts:

- `outputs/mvp_vertical_slice/baseline_001/evidence_map.json`
- `outputs/mvp_vertical_slice/baseline_001/full_skill.md`
- `outputs/mvp_vertical_slice/baseline_001/rule_ledger.json`

Missing evidence:

- More heterogeneous expert materials.
- Manual or model-based evidence quality judgment.
- Cases where unsupported or weak rules would cause bad behavior if included.

Minimum next experiment:

Create a small case with one intentionally unsupported generated rule and verify whether evidence filtering prevents it from entering compact skill.

Failure condition:

If evidence status does not affect downstream skill quality or compact decisions, H2 remains mostly an audit/logging feature rather than a method mechanism.

## H3: Fixed-budget Deployment Skill Compiler

Core chain:

```text
full skill
-> rule scoring
-> budgeted selection
-> compact skill
-> execution feedback
```

Problem it addresses:

Full skills are too long for cheap deployment, but naive compact skills may drop execution-critical rules. H3 asks whether rule selection under a token budget can use material evidence, risk, and execution evidence to produce better deployment skills.

Current supporting artifacts:

- `outputs/mvp_vertical_slice/policy_comparison_001`
- `outputs/mvp_vertical_slice/baseline_001/cost_summary.json`
- `outputs/mvp_vertical_slice/llm_agent_api_review_001`

Missing evidence:

- A true fixed-budget policy where execution-aware rules replace lower-value rules without exceeding budget.
- More cases and more varied expected rules.
- Comparison against full skill and simple summary baselines.

Minimum next experiment:

Modify the policy comparison so execution-aware policy must stay within the same budget, then observe which rules it sacrifices and whether it improves coverage.

Failure condition:

If execution-aware policy only improves by exceeding budget, or if rule scoring cannot beat simple priority-only selection under fixed budget, H3 should remain exploratory.

## Current Priority

H1 is currently the strongest mechanism candidate because it already has two failure types and can be tested with counterfactual patch variants. H2 and H3 remain important, but they need more diverse data before stronger claims.
## Update: Method Discovery Loop

The next-stage plan is now tracked in:

```text
docs/METHOD_DISCOVERY_PLAN.md
```

The plan reframes the hypotheses as four mechanism candidates:

- M1: failure-to-patch mapping.
- M2: fixed-budget compact skill compiler.
- M3: rollback / validation-gated revision.
- M4: evidence-grounded expert distillation.

Each candidate must specify a trigger condition, decision rule, alternative/counterfactual, and failure boundary before it can be treated as more than a pipeline component.

### M2 Current Probe

Artifact:

```text
outputs/mvp_vertical_slice/fixed_budget_compiler_001
```

Current observation:

```text
execution-aware-fixed-budget stays within budget and recovers R005/R006,
but it sacrifices R003 and therefore does not fully pass the verifier.
```

Interpretation:

```text
partially_supported
```

This weakens the "it only works by appending more prompt" critique, but it does not yet prove a mature compact compiler.

### M3 Current Probe

Artifact:

```text
outputs/mvp_vertical_slice/rollback_gate_001
```

Current observation:

```text
The proposed patch resolves R005/R006 but drops R003.
The validation gate rejects it and rolls back.
```

Interpretation:

```text
useful as a toy maturation probe
```

The slice shows why repair should be validation-gated, but it does not yet prove robust rollback across realistic tasks.
