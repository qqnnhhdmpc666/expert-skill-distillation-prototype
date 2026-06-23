from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_bytes

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


def verify_dependency_use_prediction(
    task: dict[str, Any], prediction: dict[str, Any], task_dir: Path | None = None
) -> dict[str, Any]:
    hidden_gold = dict(task.get("hidden_gold", {}))
    task_dir = task_dir or Path(".")
    repo_manifest = _read_optional_json(task_dir / "repo_snapshot_manifest.json")
    allowed_knowledge = _read_optional_json(task_dir / "allowed_knowledge.json")
    checks = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    missing_fields = sorted(REQUIRED_PREDICTION_FIELDS - set(prediction))
    add("schema_fields_present", not missing_fields, ",".join(missing_fields))
    add("hidden_gold_absent_from_prediction", not _contains_forbidden_gold_key(prediction))
    add("task_id_match", prediction.get("task_id") == task.get("task_id"))
    add("decision_match", prediction.get("decision") == hidden_gold.get("decision"))
    add("package_match", prediction.get("package") == hidden_gold.get("expected_package"))
    add("version_match", prediction.get("declared_version") == hidden_gold.get("expected_version"))
    add("advisory_match", prediction.get("advisory_id") == hidden_gold.get("expected_advisory_id"))
    expected_reason_codes = set(hidden_gold.get("required_reason_codes", []))
    actual_reason_codes = set(prediction.get("reason_codes", []))
    add(
        "required_reason_codes_present",
        expected_reason_codes <= actual_reason_codes,
        f"missing={sorted(expected_reason_codes - actual_reason_codes)}",
    )

    evidence = prediction.get("evidence", [])
    evidence_types = {item.get("evidence_type") for item in evidence if isinstance(item, dict)}
    required_evidence = set(hidden_gold.get("required_evidence_types", []))
    add("required_evidence_types_present", required_evidence <= evidence_types, f"missing={sorted(required_evidence - evidence_types)}")

    grounded = all(item.get("evidence_id") and item.get("path") and item.get("excerpt") for item in evidence if isinstance(item, dict))
    add("evidence_grounded", bool(evidence) and grounded)
    resolution = [_resolve_evidence_ref(item, task_dir, repo_manifest, allowed_knowledge) for item in evidence if isinstance(item, dict)]
    add(
        "evidence_refs_resolve",
        bool(evidence) and all(item["resolved"] for item in resolution),
        json.dumps([item for item in resolution if not item["resolved"]], sort_keys=True),
    )
    if prediction.get("decision") in {"dependency_used_and_affected", "dependency_used_not_affected"}:
        add("import_use_required_for_used_decision", "import_use_site" in evidence_types)
    if prediction.get("decision") != "unresolved":
        add("repo_evidence_required_for_non_unresolved", bool({"dependency_declaration", "resolved_version"} <= evidence_types))

    verifier_pass = all(bool(check["passed"]) for check in checks)
    failure_category = None
    if not verifier_pass:
        if missing_fields:
            failure_category = "schema_error"
        elif _contains_forbidden_gold_key(prediction):
            failure_category = "oracle_leakage"
        elif not required_evidence <= evidence_types or not grounded or not all(item["resolved"] for item in resolution):
            failure_category = "evidence_error"
        elif not expected_reason_codes <= actual_reason_codes:
            failure_category = "reason_code_error"
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
    result = verify_dependency_use_prediction(task, prediction, task_dir=task_path.parent)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return result


def _resolve_evidence_ref(
    item: dict[str, Any], task_dir: Path, repo_manifest: dict[str, Any], allowed_knowledge: dict[str, Any]
) -> dict[str, Any]:
    evidence_type = item.get("evidence_type")
    path = item.get("path")
    if evidence_type == "decision_evidence" and path == "derived":
        return {"evidence_id": item.get("evidence_id"), "resolved": True}
    if evidence_type == "advisory_affected_range" and path == "allowed_knowledge.json":
        source_id = item.get("source_id")
        known_sources = {source.get("source_id") for source in allowed_knowledge.get("knowledge_sources", [])}
        return {"evidence_id": item.get("evidence_id"), "resolved": source_id in known_sources}
    manifest_files = {file_item["path"]: file_item for file_item in repo_manifest.get("files", [])}
    if path not in manifest_files:
        return {"evidence_id": item.get("evidence_id"), "resolved": False, "reason": "PATH_NOT_IN_MANIFEST"}
    full_path = task_dir / "repo_snapshot" / str(path)
    if not full_path.exists():
        return {"evidence_id": item.get("evidence_id"), "resolved": False, "reason": "FILE_MISSING"}
    file_digest = sha256_bytes(full_path.read_bytes())
    if item.get("file_digest") != file_digest:
        return {"evidence_id": item.get("evidence_id"), "resolved": False, "reason": "FILE_DIGEST_MISMATCH"}
    line_start = item.get("line_start")
    line_end = item.get("line_end")
    if line_start is None or line_end is None:
        return {"evidence_id": item.get("evidence_id"), "resolved": evidence_type == "repo_file_digest"}
    lines = full_path.read_text(encoding="utf-8").splitlines()
    if not (1 <= int(line_start) <= int(line_end) <= len(lines)):
        return {"evidence_id": item.get("evidence_id"), "resolved": False, "reason": "LINE_RANGE_INVALID"}
    excerpt = "\n".join(lines[int(line_start) - 1 : int(line_end)]).strip()
    if str(item.get("excerpt", "")).strip() not in excerpt and excerpt not in str(item.get("excerpt", "")).strip():
        return {"evidence_id": item.get("evidence_id"), "resolved": False, "reason": "EXCERPT_MISMATCH"}
    return {"evidence_id": item.get("evidence_id"), "resolved": True}


def _contains_forbidden_gold_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in {"hidden_gold", "expected_decision", "expected_reason", "verifier_gold"}:
                return True
            if _contains_forbidden_gold_key(item):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_gold_key(item) for item in value)
    return False


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
