from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

from ..compiler.evidence_binding import bind_task_aware_evidence
from ..runtime.skill_knowledge_injection import build_injection_manifests
from ..runtime.trajectory_evidence import write_trajectory_evidence_package
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


def load_repo_security_task(task_dir: Path) -> dict[str, Any]:
    payload = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    missing = sorted(TASK_REQUIRED_FIELDS - set(payload))
    if missing:
        raise ValueError(f"task.json missing required fields: {missing}")
    if payload["task_type"] != "dependency_use_triage":
        raise ValueError(f"unsupported task_type: {payload['task_type']}")
    return payload


def runtime_visible_task(task: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in task.items() if key != "hidden_gold"}


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
    package = load_task_package(task_dir)
    task = package["task"]
    repo_manifest = package["repo_snapshot_manifest"]
    allowed_knowledge = package["allowed_knowledge"]
    injection = build_injection_manifests(task_dir=task_dir, condition_id=condition_id, output_dir=output_dir)
    binding = bind_task_aware_evidence(
        {
            "task_type": task["task_type"],
            "skill_requirements": task["skill_condition"].get("requirements", []),
            "available_knowledge_sources": [item["source_id"] for item in allowed_knowledge["knowledge_sources"]],
            "repo_manifest": repo_manifest,
        }
    )
    prediction, traces = _make_prediction(task_dir, task, allowed_knowledge, repo_manifest, binding)
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / "prediction.json"
    prediction_path.write_text(json.dumps(prediction, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    verifier_result = verify_dependency_use_prediction(task, prediction)
    (output_dir / "verifier_result.json").write_text(
        json.dumps(verifier_result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    trajectory = write_trajectory_evidence_package(
        output_dir=output_dir,
        task_manifest=runtime_visible_task(task),
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
    task_dir: Path,
    task: dict[str, Any],
    allowed_knowledge: dict[str, Any],
    repo_manifest: dict[str, Any],
    binding: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    package = task["knowledge_access_contract"]["package"]
    advisory_id = task["knowledge_access_contract"]["advisory_id"]
    repo_root = task_dir / "repo_snapshot"
    evidence: list[dict[str, Any]] = []
    action_trace = [{"action": "load_task", "task_id": task["task_id"]}]
    observation_trace: list[dict[str, Any]] = []
    knowledge_query_trace = [{"query_type": "advisory_by_package", "package": package, "advisory_id": advisory_id}]

    declared_version = None
    for file_item in repo_manifest["files"]:
        path = file_item["path"]
        full_path = repo_root / path
        if not full_path.exists() or full_path.is_dir():
            continue
        text = full_path.read_text(encoding="utf-8")
        if path.endswith("requirements.txt"):
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = re.fullmatch(rf"\s*{re.escape(package)}==([^\s;]+)\s*", line)
                if match:
                    declared_version = match.group(1)
                    evidence.append(_evidence("dependency_declaration", path, line_no, line))
                    evidence.append(_evidence("resolved_version", path, line_no, line))
        if path.endswith(".py"):
            for line_no, line in enumerate(text.splitlines(), start=1):
                if re.search(rf"\bimport\s+{re.escape(package)}\b|\b{re.escape(package)}\.", line):
                    evidence.append(_evidence("import_or_use_site", path, line_no, line.strip()))
        observation_trace.append({"path": path, "bytes_read": len(text.encode("utf-8"))})

    advisory = next(
        item for item in allowed_knowledge["knowledge_sources"] if item["source_id"] == advisory_id and item["package"] == package
    )
    range_event = advisory["affected_ranges"][0]
    affected = declared_version is not None and _version_in_range(declared_version, range_event)
    evidence.append(
        {
            "evidence_type": "advisory_affected_range",
            "path": "allowed_knowledge.json",
            "line": None,
            "excerpt": json.dumps(range_event, sort_keys=True),
            "source_id": advisory_id,
        }
    )
    decision = "dependency_used_and_affected" if affected and _has_type(evidence, "import_or_use_site") else "unresolved"
    reason_codes = ["VERSION_IN_AFFECTED_RANGE", "IMPORT_OR_USE_SITE_FOUND"] if decision == "dependency_used_and_affected" else [
        "REQUIRED_EVIDENCE_MISSING"
    ]
    evidence.append(
        {
            "evidence_type": "decision_evidence",
            "path": "derived",
            "line": None,
            "excerpt": f"decision={decision}; required={','.join(binding['required_evidence'])}",
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


def _evidence(evidence_type: str, path: str, line: int, excerpt: str) -> dict[str, Any]:
    return {"evidence_type": evidence_type, "path": path, "line": line, "excerpt": excerpt}


def _has_type(evidence: list[dict[str, Any]], evidence_type: str) -> bool:
    return any(item.get("evidence_type") == evidence_type for item in evidence)


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
