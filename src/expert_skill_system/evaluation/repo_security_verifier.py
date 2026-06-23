from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_PREDICTION_FIELDS = {
    "schema_version",
    "task_id",
    "decision",
    "package",
    "declared_version",
    "advisory_id",
    "evidence",
    "reason_codes",
}


def verify_dependency_use_prediction(task: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    hidden_gold = dict(task.get("hidden_gold", {}))
    checks = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    missing_fields = sorted(REQUIRED_PREDICTION_FIELDS - set(prediction))
    add("schema_fields_present", not missing_fields, ",".join(missing_fields))
    add("task_id_match", prediction.get("task_id") == task.get("task_id"))
    add("decision_match", prediction.get("decision") == hidden_gold.get("decision"))
    add("package_match", prediction.get("package") == hidden_gold.get("expected_package"))
    add("version_match", prediction.get("declared_version") == hidden_gold.get("expected_version"))
    add("advisory_match", prediction.get("advisory_id") == hidden_gold.get("expected_advisory_id"))

    evidence = prediction.get("evidence", [])
    evidence_types = {item.get("evidence_type") for item in evidence if isinstance(item, dict)}
    required_evidence = set(hidden_gold.get("required_evidence_types", []))
    add("required_evidence_types_present", required_evidence <= evidence_types, f"missing={sorted(required_evidence - evidence_types)}")

    grounded = all(item.get("path") and item.get("excerpt") for item in evidence if isinstance(item, dict))
    add("evidence_grounded", bool(evidence) and grounded)

    verifier_pass = all(bool(check["passed"]) for check in checks)
    failure_category = None
    if not verifier_pass:
        if missing_fields:
            failure_category = "schema_error"
        elif not required_evidence <= evidence_types or not grounded:
            failure_category = "evidence_error"
        else:
            failure_category = "decision_error"
    return {
        "schema_version": "repo_security_verifier_result.v1",
        "task_id": task.get("task_id"),
        "verifier_pass": verifier_pass,
        "failure_category": failure_category,
        "checks": checks,
    }


def verify_prediction_file(task_path: Path, prediction_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    task = json.loads(task_path.read_text(encoding="utf-8"))
    prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
    result = verify_dependency_use_prediction(task, prediction)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return result
