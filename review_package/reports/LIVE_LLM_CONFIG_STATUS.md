# Live LLM Config Security Status

- Scenario: `config_security_001`
- Backend: `live_llm_text`
- Model: `gpt-5.5`
- Artifact dir: `outputs\live_llm_repair_loop_config_security_001`

| Attempt | Pass | Feedback | Coverage | Schema | Weak Evidence |
|---|---:|---|---:|---:|---:|
| A1 | False | missing_capability | 0.5 | 1.0 | 1.0 |
| A2 | False | missing_capability | 0.5 | 1.0 | 1.0 |

## What happened

A1 feedback was `missing_capability` and the typed repair selected `patch_capability`.
Capabilities before repair: `CONFIG_AUDIT_EXPORT`.
Capabilities after repair: `CONFIG_AUDIT_EXPORT, CONFIG_ENV_GUARD`.
Gate decision: `accept`.

## Boundary

This is one controlled second local security slice for the live-LLM backend. It improves beyond upload-only evidence, but it is still narrow controlled evidence rather than broad security-task generalization.
