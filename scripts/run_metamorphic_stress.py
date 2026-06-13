from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.verifier import verify_controlled_execution


JSON_OUT = ROOT / "outputs" / "validation" / "metamorphic_stress_minimal.json"
MD_OUT = ROOT / "reports" / "METAMORPHIC_STRESS_STATUS.md"


def run_case(
    *,
    case_id: str,
    scenario: str,
    transform: str,
    expected_relation: str,
    expected_capabilities: tuple[str, ...],
    findings: list[dict[str, str]],
    target_text: str,
    expected_pass: bool,
) -> dict[str, Any]:
    report = verify_controlled_execution(
        expected_capabilities,
        {"attempt": case_id, "backend": "metamorphic_stress", "findings": findings},
        target_text=target_text,
    ).to_dict()
    return {
        "case_id": case_id,
        "scenario": scenario,
        "transform": transform,
        "expected_relation": expected_relation,
        "expected_pass": expected_pass,
        "actual_pass": report["pass"],
        "control_passed": bool(report["pass"]) == expected_pass,
        "feedback_type": report["feedback_type"],
        "verifier_report": report,
    }


def build_cases() -> list[dict[str, Any]]:
    clean_upload_target = "app.py: upload() validates MIME type and file signature, stores a generated UUID name, and returns only file_id. config.yaml: audit_log_retention_days=90."
    clean_config_target = "prod.audit.enabled=true retention_days=90 export_sink=s3://audit-logs. prod.debug=false. prod.api_token is loaded from ENV."
    shuffled_data_target = "\n".join(
        [
            "validation.csv sample:",
            "- row 120: user_id=556, event_date=2025-05-05, country_code=CN, label=premium",
            "train.csv sample:",
            "- row 9811: user_id=112, event_date=2025-05-04, country_code=US, label=gold_plus",
            "- row 1042: user_id=991, event_date=2025-04-11, country_code=, label=basic",
            "dataset_contract.yaml: required_fields=[user_id,event_date,country_code,label]; allowed_labels=[basic,premium,enterprise]; validation_cutoff=2025-04-30.",
        ]
    )
    injected_api_target = "OpenAPI GET /users accepts user_id without role check and returns debug_path. The report must include capability_id, evidence_span, and recommended_fix."
    return [
        run_case(
            case_id="upload_clean_target_removes_findings",
            scenario="upload_security",
            transform="remove upload type/audit weakness",
            expected_relation="Previously appended upload findings should disappear or be rejected.",
            expected_capabilities=(),
            findings=[
                {
                    "capability_id": "UPLOAD_TYPE_MAGIC",
                    "issue": "Upload type validation missing",
                    "evidence_span": "filename.endswith",
                    "recommended_fix": "Validate MIME type and magic bytes.",
                }
            ],
            target_text=clean_upload_target,
            expected_pass=False,
        ),
        run_case(
            case_id="config_clean_production_rejects_false_positive",
            scenario="config_security",
            transform="clean production config",
            expected_relation="Append-style config findings should be rejected.",
            expected_capabilities=(),
            findings=[
                {
                    "capability_id": "CONFIG_ENV_GUARD",
                    "issue": "Environment guard missing",
                    "evidence_span": "dev.api_token and dev.debug",
                    "recommended_fix": "Bind findings to prod/dev context.",
                }
            ],
            target_text=clean_config_target,
            expected_pass=False,
        ),
        run_case(
            case_id="data_quality_row_shuffle_preserves_findings",
            scenario="data_quality",
            transform="shuffle row/order presentation",
            expected_relation="The same grounded data-quality findings should remain valid.",
            expected_capabilities=(
                "DATA_REQUIRED_FIELD_COVERAGE",
                "DATA_TEMPORAL_SPLIT_GUARD",
                "DATA_LABEL_ENUM_ALIGNMENT",
            ),
            findings=[
                {
                    "capability_id": "DATA_REQUIRED_FIELD_COVERAGE",
                    "issue": "Required field coverage issue",
                    "evidence_span": "country_code=",
                    "recommended_fix": "Reject or impute rows with missing required fields.",
                },
                {
                    "capability_id": "DATA_TEMPORAL_SPLIT_GUARD",
                    "issue": "Validation event date is after cutoff",
                    "evidence_span": "event_date=2025-05-05",
                    "recommended_fix": "Keep validation rows after the cutoff out of training.",
                },
                {
                    "capability_id": "DATA_LABEL_ENUM_ALIGNMENT",
                    "issue": "Label outside allowed enum",
                    "evidence_span": "label=gold_plus",
                    "recommended_fix": "Map or reject labels outside the allowed enum.",
                },
            ],
            target_text=shuffled_data_target,
            expected_pass=True,
        ),
        run_case(
            case_id="api_injected_overbroad_risk_appears",
            scenario="api_review",
            transform="inject overbroad endpoint risk",
            expected_relation="API_OVERBROAD_RISK should be accepted when target evidence exists.",
            expected_capabilities=("API_SCHEMA_CONTRACT", "API_OVERBROAD_RISK"),
            findings=[
                {
                    "capability_id": "API_SCHEMA_CONTRACT",
                    "issue": "Report follows required schema",
                    "evidence_span": "capability_id, evidence_span, and recommended_fix",
                    "recommended_fix": "Keep structured finding fields mandatory.",
                },
                {
                    "capability_id": "API_OVERBROAD_RISK",
                    "issue": "Overbroad user lookup",
                    "evidence_span": "GET /users accepts user_id without role check",
                    "recommended_fix": "Require authorization checks for user_id lookup.",
                },
            ],
            target_text=injected_api_target,
            expected_pass=True,
        ),
    ]


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Minimal Metamorphic Stress Status",
        "",
        f"Overall pass: `{payload['overall_pass']}`",
        "",
        "| Case | Scenario | Transform | Expected pass | Actual pass | Feedback | Control passed |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload["cases"]:
        lines.append(
            f"| {row['case_id']} | {row['scenario']} | {row['transform']} | {row['expected_pass']} | {row['actual_pass']} | {row['feedback_type']} | {row['control_passed']} |"
        )
    lines.extend(
        [
            "",
            "These are minimal stress checks. They support the Robustness Gate, but they are not a full hidden-verifier benchmark.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    cases = build_cases()
    payload = {
        "run_id": "metamorphic_stress_minimal_001",
        "case_count": len(cases),
        "overall_pass": all(case["control_passed"] for case in cases),
        "claim_scope": "minimal metamorphic stress for controlled verifier relations",
        "cases": cases,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({"json": str(JSON_OUT), "report": str(MD_OUT), "overall_pass": payload["overall_pass"]}, ensure_ascii=False, indent=2))
    return 0 if payload["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
