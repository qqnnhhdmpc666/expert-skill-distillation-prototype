from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_bytes, sha256_json


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def build_injection_manifests(
    *,
    task_dir: Path,
    condition_id: str,
    output_dir: Path,
    bundle_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_dir = task_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    allowed_knowledge_path = task_dir / "allowed_knowledge.json"
    task_path = task_dir / "task.json"
    repo_manifest_path = task_dir / "repo_snapshot_manifest.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    runtime_task = _sanitize_runtime_value(
        {
            key: value
            for key, value in task.items()
            if key not in {"hidden_gold", "expected_decision", "expected_reason", "native_verifier"}
        }
    )
    runtime_task_view_path = output_dir / "runtime_task_view.json"
    runtime_task_view_path.write_text(
        json.dumps(
            {"schema_version": "repo_security_runtime_task_view.v1", "task": runtime_task},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    knowledge_enabled = condition_id in {"C3_skill_plus_knowledge", "C4_release_bundle", "C5_active_runtime"}
    skill_enabled = condition_id in {"C2_skill_only", "C3_skill_plus_knowledge", "C4_release_bundle", "C5_active_runtime"}
    bundle_fields = _bundle_fields(bundle_resolution)
    release_bundle_manifest = (bundle_resolution or {}).get("bundle_manifest") if bundle_resolution else None
    skill_payload = {
        "schema_version": "skill_injection_manifest.v1",
        "condition_id": condition_id,
        "skill_enabled": skill_enabled,
        "skill_id": "dependency_use_triage_skill" if skill_enabled else None,
        "skill_digest": _enabled_digest(
            enabled=skill_enabled, resolved_digest=bundle_fields["skill_digest"], fallback_payload=runtime_task
        ),
    }
    allowed_knowledge_digest = file_digest(allowed_knowledge_path) if knowledge_enabled else "none"
    knowledge_payload = {
        "schema_version": "knowledge_access_manifest.v1",
        "condition_id": condition_id,
        "knowledge_enabled": knowledge_enabled,
        "allowed_knowledge_sources": [str(allowed_knowledge_path)] if knowledge_enabled else [],
        "allowed_knowledge_digest": allowed_knowledge_digest,
        "knowledge_projection_digest": (bundle_fields["knowledge_projection_digest"] or allowed_knowledge_digest)
        if knowledge_enabled
        else "none",
        "knowledge_access_binding_digest": bundle_fields["knowledge_access_binding_digest"] if knowledge_enabled else "none",
        "knowledge_access_policy": "read_allowed_snapshot_only" if knowledge_enabled else "disabled",
    }
    condition_payload = {
        "schema_version": "runtime_condition_manifest.v1",
        "condition_id": condition_id,
        "skill_enabled": skill_enabled,
        "knowledge_enabled": knowledge_enabled,
        "runtime_visible_paths": [
            str(runtime_task_view_path),
            str(repo_manifest_path),
            str(task_dir / "expected_output_schema.json"),
            str(task_dir / "repo_snapshot"),
            *(knowledge_payload["allowed_knowledge_sources"] if knowledge_enabled else []),
        ],
        "hidden_evaluator_paths": [str(task_path) + "#evaluator_only_gold", str(task_dir / "verifier.py")],
        "active_bundle_digest": bundle_fields["bundle_digest"]
        or sha256_json(release_bundle_manifest or {"condition_id": condition_id}),
        **bundle_fields,
    }
    bundle_payload = {
        "schema_version": "repo_security_runtime_bundle_manifest.v1",
        "condition_id": condition_id,
        "task_id": json.loads(task_path.read_text(encoding="utf-8"))["task_id"],
        "skill_manifest_digest": sha256_json(skill_payload),
        "knowledge_manifest_digest": sha256_json(knowledge_payload),
        "condition_manifest_digest": sha256_json(condition_payload),
        "release_bundle": release_bundle_manifest or {"mode": "local_vertical_slice", "immutable": True},
        **bundle_fields,
    }
    outputs = {
        "condition_manifest": condition_payload,
        "skill_manifest": skill_payload,
        "knowledge_manifest": knowledge_payload,
        "bundle_manifest": bundle_payload,
    }
    for name, payload in outputs.items():
        (output_dir / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
    return outputs


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


def _bundle_fields(bundle_resolution: dict[str, Any] | None) -> dict[str, Any]:
    resolution = bundle_resolution or {}
    return {
        "bundle_attachment_mode": resolution.get("bundle_attachment_mode", "partial_local_manifest_only"),
        "resolution_source": resolution.get("resolution_source", "local_manifest_only"),
        "bundle_digest": resolution.get("bundle_digest"),
        "skill_digest": resolution.get("skill_digest"),
        "skill_artifact_digest": resolution.get("skill_artifact_digest"),
        "knowledge_projection_digest": resolution.get("knowledge_projection_digest"),
        "knowledge_access_binding_digest": resolution.get("knowledge_access_binding_digest"),
        "provider_policy_digest": resolution.get("provider_policy_digest"),
        "skill_family": resolution.get("skill_family"),
    }


def _enabled_digest(*, enabled: bool, resolved_digest: str | None, fallback_payload: dict[str, Any]) -> str:
    if not enabled:
        return "none"
    return resolved_digest or sha256_json(fallback_payload)
