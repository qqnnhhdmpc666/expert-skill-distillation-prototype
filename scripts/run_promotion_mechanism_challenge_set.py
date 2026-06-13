from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
JSON_OUT = ROOT / "outputs" / "validation" / "promotion_mechanism_challenge_set.json"
MD_OUT = ROOT / "reports" / "PROMOTION_MECHANISM_CHALLENGE_SET_STATUS.md"


MECHANISMS = [
    "reward_delta_only",
    "gate_only",
    "weighted_validity_score",
    "pareto_conservative",
    "qgse_protocol",
    "qgse_pareto_protocol",
]


def challenge_cases() -> list[dict[str, Any]]:
    base_sources = ["synthetic_promotion_mechanism_challenge_set"]
    return [
        card(
            "true_improvement",
            "A1 fails, patch lands, A2 behavior improves.",
            "promote_scoped",
            integrity="pass",
            behavior="pass",
            robustness="partial",
            decision="promote_with_scope_limit",
            level="L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT",
            a2_pass=True,
            gate_decision="accept",
            sources=base_sources,
        ),
        card(
            "no_op_repair",
            "Patch selected but Skill v2 is unchanged.",
            "reject",
            integrity="fail",
            behavior="pass",
            robustness="partial",
            decision="reject",
            level="L0_NON_PROMOTABLE",
            a2_pass=True,
            gate_decision="accept",
            failure_origin="repair_operator_noop_or_patch_application_failure",
            sources=base_sources,
        ),
        card(
            "behavior_gap",
            "Skill v2 changed but agent ignored the new instruction.",
            "quarantine",
            integrity="pass",
            behavior="fail",
            robustness="not_measured",
            decision="quarantine",
            level="L0_NON_PROMOTABLE",
            a2_pass=False,
            gate_decision="accept",
            failure_origin="skill_to_execution_gap",
            sources=base_sources,
        ),
        card(
            "fake_evidence",
            "A2 looks complete but evidence is not present in the target.",
            "reject",
            integrity="pass",
            behavior="fail",
            robustness="fail",
            decision="reject",
            level="L0_NON_PROMOTABLE",
            a2_pass=True,
            gate_decision="accept",
            failure_origin="evidence_grounding_failure",
            dominance_regressions=["evidence_binding"],
            sources=base_sources,
        ),
        card(
            "verifier_relaxation",
            "A2 passes because verifier/contract was relaxed.",
            "reject",
            integrity="fail",
            behavior="pass",
            robustness="fail",
            decision="reject",
            level="L0_NON_PROMOTABLE",
            a2_pass=True,
            gate_decision="accept",
            failure_origin="verifier_relaxation",
            sources=base_sources,
        ),
        evidence_support(
            "support_card_only",
            "Negative controls support robustness but cannot promote a Skill by themselves.",
            expected="support_only",
        ),
        card(
            "scope_overclaim",
            "Local pass is useful but must not become sandbox/global promotion.",
            "promote_scoped",
            integrity="pass",
            behavior="pass",
            robustness="partial",
            decision="promote_with_scope_limit",
            level="L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT",
            a2_pass=True,
            gate_decision="accept",
            sources=base_sources,
        ),
        card(
            "robustness_fail",
            "Case passes but metamorphic relation fails.",
            "quarantine",
            integrity="pass",
            behavior="pass",
            robustness="fail",
            decision="quarantine",
            level="L0_NON_PROMOTABLE",
            a2_pass=True,
            gate_decision="accept",
            failure_origin="metamorphic_robustness_failure",
            dominance_regressions=["metamorphic"],
            sources=base_sources,
        ),
        card(
            "cost_regression",
            "Outcome improves, but cost exceeds the budget.",
            "quarantine",
            integrity="pass",
            behavior="pass",
            robustness="partial",
            decision="promote_with_scope_limit",
            level="L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT",
            a2_pass=True,
            gate_decision="accept",
            dominance_regressions=["cost_budget"],
            sources=base_sources,
        ),
        card(
            "human_usefulness_fail",
            "Verifier passes, but human review says the output is not useful.",
            "quarantine",
            integrity="pass",
            behavior="pass",
            robustness="partial",
            decision="promote_with_scope_limit",
            level="L2_PROMOTE_LOCAL_WITH_SCOPE_LIMIT",
            a2_pass=True,
            gate_decision="accept",
            dominance_regressions=["human_usefulness"],
            sources=base_sources,
        ),
    ]


def card(
    case_id: str,
    description: str,
    expected: str,
    *,
    integrity: str,
    behavior: str,
    robustness: str,
    decision: str,
    level: str,
    a2_pass: bool,
    gate_decision: str,
    sources: list[str],
    failure_origin: str | None = None,
    dominance_regressions: list[str] | None = None,
) -> dict[str, Any]:
    def gate(status: str) -> dict[str, str]:
        payload = {"status": status, "evidence": description}
        if status == "fail" and failure_origin:
            payload["failure_origin"] = failure_origin
        return payload

    return {
        "card_type": "RevisionQualificationCard",
        "card_id": case_id,
        "description": description,
        "expected_decision": expected,
        "qualification_decision": decision,
        "promotion_level": level,
        "claim_scope": "controlled challenge-set scope only",
        "dominance_regressions": dominance_regressions or [],
        "gates": {
            "integrity_gate": gate(integrity),
            "behavior_gate": gate(behavior),
            "robustness_gate": gate(robustness),
        },
        "observed_delta": {
            "a1_pass": False,
            "a2_pass": a2_pass,
            "gate_decision": gate_decision,
        },
        "sources": sources,
    }


def evidence_support(case_id: str, description: str, *, expected: str) -> dict[str, Any]:
    return {
        "card_type": "EvidenceSupportCard",
        "card_id": case_id,
        "description": description,
        "expected_decision": expected,
        "qualification_decision": "supporting_evidence",
        "support_level": "supports_L3_PROMOTE_CONTROLLED",
        "claim_scope": "supporting evidence only",
        "gates": {
            "integrity_gate": {"status": "pass", "evidence": description},
            "behavior_gate": {"status": "partial", "evidence": description},
            "robustness_gate": {"status": "partial", "evidence": description},
        },
        "sources": ["synthetic_promotion_mechanism_challenge_set"],
    }


def gate_status(card: dict[str, Any], gate_name: str) -> str:
    return str(card["gates"][gate_name]["status"])


def decide(mechanism: str, card: dict[str, Any]) -> str:
    if card.get("card_type") != "RevisionQualificationCard":
        return "support_only"
    observed = card.get("observed_delta", {})
    integrity = gate_status(card, "integrity_gate")
    behavior = gate_status(card, "behavior_gate")
    robustness = gate_status(card, "robustness_gate")
    regressions = set(str(item) for item in card.get("dominance_regressions", []))
    if mechanism == "reward_delta_only":
        return "promote_unscoped" if observed.get("a2_pass") else "reject"
    if mechanism == "gate_only":
        return "promote_unscoped" if observed.get("gate_decision") == "accept" else "reject"
    if mechanism == "weighted_validity_score":
        weights = {"pass": 1.0, "partial": 0.5, "not_measured": 0.0, "fail": -1.0}
        score = 0.4 * weights[integrity] + 0.4 * weights[behavior] + 0.2 * weights[robustness]
        return "promote_unscoped" if score >= 0.65 else "reject"
    if mechanism == "pareto_conservative":
        if integrity == "fail" or robustness == "fail" or regressions:
            return "reject"
        if behavior == "fail":
            return "quarantine"
        return "promote_unscoped" if behavior == "pass" else "candidate"
    if mechanism == "qgse_protocol":
        decision = str(card["qualification_decision"])
        if decision.startswith("promote"):
            return "promote_scoped"
        return decision
    if mechanism == "qgse_pareto_protocol":
        if regressions:
            return "quarantine"
        decision = decide("qgse_protocol", card)
        if robustness == "fail" and decision == "promote_scoped":
            return "quarantine"
        return decision
    raise ValueError(f"unknown mechanism {mechanism}")


def evaluate() -> dict[str, Any]:
    cases = challenge_cases()
    mechanism_rows = []
    for mechanism in MECHANISMS:
        rows = []
        false_promotion = 0
        false_rejection = 0
        scope_errors = 0
        for item in cases:
            expected = str(item["expected_decision"])
            actual = decide(mechanism, item)
            is_false_promotion = actual.startswith("promote") and not expected.startswith("promote")
            is_false_rejection = actual in {"reject", "quarantine"} and expected.startswith("promote")
            is_scope_error = actual == "promote_unscoped" and expected == "promote_scoped"
            false_promotion += int(is_false_promotion)
            false_rejection += int(is_false_rejection)
            scope_errors += int(is_scope_error)
            rows.append(
                {
                    "case_id": item["card_id"],
                    "expected": expected,
                    "actual": actual,
                    "match": actual == expected,
                    "false_promotion": is_false_promotion,
                    "false_rejection": is_false_rejection,
                    "scope_error": is_scope_error,
                }
            )
        risk_score = false_promotion * 5 + scope_errors * 3 + false_rejection * 2
        mechanism_rows.append(
            {
                "mechanism": mechanism,
                "false_promotion_count": false_promotion,
                "false_rejection_count": false_rejection,
                "scope_error_count": scope_errors,
                "risk_score_lower_is_better": risk_score,
                "rows": rows,
            }
        )
    best = min(mechanism_rows, key=lambda row: row["risk_score_lower_is_better"])
    return {
        "run_id": "promotion_mechanism_challenge_set_001",
        "case_count": len(cases),
        "mechanisms": mechanism_rows,
        "best_on_challenge_set": best["mechanism"],
        "boundary": "Synthetic challenge set for promotion-mechanism evaluation; not external human validation.",
        "cases": cases,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Promotion Mechanism Challenge Set Status",
        "",
        f"Best on challenge set: `{payload['best_on_challenge_set']}`",
        "",
        "| Mechanism | False promotion | False rejection | Scope errors | Risk score |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["mechanisms"]:
        lines.append(
            f"| {row['mechanism']} | {row['false_promotion_count']} | {row['false_rejection_count']} | {row['scope_error_count']} | {row['risk_score_lower_is_better']} |"
        )
    lines.extend(
        [
            "",
            "False promotion is weighted highest because promoting an invalid Skill is more dangerous than withholding a valid one. This challenge set is synthetic and complements, but does not replace, external/human validation.",
            "",
            "## Challenge Cases",
            "",
        ]
    )
    for item in payload["cases"]:
        lines.append(f"- `{item['card_id']}`: {item['description']} Expected `{item['expected_decision']}`.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    payload = evaluate()
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "best": payload["best_on_challenge_set"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
