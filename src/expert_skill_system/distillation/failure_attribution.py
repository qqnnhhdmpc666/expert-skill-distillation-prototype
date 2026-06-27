from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def attribute_repo_level_run(run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    task_results_path = run_dir / "task_results.jsonl"
    if not task_results_path.exists():
        return records, _summary(records)
    for line in task_results_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("verifier_pass") is True:
            continue
        record = attribute_task_failure(Path(row["verifier_result_path"]).parent, row)
        records.append(record)
    return records, _summary(records)


def attribute_task_failure(task_run_dir: Path, task_result: dict[str, Any] | None = None) -> dict[str, Any]:
    verifier_result = _read_json(task_run_dir / "verifier_result.json")
    prediction = _read_json(task_run_dir / "prediction.json")
    repo_evidence_path = task_run_dir / "repo_evidence.json"
    provenance_path = task_run_dir / "trajectory_evidence" / "provenance.json"
    bundle_policy_path = task_run_dir / "runtime_bundle_policy.json"
    bundle_policy = _read_json(bundle_policy_path) if bundle_policy_path.exists() else {}
    evidence_types = {
        item.get("evidence_type")
        for item in prediction.get("evidence", [])
        if isinstance(item, dict) and item.get("evidence_type")
    }
    failed_checks = [
        item["name"]
        for item in verifier_result.get("checks", [])
        if item.get("passed") is False and item.get("name")
    ]
    decision = str(prediction.get("decision"))
    missing_or_invalid: list[str] = []
    failure_type = "task_data_issue"
    repair_target = "verifier"
    violated_policy = "unknown"
    decision_policy = dict(bundle_policy.get("decision_policy", {}))
    knowledge_policy = dict(bundle_policy.get("knowledge_projection_policy", {}))
    binding_plan = dict(bundle_policy.get("evidence_binding_plan", {}))
    import_candidate_paths = _candidate_paths(binding_plan, "import_use_site")
    if decision == "dependency_used_and_affected" and "import_use_site" not in evidence_types:
        failure_type = "skill_missing_rule"
        repair_target = "skill_rule"
        missing_or_invalid = ["import_use_site"]
        violated_policy = "used_decision_requires_import_use_site"
    elif decision == "dependency_used_and_affected" and decision_policy.get("version_range_comparison_required") is False:
        failure_type = "skill_overgeneralized_rule"
        repair_target = "skill_rule"
        missing_or_invalid = ["version_range_comparison"]
        violated_policy = "version_range_comparison_required"
    elif (
        decision == "unresolved"
        and "advisory_affected_range" not in evidence_types
        and "affected_ranges" not in set(knowledge_policy.get("allowed_advisory_fields", []))
    ):
        failure_type = "knowledge_gap"
        repair_target = "knowledge_projection"
        missing_or_invalid = ["advisory_affected_range"]
        violated_policy = "advisory_affected_range_required_for_affectedness"
    elif "import_use_site" not in evidence_types and import_candidate_paths == []:
        failure_type = "evidence_binding_gap"
        repair_target = "evidence_binding_plan"
        missing_or_invalid = ["import_use_site_candidate_paths"]
        violated_policy = "import_use_site_binding_requires_source_candidates"
    elif verifier_result.get("failure_category") == "evidence_error":
        failure_type = "evidence_binding_gap"
        repair_target = "evidence_binding_plan"
        missing_or_invalid = _missing_from_check_details(failed_checks, verifier_result)
        violated_policy = "required_evidence_not_satisfied"
    elif verifier_result.get("failure_category") == "schema_error":
        failure_type = "runtime_execution_gap"
        repair_target = "runtime_policy"
        violated_policy = "prediction_schema_invalid"
    elif verifier_result.get("failure_category") == "oracle_leakage":
        failure_type = "runtime_execution_gap"
        repair_target = "runtime_policy"
        violated_policy = "hidden_gold_leakage"
    elif verifier_result.get("failure_category") == "decision_error":
        failure_type = "skill_overgeneralized_rule"
        repair_target = "skill_rule"
        violated_policy = "decision_mismatch"
    return {
        "schema_version": "distillation_failure_attribution.v1",
        "task_id": prediction.get("task_id") or (task_result or {}).get("task_id"),
        "failure_type": failure_type,
        "decision": decision,
        "missing_or_invalid_evidence": missing_or_invalid,
        "violated_policy": violated_policy,
        "supporting_artifact_paths": [
            str(path)
            for path in (
                task_run_dir / "verifier_result.json",
                task_run_dir / "prediction.json",
                repo_evidence_path,
                provenance_path,
            )
            if path.exists()
        ],
        "repair_target": repair_target,
        "bundle_policy_ref": str(bundle_policy_path) if bundle_policy_path.exists() else None,
        "verifier_failure_category": verifier_result.get("failure_category"),
        "failed_checks": failed_checks,
    }


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    failure_types: dict[str, int] = {}
    repair_targets: dict[str, int] = {}
    for record in records:
        failure_types[record["failure_type"]] = failure_types.get(record["failure_type"], 0) + 1
        repair_targets[record["repair_target"]] = repair_targets.get(record["repair_target"], 0) + 1
    return {
        "schema_version": "distillation_failure_summary.v1",
        "failure_count": len(records),
        "failed_task_ids": [str(record["task_id"]) for record in records],
        "failure_types": failure_types,
        "repair_targets": repair_targets,
    }


def _missing_from_check_details(failed_checks: list[str], verifier_result: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for check in verifier_result.get("checks", []):
        if check.get("name") not in failed_checks:
            continue
        detail = str(check.get("detail", ""))
        if "import_use_site" in detail or check.get("name") == "import_use_required_for_used_decision":
            missing.append("import_use_site")
    return sorted(set(missing))


def _candidate_paths(binding_plan: dict[str, Any], evidence_type: str) -> list[str] | None:
    for item in binding_plan.get("binding_plan", []):
        if item.get("evidence_type") == evidence_type and "candidate_paths" in item:
            return [str(path) for path in item.get("candidate_paths", [])]
    return None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
