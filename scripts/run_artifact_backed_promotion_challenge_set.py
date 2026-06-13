from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.run_promotion_mechanism_challenge_set import MECHANISMS, decide
from skill_deployment.qualification import build_skill_qualification_cards


JSON_OUT = ROOT / "outputs" / "validation" / "artifact_backed_promotion_challenge_set.json"
MD_OUT = ROOT / "reports" / "ARTIFACT_BACKED_PROMOTION_CHALLENGE_SET_STATUS.md"


def gate(status: str, evidence: str, origin: str | None = None) -> dict[str, str]:
    payload = {"status": status, "evidence": evidence}
    if origin:
        payload["failure_origin"] = origin
    return payload


def card_from_existing(card: dict[str, Any], expected: str) -> dict[str, Any]:
    copied = json.loads(json.dumps(card))
    copied["expected_decision"] = expected
    copied["description"] = f"Artifact-backed case from {card['artifact']}"
    return copied


def stress_card(case: dict[str, Any], expected: str, *, origin: str) -> dict[str, Any]:
    sources = []
    for key in ("agent_output", "trace"):
        value = Path(str(case[key]))
        try:
            sources.append(str(value.relative_to(ROOT)).replace("\\", "/"))
        except ValueError:
            sources.append(str(value).replace("\\", "/"))
    return {
        "card_type": "RevisionQualificationCard",
        "card_id": case["case_id"],
        "description": f"Artifact-backed agent-level metamorphic stress from {case['agent_output']}",
        "expected_decision": expected,
        "qualification_decision": "quarantine" if expected == "quarantine" else "reject",
        "promotion_level": "L0_NON_PROMOTABLE",
        "claim_scope": "agent-level metamorphic limitation evidence only",
        "dominance_regressions": ["metamorphic"],
        "gates": {
            "integrity_gate": gate("pass", "Agent produced an output artifact on a transformed target."),
            "behavior_gate": gate("fail", case["expected_relation"], origin),
            "robustness_gate": gate("fail", "Metamorphic relation failed.", origin),
        },
        "observed_delta": {"a1_pass": False, "a2_pass": bool(case["actual_pass"]), "gate_decision": "accept"},
        "sources": sources,
    }


def build_cases() -> list[dict[str, Any]]:
    cards = {card["card_id"]: card for card in build_skill_qualification_cards(ROOT)["cards"]}
    agent_summary = json.loads((ROOT / "outputs" / "validation" / "agent_level_metamorphic_stress_001" / "summary.json").read_text(encoding="utf-8"))
    stress = {case["case_id"]: case for case in agent_summary["cases"]}
    return [
        card_from_existing(cards["harbor_llm_upload_repair_loop"], "promote_scoped"),
        card_from_existing(cards["live_llm_config_security_repair_loop"], "quarantine"),
        card_from_existing(cards["live_llm_api_review_repair_loop"], "reject"),
        stress_card(stress["agent_upload_clean_target"], "quarantine", origin="agent_false_positive_under_transform"),
        stress_card(stress["agent_config_clean_target"], "quarantine", origin="agent_false_positive_under_transform"),
        stress_card(stress["agent_data_quality_row_shuffle"], "quarantine", origin="evidence_binding_brittleness"),
        card_from_existing(cards["negative_control_robustness_support"], "support_only"),
    ]


def evaluate(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for mechanism in MECHANISMS:
        false_promotion = 0
        false_rejection = 0
        scope_error = 0
        case_rows = []
        for case in cases:
            expected = str(case["expected_decision"])
            actual = decide(mechanism, case)
            fp = actual.startswith("promote") and not expected.startswith("promote")
            fr = actual in {"reject", "quarantine"} and expected.startswith("promote")
            se = actual == "promote_unscoped" and expected == "promote_scoped"
            false_promotion += int(fp)
            false_rejection += int(fr)
            scope_error += int(se)
            case_rows.append({"case_id": case["card_id"], "expected": expected, "actual": actual, "false_promotion": fp, "false_rejection": fr, "scope_error": se})
        rows.append(
            {
                "mechanism": mechanism,
                "false_promotion_count": false_promotion,
                "false_rejection_count": false_rejection,
                "scope_error_count": scope_error,
                "risk_score_lower_is_better": false_promotion * 5 + scope_error * 3 + false_rejection * 2,
                "rows": case_rows,
            }
        )
    return rows


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Artifact-Backed Promotion Challenge Set Status",
        "",
        f"Best on artifact-backed challenge set: `{payload['best_on_artifact_backed_set']}`",
        "",
        "| Mechanism | False promotion | False rejection | Scope errors | Risk score |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in payload["mechanisms"]:
        lines.append(f"| {row['mechanism']} | {row['false_promotion_count']} | {row['false_rejection_count']} | {row['scope_error_count']} | {row['risk_score_lower_is_better']} |")
    lines.extend(["", "## Cases", ""])
    for case in payload["cases"]:
        lines.append(f"- `{case['card_id']}` expected `{case['expected_decision']}` from `{', '.join(case.get('sources', [])[:1])}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    cases = build_cases()
    rows = evaluate(cases)
    best = min(rows, key=lambda row: row["risk_score_lower_is_better"])
    payload = {
        "run_id": "artifact_backed_promotion_challenge_set_001",
        "case_count": len(cases),
        "best_on_artifact_backed_set": best["mechanism"],
        "boundary": "Artifact-backed internal challenge set; still not hidden external or human-labeled validation.",
        "mechanisms": rows,
        "cases": cases,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    MD_OUT.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "best": payload["best_on_artifact_backed_set"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
