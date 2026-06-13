# Live LLM API Review Status

- Scenario: `api_review_001`
- Backend: `live_llm_text`
- Model: `gpt-5.5`
- Artifact dir: `outputs\live_llm_repair_loop_api_review_001`

| Attempt | Pass | Feedback | Coverage | Schema | Weak Evidence |
|---|---:|---|---:|---:|---:|
| A1 | False | missing_capability | 0.5 | 0.0 | 1.0 |
| A2 | False | missing_capability | 0.5 | 1.0 | 1.0 |

## What happened

A1 feedback was `missing_capability` and the typed repair selected `patch_capability`.
Capabilities before repair: `API_SCHEMA_CONTRACT, API_OVERBROAD_RISK`.
Capabilities after repair: `API_SCHEMA_CONTRACT, API_OVERBROAD_RISK`.
Gate decision: `accept`.

## Boundary

This is one controlled local API/code-review repair loop for the live-LLM backend. It broadens beyond upload-only evidence, but it is still narrow controlled evidence rather than broad live-LLM task generalization.
