from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/revision_decision_matrix_001")

MATRIX: list[dict[str, Any]] = [
    {
        "feedback_or_risk": "missing_rule",
        "naive_action": "append_more_rules",
        "constrained_decision": "patch affected missing rules; compare against no/random/wrong-type patches",
        "primary_action": "patch_rule",
        "counterfactual": "no_patch / random_patch / wrong_type_patch fail; compiler_patch recovers R005/R006",
        "supporting_artifacts": ["counterfactual_patch_utility_001", "harbor_api_review_001", "harbor_api_review_002"],
        "key_result": "compiler_patch resolves missing_rule while no/random/wrong-type variants do not in the toy slice.",
        "claim_strength": "partially_supported",
        "limitation": "small rule pool; random can hit affected rules by chance",
    },
    {
        "feedback_or_risk": "output_format_error",
        "naive_action": "append_domain_rules",
        "constrained_decision": "rewrite output contract instead of patching domain rules",
        "primary_action": "rewrite_output_contract",
        "counterfactual": "wrong_missing_rule_patch does not resolve output_format_error; output_contract_patch resolves format failure",
        "supporting_artifacts": ["output_format_error_001", "counterfactual_patch_utility_001"],
        "key_result": "format failure maps to OUTPUT_CONTRACT rather than R005/R006 domain-rule patch.",
        "claim_strength": "partially_supported",
        "limitation": "second failure taxonomy slice only; not full taxonomy benchmark",
    },
    {
        "feedback_or_risk": "regression_observed",
        "naive_action": "accept_if_original_failure_fixed",
        "constrained_decision": "reject and rollback if patch loses previously covered rules",
        "primary_action": "reject_and_rollback",
        "counterfactual": "patch fixes R005/R006 but drops R003, so gate rejects",
        "supporting_artifacts": ["rollback_gate_001"],
        "key_result": "gate rejects a patch that resolves original failure but regresses holdout coverage.",
        "claim_strength": "supported_in_toy_slice",
        "limitation": "single constructed regression example",
    },
    {
        "feedback_or_risk": "semantic_compressed",
        "naive_action": "trust_shorter_rule_text",
        "constrained_decision": "audit trigger/action/output semantics and execute compressed candidate",
        "primary_action": "semantic_preservation_audit",
        "counterfactual": "rule-id shortcut risk requires semantic audit and execution validation",
        "supporting_artifacts": ["semantic_preservation_audit_001", "compressed_candidate_execution_001"],
        "key_result": "candidate_C is judged preserved in the toy audit and passes mock/GPT execution checks.",
        "claim_strength": "partially_supported",
        "limitation": "keyword/field audit, not deep semantic judgment",
    },
    {
        "feedback_or_risk": "rule_id_shortcut",
        "naive_action": "trust_rule_id_coverage",
        "constrained_decision": "require rule_application trace evidence",
        "primary_action": "add_invocation_protocol_and_trace_contract",
        "counterfactual": "plain compressed and shortcut variants pass simple coverage but fail trace verifier",
        "supporting_artifacts": ["skill_to_agent_loop_001", "traceable_compiler_integration_001"],
        "key_result": "protocolized compressed skill passes trace verifier; shortcut/plain variants fail strict trace.",
        "claim_strength": "partially_supported",
        "limitation": "protocol overhead can exceed budget",
    },
    {
        "feedback_or_risk": "fake_trace_evidence",
        "naive_action": "trust_trace_fields",
        "constrained_decision": "reject fake span, generic trigger, mismatched finding_id, and rule-id-only trace",
        "primary_action": "strengthen_trace_verifier_contract",
        "counterfactual": "adversarial trace outputs are rejected while valid control passes",
        "supporting_artifacts": ["adversarial_trace_verifier_001"],
        "key_result": "valid control passes; four obvious fake/weak trace cases are rejected.",
        "claim_strength": "partially_supported",
        "limitation": "basic adversarial sanity check, not deep semantic verification",
    },
    {
        "feedback_or_risk": "trace_budget_pressure",
        "naive_action": "trace_all_or_trace_none",
        "constrained_decision": "allocate trace to failure-critical / newly patched rules",
        "primary_action": "risk_based_selective_trace",
        "counterfactual": "all size=2 allocations enumerated; only R005/R006 covers both failure-critical rules",
        "supporting_artifacts": ["risk_trace_policy_baseline_001", "risk_trace_policy_robustness_001"],
        "key_result": "risk-based trace selects R005/R006 at 183/237 tokens; full trace is 300/237 and over budget.",
        "claim_strength": "partially_supported",
        "limitation": "toy rule pool; not a mature or statistically validated policy",
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
        "# Revision Decision Matrix 001",
        "",
        "## Purpose",
        "",
        "Show that the current prototype is not merely checking token budget. It makes different constrained revision decisions for different post-execution feedback/risk types.",
        "",
        "| Feedback / Risk | Naive Action | Constrained Decision | Key Result | Claim Strength |",
        "|---|---|---|---|---|",
    ]
    for row in payload["matrix"]:
        lines.append(
            f"| {row['feedback_or_risk']} | {row['naive_action']} | {row['constrained_decision']} | "
            f"{row['key_result']} | {row['claim_strength']} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Conclusion",
            "",
            f"- Status: {payload['conclusion']['status']}",
            f"- Finding: {payload['conclusion']['finding']}",
            f"- Boundary: {payload['conclusion']['boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "core_reframing": "The core problem is not budget checking, but constrained post-execution skill revision.",
        "matrix": MATRIX,
        "conclusion": {
            "status": "partially_supported",
            "finding": (
                "Existing toy slices support a nontrivial decision-chain framing: different feedback types trigger different "
                "repair, gate, trace, or rollback decisions instead of simple budget-based append/reject."
            ),
            "boundary": "Mechanism matrix over existing toy artifacts only. This is not a mature revision algorithm or benchmark.",
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "decision_matrix.json", MATRIX)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "decision_matrix.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": payload["conclusion"]["status"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
