# Small Candidate Evolution Status

Run id: `skill_evolution_lab_secure_code_review`
Candidate count: `3`

## Boundary

This is a small candidate comparison, not a multi-round autonomous search. Candidate generation reads failure reports, verifier feedback, evidence summaries, and limitation summaries only; verifier-only oracle fields are not used for generation.

| Candidate | Validation case | Decision | Score delta | FP delta | Scope violation |
|---|---|---|---:|---:|---|
| config_security_001__v3_candidate_001 | config_security_001 | not_promoted | 0.0 | 0.0 | False |
| clean_false_positive_guard__v3_candidate_002 | mini_clean_out_of_scope_001 | not_promoted | -0.4 | 3.0 | True |
| dependency_version_risk__v3_candidate_003 | mini_dependency_version_risk_001 | not_promoted | -0.4 | 1.0 | True |

## Rejected Buffer

- Rejected edit count: `5`
- Reported buffer: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\rejected_edit_buffer.json`
