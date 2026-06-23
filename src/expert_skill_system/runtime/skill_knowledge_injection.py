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
    bundle_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_dir = task_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    allowed_knowledge_path = task_dir / "allowed_knowledge.json"
    task_path = task_dir / "task.json"
    repo_manifest_path = task_dir / "repo_snapshot_manifest.json"
    knowledge_enabled = condition_id in {"C3_skill_plus_knowledge", "C4_release_bundle", "C5_active_runtime"}
    skill_enabled = condition_id in {"C2_skill_only", "C3_skill_plus_knowledge", "C4_release_bundle", "C5_active_runtime"}
    skill_payload = {
        "schema_version": "skill_injection_manifest.v1",
        "condition_id": condition_id,
        "skill_enabled": skill_enabled,
        "skill_id": "dependency_use_triage_skill" if skill_enabled else None,
        "skill_digest": file_digest(task_path) if skill_enabled else "none",
    }
    knowledge_payload = {
        "schema_version": "knowledge_access_manifest.v1",
        "condition_id": condition_id,
        "knowledge_enabled": knowledge_enabled,
        "allowed_knowledge_sources": [str(allowed_knowledge_path)] if knowledge_enabled else [],
        "knowledge_projection_digest": file_digest(allowed_knowledge_path) if knowledge_enabled else "none",
        "knowledge_access_policy": "read_allowed_snapshot_only" if knowledge_enabled else "disabled",
    }
    condition_payload = {
        "schema_version": "runtime_condition_manifest.v1",
        "condition_id": condition_id,
        "skill_enabled": skill_enabled,
        "knowledge_enabled": knowledge_enabled,
        "runtime_visible_paths": [
            str(task_path),
            str(repo_manifest_path),
            str(task_dir / "repo_snapshot"),
            *(knowledge_payload["allowed_knowledge_sources"] if knowledge_enabled else []),
        ],
        "hidden_evaluator_paths": [str(task_path) + "#hidden_gold", str(task_dir / "verifier.py")],
        "active_bundle_digest": sha256_json(bundle_manifest or {"condition_id": condition_id}),
    }
    bundle_payload = {
        "schema_version": "repo_security_runtime_bundle_manifest.v1",
        "condition_id": condition_id,
        "task_id": json.loads(task_path.read_text(encoding="utf-8"))["task_id"],
        "skill_manifest_digest": sha256_json(skill_payload),
        "knowledge_manifest_digest": sha256_json(knowledge_payload),
        "condition_manifest_digest": sha256_json(condition_payload),
        "release_bundle": bundle_manifest or {"mode": "local_vertical_slice", "immutable": True},
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
