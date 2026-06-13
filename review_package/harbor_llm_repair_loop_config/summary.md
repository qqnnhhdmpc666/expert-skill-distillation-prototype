# Harbor LLM Config Repair Loop

| Attempt | Pass | Reward | Coverage | Feedback | Schema errors |
|---|---:|---:|---:|---|---|
| A1 | False | 0.0 | 1.0 | output_contract_error | CONFIG_PROD_DEBUG missing recommended_fix, CONFIG_INSECURE_HTTP missing recommended_fix, CONFIG_HARDCODED_SECRET missing recommended_fix |
| A2 | True | 1.0 | 1.0 | pass | none |

A1 and A2 use two generated Harbor task copies so the container reads different `/app/skill` contract snapshots while keeping the same target and verifier family.

Boundary: this is controlled second-task Harbor LLM evidence for one config-security scenario. It is not open-world vulnerability discovery or broad Harbor generalization.
