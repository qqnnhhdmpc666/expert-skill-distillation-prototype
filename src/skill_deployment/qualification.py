from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PASS = "pass"
PARTIAL = "partial"
FAIL = "fail"
NOT_MEASURED = "not_measured"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def gate(status: str, evidence: str, failure_origin: str | None = None) -> dict[str, str]:
    payload = {"status": status, "evidence": evidence}
    if failure_origin:
        payload["failure_origin"] = failure_origin
    return payload


def as_set(payload: dict[str, Any], key: str) -> set[str]:
    return {str(item) for item in payload.get(key, [])}


def repair_loop_card(
    *,
    card_id: str,
    artifact: str,
    scenario: str,
    backend: str,
    summary: dict[str, Any],
    sources: list[str],
    sandboxed: bool,
    repeatability: bool = False,
) -> dict[str, Any]:
    a1 = summary.get("A1", {})
    a2 = summary.get("A2", {})
    revision = summary.get("revision", {})
    a1_missing = as_set(a1, "missing_capabilities")
    a2_missing = as_set(a2, "missing_capabilities")
    a1_schema = as_set(a1, "schema_errors")
    a2_schema = as_set(a2, "schema_errors")
    action = str(revision.get("repair_action", "unknown"))
    before_caps = set(str(item) for item in revision.get("before_capabilities", []))
    after_caps = set(str(item) for item in revision.get("after_capabilities", []))
    gate_decision = str(revision.get("gate_decision", "accept"))
    a1_pass = bool(a1.get("pass", False))
    a2_pass = bool(a2.get("pass", False))
    coverage_delta = float(a2.get("coverage", 0.0)) - float(a1.get("coverage", 0.0))
    schema_delta = float(a2.get("schema_correctness", 0.0)) - float(a1.get("schema_correctness", 0.0))
    evidence_delta = float(a2.get("evidence_binding", 0.0)) - float(a1.get("evidence_binding", 0.0))

    if action == "patch_capability":
        if not after_caps or after_caps == before_caps:
            integrity = gate(
                FAIL,
                "patch_capability was selected, but the capability manifest did not add a new capability.",
                "repair_operator_noop_or_patch_application_failure",
            )
        elif not a1_missing.issubset(after_caps):
            integrity = gate(
                PARTIAL,
                f"Skill manifest changed, but it does not explicitly cover all A1 missing capabilities: {sorted(a1_missing - after_caps)}.",
                "repair_scope_mismatch",
            )
        else:
            integrity = gate(PASS, "A1 missing capabilities are represented in the revised capability manifest.")
    elif action == "rewrite_output_contract":
        if revision.get("before_contract") and revision.get("after_contract") and revision.get("before_contract") != revision.get("after_contract"):
            integrity = gate(PASS, "The output contract changed after verifier feedback.")
        elif a1_schema and len(a2_schema) < len(a1_schema) and gate_decision == "accept":
            integrity = gate(PASS, "The contract repair removed A1 schema errors under an accepted gate decision.")
        elif revision.get("before_contract") == revision.get("after_contract"):
            integrity = gate(FAIL, "rewrite_output_contract did not change the contract marker or reduce schema errors.", "repair_operator_noop_or_patch_application_failure")
        else:
            integrity = gate(PARTIAL, "The contract repair is accepted, but explicit contract before/after evidence is incomplete.", "repair_evidence_incomplete")
    else:
        integrity = gate(PARTIAL, f"Repair action `{action}` has no specialized integrity rule yet.", "unclassified_repair_action")

    same_missing = a1_missing & a2_missing
    if a2_pass:
        behavior = gate(PASS, "A2 passes the deterministic verifier after the revision.")
    elif same_missing:
        behavior = gate(
            FAIL,
            f"A2 still misses the same capability set: {sorted(same_missing)}.",
            "skill_to_execution_gap",
        )
    elif coverage_delta > 0 or schema_delta > 0 or evidence_delta > 0 or len(a2_schema) < len(a1_schema):
        behavior = gate(PARTIAL, "A2 improves some verifier dimensions but does not pass.", "partial_behavior_improvement")
    else:
        behavior = gate(FAIL, "A2 does not show measurable behavior improvement.", "no_behavior_improvement")

    if repeatability:
        robustness = gate(PASS, "A small repeatability smoke and negative controls exist for this slice.")
    elif sandboxed and a2_pass:
        robustness = gate(PARTIAL, "The loop closes in Harbor, but repeatability/metamorphic evidence is still narrow.")
    elif a2_pass:
        robustness = gate(PARTIAL, "The loop passes locally, but sandbox/holdout/metamorphic evidence is not attached.")
    else:
        robustness = gate(NOT_MEASURED, "Robustness is not meaningful until behavior improvement is demonstrated.")

    if integrity["status"] == FAIL:
        decision = "reject"
        level = "L0_NON_PROMOTABLE"
    elif behavior["status"] == FAIL:
        decision = "quarantine"
        level = "L0_NON_PROMOTABLE"
    elif sandboxed and a2_pass:
        decision = "promote_with_scope_limit"
        level = "L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT"
    elif a2_pass:
        decision = "promote_with_scope_limit"
        level = "L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT"
    else:
        decision = "candidate_only"
        level = "L1_CANDIDATE"

    return {
        "card_type": "RevisionQualificationCard",
        "card_id": card_id,
        "artifact": artifact,
        "scenario": scenario,
        "backend": backend,
        "qualification_decision": decision,
        "promotion_level": level,
        "claim_scope": (
            f"Controlled sandboxed repair-loop evidence for {scenario} only; no broad Harbor/backend generalization."
            if sandboxed
            else f"Controlled local repair-loop evidence for {scenario} only; no broad local LLM/general task generalization."
        ),
        "gates": {
            "integrity_gate": integrity,
            "behavior_gate": behavior,
            "robustness_gate": robustness,
        },
        "observed_delta": {
            "a1_pass": a1_pass,
            "a2_pass": a2_pass,
            "coverage_delta": round(coverage_delta, 4),
            "schema_delta": round(schema_delta, 4),
            "evidence_delta": round(evidence_delta, 4),
            "a1_feedback_type": a1.get("feedback_type", "unknown"),
            "a2_feedback_type": a2.get("feedback_type", "unknown"),
            "repair_action": action,
            "gate_decision": gate_decision,
        },
        "next_required_evidence": next_evidence(decision, level, robustness["status"]),
        "sources": sources,
    }


def next_evidence(decision: str, level: str, robustness_status: str) -> list[str]:
    if decision == "reject":
        return ["Fix repair integrity before collecting more outcome evidence."]
    if decision == "quarantine":
        return ["Diagnose why the agent did not express the revised Skill in A2 output."]
    items = []
    if level.startswith("L2_PROMOTE_LOCAL"):
        items.append("Run the same loop in Harbor/Docker or a comparable sandbox.")
    if robustness_status != PASS:
        items.append("Add negative, swapped-target, fake-evidence, and metamorphic controls.")
    items.append("Attach human or external review before broad deployment claims.")
    return items


def evidence_card(
    *,
    card_id: str,
    artifact: str,
    claim_scope: str,
    support_level: str,
    notes: list[str],
    sources: list[str],
) -> dict[str, Any]:
    return {
        "card_type": "EvidenceSupportCard",
        "card_id": card_id,
        "artifact": artifact,
        "qualification_decision": "supporting_evidence",
        "support_level": support_level,
        "claim_scope": claim_scope,
        "gates": {
            "integrity_gate": gate(PASS, notes[0] if notes else "No integrity issue detected in this supporting evidence card."),
            "behavior_gate": gate(PARTIAL, notes[1] if len(notes) > 1 else "This card is not a single repair-loop behavior test."),
            "robustness_gate": gate(PARTIAL, notes[2] if len(notes) > 2 else "Robustness evidence remains bounded."),
        },
        "next_required_evidence": ["Use this card as support for a repair-loop qualification card, not as a standalone deployment claim."],
        "sources": sources,
    }


def build_skill_qualification_cards(root: Path) -> dict[str, Any]:
    validation = root / "outputs" / "validation"
    cards: list[dict[str, Any]] = []
    repeatability_path = validation / "harbor_llm_repeatability_upload.json"
    repeatability = load_json(repeatability_path) if repeatability_path.exists() else {}
    negative_path = validation / "negative_controls.json"
    negative = load_json(negative_path) if negative_path.exists() else {}
    negative_pass = bool(negative.get("overall_pass", False))

    loop_specs = [
        (
            "live_llm_upload_repair_loop",
            "outputs/live_llm_repair_loop_upload_001",
            "upload_security_001",
            "live_llm_text",
            root / "outputs" / "live_llm_repair_loop_upload_001" / "summary.json",
            False,
            False,
        ),
        (
            "live_llm_data_quality_repair_loop",
            "outputs/live_llm_repair_loop_data_quality_001",
            "data_quality_review_001",
            "live_llm_text",
            root / "outputs" / "live_llm_repair_loop_data_quality_001" / "summary.json",
            False,
            False,
        ),
        (
            "live_llm_config_security_repair_loop",
            "outputs/live_llm_repair_loop_config_security_001",
            "config_security_001",
            "live_llm_text",
            root / "outputs" / "live_llm_repair_loop_config_security_001" / "summary.json",
            False,
            False,
        ),
        (
            "live_llm_api_review_repair_loop",
            "outputs/live_llm_repair_loop_api_review_001",
            "api_review_001",
            "live_llm_text",
            root / "outputs" / "live_llm_repair_loop_api_review_001" / "summary.json",
            False,
            False,
        ),
        (
            "harbor_llm_upload_repair_loop",
            "outputs/harbor_llm_repair_loop_upload_001",
            "real-upload-security-review",
            "harbor_live_llm",
            root / "outputs" / "harbor_llm_repair_loop_upload_001" / "summary.json",
            True,
            bool(repeatability.get("a1_all_fail") and repeatability.get("a2_all_pass") and negative_pass),
        ),
        (
            "harbor_llm_config_repair_loop",
            "outputs/harbor_llm_repair_loop_config_001",
            "controlled-config-security-review",
            "harbor_live_llm",
            root / "outputs" / "harbor_llm_repair_loop_config_001" / "summary.json",
            True,
            False,
        ),
    ]
    for card_id, artifact, scenario, backend, path, sandboxed, repeat in loop_specs:
        if not path.exists():
            continue
        cards.append(
            repair_loop_card(
                card_id=card_id,
                artifact=artifact,
                scenario=scenario,
                backend=backend,
                summary=load_json(path),
                sources=[
                    f"{artifact}/summary.json",
                    f"{artifact}/A1/verifier_report.json",
                    f"{artifact}/revision/patch_plan.json",
                    f"{artifact}/A2/verifier_report.json",
                ],
                sandboxed=sandboxed,
                repeatability=repeat,
            )
        )

    generalization_path = validation / "generalization_suite.json"
    if generalization_path.exists():
        generalization = load_json(generalization_path)
        cards.append(
            evidence_card(
                card_id="offline_generalization_qualification_support",
                artifact="outputs/validation/generalization_suite.json",
                claim_scope="Strong controlled evidence that one offline pipeline can cover the stored task cases.",
                support_level="supports_L3_PROMOTE_CONTROLLED",
                notes=[
                    f"A2 passes {generalization.get('a2_pass_count')}/{generalization.get('scenario_count')} controlled cases.",
                    "This is suite-level behavior evidence, not a single deployable Skill promotion.",
                    "Negative controls and verifier stress checks are separate and must remain attached.",
                ],
                sources=["outputs/validation/generalization_suite.json"],
            )
        )
    if negative_path.exists():
        cards.append(
            evidence_card(
                card_id="negative_control_robustness_support",
                artifact="outputs/validation/negative_controls.json",
                claim_scope="Narrow robustness support against unsupported evidence and clean-target false positives.",
                support_level="supports_L3_PROMOTE_CONTROLLED",
                notes=[
                    "Unsupported evidence and append-style false positives are rejected in two controlled cases.",
                    "This does not demonstrate task-solving behavior by itself.",
                    "The control set is useful but still small.",
                ],
                sources=["outputs/validation/negative_controls.json"],
            )
        )
    if repeatability_path.exists():
        cards.append(
            evidence_card(
                card_id="harbor_upload_repeatability_support",
                artifact="outputs/validation/harbor_llm_repeatability_upload.json",
                claim_scope="Small repeatability support for the controlled Harbor upload repair loop.",
                support_level="supports_L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT",
                notes=[
                    f"{repeatability.get('run_count', 0)} Harbor upload repeats show stable A1 fail and A2 pass.",
                    "This supports one Harbor upload loop, not broad prompt robustness.",
                    str(repeatability.get("prompt_sensitivity_risk", "prompt sensitivity not measured")),
                ],
                sources=["outputs/validation/harbor_llm_repeatability_upload.json"],
            )
        )

    return {
        "generated_at": utc_now(),
        "method": "Qualification-Guided Skill Evolution",
        "principle": "feedback proposes revision; qualification decides promotion",
        "level_order": [
            "L0_NON_PROMOTABLE",
            "L1_CANDIDATE",
            "L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT",
            "L3_PROMOTE_CONTROLLED",
            "L4_PROMOTE_SANDBOXED_WITH_SCOPE_LIMIT",
            "L5_PROMOTE_REVIEWED",
        ],
        "card_count": len(cards),
        "cards": cards,
    }


def render_skill_qualification_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Skill Qualification Card Status",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"Method: {payload['method']}",
        "",
        f"Principle: {payload['principle']}",
        "",
        "These cards do not replace verifier reports. They decide whether a revised Skill can be promoted, quarantined, or rejected after verifier feedback has proposed a repair.",
        "",
        "| Card | Type | Decision | Level/Support | Integrity | Behavior | Robustness |",
        "|---|---|---|---|---|---|---|",
    ]
    for card in payload["cards"]:
        gates = card["gates"]
        level = card.get("promotion_level", card.get("support_level", "n/a"))
        lines.append(
            "| {card_id} | {card_type} | {decision} | {level} | {integrity} | {behavior} | {robustness} |".format(
                card_id=card["card_id"],
                card_type=card.get("card_type", "unknown"),
                decision=card["qualification_decision"],
                level=level,
                integrity=gates["integrity_gate"]["status"],
                behavior=gates["behavior_gate"]["status"],
                robustness=gates["robustness_gate"]["status"],
            )
        )
    lines.append("")
    for card in payload["cards"]:
        lines.extend(
            [
                f"## {card['card_id']}",
                "",
                f"- Card type: `{card.get('card_type', 'unknown')}`",
                f"- Artifact: `{card['artifact']}`",
                f"- Decision: `{card['qualification_decision']}`",
                f"- Level/support: `{card.get('promotion_level', card.get('support_level', 'n/a'))}`",
                f"- Claim scope: {card['claim_scope']}",
                "",
            ]
        )
        for name, value in card["gates"].items():
            origin = value.get("failure_origin")
            origin_text = f" Failure origin: `{origin}`." if origin else ""
            lines.append(f"- {name}: `{value['status']}`. {value['evidence']}{origin_text}")
        lines.extend(["", "Next required evidence:"])
        for item in card["next_required_evidence"]:
            lines.append(f"- {item}")
        lines.extend(["", f"Sources: {', '.join(f'`{source}`' for source in card['sources'])}", ""])
    return "\n".join(lines) + "\n"
