from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.canonical import sha256_bytes, sha256_json

REQUIRED_REGISTRY_FIELDS = {
    "task_id",
    "task_type",
    "fixture_type",
    "public_source",
    "source_url",
    "license",
    "commit_digest",
    "repo_snapshot_ref",
    "repo_snapshot_manifest",
    "allowed_knowledge",
    "expected_output_schema",
    "native_verifier",
    "status",
    "notes",
}


def load_repo_task_registry(registry_path: Path) -> dict[str, Any]:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "repo_security_task_registry.v1":
        raise ValueError("registry schema_version must be repo_security_task_registry.v1")
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("registry must contain at least one task")
    seen: set[str] = set()
    root = registry_path.parent
    for entry in tasks:
        missing = sorted(REQUIRED_REGISTRY_FIELDS - set(entry))
        if missing:
            raise ValueError(f"registry entry missing fields for {entry.get('task_id')}: {missing}")
        task_id = str(entry["task_id"])
        if task_id in seen:
            raise ValueError(f"duplicate task_id in registry: {task_id}")
        seen.add(task_id)
        _validate_paths(root, entry)
    return {
        **payload,
        "registry_path": str(registry_path),
        "registry_digest": sha256_bytes(registry_path.read_bytes()),
        "task_count": len(tasks),
    }


def select_registry_tasks(registry: dict[str, Any], task_id: str | None = None) -> list[dict[str, Any]]:
    tasks = [item for item in registry["tasks"] if item["status"] in {"active", "experimental"}]
    if task_id is not None:
        tasks = [item for item in tasks if item["task_id"] == task_id]
        if not tasks:
            raise ValueError(f"task_id not found or not runnable: {task_id}")
    return tasks


def registry_summary(registry: dict[str, Any]) -> dict[str, Any]:
    distribution: dict[str, int] = {}
    for task in registry["tasks"]:
        distribution[task["fixture_type"]] = distribution.get(task["fixture_type"], 0) + 1
    return {
        "schema_version": "repo_task_registry_summary.v1",
        "registry_digest": registry["registry_digest"],
        "task_count": registry["task_count"],
        "fixture_type_distribution": distribution,
        "task_ids": [task["task_id"] for task in registry["tasks"]],
    }


def task_entry_dir(registry_path: Path, entry: dict[str, Any]) -> Path:
    return (registry_path.parent / str(entry["task_dir"])).resolve()


def _validate_paths(root: Path, entry: dict[str, Any]) -> None:
    task_dir = root / str(entry.get("task_dir", entry["task_id"]))
    required_paths = [
        task_dir / "task.json",
        root / entry["repo_snapshot_manifest"],
        root / entry["allowed_knowledge"],
        root / entry["expected_output_schema"],
        root / entry["native_verifier"],
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(path)
    manifest = json.loads((root / entry["repo_snapshot_manifest"]).read_text(encoding="utf-8"))
    file_payload = [
        {"path": item["path"], "sha256": item.get("sha256"), "line_count": item.get("line_count")}
        for item in manifest.get("files", [])
    ]
    if sha256_json(file_payload) == sha256_json([]):
        raise ValueError(f"repo snapshot manifest has no files for {entry['task_id']}")
