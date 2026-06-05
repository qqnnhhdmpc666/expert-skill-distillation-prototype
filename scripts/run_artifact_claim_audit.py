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
