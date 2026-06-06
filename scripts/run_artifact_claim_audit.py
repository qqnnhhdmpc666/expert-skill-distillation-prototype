from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/artifact_claim_audit_001")


ARTIFACTS: list[dict[str, Any]] = [
    {
        "artifact": "baseline_001",
        "path": "outputs/mvp_vertical_slice/baseline_001",
        "supported_claim": "Expert materials can be distilled into full and compact skill artifacts, and compact_v1 can lose rules that compact_v2 restores.",
        "key_result": "no_skill 0/6; full_skill 6/6; compact_v1 4/6 missing R005/R006; compact_v2 6/6.",
        "limitation": "Deterministic local evaluator; not a real-world benchmark.",
        "role": "demo_core",
        "claim_strength": "supported",
    },
    {
        "artifact": "harbor_api_review_001",
        "path": "outputs/mvp_vertical_slice/harbor_api_review_001",
        "supported_claim": "Real Harbor verifier feedback can identify missing rules and drive a compact skill patch.",
        "key_result": "compact_v1 reward 0.0 with missing R005/R006; compact_v2 reward 1.0.",
        "limitation": "Single API-review case; same controlled task family.",
        "role": "demo_core",
        "claim_strength": "supported",
    },
    {
        "artifact": "harbor_api_review_002",
        "path": "outputs/mvp_vertical_slice/harbor_api_review_002",
        "supported_claim": "The same missing-rule repair pattern transfers to a holdout API-review case.",
        "key_result": "case002 compact_v1 fails on R005/R006; compact_v2 passes.",
        "limitation": "Small holdout; still the same rule family.",
        "role": "demo_core",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "llm_agent_api_review_001",
        "path": "outputs/mvp_vertical_slice/llm_agent_api_review_001",
        "supported_claim": "OpenAI-compatible RightCode GPT output is skill-conditioned in the controlled matrix.",
        "key_result": "gpt-5.5 compact_v1 outputs R001-R004; compact_v2 outputs R001-R006 on case001/case002.",
        "limitation": "Small matrix; not a model stability or capability benchmark.",
        "role": "demo_core",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "output_format_error_001",
        "path": "outputs/mvp_vertical_slice/output_format_error_001",
        "supported_claim": "Failure-to-patch mapping can distinguish output contract errors from missing domain rules.",
        "key_result": "output_format_error maps to OUTPUT_CONTRACT and rewrite_output_contract.",
        "limitation": "Second vertical slice only; not a full failure taxonomy.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "counterfactual_patch_utility_001",
        "path": "outputs/mvp_vertical_slice/counterfactual_patch_utility_001",
        "supported_claim": "Correct failure attribution plus correct patch action has explanatory value over no/random/wrong-type patch in toy counterfactuals.",
        "key_result": "compiler_patch resolves missing_rule; output_contract_patch resolves format failure while wrong missing-rule patch does not.",
        "limitation": "Toy counterfactual; not statistical evidence for a general patch compiler.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "fixed_budget_compiler_001",
        "path": "outputs/mvp_vertical_slice/fixed_budget_compiler_001",
        "supported_claim": "Execution-aware fixed-budget selection can recover failure-critical rules without simple append.",
        "key_result": "execution-aware-fixed-budget recovers R005/R006 under budget but drops R003.",
        "limitation": "Regression remains; selector alone is insufficient.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "rollback_gate_001",
        "path": "outputs/mvp_vertical_slice/rollback_gate_001",
        "supported_claim": "Validation gate can reject patches that resolve the original failure but introduce regressions.",
        "key_result": "patch recovers R005/R006 but loses R003; gate rejects and rolls back.",
        "limitation": "Toy gate; not a mature rollback system.",
        "role": "method_exploration",
        "claim_strength": "supported",
    },
    {
        "artifact": "validation_aware_compiler_001",
        "path": "outputs/mvp_vertical_slice/validation_aware_compiler_001",
        "supported_claim": "Validation-aware recompilation can avoid the fixed-budget regression when compressed wording is allowed.",
        "key_result": "candidate_C compressed required rules fits budget and covers R001-R006.",
        "limitation": "Success depends on compressed wording; needs semantic audit.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "semantic_preservation_audit_001",
        "path": "outputs/mvp_vertical_slice/semantic_preservation_audit_001",
        "supported_claim": "Compressed candidate_C is not merely a rule-id shortcut in the toy slice.",
        "key_result": "semantic_preservation_status preserved for R001-R006.",
        "limitation": "Keyword/field audit, not deep semantic judgment.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "skill_to_agent_loop_001",
        "path": "outputs/mvp_vertical_slice/skill_to_agent_loop_001",
        "supported_claim": "Invocation protocol and trace verifier can distinguish rule-id shortcut from rule application evidence.",
        "key_result": "protocolized compressed skill passes trace verifier; shortcut/plain compressed variants fail strict trace.",
        "limitation": "Toy protocol; not universal across agents/tasks.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "traceable_compiler_integration_001",
        "path": "outputs/mvp_vertical_slice/traceable_compiler_integration_001",
        "supported_claim": "Rules plus invocation protocol plus trace contract forms a traceable deployment artifact, but full protocol overhead can exceed budget.",
        "key_result": "protocolized variant passes trace verification but is 300/237 tokens; validation gate rejects over budget.",
        "limitation": "Integration toy slice; exposes overhead rather than solving it.",
        "role": "platform_maturation",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "real_effect_eval_001",
        "path": "outputs/mvp_vertical_slice/real_effect_eval_001",
        "supported_claim": "Patched compact skill improves controlled API-review holdout behavior over compact_v1.",
        "key_result": "compact_v1 avg coverage 0.58; patched_compact avg coverage 1.00 on 4 cases.",
        "limitation": "4-case controlled holdout; not a benchmark or real-world generalization proof.",
        "role": "platform_maturation",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "selective_trace_compiler_001",
        "path": "outputs/mvp_vertical_slice/selective_trace_compiler_001",
        "supported_claim": "Selective trace can reduce protocol overhead while preserving traceability for failure-critical rules.",
        "key_result": "full_trace 300/237 rejected; selective_trace R005/R006 183/237 accepted and blocks shortcut.",
        "limitation": "Toy trace policy; not mature tracing strategy.",
        "role": "platform_maturation",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "component_baseline_direct_summary_001",
        "path": "outputs/mvp_vertical_slice/component_baseline_direct_summary_001",
        "supported_claim": "Component attribution can compare structured deployment against a plain direct-summary skill.",
        "key_result": "direct_summary_skill avg coverage 0.92; patched_compact avg coverage 1.00 on 4 controlled cases.",
        "limitation": "Deterministic component attribution slice; not a benchmark and not broad evidence against summarization baselines.",
        "role": "platform_maturation",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "risk_trace_policy_baseline_001",
        "path": "outputs/mvp_vertical_slice/risk_trace_policy_baseline_001",
        "supported_claim": "Risk signals can allocate a fixed selective-trace budget to failure-critical rules better than a same-size random trace in this toy slice.",
        "key_result": "random_selective_trace R002/R003 gives failure-critical trace coverage 0.00; risk_based_selective_trace R005/R006 gives 1.00 at the same 183/237 token cost.",
        "limitation": "Single random seed and tiny rule pool; not statistical evidence for a mature risk policy.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "risk_trace_policy_robustness_001",
        "path": "outputs/mvp_vertical_slice/risk_trace_policy_robustness_001",
        "supported_claim": "Risk-based selective trace does not rely only on one random seed in the current toy rule pool.",
        "key_result": "Among all 15 size=2 trace allocations, only R005/R006 covers both failure-critical rules; risk-based selection picks R005/R006.",
        "limitation": "Complete enumeration of a tiny toy rule pool; not statistical significance or mature policy validation.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "direct_summary_miss_analysis_001",
        "path": "outputs/mvp_vertical_slice/direct_summary_miss_analysis_001",
        "supported_claim": "The direct-summary miss is a residual deployment-critical idempotency rule rather than broad summary failure.",
        "key_result": "Direct summary fails only case004 by missing R006; patched_compact includes R006 and passes.",
        "limitation": "One explanatory miss case; not a general long-tail failure pattern.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "adversarial_trace_verifier_001",
        "path": "outputs/mvp_vertical_slice/adversarial_trace_verifier_001",
        "supported_claim": "Trace verifier has basic adversarial sanity checks against obvious fake or weak rule-application evidence.",
        "key_result": "Valid control passes; fake evidence span, generic trigger, mismatched finding_id, and rule-id-only trace are rejected.",
        "limitation": "Toy adversarial checks only; not a deep semantic verifier or proof against sophisticated fake evidence.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "revision_decision_matrix_001",
        "path": "outputs/mvp_vertical_slice/revision_decision_matrix_001",
        "supported_claim": "The prototype is better framed as constrained post-execution skill revision rather than simple budget checking.",
        "key_result": "Different feedback/risk types map to different constrained decisions: patch rule, rewrite output contract, reject/rollback, semantic audit, trace contract, verifier strengthening, or selective trace.",
        "limitation": "Mechanism matrix over existing toy artifacts only; not a mature revision algorithm.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "posterior_revision_signal_audit_001",
        "path": "outputs/mvp_vertical_slice/posterior_revision_signal_audit_001",
        "supported_claim": "Post-execution evidence can be audited as a revision signal that changes patch, gate, and trace decisions beyond prior skill generation.",
        "key_result": "patched_compact improves coverage over compact_v1 by 0.4166 and over direct_summary by 0.0833; type-correct missing-rule and output-contract patches beat wrong-type counterfactuals.",
        "limitation": "Audit over existing controlled API-review artifacts only; not a cross-domain posterior-revision metric.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "naive_revision_ablation_001",
        "path": "outputs/mvp_vertical_slice/naive_revision_ablation_001",
        "supported_claim": "Generic revision strategies are insufficient to explain the current deployment constraints in toy slices.",
        "key_result": "always_append fixes missing_rule but not output_format_error; always_contract fixes format but not missing_rule; always_full_trace is 300/237 over budget; type-specific operator plus gate/selective trace resolves all tested axes.",
        "limitation": "Diagnostic ablation over existing artifacts only; always_regenerate_full_skill remains a strong high-cost upper bound.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "second_domain_config_security_001",
        "path": "outputs/mvp_vertical_slice/second_domain_config_security_001",
        "supported_claim": "Typed posterior revision is not only an API-review surface artifact in the current minimal evidence.",
        "key_result": "In config-security, direct_summary coverage is 0.825 with residual C006 misses; always_append fails output contract; always_contract misses C006; accept-if-fixed regresses C003; full_trace/full_skill exceed budget; typed+gate+selective_trace passes 4/4 at 166/260.",
        "limitation": "Hand-constructed second-domain probe; not a benchmark, not cross-domain proof, and not evidence against full regeneration when cost is ignored.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "operator_transfer_audit_001",
        "path": "outputs/mvp_vertical_slice/operator_transfer_audit_001",
        "supported_claim": "The config-security slice reuses the frozen API-review typed revision skeleton rather than inventing a wholly new flow.",
        "key_result": "missing_rule, output_contract_error, regression_observed, and trace_budget_pressure reuse the same operators/gates; domain-specific parts are rule semantics, config_path, and C006 trace target.",
        "limitation": "Transfer audit over a hand-constructed second domain; not proof of arbitrary domain transfer.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
    {
        "artifact": "prior_posterior_split_001",
        "path": "outputs/mvp_vertical_slice/prior_posterior_split_001",
        "supported_claim": "Prior expert-material signals and posterior verifier signals play different roles in revision decisions.",
        "key_result": "Prior signals build initial skills and cover salient rules; posterior signals identify residual deployment-critical misses, wrong repair type, regression, and trace-budget pressure across two controlled domains.",
        "limitation": "Diagnostic split, not causal proof; prior-only is represented by controlled baselines, not exhaustive prior optimization.",
        "role": "method_exploration",
        "claim_strength": "partially_supported",
    },
]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Artifact Claim Audit 001",
        "",
        "## Purpose",
        "",
        "Audit what each core artifact can safely support, and prevent overclaiming before demo/report use.",
        "",
        "| Artifact | Role | Claim Strength | Key Result | Limitation |",
        "|---|---|---|---|---|",
    ]
    for item in payload["artifacts"]:
        lines.append(
            f"| {item['artifact']} | {item['role']} | {item['claim_strength']} | "
            f"{item['key_result']} | {item['limitation']} |"
        )
    lines.extend(
        [
            "",
            "## Safe Main Claim",
            "",
            payload["safe_main_claim"],
            "",
            "## Boundary",
            "",
            payload["boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    missing = [item["artifact"] for item in ARTIFACTS if not Path(item["path"]).exists()]
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "status": "ok" if not missing else "missing_artifacts",
        "missing_artifacts": missing,
        "safe_main_claim": (
            "The prototype demonstrates a risk-budgeted traceable skill deployment loop in a controlled API-review family: "
            "expert materials become evidence-grounded skills, verifier feedback drives patch proposals, validation gates prevent "
            "regression or over-budget deployment, and selective trace focuses rule-application evidence on high-risk rules."
        ),
        "boundary": (
            "This is not a benchmark, not a universal skill compiler, and not evidence of superiority over related work. "
            "Current claims are controlled-family and toy-slice claims."
        ),
        "artifacts": ARTIFACTS,
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "manifest.json"],
            "status": payload["status"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": payload["status"]}, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
