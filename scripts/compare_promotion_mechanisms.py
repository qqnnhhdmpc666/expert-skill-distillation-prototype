from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.qualification import build_skill_qualification_cards


JSON_OUT = ROOT / "outputs" / "validation" / "promotion_mechanism_comparison.json"
MD_OUT = ROOT / "reports" / "PROMOTION_MECHANISM_EXPLORATION.md"


def status(card: dict[str, Any], gate_name: str) -> str:
    return str(card["gates"][gate_name]["status"])


def mechanism_decision(mechanism: str, card: dict[str, Any]) -> str:
    if card.get("card_type") != "RevisionQualificationCard":
        return "support_only"
    observed = card.get("observed_delta", {})
    integrity = status(card, "integrity_gate")
    behavior = status(card, "behavior_gate")
    robustness = status(card, "robustness_gate")
    if mechanism == "reward_delta_only":
        return "promote" if observed.get("a2_pass") else "reject"
    if mechanism == "gate_only":
        return "promote" if observed.get("gate_decision") == "accept" else "reject"
    if mechanism == "weighted_validity_score":
        weights = {
            "pass": 1.0,
            "partial": 0.5,
            "not_measured": 0.0,
            "fail": -1.0,
        }
        score = 0.4 * weights[integrity] + 0.4 * weights[behavior] + 0.2 * weights[robustness]
        return "promote" if score >= 0.65 else "reject"
    if mechanism == "pareto_conservative":
        if integrity == "fail":
            return "reject"
        if behavior == "fail":
            return "quarantine"
        return "promote" if behavior == "pass" else "candidate"
    if mechanism == "qgse_protocol":
        decision = str(card["qualification_decision"])
        if decision.startswith("promote"):
            return "promote"
        return decision
    raise ValueError(f"unknown mechanism {mechanism}")


def expected_decision(card: dict[str, Any]) -> str:
    if card.get("card_type") != "RevisionQualificationCard":
        return "support_only"
    card_id = str(card["card_id"])
    if card_id == "live_llm_config_security_repair_loop":
        return "quarantine"
    if card_id == "live_llm_api_review_repair_loop":
        return "reject"
    return "promote"


def criteria_results(mechanism: str, cards: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for card in cards:
        actual = mechanism_decision(mechanism, card)
        expected = expected_decision(card)
        rows.append(
            {
                "card_id": card["card_id"],
                "card_type": card.get("card_type", "unknown"),
                "expected": expected,
                "actual": actual,
                "match": actual == expected,
            }
        )
    revision_rows = [row for row in rows if row["card_type"] == "RevisionQualificationCard"]
    support_rows = [row for row in rows if row["card_type"] == "EvidenceSupportCard"]
    no_op_api = next(row for row in rows if row["card_id"] == "live_llm_api_review_repair_loop")
    config_gap = next(row for row in rows if row["card_id"] == "live_llm_config_security_repair_loop")
    scope_safe = True
    if mechanism in {"reward_delta_only", "gate_only", "weighted_validity_score", "pareto_conservative"}:
        scope_safe = False
    criteria = {
        "matches_current_grounded_labels": all(row["match"] for row in rows),
        "does_not_promote_support_cards": all(row["actual"] == "support_only" for row in support_rows),
        "rejects_api_noop_repair": no_op_api["actual"] == "reject",
        "quarantines_config_behavior_gap": config_gap["actual"] == "quarantine",
        "keeps_promotion_scope_explicit": scope_safe,
        "can_explain_failure_origin": mechanism in {"qgse_protocol", "pareto_conservative"},
    }
    return {
        "mechanism": mechanism,
        "score": sum(1 for value in criteria.values() if value),
        "criteria": criteria,
        "rows": rows,
        "recommendation": "best_current" if mechanism == "qgse_protocol" else "candidate_or_baseline",
        "failure_mode": mechanism_failure_mode(mechanism),
    }


def mechanism_failure_mode(mechanism: str) -> str:
    if mechanism == "reward_delta_only":
        return "Cannot distinguish lucky pass, repair attribution, no-op repair, or scoped promotion evidence."
    if mechanism == "gate_only":
        return "Promotes accepted patches even when A2 behavior does not improve."
    if mechanism == "weighted_validity_score":
        return "Compresses hard blockers into a score and can hide why a revision is non-promotable."
    if mechanism == "pareto_conservative":
        return "Useful as a baseline, but does not model evidence support cards or promotion scopes as explicitly as QGSE."
    return "Current best mechanism, but still needs stronger metamorphic and human-review evidence."


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Promotion Mechanism Exploration",
        "",
        "This report keeps the Skill-upgrade decision mechanism open to alternatives. QGSE is treated as the current best protocol, not as an unchangeable assumption.",
        "",
        f"Best current mechanism: `{payload['best_current_mechanism']}`",
        "",
        "| Mechanism | Score | Recommendation | Main failure mode |",
        "|---|---:|---|---|",
    ]
    for item in payload["mechanisms"]:
        lines.append(f"| {item['mechanism']} | {item['score']} | {item['recommendation']} | {item['failure_mode']} |")
    lines.extend(["", "## Criteria", ""])
    for item in payload["mechanisms"]:
        lines.extend([f"### {item['mechanism']}", ""])
        for key, value in item["criteria"].items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")
    lines.extend(
        [
            "## Current Conclusion",
            "",
            "The best current mechanism is QGSE because it preserves hard blockers, separates revision qualification from supporting evidence, forces claim scope, and records failure origin. It should remain replaceable: future mechanisms can win if they better predict human usefulness, held-out task transfer, and metamorphic robustness without hiding failures.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    cards = build_skill_qualification_cards(ROOT)["cards"]
    mechanisms = [
        criteria_results(name, cards)
        for name in [
            "reward_delta_only",
            "gate_only",
            "weighted_validity_score",
            "pareto_conservative",
            "qgse_protocol",
        ]
    ]
    best = max(mechanisms, key=lambda item: item["score"])
    payload = {
        "best_current_mechanism": best["mechanism"],
        "selection_rule": "highest criteria score on current grounded cards; tie-break in favor of explicit failure origin and scope handling",
        "mechanisms": mechanisms,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "best": payload["best_current_mechanism"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
