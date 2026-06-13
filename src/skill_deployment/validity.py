from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_SUPPORTED = "supported"
STATUS_PARTIAL = "partially_supported"
STATUS_PENDING = "manual_review_pending"
STATUS_NOT_MEASURED = "not_measured"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def metric(status: str, note: str) -> dict[str, str]:
    return {"status": status, "note": note}


def build_repair_loop_validity_card(
    *,
    card_id: str,
    artifact: str,
    scenario: str,
    backend: str,
    a1_report: dict[str, Any],
    a2_report: dict[str, Any],
    patch_plan: dict[str, Any],
    gate_decision: dict[str, Any],
    sources: list[str],
    claim_boundary: str,
    grounded_agent_artifacts: bool,
    repeatability_note: str = "Not measured for this single loop artifact.",
    transferability_note: str = "Single controlled task slice only.",
    cost_budget_note: str = "Latency and token usage are available in backend metadata/model_calls but not normalized here.",
) -> dict[str, Any]:
    a1_pass = bool(a1_report.get("pass", False))
    a2_pass = bool(a2_report.get("pass", False))
    reward_delta = float(a2_pass) - float(a1_pass)
    feedback_type = str(a1_report.get("feedback_type", "unknown"))
    repair_action = str(patch_plan.get("repair_action", "unknown"))
    gate = str(gate_decision.get("decision", "unknown"))
    missing_before = [str(item) for item in a1_report.get("missing_capabilities", [])]
    missing_after = [str(item) for item in a2_report.get("missing_capabilities", [])]
    schema_before = [str(item) for item in a1_report.get("schema_errors", [])]
    schema_after = [str(item) for item in a2_report.get("schema_errors", [])]
    weak_before = [str(item) for item in a1_report.get("weak_evidence_capabilities", [])]
    weak_after = [str(item) for item in a2_report.get("weak_evidence_capabilities", [])]
    return {
        "card_id": card_id,
        "artifact": artifact,
        "scope": f"Controlled repair loop for {scenario} on backend {backend}.",
        "metrics": {
            "outcome_delta": metric(
                STATUS_SUPPORTED if (not a1_pass and a2_pass) else STATUS_PARTIAL,
                f"A1 pass={a1_pass}, A2 pass={a2_pass}, reward_delta={reward_delta:+.1f}.",
            ),
            "evidence_grounding": metric(
                STATUS_SUPPORTED if grounded_agent_artifacts else STATUS_PARTIAL,
                "Agent artifacts show prompt/report/model-call landing and deterministic verifier reads them."
                if grounded_agent_artifacts
                else "Verifier outcomes exist, but direct target-grounding artifacts are incomplete.",
            ),
            "repair_attribution": metric(
                STATUS_SUPPORTED,
                f"A1 feedback `{feedback_type}` triggered repair `{repair_action}` and gate `{gate}`.",
            ),
            "regression_safety": metric(
                STATUS_SUPPORTED if not missing_after and not schema_after and not weak_after else STATUS_PARTIAL,
                f"After repair: missing={missing_after or ['none']}, schema_errors={schema_after or ['none']}, weak_evidence={weak_after or ['none']}.",
            ),
            "transferability": metric(STATUS_PARTIAL, transferability_note),
            "repeatability": metric(STATUS_NOT_MEASURED, repeatability_note),
            "cost_budget": metric(STATUS_PARTIAL, cost_budget_note),
            "verifier_robustness": metric(
                STATUS_PARTIAL,
                f"Verifier distinguished A1 vs A2; before repair missing={missing_before or ['none']}, schema_errors={schema_before or ['none']}, weak_evidence={weak_before or ['none']}.",
            ),
            "human_plausibility": metric(STATUS_PENDING, "No human usefulness review is attached to this loop artifact."),
        },
        "summary": {
            "scenario": scenario,
            "backend": backend,
            "a1_pass": a1_pass,
            "a2_pass": a2_pass,
            "reward_delta": reward_delta,
            "feedback_type": feedback_type,
            "repair_action": repair_action,
            "gate_decision": gate,
        },
        "claim_boundary": claim_boundary,
        "sources": sources,
    }


def build_skill_revision_validity_cards(root: Path) -> dict[str, Any]:
    validation_dir = root / "outputs" / "validation"
    generalization = load_json(validation_dir / "generalization_suite.json")
    non_oracle = load_json(validation_dir / "non_oracle_local_suite.json")
    negative = load_json(validation_dir / "negative_controls.json")
    ablation = load_json(validation_dir / "ablation_summary.json")
    repeatability = load_json(validation_dir / "harbor_llm_repeatability_upload.json")
    local_upload_dir = root / "outputs" / "live_llm_repair_loop_upload_001"
    local_config_dir = root / "outputs" / "live_llm_repair_loop_config_security_001"
    local_api_dir = root / "outputs" / "live_llm_repair_loop_api_review_001"
    local_data_quality_dir = root / "outputs" / "live_llm_repair_loop_data_quality_001"
    local_cards: list[dict[str, Any]] = []
    if (local_upload_dir / "summary.json").exists():
        local_cards.append(
            build_repair_loop_validity_card(
                card_id="live_llm_upload_repair_loop",
                artifact="outputs/live_llm_repair_loop_upload_001",
                scenario="upload_security_001",
                backend="live_llm_text",
                a1_report=load_json(local_upload_dir / "A1" / "verifier_report.json"),
                a2_report=load_json(local_upload_dir / "A2" / "verifier_report.json"),
                patch_plan=load_json(local_upload_dir / "revision" / "patch_plan.json"),
                gate_decision=load_json(local_upload_dir / "revision" / "gate_decision.json"),
                sources=[
                    "outputs/live_llm_repair_loop_upload_001/A1/verifier_report.json",
                    "outputs/live_llm_repair_loop_upload_001/revision/patch_plan.json",
                    "outputs/live_llm_repair_loop_upload_001/revision/gate_decision.json",
                    "outputs/live_llm_repair_loop_upload_001/A2/verifier_report.json",
                    "outputs/live_llm_repair_loop_upload_001/A1/security_report.json",
                    "outputs/live_llm_repair_loop_upload_001/A2/security_report.json",
                ],
                claim_boundary="Single local live-LLM repair-loop evidence on one controlled upload task; verifier and gate remain deterministic.",
                grounded_agent_artifacts=True,
                transferability_note="Single controlled security slice only.",
            )
        )
    if (local_data_quality_dir / "summary.json").exists():
        local_cards.append(
            build_repair_loop_validity_card(
                card_id="live_llm_data_quality_repair_loop",
                artifact="outputs/live_llm_repair_loop_data_quality_001",
                scenario="data_quality_review_001",
                backend="live_llm_text",
                a1_report=load_json(local_data_quality_dir / "A1" / "verifier_report.json"),
                a2_report=load_json(local_data_quality_dir / "A2" / "verifier_report.json"),
                patch_plan=load_json(local_data_quality_dir / "revision" / "patch_plan.json"),
                gate_decision=load_json(local_data_quality_dir / "revision" / "gate_decision.json"),
                sources=[
                    "outputs/live_llm_repair_loop_data_quality_001/A1/verifier_report.json",
                    "outputs/live_llm_repair_loop_data_quality_001/revision/patch_plan.json",
                    "outputs/live_llm_repair_loop_data_quality_001/revision/gate_decision.json",
                    "outputs/live_llm_repair_loop_data_quality_001/A2/verifier_report.json",
                    "outputs/live_llm_repair_loop_data_quality_001/A1/security_report.json",
                    "outputs/live_llm_repair_loop_data_quality_001/A2/security_report.json",
                ],
                claim_boundary="Single local live-LLM repair-loop evidence on one controlled non-security data-quality task; verifier and gate remain deterministic.",
                grounded_agent_artifacts=True,
                transferability_note="One controlled non-security slice only; not broad multi-domain generalization.",
            )
        )
    if (local_config_dir / "summary.json").exists():
        local_cards.append(
            build_repair_loop_validity_card(
                card_id="live_llm_config_security_repair_loop",
                artifact="outputs/live_llm_repair_loop_config_security_001",
                scenario="config_security_001",
                backend="live_llm_text",
                a1_report=load_json(local_config_dir / "A1" / "verifier_report.json"),
                a2_report=load_json(local_config_dir / "A2" / "verifier_report.json"),
                patch_plan=load_json(local_config_dir / "revision" / "patch_plan.json"),
                gate_decision=load_json(local_config_dir / "revision" / "gate_decision.json"),
                sources=[
                    "outputs/live_llm_repair_loop_config_security_001/A1/verifier_report.json",
                    "outputs/live_llm_repair_loop_config_security_001/revision/patch_plan.json",
                    "outputs/live_llm_repair_loop_config_security_001/revision/gate_decision.json",
                    "outputs/live_llm_repair_loop_config_security_001/A2/verifier_report.json",
                    "outputs/live_llm_repair_loop_config_security_001/A1/security_report.json",
                    "outputs/live_llm_repair_loop_config_security_001/A2/security_report.json",
                ],
                claim_boundary="Single local live-LLM repair-loop evidence on one controlled configuration-security task; verifier and gate remain deterministic.",
                grounded_agent_artifacts=True,
                transferability_note="Second local controlled security slice only; not broad live-LLM security-task generalization.",
            )
        )
    if (local_api_dir / "summary.json").exists():
        local_cards.append(
            build_repair_loop_validity_card(
                card_id="live_llm_api_review_repair_loop",
                artifact="outputs/live_llm_repair_loop_api_review_001",
                scenario="api_review_001",
                backend="live_llm_text",
                a1_report=load_json(local_api_dir / "A1" / "verifier_report.json"),
                a2_report=load_json(local_api_dir / "A2" / "verifier_report.json"),
                patch_plan=load_json(local_api_dir / "revision" / "patch_plan.json"),
                gate_decision=load_json(local_api_dir / "revision" / "gate_decision.json"),
                sources=[
                    "outputs/live_llm_repair_loop_api_review_001/A1/verifier_report.json",
                    "outputs/live_llm_repair_loop_api_review_001/revision/patch_plan.json",
                    "outputs/live_llm_repair_loop_api_review_001/revision/gate_decision.json",
                    "outputs/live_llm_repair_loop_api_review_001/A2/verifier_report.json",
                    "outputs/live_llm_repair_loop_api_review_001/A1/security_report.json",
                    "outputs/live_llm_repair_loop_api_review_001/A2/security_report.json",
                ],
                claim_boundary="Single local live-LLM repair-loop evidence on one controlled API/code-review task; verifier and gate remain deterministic.",
                grounded_agent_artifacts=True,
                transferability_note="Third local controlled slice only; not broad live-LLM task generalization.",
            )
        )
    harbor_upload_summary = load_json(root / "outputs" / "harbor_llm_repair_loop_upload_001" / "summary.json")
    harbor_upload_card = build_repair_loop_validity_card(
        card_id="harbor_llm_upload_repair_loop",
        artifact="outputs/harbor_llm_repair_loop_upload_001",
        scenario="real-upload-security-review",
        backend="harbor_llm_repair_upload_replay",
        a1_report=harbor_upload_summary["A1"],
        a2_report=harbor_upload_summary["A2"],
        patch_plan=load_json(root / "outputs" / "harbor_llm_repair_loop_upload_001" / "revision" / "patch_plan.json"),
        gate_decision=load_json(root / "outputs" / "harbor_llm_repair_loop_upload_001" / "revision" / "gate_decision.json"),
        sources=[
            "outputs/harbor_llm_repair_loop_upload_001/A1/verifier_report.json",
            "outputs/harbor_llm_repair_loop_upload_001/revision/patch_plan.json",
            "outputs/harbor_llm_repair_loop_upload_001/revision/gate_decision.json",
            "outputs/harbor_llm_repair_loop_upload_001/A2/verifier_report.json",
            "outputs/harbor_llm_repair_loop_upload_001/A1/security_report.json",
            "outputs/harbor_llm_repair_loop_upload_001/A2/security_report.json",
            "outputs/harbor_llm_repair_loop_upload_001/A1/target_reads.json",
            "outputs/harbor_llm_repair_loop_upload_001/A2/target_reads.json",
        ],
        claim_boundary="Controlled single-scenario Harbor LLM repair-loop evidence, not general Harbor LLM security capability.",
        grounded_agent_artifacts=True,
        repeatability_note="Supported by the separate three-run upload repeatability smoke.",
        transferability_note="Single Harbor upload slice only; cross-task transfer is evidenced separately and remains narrow.",
        cost_budget_note="Prompt, response, usage, and Harbor job artifacts are stored, but no normalized cost table is computed here.",
    )
    harbor_config_summary = load_json(root / "outputs" / "harbor_llm_repair_loop_config_001" / "summary.json")
    harbor_config_card = build_repair_loop_validity_card(
        card_id="harbor_llm_config_repair_loop",
        artifact="outputs/harbor_llm_repair_loop_config_001",
        scenario="controlled-config-security-review",
        backend="harbor_llm_repair_config_replay",
        a1_report=harbor_config_summary["A1"],
        a2_report=harbor_config_summary["A2"],
        patch_plan=load_json(root / "outputs" / "harbor_llm_repair_loop_config_001" / "revision" / "patch_plan.json"),
        gate_decision=load_json(root / "outputs" / "harbor_llm_repair_loop_config_001" / "revision" / "gate_decision.json"),
        sources=[
            "outputs/harbor_llm_repair_loop_config_001/A1/verifier_report.json",
            "outputs/harbor_llm_repair_loop_config_001/revision/patch_plan.json",
            "outputs/harbor_llm_repair_loop_config_001/revision/gate_decision.json",
            "outputs/harbor_llm_repair_loop_config_001/A2/verifier_report.json",
            "outputs/harbor_llm_repair_loop_config_001/A1/security_report.json",
            "outputs/harbor_llm_repair_loop_config_001/A2/security_report.json",
            "outputs/harbor_llm_repair_loop_config_001/A1/target_reads.json",
            "outputs/harbor_llm_repair_loop_config_001/A2/target_reads.json",
        ],
        claim_boundary="Second-task Harbor LLM evidence, still controlled and narrow.",
        grounded_agent_artifacts=True,
        transferability_note="Second distinct Harbor task family, but still narrow controlled evidence.",
        cost_budget_note="Harbor prompt/response/job artifacts exist, but no normalized cost table is computed here.",
    )

    cards = [
        *local_cards,
        {
            "card_id": "offline_generalization_suite",
            "artifact": "outputs/validation/generalization_suite.json",
            "scope": "Five controlled task families through one offline_deterministic lifecycle.",
            "metrics": {
                "outcome_delta": metric(STATUS_SUPPORTED, f"A2 passes {generalization['a2_pass_count']}/{generalization['scenario_count']} controlled tasks."),
                "evidence_grounding": metric(STATUS_PARTIAL, "Verifier checks evidence fields, but the offline agent path still emits deterministic capability/evidence hints rather than target-grounded reads."),
                "repair_attribution": metric(STATUS_SUPPORTED, "Each scenario records A1 feedback type and a distinct repair action before A2."),
                "regression_safety": metric(STATUS_PARTIAL, "Regression is measured by verifier score and strengthened by separate negative controls, not by a broad held-out clean-target suite."),
                "transferability": metric(STATUS_SUPPORTED, "The same offline suite spans upload, auth, config, API review, and one non-security data-quality task."),
                "repeatability": metric(STATUS_SUPPORTED, "The offline path is deterministic and artifact-backed; reruns should be stable modulo timestamps."),
                "cost_budget": metric(STATUS_PARTIAL, "Per-scenario summaries include latency; cost_budget_score is synthetic rather than measured from real model/token usage."),
                "verifier_robustness": metric(STATUS_PARTIAL, "Robustness is supported only indirectly here; explicit unsupported-evidence/false-positive checks live in negative_controls.json."),
                "human_plausibility": metric(STATUS_PENDING, "No systematic human rating is stored for whether A2 reports are materially more useful than A1."),
            },
            "claim_boundary": "Strong controlled lifecycle evidence, not open-world semantic quality evidence.",
            "sources": [
                "outputs/validation/generalization_suite.json",
                "runs/generalization/*/verifier/A1_report.json",
                "runs/generalization/*/revision/repair_decision.json",
            ],
        },
        {
            "card_id": "non_oracle_local_semantic_suite",
            "artifact": "outputs/validation/non_oracle_local_suite.json",
            "scope": "Deterministic non-oracle local semantic backend over five controlled task families.",
            "metrics": {
                "outcome_delta": metric(STATUS_PARTIAL, "A2 passes 5/5, but only upload shows a repair loop; four tasks already pass at A1."),
                "evidence_grounding": metric(STATUS_SUPPORTED, "The backend reads target text, emits trace.jsonl read events, and grounds findings with detector hits."),
                "repair_attribution": metric(STATUS_PARTIAL, "Only upload currently demonstrates verifier-triggered capability repair on this backend."),
                "regression_safety": metric(STATUS_PARTIAL, "No dedicated clean-target local-semantic regression suite is stored yet."),
                "transferability": metric(STATUS_PARTIAL, "The interface spans five families, but feedback diversity is low: only pass/no_op and one missing_capability case."),
                "repeatability": metric(STATUS_SUPPORTED, "This path is deterministic heuristic code with stable target reads."),
                "cost_budget": metric(STATUS_SUPPORTED, "Latency is small and there is no external token cost."),
                "verifier_robustness": metric(STATUS_PARTIAL, "Verifier remains deterministic; robustness against semantic-but-wrong heuristics is only lightly tested."),
                "human_plausibility": metric(STATUS_PENDING, "No manual review card exists for whether the heuristic reports are meaningfully useful beyond contract compliance."),
            },
            "claim_boundary": "Backend-interface and target-grounding evidence, not proof of autonomous semantic reasoning.",
            "sources": [
                "outputs/validation/non_oracle_local_suite.json",
                "agents/non_oracle_local_security_agent.py",
            ],
        },
        {
            "card_id": "negative_controls",
            "artifact": "outputs/validation/negative_controls.json",
            "scope": "Controlled checks for unsupported evidence and false-positive rejection.",
            "metrics": {
                "outcome_delta": metric(STATUS_NOT_MEASURED, "This slice is about verifier refusal behavior, not task improvement."),
                "evidence_grounding": metric(STATUS_SUPPORTED, "Unsupported evidence is explicitly rejected when evidence_span is absent from the target."),
                "repair_attribution": metric(STATUS_PARTIAL, "The clean-config control demonstrates gate behavior after a false-positive style repair, but not a full A1/A2 loop."),
                "regression_safety": metric(STATUS_SUPPORTED, "Always-append findings are rejected on a clean config; empty typed output can pass when expected issue set is empty."),
                "transferability": metric(STATUS_PARTIAL, "Only two negative controls exist so far."),
                "repeatability": metric(STATUS_SUPPORTED, "These controls are deterministic and should be exactly reproducible."),
                "cost_budget": metric(STATUS_SUPPORTED, "No external model cost is involved."),
                "verifier_robustness": metric(STATUS_SUPPORTED, "This is the strongest direct evidence that verifier/gate can reject unsupported evidence and false positives."),
                "human_plausibility": metric(STATUS_PENDING, "No human audit artifacts accompany the negative controls."),
            },
            "claim_boundary": "Narrow robustness evidence for two adversarial patterns, not a broad adversarial verification benchmark.",
            "sources": ["outputs/validation/negative_controls.json"],
        },
        {
            "card_id": "ablation_summary",
            "artifact": "outputs/validation/ablation_summary.json",
            "scope": "Controlled strategy comparison across upload and config tasks.",
            "metrics": {
                "outcome_delta": metric(STATUS_SUPPORTED, "Typed repair plus gate reaches PASS on both scenarios; naive strategies fail or incur regressions on config."),
                "evidence_grounding": metric(STATUS_PARTIAL, "Ablation reuses the same controlled verifier path; it does not independently validate semantic grounding."),
                "repair_attribution": metric(STATUS_SUPPORTED, "Different repair choices produce measurably different outcomes under the same inputs."),
                "regression_safety": metric(STATUS_SUPPORTED, "Always-append and naive-regenerate show regression_count > 0 on config; gate rejects those paths."),
                "transferability": metric(STATUS_PARTIAL, "Only two scenarios are included in the executable ablation."),
                "repeatability": metric(STATUS_SUPPORTED, "The ablation is deterministic."),
                "cost_budget": metric(STATUS_PARTIAL, "Synthetic cost_budget_score differentiates strategies, but it is not calibrated to true runtime or token spend."),
                "verifier_robustness": metric(STATUS_PARTIAL, "The verifier distinguishes regressions here, but broader adversarial checks remain outside this table."),
                "human_plausibility": metric(STATUS_PENDING, "No human comparison of strategy outputs is recorded."),
            },
            "claim_boundary": "Useful controlled attribution evidence, not a benchmark-scale ablation.",
            "sources": ["outputs/validation/ablation_summary.json"],
        },
        harbor_upload_card,
        harbor_config_card,
        {
            "card_id": "harbor_llm_upload_repeatability",
            "artifact": "outputs/validation/harbor_llm_repeatability_upload.json",
            "scope": "Three-run repeatability smoke for the Harbor upload LLM repair loop.",
            "metrics": {
                "outcome_delta": metric(STATUS_SUPPORTED, "All three runs show A1 fail and A2 pass with reward delta +1.0."),
                "evidence_grounding": metric(STATUS_PARTIAL, "Repeatability summarizes verifier outcomes and model usage; grounding remains delegated to the underlying run artifacts."),
                "repair_attribution": metric(STATUS_SUPPORTED, "Failure reason and missing-capability set are stable across repeats."),
                "regression_safety": metric(STATUS_PARTIAL, "This slice checks stability of the same loop, not regression on unrelated clean tasks."),
                "transferability": metric(STATUS_NOT_MEASURED, "Repeatability is measured only on upload."),
                "repeatability": metric(STATUS_SUPPORTED, "A1 all fail, A2 all pass, reward stable, failure reason stable across three runs."),
                "cost_budget": metric(STATUS_SUPPORTED, repeatability["token_latency_assessment"]),
                "verifier_robustness": metric(STATUS_PARTIAL, "Stable failure types reduce the chance of arbitrary verifier drift, but do not exhaust robustness concerns."),
                "human_plausibility": metric(STATUS_PENDING, "No repeated human evaluation accompanies the loop repeats."),
            },
            "claim_boundary": "Small repeatability smoke for one Harbor upload loop, not a broad prompt-sensitivity study.",
            "sources": ["outputs/validation/harbor_llm_repeatability_upload.json"],
        },
    ]
    return {
        "generated_at": utc_now(),
        "card_count": len(cards),
        "status_vocab": [STATUS_SUPPORTED, STATUS_PARTIAL, STATUS_NOT_MEASURED, STATUS_PENDING],
        "cards": cards,
    }


def render_skill_revision_validity_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Skill Revision Validity Card Status",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This file does not collapse everything into one score. It records which parts of the current evidence are genuinely supported, only partially supported, not measured, or still waiting on human review.",
        "",
    ]
    for card in payload["cards"]:
        lines.extend(
            [
                f"## {card['card_id']}",
                "",
                f"- Artifact: `{card['artifact']}`",
                f"- Scope: {card['scope']}",
                f"- Claim boundary: {card['claim_boundary']}",
                "",
                "| Dimension | Status | Note |",
                "|---|---|---|",
            ]
        )
        for name, item in card["metrics"].items():
            lines.append(f"| {name} | {item['status']} | {item['note']} |")
        lines.extend(["", f"- Sources: {', '.join(f'`{source}`' for source in card['sources'])}", ""])
    return "\n".join(lines) + "\n"


def render_single_validity_card_markdown(card: dict[str, Any]) -> str:
    lines = [
        f"# {card['card_id']}",
        "",
        f"- Artifact: `{card['artifact']}`",
        f"- Scope: {card['scope']}",
        f"- Claim boundary: {card['claim_boundary']}",
        "",
        "| Dimension | Status | Note |",
        "|---|---|---|",
    ]
    for name, item in card["metrics"].items():
        lines.append(f"| {name} | {item['status']} | {item['note']} |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Scenario: `{card['summary']['scenario']}`",
            f"- Backend: `{card['summary']['backend']}`",
            f"- A1 pass: `{card['summary']['a1_pass']}`",
            f"- A2 pass: `{card['summary']['a2_pass']}`",
            f"- Reward delta: `{card['summary']['reward_delta']:+.1f}`",
            f"- Feedback type: `{card['summary']['feedback_type']}`",
            f"- Repair action: `{card['summary']['repair_action']}`",
            f"- Gate decision: `{card['summary']['gate_decision']}`",
            "",
            f"- Sources: {', '.join(f'`{source}`' for source in card['sources'])}",
            "",
        ]
    )
    return "\n".join(lines)
