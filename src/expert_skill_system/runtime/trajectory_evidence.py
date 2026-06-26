from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_json


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_trajectory_evidence_package(
    *,
    output_dir: Path,
    task_manifest: dict[str, Any],
    injection_manifests: dict[str, Any],
    prediction: dict[str, Any],
    verifier_result: dict[str, Any],
    action_trace: list[dict[str, Any]],
    observation_trace: list[dict[str, Any]],
    knowledge_query_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    package_dir = output_dir / "trajectory_evidence"
    package_dir.mkdir(parents=True, exist_ok=True)
    outcome = {
        "schema_version": "trajectory_outcome.v1",
        "task_id": task_manifest.get("task_id"),
        "skill_used": injection_manifests["skill_manifest"]["skill_enabled"],
        "knowledge_used": injection_manifests["knowledge_manifest"]["knowledge_enabled"],
        "knowledge_queries": len(knowledge_query_trace),
        "evidence_refs": prediction.get("evidence", []),
        "prediction": prediction,
        "verifier_pass": verifier_result.get("verifier_pass"),
        "failure_category": verifier_result.get("failure_category"),
    }
    environment = {
        "schema_version": "runtime_environment_manifest.v1",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    cost = {
        "schema_version": "trajectory_cost.v1",
        "llm_calls": 0,
        "llm_tokens": None,
        "runtime_seconds": None,
        "cost_reason": "local deterministic vertical slice",
    }
    provenance = {
        "schema_version": "trajectory_provenance.v1",
        "task_digest": sha256_json(task_manifest),
        "prediction_digest": sha256_json(prediction),
        "verifier_result_digest": sha256_json(verifier_result),
        "condition_manifest_digest": sha256_json(injection_manifests["condition_manifest"]),
        **_repo_provenance_fields(task_manifest),
        **_bundle_provenance_fields(injection_manifests["bundle_manifest"]),
    }
    files = {
        "task_manifest.json": task_manifest,
        "condition_manifest.json": injection_manifests["condition_manifest"],
        "skill_manifest.json": injection_manifests["skill_manifest"],
        "knowledge_manifest.json": injection_manifests["knowledge_manifest"],
        "bundle_manifest.json": injection_manifests["bundle_manifest"],
        "environment_manifest.json": environment,
        "verifier_result.json": verifier_result,
        "outcome.json": outcome,
        "cost.json": cost,
        "provenance.json": provenance,
    }
    for filename, payload in files.items():
        write_json(package_dir / filename, payload)
    write_jsonl(package_dir / "action_trace.jsonl", action_trace)
    write_jsonl(package_dir / "observation_trace.jsonl", observation_trace)
    write_jsonl(package_dir / "knowledge_query_trace.jsonl", knowledge_query_trace)
    return {"package_dir": str(package_dir), "outcome": outcome, "provenance": provenance}


def _bundle_provenance_fields(bundle_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "bundle_attachment_mode": bundle_manifest.get("bundle_attachment_mode", "partial_local_manifest_only"),
        "bundle_digest": bundle_manifest.get("bundle_digest"),
        "skill_digest": bundle_manifest.get("skill_digest"),
        "skill_artifact_digest": bundle_manifest.get("skill_artifact_digest"),
        "knowledge_projection_digest": bundle_manifest.get("knowledge_projection_digest"),
        "knowledge_access_binding_digest": bundle_manifest.get("knowledge_access_binding_digest"),
        "provider_policy_digest": bundle_manifest.get("provider_policy_digest"),
        "skill_family": bundle_manifest.get("skill_family"),
    }


def _repo_provenance_fields(task_manifest: dict[str, Any]) -> dict[str, Any]:
    public_source = task_manifest.get("public_source")
    source_url = public_source.get("source_url") if isinstance(public_source, dict) else None
    fixture_type = public_source.get("fixture_type") if isinstance(public_source, dict) else None
    return {
        "fixture_type": fixture_type,
        "source_url": source_url,
        "repo_snapshot_ref": task_manifest.get("repo_snapshot_ref"),
        "commit_digest": task_manifest.get("commit_digest"),
        "repo_snapshot_manifest_digest": task_manifest.get("repo_snapshot_manifest_digest"),
        "repo_snapshot_content_digest": task_manifest.get("repo_snapshot_content_digest"),
    }
