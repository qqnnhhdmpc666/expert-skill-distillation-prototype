# Live LLM Data Quality Status

- Scenario: `data_quality_review_001`
- Backend: `live_llm_text`
- Model: `gpt-5.5`
- Artifact dir: `outputs\live_llm_repair_loop_data_quality_001`

| Attempt | Pass | Feedback | Coverage | Schema | Weak Evidence |
|---|---:|---|---:|---:|---:|
| A1 | False | output_contract_error | 1.0 | 0.0 | 1.0 |
| A2 | True | pass | 1.0 | 1.0 | 1.0 |

## What happened

A1 used a relaxed output-contract prompt so the live LLM could emit target-grounded findings without `recommended_fix` fields.
The deterministic verifier rejected that output with `output_contract_error`.
The typed repair path then applied `rewrite_output_contract`, and A2 reran with the same target but a strict contract.

## Boundary

This is one controlled non-security local live-LLM repair loop. It shows the system is not only shaped for security tasks, but it is still narrow evidence rather than broad multi-domain generalization.
