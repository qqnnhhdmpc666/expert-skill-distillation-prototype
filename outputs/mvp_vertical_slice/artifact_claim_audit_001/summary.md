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
| risk_trace_policy_baseline_001 | method_exploration | partially_supported | random_selective_trace R002/R003 gives failure-critical trace coverage 0.00; risk_based_selective_trace R005/R006 gives 1.00 at the same 183/237 token cost. | Single random seed and tiny rule pool; not statistical evidence for a mature risk policy. |
| risk_trace_policy_robustness_001 | method_exploration | partially_supported | Among all 15 size=2 trace allocations, only R005/R006 covers both failure-critical rules; risk-based selection picks R005/R006. | Complete enumeration of a tiny toy rule pool; not statistical significance or mature policy validation. |
| direct_summary_miss_analysis_001 | method_exploration | partially_supported | Direct summary fails only case004 by missing R006; patched_compact includes R006 and passes. | One explanatory miss case; not a general long-tail failure pattern. |
| adversarial_trace_verifier_001 | method_exploration | partially_supported | Valid control passes; fake evidence span, generic trigger, mismatched finding_id, and rule-id-only trace are rejected. | Toy adversarial checks only; not a deep semantic verifier or proof against sophisticated fake evidence. |
| revision_decision_matrix_001 | method_exploration | partially_supported | Different feedback/risk types map to different constrained decisions: patch rule, rewrite output contract, reject/rollback, semantic audit, trace contract, verifier strengthening, or selective trace. | Mechanism matrix over existing toy artifacts only; not a mature revision algorithm. |
| posterior_revision_signal_audit_001 | method_exploration | partially_supported | patched_compact improves coverage over compact_v1 by 0.4166 and over direct_summary by 0.0833; type-correct missing-rule and output-contract patches beat wrong-type counterfactuals. | Audit over existing controlled API-review artifacts only; not a cross-domain posterior-revision metric. |
| naive_revision_ablation_001 | method_exploration | partially_supported | always_append fixes missing_rule but not output_format_error; always_contract fixes format but not missing_rule; always_full_trace is 300/237 over budget; type-specific operator plus gate/selective trace resolves all tested axes. | Diagnostic ablation over existing artifacts only; always_regenerate_full_skill remains a strong high-cost upper bound. |

## Safe Main Claim

The prototype demonstrates a risk-budgeted traceable skill deployment loop in a controlled API-review family: expert materials become evidence-grounded skills, verifier feedback drives patch proposals, validation gates prevent regression or over-budget deployment, and selective trace focuses rule-application evidence on high-risk rules.

## Boundary

This is not a benchmark, not a universal skill compiler, and not evidence of superiority over related work. Current claims are controlled-family and toy-slice claims.
