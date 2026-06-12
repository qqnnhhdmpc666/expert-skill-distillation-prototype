from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evidence import append_jsonl, write_json
from .provenance import hash_file_sha256, hash_json_file_sha256
from .schemas import SkillPackage


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def installed_root(project_root: Path) -> Path:
    return project_root / "outputs" / "installed_skills"


def registry_path(project_root: Path) -> Path:
    return installed_root(project_root) / "registry.json"


def active_pointer_path(project_root: Path) -> Path:
    return installed_root(project_root) / "active_skill_pointer.json"


def active_pointer_dir(project_root: Path) -> Path:
    return installed_root(project_root) / "active_skill_pointers"


def per_skill_active_pointer_path(project_root: Path, skill_id: str) -> Path:
    return active_pointer_dir(project_root) / f"{skill_id}.json"


def install_history_path(project_root: Path) -> Path:
    return installed_root(project_root) / "install_history.jsonl"


def rollback_event_path(project_root: Path) -> Path:
    return installed_root(project_root) / "rollback_event.json"


def package_versions_root(project_root: Path, skill_id: str) -> Path:
    return installed_root(project_root) / "packages" / skill_id / "versions"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_registry(project_root: Path) -> dict[str, Any]:
    return load_json(
        registry_path(project_root),
        {
            "generated_at": utc_now(),
            "registry_type": "runtime_installed_skill_registry",
            "skills": [],
            "boundary": "Prototype runtime registry for installed Skill packages.",
        },
    )


def save_registry(project_root: Path, payload: dict[str, Any]) -> None:
    payload = dict(payload)
    payload["generated_at"] = utc_now()
    payload["registry_type"] = "runtime_installed_skill_registry"
    payload["boundary"] = "Prototype runtime registry read by skill-deploy run-skill; not a production package manager."
    write_json(registry_path(project_root), payload)


def load_active_pointer(project_root: Path, skill_id: str | None = None) -> dict[str, Any]:
    if skill_id:
        per_skill_path = per_skill_active_pointer_path(project_root, skill_id)
        if per_skill_path.exists():
            return load_json(per_skill_path, {})
        legacy = load_json(active_pointer_path(project_root), {})
        if str(legacy.get("skill_id")) == skill_id:
            return legacy
        return {}
    return load_json(active_pointer_path(project_root), {})


def save_active_pointer(project_root: Path, payload: dict[str, Any]) -> None:
    skill_id = str(payload.get("skill_id") or "")
    if skill_id:
        write_json(per_skill_active_pointer_path(project_root, skill_id), payload)
    write_json(active_pointer_path(project_root), payload)


def skill_version_dir(project_root: Path, skill_id: str, version: str) -> Path:
    return package_versions_root(project_root, skill_id) / version


def read_skill_version(skill_dir: Path) -> tuple[SkillPackage, str, dict[str, Any]]:
    manifest_path = skill_dir / "manifest.json"
    skill_path = skill_dir / "SKILL.md"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    package = SkillPackage.from_dict(manifest)
    skill_text = skill_path.read_text(encoding="utf-8")
    return package, skill_text, manifest


def _skill_row_by_id(registry: dict[str, Any], skill_id: str) -> dict[str, Any] | None:
    for row in registry.get("skills", []):
        if str(row.get("skill_id")) == skill_id:
            return row
    return None


def _available_versions_from_package(skill_source_dir: Path) -> list[str]:
    versions_dir = skill_source_dir / "versions"
    if not versions_dir.exists():
        return []
    return sorted(item.name for item in versions_dir.iterdir() if item.is_dir() and (item / "manifest.json").exists() and (item / "SKILL.md").exists())


def install_skill_package(project_root: Path, skill_source_dir: Path, requested_version: str | None = None) -> dict[str, Any]:
    skill_source_dir = skill_source_dir.resolve()
    root_manifest_path = skill_source_dir / "manifest.json"
    if not root_manifest_path.exists():
        raise ValueError(f"install source is missing manifest.json: {skill_source_dir}")
    root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8-sig"))
    skill_id = str(root_manifest["skill_id"])
    versions = _available_versions_from_package(skill_source_dir)
    if not versions:
        raise ValueError(f"install source has no installable versions/: {skill_source_dir}")
    selected_version = requested_version or versions[-1]
    if selected_version not in versions:
        raise ValueError(f"requested version `{selected_version}` not found in package versions {versions}")
    source_version_dir = skill_source_dir / "versions" / selected_version
    package, skill_text, manifest = read_skill_version(source_version_dir)
    if package.skill_id != skill_id:
        raise ValueError(f"root skill_id `{skill_id}` does not match version manifest skill_id `{package.skill_id}`")

    dest_version_dir = skill_version_dir(project_root, skill_id, selected_version)
    if dest_version_dir.exists():
        shutil.rmtree(dest_version_dir)
    dest_version_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_version_dir, dest_version_dir)

    registry = load_registry(project_root)
    row = _skill_row_by_id(registry, skill_id)
    if row is None:
        row = {
            "skill_id": skill_id,
            "package_source": str(skill_source_dir),
            "installed_versions": [],
            "active_version": selected_version,
        }
        registry.setdefault("skills", []).append(row)
    row["package_source"] = str(skill_source_dir)
    row["active_version"] = selected_version
    versions_set = {str(item) for item in row.get("installed_versions", [])}
    versions_set.add(selected_version)
    row["installed_versions"] = sorted(versions_set)
    row["active_skill_dir"] = str(dest_version_dir)
    row["skill_hash"] = hash_file_sha256(dest_version_dir / "SKILL.md")
    row["manifest_hash"] = hash_json_file_sha256(dest_version_dir / "manifest.json")
    save_registry(project_root, registry)

    pointer = {
        "skill_id": skill_id,
        "active_version": selected_version,
        "skill_dir": str(dest_version_dir),
        "updated_at": utc_now(),
    }
    save_active_pointer(project_root, pointer)
    append_jsonl(
        install_history_path(project_root),
        {
            "timestamp": utc_now(),
            "event": "install",
            "skill_id": skill_id,
            "version": selected_version,
            "skill_dir": str(dest_version_dir),
            "skill_hash": hash_file_sha256(dest_version_dir / "SKILL.md"),
            "manifest_hash": hash_json_file_sha256(dest_version_dir / "manifest.json"),
        },
    )
    return {
        "skill_id": skill_id,
        "active_version": selected_version,
        "skill_dir": str(dest_version_dir),
        "manifest": manifest,
        "skill_text_chars": len(skill_text),
    }


def resolve_installed_skill(project_root: Path, skill_id: str) -> dict[str, Any]:
    registry = load_registry(project_root)
    row = _skill_row_by_id(registry, skill_id)
    if row is None:
        raise ValueError(f"skill `{skill_id}` is not installed")
    pointer = load_active_pointer(project_root, skill_id)
    if str(pointer.get("skill_id")) != skill_id:
        raise ValueError(f"active skill pointer does not point to `{skill_id}`")
    version = str(pointer.get("active_version") or "")
    skill_dir = Path(str(pointer.get("skill_dir") or "")).resolve()
    if not version or not skill_dir.exists():
        raise ValueError(f"active pointer for `{skill_id}` is invalid")
    package, skill_text, manifest = read_skill_version(skill_dir)
    return {
        "registry_row": row,
        "pointer": pointer,
        "skill_dir": skill_dir,
        "skill_package": package,
        "skill_text": skill_text,
        "manifest": manifest,
    }


def rollback_installed_skill(project_root: Path, skill_id: str, to_version: str) -> dict[str, Any]:
    registry = load_registry(project_root)
    row = _skill_row_by_id(registry, skill_id)
    if row is None:
        raise ValueError(f"skill `{skill_id}` is not installed")
    installed_versions = [str(item) for item in row.get("installed_versions", [])]
    if to_version not in installed_versions:
        raise ValueError(f"rollback target `{to_version}` is not installed for `{skill_id}`")
    from_version = str(row.get("active_version") or "")
    dest_version_dir = skill_version_dir(project_root, skill_id, to_version)
    if not dest_version_dir.exists():
        raise ValueError(f"rollback target directory does not exist: {dest_version_dir}")
    row["active_version"] = to_version
    row["active_skill_dir"] = str(dest_version_dir)
    row["skill_hash"] = hash_file_sha256(dest_version_dir / "SKILL.md")
    row["manifest_hash"] = hash_json_file_sha256(dest_version_dir / "manifest.json")
    save_registry(project_root, registry)
    pointer = {
        "skill_id": skill_id,
        "active_version": to_version,
        "skill_dir": str(dest_version_dir),
        "updated_at": utc_now(),
    }
    save_active_pointer(project_root, pointer)
    event = {
        "timestamp": utc_now(),
        "event": "rollback",
        "skill_id": skill_id,
        "from_version": from_version,
        "to_version": to_version,
        "skill_dir": str(dest_version_dir),
        "skill_hash": hash_file_sha256(dest_version_dir / "SKILL.md"),
        "manifest_hash": hash_json_file_sha256(dest_version_dir / "manifest.json"),
    }
    append_jsonl(install_history_path(project_root), event)
    write_json(rollback_event_path(project_root), event)
    return event
