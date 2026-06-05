# Artifact Claim Audit 001

## Purpose

Audit what each core artifact can safely support, and prevent overclaiming before demo/report use.

| Artifact | Role | Claim Strength | Key Result | Limitation |
|---|---|---|---|---|
| baseline_001 | demo_core | supported | no_skill 0/6; full_skill 6/6; compact_v1 4/6 missing R005/R006; compact_v2 6/6. | Deterministic local evaluator; not a real-world benchmark. |
| harbor_api_review_001 | demo_core | supported | compact_v1 reward 0.0 with missing R005/R006; compact_v2 reward 1.0. | Single API-review case; same controlled task family. |
| harbor_api_review_002 | demo_core | partially_supported | case002 compact_v1 fails on R005/R006; compact_v2 passes. | Small holdout; still the same rule family. |
| llm_agent_api_review_001 | demo_core | partially_supported | gpt-5.5 compact_v1 outputs R001-R004; compact_v2 outputs R001-R006 on case001/case002. | Small matrix; not a model stability or capability benchmark. |
| output_format_error_001 | method_exploration | partially_supported | output_format_error maps to OUTPUT_CONTRACT and rewrite_output_contract. | Second vertical slice only; not a full failure taxonomy. |
| counterfactual_patch_utility_001 | method_exploration | partially_supported | compiler_patch resolves missing_rule; output_contract_patch resolves format failure while wrong missing-rule patch does not. | Toy counterfactual; not statistical evidence for a general patch compiler. |
| fixed_budget_compiler_001 | method_exploration | partially_supported | execution-aware-fixed-budget recovers R005/R006 under budget but drops R003. | Regression remains; selector alone is insufficient. |
| rollback_gate_001 | method_exploration | supported | patch recovers R005/R006 but loses R003; gate rejects and rolls back. | Toy gate; not a mature rollback system. |
| validation_aware_compiler_001 | method_exploration | partially_supported | candidate_C compressed required rules fits budget and covers R001-R006. | Success depends on compressed wording; needs semantic audit. |
| semantic_preservation_audit_001 | method_exploration | partially_supported | semantic_preservation_status preserved for R001-R006. | Keyword/field audit, not deep semantic judgment. |
| skill_to_agent_loop_001 | method_exploration | partially_supported | protocolized compressed skill passes trace verifier; shortcut/plain compressed variants fail strict trace. | Toy protocol; not universal across agents/tasks. |
| traceable_compiler_integration_001 | platform_maturation | partially_supported | protocolized variant passes trace verification but is 300/237 tokens; validation gate rejects over budget. | Integration toy slice; exposes overhead rather than solving it. |
| real_effect_eval_001 | platform_maturation | partially_supported | compact_v1 avg coverage 0.58; patched_compact avg coverage 1.00 on 4 cases. | 4-case controlled holdout; not a benchmark or real-world generalization proof. |
| selective_trace_compiler_001 | platform_maturation | partially_supported | full_trace 300/237 rejected; selective_trace R005/R006 183/237 accepted and blocks shortcut. | Toy trace policy; not mature tracing strategy. |
| component_baseline_direct_summary_001 | platform_maturation | partially_supported | direct_summary_skill avg coverage 0.92; patched_compact avg coverage 1.00 on 4 controlled cases. | Deterministic component attribution slice; not a benchmark and not broad evidence against summarization baselines. |

## Safe Main Claim

The prototype demonstrates a risk-budgeted traceable skill deployment loop in a controlled API-review family: expert materials become evidence-grounded skills, verifier feedback drives patch proposals, validation gates prevent regression or over-budget deployment, and selective trace focuses rule-application evidence on high-risk rules.

## Boundary

This is not a benchmark, not a universal skill compiler, and not evidence of superiority over related work. Current claims are controlled-family and toy-slice claims.
