from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

from ..compiler.evidence_binding import bind_task_aware_evidence
from ..runtime.skill_knowledge_injection import build_injection_manifests
from ..runtime.trajectory_evidence import write_trajectory_evidence_package
from .repo_evidence_collector import collect_repo_evidence
from .repo_security_verifier import verify_dependency_use_prediction

TASK_REQUIRED_FIELDS = {
    "schema_version",
    "task_id",
    "task_type",
    "public_source",
    "license",
    "repo_snapshot_ref",
    "commit_digest",
    "task_instruction",
    "allowed_tools",
    "skill_condition",
    "knowledge_access_contract",
    "expected_output_schema",
    "native_verifier",
    "hidden_gold",
    "resource_budget",
}

EVALUATOR_ONLY_TASK_FIELDS = {"hidden_gold", "expected_decision", "expected_reason", "native_verifier"}


def load_repo_security_task(task_dir: Path) -> dict[str, Any]:
    payload = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    missing = sorted(TASK_REQUIRED_FIELDS - set(payload))
    if missing:
        raise ValueError(f"task.json missing required fields: {missing}")
    if payload["task_type"] != "dependency_use_triage":
        raise ValueError(f"unsupported task_type: {payload['task_type']}")
    return payload


def runtime_visible_task(task: dict[str, Any]) -> dict[str, Any]:
    return _sanitize_runtime_value({key: value for key, value in task.items() if key not in EVALUATOR_ONLY_TASK_FIELDS})


def load_runtime_task_view(task_dir: Path) -> dict[str, Any]:
    package = load_task_package(task_dir)
    return {
        "schema_version": "repo_security_runtime_task_view.v1",
        "task": package["runtime_visible_task"],
        "repo_snapshot_manifest": package["repo_snapshot_manifest"],
        "allowed_knowledge": package["allowed_knowledge"],
        "expected_output_schema": package["expected_output_schema"],
        "runtime_visible_paths": [
            str(task_dir / "task.json"),
            str(task_dir / "repo_snapshot_manifest.json"),
            str(task_dir / "allowed_knowledge.json"),
            str(task_dir / "expected_output_schema.json"),
            str(task_dir / "repo_snapshot"),
        ],
        "evaluator_only_paths": [
            str(task_dir / "task.json") + "#evaluator_only_gold",
            str(task_dir / "verifier.py"),
        ],
    }


def load_task_package(task_dir: Path) -> dict[str, Any]:
    task = load_repo_security_task(task_dir)
    return {
        "task": task,
        "runtime_visible_task": runtime_visible_task(task),
        "repo_snapshot_manifest": _read_json(task_dir / "repo_snapshot_manifest.json"),
        "allowed_knowledge": _read_json(task_dir / "allowed_knowledge.json"),
        "expected_output_schema": _read_json(task_dir / "expected_output_schema.json"),
    }


def run_dependency_use_triage(task_dir: Path, output_dir: Path, condition_id: str = "C5_active_runtime") -> dict[str, Any]:
    task = load_repo_security_task(task_dir)
    runtime_view = load_runtime_task_view(task_dir)
    runtime_task = runtime_view["task"]
    repo_manifest = runtime_view["repo_snapshot_manifest"]
    allowed_knowledge = runtime_view["allowed_knowledge"]
    injection = build_injection_manifests(task_dir=task_dir, condition_id=condition_id, output_dir=output_dir)
    binding = bind_task_aware_evidence(
        {
            "task_type": runtime_task["task_type"],
            "skill_requirements": runtime_task["skill_condition"].get("requirements", []),
            "available_knowledge_sources": [item["source_id"] for item in allowed_knowledge["knowledge_sources"]],
            "repo_manifest": repo_manifest,
        }
    )
    repo_evidence = collect_repo_evidence(
        task_dir=task_dir, repo_manifest=repo_manifest, package=runtime_task["knowledge_access_contract"]["package"]
    )
    prediction, traces = _make_prediction(runtime_task, allowed_knowledge, binding, repo_evidence)
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / "prediction.json"
    prediction_path.write_text(json.dumps(prediction, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    verifier_result = verify_dependency_use_prediction(task, prediction, task_dir=task_dir)
    (output_dir / "verifier_result.json").write_text(
        json.dumps(verifier_result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    trajectory = write_trajectory_evidence_package(
        output_dir=output_dir,
        task_manifest=runtime_task,
        injection_manifests=injection,
        prediction=prediction,
        verifier_result=verifier_result,
        action_trace=traces["action_trace"],
        observation_trace=traces["observation_trace"],
        knowledge_query_trace=traces["knowledge_query_trace"],
    )
    return {
        "schema_version": "repo_security_task_run.v1",
        "task_id": task["task_id"],
        "prediction_path": str(prediction_path),
        "verifier_result_path": str(output_dir / "verifier_result.json"),
        "trajectory_evidence": trajectory,
        "verifier_pass": verifier_result["verifier_pass"],
        "failure_category": verifier_result["failure_category"],
    }


def _make_prediction(
    task: dict[str, Any],
    allowed_knowledge: dict[str, Any],
    binding: dict[str, Any],
    repo_evidence: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    package = task["knowledge_access_contract"]["package"]
    advisory_id = task["knowledge_access_contract"]["advisory_id"]
    evidence: list[dict[str, Any]] = []
    action_trace = [{"action": "load_task", "task_id": task["task_id"]}]
    observation_trace: list[dict[str, Any]] = [
        {
            "path": item["path"],
            "evidence_id": item["evidence_id"],
            "evidence_type": item["evidence_type"],
        }
        for item in repo_evidence
    ]
    knowledge_query_trace = [{"query_type": "advisory_by_package", "package": package, "advisory_id": advisory_id}]

    evidence.extend(item for item in repo_evidence if item["evidence_type"] != "repo_file_digest")
    version_evidence = next((item for item in repo_evidence if item["evidence_type"] == "resolved_version"), None)
    declared_version = version_evidence["attributes"]["version"] if version_evidence else None

    advisory = next(
        item for item in allowed_knowledge["knowledge_sources"] if item["source_id"] == advisory_id and item["package"] == package
    )
    range_event = advisory["affected_ranges"][0]
    affected = declared_version is not None and _version_in_range(declared_version, range_event)
    evidence.append(
        {
            "evidence_id": _stable_evidence_id("advisory_affected_range", "allowed_knowledge.json", json.dumps(range_event, sort_keys=True)),
            "evidence_type": "advisory_affected_range",
            "path": "allowed_knowledge.json",
            "line_start": None,
            "line_end": None,
            "excerpt": json.dumps(range_event, sort_keys=True),
            "file_digest": None,
            "source_id": advisory_id,
        }
    )
    has_use = _has_type(evidence, "import_use_site")
    if declared_version is None:
        decision = "unresolved"
        reason_codes = ["REQUIRED_EVIDENCE_MISSING"]
    elif not has_use:
        decision = "dependency_present_not_used"
        reason_codes = ["NO_IMPORT_USE_SITE"]
    elif affected:
        decision = "dependency_used_and_affected"
        reason_codes = ["VERSION_IN_AFFECTED_RANGE", "IMPORT_USE_SITE_FOUND"]
    else:
        decision = "dependency_used_not_affected"
        reason_codes = ["VERSION_NOT_AFFECTED", "IMPORT_USE_SITE_FOUND"]
    decision_excerpt = f"decision={decision}; required={','.join(binding['required_evidence'])}"
    evidence.append(
        {
            "evidence_id": _stable_evidence_id("decision_evidence", "derived", decision_excerpt),
            "evidence_type": "decision_evidence",
            "path": "derived",
            "line_start": None,
            "line_end": None,
            "excerpt": decision_excerpt,
            "file_digest": None,
        }
    )
    prediction = {
        "schema_version": "repo_security_prediction.v1",
        "task_id": task["task_id"],
        "task_type": task["task_type"],
        "decision": decision,
        "package": package,
        "declared_version": declared_version,
        "advisory_id": advisory_id,
        "evidence": evidence,
        "reason_codes": reason_codes,
    }
    action_trace.append({"action": "emit_prediction", "decision": decision})
    return prediction, {
        "action_trace": action_trace,
        "observation_trace": observation_trace,
        "knowledge_query_trace": knowledge_query_trace,
    }


def _has_type(evidence: list[dict[str, Any]], evidence_type: str) -> bool:
    return any(item.get("evidence_type") == evidence_type for item in evidence)


def _stable_evidence_id(evidence_type: str, path: str, excerpt: str) -> str:
    from ..core.canonical import sha256_json

    return sha256_json({"evidence_type": evidence_type, "path": path, "excerpt": excerpt})


def _version_in_range(version_text: str, range_event: dict[str, Any]) -> bool:
    try:
        version = Version(version_text)
        introduced = Version(str(range_event.get("introduced", "0")))
        fixed = Version(str(range_event["fixed"]))
    except (InvalidVersion, KeyError):
        return False
    return introduced <= version < fixed


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_runtime_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_runtime_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_runtime_value(item) for item in value]
    if value == "hidden_gold":
        return "evaluator_only_gold"
    if value == "verifier_expected_answer":
        return "evaluator_only_answer"
    return value
