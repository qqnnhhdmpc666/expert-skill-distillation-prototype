from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path("outputs/mvp_vertical_slice/adversarial_trace_verifier_001")
CASE_PATH = Path("data/harbor_api_review_tasks/api-review-001-compact-v1/case_001_openapi.md")
VALID_REVIEW_PATH = Path("outputs/mvp_vertical_slice/skill_to_agent_loop_001/case001_mock_protocolized_compressed_skill/review.json")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def run_trace_verifier(review_path: Path, output_path: Path) -> dict[str, Any]:
    subprocess.run(
        [
            sys.executable,
            "scripts/verify_api_review_trace_json.py",
            "--review",
            str(review_path),
            "--case",
            str(CASE_PATH),
            "--output",
            str(output_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    return read_json(output_path)


def make_cases(valid_review: dict[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    fake_evidence = deepcopy(valid_review)
    fake_evidence["rule_applications"][4]["evidence_span"] = "Checkout callback contains refund webhook signature."
    cases.append(
        {
            "adversarial_case": "fake_evidence_span",
            "expected_reject_reason": "evidence span is unrelated to the API case and R005 trigger terms",
            "review": fake_evidence,
        }
    )

    generic_trigger = deepcopy(valid_review)
    generic_trigger["rule_applications"][5]["trigger_condition_found"] = "This rule applies here."
    generic_trigger["rule_applications"][5]["evidence_span"] = "This should be checked."
    cases.append(
        {
            "adversarial_case": "generic_trigger",
            "expected_reject_reason": "trigger and evidence are generic rather than case/rule relevant",
            "review": generic_trigger,
        }
    )

    mismatched = deepcopy(valid_review)
    mismatched["rule_applications"][0]["finding_id"] = "F2"
    cases.append(
        {
            "adversarial_case": "mismatched_finding_id",
            "expected_reject_reason": "rule_application points to a finding with a different rule_id",
            "review": mismatched,
        }
    )

    rule_id_only = deepcopy(valid_review)
    rule_id_only["rule_applications"][1] = {
        "rule_id": "R002",
        "applicable": True,
        "finding_id": "F2",
        "trigger_condition_found": "n/a",
        "evidence_span": "n/a",
        "confidence": "medium",
    }
    cases.append(
        {
            "adversarial_case": "rule_id_only_trace",
            "expected_reject_reason": "trace has rule_id but no real trigger/evidence",
            "review": rule_id_only,
        }
    )

    return cases


def render_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Adversarial Trace Verifier 001",
        "",
        "## Purpose",
        "",
        "Check whether the trace verifier rejects obvious fake or weak rule-application evidence.",
        "",
        "| Case | Expected Reject Reason | Verifier Passed | Rejected As Expected | Key Error |",
        "|---|---|---|---|---|",
    ]
    for row in payload["results"]:
        errors = row["verifier_result"].get("trace_errors", [])
        key_error = errors[0] if errors else "none"
        lines.append(
            f"| {row['adversarial_case']} | {row['expected_reject_reason']} | "
            f"{row['verifier_passed']} | {row['rejected_as_expected']} | {key_error} |"
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
    valid_review = read_json(VALID_REVIEW_PATH)
    valid_dir = OUT_DIR / "valid_control"
    valid_review_path = valid_dir / "review.json"
    write_json(valid_review_path, valid_review)
    valid_result = run_trace_verifier(valid_review_path, valid_dir / "trace_verification.json")

    results: list[dict[str, Any]] = []
    for item in make_cases(valid_review):
        case_dir = OUT_DIR / item["adversarial_case"]
        review_path = case_dir / "review.json"
        output_path = case_dir / "trace_verification.json"
        write_json(review_path, item["review"])
        verifier_result = run_trace_verifier(review_path, output_path)
        verifier_passed = bool(verifier_result.get("passed"))
        results.append(
            {
                "adversarial_case": item["adversarial_case"],
                "expected_reject_reason": item["expected_reject_reason"],
                "verifier_decision": "accept" if verifier_passed else "reject",
                "verifier_passed": verifier_passed,
                "rejected_as_expected": not verifier_passed,
                "verifier_result": verifier_result,
                "interpretation": "rejected_as_expected" if not verifier_passed else "unexpected_accept",
            }
        )

    rejected_count = sum(1 for row in results if row["rejected_as_expected"])
    if valid_result.get("passed") and rejected_count == len(results):
        status = "partially_supported"
        finding = "Trace verifier rejects the constructed obvious fake/weak evidence cases while accepting the valid control."
    elif not valid_result.get("passed"):
        status = "inconclusive"
        finding = "Valid control failed, so adversarial conclusions are not reliable."
    else:
        status = "partially_supported_with_gaps"
        finding = "Trace verifier rejects some but not all adversarial cases; accepted cases indicate verifier-contract weakness."
    payload = {
        "run_id": OUT_DIR.name,
        "created_at": created_at,
        "valid_control": {
            "review": str(valid_review_path),
            "verifier_passed": bool(valid_result.get("passed")),
            "verifier_result": valid_result,
        },
        "results": results,
        "conclusion": {
            "status": status,
            "finding": finding,
            "boundary": "Toy adversarial sanity check only. This is not a deep semantic verifier or proof against sophisticated fake evidence.",
        },
    }
    write_json(OUT_DIR / "summary.json", payload)
    write_json(OUT_DIR / "adversarial_results.json", results)
    write_text(OUT_DIR / "summary.md", render_summary(payload))
    write_json(
        OUT_DIR / "manifest.json",
        {
            "run_id": OUT_DIR.name,
            "created_at": created_at,
            "artifacts": ["summary.json", "summary.md", "adversarial_results.json", "*/review.json", "*/trace_verification.json"],
            "boundary": payload["conclusion"]["boundary"],
        },
    )
    print(json.dumps({"output_dir": str(OUT_DIR), "status": status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
