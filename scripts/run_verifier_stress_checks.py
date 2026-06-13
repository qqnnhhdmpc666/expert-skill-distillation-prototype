from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
import sys

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import select_controlled_task_cases, verify_controlled_execution


DATA_ROOT = ROOT / "data" / "task_cases"
OUT = ROOT / "outputs" / "validation"
REPORTS = ROOT / "reports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def summarize(report: Any) -> dict[str, Any]:
    payload = report.to_dict() if hasattr(report, "to_dict") else dict(report)
    scores = payload.get("scores", {})
    return {
        "pass": payload.get("pass"),
        "feedback_type": payload.get("feedback_type"),
        "missing_capabilities": payload.get("missing_capabilities", []),
        "unsupported_evidence_capabilities": payload.get("unsupported_evidence_capabilities", []),
        "false_positive_capabilities": payload.get("false_positive_capabilities", []),
        "schema_errors": payload.get("schema_errors", []),
        "evidence_binding_score": scores.get("evidence_binding_score"),
    }


def main() -> int:
    upload_case = select_controlled_task_cases(DATA_ROOT, "upload")[0]
    data_quality_case = select_controlled_task_cases(DATA_ROOT, "data_quality")[0]
    upload_report = read_json(ROOT / "outputs" / "live_llm_upload_001" / "security_report.json")

    checks: list[dict[str, Any]] = []

    strict_match = verify_controlled_execution(
        upload_case.expected_capabilities,
        upload_report,
        feedback_overrides=upload_case.verifier_contract.get("feedback_overrides", {}),
        target_text=upload_case.target_asset,
    )
    checks.append(
        {
            "check_id": "upload_live_llm_strict_target_match",
            "purpose": "A valid upload report should still pass when strict target-text evidence binding is enabled.",
            "target_case": upload_case.case_id,
            "status": "pass" if strict_match.passed else "fail",
            "report": summarize(strict_match),
        }
    )

    swapped_target = verify_controlled_execution(
        upload_case.expected_capabilities,
        upload_report,
        feedback_overrides=upload_case.verifier_contract.get("feedback_overrides", {}),
        target_text=data_quality_case.target_asset,
    )
    checks.append(
        {
            "check_id": "upload_report_against_swapped_data_quality_target",
            "purpose": "The same upload report should fail when evaluated against the wrong target asset.",
            "target_case": data_quality_case.case_id,
            "status": "pass" if (not swapped_target.passed and swapped_target.feedback_type == "unsupported_evidence") else "fail",
            "report": summarize(swapped_target),
        }
    )

    synthetic_bad_evidence = verify_controlled_execution(
        upload_case.expected_capabilities,
        {
            "findings": [
                {
                    "capability_id": "UPLOAD_TYPE_MAGIC",
                    "issue": "Upload type validation",
                    "evidence_span": "app.py: upload() trusts client-side JavaScript checksum",
                    "recommended_fix": "Validate MIME and magic bytes server side.",
                }
            ]
        },
        target_text=upload_case.target_asset,
    )
    checks.append(
        {
            "check_id": "synthetic_bad_upload_evidence",
            "purpose": "A non-empty but non-matching evidence span should be rejected by the shared verifier when strict target binding is enabled.",
            "target_case": upload_case.case_id,
            "status": "pass" if (not synthetic_bad_evidence.passed and "UPLOAD_TYPE_MAGIC" in synthetic_bad_evidence.unsupported_evidence_capabilities) else "fail",
            "report": summarize(synthetic_bad_evidence),
        }
    )

    payload = {
        "run_id": "verifier_stress_checks_001",
        "created_at": utc_now(),
        "strict_evidence_binding_added_to_shared_verifier": True,
        "checks": checks,
        "overall_pass": all(item["status"] == "pass" for item in checks),
        "boundary": "Strict target-text evidence binding is available in the shared verifier, but it is not enabled by default across every existing backend artifact path.",
    }
    write_json(OUT / "verifier_stress_checks.json", payload)
    write_text(
        REPORTS / "VERIFIER_STRESS_STATUS.md",
        "\n".join(
            [
                "# Verifier Stress Status",
                "",
                "## Result",
                "",
                f"- Checks: `{len(checks)}`",
                f"- Passed: `{sum(1 for item in checks if item['status'] == 'pass')}/{len(checks)}`",
                f"- Overall: `{'PASS' if payload['overall_pass'] else 'FAIL'}`",
                "",
                "| Check | Purpose | Result | Feedback | Unsupported Evidence |",
                "|---|---|---:|---|---|",
                *[
                    f"| {item['check_id']} | {item['purpose']} | {item['status']} | "
                    f"{item['report']['feedback_type']} | "
                    f"{', '.join(item['report']['unsupported_evidence_capabilities']) or 'none'} |"
                    for item in checks
                ],
                "",
                "## What improved",
                "",
                "1. The shared verifier can now perform optional strict target-text evidence binding.",
                "2. A valid upload report still passes against the correct target text.",
                "3. The same report fails against a swapped non-security target, reducing the chance of accidental target/report mismatch passing silently.",
                "4. A non-empty but fabricated evidence span is now caught by the shared verifier under strict mode.",
                "",
                "## Boundary",
                "",
                "This strengthens verifier credibility, but it is still substring-level evidence binding. It is not deep semantic grounding and is not yet enabled by default in every legacy artifact path.",
                "",
            ]
        )
        + "\n",
    )
    print(json.dumps({"output": str(OUT / "verifier_stress_checks.json"), "overall_pass": payload["overall_pass"]}, ensure_ascii=False, indent=2))
    return 0 if payload["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
