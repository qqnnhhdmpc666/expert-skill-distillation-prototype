# Live LLM Repair Loop: config_security_001

| Attempt | Pass | Feedback | Coverage | Missing |
|---|---:|---|---:|---|
| A1 | False | missing_capability | 0.5 | CONFIG_ENV_GUARD |
| A2 | False | missing_capability | 0.5 | CONFIG_ENV_GUARD |

## Boundary

The LLM is only the agent that reads target/skill and emits `security_report.json`. The verifier/gate are deterministic and do not ask the LLM to grade itself.
