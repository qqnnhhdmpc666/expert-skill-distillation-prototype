# Live LLM Repair Loop: api_review_001

| Attempt | Pass | Feedback | Coverage | Missing |
|---|---:|---|---:|---|
| A1 | False | missing_capability | 0.5 | API_OVERBROAD_RISK |
| A2 | False | missing_capability | 0.5 | API_OVERBROAD_RISK |

## Boundary

The LLM is only the agent that reads target/skill and emits `security_report.json`. The verifier/gate are deterministic and do not ask the LLM to grade itself.
